# test_state_manager.py
# Marcus Daley — 2026-05-01 — Unit tests for workflow state manager

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from state_manager import (
    WorkflowState,
    PhaseStatus,
    detect_resume_point,
    load_state,
    save_state,
    mark_phase_complete,
    mark_phase_failed,
)


@pytest.fixture
def tmp_state_dir(tmp_path):
    return tmp_path


def test_detect_resume_point_flag_wins(tmp_state_dir):
    (tmp_state_dir / "workflow_state.json").write_text('{"current_phase": "execution"}')
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag="planning")
    assert result == "planning"


def test_detect_resume_point_from_state(tmp_state_dir):
    state = {
        "workflow_id": "test-123",
        "task": "test",
        "created_at": "2026-05-01T00:00:00+00:00",
        "updated_at": "2026-05-01T00:00:00+00:00",
        "phases": {
            "brainstorm": {"status": "complete", "completed_at": None, "failed_at": None, "failure_reason": None},
            "planning": {"status": "incomplete", "completed_at": None, "failed_at": None, "failure_reason": None},
            "execution": {"status": "not_started", "completed_at": None, "failed_at": None, "failure_reason": None},
            "verification": {"status": "not_started", "completed_at": None, "failed_at": None, "failure_reason": None},
        },
    }
    (tmp_state_dir / "workflow_state.json").write_text(json.dumps(state))
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "planning"


def test_detect_resume_point_from_phases_json(tmp_state_dir):
    (tmp_state_dir / "phases.json").write_text('{"phases": []}')
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "execution"


def test_detect_resume_point_from_spec_md(tmp_state_dir):
    (tmp_state_dir / "spec.md").write_text("# spec")
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "planning"


def test_detect_resume_point_default(tmp_state_dir):
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "brainstorm"


def test_save_and_load_state(tmp_state_dir):
    state = WorkflowState(
        workflow_id="abc-123",
        task="build auth system",
        phases={
            "brainstorm": PhaseStatus(status="complete"),
            "planning": PhaseStatus(status="incomplete"),
            "execution": PhaseStatus(status="not_started"),
            "verification": PhaseStatus(status="not_started"),
        },
    )
    save_state(state, state_dir=tmp_state_dir)
    loaded = load_state(state_dir=tmp_state_dir)
    assert loaded.workflow_id == "abc-123"
    assert loaded.phases["brainstorm"].status == "complete"


def test_mark_phase_complete(tmp_state_dir):
    state = WorkflowState(
        workflow_id="abc-123",
        task="test task",
        phases={
            "brainstorm": PhaseStatus(status="in_progress"),
            "planning": PhaseStatus(status="not_started"),
            "execution": PhaseStatus(status="not_started"),
            "verification": PhaseStatus(status="not_started"),
        },
    )
    save_state(state, state_dir=tmp_state_dir)
    updated = mark_phase_complete("brainstorm", state_dir=tmp_state_dir)
    assert updated.phases["brainstorm"].status == "complete"
    assert updated.phases["brainstorm"].completed_at is not None


def test_mark_phase_failed(tmp_state_dir):
    state = WorkflowState(
        workflow_id="abc-123",
        task="test task",
        phases={
            "brainstorm": PhaseStatus(status="in_progress"),
            "planning": PhaseStatus(status="not_started"),
            "execution": PhaseStatus(status="not_started"),
            "verification": PhaseStatus(status="not_started"),
        },
    )
    save_state(state, state_dir=tmp_state_dir)
    updated = mark_phase_failed("brainstorm", reason="spec unclear", state_dir=tmp_state_dir)
    assert updated.phases["brainstorm"].status == "failed"
    assert updated.phases["brainstorm"].failure_reason == "spec unclear"


def test_detect_resume_point_all_complete_returns_complete(tmp_state_dir):
    """All phases complete — should return 'complete', not restart brainstorm."""
    state = WorkflowState(
        workflow_id="abc-123",
        task="test task",
        phases={p: PhaseStatus(status="complete") for p in ["brainstorm", "planning", "execution", "verification"]},
    )
    save_state(state, state_dir=tmp_state_dir)
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "complete"


def test_workflow_state_coerces_dict_phases():
    """WorkflowState.__post_init__ should coerce plain dict phases to PhaseStatus."""
    state = WorkflowState(
        workflow_id="abc-123",
        task="test",
        phases={"brainstorm": {"status": "not_started", "completed_at": None, "failed_at": None, "failure_reason": None}},
    )
    assert isinstance(state.phases["brainstorm"], PhaseStatus)
