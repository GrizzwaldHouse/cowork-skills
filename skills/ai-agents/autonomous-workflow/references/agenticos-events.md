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
{ "event": "workflow.started",        "workflow_id": "uuid4", "task": "string",         "timestamp": "ISO8601" }
{ "event": "workflow.phase_started",  "workflow_id": "uuid4", "phase": "brainstorm|planning|execution|verification", "timestamp": "ISO8601" }
{ "event": "workflow.phase_complete", "workflow_id": "uuid4", "phase": "string",         "timestamp": "ISO8601" }
{ "event": "workflow.vote_cast",      "workflow_id": "uuid4", "decision": "string",      "result": "PASS|FAIL|BLOCKED", "voters": ["Engineer","Architect","PM","Security"], "timestamp": "ISO8601" }
{ "event": "workflow.complete",       "workflow_id": "uuid4", "phases_run": 4,           "timestamp": "ISO8601" }
{ "event": "workflow.failed",         "workflow_id": "uuid4", "phase": "string",         "reason": "string", "timestamp": "ISO8601" }
```

## AgenticOS Side
Events are appended to `outputs/workflow_events.json` on the AgenticOS server.
The React HUD can poll `GET /progress?since=<seq>` or subscribe via WebSocket (`/ws`) to display workflow progress.
