# test_session_bridge.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Coverage for session_bridge.py. Patches scan_active_sessions
#          and the state_store read/write functions so we never touch
#          the real filesystem of the developer's workstation.

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from AgenticOS.models import (
    AgentDomain,
    AgentState,
    AgentStatus,
    DiscoveredSession,
)
from AgenticOS.session_bridge import (
    _apply_classifications,
    _detect_transitions,
    _merge_agents,
    _run_one_cycle,
    _session_to_agent_state,
    _translate_status,
    run_bridge_loop,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_session(
    session_id: str,
    plugin_id: str = "plugin-a",
    status: str = "in_progress",
    sub_agent_count: int = 1,
    timeline_tail: list[dict] | None = None,
) -> DiscoveredSession:
    return DiscoveredSession(
        session_id=session_id,
        plugin_id=plugin_id,
        objective=f"do {session_id}",
        status=status,
        last_active_at=datetime.now(timezone.utc),
        mission_state_path=Path(f"/tmp/{session_id}/mission-state.json"),
        output_dir=None,
        sub_agent_count=sub_agent_count,
        timeline_tail=timeline_tail or [],
    )


def _manual_agent(agent_id: str = "MANUAL-01") -> AgentState:
    return AgentState(
        agent_id=agent_id,
        domain=AgentDomain.SOFTWARE_ENG,
        task="manual task",
        stage_label="stage 1",
        stage=1,
        total_stages=1,
        progress_pct=0,
        status=AgentStatus.ACTIVE,
        context_pct_used=0,
        updated_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# _translate_status
# ---------------------------------------------------------------------------

def test_translate_status_known_values():
    assert _translate_status("in_progress") == AgentStatus.ACTIVE
    assert _translate_status("complete") == AgentStatus.COMPLETE
    assert _translate_status("error") == AgentStatus.ERROR


def test_translate_status_unknown_falls_back_to_active():
    assert _translate_status("brand_new_status") == AgentStatus.ACTIVE


# ---------------------------------------------------------------------------
# _session_to_agent_state
# ---------------------------------------------------------------------------

def test_session_to_agent_state_first_observation():
    session = _fake_session("session-x")
    agent = _session_to_agent_state(session, previous=None)
    assert agent.agent_id == "plugin-a/session-x"
    assert agent.status == AgentStatus.ACTIVE
    assert agent.discovered_session_id == "session-x"
    assert agent.last_progress_at == session.last_active_at
    assert agent.sub_agent_count == 1


def test_session_to_agent_state_preserves_previous_fields():
    # When the previous AgentState had a domain, stage, error_msg, etc.,
    # the new translation must preserve them.
    session = _fake_session("session-x")
    previous = AgentState(
        agent_id="plugin-a/session-x",
        domain=AgentDomain.GAME_DEV,
        task="old task",
        stage_label="phase 3",
        stage=3,
        total_stages=5,
        progress_pct=60,
        status=AgentStatus.ACTIVE,
        context_pct_used=25,
        error_msg=None,
        updated_at=datetime.now(timezone.utc),
        discovered_session_id="session-x",
    )
    agent = _session_to_agent_state(session, previous=previous)
    assert agent.domain == AgentDomain.GAME_DEV
    assert agent.stage == 3
    assert agent.total_stages == 5
    assert agent.progress_pct == 60
    assert agent.context_pct_used == 25
    assert agent.stage_label == "phase 3"


# ---------------------------------------------------------------------------
# _merge_agents
# ---------------------------------------------------------------------------

def test_merge_preserves_manual_agents():
    manual = _manual_agent()
    discovered = [_fake_session("session-x")]
    merged = _merge_agents([manual], discovered)
    # First entry must be the manual agent (sorted before discovered).
    assert merged[0].agent_id == "MANUAL-01"
    assert merged[0].discovered_session_id is None
    # Then comes the discovered one.
    assert any(a.discovered_session_id == "session-x" for a in merged)


def test_merge_upserts_discovered_agents():
    # Existing AgentState for the same session_id should be replaced
    # with the latest values rather than duplicated.
    existing = AgentState(
        agent_id="plugin-a/session-x",
        domain=AgentDomain.GENERAL,
        task="old objective",
        stage_label="Discovered Session",
        stage=1,
        total_stages=1,
        progress_pct=0,
        status=AgentStatus.ACTIVE,
        context_pct_used=0,
        updated_at=datetime.now(timezone.utc) - timedelta(seconds=120),
        discovered_session_id="session-x",
    )
    discovered = [_fake_session("session-x")]
    merged = _merge_agents([existing], discovered)
    # Exactly one row keyed by session-x.
    matching = [a for a in merged if a.discovered_session_id == "session-x"]
    assert len(matching) == 1
    assert matching[0].task == "do session-x"


# ---------------------------------------------------------------------------
# _apply_classifications
# ---------------------------------------------------------------------------

def test_apply_classifications_marks_stuck():
    session = _fake_session("session-x")
    agent = _session_to_agent_state(session, previous=None)
    # Backdate progress so the stuck threshold is crossed.
    agent.last_progress_at = datetime.now(timezone.utc) - timedelta(seconds=500)
    _apply_classifications(agent, [session], now=datetime.now(timezone.utc))
    assert agent.is_stuck is True


def test_apply_classifications_marks_looping():
    timeline = [
        {"kind": "tool_use", "agent": "AGENT-01"} for _ in range(5)
    ]
    session = _fake_session("session-x", timeline_tail=timeline)
    agent = _session_to_agent_state(session, previous=None)
    _apply_classifications(agent, [session], now=datetime.now(timezone.utc))
    assert agent.is_looping is True


def test_apply_classifications_detects_silent_failure():
    session = _fake_session("session-x", status="in_progress", sub_agent_count=0)
    agent = _session_to_agent_state(session, previous=None)
    _apply_classifications(agent, [session], now=datetime.now(timezone.utc))
    assert agent.error_msg is not None
    assert "Silent failure" in agent.error_msg


# ---------------------------------------------------------------------------
# _detect_transitions
# ---------------------------------------------------------------------------

def test_detect_transitions_added_agent():
    new = _session_to_agent_state(_fake_session("new-one"), previous=None)
    events = _detect_transitions(last_known={}, merged=[new])
    assert any(e["kind"] == "added" for e in events)


def test_detect_transitions_status_change():
    prev_session = _fake_session("session-x", status="in_progress")
    prev_agent = _session_to_agent_state(prev_session, previous=None)
    last_known = {"session-x": prev_agent}

    completed_session = _fake_session("session-x", status="complete")
    new_agent = _session_to_agent_state(completed_session, previous=prev_agent)

    events = _detect_transitions(last_known, [new_agent])
    assert any(e["kind"] == "status_changed" for e in events)


def test_detect_transitions_removed_agent():
    prev_session = _fake_session("session-x")
    prev_agent = _session_to_agent_state(prev_session, previous=None)
    last_known = {"session-x": prev_agent}
    events = _detect_transitions(last_known, merged=[])
    assert any(e["kind"] == "removed" for e in events)


# ---------------------------------------------------------------------------
# _run_one_cycle (integration-light)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_one_cycle_writes_merged_state(tmp_path, monkeypatch):
    # Stub scan + state_store so the cycle hits a tmp_path agents.json.
    agents_path = tmp_path / "agents.json"
    agents_path.write_text("[]", encoding="utf-8")

    fake_session = _fake_session("session-x")

    monkeypatch.setattr(
        "AgenticOS.session_bridge.scan_active_sessions",
        lambda: [fake_session],
    )
    # Patch the read/write to use tmp_path so we never touch real state.
    from AgenticOS import state_store as _store

    monkeypatch.setattr(
        "AgenticOS.session_bridge.read_agents",
        lambda _path=None: _store.read_agents(agents_path),
    )
    monkeypatch.setattr(
        "AgenticOS.session_bridge.write_agents",
        lambda agents, _path=None: _store.write_agents(agents, agents_path),
    )

    last_known: dict[str, AgentState] = {}
    await _run_one_cycle(last_known)

    written = _store.read_agents(agents_path)
    assert len(written) == 1
    assert written[0].discovered_session_id == "session-x"
    # last_known should now contain the agent for the next cycle.
    assert "session-x" in last_known


# ---------------------------------------------------------------------------
# run_bridge_loop -- integration smoke test (one tick + stop)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_bridge_loop_responds_to_stop_event(tmp_path, monkeypatch):
    # Configure fakes that produce nothing so the loop body is cheap.
    monkeypatch.setattr(
        "AgenticOS.session_bridge.scan_active_sessions",
        lambda: [],
    )
    monkeypatch.setattr(
        "AgenticOS.session_bridge.read_agents",
        lambda _path=None: [],
    )
    monkeypatch.setattr(
        "AgenticOS.session_bridge.write_agents",
        lambda agents, _path=None: None,
    )

    stop = asyncio.Event()
    task = asyncio.create_task(run_bridge_loop(stop, interval_s=0.05))

    # Let it tick a few times then ask it to stop.
    await asyncio.sleep(0.15)
    stop.set()

    # The loop must exit promptly. 0.5s is generous for CI.
    await asyncio.wait_for(task, timeout=0.5)
