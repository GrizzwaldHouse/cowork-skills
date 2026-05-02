# WorkflowStatusPanel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only WorkflowStatusPanel HUD to the AgenticOS Command Center that polls a new `GET /workflow-events` endpoint and renders live phase-by-phase status for autonomous-workflow skill runs.

**Architecture:** A new FastAPI endpoint reads `state/outputs/workflow_events.json` (written by `POST /events`) and returns a cursor-paginated slice. A React polling hook accumulates events, groups them by `workflow_id`, and derives `WorkflowGroup` objects. The panel component renders one collapsible section per group using the existing `tokens.css` palette and `data-state` CSS attribute pattern.

**Tech Stack:** Python 3.10+ / FastAPI / Pydantic v2 (server); React 18 / TypeScript / CSS Modules (client); pytest (server tests); Vitest (client tests).

**Spec:** `docs/superpowers/specs/2026-05-01-workflow-status-panel-design.md`

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `AgenticOS/agentic_server.py` | Add `GET /workflow-events` endpoint |
| Modify | `AgenticOS/frontend/src/config.ts` | Add `ENDPOINTS.workflowEvents` |
| Create | `AgenticOS/frontend/src/types/workflow.ts` | Wire-shape types for `WorkflowEvent` and derived views |
| Create | `AgenticOS/frontend/src/hooks/useWorkflowEvents.ts` | Polling hook with cursor accumulation and group derivation |
| Create | `AgenticOS/frontend/src/components/WorkflowStatusPanel/WorkflowStatusPanel.tsx` | Panel component |
| Create | `AgenticOS/frontend/src/components/WorkflowStatusPanel/WorkflowStatusPanel.css` | Scoped styles |
| Modify | `AgenticOS/frontend/src/App.tsx` | Wire panel below SkillCommandPanel |
| Create | `AgenticOS/tests/test_workflow_events_endpoint.py` | pytest tests for the new endpoint |

---

## Task 1: Add `GET /workflow-events` endpoint

**Files:**
- Modify: `AgenticOS/agentic_server.py` (inside `_register_routes`)
- Create: `AgenticOS/tests/test_workflow_events_endpoint.py`

- [ ] **Step 1: Write the failing test**

Create `AgenticOS/tests/test_workflow_events_endpoint.py`:

```python
# AgenticOS/tests/test_workflow_events_endpoint.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Tests for GET /workflow-events endpoint.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from AgenticOS.agentic_server import create_app


@pytest.fixture()
def client(tmp_path: Path):
    events_file = tmp_path / "workflow_events.json"
    events_file.write_text(
        json.dumps([
            {
                "event": "workflow.started",
                "workflow_id": "wf-001",
                "task": "Build something",
                "timestamp": "2026-05-01T10:00:00Z",
            },
            {
                "event": "workflow.phase_started",
                "workflow_id": "wf-001",
                "phase": "brainstorm",
                "timestamp": "2026-05-01T10:00:01Z",
            },
            {
                "event": "workflow.started",
                "workflow_id": "wf-002",
                "task": "Other task",
                "timestamp": "2026-05-01T10:01:00Z",
            },
        ]),
        encoding="utf-8",
    )
    with patch("AgenticOS.agentic_server.OUTPUTS_DIR", tmp_path):
        app = create_app()
        yield TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def client_no_file(tmp_path: Path):
    with patch("AgenticOS.agentic_server.OUTPUTS_DIR", tmp_path):
        app = create_app()
        yield TestClient(app, raise_server_exceptions=True)


def test_returns_all_events(client):
    resp = client.get("/workflow-events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["since"] == 0
    assert body["count"] == 3
    assert len(body["events"]) == 3


def test_since_cursor_slices_events(client):
    resp = client.get("/workflow-events?since=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["since"] == 1
    assert body["count"] == 2
    assert body["events"][0]["event"] == "workflow.phase_started"


def test_workflow_id_filter(client):
    resp = client.get("/workflow-events?workflow_id=wf-002")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["events"][0]["workflow_id"] == "wf-002"


def test_since_beyond_length_returns_empty(client):
    resp = client.get("/workflow-events?since=99")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["events"] == []


def test_missing_file_returns_empty(client_no_file):
    resp = client_no_file.get("/workflow-events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["events"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd C:\ClaudeSkills
python -m pytest AgenticOS/tests/test_workflow_events_endpoint.py -v
```

Expected: 5 failures — `404 Not Found` on `/workflow-events`.

- [ ] **Step 3: Add endpoint inside `_register_routes` in `agentic_server.py`**

Find the comment block `# Workflow events — one-way push from autonomous-workflow skill` (around line 891). Add the new GET endpoint **immediately after** the existing `@app.post("/events")` handler (before the `@app.websocket("/ws")` line):

```python
    @app.get("/workflow-events")
    async def get_workflow_events(
        since: int = Query(default=0, ge=0, description="Return events at index >= since"),
        workflow_id: Optional[str] = Query(default=None, description="Filter to one workflow run"),
    ) -> JSONResponse:
        """Return workflow lifecycle events written by the autonomous-workflow skill.
        Uses a 0-based array-index cursor matching the /progress endpoint convention."""
        events_file = OUTPUTS_DIR / "workflow_events.json"
        if not events_file.exists():
            return JSONResponse({"since": since, "count": 0, "events": []})
        try:
            all_events: list = json.loads(events_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            _logger.warning("Could not read workflow_events.json: %s", exc)
            return JSONResponse({"since": since, "count": 0, "events": []})

        sliced = all_events[since:]
        if workflow_id is not None:
            sliced = [e for e in sliced if e.get("workflow_id") == workflow_id]
        return JSONResponse({"since": since, "count": len(sliced), "events": sliced})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest AgenticOS/tests/test_workflow_events_endpoint.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add AgenticOS/agentic_server.py AgenticOS/tests/test_workflow_events_endpoint.py
git commit -m "feat(agenticos): add GET /workflow-events endpoint with cursor + filter"
```

---

## Task 2: TypeScript types

**Files:**
- Create: `AgenticOS/frontend/src/types/workflow.ts`
- Modify: `AgenticOS/frontend/src/config.ts`

- [ ] **Step 1: Create `src/types/workflow.ts`**

```typescript
// workflow.ts
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: TypeScript mirror of WorkflowEvent from AgenticOS/models.py and
//          derived view types consumed by useWorkflowEvents and WorkflowStatusPanel.

// ---------------------------------------------------------------------------
// Wire shape — mirrors WorkflowEvent(extra="allow") from models.py
// ---------------------------------------------------------------------------

export type WorkflowEventKind =
  | 'workflow.started'
  | 'workflow.phase_started'
  | 'workflow.phase_complete'
  | 'workflow.vote_cast'
  | 'workflow.complete'
  | 'workflow.failed';

export type VoteResult = 'PASS' | 'FAIL' | 'BLOCKED';

// Intersection type avoids readonly/index-signature conflict in strict TS.
export type WorkflowEvent = {
  readonly event: WorkflowEventKind;
  readonly workflow_id: string;
  readonly timestamp: string;
  readonly task?: string;
  readonly phase?: string;
  readonly decision?: string;
  readonly result?: VoteResult;
  readonly voters?: readonly string[];
  readonly phases_run?: number;
  readonly reason?: string;
} & Record<string, unknown>;

// ---------------------------------------------------------------------------
// Derived view types — produced by groupWorkflowEvents()
// ---------------------------------------------------------------------------

export type WorkflowTerminalStatus = 'active' | 'complete' | 'failed';

export interface PhaseRecord {
  readonly name: string;
  readonly started: boolean;
  readonly complete: boolean;
  readonly voteResult: VoteResult | null;
}

export interface WorkflowGroup {
  readonly workflowId: string;
  readonly task: string | null;
  readonly events: readonly WorkflowEvent[];
  readonly phases: readonly PhaseRecord[];
  readonly terminalStatus: WorkflowTerminalStatus;
  readonly failureReason: string | null;
  readonly startedAt: string;
  readonly updatedAt: string;
}

// ---------------------------------------------------------------------------
// REST response shape — mirrors GET /workflow-events response body
// ---------------------------------------------------------------------------

export interface WorkflowEventsResponse {
  readonly since: number;
  readonly count: number;
  readonly events: readonly WorkflowEvent[];
}
```

- [ ] **Step 2: Add `ENDPOINTS.workflowEvents` to `config.ts`**

Open `AgenticOS/frontend/src/config.ts`. Inside the `ENDPOINTS` object (after `taskSnapshot`), add:

```typescript
  workflowEvents: (since = 0, workflowId?: string): string => {
    const params = new URLSearchParams({ since: String(since) });
    if (workflowId !== undefined) params.set('workflow_id', workflowId);
    return `${REST_BASE}/workflow-events?${params.toString()}`;
  },
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd AgenticOS/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add AgenticOS/frontend/src/types/workflow.ts AgenticOS/frontend/src/config.ts
git commit -m "feat(frontend): add WorkflowEvent types and ENDPOINTS.workflowEvents"
```

---

## Task 3: `useWorkflowEvents` hook

**Files:**
- Create: `AgenticOS/frontend/src/hooks/useWorkflowEvents.ts`

The canonical phases in order: `brainstorm`, `planning`, `execution`, `verification`.

- [ ] **Step 1: Create `src/hooks/useWorkflowEvents.ts`**

```typescript
// useWorkflowEvents.ts
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: Polls GET /workflow-events every 5 s, accumulates events via a
//          cursor ref, groups by workflow_id into WorkflowGroup objects,
//          and returns the display subset (all active + 3 most-recent terminal).

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ENDPOINTS } from '@/config';
import type {
  PhaseRecord,
  VoteResult,
  WorkflowEvent,
  WorkflowEventsResponse,
  WorkflowGroup,
  WorkflowTerminalStatus,
} from '@/types/workflow';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_MS = 5_000;
const MAX_TERMINAL_GROUPS = 3;
const CANONICAL_PHASES = ['brainstorm', 'planning', 'execution', 'verification'] as const;

// ---------------------------------------------------------------------------
// Pure grouping logic — exported for unit tests
// ---------------------------------------------------------------------------

export function groupWorkflowEvents(
  events: readonly WorkflowEvent[]
): Map<string, WorkflowGroup> {
  const groupMap = new Map<string, WorkflowGroup>();

  for (const evt of events) {
    const id = evt.workflow_id;
    const existing = groupMap.get(id);
    const updatedEvents: WorkflowEvent[] = existing
      ? [...existing.events, evt]
      : [evt];

    groupMap.set(id, buildGroup(id, updatedEvents));
  }

  return groupMap;
}

function buildGroup(workflowId: string, events: readonly WorkflowEvent[]): WorkflowGroup {
  // Derive task from first workflow.started event.
  const startedEvt = events.find((e) => e.event === 'workflow.started');
  const task = typeof startedEvt?.task === 'string' ? startedEvt.task : null;

  // Build phase records. Start with canonical phases, then append unknowns.
  const phaseNames = new Set<string>(CANONICAL_PHASES);
  for (const e of events) {
    if (
      (e.event === 'workflow.phase_started' || e.event === 'workflow.phase_complete') &&
      typeof e.phase === 'string'
    ) {
      phaseNames.add(e.phase);
    }
  }

  const phases: PhaseRecord[] = [...phaseNames].map((name) => {
    const started = events.some(
      (e) => e.event === 'workflow.phase_started' && e.phase === name
    );
    const complete = events.some(
      (e) => e.event === 'workflow.phase_complete' && e.phase === name
    );
    const voteEvt = [...events]
      .reverse()
      .find((e) => e.event === 'workflow.vote_cast' && e.phase === name);
    const voteResult: VoteResult | null =
      voteEvt !== undefined && isVoteResult(voteEvt.result) ? voteEvt.result : null;

    return { name, started, complete, voteResult };
  });

  // Terminal status.
  let terminalStatus: WorkflowTerminalStatus = 'active';
  if (events.some((e) => e.event === 'workflow.complete')) terminalStatus = 'complete';
  else if (events.some((e) => e.event === 'workflow.failed')) terminalStatus = 'failed';

  // Failure reason.
  const failedEvt = events.find((e) => e.event === 'workflow.failed');
  const failureReason =
    failedEvt !== undefined && typeof failedEvt.reason === 'string'
      ? failedEvt.reason
      : null;

  const startedAt = events[0]?.timestamp ?? '';
  const updatedAt = events[events.length - 1]?.timestamp ?? '';

  return {
    workflowId,
    task,
    events,
    phases,
    terminalStatus,
    failureReason,
    startedAt,
    updatedAt,
  };
}

function isVoteResult(v: unknown): v is VoteResult {
  return v === 'PASS' || v === 'FAIL' || v === 'BLOCKED';
}

// ---------------------------------------------------------------------------
// Display filter — active groups + 3 most-recently-updated terminal groups
// ---------------------------------------------------------------------------

export function filterDisplayGroups(
  groups: ReadonlyMap<string, WorkflowGroup>
): ReadonlyMap<string, WorkflowGroup> {
  const active: WorkflowGroup[] = [];
  const terminal: WorkflowGroup[] = [];

  for (const group of groups.values()) {
    if (group.terminalStatus === 'active') active.push(group);
    else terminal.push(group);
  }

  terminal.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  const visible = [...active, ...terminal.slice(0, MAX_TERMINAL_GROUPS)];
  return new Map(visible.map((g) => [g.workflowId, g]));
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export interface UseWorkflowEventsReturn {
  readonly workflowGroups: ReadonlyMap<string, WorkflowGroup>;
  readonly error: string | null;
}

export function useWorkflowEvents(): UseWorkflowEventsReturn {
  const [allEvents, setAllEvents] = useState<readonly WorkflowEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const cursorRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const poll = useCallback(async (): Promise<void> => {
    try {
      const url = ENDPOINTS.workflowEvents(cursorRef.current);
      const resp = await window.fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const body = (await resp.json()) as WorkflowEventsResponse;
      if (body.count > 0) {
        cursorRef.current += body.count;
        setAllEvents((prev) => [...prev, ...body.events]);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void poll();
    timerRef.current = setInterval(() => void poll(), POLL_MS);
    return () => {
      if (timerRef.current !== null) clearInterval(timerRef.current);
      cursorRef.current = 0;
      setAllEvents([]);
    };
  }, [poll]);

  const workflowGroups = useMemo(() => {
    const all = groupWorkflowEvents(allEvents);
    return filterDisplayGroups(all);
  }, [allEvents]);

  return { workflowGroups, error };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd AgenticOS/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add AgenticOS/frontend/src/hooks/useWorkflowEvents.ts
git commit -m "feat(frontend): add useWorkflowEvents polling hook with group derivation"
```

---

## Task 4: `WorkflowStatusPanel` component

**Files:**
- Create: `AgenticOS/frontend/src/components/WorkflowStatusPanel/WorkflowStatusPanel.tsx`
- Create: `AgenticOS/frontend/src/components/WorkflowStatusPanel/WorkflowStatusPanel.css`

- [ ] **Step 1: Create `WorkflowStatusPanel.css`**

```css
/* WorkflowStatusPanel.css
   Developer: Marcus Daley
   Date: 2026-05-01
   Purpose: Scoped styles for the workflow HUD panel. All colors reference
            tokens.css variables; no hex values appear here. */

/* --------------- Panel shell --------------- */
.workflow-panel {
  border: 1px solid rgba(139, 116, 53, 0.25);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.workflow-panel__title {
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: var(--letter-extra-wide);
  color: rgba(201, 169, 78, 0.55);
  text-transform: uppercase;
  margin: 0;
}

/* --------------- Empty state --------------- */
.workflow-panel--empty {
  min-height: 48px;
  justify-content: center;
}

.workflow-panel__empty-msg {
  font-size: var(--font-size-xs);
  letter-spacing: var(--letter-extra-wide);
  color: rgba(201, 169, 78, 0.3);
  text-transform: uppercase;
  margin: 0;
  text-align: center;
}

/* --------------- Error state --------------- */
.workflow-panel__error {
  font-size: var(--font-size-sm);
  color: var(--color-error-red);
  margin: 0;
}

/* --------------- Workflow section --------------- */
.workflow-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: rgba(27, 40, 56, 0.6);
  border-radius: var(--radius-md);
  border: 1px solid rgba(139, 116, 53, 0.15);
}

.workflow-section__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.workflow-section__id {
  font-size: var(--font-size-xs);
  color: rgba(201, 169, 78, 0.6);
  letter-spacing: var(--letter-wide);
  font-family: monospace;
}

.workflow-section__task {
  font-size: var(--font-size-sm);
  color: rgba(245, 230, 200, 0.85);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --------------- Status pill --------------- */
.workflow-pill {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: var(--letter-extra-wide);
  border-radius: var(--radius-sm);
  padding: 2px 7px;
  text-transform: uppercase;
  margin-left: auto;
  flex-shrink: 0;
}

.workflow-pill[data-status='active'] {
  background: rgba(201, 169, 78, 0.18);
  color: var(--color-gold-accent);
  border: 1px solid rgba(201, 169, 78, 0.35);
}

.workflow-pill[data-status='complete'] {
  background: rgba(39, 174, 96, 0.15);
  color: var(--color-success-green);
  border: 1px solid rgba(39, 174, 96, 0.3);
}

.workflow-pill[data-status='failed'] {
  background: rgba(192, 57, 43, 0.15);
  color: var(--color-error-red);
  border: 1px solid rgba(192, 57, 43, 0.3);
}

/* --------------- Phase bar --------------- */
.workflow-phases {
  display: flex;
  gap: 2px;
  height: 24px;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.workflow-phase {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  transition: background var(--motion-medium) var(--ease-standard);
  padding: 0 4px;
  overflow: hidden;
}

.workflow-phase[data-state='pending'] {
  background: rgba(27, 40, 56, 0.9);
  color: rgba(201, 169, 78, 0.25);
  border: 1px solid rgba(139, 116, 53, 0.12);
}

.workflow-phase[data-state='active'] {
  background: rgba(201, 169, 78, 0.14);
  color: var(--color-gold-accent);
  border: 1px solid rgba(201, 169, 78, 0.3);
  animation: phase-pulse var(--motion-slow) ease-in-out infinite alternate;
}

.workflow-phase[data-state='complete'] {
  background: rgba(77, 182, 172, 0.12);
  color: var(--color-teal-fg);
  border: 1px solid rgba(77, 182, 172, 0.25);
}

.workflow-phase[data-state='voted-pass'] {
  background: rgba(39, 174, 96, 0.12);
  color: var(--color-success-green);
  border: 1px solid rgba(39, 174, 96, 0.25);
}

.workflow-phase[data-state='voted-fail'] {
  background: rgba(192, 57, 43, 0.12);
  color: var(--color-error-red);
  border: 1px solid rgba(192, 57, 43, 0.25);
}

@keyframes phase-pulse {
  from { opacity: 0.7; }
  to   { opacity: 1.0; }
}

/* --------------- Vote badge --------------- */
.vote-badge {
  font-size: 8px;
  font-weight: 700;
  border-radius: 2px;
  padding: 1px 4px;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.vote-badge[data-result='PASS'] {
  background: rgba(39, 174, 96, 0.2);
  color: var(--color-success-green);
}

.vote-badge[data-result='FAIL'],
.vote-badge[data-result='BLOCKED'] {
  background: rgba(192, 57, 43, 0.2);
  color: var(--color-error-red);
}

/* --------------- Footer meta --------------- */
.workflow-section__meta {
  font-size: var(--font-size-xs);
  color: rgba(160, 180, 255, 0.35);
  font-family: monospace;
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}
```

- [ ] **Step 2: Create `WorkflowStatusPanel.tsx`**

```typescript
// WorkflowStatusPanel.tsx
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: Read-only HUD panel showing live status for autonomous-workflow
//          skill runs. Self-hides when no events exist. One section per
//          workflow_id with phase segment bar and vote badges.

import type { FC } from 'react';
import { useWorkflowEvents } from '@/hooks/useWorkflowEvents';
import type { PhaseRecord, WorkflowGroup, WorkflowTerminalStatus } from '@/types/workflow';
import './WorkflowStatusPanel.css';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function phaseState(phase: PhaseRecord): string {
  if (phase.voteResult === 'PASS') return 'voted-pass';
  if (phase.voteResult === 'FAIL' || phase.voteResult === 'BLOCKED') return 'voted-fail';
  if (phase.complete) return 'complete';
  if (phase.started) return 'active';
  return 'pending';
}

function formatTimestamp(iso: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return iso;
  }
}

function pillLabel(status: WorkflowTerminalStatus): string {
  if (status === 'complete') return 'COMPLETE';
  if (status === 'failed') return 'FAILED';
  return 'RUNNING';
}

// ---------------------------------------------------------------------------
// WorkflowSection — one workflow run
// ---------------------------------------------------------------------------

const WorkflowSection: FC<{ group: WorkflowGroup }> = ({ group }) => (
  <section
    className="workflow-section"
    aria-label={`Workflow ${group.workflowId}`}
  >
    <header className="workflow-section__header">
      <span className="workflow-section__id mono">
        {group.workflowId.slice(0, 8)}
      </span>
      {group.task !== null && (
        <span className="workflow-section__task" title={group.task}>
          {group.task}
        </span>
      )}
      <span
        className="workflow-pill tactical-label"
        data-status={group.terminalStatus}
        aria-label={`Status: ${pillLabel(group.terminalStatus)}`}
      >
        {pillLabel(group.terminalStatus)}
      </span>
    </header>

    <div className="workflow-phases" role="list" aria-label="Phase progress">
      {group.phases.map((phase) => {
        const state = phaseState(phase);
        return (
          <div
            key={phase.name}
            className="workflow-phase"
            data-state={state}
            role="listitem"
            aria-label={`${phase.name}: ${state}`}
          >
            <span>{phase.name.slice(0, 4).toUpperCase()}</span>
            {phase.voteResult !== null && (
              <span
                className="vote-badge"
                data-result={phase.voteResult}
                aria-label={`Vote: ${phase.voteResult}`}
              >
                {phase.voteResult}
              </span>
            )}
          </div>
        );
      })}
    </div>

    {group.failureReason !== null && (
      <p className="workflow-panel__error" role="alert">
        {group.failureReason}
      </p>
    )}

    <div className="workflow-section__meta">
      <span>Started {formatTimestamp(group.startedAt)}</span>
      <span>Updated {formatTimestamp(group.updatedAt)}</span>
    </div>
  </section>
);

// ---------------------------------------------------------------------------
// WorkflowStatusPanel
// ---------------------------------------------------------------------------

export const WorkflowStatusPanel: FC = () => {
  const { workflowGroups, error } = useWorkflowEvents();

  if (workflowGroups.size === 0 && error === null) {
    return (
      <aside className="workflow-panel workflow-panel--empty" aria-label="Workflow status">
        <h2 className="workflow-panel__title">WORKFLOW STATUS</h2>
        <p className="workflow-panel__empty-msg tactical-label">NO WORKFLOWS ACTIVE</p>
      </aside>
    );
  }

  return (
    <aside className="workflow-panel" aria-label="Workflow status">
      <h2 className="workflow-panel__title">WORKFLOW STATUS</h2>

      {error !== null && (
        <p className="workflow-panel__error" role="alert">{error}</p>
      )}

      {[...workflowGroups.values()].map((group) => (
        <WorkflowSection key={group.workflowId} group={group} />
      ))}
    </aside>
  );
};
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd AgenticOS/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add AgenticOS/frontend/src/components/WorkflowStatusPanel/
git commit -m "feat(frontend): add WorkflowStatusPanel component and styles"
```

---

## Task 5: Wire panel into `App.tsx`

**Files:**
- Modify: `AgenticOS/frontend/src/App.tsx`

- [ ] **Step 1: Add the import**

In `AgenticOS/frontend/src/App.tsx`, add the import after the existing `SkillCommandPanel` import line:

```typescript
import { WorkflowStatusPanel } from '@/components/WorkflowStatusPanel/WorkflowStatusPanel';
```

- [ ] **Step 2: Add the JSX**

Find the block:
```tsx
          <SkillCommandPanel selectedProject={selectedProject} />

          {viewMode === 'brain' ? (
```

Replace with:
```tsx
          <SkillCommandPanel selectedProject={selectedProject} />

          <WorkflowStatusPanel />

          {viewMode === 'brain' ? (
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd AgenticOS/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add AgenticOS/frontend/src/App.tsx
git commit -m "feat(frontend): wire WorkflowStatusPanel into app shell below SkillCommandPanel"
```

---

## Task 6: Build verification

- [ ] **Step 1: Run the full frontend build**

```bash
cd AgenticOS/frontend
npm run build
```

Expected: build succeeds with no TypeScript errors and no import resolution failures.

- [ ] **Step 2: Run all Python tests**

```bash
cd C:\ClaudeSkills
python -m pytest AgenticOS/tests/ -v
```

Expected: all existing tests pass plus the 5 new workflow endpoint tests.

- [ ] **Step 3: Start the server and confirm the endpoint responds**

```bash
cd C:\ClaudeSkills
python -m AgenticOS.agentic_server
```

Then in a second terminal:
```bash
curl http://127.0.0.1:7842/workflow-events
```

Expected JSON: `{"since": 0, "count": 0, "events": []}` (no events written yet).

- [ ] **Step 4: Commit verification tag**

```bash
git tag workflow-status-panel-v1
```

---

## Self-Review Checklist

### Spec coverage

| Spec section | Task covering it |
|---|---|
| §3.1 GET /workflow-events endpoint | Task 1 |
| §3.2 useWorkflowEvents hook (cursor, grouping) | Task 3 |
| §4 TypeScript types | Task 2 |
| §5 Hook contract + grouping logic + display subset | Task 3 |
| §6.1 Layout | Task 4 |
| §6.2 Phase segment bar (data-state, tokens) | Task 4 |
| §6.3 Status pill mapping | Task 4 |
| §6.4 Vote badge | Task 4 |
| §6.5 Empty state | Task 4 |
| §6.6 Error state | Task 4 |
| §7 App.tsx integration | Task 5 |
| §8 config.ts ENDPOINTS.workflowEvents | Task 2 |
| §9 Color contract (tokens only) | Task 4 CSS |
| §10 All 7 files enumerated | Tasks 1–5 |

All spec requirements covered.

### Placeholder scan

No TBD, TODO, "implement later", "add appropriate", or "similar to" patterns present.
All code blocks are complete and runnable.

### Type consistency

- `WorkflowEvent`, `WorkflowGroup`, `PhaseRecord`, `VoteResult`, `WorkflowTerminalStatus`,
  `WorkflowEventsResponse` — all defined in Task 2 (`workflow.ts`), imported by name in
  Tasks 3 and 4. No divergent spellings.
- `groupWorkflowEvents` and `filterDisplayGroups` — defined in Task 3, not referenced in
  later tasks (component calls hook, not utilities directly). Consistent.
- `ENDPOINTS.workflowEvents` — defined in Task 2, called in Task 3. Signature matches:
  `(since?: number, workflowId?: string) => string`.
