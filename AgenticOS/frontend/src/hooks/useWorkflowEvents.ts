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
