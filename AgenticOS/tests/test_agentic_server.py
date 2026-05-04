# test_agentic_server.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Endpoint integration tests for agentic_server.py. Uses
#          httpx.ASGITransport so the lifespan handler runs and the
#          watchdog observer is exercised end-to-end. Reviewer
#          subprocess calls are patched so no Claude CLI is invoked.

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

import httpx
import pytest

from AgenticOS import agentic_server, reviewer_spawner, state_store, task_store
from AgenticOS.models import (
    AgentDomain,
    AgentState,
    AgentStatus,
    ApprovalKind,
    AgenticTask,
    ReviewerOutcome,
    ReviewerVerdict,
    TerminalActionResult,
    TerminalWindow,
    TaskStatus,
)


# ---------------------------------------------------------------------------
# Test data builder
# ---------------------------------------------------------------------------

def _make_agent(agent_id: str, output_ref: str | None = None) -> AgentState:
    """Construct a minimal AgentState; output_ref is parameterised so
    review tests can point at a real file on disk."""
    return AgentState(
        agent_id=agent_id,
        domain=AgentDomain.GENERAL,
        task="server test",
        stage_label="step",
        stage=1,
        total_stages=2,
        progress_pct=50,
        status=AgentStatus.WAITING_APPROVAL,
        context_pct_used=10,
        output_ref=output_ref,
        awaiting=ApprovalKind.PROCEED,
        updated_at=datetime.now(timezone.utc),
    )


def _make_task(task_id: str = "task-001") -> AgenticTask:
    """Construct a valid canonical task runtime record."""
    now = datetime.now(timezone.utc)
    return AgenticTask(
        id=task_id,
        title="server task",
        status=TaskStatus.PENDING,
        assigned_to=None,
        dependencies=[],
        priority=1,
        locked_by=None,
        created_at=now,
        updated_at=now,
        checkpoints=[],
        output=None,
    )


def _make_terminal() -> TerminalWindow:
    """Construct one visible terminal-control payload."""
    return TerminalWindow(
        hwnd=1001,
        pid=9001,
        title="CLAW worker",
        process_name="cmd.exe",
        executable="C:/Windows/System32/cmd.exe",
        cwd="C:/ClaudeSkills",
        command_line="cmd.exe /k claw",
        is_visible=True,
        is_agent_like=True,
        detected_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    """Redirect every state path used by the server module to a tmp
    directory so tests are hermetic. Returns the resolved paths so
    assertions can read them back directly."""
    state_dir = tmp_path / "state"
    outputs_dir = state_dir / "outputs"
    task_runtime_dir = tmp_path / "agentic-os"
    state_dir.mkdir()
    outputs_dir.mkdir()

    agents_path = state_dir / "agents.json"
    queue_path = state_dir / "approval_queue.json"
    agents_path.write_text("[]", encoding="utf-8")
    queue_path.write_text("[]", encoding="utf-8")

    # Patch the references the server imported at module load time.
    monkeypatch.setattr(agentic_server, "AGENTS_JSON", agents_path)
    monkeypatch.setattr(agentic_server, "APPROVAL_QUEUE_JSON", queue_path)
    monkeypatch.setattr(agentic_server, "STATE_DIR", state_dir)
    monkeypatch.setattr(agentic_server, "OUTPUTS_DIR", outputs_dir)
    # Patch the underlying state_store defaults too so any helper that
    # falls back to the module default still hits tmp.
    monkeypatch.setattr(state_store, "AGENTS_JSON", agents_path)
    monkeypatch.setattr(state_store, "APPROVAL_QUEUE_JSON", queue_path)
    monkeypatch.setattr(task_store, "AGENTIC_TASK_RUNTIME_DIR", task_runtime_dir)

    return {
        "state_dir": state_dir,
        "outputs_dir": outputs_dir,
        "agents_path": agents_path,
        "queue_path": queue_path,
        "task_runtime_dir": task_runtime_dir,
    }


@pytest.fixture
async def client(
    isolated_state: dict[str, Path],
) -> AsyncIterator[httpx.AsyncClient]:
    """Build an ASGI-bound httpx client with lifespan support so
    startup/shutdown handlers run during the test."""
    transport = httpx.ASGITransport(app=agentic_server.app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as http_client:
        # Trigger startup by issuing a healthz call before the body of
        # the test runs. ASGITransport executes lifespan once per
        # client lifetime under the hood.
        yield http_client


# ---------------------------------------------------------------------------
# 1. /healthz
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_healthz_returns_status_ok(client: httpx.AsyncClient) -> None:
    """Liveness endpoint returns 200 with status=ok and reports the
    configured ports back to the caller."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "websocket_port" in body and "rest_port" in body


# ---------------------------------------------------------------------------
# 2. POST /approve/{agent_id} writes a proceed entry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_writes_proceed_entry(
    client: httpx.AsyncClient,
    isolated_state: dict[str, Path],
) -> None:
    """POST /approve must append a proceed entry to approval_queue.json
    and respond with the recorded fields."""
    response = await client.post(
        "/approve/AGENT-01",
        json={"decision": "proceed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["agent_id"] == "AGENT-01"
    assert body["decision"] == ApprovalKind.PROCEED.value

    queue = json.loads(isolated_state["queue_path"].read_text(encoding="utf-8"))
    assert len(queue) == 1
    assert queue[0]["agent_id"] == "AGENT-01"
    assert queue[0]["decision"] == ApprovalKind.PROCEED.value


# ---------------------------------------------------------------------------
# 3. POST /research/{agent_id} writes a research entry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_research_writes_research_entry(
    client: httpx.AsyncClient,
    isolated_state: dict[str, Path],
) -> None:
    """POST /research must append a research entry to the queue."""
    response = await client.post(
        "/research/AGENT-02",
        json={"decision": "research"},
    )
    assert response.status_code == 200
    queue = json.loads(isolated_state["queue_path"].read_text(encoding="utf-8"))
    assert queue[0]["decision"] == ApprovalKind.RESEARCH.value
    assert queue[0]["agent_id"] == "AGENT-02"


# ---------------------------------------------------------------------------
# 4. GET /agents returns the current state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_agents_returns_current_state(
    client: httpx.AsyncClient,
    isolated_state: dict[str, Path],
) -> None:
    """GET /agents must return whatever is currently in agents.json,
    parsed and validated through the state_store."""
    state_store.write_agents(
        [_make_agent("AGENT-A"), _make_agent("AGENT-B")],
        path=isolated_state["agents_path"],
    )
    response = await client.get("/agents")
    assert response.status_code == 200
    body = response.json()
    assert {a["agent_id"] for a in body} == {"AGENT-A", "AGENT-B"}


# ---------------------------------------------------------------------------
# 5. POST /review/{agent_id} spawns the reviewer with the resolved context
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_review_spawns_reviewer_and_records_decision(
    client: httpx.AsyncClient,
    isolated_state: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """POST /review must record a review entry, call the async
    spawner, and surface the verdict outcome in the response."""
    # Seed a real file the server can verify exists before recording.
    output_file = isolated_state["outputs_dir"] / "agent-AGENT-01-stage-2.md"
    output_file.write_text("agent output content", encoding="utf-8")

    # Patch the async spawner so no real subprocess runs. Returning a
    # fully-formed ReviewerVerdict mirrors the production contract.
    async def _fake_spawn(
        agent_id: str,
        reviewer_context: str,
        outputs_dir: Path = isolated_state["outputs_dir"],
    ) -> ReviewerVerdict:
        return ReviewerVerdict(
            agent_id=agent_id,
            outcome=ReviewerOutcome.PASS,
            notes="PASS: looks fine",
            reviewed_context=reviewer_context,
            verdict_path=str(isolated_state["outputs_dir"] / "stub.md"),
            reviewed_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(agentic_server, "spawn_reviewer_async", _fake_spawn)

    response = await client.post(
        "/review/AGENT-01",
        json={
            "decision": "review",
            "reviewer_context": str(output_file),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["agent_id"] == "AGENT-01"
    assert body["decision"] == ApprovalKind.REVIEW.value
    assert body["verdict_outcome"] == ReviewerOutcome.PASS.value

    # Decision must have been persisted to the queue with the context.
    queue = json.loads(isolated_state["queue_path"].read_text(encoding="utf-8"))
    assert queue[0]["reviewer_context"] == str(output_file)


# ---------------------------------------------------------------------------
# 6. Invalid decision payload rejected with 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_decision_returns_422(
    client: httpx.AsyncClient,
) -> None:
    """A decision string outside the ApprovalKind enum must be
    rejected by the Pydantic body validator."""
    response = await client.post(
        "/approve/AGENT-01",
        json={"decision": "totally-bogus"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 7. Canonical task runtime endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_task_endpoints_claim_checkpoint_and_complete(
    client: httpx.AsyncClient,
    isolated_state: dict[str, Path],
) -> None:
    """Task REST endpoints must drive the canonical task_store API."""
    task_store.write_task(_make_task(), isolated_state["task_runtime_dir"])

    claim_response = await client.post(
        "/tasks/task-001/claim",
        json={"agent_id": "agent-terminal-3"},
    )
    assert claim_response.status_code == 200, claim_response.text
    assert claim_response.json()["status"] == TaskStatus.IN_PROGRESS.value

    conflict_response = await client.post(
        "/tasks/task-001/claim",
        json={"agent_id": "agent-terminal-4"},
    )
    assert conflict_response.status_code == 409

    checkpoint_response = await client.post(
        "/tasks/task-001/checkpoint",
        json={"checkpoint": {"message": "halfway"}},
    )
    assert checkpoint_response.status_code == 200
    assert checkpoint_response.json()["checkpoints"][-1]["message"] == "halfway"

    complete_response = await client.post(
        "/tasks/task-001/complete",
        json={"output": {"result": "done"}},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == TaskStatus.COMPLETE.value

    snapshot_response = await client.get("/tasks/snapshot")
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["tasks"][0]["id"] == "task-001"


@pytest.mark.asyncio
async def test_skill_action_dispatch_creates_watched_task(
    client: httpx.AsyncClient,
    isolated_state: dict[str, Path],
) -> None:
    """Skill action buttons create canonical tasks for the watched panel."""
    response = await client.post(
        "/skill-actions/agentforge-agent-contracts/run",
        json={
            "objective": "Add a new planner agent test.",
            "project_path": str(Path("C:/Users/daley/Projects/SeniorDevBuddy")),
            "project_name": "SeniorDevBuddy",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    task = body["task"]
    assert task["id"].startswith("skill-agentforge-agent-contracts-")
    assert task["assigned_to"] == "skill-agent-contracts"
    assert task["status"] == TaskStatus.PENDING.value
    assert "Use $agentforge-agent-contracts" in body["prompt"]

    snapshot_response = await client.get("/tasks/snapshot")
    assert snapshot_response.status_code == 200
    ids = {item["id"] for item in snapshot_response.json()["tasks"]}
    assert task["id"] in ids


@pytest.mark.asyncio
async def test_task_fail_endpoint_requires_error_context(
    client: httpx.AsyncClient,
    isolated_state: dict[str, Path],
) -> None:
    """The failure endpoint rejects ambiguous failure payloads."""
    task_store.write_task(_make_task(), isolated_state["task_runtime_dir"])
    await client.post(
        "/tasks/task-001/claim",
        json={"agent_id": "agent-terminal-3"},
    )

    bad_response = await client.post("/tasks/task-001/fail", json={})
    assert bad_response.status_code == 422

    fail_response = await client.post(
        "/tasks/task-001/fail",
        json={"error_context": {"error": "boom"}},
    )
    assert fail_response.status_code == 200
    assert fail_response.json()["status"] == TaskStatus.FAILED.value


# ---------------------------------------------------------------------------
# 8. Terminal control endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_terminal_list_endpoint_returns_visible_windows(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /terminals returns the terminal-control inventory payload."""
    terminal = _make_terminal()
    seen_agent_only: list[bool] = []

    def _fake_list(agent_only: bool = False) -> list[TerminalWindow]:
        seen_agent_only.append(agent_only)
        return [terminal]

    monkeypatch.setattr(agentic_server, "list_terminal_windows", _fake_list)

    response = await client.get("/terminals?agent_only=true")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["title"] == "CLAW worker"
    assert body[0]["is_agent_like"] is True
    assert seen_agent_only == [True]


@pytest.mark.asyncio
async def test_terminal_focus_and_close_endpoints_return_action_results(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal focus and close commands pass handles to control helpers."""
    focused: list[int] = []
    closed: list[int] = []

    def _fake_focus(hwnd: int) -> TerminalActionResult:
        focused.append(hwnd)
        return TerminalActionResult(ok=True, hwnd=hwnd, message="focused")

    def _fake_close(hwnd: int) -> TerminalActionResult:
        closed.append(hwnd)
        return TerminalActionResult(ok=True, hwnd=hwnd, message="closed")

    monkeypatch.setattr(agentic_server, "focus_terminal_window", _fake_focus)
    monkeypatch.setattr(agentic_server, "close_terminal_window", _fake_close)

    focus_response = await client.post("/terminals/1001/focus")
    close_response = await client.post("/terminals/1001/close")

    assert focus_response.status_code == 200
    assert close_response.status_code == 200
    assert focus_response.json()["message"] == "focused"
    assert close_response.json()["message"] == "closed"
    assert focused == [1001]
    assert closed == [1001]


@pytest.mark.asyncio
async def test_terminal_terminate_requires_confirmation(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Process termination is blocked unless the exact confirmation is sent."""
    terminated: list[int] = []

    def _fake_terminate(pid: int) -> TerminalActionResult:
        terminated.append(pid)
        return TerminalActionResult(ok=True, pid=pid, message="terminated")

    monkeypatch.setattr(agentic_server, "terminate_terminal_process", _fake_terminate)

    rejected = await client.post("/terminals/9001/terminate", json={"confirm": "yes"})
    accepted = await client.post(
        "/terminals/9001/terminate",
        json={"confirm": "TERMINATE"},
    )

    assert rejected.status_code == 422
    assert accepted.status_code == 200
    assert accepted.json()["message"] == "terminated"
    assert terminated == [9001]
