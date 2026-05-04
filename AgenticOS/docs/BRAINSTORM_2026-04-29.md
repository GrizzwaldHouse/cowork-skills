# AGENTIC OS COMMAND CENTER — EXPANSION BRAINSTORM

Captured: 2026-04-29

The state bus, PyQt6 launcher, WPF dashboard alt, React + Spline frontend, AgentCard grid, and reviewer subprocess all exist. This artifact locks the next expansion: terminal discovery, neural-brain global view, stuck/loop detection, full visibility logging. The rule for tonight is expand without erasing.

---

## SECTION 1 — WHAT THE COMMAND CENTER MUST DO

### Q1.1 What is the user's ground-truth ask?
- [x] Auto-detect every running Claude Code terminal/session, no manual config: Marcus runs many CLI agents in parallel and switching between cmd.exe windows is the friction point.
- [x] One screen with one panel per session, all live, all controllable: replaces tab-flipping.
- [x] Spline 3D neural-brain global view as the primary visual: each agent is a brain node, edges show task lineage, stuck nodes pulse red.
- [x] Full visibility on stuck/looping/silent failures: idle threshold, loop pattern detection, every state transition logged.
- [ ] Cross-machine session aggregation: out of scope — local only tonight.

### Q1.2 What is the integration point with Claude Code?
- [x] `%APPDATA%\Claude\local-agent-mode-sessions\<plugin-id>\<session-id>\` — every Cowork session writes `mission-state.json`, `subagent-tracking.json`, agent replays, and outputs here. The state bus already exists in the filesystem; we just have to read it.
- [ ] Process injection / stdin capture: too brittle on Windows; unreliable.
- [ ] CLI subprocess wrapper: works for new sessions but misses ones started outside the wrapper.

The session directory approach reads what Claude Code already writes, so it works for every session whether started by us or not.

### Q1.3 What is the source of "active" for a session?
- [x] `mission-state.json` mtime within last N seconds (configurable, default 60): a session is active when it's writing to disk.
- [x] Process scan via `psutil` for any `claude.exe` / `claude` process: confirms the CLI is actually running, not just leftover state.
- [x] Both: belt and suspenders.

---

## SECTION 2 — MODULES TO ADD (NEW FILES, NO EDITS TO EXISTING)

### Q2.1 Session discovery module
- [x] `AgenticOS/session_discovery.py`: stdlib + psutil. Scans the Cowork sessions root, parses each `mission-state.json`, returns a list of `DiscoveredSession` Pydantic models. Reads only — never writes inside session dirs.
- [x] Constants in `config.py`: `COWORK_SESSIONS_ROOT`, `SESSION_ACTIVE_THRESHOLD_S`, `SESSION_SCAN_INTERVAL_S`. No hardcoded paths in the discovery module itself.

### Q2.2 Session-to-agent bridge
- [x] `AgenticOS/session_bridge.py`: subscribes to discovery results, translates each `DiscoveredSession` into an `AgentState`, writes the merged list to `agents.json` via the existing `state_store`. Existing manually-registered agents are preserved.
- [x] Bridge runs as an asyncio task started by `agentic_server.py` lifespan: same pattern as the watchdog observer.
- [ ] Bridge-as-separate-process: introduces IPC complexity tonight without payoff.

### Q2.3 Stuck and loop detection
- [x] `AgenticOS/stuck_detector.py`: pure functions. Inputs: agent state history (last N transitions). Outputs: stuck flag (idle > threshold), loop flag (last K transitions all identical action). No timers — invoked on every state change.
- [x] Surface as new fields on `AgentState`: `is_stuck`, `is_looping`, `last_progress_at`. Existing consumers ignore unknown fields (Pydantic v2 default).
- [ ] Auto-kill stuck agents: not tonight — surface only, Marcus decides.

### Q2.4 Progress event log
- [x] `AgenticOS/progress_log.py`: append-only NDJSON at `state/progress.log`. Every state transition (added / updated / removed / stuck-flagged / loop-flagged) writes a line. Existing WebSocket diff broadcaster is the read side, this is the audit trail.
- [x] New REST endpoint `GET /progress?since=<seq>` for retrospective queries (replay after reconnect, no events dropped).

### Q2.5 Frontend — neural-brain view
- [x] `frontend/src/components/NeuralBrainView/`: new component, Spline scene + agent nodes. Nodes positioned via force-directed layout (d3-force) using parent/child task lineage from `mission-state.json` timeline.
- [x] `frontend/src/components/ViewModeToggle/`: top-right toggle, persists to `localStorage`. Modes: `grid` (existing AgentCard grid) and `brain` (new Spline view).
- [x] No deletion of existing `AgentCard` grid: brain view is additive.
- [ ] Replace AgentCard grid with brain-only: rejected — grid is faster for triage.

### Q2.6 Frontend — terminal stream panel
- [x] `frontend/src/components/TerminalStreamPanel/`: opens when an agent card is clicked. Tails the session's most recent output file via SSE from a new `GET /agents/:id/stream` endpoint.
- [x] Backend endpoint reads the latest `agent-replay-*.jsonl` file and streams new lines as Server-Sent Events.

---

## SECTION 3 — STUCK / LOOP / SILENT FAILURE RULES

### Q3.1 Idle threshold
- [x] Default 90 seconds with no `mission-state.json` mtime change AND no new lines in the active replay file: the agent is idle.
- [x] Configurable in `config.py` as `STUCK_IDLE_THRESHOLD_S`.

### Q3.2 Loop detection
- [x] Last 5 timeline entries have identical `kind` and `agent` fields: flag as loop.
- [x] Configurable as `LOOP_WINDOW_SIZE` and `LOOP_IDENTICAL_THRESHOLD`.

### Q3.3 Silent failure
- [x] Process exited (psutil shows session ID's child processes gone) but `mission-state.json` status is still "in_progress": flag as silent failure.
- [x] Surface on the agent card with red border and an explanatory tooltip.

### Q3.4 What to NOT auto-do
- [x] Never auto-kill a session: Marcus pushes the kill button manually.
- [x] Never edit files inside a session directory: read-only on every Cowork session path.

---

## SECTION 4 — VISIBILITY GUARANTEES

### Q4.1 What must always be visible to Marcus
- [x] Every active session as a card and a brain node.
- [x] Every state transition timestamp and reason in the progress log.
- [x] Every stuck/loop flag with the threshold that was crossed.
- [x] WebSocket connection status + last sequence number (already implemented).
- [x] Sub-agent spawn count per session (read from `subagent-tracking.json`).

### Q4.2 What the agent doing the implementation must report back
- [x] Progress milestone after each module file is written (file path + line count).
- [x] Each test command's pass/fail with output tail.
- [x] Final summary: files created, lines added, tests run, what's verified, what's deferred.
- [x] Stop-and-ask if any work creates ambiguity: don't silently make a call.

---

## SECTION 5 — CONSTRAINTS (HARD LOCKS)

### Q5.1 Code preservation
- [x] No deletion of existing files. No refactoring of existing files unless strictly necessary for the new modules to integrate (and only the minimum surgical change).
- [x] All new code goes in new files. Edits to existing files are append-only or single-import additions.

### Q5.2 Modularity
- [x] New modules follow the existing pattern: typed, single-purpose, file header comment, named export, optional `--test` block where it makes sense for Python (pytest tests in `AgenticOS/tests/` for everything substantive).
- [x] React components follow the existing component-folder pattern (`ComponentName/ComponentName.tsx + ComponentName.css + index.ts + tests`).
- [x] Config in `config.py` only.

### Q5.3 Bloating
- [x] No new top-level dependency unless functionally required: `psutil` is the only new Python dep tonight; `d3-force` is the only new npm dep.
- [x] No mockup HTML, no demo pages, no scaffolding that won't be wired in this session.

### Q5.4 Visibility
- [x] Every state transition emits an event to the new `progress_log` AND broadcasts via the existing WebSocket diff system.
- [x] No silent failures: every exception caught is logged with category and re-raised or surfaced to the user.

---

## SECTION 6 — RISK REGISTER

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Cowork session schema differs across plugin IDs | Medium | Discovery module wraps each `mission-state.json` parse in try/except; bad sessions are skipped with a logged warning, not a crash |
| psutil process scan is slow on Windows | Low | Cache results for SESSION_SCAN_INTERVAL_S (default 5s); never block the FastAPI request loop |
| Spline scene file missing or corrupt | Medium | NeuralBrainView falls back to a 2D SVG node graph if Spline fails to load; logged as a warning |
| Tailing a JSONL file across rotations | Medium | TerminalStreamPanel reopens the file on EOF and detects rotation by inode change |
| Existing tests break from new fields on AgentState | Low | Pydantic v2 ignores unknown fields by default; new fields are Optional with defaults |
| WebSocket overload from many active agents | Low | Discovery cap: `MAX_DISCOVERED_SESSIONS` (default 32) |

---

## EXECUTION ORDER (LOCKED)

1. `pip install psutil` (only new Python dep tonight).
2. `config.py` additions: `COWORK_SESSIONS_ROOT`, `SESSION_ACTIVE_THRESHOLD_S`, `SESSION_SCAN_INTERVAL_S`, `STUCK_IDLE_THRESHOLD_S`, `LOOP_WINDOW_SIZE`, `LOOP_IDENTICAL_THRESHOLD`, `MAX_DISCOVERED_SESSIONS`.
3. `models.py` additions: `DiscoveredSession`, optional fields on `AgentState` (`is_stuck`, `is_looping`, `last_progress_at`, `sub_agent_count`).
4. `session_discovery.py` — scan + parse + return list.
5. `stuck_detector.py` — pure functions on transition history.
6. `progress_log.py` — append-only NDJSON writer + REST endpoint.
7. `session_bridge.py` — async task that ties discovery to state_store.
8. `agentic_server.py` — single edit: register the bridge in lifespan startup. Plus the `/progress` and `/agents/:id/stream` endpoints.
9. Frontend: `cd frontend && npm install d3-force`.
10. Frontend new components: `NeuralBrainView/`, `ViewModeToggle/`, `TerminalStreamPanel/`.
11. `App.tsx` — single addition: render the toggle and switch between grid and brain.
12. Run pytest, run vite build, run launcher.

---

## DEFERRED FOR MARCUS

- Cross-machine session aggregation (multi-host).
- Auto-kill stuck agents after threshold.
- Persistent SQLite event store for >24h history.
- Authentication on the FastAPI port (currently loopback-only).
- Spline scene customization (which neural-brain scene asset to load).
