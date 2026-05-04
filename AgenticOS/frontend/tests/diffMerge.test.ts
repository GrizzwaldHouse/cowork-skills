// diffMerge.test.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for the pure diffMerge utility. Verifies that
//          snapshot ingestion replaces the map, diffs apply add/update/
//          remove correctly, and a no-op diff returns the same map
//          reference (cheap React reference-equality optimization).

import { describe, expect, it } from 'vitest';
import {
  agentMapToArray,
  applyDiff,
  applySnapshot,
  type AgentMap,
} from '@/utils/diffMerge';
import {
  MESSAGE_TYPE_DIFF,
  MESSAGE_TYPE_SNAPSHOT,
} from '@/config';
import type { AgentState } from '@/types/agent';
import type { DiffMessage, SnapshotMessage } from '@/types/messages';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeAgent(id: string, overrides: Partial<AgentState> = {}): AgentState {
  // Single base shape; tests parameterize id and any field they care about.
  const base: AgentState = {
    agent_id: id,
    domain: 'general',
    task: 'Test task',
    stage_label: 'Step',
    stage: 1,
    total_stages: 1,
    progress_pct: 0,
    status: 'active',
    context_pct_used: 0,
    output_ref: null,
    awaiting: null,
    error_msg: null,
    spawned_by: null,
    reviewer_verdict: null,
    updated_at: '2026-04-29T10:00:00Z',
  };
  return { ...base, ...overrides };
}

function makeSnapshot(...agents: AgentState[]): SnapshotMessage {
  // Index by agent_id for the wire shape.
  const indexed: Record<string, AgentState> = {};
  for (const agent of agents) {
    indexed[agent.agent_id] = agent;
  }
  return { type: MESSAGE_TYPE_SNAPSHOT, seq: 1, agents: indexed };
}

function makeDiff(
  seq: number,
  added: AgentState[] = [],
  updated: AgentState[] = [],
  removed: string[] = []
): DiffMessage {
  // Helper builds the wire shape from arrays so test intent is readable.
  const indexAdded: Record<string, AgentState> = {};
  for (const agent of added) {
    indexAdded[agent.agent_id] = agent;
  }
  const indexUpdated: Record<string, AgentState> = {};
  for (const agent of updated) {
    indexUpdated[agent.agent_id] = agent;
  }
  return {
    type: MESSAGE_TYPE_DIFF,
    seq,
    added: indexAdded,
    updated: indexUpdated,
    removed,
  };
}

describe('applySnapshot', () => {
  it('builds a map containing every agent from the snapshot', () => {
    const snapshot = makeSnapshot(makeAgent('AGENT-01'), makeAgent('AGENT-02'));
    const map = applySnapshot(snapshot);
    expect(map.size).toBe(2);
    expect(map.get('AGENT-01')?.agent_id).toBe('AGENT-01');
  });

  it('returns an empty map when the snapshot has no agents', () => {
    // Edge case: a fresh server with no active agents must clear the map.
    const map = applySnapshot(makeSnapshot());
    expect(map.size).toBe(0);
  });
});

describe('applyDiff', () => {
  it('adds new agents to the map', () => {
    // Adding an agent should leave existing entries untouched.
    const before: AgentMap = applySnapshot(makeSnapshot(makeAgent('AGENT-01')));
    const diff = makeDiff(2, [makeAgent('AGENT-02', { progress_pct: 50 })]);
    const after = applyDiff(before, diff);
    expect(after.size).toBe(2);
    expect(after.get('AGENT-02')?.progress_pct).toBe(50);
  });

  it('updates existing agents with the new full state', () => {
    // Updates carry a full AgentState; the new value replaces the old.
    const before = applySnapshot(makeSnapshot(makeAgent('AGENT-01', { progress_pct: 10 })));
    const diff = makeDiff(2, [], [makeAgent('AGENT-01', { progress_pct: 75 })]);
    const after = applyDiff(before, diff);
    expect(after.get('AGENT-01')?.progress_pct).toBe(75);
  });

  it('removes agents listed under removed', () => {
    // Remove one agent and confirm the other stays.
    const before = applySnapshot(
      makeSnapshot(makeAgent('AGENT-01'), makeAgent('AGENT-02'))
    );
    const diff = makeDiff(2, [], [], ['AGENT-01']);
    const after = applyDiff(before, diff);
    expect(after.has('AGENT-01')).toBe(false);
    expect(after.has('AGENT-02')).toBe(true);
  });

  it('returns the same map reference for an empty (no-op) diff', () => {
    // Reference-equal short-circuit lets React skip re-render work.
    const before = applySnapshot(makeSnapshot(makeAgent('AGENT-01')));
    const diff = makeDiff(2, [], [], []);
    const after = applyDiff(before, diff);
    expect(after).toBe(before);
  });
});

describe('agentMapToArray', () => {
  it('returns a stable, lexicographically sorted array of agents', () => {
    // Insertion order Z, A; sort must yield A, Z so card order is stable
    // even when the server adds agents in arbitrary order.
    const map = applySnapshot(
      makeSnapshot(makeAgent('AGENT-Z'), makeAgent('AGENT-A'))
    );
    const list = agentMapToArray(map);
    expect(list.map((agent) => agent.agent_id)).toEqual([
      'AGENT-A',
      'AGENT-Z',
    ]);
  });
});
