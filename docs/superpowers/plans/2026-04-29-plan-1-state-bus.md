# 2026-04-29-plan-1-state-bus.md
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Step-by-step TDD implementation plan for the FastAPI State Bus (Plan 1 of 5)

---

## Goal

Build `AgenticOS/agentic_server.py` — the central nervous system of the AgenticOS Command Center. When complete, the server:

- Serves the built React frontend as static files from `AgenticOS/frontend/dist/`
- Broadcasts agent state diffs over WebSocket `ws://localhost:7842/ws` to all connected React clients
- Watches `AgenticOS/state/agents.json` with watchdog and broadcasts on every file change
- Exposes three REST endpoints for human approval decisions
- Spawns Claude Haiku reviewer subprocesses on `POST /review/{agent_id}`
- Initializes all required state files and directories on first run
- Is fully typed, fully commented, and contains zero hardcoded values

---

## Architecture

```
agentic_server.py          # FastAPI app — WebSocket hub, REST endpoints, static file serving
config.py                  # All constants: PORT, BASE_DIR, STATE paths, timeouts
models.py                  # Pydantic models: AgentState, ApprovalDecision, ReviewRequest
state_watcher.py           # Watchdog FileSystemEventHandler subclass
reviewer_spawner.py        # Claude Haiku subprocess spawner

state/
  agents.json              # [] on first run
  approval_queue.json      # [] on first run
  outputs/                 # Created on first run; reviewer verdicts land here

tests/AgenticOS/
  test_state_bus.py        # FastAPI endpoint + WebSocket integration tests
  test_models.py           # Pydantic model validation tests
  test_reviewer.py         # Reviewer spawner unit tests
```

Data flow:
1. Sub-agent writes to `state/agents.json`
2. Watchdog detects change → calls `broadcast_state()`
3. `broadcast_state()` reads `agents.json`, serializes, sends to all active WebSocket connections
4. React client receives state → re-renders agent cards
5. User clicks approval button → React POSTs to `/approve/{agent_id}` or `/research/{agent_id}` or `/review/{agent_id}`
6. FastAPI appends decision to `approval_queue.json`
7. For `/review/`: FastAPI also spawns Claude Haiku subprocess; verdict written to `state/outputs/agent-{id}-review.md`

---

## Tech Stack

| Concern | Library | Version |
|---|---|---|
| Web framework | fastapi | >=0.110.0 |
| ASGI server | uvicorn | >=0.29.0 |
| WebSocket support | websockets | >=12.0 (fastapi dependency) |
| Pydantic models | pydantic | >=2.0 |
| File watching | watchdog | >=4.0.0 (already installed) |
| Static file serving | fastapi.staticfiles | built-in |
| CORS | fastapi.middleware.cors | built-in |
| Subprocess | subprocess | stdlib |
| Date/time | datetime | stdlib |
| JSON state | json | stdlib |
| Type hints | typing, pathlib | stdlib |

Python version: 3.14 (matches project requirement)

---

## Pre-Flight Checks

Before writing a single file, run these two commands to confirm the environment:

```bash
# Confirm Python 3.14 is on PATH
python --version

# Confirm watchdog is installed (already in requirements.txt)
python -c "import watchdog; print(watchdog.__version__)"
```

If either fails, stop and resolve the environment before proceeding.

---

## Step 1 — Install Dependencies (2 min)

### 1.1 Add new dependencies to `C:\ClaudeSkills\scripts\requirements.txt`

Read the current file first (already done — it has watchdog, pythonnet, plyer).
Append the new lines:

```
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.0
```

Full updated file:
```
watchdog>=4.0.0
pythonnet>=3.0.3
plyer>=2.1.0
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.0
```

### 1.2 Install

```bash
pip install fastapi>=0.110.0 uvicorn>=0.29.0 pydantic>=2.0
```

### 1.3 Verify

```bash
python -c "import fastapi, uvicorn, pydantic; print('OK')"
```

Expected output: `OK`

### Commit

```bash
git add C:/ClaudeSkills/scripts/requirements.txt
git commit -m "deps: add fastapi, uvicorn, pydantic for AgenticOS state bus"
```

---

## Step 2 — Create Directory Structure (2 min)

### 2.1 Create all directories

```bash
mkdir -p C:/ClaudeSkills/AgenticOS/state/outputs
mkdir -p C:/ClaudeSkills/tests/AgenticOS
```

### 2.2 Create `__init__.py` files so pytest can discover the test package

Create `C:\ClaudeSkills\tests\AgenticOS\__init__.py`:

```python
# __init__.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Makes tests/AgenticOS a Python package for pytest discovery
```

### 2.3 Create empty state files (first-run bootstrap — agents write to these)

Create `C:\ClaudeSkills\AgenticOS\state\agents.json`:

```json
[]
```

Create `C:\ClaudeSkills\AgenticOS\state\approval_queue.json`:

```json
[]
```

### Commit

```bash
git add C:/ClaudeSkills/AgenticOS/ C:/ClaudeSkills/tests/AgenticOS/
git commit -m "scaffold: create AgenticOS directory tree and empty state files"
```

---

## Step 3 — Write `config.py` (3 min)

### 3.1 Create `C:\ClaudeSkills\AgenticOS\config.py`

All constants live here. Zero hardcoded values anywhere else in the module.

```python
# config.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Central constants for AgenticOS — port, paths, timeouts.
#          Every hardcoded value in the module lives here and only here.

from pathlib import Path

# ---------------------------------------------------------------------------
# Base directories
# ---------------------------------------------------------------------------

# Root of the ClaudeSkills installation
BASE_DIR: Path = Path("C:/ClaudeSkills")

# Root of the AgenticOS subsystem inside ClaudeSkills
AGENTIC_DIR: Path = BASE_DIR / "AgenticOS"

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

# Port the FastAPI server listens on — matches WebSocket URL in React client
SERVER_PORT: int = 7842

# Host to bind — localhost only; never expose to network
SERVER_HOST: str = "127.0.0.1"

# CORS origins allowed — React dev server + production (served from same host)
CORS_ORIGINS: list[str] = [
    "http://localhost:5173",    # Vite dev server default port
    "http://localhost:7842",    # Production: FastAPI serves the built frontend
    "http://127.0.0.1:5173",
    "http://127.0.0.1:7842",
]

# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

# Seconds between keep-alive pings to connected WebSocket clients
WS_PING_INTERVAL: int = 20

# Seconds a client has to respond to a ping before being dropped
WS_PING_TIMEOUT: int = 10

# ---------------------------------------------------------------------------
# State file paths
# ---------------------------------------------------------------------------

# Directory holding all runtime state JSON files
STATE_DIR: Path = AGENTIC_DIR / "state"

# Live agent state — sub-agents write here at every stage transition
AGENTS_JSON: Path = STATE_DIR / "agents.json"

# Pending approval decisions — FastAPI appends here on approval POSTs
APPROVAL_QUEUE_JSON: Path = STATE_DIR / "approval_queue.json"

# Directory where agent output files and reviewer verdicts are written
OUTPUTS_DIR: Path = STATE_DIR / "outputs"

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

# Path to the built React frontend — served as static files by FastAPI
FRONTEND_DIST_DIR: Path = AGENTIC_DIR / "frontend" / "dist"

# URL path prefix under which the frontend is mounted
FRONTEND_MOUNT_PATH: str = "/app"

# ---------------------------------------------------------------------------
# Reviewer subprocess
# ---------------------------------------------------------------------------

# Claude model used for reviewer agents — Haiku is fast and cost-effective
REVIEWER_MODEL: str = "claude-haiku-4-5-20251001"

# Seconds to wait for the reviewer subprocess to complete before timing out
REVIEWER_TIMEOUT_SECONDS: int = 120

# Template for the reviewer verdict output filename inside OUTPUTS_DIR
# Usage: REVIEWER_OUTPUT_TEMPLATE.format(agent_id="AGENT-01")
REVIEWER_OUTPUT_TEMPLATE: str = "agent-{agent_id}-review.md"

# System prompt sent to the reviewer Claude instance
REVIEWER_PROMPT_TEMPLATE: str = (
    "You are an independent reviewer agent. Review the following work output "
    "for correctness, completeness, and bias. Output a structured verdict: "
    "PASS | REVISE | REJECT with specific, actionable notes.\n\n"
    "Work output:\n{content}"
)

# ---------------------------------------------------------------------------
# File watcher
# ---------------------------------------------------------------------------

# Seconds the watchdog observer sleeps between filesystem event checks
WATCHER_POLL_INTERVAL: float = 0.5
```

### 3.2 Verify it imports cleanly

```bash
cd C:/ClaudeSkills && python -c "from AgenticOS.config import SERVER_PORT, AGENTS_JSON; print(SERVER_PORT, AGENTS_JSON)"
```

Expected output: `7842 C:\ClaudeSkills\AgenticOS\state\agents.json`

### Commit

```bash
git add C:/ClaudeSkills/AgenticOS/config.py
git commit -m "feat(agentic-os): add config.py with all constants for state bus"
```

---

## Step 4 — Write Failing Tests for `models.py` (3 min)

TDD: tests first. These tests will fail until Step 5.

### 4.1 Create `C:\ClaudeSkills\tests\AgenticOS\test_models.py`

```python
# test_models.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Pydantic model validation tests for AgenticOS state shapes.
#          Run: pytest tests/AgenticOS/test_models.py

import pytest
from datetime import datetime, timezone
from AgenticOS.models import (
    AgentStatus,
    AgentDomain,
    AwaitingDecision,
    AgentState,
    ApprovalDecision,
    ApprovalDecisionType,
    ReviewRequest,
    ApprovalQueueEntry,
)


class TestAgentState:
    """AgentState model validation — all fields, all statuses."""

    def test_valid_active_agent(self):
        # Minimal valid active agent — all required fields present
        agent = AgentState(
            agent_id="AGENT-01",
            domain=AgentDomain.VA_ADVISORY,
            task="Analyze CFR Title 38",
            stage_label="Analyzing CFR Title 38 Part 3",
            stage=2,
            total_stages=5,
            progress_pct=64,
            status=AgentStatus.ACTIVE,
            context_pct_used=34,
            updated_at=datetime.now(timezone.utc),
        )
        assert agent.agent_id == "AGENT-01"
        assert agent.status == AgentStatus.ACTIVE
        assert agent.awaiting is None
        assert agent.error_msg is None
        assert agent.reviewer_verdict is None
        assert agent.spawned_by is None

    def test_progress_pct_upper_bound(self):
        # progress_pct must not exceed 100
        with pytest.raises(Exception):
            AgentState(
                agent_id="AGENT-01",
                domain=AgentDomain.GENERAL,
                task="test",
                stage_label="test",
                stage=1,
                total_stages=1,
                progress_pct=101,
                status=AgentStatus.ACTIVE,
                context_pct_used=0,
                updated_at=datetime.now(timezone.utc),
            )

    def test_progress_pct_lower_bound(self):
        # progress_pct must not be negative
        with pytest.raises(Exception):
            AgentState(
                agent_id="AGENT-01",
                domain=AgentDomain.GENERAL,
                task="test",
                stage_label="test",
                stage=1,
                total_stages=1,
                progress_pct=-1,
                status=AgentStatus.ACTIVE,
                context_pct_used=0,
                updated_at=datetime.now(timezone.utc),
            )

    def test_context_pct_used_bounds(self):
        # context_pct_used must be 0-100 inclusive
        with pytest.raises(Exception):
            AgentState(
                agent_id="AGENT-01",
                domain=AgentDomain.GENERAL,
                task="test",
                stage_label="test",
                stage=1,
                total_stages=1,
                progress_pct=0,
                status=AgentStatus.ACTIVE,
                context_pct_used=101,
                updated_at=datetime.now(timezone.utc),
            )

    def test_stage_must_not_exceed_total_stages(self):
        # stage > total_stages is invalid
        with pytest.raises(Exception):
            AgentState(
                agent_id="AGENT-01",
                domain=AgentDomain.GENERAL,
                task="test",
                stage_label="test",
                stage=6,
                total_stages=5,
                progress_pct=100,
                status=AgentStatus.COMPLETE,
                context_pct_used=50,
                updated_at=datetime.now(timezone.utc),
            )

    def test_waiting_approval_status_with_awaiting_field(self):
        # waiting_approval status must allow awaiting field to be set
        agent = AgentState(
            agent_id="AGENT-02",
            domain=AgentDomain.GAME_DEV,
            task="Build level",
            stage_label="Generating terrain",
            stage=3,
            total_stages=6,
            progress_pct=50,
            status=AgentStatus.WAITING_APPROVAL,
            context_pct_used=20,
            awaiting=AwaitingDecision.PROCEED,
            updated_at=datetime.now(timezone.utc),
        )
        assert agent.awaiting == AwaitingDecision.PROCEED

    def test_error_status_with_error_msg(self):
        # error status must allow error_msg to be populated
        agent = AgentState(
            agent_id="AGENT-03",
            domain=AgentDomain.SOFTWARE_ENG,
            task="Write tests",
            stage_label="Running pytest",
            stage=1,
            total_stages=3,
            progress_pct=10,
            status=AgentStatus.ERROR,
            context_pct_used=5,
            error_msg="pytest exited with code 1",
            updated_at=datetime.now(timezone.utc),
        )
        assert agent.error_msg == "pytest exited with code 1"

    def test_all_domains_valid(self):
        # Every domain value in the enum must be accepted
        for domain in AgentDomain:
            agent = AgentState(
                agent_id="AGENT-01",
                domain=domain,
                task="test",
                stage_label="test",
                stage=1,
                total_stages=1,
                progress_pct=0,
                status=AgentStatus.ACTIVE,
                context_pct_used=0,
                updated_at=datetime.now(timezone.utc),
            )
            assert agent.domain == domain

    def test_serializes_to_dict(self):
        # Model must serialize cleanly for JSON broadcast
        agent = AgentState(
            agent_id="AGENT-01",
            domain=AgentDomain.GENERAL,
            task="test",
            stage_label="test",
            stage=1,
            total_stages=1,
            progress_pct=0,
            status=AgentStatus.ACTIVE,
            context_pct_used=0,
            updated_at=datetime.now(timezone.utc),
        )
        data = agent.model_dump(mode="json")
        assert data["agent_id"] == "AGENT-01"
        assert "updated_at" in data


class TestApprovalDecision:
    """ApprovalDecision request body model."""

    def test_proceed_decision(self):
        decision = ApprovalDecision(decision=ApprovalDecisionType.PROCEED)
        assert decision.decision == ApprovalDecisionType.PROCEED

    def test_research_decision(self):
        decision = ApprovalDecision(decision=ApprovalDecisionType.RESEARCH)
        assert decision.decision == ApprovalDecisionType.RESEARCH

    def test_invalid_decision_rejected(self):
        # String values not in the enum must be rejected
        with pytest.raises(Exception):
            ApprovalDecision(decision="invalid_value")


class TestReviewRequest:
    """ReviewRequest body model — POST /review/{agent_id}."""

    def test_valid_review_request(self):
        req = ReviewRequest(
            decision=ApprovalDecisionType.REVIEW,
            reviewer_context="state/outputs/agent-01-stage-2.md",
        )
        assert req.reviewer_context == "state/outputs/agent-01-stage-2.md"

    def test_reviewer_context_defaults_to_none(self):
        # reviewer_context is optional — default None when not provided
        req = ReviewRequest(decision=ApprovalDecisionType.REVIEW)
        assert req.reviewer_context is None


class TestApprovalQueueEntry:
    """ApprovalQueueEntry — the shape written to approval_queue.json."""

    def test_full_entry(self):
        entry = ApprovalQueueEntry(
            agent_id="AGENT-01",
            decision=ApprovalDecisionType.REVIEW,
            reviewer_context="state/outputs/agent-01-stage-2.md",
            decided_at=datetime.now(timezone.utc),
        )
        assert entry.agent_id == "AGENT-01"
        assert entry.decision == ApprovalDecisionType.REVIEW

    def test_reviewer_context_optional(self):
        entry = ApprovalQueueEntry(
            agent_id="AGENT-01",
            decision=ApprovalDecisionType.PROCEED,
            decided_at=datetime.now(timezone.utc),
        )
        assert entry.reviewer_context is None
```

### 4.2 Run tests — confirm they all FAIL (import error expected)

```bash
cd C:/ClaudeSkills && python -m pytest tests/AgenticOS/test_models.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'AgenticOS'` — this is correct. Tests are red.

---

## Step 5 — Implement `models.py` (5 min)

### 5.1 Create `C:\ClaudeSkills\AgenticOS\__init__.py`

Makes `AgenticOS` a proper Python package for absolute imports.

```python
# __init__.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Makes AgenticOS a Python package importable from C:\ClaudeSkills root
```

### 5.2 Create `C:\ClaudeSkills\AgenticOS\models.py`

```python
# models.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Pydantic v2 models for all AgenticOS state shapes.
#          Used by agentic_server.py for request validation and WebSocket broadcasts.

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerations — named constants for all status/domain/decision strings
# ---------------------------------------------------------------------------

class AgentStatus(str, Enum):
    # Agent is actively working on its current stage
    ACTIVE = "active"
    # Agent has paused at a gate and is waiting for a human approval decision
    WAITING_APPROVAL = "waiting_approval"
    # Agent is waiting for a reviewer sub-agent to finish and return a verdict
    WAITING_REVIEW = "waiting_review"
    # Agent has finished all stages successfully
    COMPLETE = "complete"
    # Agent encountered an unrecoverable error — error_msg will be populated
    ERROR = "error"


class AgentDomain(str, Enum):
    # Veterans Affairs benefits advisory work
    VA_ADVISORY = "va-advisory"
    # Unreal Engine / game development work
    GAME_DEV = "game-dev"
    # General software engineering tasks
    SOFTWARE_ENG = "software-eng"
    # 3D content creation and asset work
    CONTENT_3D = "3d-content"
    # Domain-agnostic or catch-all tasks
    GENERAL = "general"


class AwaitingDecision(str, Enum):
    # Agent is waiting for a proceed gate approval
    PROCEED = "proceed"
    # Agent is waiting for a research-more decision
    RESEARCH = "research"
    # Agent is waiting for a reviewer agent verdict before proceeding
    REVIEW = "review"


class ApprovalDecisionType(str, Enum):
    # User approved proceeding to the next stage
    PROCEED = "proceed"
    # User requested additional research before proceeding
    RESEARCH = "research"
    # User requested an independent reviewer agent assessment
    REVIEW = "review"


# ---------------------------------------------------------------------------
# Core state model — written by agents, broadcast over WebSocket
# ---------------------------------------------------------------------------

class AgentState(BaseModel):
    # Unique identifier for this agent instance (e.g. "AGENT-01")
    agent_id: str

    # Which domain this agent is operating in
    domain: AgentDomain

    # Human-readable description of this agent's overall task
    task: str

    # Human-readable label for the current stage (e.g. "Analyzing CFR Title 38 Part 3")
    stage_label: str

    # Current stage number (1-indexed)
    stage: int = Field(ge=1)

    # Total number of stages this agent will execute
    total_stages: int = Field(ge=1)

    # Overall progress percentage (0-100 inclusive)
    progress_pct: int = Field(ge=0, le=100)

    # Current agent lifecycle status
    status: AgentStatus

    # Percentage of the context window consumed so far (0-100 inclusive)
    context_pct_used: int = Field(ge=0, le=100)

    # Optional path to the agent's most recent output file (relative to AgenticOS/)
    output_ref: Optional[str] = None

    # Which approval decision this agent is currently waiting for (None if not waiting)
    awaiting: Optional[AwaitingDecision] = None

    # Error message when status == ERROR; None otherwise
    error_msg: Optional[str] = None

    # agent_id of the parent agent that spawned this one; None for top-level agents
    spawned_by: Optional[str] = None

    # Verdict written by the reviewer agent; None until review is complete
    reviewer_verdict: Optional[str] = None

    # ISO 8601 UTC timestamp of the last state update written by the agent
    updated_at: datetime

    @model_validator(mode="after")
    def stage_must_not_exceed_total(self) -> "AgentState":
        # Stage number cannot logically exceed the declared total stages
        if self.stage > self.total_stages:
            raise ValueError(
                f"stage ({self.stage}) must not exceed total_stages ({self.total_stages})"
            )
        return self


# ---------------------------------------------------------------------------
# Request body models — used by FastAPI endpoint handlers
# ---------------------------------------------------------------------------

class ApprovalDecision(BaseModel):
    # The human decision: proceed, research, or review
    decision: ApprovalDecisionType


class ReviewRequest(BaseModel):
    # Decision must be REVIEW for this endpoint
    decision: ApprovalDecisionType

    # Path to the agent output file the reviewer should assess
    # Optional — if omitted, FastAPI reads output_ref from agents.json
    reviewer_context: Optional[str] = None


# ---------------------------------------------------------------------------
# Approval queue entry — written to approval_queue.json by FastAPI
# ---------------------------------------------------------------------------

class ApprovalQueueEntry(BaseModel):
    # Which agent this decision targets
    agent_id: str

    # The decision type written by the human
    decision: ApprovalDecisionType

    # Path to the output the reviewer should read; None for non-review decisions
    reviewer_context: Optional[str] = None

    # UTC timestamp when the decision was recorded
    decided_at: datetime
```

### 5.3 Run tests — confirm they all PASS

```bash
cd C:/ClaudeSkills && python -m pytest tests/AgenticOS/test_models.py -v
```

Expected:
```
tests/AgenticOS/test_models.py::TestAgentState::test_valid_active_agent PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_progress_pct_upper_bound PASSED
...
tests/AgenticOS/test_models.py::TestApprovalQueueEntry::test_reviewer_context_optional PASSED

15 passed in X.XXs
```

All 15 tests must be green before proceeding.

### Commit

```bash
git add C:/ClaudeSkills/AgenticOS/__init__.py C:/ClaudeSkills/AgenticOS/models.py C:/ClaudeSkills/tests/AgenticOS/test_models.py
git commit -m "feat(agentic-os): add Pydantic models and passing model tests"
```

---

## Step 6 — Write Failing Tests for `state_watcher.py` (3 min)

### 6.1 Create `C:\ClaudeSkills\tests\AgenticOS\test_state_bus.py`

This file tests the watcher integration and all REST + WebSocket endpoints. Tests are written now; implementation comes in Steps 7-9.

```python
# test_state_bus.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Integration tests for the FastAPI state bus — WebSocket broadcasts,
#          REST approval endpoints, and file watcher event handling.
#          Run: pytest tests/AgenticOS/test_state_bus.py

import json
import pytest
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from AgenticOS.agentic_server import app, broadcast_state, connection_manager
from AgenticOS.models import (
    AgentState, AgentStatus, AgentDomain, ApprovalDecisionType,
    ApprovalQueueEntry,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    # Provide a synchronous test client for REST endpoint tests
    return TestClient(app)


@pytest.fixture
def sample_agent_state() -> dict:
    # Minimal valid agent state dict as would be written to agents.json
    return {
        "agent_id": "AGENT-01",
        "domain": "va-advisory",
        "task": "Analyze CFR Title 38",
        "stage_label": "Analyzing CFR Title 38 Part 3",
        "stage": 2,
        "total_stages": 5,
        "progress_pct": 64,
        "status": "active",
        "context_pct_used": 34,
        "output_ref": "state/outputs/agent-01-stage-2.md",
        "awaiting": None,
        "error_msg": None,
        "spawned_by": None,
        "reviewer_verdict": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def agents_json_path(tmp_path) -> Path:
    # Write a temporary agents.json for watcher tests
    agents_file = tmp_path / "agents.json"
    agents_file.write_text("[]", encoding="utf-8")
    return agents_file


@pytest.fixture
def approval_queue_path(tmp_path) -> Path:
    # Write a temporary approval_queue.json for approval endpoint tests
    queue_file = tmp_path / "approval_queue.json"
    queue_file.write_text("[]", encoding="utf-8")
    return queue_file


# ---------------------------------------------------------------------------
# REST endpoint tests
# ---------------------------------------------------------------------------

class TestApproveEndpoint:
    """POST /approve/{agent_id} — writes proceed decision to approval_queue.json."""

    def test_approve_returns_200(self, client, tmp_path, monkeypatch):
        # Patch APPROVAL_QUEUE_JSON to a temp file so test is isolated
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)

        response = client.post("/approve/AGENT-01", json={"decision": "proceed"})
        assert response.status_code == 200

    def test_approve_writes_to_queue(self, client, tmp_path, monkeypatch):
        # Decision must be appended to approval_queue.json
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)

        client.post("/approve/AGENT-01", json={"decision": "proceed"})

        written = json.loads(queue_file.read_text(encoding="utf-8"))
        assert len(written) == 1
        assert written[0]["agent_id"] == "AGENT-01"
        assert written[0]["decision"] == "proceed"

    def test_approve_response_body(self, client, tmp_path, monkeypatch):
        # Response must include status and agent_id
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)

        response = client.post("/approve/AGENT-01", json={"decision": "proceed"})
        body = response.json()
        assert body["agent_id"] == "AGENT-01"
        assert body["decision"] == "proceed"

    def test_approve_invalid_decision_rejected(self, client):
        # Invalid decision strings must be rejected with 422
        response = client.post("/approve/AGENT-01", json={"decision": "invalid"})
        assert response.status_code == 422

    def test_approve_multiple_agents_accumulate(self, client, tmp_path, monkeypatch):
        # Multiple agents' decisions must accumulate in the queue
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)

        client.post("/approve/AGENT-01", json={"decision": "proceed"})
        client.post("/approve/AGENT-02", json={"decision": "research"})

        written = json.loads(queue_file.read_text(encoding="utf-8"))
        assert len(written) == 2
        agent_ids = {entry["agent_id"] for entry in written}
        assert agent_ids == {"AGENT-01", "AGENT-02"}


class TestResearchEndpoint:
    """POST /research/{agent_id} — writes research decision to approval_queue.json."""

    def test_research_returns_200(self, client, tmp_path, monkeypatch):
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)

        response = client.post("/research/AGENT-01", json={"decision": "research"})
        assert response.status_code == 200

    def test_research_writes_research_decision(self, client, tmp_path, monkeypatch):
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)

        client.post("/research/AGENT-02", json={"decision": "research"})

        written = json.loads(queue_file.read_text(encoding="utf-8"))
        assert written[0]["decision"] == "research"
        assert written[0]["agent_id"] == "AGENT-02"


class TestReviewEndpoint:
    """POST /review/{agent_id} — spawns reviewer and writes to queue."""

    def test_review_returns_200(self, client, tmp_path, monkeypatch):
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)
        # Patch spawner so test does not call Claude CLI
        monkeypatch.setattr(
            "AgenticOS.agentic_server.spawn_reviewer",
            lambda agent_id, reviewer_context: None,
        )

        response = client.post(
            "/review/AGENT-01",
            json={"decision": "review", "reviewer_context": "state/outputs/agent-01-stage-2.md"},
        )
        assert response.status_code == 200

    def test_review_writes_review_decision_to_queue(self, client, tmp_path, monkeypatch):
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)
        monkeypatch.setattr(
            "AgenticOS.agentic_server.spawn_reviewer",
            lambda agent_id, reviewer_context: None,
        )

        client.post(
            "/review/AGENT-01",
            json={"decision": "review", "reviewer_context": "state/outputs/agent-01-stage-2.md"},
        )

        written = json.loads(queue_file.read_text(encoding="utf-8"))
        assert written[0]["decision"] == "review"
        assert written[0]["reviewer_context"] == "state/outputs/agent-01-stage-2.md"

    def test_review_calls_spawn_reviewer(self, client, tmp_path, monkeypatch):
        # spawn_reviewer must be called with the correct agent_id and context path
        queue_file = tmp_path / "approval_queue.json"
        queue_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.APPROVAL_QUEUE_JSON", queue_file)

        called_with: list = []
        monkeypatch.setattr(
            "AgenticOS.agentic_server.spawn_reviewer",
            lambda agent_id, reviewer_context: called_with.append((agent_id, reviewer_context)),
        )

        client.post(
            "/review/AGENT-01",
            json={"decision": "review", "reviewer_context": "state/outputs/agent-01-stage-2.md"},
        )

        assert len(called_with) == 1
        assert called_with[0][0] == "AGENT-01"
        assert called_with[0][1] == "state/outputs/agent-01-stage-2.md"


# ---------------------------------------------------------------------------
# broadcast_state function tests
# ---------------------------------------------------------------------------

class TestBroadcastState:
    """broadcast_state reads agents.json and sends to all active WebSocket connections."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_connected_clients(self, tmp_path, monkeypatch, sample_agent_state):
        # Patch AGENTS_JSON to a temp file containing one agent
        agents_file = tmp_path / "agents.json"
        agents_file.write_text(json.dumps([sample_agent_state]), encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.AGENTS_JSON", agents_file)

        # Create a mock WebSocket connection
        mock_ws = AsyncMock()
        connection_manager.active_connections.clear()
        connection_manager.active_connections.append(mock_ws)

        await broadcast_state()

        # The mock WebSocket must have received exactly one send_text call
        mock_ws.send_text.assert_called_once()
        payload = json.loads(mock_ws.send_text.call_args[0][0])
        assert isinstance(payload, list)
        assert payload[0]["agent_id"] == "AGENT-01"

        # Clean up
        connection_manager.active_connections.clear()

    @pytest.mark.asyncio
    async def test_broadcast_handles_empty_agents_file(self, tmp_path, monkeypatch):
        # Empty agents.json must broadcast an empty list without error
        agents_file = tmp_path / "agents.json"
        agents_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.AGENTS_JSON", agents_file)

        mock_ws = AsyncMock()
        connection_manager.active_connections.clear()
        connection_manager.active_connections.append(mock_ws)

        await broadcast_state()

        payload = json.loads(mock_ws.send_text.call_args[0][0])
        assert payload == []

        connection_manager.active_connections.clear()

    @pytest.mark.asyncio
    async def test_broadcast_handles_no_connections(self, tmp_path, monkeypatch):
        # broadcast_state with no connected clients must not raise
        agents_file = tmp_path / "agents.json"
        agents_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.AGENTS_JSON", agents_file)
        connection_manager.active_connections.clear()

        # Must complete without exception
        await broadcast_state()

    @pytest.mark.asyncio
    async def test_broadcast_skips_dead_connections(self, tmp_path, monkeypatch):
        # A connection that raises on send_text must be removed from active_connections
        agents_file = tmp_path / "agents.json"
        agents_file.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.agentic_server.AGENTS_JSON", agents_file)

        dead_ws = AsyncMock()
        dead_ws.send_text.side_effect = Exception("connection closed")
        connection_manager.active_connections.clear()
        connection_manager.active_connections.append(dead_ws)

        # Must not raise even when connection is dead
        await broadcast_state()

        # Dead connection must have been removed
        assert len(connection_manager.active_connections) == 0


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """GET /health — liveness check."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_ok(self, client):
        body = client.get("/health").json()
        assert body["status"] == "ok"
```

### 6.2 Run tests — confirm they all FAIL (import error expected)

```bash
cd C:/ClaudeSkills && python -m pytest tests/AgenticOS/test_state_bus.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'AgenticOS.agentic_server'` — correct, still red.

---

## Step 7 — Implement `state_watcher.py` (4 min)

### 7.1 Create `C:\ClaudeSkills\AgenticOS\state_watcher.py`

```python
# state_watcher.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Watchdog file system event handler that triggers a WebSocket broadcast
#          whenever agents.json is modified by a sub-agent.

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable, Coroutine, Any

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from AgenticOS.config import AGENTS_JSON, WATCHER_POLL_INTERVAL

# Module-level logger for watcher events
logger = logging.getLogger("state_watcher")


class AgentsJsonHandler(FileSystemEventHandler):
    """Watchdog event handler that fires a broadcast coroutine on agents.json changes.

    Only reacts to modification events on the specific agents.json file.
    Other file changes in the watched directory are silently ignored.
    """

    def __init__(
        self,
        broadcast_callback: Callable[[], Coroutine[Any, Any, None]],
        loop: asyncio.AbstractEventLoop,
        watched_file: Path = AGENTS_JSON,
    ) -> None:
        # Coroutine to call when agents.json changes — typically broadcast_state()
        self._callback = broadcast_callback
        # The event loop running the FastAPI app — needed to schedule the coroutine
        self._loop = loop
        # Absolute path of the file to watch — resolved for reliable comparison
        self._watched_file = watched_file.resolve()

    def on_modified(self, event: FileSystemEvent) -> None:
        # Ignore directory change events — only care about file modifications
        if event.is_directory:
            return

        # Resolve the changed path and compare to the watched file
        changed_path = Path(str(event.src_path)).resolve()
        if changed_path != self._watched_file:
            return

        logger.debug("agents.json modified — scheduling broadcast")

        # Schedule the async broadcast_state coroutine on the FastAPI event loop
        # call_soon_threadsafe is required because watchdog runs on a background thread
        asyncio.run_coroutine_threadsafe(self._callback(), self._loop)


def start_watcher(
    broadcast_callback: Callable[[], Coroutine[Any, Any, None]],
    loop: asyncio.AbstractEventLoop,
    watched_file: Path = AGENTS_JSON,
) -> Observer:
    """Start the watchdog observer and return it for lifecycle management.

    The caller is responsible for calling observer.stop() on shutdown.
    The observer runs on a daemon thread — it will not block process exit.
    """
    handler = AgentsJsonHandler(
        broadcast_callback=broadcast_callback,
        loop=loop,
        watched_file=watched_file,
    )

    observer = Observer()

    # Watch the directory containing agents.json — watchdog monitors directories, not files
    watch_dir = str(watched_file.parent)
    observer.schedule(handler, watch=watch_dir, recursive=False)
    observer.start()

    logger.info("Watching %s for changes (poll interval: %ss)", watched_file, WATCHER_POLL_INTERVAL)
    return observer
```

### Verify import

```bash
cd C:/ClaudeSkills && python -c "from AgenticOS.state_watcher import AgentsJsonHandler, start_watcher; print('OK')"
```

Expected: `OK`

### Commit

```bash
git add C:/ClaudeSkills/AgenticOS/state_watcher.py
git commit -m "feat(agentic-os): add watchdog file watcher for agents.json"
```

---

## Step 8 — Write Failing Tests for `reviewer_spawner.py` (3 min)

### 8.1 Create `C:\ClaudeSkills\tests\AgenticOS\test_reviewer.py`

```python
# test_reviewer.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Unit tests for the Claude Haiku reviewer subprocess spawner.
#          Tests mock subprocess.run — no actual Claude CLI calls are made.
#          Run: pytest tests/AgenticOS/test_reviewer.py

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from AgenticOS.reviewer_spawner import spawn_reviewer, build_reviewer_prompt


class TestBuildReviewerPrompt:
    """build_reviewer_prompt constructs the Claude CLI prompt from output file content."""

    def test_includes_content(self, tmp_path):
        # Output file content must appear verbatim in the prompt
        output_file = tmp_path / "agent-01-stage-2.md"
        output_file.write_text("This is the agent output.", encoding="utf-8")
        prompt = build_reviewer_prompt(str(output_file))
        assert "This is the agent output." in prompt

    def test_includes_instructions(self, tmp_path):
        # Reviewer instructions (PASS | REVISE | REJECT) must be in the prompt
        output_file = tmp_path / "agent-01-stage-2.md"
        output_file.write_text("content", encoding="utf-8")
        prompt = build_reviewer_prompt(str(output_file))
        assert "PASS" in prompt
        assert "REVISE" in prompt
        assert "REJECT" in prompt

    def test_missing_file_raises_file_not_found(self):
        # Missing output file must raise FileNotFoundError with clear message
        with pytest.raises(FileNotFoundError):
            build_reviewer_prompt("state/outputs/nonexistent-file.md")


class TestSpawnReviewer:
    """spawn_reviewer calls Claude CLI subprocess and writes verdict to outputs/."""

    def test_writes_verdict_file(self, tmp_path, monkeypatch):
        # The reviewer verdict must be written to the correct path in OUTPUTS_DIR
        output_file = tmp_path / "agent-01-stage-2.md"
        output_file.write_text("Agent output content here.", encoding="utf-8")

        # Patch OUTPUTS_DIR to tmp_path so test is isolated
        monkeypatch.setattr("AgenticOS.reviewer_spawner.OUTPUTS_DIR", tmp_path)

        # Patch subprocess.run to return a fake Claude response
        mock_result = MagicMock()
        mock_result.stdout = "PASS: The output is correct and complete."
        mock_result.returncode = 0

        with patch("AgenticOS.reviewer_spawner.subprocess.run", return_value=mock_result):
            spawn_reviewer("AGENT-01", str(output_file))

        # Verdict file must exist at the expected path
        verdict_file = tmp_path / "agent-AGENT-01-review.md"
        assert verdict_file.exists()
        assert "PASS" in verdict_file.read_text(encoding="utf-8")

    def test_verdict_file_contains_agent_id(self, tmp_path, monkeypatch):
        # Verdict file header must include the agent_id for traceability
        output_file = tmp_path / "agent-01-stage-2.md"
        output_file.write_text("content", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.reviewer_spawner.OUTPUTS_DIR", tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = "REVISE: Missing citations."
        mock_result.returncode = 0

        with patch("AgenticOS.reviewer_spawner.subprocess.run", return_value=mock_result):
            spawn_reviewer("AGENT-01", str(output_file))

        verdict_text = (tmp_path / "agent-AGENT-01-review.md").read_text(encoding="utf-8")
        assert "AGENT-01" in verdict_text

    def test_subprocess_called_with_correct_model(self, tmp_path, monkeypatch):
        # Claude CLI must be invoked with the REVIEWER_MODEL constant — not hardcoded
        output_file = tmp_path / "agent-01-stage-2.md"
        output_file.write_text("content", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.reviewer_spawner.OUTPUTS_DIR", tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = "PASS: Good."
        mock_result.returncode = 0

        with patch("AgenticOS.reviewer_spawner.subprocess.run", return_value=mock_result) as mock_run:
            spawn_reviewer("AGENT-01", str(output_file))

        # The command list must include the model flag
        cmd = mock_run.call_args[0][0]
        assert "--model" in cmd
        # Model value must come from REVIEWER_MODEL, not be hardcoded
        from AgenticOS.config import REVIEWER_MODEL
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == REVIEWER_MODEL

    def test_nonzero_returncode_raises(self, tmp_path, monkeypatch):
        # Non-zero Claude CLI exit code must raise RuntimeError
        output_file = tmp_path / "agent-01-stage-2.md"
        output_file.write_text("content", encoding="utf-8")
        monkeypatch.setattr("AgenticOS.reviewer_spawner.OUTPUTS_DIR", tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 1
        mock_result.stderr = "Error: API rate limit"

        with patch("AgenticOS.reviewer_spawner.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="Reviewer subprocess failed"):
                spawn_reviewer("AGENT-01", str(output_file))

    def test_missing_output_file_raises(self, tmp_path, monkeypatch):
        # spawn_reviewer with a nonexistent context file must raise FileNotFoundError
        monkeypatch.setattr("AgenticOS.reviewer_spawner.OUTPUTS_DIR", tmp_path)
        with pytest.raises(FileNotFoundError):
            spawn_reviewer("AGENT-01", "state/outputs/nonexistent.md")
```

### 8.2 Run tests — confirm they all FAIL

```bash
cd C:/ClaudeSkills && python -m pytest tests/AgenticOS/test_reviewer.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'AgenticOS.reviewer_spawner'` — correct.

---

## Step 9 — Implement `reviewer_spawner.py` (4 min)

### 9.1 Create `C:\ClaudeSkills\AgenticOS\reviewer_spawner.py`

```python
# reviewer_spawner.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Spawns a Claude Haiku reviewer subprocess via the Claude CLI.
#          Called by agentic_server.py when a user clicks "REVIEW BY AGENT".
#          Reviewer verdict is written to state/outputs/agent-{id}-review.md.

from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from AgenticOS.config import (
    OUTPUTS_DIR,
    REVIEWER_MODEL,
    REVIEWER_OUTPUT_TEMPLATE,
    REVIEWER_PROMPT_TEMPLATE,
    REVIEWER_TIMEOUT_SECONDS,
)

# Module-level logger for reviewer spawn events
logger = logging.getLogger("reviewer_spawner")


def build_reviewer_prompt(reviewer_context_path: str) -> str:
    """Read the agent output file and build the Claude reviewer prompt.

    Parameters
    ----------
    reviewer_context_path:
        Path to the agent's output markdown file to be reviewed.

    Returns the fully constructed prompt string ready for the Claude CLI.

    Raises FileNotFoundError if the output file does not exist.
    """
    context_path = Path(reviewer_context_path)

    # Confirm the file exists before attempting to read it
    if not context_path.exists():
        raise FileNotFoundError(
            f"Reviewer context file not found: {context_path}"
        )

    # Read the agent's output content to embed in the prompt
    content = context_path.read_text(encoding="utf-8")

    # Substitute content into the template from config — no hardcoded prompt strings here
    return REVIEWER_PROMPT_TEMPLATE.format(content=content)


def spawn_reviewer(agent_id: str, reviewer_context: str) -> Path:
    """Invoke Claude Haiku as a reviewer subprocess and write the verdict to disk.

    Parameters
    ----------
    agent_id:
        The ID of the agent whose output is being reviewed (e.g. "AGENT-01").
    reviewer_context:
        Path to the output file the reviewer should assess.

    Returns the Path of the written verdict file.

    Raises
    ------
    FileNotFoundError
        If the reviewer_context file does not exist.
    RuntimeError
        If the Claude CLI subprocess exits with a non-zero return code.
    """
    # Build the prompt — will raise FileNotFoundError if context file is missing
    prompt = build_reviewer_prompt(reviewer_context)

    # Construct the Claude CLI command using config constants — no hardcoded values
    cmd: list[str] = [
        "claude",
        "--model", REVIEWER_MODEL,
        "--print",       # Non-interactive single-shot mode
        prompt,
    ]

    logger.info("Spawning reviewer for %s with model %s", agent_id, REVIEWER_MODEL)

    # Run the subprocess — capture stdout, enforce timeout from config
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=REVIEWER_TIMEOUT_SECONDS,
        encoding="utf-8",
    )

    # Non-zero exit code means the Claude CLI failed — surface the error clearly
    if result.returncode != 0:
        raise RuntimeError(
            f"Reviewer subprocess failed for {agent_id} "
            f"(exit {result.returncode}): {result.stderr}"
        )

    verdict_text = result.stdout.strip()

    # Build the verdict file path using the config template — no hardcoded filenames
    verdict_filename = REVIEWER_OUTPUT_TEMPLATE.format(agent_id=agent_id)
    verdict_path = OUTPUTS_DIR / verdict_filename

    # Ensure the outputs directory exists before writing
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write the verdict with a header for traceability
    timestamp = datetime.now(timezone.utc).isoformat()
    verdict_content = (
        f"# Reviewer Verdict — {agent_id}\n"
        f"# Reviewed at: {timestamp}\n"
        f"# Model: {REVIEWER_MODEL}\n"
        f"# Context file: {reviewer_context}\n\n"
        f"{verdict_text}\n"
    )
    verdict_path.write_text(verdict_content, encoding="utf-8")

    logger.info("Reviewer verdict written to %s", verdict_path)
    return verdict_path
```

### 9.2 Run reviewer tests — confirm all PASS

```bash
cd C:/ClaudeSkills && python -m pytest tests/AgenticOS/test_reviewer.py -v
```

Expected: all 8 tests green.

### Commit

```bash
git add C:/ClaudeSkills/AgenticOS/reviewer_spawner.py C:/ClaudeSkills/tests/AgenticOS/test_reviewer.py
git commit -m "feat(agentic-os): add reviewer spawner and passing reviewer tests"
```

---

## Step 10 — Implement `agentic_server.py` (10 min)

This is the largest file. Write it completely — no placeholders.

### 10.1 Create `C:\ClaudeSkills\AgenticOS\agentic_server.py`

```python
# agentic_server.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: FastAPI state bus for the AgenticOS Command Center.
#          Serves the React frontend, manages WebSocket connections,
#          broadcasts agent state diffs, and handles approval REST endpoints.

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from AgenticOS.config import (
    AGENTS_JSON,
    APPROVAL_QUEUE_JSON,
    CORS_ORIGINS,
    FRONTEND_DIST_DIR,
    FRONTEND_MOUNT_PATH,
    OUTPUTS_DIR,
    SERVER_HOST,
    SERVER_PORT,
    STATE_DIR,
)
from AgenticOS.models import (
    ApprovalDecision,
    ApprovalDecisionType,
    ApprovalQueueEntry,
    ReviewRequest,
)
from AgenticOS.reviewer_spawner import spawn_reviewer
from AgenticOS.state_watcher import start_watcher

# Configure module logger
logger = logging.getLogger("agentic_server")


# ---------------------------------------------------------------------------
# Connection manager — tracks all active WebSocket client connections
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manages the set of active WebSocket connections.

    All broadcast operations iterate over active_connections and remove
    any that fail (dead connections are cleaned up automatically).
    """

    def __init__(self) -> None:
        # List of all currently connected WebSocket clients
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        # Accept the handshake and register the connection
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        # Remove the connection from the active list on clean close
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected. Total: %d", len(self.active_connections))

    async def broadcast(self, message: str) -> None:
        # Send a text message to all active connections; remove dead ones
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as exc:
                # Connection is dead — mark for removal after iteration
                logger.warning("WebSocket send failed (%s) — removing connection", exc)
                dead.append(connection)
        # Remove all dead connections found during this broadcast
        for connection in dead:
            if connection in self.active_connections:
                self.active_connections.remove(connection)


# Module-level singleton — shared by WebSocket endpoint and broadcast_state()
connection_manager = ConnectionManager()


# ---------------------------------------------------------------------------
# State broadcast — reads agents.json and sends to all WebSocket clients
# ---------------------------------------------------------------------------

async def broadcast_state() -> None:
    """Read agents.json and broadcast its contents to all connected WebSocket clients.

    Called by the watchdog handler whenever agents.json changes.
    Silently handles missing or malformed JSON to avoid crashing the watcher.
    """
    try:
        # Read the current agent state from disk
        raw = AGENTS_JSON.read_text(encoding="utf-8")
        agents_data = json.loads(raw)
    except FileNotFoundError:
        # agents.json does not exist yet — broadcast empty state
        logger.warning("agents.json not found during broadcast — sending empty state")
        agents_data = []
    except json.JSONDecodeError as exc:
        # File is being written mid-read — skip this broadcast cycle
        logger.warning("agents.json JSON parse error during broadcast: %s", exc)
        return

    # Serialize to JSON string for WebSocket transmission
    payload = json.dumps(agents_data)
    await connection_manager.broadcast(payload)


# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan handler — starts the file watcher on startup, stops it on shutdown."""
    # Ensure all required state directories and files exist before serving
    _bootstrap_state_files()

    # Capture the running event loop so the watchdog thread can schedule coroutines
    loop = asyncio.get_running_loop()

    # Start the watchdog observer — returns the observer for shutdown use
    observer = start_watcher(
        broadcast_callback=broadcast_state,
        loop=loop,
        watched_file=AGENTS_JSON,
    )

    logger.info("AgenticOS state bus started on %s:%d", SERVER_HOST, SERVER_PORT)
    yield

    # Clean shutdown — stop the watchdog observer thread
    observer.stop()
    observer.join()
    logger.info("AgenticOS state bus shut down cleanly")


def _bootstrap_state_files() -> None:
    """Create required directories and initialize empty JSON state files on first run."""
    # Create state directory and outputs subdirectory if they do not exist
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize agents.json to an empty array if it does not exist
    if not AGENTS_JSON.exists():
        AGENTS_JSON.write_text("[]", encoding="utf-8")
        logger.info("Initialized empty agents.json at %s", AGENTS_JSON)

    # Initialize approval_queue.json to an empty array if it does not exist
    if not APPROVAL_QUEUE_JSON.exists():
        APPROVAL_QUEUE_JSON.write_text("[]", encoding="utf-8")
        logger.info("Initialized empty approval_queue.json at %s", APPROVAL_QUEUE_JSON)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AgenticOS State Bus",
    description="WebSocket + REST hub for AgenticOS Command Center agent supervision.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server and same-host production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the built React frontend as static files if the dist directory exists
if FRONTEND_DIST_DIR.exists():
    app.mount(
        FRONTEND_MOUNT_PATH,
        StaticFiles(directory=str(FRONTEND_DIST_DIR), html=True),
        name="frontend",
    )
    logger.info("Frontend mounted from %s at %s", FRONTEND_DIST_DIR, FRONTEND_MOUNT_PATH)
else:
    logger.warning(
        "Frontend dist directory not found at %s — skipping static file mount. "
        "Run 'npm run build' inside AgenticOS/frontend/ to build the React app.",
        FRONTEND_DIST_DIR,
    )


# ---------------------------------------------------------------------------
# Helper — approval queue read/write
# ---------------------------------------------------------------------------

def _read_approval_queue() -> list[dict]:
    """Read and parse the current approval_queue.json contents."""
    try:
        raw = APPROVAL_QUEUE_JSON.read_text(encoding="utf-8")
        return json.loads(raw)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Could not read approval_queue.json: %s — treating as empty", exc)
        return []


def _write_approval_queue(queue: list[dict]) -> None:
    """Serialize and write the approval queue list back to disk atomically."""
    APPROVAL_QUEUE_JSON.write_text(json.dumps(queue, indent=2, default=str), encoding="utf-8")


def _append_to_queue(entry: ApprovalQueueEntry) -> None:
    """Read the current queue, append one entry, and write it back."""
    queue = _read_approval_queue()
    queue.append(entry.model_dump(mode="json"))
    _write_approval_queue(queue)
    logger.info("Appended decision '%s' for %s to approval queue", entry.decision, entry.agent_id)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check() -> JSONResponse:
    """Liveness endpoint — returns ok if the server is running."""
    return JSONResponse({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.post("/approve/{agent_id}")
async def approve_agent(agent_id: str, body: ApprovalDecision) -> JSONResponse:
    """Record a proceed decision for the specified agent.

    Appends a proceed entry to approval_queue.json.
    The waiting agent polls this file and reads its gate decision.
    """
    entry = ApprovalQueueEntry(
        agent_id=agent_id,
        decision=ApprovalDecisionType.PROCEED,
        reviewer_context=None,
        decided_at=datetime.now(timezone.utc),
    )
    _append_to_queue(entry)

    return JSONResponse({
        "agent_id": agent_id,
        "decision": ApprovalDecisionType.PROCEED.value,
        "decided_at": entry.decided_at.isoformat(),
    })


@app.post("/research/{agent_id}")
async def research_agent(agent_id: str, body: ApprovalDecision) -> JSONResponse:
    """Record a research decision for the specified agent.

    Appends a research entry to approval_queue.json.
    The waiting agent reads this as a signal to spawn a research sub-agent.
    """
    entry = ApprovalQueueEntry(
        agent_id=agent_id,
        decision=ApprovalDecisionType.RESEARCH,
        reviewer_context=None,
        decided_at=datetime.now(timezone.utc),
    )
    _append_to_queue(entry)

    return JSONResponse({
        "agent_id": agent_id,
        "decision": ApprovalDecisionType.RESEARCH.value,
        "decided_at": entry.decided_at.isoformat(),
    })


@app.post("/review/{agent_id}")
async def review_agent(agent_id: str, body: ReviewRequest) -> JSONResponse:
    """Spawn a Claude Haiku reviewer for the specified agent's output.

    1. Appends a review entry to approval_queue.json.
    2. Calls spawn_reviewer() to invoke Claude Haiku via subprocess.
    3. The reviewer verdict is written to state/outputs/agent-{id}-review.md.
    4. The watchdog detects the new file and broadcasts updated state.

    reviewer_context in the request body is the path to the agent's output file.
    If omitted, the server attempts to read output_ref from agents.json.
    """
    # Resolve the reviewer context path — use request body or fall back to agents.json
    reviewer_context = body.reviewer_context
    if reviewer_context is None:
        reviewer_context = _resolve_output_ref(agent_id)

    if reviewer_context is None:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No reviewer_context provided and no output_ref found "
                f"in agents.json for {agent_id}"
            ),
        )

    # Write the decision to the queue before spawning (agent can see it immediately)
    entry = ApprovalQueueEntry(
        agent_id=agent_id,
        decision=ApprovalDecisionType.REVIEW,
        reviewer_context=reviewer_context,
        decided_at=datetime.now(timezone.utc),
    )
    _append_to_queue(entry)

    # Spawn the reviewer subprocess — this is synchronous but bounded by REVIEWER_TIMEOUT_SECONDS
    spawn_reviewer(agent_id=agent_id, reviewer_context=reviewer_context)

    return JSONResponse({
        "agent_id": agent_id,
        "decision": ApprovalDecisionType.REVIEW.value,
        "reviewer_context": reviewer_context,
        "decided_at": entry.decided_at.isoformat(),
    })


def _resolve_output_ref(agent_id: str) -> str | None:
    """Look up the output_ref for a given agent_id in agents.json.

    Returns the output_ref string, or None if the agent is not found.
    """
    try:
        agents = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
        for agent in agents:
            if agent.get("agent_id") == agent_id:
                return agent.get("output_ref")
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Could not read agents.json for output_ref lookup: %s", exc)
    return None


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint at ws://localhost:7842/ws.

    On connect: register the client and immediately broadcast current state.
    On disconnect: remove the client from active_connections.
    Messages from clients are acknowledged but not processed (server is broadcast-only).
    """
    await connection_manager.connect(websocket)

    # Immediately send current state to the newly connected client
    await broadcast_state()

    try:
        while True:
            # Keep the connection alive by waiting for client messages
            # Client messages are not currently acted on — server pushes state
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Normal client disconnect — clean up
        connection_manager.disconnect(websocket)
    except Exception as exc:
        # Unexpected error — log and clean up
        logger.error("WebSocket error: %s", exc)
        connection_manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Configure logging for direct script execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    # Start the ASGI server — port and host come from config, never hardcoded
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
```

### 10.2 Verify the app imports cleanly

```bash
cd C:/ClaudeSkills && python -c "from AgenticOS.agentic_server import app, broadcast_state, connection_manager; print('OK')"
```

Expected: `OK`

### Commit

```bash
git add C:/ClaudeSkills/AgenticOS/agentic_server.py
git commit -m "feat(agentic-os): implement agentic_server.py — FastAPI state bus with WebSocket and REST endpoints"
```

---

## Step 11 — Run All Tests (3 min)

### 11.1 Run the full AgenticOS test suite

```bash
cd C:/ClaudeSkills && python -m pytest tests/AgenticOS/ -v
```

### 11.2 Expected output — all green

```
tests/AgenticOS/test_models.py::TestAgentState::test_valid_active_agent PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_progress_pct_upper_bound PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_progress_pct_lower_bound PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_context_pct_used_bounds PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_stage_must_not_exceed_total_stages PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_waiting_approval_status_with_awaiting_field PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_error_status_with_error_msg PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_all_domains_valid PASSED
tests/AgenticOS/test_models.py::TestAgentState::test_serializes_to_dict PASSED
tests/AgenticOS/test_models.py::TestApprovalDecision::test_proceed_decision PASSED
tests/AgenticOS/test_models.py::TestApprovalDecision::test_research_decision PASSED
tests/AgenticOS/test_models.py::TestApprovalDecision::test_invalid_decision_rejected PASSED
tests/AgenticOS/test_models.py::TestReviewRequest::test_valid_review_request PASSED
tests/AgenticOS/test_models.py::TestReviewRequest::test_reviewer_context_defaults_to_none PASSED
tests/AgenticOS/test_models.py::TestApprovalQueueEntry::test_full_entry PASSED
tests/AgenticOS/test_models.py::TestApprovalQueueEntry::test_reviewer_context_optional PASSED

tests/AgenticOS/test_state_bus.py::TestApproveEndpoint::test_approve_returns_200 PASSED
tests/AgenticOS/test_state_bus.py::TestApproveEndpoint::test_approve_writes_to_queue PASSED
tests/AgenticOS/test_state_bus.py::TestApproveEndpoint::test_approve_response_body PASSED
tests/AgenticOS/test_state_bus.py::TestApproveEndpoint::test_approve_invalid_decision_rejected PASSED
tests/AgenticOS/test_state_bus.py::TestApproveEndpoint::test_approve_multiple_agents_accumulate PASSED
tests/AgenticOS/test_state_bus.py::TestResearchEndpoint::test_research_returns_200 PASSED
tests/AgenticOS/test_state_bus.py::TestResearchEndpoint::test_research_writes_research_decision PASSED
tests/AgenticOS/test_state_bus.py::TestReviewEndpoint::test_review_returns_200 PASSED
tests/AgenticOS/test_state_bus.py::TestReviewEndpoint::test_review_writes_review_decision_to_queue PASSED
tests/AgenticOS/test_state_bus.py::TestReviewEndpoint::test_review_calls_spawn_reviewer PASSED
tests/AgenticOS/test_state_bus.py::TestBroadcastState::test_broadcast_sends_to_connected_clients PASSED
tests/AgenticOS/test_state_bus.py::TestBroadcastState::test_broadcast_handles_empty_agents_file PASSED
tests/AgenticOS/test_state_bus.py::TestBroadcastState::test_broadcast_handles_no_connections PASSED
tests/AgenticOS/test_state_bus.py::TestBroadcastState::test_broadcast_skips_dead_connections PASSED
tests/AgenticOS/test_state_bus.py::TestHealthEndpoint::test_health_returns_200 PASSED
tests/AgenticOS/test_state_bus.py::TestHealthEndpoint::test_health_returns_status_ok PASSED

tests/AgenticOS/test_reviewer.py::TestBuildReviewerPrompt::test_includes_content PASSED
tests/AgenticOS/test_reviewer.py::TestBuildReviewerPrompt::test_includes_instructions PASSED
tests/AgenticOS/test_reviewer.py::TestBuildReviewerPrompt::test_missing_file_raises_file_not_found PASSED
tests/AgenticOS/test_reviewer.py::TestSpawnReviewer::test_writes_verdict_file PASSED
tests/AgenticOS/test_reviewer.py::TestSpawnReviewer::test_verdict_file_contains_agent_id PASSED
tests/AgenticOS/test_reviewer.py::TestSpawnReviewer::test_subprocess_called_with_correct_model PASSED
tests/AgenticOS/test_reviewer.py::TestSpawnReviewer::test_nonzero_returncode_raises PASSED
tests/AgenticOS/test_reviewer.py::TestSpawnReviewer::test_missing_output_file_raises PASSED

================= 39 passed in X.XXs =================
```

If any test fails, fix the implementation before committing. Do not disable or skip tests.

### 11.3 Smoke-test the running server

```bash
cd C:/ClaudeSkills && python -m AgenticOS.agentic_server &
sleep 3
curl http://localhost:7842/health
```

Expected:
```json
{"status": "ok", "timestamp": "2026-04-29T..."}
```

Kill the server after confirming: `kill %1`

### Final commit

```bash
git add C:/ClaudeSkills/tests/AgenticOS/test_state_bus.py
git commit -m "test(agentic-os): add full state bus and reviewer integration tests — 39 passing"
```

---

## Step 12 — Final State Verification (2 min)

Confirm every file is in place:

```bash
ls C:/ClaudeSkills/AgenticOS/
# Expected: __init__.py  agentic_server.py  config.py  models.py  reviewer_spawner.py  state/  state_watcher.py

ls C:/ClaudeSkills/AgenticOS/state/
# Expected: agents.json  approval_queue.json  outputs/

ls C:/ClaudeSkills/tests/AgenticOS/
# Expected: __init__.py  test_models.py  test_reviewer.py  test_state_bus.py
```

Confirm scripts/requirements.txt includes all three new dependencies:

```bash
grep -E "fastapi|uvicorn|pydantic" C:/ClaudeSkills/scripts/requirements.txt
```

Expected:
```
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.0
```

---

## Self-Review Checklist

### Spec Coverage

- [x] Serves React frontend static files from `AgenticOS/frontend/dist/` — mounted at `/app` in agentic_server.py
- [x] WebSocket endpoint at `ws://localhost:7842/ws` — implemented in `websocket_endpoint()`
- [x] Watchdog on `agents.json` — `state_watcher.py` with `AgentsJsonHandler`, started in `lifespan()`
- [x] `POST /approve/{agent_id}` with `{"decision": "proceed"}` — writes to approval_queue.json
- [x] `POST /research/{agent_id}` with `{"decision": "research"}` — writes to approval_queue.json
- [x] `POST /review/{agent_id}` — spawns Claude Haiku subprocess, writes verdict to `state/outputs/agent-{id}-review.md`
- [x] Pydantic models for all state shapes — `AgentState`, `ApprovalDecision`, `ReviewRequest`, `ApprovalQueueEntry`
- [x] CORS configured for localhost — `CORS_ORIGINS` list in config.py
- [x] `agents.json` and `approval_queue.json` created as `[]` on first run — `_bootstrap_state_files()`
- [x] `state/outputs/` directory created on first run — `_bootstrap_state_files()`
- [x] All fields in `AgentState` spec covered — all 14 fields modeled with correct types
- [x] All status values covered — `active`, `waiting_approval`, `waiting_review`, `complete`, `error`
- [x] All domain values covered — `va-advisory`, `game-dev`, `software-eng`, `3d-content`, `general`
- [x] Approval queue shape matches spec — all 4 fields present in `ApprovalQueueEntry`

### Placeholder Scan

- [x] No `TODO` or `FIXME` or `pass` in any implementation file
- [x] No `...` ellipsis used as a body placeholder
- [x] No `raise NotImplementedError` in any implementation file
- [x] No hardcoded port numbers — all use `SERVER_PORT` from config.py
- [x] No hardcoded paths — all use `Path` constants from config.py
- [x] No hardcoded model strings — `REVIEWER_MODEL` from config.py
- [x] No hardcoded timeouts — `REVIEWER_TIMEOUT_SECONDS` from config.py

### Type Consistency

- [x] All function parameters and return values have type hints
- [x] All Pydantic fields are typed
- [x] `Optional[str]` used consistently for nullable string fields
- [x] `list[str]` / `list[dict]` used (not `List` from `typing` — Python 3.10+ generics)
- [x] `datetime` fields use `datetime.now(timezone.utc)` — timezone-aware, never naive

### Coding Standards

- [x] File header on every file: filename, developer (Marcus Daley), date (2026-04-29), purpose
- [x] Single-line `#` comments on every function and non-obvious line
- [x] Zero hardcoded values — all in config.py
- [x] Named constants only (enums for all string discriminators)
- [x] `from __future__ import annotations` on all implementation files

### Test Coverage

- [x] TDD order followed: failing test written before every implementation
- [x] 39 total tests across 3 test files
- [x] All REST endpoints covered (approve, research, review, health)
- [x] WebSocket broadcast covered (normal, empty, no connections, dead connections)
- [x] Model validation covered (bounds, enums, optional fields, cross-field validation)
- [x] Reviewer spawner covered (prompt building, subprocess mock, error handling)
- [x] Every test uses `monkeypatch` or `unittest.mock` — no live filesystem or subprocess calls in tests

---

## Deliverables After Plan Execution

| File | Description |
|---|---|
| `C:\ClaudeSkills\AgenticOS\__init__.py` | Package init |
| `C:\ClaudeSkills\AgenticOS\config.py` | All constants |
| `C:\ClaudeSkills\AgenticOS\models.py` | Pydantic models |
| `C:\ClaudeSkills\AgenticOS\state_watcher.py` | Watchdog handler |
| `C:\ClaudeSkills\AgenticOS\reviewer_spawner.py` | Claude Haiku subprocess spawner |
| `C:\ClaudeSkills\AgenticOS\agentic_server.py` | FastAPI state bus (main file) |
| `C:\ClaudeSkills\AgenticOS\state\agents.json` | Initialized as `[]` |
| `C:\ClaudeSkills\AgenticOS\state\approval_queue.json` | Initialized as `[]` |
| `C:\ClaudeSkills\AgenticOS\state\outputs\` | Directory created |
| `C:\ClaudeSkills\tests\AgenticOS\__init__.py` | Test package init |
| `C:\ClaudeSkills\tests\AgenticOS\test_models.py` | 16 Pydantic model tests |
| `C:\ClaudeSkills\tests\AgenticOS\test_state_bus.py` | 15 endpoint + WebSocket tests |
| `C:\ClaudeSkills\tests\AgenticOS\test_reviewer.py` | 8 reviewer spawner tests |
| `C:\ClaudeSkills\scripts\requirements.txt` | Updated with fastapi, uvicorn, pydantic |

**Total: 39 tests, 0 placeholders, 0 hardcoded values.**

---

## Next Plan

Plan 2 of 5: `agentic_dashboard.py` — WPF system tray launcher that starts `agentic_server.py` as a managed subprocess and hosts the React UI in a WebView2 window.
