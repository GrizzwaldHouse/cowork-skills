# Autonomous Workflow Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a spec-driven, phase-based workflow orchestration skill that bootstraps a runnable runtime, extends the ralph loop with hybrid multi-role voting and phase isolation, and broadcasts one-way events to AgenticOS.

**Architecture:** Skill entry point (`SKILL.md`) routes to phase reference files; Python scripts (`state_manager.py`, `agenticos_push.py`, `bootstrap.py`) handle all runtime state and I/O; AgenticOS gains a new `POST /events` endpoint that appends to a watched `workflow_events.json` sidecar so the existing WebSocket broadcaster surfaces workflow progress to the React HUD.

**Tech Stack:** Python 3.10+ (stdlib only for scripts), Markdown (skill files), FastAPI (AgenticOS endpoint addition), pytest (script unit tests), JSON (state files)

---

## File Map

### New files to create

| Path | Responsibility |
|------|---------------|
| `skills/ai-agents/autonomous-workflow/SKILL.md` | Entry point: triggers, adaptive resume logic, argument parsing, phase routing |
| `skills/ai-agents/autonomous-workflow/references/phase-brainstorm.md` | GStack 4-role simulation protocol |
| `skills/ai-agents/autonomous-workflow/references/phase-planning.md` | GSD decomposition → `phases.json` |
| `skills/ai-agents/autonomous-workflow/references/phase-execution.md` | TDD execution contract per phase |
| `skills/ai-agents/autonomous-workflow/references/phase-verification.md` | Automated review + security gate |
| `skills/ai-agents/autonomous-workflow/references/voting-protocol.md` | Hybrid voting rules and thresholds |
| `skills/ai-agents/autonomous-workflow/references/agenticos-events.md` | Event push contract and payload schemas |
| `skills/ai-agents/autonomous-workflow/templates/workflow.md` | Workflow markdown schema template |
| `skills/ai-agents/autonomous-workflow/templates/task.md` | Task markdown schema template |
| `skills/ai-agents/autonomous-workflow/templates/skill-template.md` | Skill markdown schema template |
| `skills/ai-agents/autonomous-workflow/scripts/state_manager.py` | Read/write `workflow_state.json`, detect resume point |
| `skills/ai-agents/autonomous-workflow/scripts/agenticos_push.py` | Fire-and-forget HTTP POST to AgenticOS `/events` |
| `skills/ai-agents/autonomous-workflow/scripts/bootstrap.py` | Generate runtime scaffold from templates on first invoke |
| `skills/ai-agents/autonomous-workflow/state/.gitkeep` | Placeholder so `state/` is tracked but contents are gitignored |
| `tests/ai-agents/autonomous-workflow/test_state_manager.py` | Unit tests for state_manager.py |
| `tests/ai-agents/autonomous-workflow/test_agenticos_push.py` | Unit tests for agenticos_push.py |
| `tests/ai-agents/autonomous-workflow/test_bootstrap.py` | Unit tests for bootstrap.py |

### Files to modify

| Path | Change |
|------|--------|
| `AgenticOS/agentic_server.py` | Add `POST /events` endpoint + workflow events watcher |
| `.gitignore` | Add `skills/ai-agents/autonomous-workflow/state/*.json` |

---

## Task 1: State Manager — Core Read/Write

**Files:**
- Create: `skills/ai-agents/autonomous-workflow/scripts/state_manager.py`
- Create: `tests/ai-agents/autonomous-workflow/test_state_manager.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# tests/ai-agents/autonomous-workflow/test_state_manager.py
# Marcus Daley — 2026-05-01 — Unit tests for workflow state manager

import json
import pytest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).parents[3] / "skills" / "ai-agents" / "autonomous-workflow" / "scripts"))

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
    """--from flag overrides everything, even existing state."""
    (tmp_state_dir / "workflow_state.json").write_text('{"current_phase": "execution"}')
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag="planning")
    assert result == "planning"


def test_detect_resume_point_from_state(tmp_state_dir):
    """Resumes from last incomplete phase when state file exists."""
    state = {
        "workflow_id": "test-123",
        "phases": {
            "brainstorm": {"status": "complete"},
            "planning": {"status": "incomplete"},
            "execution": {"status": "not_started"},
            "verification": {"status": "not_started"},
        },
    }
    (tmp_state_dir / "workflow_state.json").write_text(json.dumps(state))
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "planning"


def test_detect_resume_point_from_phases_json(tmp_state_dir):
    """Enters execution when phases.json exists but no state."""
    (tmp_state_dir / "phases.json").write_text('{"phases": []}')
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "execution"


def test_detect_resume_point_from_spec_md(tmp_state_dir):
    """Enters planning when spec.md exists but no phases.json or state."""
    (tmp_state_dir / "spec.md").write_text("# spec")
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "planning"


def test_detect_resume_point_default(tmp_state_dir):
    """Starts at brainstorm when nothing exists."""
    result = detect_resume_point(state_dir=tmp_state_dir, from_flag=None)
    assert result == "brainstorm"


def test_save_and_load_state(tmp_state_dir):
    """Round-trip save/load preserves all fields."""
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
    """Marking a phase complete updates status and sets completed_at."""
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
    """Marking a phase failed records reason and sets failed_at."""
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
```

- [ ] **Step 2: Run tests — verify they all fail with ImportError**

```bash
cd "C:/ClaudeSkills"
python -m pytest tests/ai-agents/autonomous-workflow/test_state_manager.py -v
```

Expected: `ImportError: No module named 'state_manager'`

- [ ] **Step 3: Create state_manager.py**

```python
# skills/ai-agents/autonomous-workflow/scripts/state_manager.py
# Marcus Daley — 2026-05-01 — Workflow state read/write and resume detection

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PHASE_ORDER = ["brainstorm", "planning", "execution", "verification"]
STATE_FILE = "workflow_state.json"


@dataclass
class PhaseStatus:
    status: str  # not_started | in_progress | complete | failed
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None


@dataclass
class WorkflowState:
    workflow_id: str
    task: str
    phases: dict  # phase_name -> PhaseStatus
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())

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
            if state.phases[phase].status in ("not_started", "in_progress", "failed", "incomplete"):
                return phase
        return "brainstorm"

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
```

- [ ] **Step 4: Run tests — verify all pass**

```bash
cd "C:/ClaudeSkills"
python -m pytest tests/ai-agents/autonomous-workflow/test_state_manager.py -v
```

Expected: 8 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add skills/ai-agents/autonomous-workflow/scripts/state_manager.py tests/ai-agents/autonomous-workflow/test_state_manager.py
git commit -m "feat(workflow): add state_manager with adaptive resume detection"
```

---

## Task 2: AgenticOS Push — Fire-and-Forget HTTP

**Files:**
- Create: `skills/ai-agents/autonomous-workflow/scripts/agenticos_push.py`
- Create: `tests/ai-agents/autonomous-workflow/test_agenticos_push.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ai-agents/autonomous-workflow/test_agenticos_push.py
# Marcus Daley — 2026-05-01 — Unit tests for AgenticOS event push

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[3] / "skills" / "ai-agents" / "autonomous-workflow" / "scripts"))

from agenticos_push import push_event, build_event_payload, EventType


def test_build_event_payload_workflow_started():
    payload = build_event_payload(
        event_type=EventType.WORKFLOW_STARTED,
        workflow_id="abc-123",
        extra={"task": "build auth system"},
    )
    assert payload["event"] == "workflow.started"
    assert payload["workflow_id"] == "abc-123"
    assert payload["task"] == "build auth system"
    assert "timestamp" in payload


def test_build_event_payload_phase_complete():
    payload = build_event_payload(
        event_type=EventType.PHASE_COMPLETE,
        workflow_id="abc-123",
        extra={"phase": "planning"},
    )
    assert payload["event"] == "workflow.phase_complete"
    assert payload["phase"] == "planning"


def test_push_event_success(requests_mock):
    requests_mock.post("http://localhost:8000/events", json={"ok": True}, status_code=200)
    result = push_event(
        event_type=EventType.WORKFLOW_STARTED,
        workflow_id="abc-123",
        base_url="http://localhost:8000",
        extra={"task": "test"},
    )
    assert result is True


def test_push_event_silent_failure_on_connection_error():
    """Never raises — AgenticOS unavailability must not block the workflow."""
    with patch("agenticos_push.requests") as mock_requests:
        mock_requests.post.side_effect = Exception("connection refused")
        result = push_event(
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id="abc-123",
            base_url="http://localhost:8000",
            extra={},
        )
    assert result is False


def test_push_event_silent_failure_on_timeout():
    """Timeout must not raise."""
    with patch("agenticos_push.requests") as mock_requests:
        import requests as req_lib
        mock_requests.post.side_effect = req_lib.exceptions.Timeout()
        result = push_event(
            event_type=EventType.PHASE_COMPLETE,
            workflow_id="abc-123",
            base_url="http://localhost:8000",
            extra={"phase": "brainstorm"},
        )
    assert result is False
```

- [ ] **Step 2: Run tests — verify they fail with ImportError**

```bash
cd "C:/ClaudeSkills"
python -m pytest tests/ai-agents/autonomous-workflow/test_agenticos_push.py -v
```

Expected: `ImportError: No module named 'agenticos_push'`

- [ ] **Step 3: Create agenticos_push.py**

```python
# skills/ai-agents/autonomous-workflow/scripts/agenticos_push.py
# Marcus Daley — 2026-05-01 — Fire-and-forget event broadcast to AgenticOS

import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import requests

_logger = logging.getLogger(__name__)
_TIMEOUT_S = 2


class EventType(str, Enum):
    WORKFLOW_STARTED = "workflow.started"
    PHASE_STARTED = "workflow.phase_started"
    PHASE_COMPLETE = "workflow.phase_complete"
    VOTE_CAST = "workflow.vote_cast"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_FAILED = "workflow.failed"


def build_event_payload(
    event_type: EventType,
    workflow_id: str,
    extra: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event": event_type.value,
        "workflow_id": workflow_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


def push_event(
    event_type: EventType,
    workflow_id: str,
    base_url: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> bool:
    """POST event to AgenticOS. Returns True on success, False on any failure.
    Never raises — AgenticOS unavailability must not block workflow execution."""
    url = (base_url or os.environ.get("AGENTICOS_URL", "http://localhost:8000")) + "/events"
    payload = build_event_payload(event_type, workflow_id, extra or {})
    try:
        resp = requests.post(url, json=payload, timeout=_TIMEOUT_S)
        resp.raise_for_status()
        return True
    except Exception as exc:
        _logger.debug("AgenticOS push failed (non-blocking): %s", exc)
        return False
```

- [ ] **Step 4: Install requests if not present, then run tests**

```bash
pip show requests || pip install requests
cd "C:/ClaudeSkills"
python -m pytest tests/ai-agents/autonomous-workflow/test_agenticos_push.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add skills/ai-agents/autonomous-workflow/scripts/agenticos_push.py tests/ai-agents/autonomous-workflow/test_agenticos_push.py
git commit -m "feat(workflow): add agenticos_push with fire-and-forget event broadcast"
```

---

## Task 3: Bootstrap Script — Runtime Scaffold Generator

**Files:**
- Create: `skills/ai-agents/autonomous-workflow/scripts/bootstrap.py`
- Create: `tests/ai-agents/autonomous-workflow/test_bootstrap.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ai-agents/autonomous-workflow/test_bootstrap.py
# Marcus Daley — 2026-05-01 — Unit tests for bootstrap scaffold generator

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[3] / "skills" / "ai-agents" / "autonomous-workflow" / "scripts"))

from bootstrap import scaffold_project, validate_target_path, ScaffoldError

TEMPLATES_DIR = Path(__file__).parents[3] / "skills" / "ai-agents" / "autonomous-workflow" / "templates"


def test_validate_target_path_rejects_traversal(tmp_path):
    """Path traversal attempts must raise ScaffoldError."""
    with pytest.raises(ScaffoldError, match="traversal"):
        validate_target_path(tmp_path, "../../../etc/passwd")


def test_validate_target_path_accepts_relative(tmp_path):
    result = validate_target_path(tmp_path, "my-project/workflow")
    assert result == tmp_path / "my-project" / "workflow"


def test_scaffold_creates_expected_structure(tmp_path):
    """scaffold_project creates workflows/, tasks/, skills/, orchestrator/, state/ dirs."""
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    for subdir in ["workflows", "tasks", "skills", "orchestrator", "state"]:
        assert (tmp_path / "my-project" / subdir).is_dir(), f"Missing: {subdir}/"


def test_scaffold_copies_templates(tmp_path):
    """Template files are copied into the appropriate scaffold directories."""
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    assert (tmp_path / "my-project" / "workflows" / "workflow.md").exists()
    assert (tmp_path / "my-project" / "tasks" / "task.md").exists()
    assert (tmp_path / "my-project" / "skills" / "skill-template.md").exists()


def test_scaffold_creates_initial_state_json(tmp_path):
    """state/workflow_state.json is not created by bootstrap — state/ must be empty."""
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    state_dir = tmp_path / "my-project" / "state"
    assert state_dir.is_dir()
    assert not (state_dir / "workflow_state.json").exists()


def test_scaffold_is_idempotent(tmp_path):
    """Running scaffold twice on same dir does not raise or corrupt files."""
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    assert (tmp_path / "my-project" / "workflows" / "workflow.md").exists()
```

- [ ] **Step 2: Run tests — verify ImportError**

```bash
cd "C:/ClaudeSkills"
python -m pytest tests/ai-agents/autonomous-workflow/test_bootstrap.py -v
```

Expected: `ImportError: No module named 'bootstrap'`

- [ ] **Step 3: Create bootstrap.py**

```python
# skills/ai-agents/autonomous-workflow/scripts/bootstrap.py
# Marcus Daley — 2026-05-01 — Runtime scaffold generator for autonomous-workflow

import shutil
from pathlib import Path

SCAFFOLD_DIRS = ["workflows", "tasks", "skills", "orchestrator", "state"]

TEMPLATE_MAP = {
    "workflow.md": "workflows",
    "task.md": "tasks",
    "skill-template.md": "skills",
}


class ScaffoldError(ValueError):
    pass


def validate_target_path(base: Path, relative: str) -> Path:
    """Resolve relative path under base and reject any path traversal."""
    resolved = (base / relative).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise ScaffoldError(f"Path traversal detected in: {relative!r}")
    return resolved


def scaffold_project(target_dir: Path, templates_dir: Path) -> None:
    """Create the runtime scaffold directory structure under target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)

    for subdir in SCAFFOLD_DIRS:
        (target_dir / subdir).mkdir(exist_ok=True)

    for template_file, dest_subdir in TEMPLATE_MAP.items():
        src = templates_dir / template_file
        dst = target_dir / dest_subdir / template_file
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
```

- [ ] **Step 4: Create placeholder template files so bootstrap tests can find them**

Create `skills/ai-agents/autonomous-workflow/templates/workflow.md`:

```markdown
---
# Workflow Template
# Copy this file to workflows/ and fill in each section.
---

## Workflow Name
[Name]

## Trigger Conditions
[What kicks this workflow off]

## Phase Definitions
- brainstorm
- planning
- execution
- verification

## Execution Graph
[Mermaid or ASCII diagram]

## Agent Responsibilities
[Role → phase mapping]

## State Management
[Where state files live]

## Failure Handling
[Per-phase recovery strategy]

## Security Constraints
[Auth, secret handling, file permissions]
```

Create `skills/ai-agents/autonomous-workflow/templates/task.md`:

```markdown
---
# Task Template
# Copy this file to tasks/ and fill in each section.
---

## Title
[Task name]

## Purpose
[Why this task exists]

## Inputs
- input_name: type — description

## Outputs
- output_name: type — description

## Dependencies
- [Other tasks or files that must exist first]

## Execution Steps
1. Step one
2. Step two

## Validation Rules
- [ ] Rule one
- [ ] Rule two

## Failure Conditions
- Condition → expected behavior

## Recovery Strategy
[How to resume after failure]
```

Create `skills/ai-agents/autonomous-workflow/templates/skill-template.md`:

```markdown
---
# Skill Template
# Copy this file to skills/ and fill in each section.
---

## Skill Name
[Name]

## Capability Description
[What this skill enables]

## Inputs
- input_name: type — description

## Outputs
- output_name: type — description

## Execution Contract
[Preconditions and postconditions]

## Constraints
- [Hard limits]

## Reusable Patterns
[Common usage patterns]

## Example Usage
[Concrete invocation example]
```

- [ ] **Step 5: Run tests — verify all pass**

```bash
cd "C:/ClaudeSkills"
python -m pytest tests/ai-agents/autonomous-workflow/test_bootstrap.py -v
```

Expected: 6 tests PASSED

- [ ] **Step 6: Commit**

```bash
git add skills/ai-agents/autonomous-workflow/scripts/bootstrap.py skills/ai-agents/autonomous-workflow/templates/ tests/ai-agents/autonomous-workflow/test_bootstrap.py
git commit -m "feat(workflow): add bootstrap scaffold generator and workflow/task/skill templates"
```

---

## Task 4: AgenticOS — Add POST /events Endpoint

**Files:**
- Modify: `AgenticOS/agentic_server.py`

- [ ] **Step 1: Find the handoff section end in agentic_server.py to locate insertion point**

The `POST /handoff/snapshot` endpoint is around line 865. The new `/events` endpoint goes after the last handoff route, before the WebSocket section (around line 890).

- [ ] **Step 2: Add WorkflowEvent model and POST /events route**

In `AgenticOS/agentic_server.py`, after the existing imports add the `WorkflowEvent` model, then insert the endpoint after `POST /handoff/snapshot`:

Add to imports section (near other Pydantic models):

```python
# Near top of file with other model imports
from pydantic import BaseModel as PydanticBaseModel

class WorkflowEvent(PydanticBaseModel):
    event: str
    workflow_id: str
    timestamp: str
    model_config = {"extra": "allow"}  # accept phase, task, reason etc.
```

Add endpoint after the last `/handoff` route:

```python
    # -------------------------------------------------------------------
    # Workflow events — one-way push from autonomous-workflow skill
    # -------------------------------------------------------------------

    @app.post("/events")
    async def receive_workflow_event(body: WorkflowEvent) -> JSONResponse:
        """Accept a workflow lifecycle event from the autonomous-workflow skill.
        Appends to workflow_events.json; the file watcher broadcasts the update."""
        events_file = OUTPUTS_DIR / "workflow_events.json"
        existing: list = []
        if events_file.exists():
            try:
                existing = json.loads(events_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = []
        existing.append(body.model_dump())
        tmp = events_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        tmp.replace(events_file)
        return JSONResponse({"ok": True, "event": body.event})
```

- [ ] **Step 3: Run AgenticOS server and verify endpoint responds**

```bash
cd "C:/ClaudeSkills/AgenticOS"
python -m uvicorn agentic_server:app --port 8000 --reload &
# Wait 2s for startup
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event":"workflow.started","workflow_id":"test-001","timestamp":"2026-05-01T00:00:00Z","task":"test"}'
```

Expected: `{"ok": true, "event": "workflow.started"}`

- [ ] **Step 4: Stop server, commit**

```bash
git add AgenticOS/agentic_server.py
git commit -m "feat(agenticos): add POST /events endpoint for workflow event ingestion"
```

---

## Task 5: Update .gitignore for State Files

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add state directory entries**

Open `.gitignore` and add:

```gitignore
# Autonomous workflow runtime state
skills/ai-agents/autonomous-workflow/state/*.json
skills/ai-agents/autonomous-workflow/state/*.txt
```

- [ ] **Step 2: Create state/.gitkeep**

```bash
New-Item -ItemType Directory -Force "C:\ClaudeSkills\skills\ai-agents\autonomous-workflow\state"
New-Item -ItemType File -Force "C:\ClaudeSkills\skills\ai-agents\autonomous-workflow\state\.gitkeep"
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore skills/ai-agents/autonomous-workflow/state/.gitkeep
git commit -m "chore: gitignore workflow runtime state; add state/.gitkeep"
```

---

## Task 6: Reference Files — Phase Protocols

**Files:**
- Create: `skills/ai-agents/autonomous-workflow/references/phase-brainstorm.md`
- Create: `skills/ai-agents/autonomous-workflow/references/phase-planning.md`
- Create: `skills/ai-agents/autonomous-workflow/references/phase-execution.md`
- Create: `skills/ai-agents/autonomous-workflow/references/phase-verification.md`
- Create: `skills/ai-agents/autonomous-workflow/references/voting-protocol.md`
- Create: `skills/ai-agents/autonomous-workflow/references/agenticos-events.md`

- [ ] **Step 1: Create phase-brainstorm.md**

```markdown
# Phase: Brainstorm
<!-- Marcus Daley — 2026-05-01 — GStack role simulation protocol -->

## Purpose
Clarify intent and produce a locked spec.md before any planning or code.

## Method: GStack Role Simulation (single context)
Simulate four roles sequentially. Each role reasons from its own incentives.

### CEO
- What is the business/user value?
- What does success look like in one sentence?
- What would kill this project?

### Engineer
- What is technically feasible in the first iteration?
- What are the hidden complexity traps?
- What dependencies does this introduce?

### Designer
- Who uses this and what is their mental model?
- Where will users get confused?
- What is the minimal interface that covers the use cases?

### Security
- What are the trust boundaries?
- What data is sensitive and where does it flow?
- What is the blast radius of a failure?

## Output Contract
Produces `spec.md` in the working directory with sections:
- Goal (one sentence)
- Roles and stakeholders
- Functional requirements (numbered)
- Non-functional requirements (performance, security, scale)
- Out of scope (explicit)
- Open questions (for human review)

## Completion Criteria
`spec.md` exists and contains all six sections with no "TBD" placeholders.
```

- [ ] **Step 2: Create phase-planning.md**

```markdown
# Phase: Planning
<!-- Marcus Daley — 2026-05-01 — GSD decomposition into phases.json -->

## Purpose
Decompose spec.md into discrete executable phases and produce phases.json.

## Input
`spec.md` in the working directory.

## Method: GSD Phase Decomposition
1. Read spec.md functional requirements
2. Group requirements into 3-7 cohesive phases (not more — each phase must be independently testable)
3. For each phase define: name, goal, inputs, outputs, acceptance criteria, estimated complexity (S/M/L)
4. Identify dependencies between phases (which phases must complete before others can start)
5. Order phases by dependency graph (topological sort)

## Output Contract
Produces `phases.json` in the working directory:

```json
{
  "workflow_id": "uuid",
  "spec_path": "spec.md",
  "phases": [
    {
      "id": "phase-slug",
      "name": "Human-readable name",
      "goal": "One sentence",
      "inputs": ["file or state dependency"],
      "outputs": ["file or artifact produced"],
      "acceptance_criteria": ["testable criterion"],
      "complexity": "S|M|L",
      "depends_on": ["other-phase-slug"]
    }
  ]
}
```

## Completion Criteria
`phases.json` exists, parses as valid JSON, contains at least one phase, and all phases have non-empty acceptance_criteria arrays.
```

- [ ] **Step 3: Create phase-execution.md**

```markdown
# Phase: Execution
<!-- Marcus Daley — 2026-05-01 — TDD execution contract per phase -->

## Purpose
Implement each phase from phases.json using Test-Driven Development.

## Input
`phases.json` — read the next phase with status `not_started`.

## Method: Superpower-Style TDD
For each phase in order:

1. **Write the failing test** — test the acceptance criterion directly, not the implementation
2. **Run the test — verify it fails for the right reason** (missing function, wrong output — not a syntax error)
3. **Write the minimal implementation** that makes the test pass
4. **Run the test — verify it passes**
5. **Refactor if needed** — clean up without changing behavior; re-run tests
6. **Commit** with message: `feat(<phase-id>): <what was implemented>`
7. **Update state** — call `mark_phase_complete()` in state_manager.py
8. **Push event** — call `push_event(EventType.PHASE_COMPLETE, ...)` in agenticos_push.py

## Voting Gate (before starting execution)
This phase triggers a **high-stakes voting gate** if phases.json was just generated.
Read `references/voting-protocol.md` and execute the hybrid vote before writing any code.

## Completion Criteria
All phases in phases.json have `status: complete` in workflow_state.json.
```

- [ ] **Step 4: Create phase-verification.md**

```markdown
# Phase: Verification
<!-- Marcus Daley — 2026-05-01 — Automated review and security gate -->

## Purpose
Validate that execution output is correct, performant, and secure before declaring the workflow complete.

## Input
All files produced during the execution phase.

## Method
Run three verification passes in order. All three must pass.

### Pass 1: Test Suite
```bash
python -m pytest --tb=short -q
```
Expected: 0 failures, 0 errors. Any failure blocks completion.

### Pass 2: Security Scan
Check for:
- [ ] No hardcoded secrets (grep for password, api_key, token = "...)
- [ ] No `eval()` or `exec()` on external input
- [ ] No path traversal vulnerabilities (unvalidated user paths)
- [ ] No SQL string interpolation

### Pass 3: Code Review Agent
Spawn a review subagent with this prompt:
```
Review the code produced in the execution phase against these criteria:
1. Does every public function have a clear single responsibility?
2. Are all error cases handled explicitly (no silent swallowing)?
3. Does the implementation match the acceptance criteria in phases.json?
4. Are there any race conditions or shared mutable state issues?

Return: PASS or FAIL with specific line references for any failures.
```

## Output Contract
Produces `verification_report.md` with:
- Test results (pass/fail counts)
- Security scan findings (or "clean")
- Code review verdict (PASS/FAIL + findings)
- Overall status: COMPLETE or BLOCKED

## Completion Criteria
`verification_report.md` exists and overall status is COMPLETE.
```

- [ ] **Step 5: Create voting-protocol.md**

```markdown
# Voting Protocol
<!-- Marcus Daley — 2026-05-01 — Hybrid voting rules and thresholds -->

## When to Vote

### Simulated (single context — faster, lower cost)
Use for:
- Routine implementation decisions (which library, naming, file structure)
- Minor architectural choices within a single phase
- Style and formatting decisions

Procedure: reason through each role's perspective in sequence, reach a conclusion, proceed.

### Parallel Subagents (4 concurrent — higher quality, higher cost)
Use for:
- Architecture decisions that affect 2 or more phases
- Security boundary definitions (trust boundaries, auth, data flow)
- Integration contracts with external systems (AgenticOS, MCP servers, external APIs)
- Any decision where the four roles have conflicting incentives

## Parallel Vote Procedure

1. Spawn four subagents concurrently, each with a role-scoped prompt:

**Engineer prompt:**
```
You are the Engineer on a 4-person review panel. Evaluate this decision from a technical implementation perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

**Architect prompt:**
```
You are the Architect on a 4-person review panel. Evaluate this decision from a systems design and long-term maintainability perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

**PM prompt:**
```
You are the Product Manager on a 4-person review panel. Evaluate this decision from a user value and scope perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

**Security prompt:**
```
You are the Security Engineer on a 4-person review panel. Evaluate this decision from a security and risk perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

2. Aggregate results:
   - 3 or 4 "pass" votes → PASS
   - 2 "pass" votes → tie → Architect vote is tiebreaker → Architect decides
   - 0 or 1 "pass" votes → FAIL → escalate to human

3. **Security veto:** If Security returns `fail` with a non-empty `concerns` array, the decision is BLOCKED regardless of other votes. Security concerns must be addressed before proceeding.

4. Log to `state/votes.json`:
```json
{
  "votes": [
    {
      "decision": "description",
      "timestamp": "ISO8601",
      "ballots": {
        "Engineer": {"vote": "pass", "justification": "...", "concerns": []},
        "Architect": {"vote": "pass", "justification": "...", "concerns": []},
        "PM": {"vote": "pass", "justification": "...", "concerns": []},
        "Security": {"vote": "fail", "justification": "...", "concerns": ["XSS risk"]}
      },
      "result": "BLOCKED",
      "blocking_role": "Security"
    }
  ]
}
```
```

- [ ] **Step 6: Create agenticos-events.md**

```markdown
# AgenticOS Event Contract
<!-- Marcus Daley — 2026-05-01 — Event push schema and endpoint spec -->

## Endpoint
POST `{AGENTICOS_URL}/events`
Default: `http://localhost:8000/events`
Override: `--agenticos-url` flag or `AGENTICOS_URL` environment variable.

## Behavior
- Fire-and-forget: the skill never waits for confirmation
- Silent failure: any HTTP error, timeout, or connection refusal is logged at DEBUG level and ignored
- Timeout: 2 seconds maximum per request

## Event Schemas

```json
{ "event": "workflow.started",       "workflow_id": "uuid4", "task": "string",         "timestamp": "ISO8601" }
{ "event": "workflow.phase_started", "workflow_id": "uuid4", "phase": "brainstorm|planning|execution|verification", "timestamp": "ISO8601" }
{ "event": "workflow.phase_complete","workflow_id": "uuid4", "phase": "string",         "timestamp": "ISO8601" }
{ "event": "workflow.vote_cast",     "workflow_id": "uuid4", "decision": "string",      "result": "PASS|FAIL|BLOCKED", "voters": ["Engineer","Architect","PM","Security"], "timestamp": "ISO8601" }
{ "event": "workflow.complete",      "workflow_id": "uuid4", "phases_run": 4,           "timestamp": "ISO8601" }
{ "event": "workflow.failed",        "workflow_id": "uuid4", "phase": "string",         "reason": "string", "timestamp": "ISO8601" }
```

## AgenticOS Side
Events are appended to `outputs/workflow_events.json` on the AgenticOS server.
The React HUD can poll `GET /events?since=<seq>` or subscribe via WebSocket to display workflow progress.
```

- [ ] **Step 7: Commit all reference files**

```bash
git add skills/ai-agents/autonomous-workflow/references/
git commit -m "feat(workflow): add phase reference files and voting/events protocol docs"
```

---

## Task 7: SKILL.md — Entry Point

**Files:**
- Create: `skills/ai-agents/autonomous-workflow/SKILL.md`

- [ ] **Step 1: Create SKILL.md**

```markdown
---
name: autonomous-workflow
description: >
  Spec-driven, phase-based workflow orchestration that runs projects end-to-end
  with minimal human intervention. Use this skill whenever the user says "run this
  end to end", "autonomous workflow", "execute phases", "ralph loop", "orchestrate
  this", or shares a project spec and wants it implemented without hand-holding.
  Also triggers when spec.md, phases.json, or state/workflow_state.json exist in
  the working directory. Extends the ralph loop with phase isolation, hybrid
  multi-role voting, and one-way AgenticOS event broadcasting.
---
<!-- Marcus Daley — 2026-05-01 — Autonomous workflow engine entry point -->

# Autonomous Workflow Engine

## What This Skill Does

Runs a 4-phase workflow (brainstorm → planning → execution → verification) with:
- **Adaptive resume**: detects existing state/spec/phases and picks up where you left off
- **Phase isolation**: each phase runs in a clean context — no context bleed
- **Hybrid voting**: simulated for routine decisions, 4-agent parallel vote for high-stakes gates
- **AgenticOS integration**: broadcasts lifecycle events to the state bus (fire-and-forget)

## Invocation

```
/autonomous-workflow [--from=brainstorm|planning|execution|verification]
                     [--no-vote]
                     [--agenticos-url=<url>]
                     <task description or path to spec.md>
```

## Resume Priority (checked in this order)

1. `--from=<phase>` flag → jump directly to that phase (overrides everything)
2. `state/workflow_state.json` exists → resume from last incomplete phase
3. `phases.json` exists → skip brainstorm+planning, enter execution
4. `spec.md` exists → skip brainstorm, enter planning
5. Nothing found → start at brainstorm

## Phase Routing

When this skill triggers, read the phase reference file for the current phase:

| Phase | Reference File |
|-------|---------------|
| brainstorm | `references/phase-brainstorm.md` |
| planning | `references/phase-planning.md` |
| execution | `references/phase-execution.md` |
| verification | `references/phase-verification.md` |

Read only the reference file for the current phase — not all of them. Load the next one when the current phase completes.

## State Management

Use `scripts/state_manager.py` to:
- `detect_resume_point(state_dir, from_flag)` — determine entry phase
- `mark_phase_complete(phase, state_dir)` — update state after each phase
- `mark_phase_failed(phase, reason, state_dir)` — record failures for retry

State files live in `state/` (gitignored). Pass `state_dir` as `Path("state")` relative to the working directory.

## AgenticOS Events

After each phase transition, call `scripts/agenticos_push.py`:

```python
from scripts.agenticos_push import push_event, EventType
push_event(EventType.PHASE_COMPLETE, workflow_id=state.workflow_id, extra={"phase": "brainstorm"})
```

This is fire-and-forget. Never await it or check the return value in the critical path.

## Voting Gates

Before entering the execution phase (planning → execution transition), check `references/voting-protocol.md` and run the appropriate vote level. Skip voting if `--no-vote` flag is set.

## First-Time Bootstrap

If the target project directory has no scaffold (no `workflows/`, `tasks/`, `skills/` subdirs), run:

```python
from scripts.bootstrap import scaffold_project
from pathlib import Path
scaffold_project(target_dir=Path("."), templates_dir=Path("templates"))
```

This copies templates into the project once. Subsequent runs skip this step.

## Loop Behavior (Ralph Extension)

This skill continues iterating until all phases in `workflow_state.json` have `status: complete`. After each phase:

1. Call `mark_phase_complete()` or `mark_phase_failed()`
2. Push the event to AgenticOS
3. Check if verification phase is complete — if yes, the workflow is done
4. Otherwise load the next phase reference file and continue

On failure: log the reason, update state, and surface the failure to the user with the specific phase and reason. Do not silently swallow phase failures.
```

- [ ] **Step 2: Verify SKILL.md is under 500 lines**

```bash
(Get-Content "C:\ClaudeSkills\skills\ai-agents\autonomous-workflow\SKILL.md").Count
```

Expected: under 100 lines (well within limit)

- [ ] **Step 3: Commit**

```bash
git add skills/ai-agents/autonomous-workflow/SKILL.md
git commit -m "feat(workflow): add autonomous-workflow SKILL.md entry point"
```

---

## Task 8: Run Full Test Suite and Verify

- [ ] **Step 1: Run all new tests**

```bash
cd "C:/ClaudeSkills"
python -m pytest tests/ai-agents/autonomous-workflow/ -v
```

Expected: 19+ tests PASSED, 0 FAILED

- [ ] **Step 2: Verify skill directory structure is complete**

```bash
Get-ChildItem -Recurse "C:\ClaudeSkills\skills\ai-agents\autonomous-workflow" | Select-Object FullName
```

Expected output includes:
- `SKILL.md`
- `references/phase-brainstorm.md`
- `references/phase-planning.md`
- `references/phase-execution.md`
- `references/phase-verification.md`
- `references/voting-protocol.md`
- `references/agenticos-events.md`
- `templates/workflow.md`
- `templates/task.md`
- `templates/skill-template.md`
- `scripts/state_manager.py`
- `scripts/agenticos_push.py`
- `scripts/bootstrap.py`
- `state/.gitkeep`

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat(workflow): complete autonomous-workflow skill — all tests passing"
```

---

## Self-Review Against Spec

| Spec Requirement | Covered by Task |
|-----------------|----------------|
| Adaptive resume (D+B) | Task 1 `detect_resume_point`, Task 7 SKILL.md |
| Ralph loop extension | Task 7 SKILL.md loop behavior section |
| Hybrid voting (C) | Task 6 voting-protocol.md, Task 7 routing |
| Phase isolation | Task 6 phase-execution.md (headless per-phase) |
| AgenticOS one-way push (C) | Task 2 agenticos_push.py, Task 4 /events endpoint |
| Bootstrap on first invoke | Task 3 bootstrap.py, Task 7 SKILL.md |
| Security constraints | Task 3 path traversal validation, Task 4 Pydantic model |
| Performance (2s timeout, async push) | Task 2 `_TIMEOUT_S = 2` |
| No hardcoded values | All scripts use env vars + parameters |
| Templates (workflow/task/skill) | Task 3 template files |
| `state/` gitignored | Task 5 .gitignore |
| All 6 event types | Task 2 EventType enum |
