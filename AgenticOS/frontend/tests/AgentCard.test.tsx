// AgentCard.test.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for the AgentCard component. Covers identity
//          rendering, status-driven button gating, and the conditional
//          ReviewerPanel + error banner. Uses a fixture factory so each
//          test reads as a focused override.

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { AgentCard } from '@/components/AgentCard/AgentCard';
import type { AgentState } from '@/types/agent';

// ---------------------------------------------------------------------------
// makeAgent
//
// Returns a known-good AgentState that satisfies all required fields.
// Tests override individual fields via the partial argument so the
// intent of each test is visible at a glance.
// ---------------------------------------------------------------------------

function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
  // Spread the base, then the override. Required keys must always be
  // present even when overrides is empty.
  const base: AgentState = {
    agent_id: 'AGENT-01',
    domain: 'va-advisory',
    task: 'Analyze CFR Title 38',
    stage_label: 'Parsing regulation text',
    stage: 2,
    total_stages: 5,
    progress_pct: 40,
    status: 'active',
    context_pct_used: 30,
    output_ref: null,
    awaiting: null,
    error_msg: null,
    spawned_by: null,
    reviewer_verdict: null,
    updated_at: '2026-04-29T10:00:00Z',
  };
  return { ...base, ...overrides };
}

// ---------------------------------------------------------------------------
// renderCard
//
// Standard render harness. Returns the spy so tests can assert on
// callback args without instantiating one per test.
// ---------------------------------------------------------------------------

function renderCard(
  agent: AgentState,
  isLoading: boolean = false,
  postError: string | null = null
) {
  const onApprove = vi.fn();
  render(
    <AgentCard
      agent={agent}
      isLoading={isLoading}
      postError={postError}
      onApprove={onApprove}
    />
  );
  return { onApprove };
}

describe('AgentCard', () => {
  it('renders the agent ID, domain label, and stage line', () => {
    // Verifies the static identity fields make it into the DOM.
    renderCard(makeAgent());
    expect(screen.getByText('AGENT-01')).toBeInTheDocument();
    expect(screen.getByText('[VA-ADVISORY]')).toBeInTheDocument();
    // The stage line includes the formatted prefix from formatters.ts.
    expect(
      screen.getByText(/Stage 2\/5/u)
    ).toBeInTheDocument();
    expect(
      screen.getByText('Analyze CFR Title 38')
    ).toBeInTheDocument();
  });

  it('updates the StatusPill text when the status prop changes', () => {
    // First render in active state so we have a baseline.
    const { rerender } = render(
      <AgentCard
        agent={makeAgent({ status: 'active' })}
        isLoading={false}
        postError={null}
        onApprove={vi.fn()}
      />
    );
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();

    // Re-render with a new status; the pill must reflect the change.
    rerender(
      <AgentCard
        agent={makeAgent({ status: 'waiting_approval' })}
        isLoading={false}
        postError={null}
        onApprove={vi.fn()}
      />
    );
    expect(screen.getByText('WAITING APPROVAL')).toBeInTheDocument();
  });

  it('disables approval buttons unless status is waiting_approval', () => {
    // Sanity: in the active state the gate is not open.
    renderCard(makeAgent({ status: 'active' }));
    expect(screen.getByRole('button', { name: /proceed/iu })).toBeDisabled();
    expect(
      screen.getByRole('button', { name: /research more/iu })
    ).toBeDisabled();
    expect(
      screen.getByRole('button', { name: /review by agent/iu })
    ).toBeDisabled();
  });

  it('forwards the agent_id and decision when a gate button is clicked', () => {
    // When the gate is open, every button must POST a different decision
    // but the same agent_id.
    const agent = makeAgent({ status: 'waiting_approval' });
    const { onApprove } = renderCard(agent);

    fireEvent.click(screen.getByRole('button', { name: /proceed/iu }));
    expect(onApprove).toHaveBeenLastCalledWith('AGENT-01', 'proceed');

    fireEvent.click(screen.getByRole('button', { name: /research more/iu }));
    expect(onApprove).toHaveBeenLastCalledWith('AGENT-01', 'research');

    fireEvent.click(screen.getByRole('button', { name: /review by agent/iu }));
    expect(onApprove).toHaveBeenLastCalledWith('AGENT-01', 'review');
  });

  it('renders the error banner only when status is error and msg is set', () => {
    // An error message paired with a non-error status should NOT show
    // the alert; this prevents stale errors from leaking visually.
    renderCard(makeAgent({ status: 'active', error_msg: 'stale error' }));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows the reviewer panel only when reviewer_verdict is non-null', () => {
    // No verdict: panel is absent entirely.
    renderCard(makeAgent({ reviewer_verdict: null }));
    expect(screen.queryByText(/reviewer verdict/iu)).not.toBeInTheDocument();
  });
});
