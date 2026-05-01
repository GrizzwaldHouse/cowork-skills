# state_manager.py
# Marcus Daley — 2026-05-01 — Workflow state read/write and resume detection

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PHASE_ORDER = ["brainstorm", "planning", "execution", "verification"]
STATE_FILE = "workflow_state.json"
INCOMPLETE_STATUSES = {"not_started", "in_progress", "failed", "incomplete"}


@dataclass
class PhaseStatus:
    status: str  # not_started | in_progress | incomplete | complete | failed
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None


@dataclass
class WorkflowState:
    workflow_id: str
    task: str
    phases: dict  # phase_name -> PhaseStatus  (coerced in __post_init__)
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())

    def __post_init__(self):
        self.phases = {
            k: PhaseStatus(**v) if isinstance(v, dict) else v
            for k, v in self.phases.items()
        }

    @classmethod
    def new(cls, task: str) -> "WorkflowState":
        return cls(
            workflow_id=str(uuid.uuid4()),
            task=task,
            phases={p: PhaseStatus(status="not_started") for p in PHASE_ORDER},
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_path(state_dir: Path) -> Path:
    return state_dir / STATE_FILE


def save_state(state: WorkflowState, state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    state.updated_at = _now()
    data = asdict(state)
    tmp = _state_path(state_dir).with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(_state_path(state_dir))


def load_state(state_dir: Path) -> WorkflowState:
    data = json.loads(_state_path(state_dir).read_text(encoding="utf-8"))
    phases = {k: PhaseStatus(**v) for k, v in data["phases"].items()}
    return WorkflowState(
        workflow_id=data["workflow_id"],
        task=data["task"],
        phases=phases,
        created_at=data.get("created_at", _now()),
        updated_at=data.get("updated_at", _now()),
    )


def detect_resume_point(state_dir: Path, from_flag: Optional[str]) -> str:
    """Return the phase name to start execution from."""
    if from_flag:
        return from_flag

    state_file = _state_path(state_dir)
    if state_file.exists():
        state = load_state(state_dir)
        for phase in PHASE_ORDER:
            if state.phases[phase].status in INCOMPLETE_STATUSES:
                return phase
        return "complete"  # all phases done — workflow is finished

    if (state_dir / "phases.json").exists():
        return "execution"

    if (state_dir / "spec.md").exists():
        return "planning"

    return "brainstorm"


def mark_phase_complete(phase: str, state_dir: Path) -> WorkflowState:
    state = load_state(state_dir)
    state.phases[phase].status = "complete"
    state.phases[phase].completed_at = _now()
    save_state(state, state_dir)
    return state


def mark_phase_failed(phase: str, reason: str, state_dir: Path) -> WorkflowState:
    state = load_state(state_dir)
    state.phases[phase].status = "failed"
    state.phases[phase].failed_at = _now()
    state.phases[phase].failure_reason = reason
    save_state(state, state_dir)
    return state
