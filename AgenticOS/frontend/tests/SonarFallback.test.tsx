// SonarFallback.test.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Render tests for the SonarFallback component. Covers the
//          empty-agents render path, the per-status class application, the
//          fixed slot count regardless of agent count, and the progress
//          custom-property propagation.

import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SonarFallback } from '@/components/SonarHUD/SonarFallback';
import { MAX_AGENT_SLOTS } from '@/utils/splineSync';
import type { AgentState, AgentStatus } from '@/types/agent';

// makeAgent — same factory pattern used by AgentCard.test.tsx so tests
// across the suite read consistently. Only the fields under test need to
// vary between cases; everything else is a known-good baseline.
function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
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

describe('SonarFallback', () => {
  it('renders without throwing when given an empty agents array', () => {
    // Smoke test: the empty path is the most likely state on first paint
    // before the WebSocket snapshot arrives.
    expect(() => render(<SonarFallback agents={[]} />)).not.toThrow();
  });

  it('exposes an accessible region label so screen readers announce CSS mode', () => {
    // The fallback must be discoverable as a region; the operator deserves
    // to know the HUD is running in degraded mode.
    render(<SonarFallback agents={[]} />);
    expect(screen.getByRole('region')).toBeInTheDocument();
  });

  it('renders exactly MAX_AGENT_SLOTS slot elements regardless of agent count', () => {
    // Layout contract: a single agent must still produce a full grid so
    // adding a second agent does not cause a reflow.
    const { container } = render(<SonarFallback agents={[makeAgent()]} />);
    const slots = container.querySelectorAll('.sonar-slot');
    expect(slots).toHaveLength(MAX_AGENT_SLOTS);
  });

  it('applies the matching ring class for every AgentStatus value', () => {
    // Each status string must produce a CSS class with the same suffix so
    // the stylesheet selectors match without runtime mapping.
    const statuses: readonly AgentStatus[] = [
      'active',
      'waiting_approval',
      'waiting_review',
      'complete',
      'error',
    ];

    for (const status of statuses) {
      const { container, unmount } = render(
        <SonarFallback agents={[makeAgent({ status })]} />
      );
      const ring = container.querySelector(`.sonar-ring--${status}`);
      expect(ring).not.toBeNull();
      // Unmount between iterations to keep the DOM clean and avoid the
      // testing-library duplicate-element warning when the next render
      // also produces the same selector match.
      unmount();
    }
  });

  it('marks every slot beyond the agents array as inactive', () => {
    // One filled slot leaves MAX_AGENT_SLOTS - 1 inactive slots; matching
    // count protects against off-by-one in the index loop.
    const { container } = render(<SonarFallback agents={[makeAgent()]} />);
    const inactiveRings = container.querySelectorAll('.sonar-ring--inactive');
    expect(inactiveRings).toHaveLength(MAX_AGENT_SLOTS - 1);
  });

  it('renders the agent_id as the slot identifier when an agent is present', () => {
    // The visible label must come from the agent's identifier, not the
    // placeholder, so operators can correlate the ring with logs.
    render(<SonarFallback agents={[makeAgent({ agent_id: 'AGENT-07' })]} />);
    expect(screen.getByText('AGENT-07')).toBeInTheDocument();
  });

  it('forwards progress_pct as the --progress CSS custom property', () => {
    // The conic-gradient progress arc reads --progress; this asserts the
    // property reaches the DOM with the right value.
    const { container } = render(
      <SonarFallback agents={[makeAgent({ progress_pct: 75 })]} />
    );
    const ring = container.querySelector('.sonar-ring--active') as HTMLElement | null;
    expect(ring).not.toBeNull();
    if (ring !== null) {
      // jsdom returns the value as the original string; compare loosely.
      expect(ring.style.getPropertyValue('--progress')).toBe('75');
    }
  });
});
