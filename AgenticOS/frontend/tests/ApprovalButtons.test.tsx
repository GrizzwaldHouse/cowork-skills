// ApprovalButtons.test.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for ApprovalButtons. Covers gate-open logic,
//          per-button payload routing, the in-flight loading state,
//          and the error banner.

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ApprovalButtons } from '@/components/ApprovalButtons/ApprovalButtons';
import type { AgentState } from '@/types/agent';

// Reused fixture factory; identical pattern to AgentCard.test.tsx.
function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
  const base: AgentState = {
    agent_id: 'AGENT-42',
    domain: 'general',
    task: 'Test task',
    stage_label: 'Step',
    stage: 1,
    total_stages: 3,
    progress_pct: 10,
    status: 'waiting_approval',
    context_pct_used: 5,
    output_ref: null,
    awaiting: 'proceed',
    error_msg: null,
    spawned_by: null,
    reviewer_verdict: null,
    updated_at: '2026-04-29T10:00:00Z',
  };
  return { ...base, ...overrides };
}

describe('ApprovalButtons', () => {
  it('PROCEED click fires onApprove with proceed decision', () => {
    // Gate is open by default in the fixture.
    const onApprove = vi.fn();
    render(
      <ApprovalButtons
        agent={makeAgent()}
        isLoading={false}
        postError={null}
        onApprove={onApprove}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /proceed/iu }));
    expect(onApprove).toHaveBeenCalledOnce();
    expect(onApprove).toHaveBeenCalledWith('proceed');
  });

  it('RESEARCH MORE click fires onApprove with research decision', () => {
    // Independent check; ensures the second button is wired correctly.
    const onApprove = vi.fn();
    render(
      <ApprovalButtons
        agent={makeAgent()}
        isLoading={false}
        postError={null}
        onApprove={onApprove}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /research more/iu }));
    expect(onApprove).toHaveBeenCalledWith('research');
  });

  it('REVIEW BY AGENT click fires onApprove with review decision', () => {
    // Same pattern as above for the third button.
    const onApprove = vi.fn();
    render(
      <ApprovalButtons
        agent={makeAgent()}
        isLoading={false}
        postError={null}
        onApprove={onApprove}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /review by agent/iu }));
    expect(onApprove).toHaveBeenCalledWith('review');
  });

  it('disables every button when status is not waiting_approval', () => {
    // ACTIVE means the agent is mid-stage; no approval should be sent.
    render(
      <ApprovalButtons
        agent={makeAgent({ status: 'active' })}
        isLoading={false}
        postError={null}
        onApprove={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: /proceed/iu })).toBeDisabled();
    expect(
      screen.getByRole('button', { name: /research more/iu })
    ).toBeDisabled();
    expect(
      screen.getByRole('button', { name: /review by agent/iu })
    ).toBeDisabled();
  });

  it('disables every button while a POST is in flight, even at gate', () => {
    // isLoading must override gate-open to prevent double submission.
    render(
      <ApprovalButtons
        agent={makeAgent()}
        isLoading={true}
        postError={null}
        onApprove={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: /proceed/iu })).toBeDisabled();
    expect(screen.getByText(/sending/iu)).toBeInTheDocument();
  });

  it('renders the postError as an accessible alert', () => {
    // Surfacing the message via role=alert lets screen readers announce.
    render(
      <ApprovalButtons
        agent={makeAgent()}
        isLoading={false}
        postError="Server responded with 500: Internal Server Error"
        onApprove={vi.fn()}
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent(/500/u);
  });
});
