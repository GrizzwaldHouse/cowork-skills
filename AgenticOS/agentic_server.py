# agentic_server.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: FastAPI state bus for the AgenticOS Command Center. Hosts the
#          WebSocket endpoint that streams agent state diffs to the
#          React UI, exposes the REST endpoints used by the approval
#          buttons, mounts the watchdog observer on startup, and serves
#          the built React frontend as static files when present.

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from AgenticOS.config import (
    AGENTS_JSON,
    APPROVAL_QUEUE_JSON,
    CORS_ORIGINS,
    FRONTEND_DIST_DIR,
    FRONTEND_MOUNT_PATH,
    LOGGER_NAME,
    OUTPUTS_DIR,
    REST_PORT,
    SERVER_HOST,
    STATE_DIR,
    TERMINAL_CONTROL_TERMINATE_CONFIRMATION,
    WEBSOCKET_PORT,
)
from AgenticOS.file_watcher import start_file_watcher
from AgenticOS.models import (
    AgentState,
    ApprovalDecision,
    ApprovalKind,
    ApprovalQueueEntry,
    WorkflowEvent,
)
from AgenticOS.reviewer_spawner import (
    ReviewerSpawnError,
    spawn_reviewer_async,
)
from AgenticOS.state_store import (
    StateSchemaError,
    append_approval_entry,
    bootstrap_state_files,
    read_agents,
)
from AgenticOS.skill_actions import (
    dispatch_skill_action,
    list_skill_actions,
)
from AgenticOS.task_store import (
    TaskConflictError,
    TaskNotFoundError,
    TaskRuntimeError,
    bootstrap_task_runtime,
    claim_task,
    complete_task,
    fail_task,
    read_snapshot,
    read_task,
    read_tasks,
    reconcile_task_runtime,
    update_task_checkpoint,
)
from AgenticOS.task_watcher import start_task_watcher
from AgenticOS.terminal_control import (
    close_terminal_window,
    focus_terminal_window,
    list_terminal_windows,
    terminate_terminal_process,
)
from AgenticOS.websocket_broadcaster import (
    WebSocketBroadcaster,
    get_broadcaster,
)

# Phase 2 expansion (2026-04-29): bridge + progress log integration.
from AgenticOS.progress_log import progress_log
from AgenticOS.session_bridge import run_bridge_loop

# Phase 1 (2026-04-30): project registry + discovery daemon.
from AgenticOS.project_registry import registry as project_registry
from AgenticOS.project_watcher import run_project_watcher

# Handoff manifest REST support.
from AgenticOS.handoff_writer import handoff_status_payload


# Module logger; child of the project-wide AgenticOS logger.
_logger = logging.getLogger(f"{LOGGER_NAME}.server")


# ---------------------------------------------------------------------------
# Application state container
#
# Holds references to the watchdog Observer and the broadcaster so the
# lifespan handler can shut them down cleanly. Stored on the FastAPI
# app instance via app.state to avoid module-level mutable state.
# ---------------------------------------------------------------------------

class _ServerState:
    """Per-app runtime state. One instance per FastAPI app."""

    def __init__(self) -> None:
        # Watchdog observer started by the lifespan handler. None until
        # startup completes.
        self.observer: Optional[object] = None

        # The shared WebSocket broadcaster, populated on startup.
        self.broadcaster: Optional[WebSocketBroadcaster] = None

        # Phase 2 expansion (2026-04-29): the asyncio task that runs
        # the session discovery bridge, plus the Event used to ask it
        # to stop. Both are populated in the lifespan handler.
        self.bridge_task: Optional[asyncio.Task] = None
        self.bridge_stop_event: Optional[asyncio.Event] = None

        # Phase 1 (2026-04-30): project discovery daemon task + stop event.
        self.watcher_task: Optional[asyncio.Task] = None
        self.watcher_stop_event: Optional[asyncio.Event] = None

        # Hybrid task runtime watchdog. Observes the canonical lowercase
        # agentic-os/tasks and agentic-os/locks tree.
        self.task_observer: Optional[object] = None


# ---------------------------------------------------------------------------
# Broadcast bridge between watchdog events and the broadcaster
# ---------------------------------------------------------------------------

async def _broadcast_current_agents(broadcaster: WebSocketBroadcaster) -> None:
    """Read agents.json through the validated state_store and push the
    result to every connected client. Errors during read are logged
    but never re-raised: the watcher must keep firing."""
    try:
        agents = read_agents(AGENTS_JSON)
    except StateSchemaError as exc:
        # Malformed file or schema mismatch. Most likely cause is a
        # mid-write read race; the next event will retry.
        _logger.warning("Skipping broadcast; agents.json invalid: %s", exc)
        return
    except Exception as exc:
        # Defensive: any unexpected error gets logged and swallowed so
        # the watchdog thread is not poisoned.
        _logger.exception("Unexpected error reading agents.json: %s", exc)
        return

    await broadcaster.broadcast_state(agents)


# ---------------------------------------------------------------------------
# Lifespan handler — wires up watchdog + broadcaster on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Bootstrap state files, start the watchdog observer, and tear
    everything down cleanly on shutdown."""
    # 1. Make sure required directories and seed JSON files exist.
    bootstrap_state_files()
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    bootstrap_task_runtime()

    # 2. Acquire the broadcaster singleton and stash it on app.state.
    state: _ServerState = app.state.runtime
    state.broadcaster = get_broadcaster()

    # 3. Capture the live event loop. Watchdog runs on a background
    # thread and uses run_coroutine_threadsafe to call back into here.
    loop = asyncio.get_running_loop()

    # 4. Build a closure that the watcher can invoke without needing
    # to know about FastAPI internals.
    async def on_state_change() -> None:
        # The broadcaster is always present here; checked above.
        assert state.broadcaster is not None
        await _broadcast_current_agents(state.broadcaster)

    # 5. Start watching agents.json and remember the observer so we
    # can stop it during shutdown.
    state.observer = start_file_watcher(
        broadcast_callback=on_state_change,
        loop=loop,
        watched_file=AGENTS_JSON,
    )

    # 5b. Start the canonical task runtime watcher. The watcher reacts
    # to task and lock file events, reconciles ownership/readiness, then
    # bridges task cards into agents.json for the existing dashboard.
    reconcile_task_runtime()
    state.task_observer = start_task_watcher(
        broadcast_callback=on_state_change,
        loop=loop,
    )

    # 6. Start the session-discovery bridge as a long-running asyncio
    # task. The bridge polls the Cowork sessions root, translates each
    # discovered session into an AgentState, and writes the merged
    # list to agents.json -- the watcher above picks up that write
    # and broadcasts it. We use an asyncio.Event for shutdown rather
    # than cancellation so the bridge can drain its current cycle.
    state.bridge_stop_event = asyncio.Event()
    state.bridge_task = asyncio.create_task(
        run_bridge_loop(state.bridge_stop_event)
    )

    # 6b. Open the project registry database and start the project
    # discovery daemon. The daemon watches configured root paths for
    # new CLAUDE.md files and polls for claude.exe processes.
    await project_registry.open()
    state.watcher_stop_event = asyncio.Event()
    state.watcher_task = asyncio.create_task(
        run_project_watcher(state.watcher_stop_event, project_registry)
    )

    # 7. Push the initial state so the broadcaster's last_state cache
    # matches reality before any clients connect.
    await _broadcast_current_agents(state.broadcaster)

    _logger.info(
        "AgenticOS state bus ready on http://%s:%d (REST) / ws://%s:%d/ws",
        SERVER_HOST, REST_PORT, SERVER_HOST, WEBSOCKET_PORT,
    )

    try:
        yield
    finally:
        # Shutdown: stop the watchdog thread, drain the broadcaster.
        # Stop the bridge first so it does not race with watchdog
        # shutdown when both try to access agents.json.
        bridge_stop_event = getattr(state, "bridge_stop_event", None)
        bridge_task = getattr(state, "bridge_task", None)
        if bridge_stop_event is not None:
            bridge_stop_event.set()
        if bridge_task is not None:
            try:
                await asyncio.wait_for(bridge_task, timeout=5.0)
            except asyncio.TimeoutError:
                bridge_task.cancel()
                _logger.warning("Bridge task did not stop within 5s; cancelled")

        # Stop the project discovery daemon.
        watcher_stop_event = getattr(state, "watcher_stop_event", None)
        watcher_task = getattr(state, "watcher_task", None)
        if watcher_stop_event is not None:
            watcher_stop_event.set()
        if watcher_task is not None:
            try:
                await asyncio.wait_for(watcher_task, timeout=5.0)
            except asyncio.TimeoutError:
                watcher_task.cancel()
                _logger.warning("Project watcher did not stop within 5s; cancelled")

        # Close the project registry database connection.
        await project_registry.close()

        if state.observer is not None:
            state.observer.stop()
            state.observer.join()
            state.observer = None
        if state.task_observer is not None:
            state.task_observer.stop()
            state.task_observer.join()
            state.task_observer = None
        if state.broadcaster is not None:
            await state.broadcaster.reset()
        _logger.info("AgenticOS state bus shut down cleanly")


# ---------------------------------------------------------------------------
# FastAPI application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Build a configured FastAPI instance. Exposed as a factory so
    tests can construct fresh apps without the global side effects of
    a module-level singleton."""
    application = FastAPI(
        title="AgenticOS State Bus",
        description=(
            "WebSocket and REST hub powering the AgenticOS Command Center. "
            "Streams agent state diffs to the React UI and accepts approval "
            "decisions from the operator."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # Attach the runtime state container so the lifespan handler and
    # endpoint handlers can share access to the observer + broadcaster.
    application.state.runtime = _ServerState()

    # CORS for the Vite dev server and same-host production build.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Mount static frontend if a build is present. We do this at app
    # construction time so OpenAPI introspection sees the route.
    if FRONTEND_DIST_DIR.exists():
        application.mount(
            FRONTEND_MOUNT_PATH,
            StaticFiles(directory=str(FRONTEND_DIST_DIR), html=True),
            name="frontend",
        )
        _logger.info(
            "Mounted built frontend from %s at %s",
            FRONTEND_DIST_DIR, FRONTEND_MOUNT_PATH,
        )
    else:
        _logger.info(
            "Frontend dist not found at %s; static mount skipped. "
            "Build the React app to enable the production UI.",
            FRONTEND_DIST_DIR,
        )

    _register_routes(application)
    return application


# ---------------------------------------------------------------------------
# Helpers shared by REST handlers
# ---------------------------------------------------------------------------

def _record_decision(
    agent_id: str,
    decision: ApprovalKind,
    reviewer_context: Optional[str],
) -> ApprovalQueueEntry:
    """Persist an approval entry to approval_queue.json and return it.
    Centralised so every endpoint records the timestamp the same way."""
    entry = ApprovalQueueEntry(
        agent_id=agent_id,
        decision=decision,
        reviewer_context=reviewer_context,
        decided_at=datetime.now(timezone.utc),
    )
    # append_approval_entry holds the OS-level lock for the read-
    # modify-write cycle, so concurrent POSTs cannot lose data.
    append_approval_entry(entry, APPROVAL_QUEUE_JSON)
    return entry


def _resolve_replay_file(agent_id: str, outputs_dir: Path) -> Optional[Path]:
    """Locate the most recent agent-replay-*.jsonl file for ``agent_id``.

    Two layouts are tolerated:
      1. <outputs_dir>/agent-<id>-replay-<n>.jsonl (flat per-agent files)
      2. <outputs_dir>/<id>/agent-replay-<n>.jsonl (per-agent subdirs)

    Returns the freshest match by mtime. None when no file matches yet.
    """
    if not outputs_dir.exists():
        return None
    candidates: list[Path] = []
    # Pattern 1: flat layout.
    for p in outputs_dir.glob(f"agent-{agent_id}-replay-*.jsonl"):
        candidates.append(p)
    # Pattern 2: per-agent dir.
    agent_dir = outputs_dir / agent_id
    if agent_dir.is_dir():
        for p in agent_dir.glob("agent-replay-*.jsonl"):
            candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _resolve_output_ref(agent_id: str) -> Optional[str]:
    """Look up output_ref for ``agent_id`` in agents.json. Returns None
    when the agent is unknown or the file is missing/invalid."""
    try:
        for agent in read_agents(AGENTS_JSON):
            if agent.agent_id == agent_id:
                return agent.output_ref
    except StateSchemaError as exc:
        _logger.warning("Could not resolve output_ref: %s", exc)
    return None


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

def _register_routes(app: FastAPI) -> None:
    """Attach every HTTP and WebSocket route to ``app``. Kept inside a
    function so create_app stays readable and tests can inspect the
    route table after construction."""

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        """Liveness probe. Returns 200 OK once the lifespan handler
        has finished bootstrapping. Suitable for readiness checks
        from a process supervisor."""
        return JSONResponse(
            {
                "status": "ok",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "websocket_port": WEBSOCKET_PORT,
                "rest_port": REST_PORT,
            }
        )

    @app.get("/agents", response_model=list[AgentState])
    async def list_agents() -> list[AgentState]:
        """Return the current contents of agents.json. The WebSocket
        is the primary delivery channel; this endpoint exists so
        non-realtime clients (curl, integration tests) can pull state."""
        try:
            return read_agents(AGENTS_JSON)
        except StateSchemaError as exc:
            # 500 because the server's own state file is malformed,
            # which is a server-side problem from the client's view.
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # -------------------------------------------------------------------
    # Canonical task runtime routes (Hybrid AgenticOS layer)
    # -------------------------------------------------------------------

    @app.get("/tasks")
    async def list_tasks() -> JSONResponse:
        """Return canonical task files from agentic-os/tasks."""
        try:
            tasks = read_tasks()
            return JSONResponse([task.model_dump(mode="json") for task in tasks])
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/tasks/snapshot")
    async def get_task_snapshot() -> JSONResponse:
        """Return the latest canonical task runtime snapshot."""
        try:
            snapshot = read_snapshot()
            return JSONResponse(snapshot.model_dump(mode="json"))
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/skill-actions")
    async def get_skill_actions(
        project_path: str | None = Query(default=None),
    ) -> JSONResponse:
        """Return command-panel skill actions for the selected project."""
        return JSONResponse(list_skill_actions(project_path))

    @app.post("/skill-actions/{slug}/run")
    async def run_skill_action(slug: str, body: dict) -> JSONResponse:
        """Create a watched AgenticOS task from a skill command button."""
        try:
            dispatch = dispatch_skill_action(
                slug,
                objective=body.get("objective"),
                project_path=body.get("project_path"),
                project_name=body.get("project_name"),
            )
            return JSONResponse(dispatch, status_code=201)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/tasks/{task_id}")
    async def get_task(task_id: str) -> JSONResponse:
        """Return one canonical task document."""
        try:
            task = read_task(task_id)
            return JSONResponse(task.model_dump(mode="json"))
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/tasks/{task_id}/claim")
    async def claim_task_endpoint(task_id: str, body: dict) -> JSONResponse:
        """Claim a pending task for a distributed worker."""
        agent_id = body.get("agent_id")
        if not agent_id:
            raise HTTPException(status_code=422, detail="agent_id is required")
        try:
            task = claim_task(task_id, str(agent_id))
            return JSONResponse(task.model_dump(mode="json"))
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TaskConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/tasks/{task_id}/checkpoint")
    async def checkpoint_task(task_id: str, body: dict) -> JSONResponse:
        """Append a progress checkpoint to the task's current owner."""
        checkpoint = body.get("checkpoint")
        if checkpoint is None:
            raise HTTPException(status_code=422, detail="checkpoint is required")
        try:
            task = update_task_checkpoint(task_id, checkpoint)
            return JSONResponse(task.model_dump(mode="json"))
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TaskConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/tasks/{task_id}/complete")
    async def complete_task_endpoint(task_id: str, body: dict) -> JSONResponse:
        """Mark a claimed task complete and release its lock."""
        try:
            task = complete_task(task_id, body.get("output"))
            return JSONResponse(task.model_dump(mode="json"))
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TaskConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/tasks/{task_id}/fail")
    async def fail_task_endpoint(task_id: str, body: dict) -> JSONResponse:
        """Mark a claimed task failed and release its lock."""
        if "error_context" not in body:
            raise HTTPException(status_code=422, detail="error_context is required")
        try:
            task = fail_task(task_id, body.get("error_context"))
            return JSONResponse(task.model_dump(mode="json"))
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TaskConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except TaskRuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # -------------------------------------------------------------------
    # Local terminal control routes (Universal Hub operator panel)
    # -------------------------------------------------------------------

    @app.get("/terminals")
    async def get_terminals(agent_only: bool = Query(False)) -> JSONResponse:
        """Return visible command prompt / PowerShell / Windows Terminal windows."""
        windows = list_terminal_windows(agent_only=agent_only)
        return JSONResponse([window.model_dump(mode="json") for window in windows])

    @app.post("/terminals/{hwnd}/focus")
    async def focus_terminal(hwnd: int) -> JSONResponse:
        """Restore and foreground a terminal window when Windows allows it."""
        result = focus_terminal_window(hwnd)
        return JSONResponse(result.model_dump(mode="json"))

    @app.post("/terminals/{hwnd}/close")
    async def close_terminal(hwnd: int) -> JSONResponse:
        """Request a graceful terminal window close through WM_CLOSE."""
        result = close_terminal_window(hwnd)
        return JSONResponse(result.model_dump(mode="json"))

    @app.post("/terminals/{pid}/terminate")
    async def terminate_terminal(pid: int, body: dict) -> JSONResponse:
        """Terminate a terminal process only after an explicit confirmation string."""
        if body.get("confirm") != TERMINAL_CONTROL_TERMINATE_CONFIRMATION:
            raise HTTPException(
                status_code=422,
                detail=(
                    "confirm must equal "
                    f"{TERMINAL_CONTROL_TERMINATE_CONFIRMATION!r}"
                ),
            )
        result = terminate_terminal_process(pid)
        return JSONResponse(result.model_dump(mode="json"))

    @app.post("/approve/{agent_id}")
    async def approve(agent_id: str, body: ApprovalDecision) -> JSONResponse:
        """Record a 'proceed' decision for ``agent_id``. Body decision
        is required by the schema but always coerced to PROCEED here
        so the endpoint cannot record the wrong kind."""
        # Force the kind regardless of body so the endpoint contract
        # cannot be subverted by a misconfigured client.
        entry = _record_decision(agent_id, ApprovalKind.PROCEED, None)
        return JSONResponse(
            {
                "agent_id": entry.agent_id,
                "decision": entry.decision.value,
                "decided_at": entry.decided_at.isoformat(),
            }
        )

    @app.post("/research/{agent_id}")
    async def research(agent_id: str, body: ApprovalDecision) -> JSONResponse:
        """Record a 'research more' decision for ``agent_id``."""
        entry = _record_decision(agent_id, ApprovalKind.RESEARCH, None)
        return JSONResponse(
            {
                "agent_id": entry.agent_id,
                "decision": entry.decision.value,
                "decided_at": entry.decided_at.isoformat(),
            }
        )

    @app.post("/review/{agent_id}")
    async def review(agent_id: str, body: ApprovalDecision) -> JSONResponse:
        """Record a 'review by agent' decision and spawn the reviewer.

        The reviewer subprocess runs on the default thread pool so the
        event loop is not blocked while Claude responds. The verdict
        is written to disk by the spawner; the watchdog notices the
        new file and broadcasts the updated state automatically."""
        # Resolve the context: explicit body wins, otherwise look up
        # the agent's output_ref in agents.json.
        reviewer_context = body.reviewer_context or _resolve_output_ref(agent_id)
        if reviewer_context is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"reviewer_context not provided in body and no output_ref "
                    f"found for {agent_id} in agents.json"
                ),
            )

        # Confirm the file exists before we record the decision; saves
        # a queue entry that no agent can ever satisfy.
        if not Path(reviewer_context).exists():
            raise HTTPException(
                status_code=404,
                detail=f"reviewer_context file not found: {reviewer_context}",
            )

        entry = _record_decision(
            agent_id, ApprovalKind.REVIEW, reviewer_context
        )

        try:
            verdict = await spawn_reviewer_async(
                agent_id=agent_id,
                reviewer_context=reviewer_context,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ReviewerSpawnError as exc:
            # 502 because the upstream service (Claude CLI) failed.
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return JSONResponse(
            {
                "agent_id": entry.agent_id,
                "decision": entry.decision.value,
                "decided_at": entry.decided_at.isoformat(),
                "reviewer_context": reviewer_context,
                "verdict_outcome": verdict.outcome.value,
                "verdict_path": verdict.verdict_path,
            }
        )

    @app.get("/progress")
    async def get_progress(
        since: int = Query(default=0, ge=0, description="Return events with seq >= since"),
    ) -> JSONResponse:
        """Return progress-log events whose seq is >= ``since``.
        Supports recovery after a WebSocket reconnect: a client that
        knows the last seq it processed can replay everything missed
        without dropping events. Reads through the global progress_log
        singleton; tests that need an isolated log instantiate
        ProgressLog directly."""
        try:
            events = progress_log.read_since(since)
        except Exception as exc:
            _logger.exception("Could not read progress log: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return JSONResponse({"since": since, "count": len(events), "events": events})

    @app.get("/agents/{agent_id}/stream")
    async def stream_agent(agent_id: str):
        """Server-Sent Events stream that tails the most recent
        agent-replay-*.jsonl file for ``agent_id`` inside OUTPUTS_DIR.

        Each new line in the file is delivered as one SSE event. The
        stream ends when the client disconnects; until then the
        endpoint sleeps briefly between EOF checks rather than holding
        a hot loop. We do not use watchdog here because the file may
        not exist when the stream opens (a brand-new agent has not
        produced output yet) and watchdog requires an existing target."""
        # Locate the latest replay file for this agent. The convention
        # used by Cowork-style sub-agents is agent-replay-<n>.jsonl in
        # OUTPUTS_DIR. We accept either flat or per-agent layouts.
        from AgenticOS.config import OUTPUTS_DIR

        async def _event_source():
            # Sleep increment when the file does not yet exist or has
            # no new bytes. Kept small so the UI feels live, large
            # enough that an idle stream costs near-zero CPU.
            poll_interval_s = 0.5

            # Resolve the file once at start; if it does not exist,
            # we still emit a heartbeat so the client knows we are
            # connected and waiting.
            target = _resolve_replay_file(agent_id, OUTPUTS_DIR)

            # Send a connect comment so EventSource onopen fires immediately.
            yield ": connected\n\n"

            offset = 0
            while True:
                try:
                    if target is None or not target.exists():
                        # Re-resolve in case the file was just created.
                        target = _resolve_replay_file(agent_id, OUTPUTS_DIR)
                        await asyncio.sleep(poll_interval_s)
                        continue

                    with open(target, "rb") as handle:
                        handle.seek(offset)
                        chunk = handle.read()
                        offset = handle.tell()

                    if chunk:
                        for line in chunk.splitlines():
                            try:
                                payload = line.decode("utf-8", errors="replace")
                            except Exception:
                                continue
                            # SSE format: data: <line>\n\n
                            yield f"data: {payload}\n\n"
                    else:
                        await asyncio.sleep(poll_interval_s)
                except asyncio.CancelledError:
                    # Client disconnected; clean exit.
                    break
                except Exception as exc:
                    _logger.warning(
                        "Stream error for %s: %s", agent_id, exc
                    )
                    yield f"event: error\ndata: {exc!r}\n\n"
                    break

        return StreamingResponse(
            _event_source(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # -------------------------------------------------------------------
    # Project registry routes (Phase 1 -- Universal Hub)
    # -------------------------------------------------------------------

    @app.post("/projects/register")
    async def register_project(body: dict) -> JSONResponse:
        """Register or refresh a project. Body: {path, name?, tech_stack?, skills?}"""
        import hashlib as _hashlib
        path = body.get("path", "")
        if not path:
            raise HTTPException(status_code=422, detail="path is required")
        from AgenticOS.project_registry import extract_project_metadata
        from pathlib import Path as _Path
        claude_md = _Path(path) / "CLAUDE.md"
        meta = extract_project_metadata(claude_md) if claude_md.exists() else {
            "name": body.get("name", _Path(path).name),
            "tech_stack": body.get("tech_stack", []),
            "skills": body.get("skills", []),
        }
        project_id = _hashlib.sha256(str(_Path(path).resolve()).encode()).hexdigest()[:16]
        record = await project_registry.upsert(
            project_id=project_id,
            path=path,
            name=meta["name"],
            tech_stack=meta["tech_stack"],
            skills=meta["skills"],
        )
        return JSONResponse(record.to_dict(), status_code=201)

    @app.get("/projects")
    async def list_projects() -> JSONResponse:
        """Return all registered projects."""
        projects = await project_registry.list_all()
        return JSONResponse([p.to_dict() for p in projects])

    @app.get("/projects/active")
    async def list_active_projects() -> JSONResponse:
        """Return only projects seen recently."""
        projects = await project_registry.list_active()
        return JSONResponse([p.to_dict() for p in projects])

    @app.get("/projects/{project_id}")
    async def get_project(project_id: str) -> JSONResponse:
        """Return a single project by ID."""
        record = await project_registry.get(project_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return JSONResponse(record.to_dict())

    @app.get("/projects/{project_id}/phase")
    async def get_project_phase(project_id: str) -> JSONResponse:
        """Return what Marcus needs to do RIGHT NOW for this project."""
        record = await project_registry.get(project_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        # Count active agents for this project (matched by path prefix).
        try:
            all_agents = read_agents(AGENTS_JSON)
            project_agents = [
                a for a in all_agents
                if record.path and (
                    (a.output_ref or "").startswith(record.path)
                    or record.name.lower() in (a.task or "").lower()
                )
            ]
        except StateSchemaError:
            project_agents = []

        waiting = [a for a in project_agents if "waiting" in str(a.status)]
        phase_hint = record.phase_hint
        if waiting:
            phase_hint = (
                f"APPROVE or REVIEW: {waiting[0].agent_id} is waiting — "
                f"{waiting[0].task[:80]}"
            )
        elif not phase_hint:
            phase_hint = (
                "No specific task recorded. Check recent agent output or "
                "add a phase_hint via POST /projects/{id}/phase."
            )
        return JSONResponse({
            "id": record.id,
            "name": record.name,
            "path": record.path,
            "phase_hint": phase_hint,
            "agent_count": len(project_agents),
            "waiting_count": len(waiting),
            "skills": record.skills,
            "last_seen": record.last_seen,
        })

    @app.post("/projects/{project_id}/phase")
    async def update_project_phase(project_id: str, body: dict) -> JSONResponse:
        """Set the phase_hint (what Marcus should do now) for a project."""
        hint = body.get("hint", "")
        if not hint:
            raise HTTPException(status_code=422, detail="hint is required")
        record = await project_registry.get(project_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        await project_registry.update_phase_hint(project_id, hint)
        return JSONResponse({"id": project_id, "phase_hint": hint})

    # -------------------------------------------------------------------
    # Handoff manifest routes (Ollama continuous-work feature)
    # -------------------------------------------------------------------

    @app.get("/handoff")
    async def get_handoff_status() -> JSONResponse:
        """Return the current handoff manifest status."""
        return JSONResponse(handoff_status_payload())

    @app.post("/handoff/snapshot")
    async def create_handoff_snapshot(body: dict) -> JSONResponse:
        """Write a handoff manifest from the current session state.
        Body keys match HandoffManifest fields: project_name, project_path,
        plan_summary, completed_tasks, pending_tasks, current_task,
        context_notes, files_modified, next_action."""
        from AgenticOS.handoff_writer import snapshot_current_work
        try:
            manifest = snapshot_current_work(
                project_name=body.get("project_name", "Unknown"),
                project_path=body.get("project_path", ""),
                plan_summary=body.get("plan_summary", ""),
                completed_tasks=body.get("completed_tasks", []),
                pending_tasks=body.get("pending_tasks", []),
                current_task=body.get("current_task"),
                context_notes=body.get("context_notes", ""),
                files_modified=body.get("files_modified", []),
                next_action=body.get("next_action", ""),
            )
            return JSONResponse({"status": "written", "manifest": manifest.to_dict()})
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # -------------------------------------------------------------------
    # Workflow events — one-way push from autonomous-workflow skill
    # -------------------------------------------------------------------

    @app.post("/events")
    async def receive_workflow_event(body: WorkflowEvent) -> JSONResponse:
        """Accept a workflow lifecycle event from the autonomous-workflow skill.
        Appends to workflow_events.json; fire-and-forget from skill side."""
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

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """Primary realtime channel. Clients connect, immediately
        receive a snapshot of the current state, and then receive
        diff frames whenever agents.json changes."""
        broadcaster = get_broadcaster()
        await broadcaster.connect(websocket)
        try:
            while True:
                # We do not currently act on inbound messages but we
                # must consume them to keep the connection alive.
                # receive_text returns when the peer sends a frame
                # OR when the socket closes.
                await websocket.receive_text()
        except WebSocketDisconnect:
            await broadcaster.disconnect(websocket)
        except Exception as exc:
            # Unexpected error: log, drop the client, do not re-raise
            # so the server keeps serving other clients.
            _logger.warning("WebSocket error for client; dropping: %s", exc)
            await broadcaster.disconnect(websocket)


# ---------------------------------------------------------------------------
# Module-level app instance
#
# Defined at import time so `uvicorn AgenticOS.agentic_server:app` works.
# create_app handles all configuration; this is just a thin shim.
# ---------------------------------------------------------------------------

app = create_app()


# ---------------------------------------------------------------------------
# Direct-execution entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Convenience entry point: ``python -m AgenticOS.agentic_server``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    # Both ports are equal in the default config but kept distinct here
    # so a future split (REST behind a proxy) does not require code changes.
    if WEBSOCKET_PORT != REST_PORT:
        _logger.warning(
            "WEBSOCKET_PORT (%d) and REST_PORT (%d) differ; uvicorn binds "
            "to REST_PORT only. Run a second server or proxy for split deployment.",
            WEBSOCKET_PORT, REST_PORT,
        )
    uvicorn.run(
        "AgenticOS.agentic_server:app",
        host=SERVER_HOST,
        port=REST_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
