# AgenticOS State Bus

Plan 1 of the AgenticOS Command Center: the FastAPI process that owns
the WebSocket and REST endpoints powering the supervisor UI.

This package is private work product. See `LICENSE`, `COPYRIGHT.md`,
`PRIVACY.md`, and `NOTICE` at the repository root for the full terms.

## What lives here

- `config.py`: every port, path, timeout, and template constant. No
  other module is allowed to hardcode a value that could change.
- `models.py`: Pydantic v2 models for every cross-process state shape
  (`AgentState`, `ApprovalDecision`, `ApprovalQueueEntry`,
  `ReviewerVerdict`) plus the supporting enums.
- `state_store.py`: thread-safe atomic JSON readers and writers for
  `agents.json` and `approval_queue.json`. Uses temp-then-rename and
  advisory file locks (msvcrt on Windows, fcntl elsewhere).
- `file_watcher.py`: watchdog observer that fires an asyncio-scheduled
  broadcast whenever `agents.json` changes. No polling.
- `websocket_broadcaster.py`: connection manager that diffs current vs
  previous state and broadcasts only the delta to every connected
  client. Snapshots are sent on connect.
- `reviewer_spawner.py`: spawns Claude Haiku 4.5 via the `claude` CLI,
  writes the verdict to `state/outputs/agent-{id}-review.md`, and
  exposes both sync and async entry points.
- `agentic_server.py`: the FastAPI app that ties everything together.
  Provides the WebSocket endpoint at `/ws` and REST endpoints at
  `/healthz`, `/agents`, `/approve/{agent_id}`, `/research/{agent_id}`,
  `/review/{agent_id}`.
- `state/`: runtime data directory (created on first boot).
- `tests/`: pytest suite covering state I/O, broadcaster, and server
  endpoints.

## Prerequisites

Python 3.10 or later (the project standard is 3.13). Install
dependencies from this folder:

```bash
pip install -r requirements.txt
```

The reviewer subprocess depends on the Claude Code CLI being available
on `PATH`. If you only intend to run the server and the UI without
exercising the reviewer flow, the CLI is optional.

## Running the server

From the `C:\ClaudeSkills` repository root so the absolute imports
resolve:

```bash
python -m AgenticOS.agentic_server
```

You can also point uvicorn at the app directly:

```bash
uvicorn AgenticOS.agentic_server:app --host 127.0.0.1 --port 7842
```

The host and port are read from `AgenticOS/config.py`. Both default to
`127.0.0.1:7842`. Edit the constants in that file rather than passing
flags so every consumer sees the same values.

On startup the server will:

1. Create `AgenticOS/state/` and `AgenticOS/state/outputs/` if missing.
2. Seed `agents.json` and `approval_queue.json` with `[]` if missing.
3. Start the watchdog observer on `agents.json`.
4. Mount the built React frontend from `AgenticOS/frontend/dist/` at
   `http://127.0.0.1:7842/app` if a build is present.

`Ctrl+C` performs a clean shutdown: the observer is stopped and joined,
and every WebSocket is closed.

## Connecting a client to the WebSocket

Open `ws://127.0.0.1:7842/ws`. On connect the server immediately sends
a snapshot frame:

```json
{
  "type": "snapshot",
  "agents": [...],
  "added": [],
  "updated": [],
  "removed": [],
  "sent_at": "2026-04-29T14:32:00.123456+00:00"
}
```

Subsequent frames are diffs:

```json
{
  "type": "diff",
  "agents": [],
  "added":   [{"agent_id": "AGENT-02", "...": "..."}],
  "updated": [{"agent_id": "AGENT-01", "...": "..."}],
  "removed": ["AGENT-03"],
  "sent_at": "2026-04-29T14:32:01.456789+00:00"
}
```

Inbound text frames are accepted but currently ignored; the server is
broadcast-only.

A quick sanity check from a Python REPL:

```python
import asyncio, websockets
async def main():
    async with websockets.connect("ws://127.0.0.1:7842/ws") as ws:
        print(await ws.recv())  # snapshot
asyncio.run(main())
```

## Invoking the REST endpoints

The endpoints live alongside the WebSocket on the same port.

```bash
# Liveness check
curl http://127.0.0.1:7842/healthz

# List current agents (validated through Pydantic)
curl http://127.0.0.1:7842/agents

# Record a "proceed" decision for AGENT-01
curl -X POST http://127.0.0.1:7842/approve/AGENT-01 \
     -H "Content-Type: application/json" \
     -d '{"decision":"proceed"}'

# Record a "research more" decision for AGENT-01
curl -X POST http://127.0.0.1:7842/research/AGENT-01 \
     -H "Content-Type: application/json" \
     -d '{"decision":"research"}'

# Spawn a reviewer for AGENT-01 against an explicit context file
curl -X POST http://127.0.0.1:7842/review/AGENT-01 \
     -H "Content-Type: application/json" \
     -d '{"decision":"review","reviewer_context":"AgenticOS/state/outputs/agent-01-stage-2.md"}'
```

If `reviewer_context` is omitted from a `/review/{agent_id}` body the
server falls back to the agent's `output_ref` field in `agents.json`.

All endpoints return JSON. Validation failures (missing field, value
outside an enum) return `422` with details from Pydantic. A missing
context file returns `404`. A reviewer subprocess failure (CLI not on
`PATH`, non-zero exit, timeout) returns `502`.

## Running the tests

From the `AgenticOS/` folder so pytest discovers `tests/conftest.py`
and the relative imports resolve:

```bash
cd C:/ClaudeSkills/AgenticOS
pytest -v
```

The suite runs in-process: no real Claude CLI is invoked, no real
WebSocket clients are required. State files are written to pytest's
`tmp_path` so concurrent runs do not interfere with each other.

## What this does not do (yet)

Plan 1 stops at the state bus. The WPF system tray launcher
(`agentic_dashboard.py`), the React + Spline frontend, and the
`skills/agentic-parallel/` protocol are tracked in subsequent plans
under `docs/superpowers/plans/`.
