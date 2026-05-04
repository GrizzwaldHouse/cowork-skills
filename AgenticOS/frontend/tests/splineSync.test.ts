// splineSync.test.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for syncSplineState. Verifies the per-slot variable
//          writes, the global agent count, status mapping, progress
//          clamping at the 0/100 bounds, slot count clamping at
//          MAX_AGENT_SLOTS, and graceful handling of an empty agents
//          array. Uses a hand-rolled mock Application object so the tests
//          run with no Spline runtime loaded.

import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Application } from '@splinetool/runtime';
import { MAX_AGENT_SLOTS, syncSplineState } from '@/utils/splineSync';
import type { AgentState, AgentStatus } from '@/types/agent';

// ---------------------------------------------------------------------------
// makeAgent
//
// Returns a known-good AgentState. Tests override individual fields via the
// partial argument so each test reads as a focused override against the
// same baseline; identical pattern to AgentCard.test.tsx for consistency.
// ---------------------------------------------------------------------------

function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
  // Required keys must always be present so the union type stays satisfied
  // even when overrides is empty. Mirrors the wire shape from AgenticOS.models.
  const base: AgentState = {
    agent_id: 'AGENT-01',
    domain: 'general',
    task: 'Test task',
    stage_label: 'Running',
    stage: 1,
    total_stages: 3,
    progress_pct: 50,
    status: 'active',
    context_pct_used: 20,
    output_ref: null,
    awaiting: null,
    error_msg: null,
    spawned_by: null,
    reviewer_verdict: null,
    updated_at: '2026-04-29T00:00:00Z',
  };
  return { ...base, ...overrides };
}

// ---------------------------------------------------------------------------
// makeMockSpline
//
// Builds a minimal Application stand-in. Only the methods syncSplineState
// touches need to exist. Cast through unknown so TypeScript accepts the
// reduced surface; at runtime the production code only ever calls these
// methods, so the mock is sufficient for behavior verification.
// ---------------------------------------------------------------------------

function makeMockSpline(): Application {
  return {
    setVariable: vi.fn(),
    emitEvent: vi.fn(),
    emitEventReverse: vi.fn(),
  } as unknown as Application;
}

// Convenience: pull the call list out of the spy in a typed way. setVariable
// always receives [name: string, value: unknown], reflected here.
function setVariableCalls(
  spline: Application
): Array<readonly [string, unknown]> {
  // Vitest typings widen mock.calls to unknown[][]; we know the shape.
  const fn = spline.setVariable as unknown as ReturnType<typeof vi.fn>;
  return fn.mock.calls.map((entry) => [entry[0] as string, entry[1]] as const);
}

describe('syncSplineState', () => {
  let spline: Application;

  beforeEach(() => {
    // Fresh spy per test so call history does not leak between cases.
    spline = makeMockSpline();
  });

  it('writes progress, state, and active=true for a single live agent', () => {
    // Baseline: one agent, progress 64, active status. Slot 1 should
    // receive all three variables with the literal values from the agent.
    const agents = [makeAgent({ progress_pct: 64, status: 'active' })];
    syncSplineState(spline, agents);

    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_progress', 64);
    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_state', 'active');
    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_active', true);
  });

  it('maps every AgentStatus value to its matching spline state string', () => {
    // The mapping must be total over the union: a missing entry would let
    // a valid status fall through to the inactive default and freeze the
    // ring animation.
    const allStatuses: readonly AgentStatus[] = [
      'active',
      'waiting_approval',
      'waiting_review',
      'complete',
      'error',
    ];

    for (const status of allStatuses) {
      const localSpline = makeMockSpline();
      syncSplineState(localSpline, [makeAgent({ status })]);
      expect(localSpline.setVariable).toHaveBeenCalledWith('agent_1_state', status);
    }
  });

  it('clamps progress_pct below zero up to the lower bound', () => {
    // Defensive clamp: a future server bug producing -10 must not let the
    // depth gauge spin to a negative angle.
    syncSplineState(spline, [makeAgent({ progress_pct: -10 })]);
    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_progress', 0);
  });

  it('clamps progress_pct above one hundred down to the upper bound', () => {
    // Symmetric clamp. 150 must read as 100, never overshooting the dial.
    syncSplineState(spline, [makeAgent({ progress_pct: 150 })]);
    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_progress', 100);
  });

  it('zeroes out unused slots beyond the active agent count', () => {
    // One agent occupies slot 1; slots 2..MAX_AGENT_SLOTS must be reset
    // to defaults so a previous render's data does not linger.
    syncSplineState(spline, [makeAgent()]);

    for (let slot = 2; slot <= MAX_AGENT_SLOTS; slot += 1) {
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_progress`, 0);
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_state`, 'active');
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_active`, false);
    }
  });

  it('sets global_agent_count to the visible agent count', () => {
    // Two distinct agents, two-slot scene; global count reads as 2.
    const agents = [
      makeAgent({ agent_id: 'AGENT-01' }),
      makeAgent({ agent_id: 'AGENT-02' }),
    ];
    syncSplineState(spline, agents);
    expect(spline.setVariable).toHaveBeenCalledWith('global_agent_count', 2);
  });

  it('writes only global_agent_count=0 plus zeroed slots when agents is empty', () => {
    // Empty agents array: every slot resets, the count is zero, but the
    // call still happens so the scene is not stuck on yesterday's value.
    syncSplineState(spline, []);

    expect(spline.setVariable).toHaveBeenCalledWith('global_agent_count', 0);
    for (let slot = 1; slot <= MAX_AGENT_SLOTS; slot += 1) {
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_active`, false);
    }
  });

  it('clamps the visible count to maxSlots when agents exceed the ceiling', () => {
    // Build MAX_AGENT_SLOTS + 5 agents to ensure overflow. The global
    // count must be clamped, and the overflow agents must not produce
    // any setVariable call beyond MAX_AGENT_SLOTS.
    const overflowAgents = Array.from(
      { length: MAX_AGENT_SLOTS + 5 },
      (_unused, index) => makeAgent({ agent_id: `AGENT-${index + 1}` })
    );
    syncSplineState(spline, overflowAgents);

    expect(spline.setVariable).toHaveBeenCalledWith('global_agent_count', MAX_AGENT_SLOTS);

    // Confirm no slot beyond MAX_AGENT_SLOTS was written. Any call to
    // agent_{MAX+1}_* would be a silent runtime no-op but a sign of a bug.
    const calls = setVariableCalls(spline);
    const writtenSlotNumbers = calls
      .map(([name]) => name.match(/^agent_(\d+)_/u))
      .filter((match): match is RegExpMatchArray => match !== null)
      .map((match) => Number.parseInt(match[1] as string, 10));

    for (const slot of writtenSlotNumbers) {
      expect(slot).toBeLessThanOrEqual(MAX_AGENT_SLOTS);
    }
  });

  it('respects a custom maxSlots argument override', () => {
    // Smaller scene scenario: the caller passes 4. Only slots 1..4 should
    // receive any variable writes; slot 5+ must remain untouched.
    syncSplineState(spline, [makeAgent(), makeAgent({ agent_id: 'A2' })], 4);

    const calls = setVariableCalls(spline);
    const progressCalls = calls.filter(([name]) => name.endsWith('_progress'));
    expect(progressCalls).toHaveLength(4);

    expect(spline.setVariable).toHaveBeenCalledWith('global_agent_count', 2);
  });

  it('always writes the global count exactly once per call', () => {
    // Regression guard: a refactor that puts the global write inside the
    // loop would silently double-fire. One sync call, one global write.
    syncSplineState(spline, [makeAgent()]);

    const calls = setVariableCalls(spline);
    const globalCalls = calls.filter(([name]) => name === 'global_agent_count');
    expect(globalCalls).toHaveLength(1);
  });
});
