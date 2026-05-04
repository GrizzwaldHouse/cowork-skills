# test_state_store.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Verifies the atomic, lock-protected JSON state I/O helpers in
#          state_store.py. Tests cover happy-path round trips, concurrent
#          reads, malformed JSON handling, missing files, schema mismatch,
#          lock contention, and the bootstrap routine.

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from AgenticOS import state_store
from AgenticOS.models import (
    AgentDomain,
    AgentState,
    AgentStatus,
    ApprovalKind,
    ApprovalQueueEntry,
)
from AgenticOS.state_store import (
    StateLockError,
    StateSchemaError,
    _advisory_lock,
    append_approval_entry,
    bootstrap_state_files,
    read_agents,
    read_approval_queue,
    write_agents,
    write_approval_queue,
)


# ---------------------------------------------------------------------------
# Test data builders
# ---------------------------------------------------------------------------

def _make_agent(agent_id: str = "AGENT-01", stage: int = 1) -> AgentState:
    """Construct a minimal valid AgentState for a given id and stage.
    Pulled out so each test stays focused on the behaviour it asserts."""
    return AgentState(
        agent_id=agent_id,
        domain=AgentDomain.GENERAL,
        task="unit test",
        stage_label="setup",
        stage=stage,
        total_stages=3,
        progress_pct=stage * 10,
        status=AgentStatus.ACTIVE,
        context_pct_used=10,
        updated_at=datetime.now(timezone.utc),
    )


def _make_queue_entry(agent_id: str = "AGENT-01") -> ApprovalQueueEntry:
    """Construct a minimal valid ApprovalQueueEntry."""
    return ApprovalQueueEntry(
        agent_id=agent_id,
        decision=ApprovalKind.PROCEED,
        reviewer_context=None,
        decided_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# 1. Atomic write produces the expected file contents
# ---------------------------------------------------------------------------

def test_atomic_write_round_trip_agents(tmp_path: Path) -> None:
    """Writing a list of agents and reading it back yields equal data."""
    agents_path = tmp_path / "agents.json"
    original = [_make_agent("AGENT-01"), _make_agent("AGENT-02", stage=2)]

    # write_agents must atomically replace the file with valid JSON.
    write_agents(original, path=agents_path)

    # The file must now exist and parse as a JSON list of length 2.
    raw = agents_path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert isinstance(parsed, list) and len(parsed) == 2

    # Round-tripping through read_agents must produce equivalent models.
    loaded = read_agents(path=agents_path)
    assert {agent.agent_id for agent in loaded} == {"AGENT-01", "AGENT-02"}


# ---------------------------------------------------------------------------
# 2. Concurrent reads from many threads do not corrupt each other
# ---------------------------------------------------------------------------

def test_concurrent_reads_return_consistent_data(tmp_path: Path) -> None:
    """Spawning many reader threads against a stable file must each
    receive an intact, validated agent list."""
    agents_path = tmp_path / "agents.json"
    write_agents([_make_agent("AGENT-01")], path=agents_path)

    results: list[list[AgentState]] = []
    errors: list[Exception] = []

    def _worker() -> None:
        # Each thread performs an independent read; any exception is
        # captured for assertion in the main thread.
        try:
            results.append(read_agents(path=agents_path))
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # No reader may have raised, and every reader must have seen the
    # single agent we wrote.
    assert not errors, f"reader thread raised: {errors[0]!r}"
    assert all(len(r) == 1 and r[0].agent_id == "AGENT-01" for r in results)


# ---------------------------------------------------------------------------
# 3. Malformed JSON surfaces as StateSchemaError
# ---------------------------------------------------------------------------

def test_malformed_json_raises_state_schema_error(tmp_path: Path) -> None:
    """A file containing non-JSON garbage must raise StateSchemaError so
    the caller can decide whether to retry or alert."""
    agents_path = tmp_path / "agents.json"
    agents_path.write_text("{ this is not valid json", encoding="utf-8")

    with pytest.raises(StateSchemaError):
        read_agents(path=agents_path)


# ---------------------------------------------------------------------------
# 4. Missing file returns an empty list (first-run condition)
# ---------------------------------------------------------------------------

def test_missing_file_returns_empty_list(tmp_path: Path) -> None:
    """Reading a path that does not exist must return [] rather than
    raise: the bus treats absence as 'no agents have started yet'."""
    missing_path = tmp_path / "does-not-exist.json"
    assert read_agents(path=missing_path) == []
    assert read_approval_queue(path=missing_path) == []


# ---------------------------------------------------------------------------
# 5. Schema mismatch (valid JSON, wrong shape) raises StateSchemaError
# ---------------------------------------------------------------------------

def test_schema_mismatch_raises_state_schema_error(tmp_path: Path) -> None:
    """A file containing valid JSON whose entries do not match the
    AgentState model must raise so an upstream writer bug is loud."""
    agents_path = tmp_path / "agents.json"
    # Top-level object instead of array fails the array check.
    agents_path.write_text(json.dumps({"agent_id": "AGENT-01"}), encoding="utf-8")
    with pytest.raises(StateSchemaError):
        read_agents(path=agents_path)

    # Top-level array but entry missing required fields fails the model check.
    agents_path.write_text(json.dumps([{"agent_id": "AGENT-01"}]), encoding="utf-8")
    with pytest.raises(StateSchemaError):
        read_agents(path=agents_path)


# ---------------------------------------------------------------------------
# 6. Lock contention surfaces as StateLockError when timeout is exceeded
# ---------------------------------------------------------------------------

def test_advisory_lock_contention_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If a writer holds the advisory lock and a competitor times out
    waiting, the competitor must raise StateLockError rather than
    block forever or silently overwrite."""
    # Force the lock acquire timeout to a tiny value so the test runs
    # quickly without flaking.
    monkeypatch.setattr(state_store, "LOCK_ACQUIRE_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(state_store, "LOCK_RETRY_INTERVAL_SECONDS", 0.02)

    target = tmp_path / "queue.json"
    target.write_text("[]", encoding="utf-8")

    # Hold the OS lock open in the main thread, then try to acquire it
    # again from another. The second acquisition must raise.
    holder = open(target, "r+", encoding="utf-8")
    try:
        with _advisory_lock(holder):
            error_box: list[Exception] = []

            def _competitor() -> None:
                try:
                    competitor = open(target, "r+", encoding="utf-8")
                    try:
                        with _advisory_lock(competitor):
                            pass  # pragma: no cover - should not reach
                    finally:
                        competitor.close()
                except Exception as exc:
                    error_box.append(exc)

            thread = threading.Thread(target=_competitor)
            thread.start()
            thread.join(timeout=2.0)

            assert error_box, "competitor should have raised StateLockError"
            assert isinstance(error_box[0], StateLockError)
    finally:
        holder.close()


# ---------------------------------------------------------------------------
# 7. append_approval_entry serialises correctly under lock
# ---------------------------------------------------------------------------

def test_append_approval_entry_round_trip(tmp_path: Path) -> None:
    """Appending two entries must preserve order and round-trip cleanly."""
    queue_path = tmp_path / "approval_queue.json"
    queue_path.write_text("[]", encoding="utf-8")

    append_approval_entry(_make_queue_entry("AGENT-01"), path=queue_path)
    append_approval_entry(_make_queue_entry("AGENT-02"), path=queue_path)

    entries = read_approval_queue(path=queue_path)
    assert [e.agent_id for e in entries] == ["AGENT-01", "AGENT-02"]


# ---------------------------------------------------------------------------
# 8. bootstrap_state_files seeds empty arrays without overwriting existing data
# ---------------------------------------------------------------------------

def test_bootstrap_state_files_idempotent(tmp_path: Path) -> None:
    """First call creates empty arrays; second call must not overwrite
    pre-existing content."""
    agents_path = tmp_path / "agents.json"
    queue_path = tmp_path / "approval_queue.json"

    bootstrap_state_files(agents_path=agents_path, queue_path=queue_path)
    assert agents_path.read_text(encoding="utf-8") == "[]"
    assert queue_path.read_text(encoding="utf-8") == "[]"

    # Pre-fill with content; bootstrap must leave it alone the second time.
    write_agents([_make_agent("AGENT-99")], path=agents_path)
    bootstrap_state_files(agents_path=agents_path, queue_path=queue_path)

    loaded = read_agents(path=agents_path)
    assert len(loaded) == 1 and loaded[0].agent_id == "AGENT-99"


# ---------------------------------------------------------------------------
# 9. write_approval_queue replaces the file atomically
# ---------------------------------------------------------------------------

def test_write_approval_queue_replaces_contents(tmp_path: Path) -> None:
    """Calling write_approval_queue must replace the file rather than
    append, so a caller that wants append semantics uses
    append_approval_entry explicitly."""
    queue_path = tmp_path / "approval_queue.json"
    write_approval_queue(
        [_make_queue_entry("AGENT-01"), _make_queue_entry("AGENT-02")],
        path=queue_path,
    )
    assert len(read_approval_queue(path=queue_path)) == 2

    # Replace with a single entry.
    write_approval_queue([_make_queue_entry("AGENT-03")], path=queue_path)
    entries = read_approval_queue(path=queue_path)
    assert len(entries) == 1 and entries[0].agent_id == "AGENT-03"
