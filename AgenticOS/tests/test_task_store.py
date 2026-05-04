# test_task_store.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Verifies the canonical agentic-os task runtime store: schema
#          validation, lock ownership, readiness recovery, append-only logs,
#          and snapshot writes.

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from AgenticOS.models import AgenticTask, TaskStatus
from AgenticOS.task_store import (
    TaskConflictError,
    TaskSchemaError,
    bootstrap_task_runtime,
    claim_task,
    complete_task,
    fail_task,
    read_locks,
    read_task,
    read_tasks,
    recover_orphaned_tasks,
    refresh_task_readiness,
    release_task_lock,
    update_task_checkpoint,
    validate_locks,
    write_snapshot,
    write_task,
)


def _make_task(
    task_id: str = "task-001",
    status: TaskStatus = TaskStatus.PENDING,
    dependencies: list[str] | None = None,
) -> AgenticTask:
    now = datetime.now(timezone.utc)
    return AgenticTask(
        id=task_id,
        title=f"Task {task_id}",
        status=status,
        assigned_to=None,
        dependencies=dependencies or [],
        priority=1,
        locked_by=None,
        created_at=now,
        updated_at=now,
        checkpoints=[],
        output=None,
    )


def test_schema_validation_rejects_invalid_task(tmp_path: Path) -> None:
    paths = bootstrap_task_runtime(tmp_path)
    (paths.tasks_dir / "task-bad.json").write_text(
        json.dumps({"id": "task-bad"}),
        encoding="utf-8",
    )

    with pytest.raises(TaskSchemaError):
        read_tasks(tmp_path)


def test_claim_and_release_task_lock(tmp_path: Path) -> None:
    write_task(_make_task(), tmp_path)

    claimed = claim_task("task-001", "agent-terminal-3", tmp_path)
    assert claimed.status == TaskStatus.IN_PROGRESS
    assert claimed.locked_by == "agent-terminal-3"
    assert read_locks(tmp_path)[0].agent_id == "agent-terminal-3"

    with pytest.raises(TaskConflictError):
        claim_task("task-001", "agent-terminal-4", tmp_path)

    released = release_task_lock("task-001", "agent-terminal-3", tmp_path)
    assert released.locked_by is None
    assert read_locks(tmp_path) == []


def test_release_fails_for_non_owner(tmp_path: Path) -> None:
    write_task(_make_task(), tmp_path)
    claim_task("task-001", "agent-terminal-3", tmp_path)

    with pytest.raises(TaskConflictError):
        release_task_lock("task-001", "agent-terminal-4", tmp_path)


def test_orphaned_in_progress_task_recovers_to_pending(tmp_path: Path) -> None:
    task = _make_task(status=TaskStatus.IN_PROGRESS)
    task.locked_by = "agent-terminal-3"
    write_task(task, tmp_path)

    events = recover_orphaned_tasks(tmp_path)

    assert events == ["RECOVERED orphaned task task-001"]
    assert read_task("task-001", tmp_path).status == TaskStatus.PENDING
    assert read_task("task-001", tmp_path).locked_by is None


def test_dependency_readiness_blocks_and_unblocks(tmp_path: Path) -> None:
    write_task(_make_task("task-001", status=TaskStatus.PENDING), tmp_path)
    write_task(
        _make_task(
            "task-002",
            status=TaskStatus.PENDING,
            dependencies=["task-001"],
        ),
        tmp_path,
    )

    refresh_task_readiness(tmp_path)
    assert read_task("task-002", tmp_path).status == TaskStatus.BLOCKED

    claim_task("task-001", "agent-terminal-3", tmp_path)
    complete_task("task-001", {"result": "done"}, tmp_path)

    assert read_task("task-002", tmp_path).status == TaskStatus.PENDING


def test_checkpoint_complete_and_fail_require_active_lock(tmp_path: Path) -> None:
    write_task(_make_task(), tmp_path)

    with pytest.raises(TaskConflictError):
        update_task_checkpoint("task-001", "not claimed", tmp_path)

    claim_task("task-001", "agent-terminal-3", tmp_path)
    updated = update_task_checkpoint("task-001", {"message": "halfway"}, tmp_path)
    assert updated.checkpoints[-1]["message"] == "halfway"

    completed = complete_task("task-001", {"result": "ok"}, tmp_path)
    assert completed.status == TaskStatus.COMPLETE
    assert read_locks(tmp_path) == []


def test_fail_task_writes_error_context_and_releases_lock(tmp_path: Path) -> None:
    write_task(_make_task(), tmp_path)
    claim_task("task-001", "agent-terminal-3", tmp_path)

    failed = fail_task("task-001", {"error": "boom"}, tmp_path)

    assert failed.status == TaskStatus.FAILED
    assert failed.output == {"error": "boom"}
    assert read_locks(tmp_path) == []


def test_malformed_lock_file_surfaces_schema_error(tmp_path: Path) -> None:
    paths = bootstrap_task_runtime(tmp_path)
    (paths.locks_dir / "task-001.lock").write_text("{bad json", encoding="utf-8")

    with pytest.raises(TaskSchemaError):
        read_locks(tmp_path)


def test_validate_locks_removes_stale_lock(tmp_path: Path) -> None:
    paths = bootstrap_task_runtime(tmp_path)
    (paths.locks_dir / "task-missing.lock").write_text(
        json.dumps(
            {
                "task_id": "task-missing",
                "agent_id": "agent-terminal-3",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ),
        encoding="utf-8",
    )

    events = validate_locks(tmp_path)

    assert events == ["REMOVED stale lock for missing task task-missing"]
    assert read_locks(tmp_path) == []


def test_snapshot_and_logs_are_written(tmp_path: Path) -> None:
    write_task(_make_task(), tmp_path)
    snapshot = write_snapshot(tmp_path)

    paths = bootstrap_task_runtime(tmp_path)
    parsed = json.loads(paths.snapshot_json.read_text(encoding="utf-8"))
    assert parsed["tasks"][0]["id"] == "task-001"
    assert snapshot.tasks[0].id == "task-001"

    claim_task("task-001", "agent-terminal-3", tmp_path)
    events_log = paths.events_log.read_text(encoding="utf-8")
    assert "CLAIMED task-001 by agent-terminal-3" in events_log
