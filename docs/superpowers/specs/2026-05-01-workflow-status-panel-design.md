# WorkflowStatusPanel — Design Spec
**Author:** Marcus Daley  
**Date:** 2026-05-01  
**Status:** Approved (brainstorm confirmed 2026-05-01)

---

## 1. Purpose

The WorkflowStatusPanel is a read-only HUD component that renders live status for
autonomous-workflow skill runs inside the AgenticOS Command Center. It connects the
`autonomous-workflow` skill's event stream (written to `state/outputs/workflow_events.json`
via `POST /events`) to a human-readable panel in the React frontend.

The panel follows the "what matters now" philosophy established by PhaseCard: ADHD-friendly,
high contrast, no noise when nothing is running.

---

## 2. Scope

### In scope
- `GET /workflow-events` REST endpoint (Python, `agentic_server.py`)
- `src/types/workflow.ts` — TypeScript mirror of `WorkflowEvent` from `models.py`
- `src/hooks/useWorkflowEvents.ts` — 5 s polling hook with grouping logic
- `src/config.ts` — `ENDPOINTS.workflowEvents` addition
- `src/components/WorkflowStatusPanel/WorkflowStatusPanel.tsx` + `.css`
- `App.tsx` — panel wired below `SkillCommandPanel`, above the agent grid

### Out of scope
- WebSocket broadcast of workflow events (future work)
- Writing to or controlling workflow execution from the HUD (read-only)
- Light theme support

---

## 3. Data Source

### 3.1 Server side — `GET /workflow-events`

New endpoint on `agentic_server.py`, follows the `/progress` pattern exactly.

```
GET /workflow-events?since=0&workflow_id=<optional-uuid>
```

Response shape:
```json
{
  "since": 0,
  "count": 4,
  "events": [
    {
      "event": "workflow.started",
      "workflow_id": "abc-123",
      "task": "Build WorkflowStatusPanel",
      "timestamp": "2026-05-01T10:00:00Z"
    }
  ]
}
```

Reads `OUTPUTS_DIR / "workflow_events.json"`. Returns `{"since": since, "count": 0, "events": []}` when the file does not exist yet. The `since` parameter is a 0-based array index (not a timestamp), matching the `/progress` cursor convention. Optional `workflow_id` query param filters to a single run.

### 3.2 Client side — `useWorkflowEvents` hook

- Polls `GET /workflow-events?since=<cursor>` every **5 000 ms** via `setInterval`.
- Holds a `cursorRef = useRef<number>(0)` internally; after each successful fetch appends
  returned events to a state array and advances `cursorRef.current += count`.
- Returns `workflowGroups: Map<string, WorkflowGroup>` where each group contains the
  ordered event list, derived phase progress, latest vote result, and terminal status.
- Clears accumulated events and resets the cursor on unmount. Never throws — errors are
  surfaced as `error: string | null`.

---

## 4. TypeScript Types (`src/types/workflow.ts`)

```ts
// Mirrors WorkflowEvent in AgenticOS/models.py (extra="allow").
// Index signature uses a type union so strict TypeScript accepts it alongside
// readonly named fields (exactOptionalPropertyTypes safe).
export type WorkflowEvent = {
  readonly event: WorkflowEventKind;
  readonly workflow_id: string;
  readonly timestamp: string;          // ISO 8601
  readonly task?: string;              // present on workflow.started
  readonly phase?: string;             // present on phase_started / phase_complete
  readonly decision?: string;          // present on vote_cast
  readonly result?: VoteResult;        // present on vote_cast
  readonly voters?: readonly string[]; // present on vote_cast
  readonly phases_run?: number;        // present on workflow.complete
  readonly reason?: string;            // present on workflow.failed
} & Record<string, unknown>;          // extra fields allowed by server schema

export type WorkflowEventKind =
  | 'workflow.started'
  | 'workflow.phase_started'
  | 'workflow.phase_complete'
  | 'workflow.vote_cast'
  | 'workflow.complete'
  | 'workflow.failed';

export type VoteResult = 'PASS' | 'FAIL' | 'BLOCKED';

export type WorkflowTerminalStatus = 'complete' | 'failed' | 'active';

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
  readonly phases: readonly PhaseRecord[];    // ordered: brainstorm, planning, execution, verification
  readonly terminalStatus: WorkflowTerminalStatus;
  readonly failureReason: string | null;
  readonly startedAt: string;
  readonly updatedAt: string;
}
```

---

## 5. Hook Contract (`src/hooks/useWorkflowEvents.ts`)

```ts
interface UseWorkflowEventsReturn {
  readonly workflowGroups: ReadonlyMap<string, WorkflowGroup>;
  readonly error: string | null;
}

export function useWorkflowEvents(): UseWorkflowEventsReturn
```

### Grouping logic

1. Fetch returns a flat event array in append order.
2. Group by `workflow_id`.
3. For each group, derive `phases` by scanning for `phase_started` / `phase_complete` /
   `vote_cast` events. The four canonical phase names are:
   `brainstorm`, `planning`, `execution`, `verification`.
   Any unknown phase name is added dynamically after the canonical four.
4. `terminalStatus` is `'complete'` if a `workflow.complete` event exists, `'failed'` if
   a `workflow.failed` event exists, otherwise `'active'`.

### Display subset rule

Return all `active` groups plus the **3 most recently updated** terminal groups.
This keeps the panel focused without requiring server-side pagination.

---

## 6. Component Design (`WorkflowStatusPanel`)

### 6.1 Layout

```
┌─ WORKFLOW STATUS ──────────────────────────────────────────┐
│ [workflow_id truncated]  "task description"    [STATUS PILL]│
│ ┌─ Phase bar ──────────────────────────────────────────────┐│
│ │ BRAINSTORM ✓ │ PLANNING ✓ │ EXECUTION → │ VERIFICATION   ││
│ └──────────────────────────────────────────────────────────┘│
│ Vote: PASS  ·  Started 10:00:01  ·  Updated 10:02:33        │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Phase segment bar

- Four equal-width segments, one per canonical phase.
- Segment states: `pending` (dim), `active` (gold pulsing), `complete` (teal), `voted-pass`
  (green), `voted-fail` (red).
- Uses CSS `data-state` attribute for color switching — no JS hex values in TSX.
- Reuses `--color-*` tokens from `tokens.css`; no new color values introduced.

### 6.3 Status pill mapping

| `terminalStatus` | Pill label | Color token |
|---|---|---|
| `active` | `RUNNING` | `--color-gold-accent` |
| `complete` | `COMPLETE` | `--color-success-green` |
| `failed` | `FAILED` | `--color-error-red` |

### 6.4 Vote badge

Appears inline after the phase name when `voteResult !== null`:
- `PASS` → small green chip: `--color-success-green`
- `FAIL` | `BLOCKED` → small red chip: `--color-error-red`

Mirrors the `ACTION NEEDED` badge pattern in `PhaseCard.tsx`.

### 6.5 Empty state

When `workflowGroups.size === 0`, renders:
```
WORKFLOW STATUS
NO WORKFLOWS ACTIVE
```
Same pattern as `SubagentActivityPanel`'s `--empty` modifier class.

### 6.6 Error state

Renders a single `role="alert"` paragraph showing the fetch error string.
Does not unmount the panel.

---

## 7. App.tsx Integration

```tsx
// Below <SkillCommandPanel>, above the agent grid <main>:
<WorkflowStatusPanel />
```

No props required. The panel is always mounted; it self-hides via the empty state.

---

## 8. `config.ts` Addition

```ts
workflowEvents: (since = 0, workflowId?: string): string => {
  const params = new URLSearchParams({ since: String(since) });
  if (workflowId) params.set('workflow_id', workflowId);
  return `${REST_BASE}/workflow-events?${params.toString()}`;
},
```

---

## 9. Status Color Contract

All colors reference `tokens.css` variables exclusively. No new tokens are introduced;
the mapping is:

| Workflow state | CSS token |
|---|---|
| Active / running | `--color-gold-accent` |
| Phase active (pulsing) | `--color-gold-accent` + CSS animation |
| Phase complete | `--color-teal-fg` |
| Vote PASS | `--color-success-green` |
| Vote FAIL / BLOCKED | `--color-error-red` |
| Workflow complete | `--color-success-green` |
| Workflow failed | `--color-error-red` |

---

## 10. Files Changed

| File | Change type |
|---|---|
| `AgenticOS/agentic_server.py` | Add `GET /workflow-events` endpoint |
| `AgenticOS/frontend/src/config.ts` | Add `ENDPOINTS.workflowEvents` |
| `AgenticOS/frontend/src/types/workflow.ts` | New file |
| `AgenticOS/frontend/src/hooks/useWorkflowEvents.ts` | New file |
| `AgenticOS/frontend/src/components/WorkflowStatusPanel/WorkflowStatusPanel.tsx` | New file |
| `AgenticOS/frontend/src/components/WorkflowStatusPanel/WorkflowStatusPanel.css` | New file |
| `AgenticOS/frontend/src/App.tsx` | Wire panel below SkillCommandPanel |

---

## 11. Non-Goals

- No WebSocket integration in this iteration.
- No workflow cancellation or control actions.
- No persistence of dismissed workflows.
- No light theme.
