// SubagentActivityPanel.test.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Unit tests for SubagentActivityPanel. Covers empty state,
//          sub-agent grouping under parents, stage label rendering,
//          context level data attributes, and error banner visibility.

import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SubagentActivityPanel } from '@/components/SubagentActivityPanel/SubagentActivityPanel';
import type { AgentState } from '@/types/agent';

// makeAgent returns a minimal valid AgentState. Tests override only what
// they need; the base covers every required field.
function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
  const base: AgentState = {
    agent_id: 'AGENT-01',
    domain: 'va-advisory',
    task: 'Analyze CFR Title 38',
    stage_label: 'Parsing regulation text',
    stage: 1,
    total_stages: 3,
    progress_pct: 33,
    status: 'active',
    context_pct_used: 20,
    output_ref: null,
    awaiting: null,
    error_msg: null,
    spawned_by: null,
    reviewer_verdict: null,
    updated_at: '2026-04-30T10:00:00Z',
  };
  return { ...base, ...overrides };
}

describe('SubagentActivityPanel', () => {
  it('renders the empty state when no sub-agents exist', () => {
    // A list of top-level agents (spawned_by === null) should produce
    // the quiet empty state, not a broken layout.
    render(
      <SubagentActivityPanel
        agents={[makeAgent({ agent_id: 'AGENT-01', spawned_by: null })]}
      />
    );
    expect(screen.getByText(/no sub-agents active/iu)).toBeInTheDocument();
  });

  it('renders the empty state when the agents list is empty', () => {
    render(<SubagentActivityPanel agents={[]} />);
    expect(screen.getByText(/no sub-agents active/iu)).toBeInTheDocument();
  });

  it('renders a sub-agent row when spawned_by is set', () => {
    const parent = makeAgent({ agent_id: 'AGENT-01', spawned_by: null });
    const child = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-01',
      task: 'Research buddy letter criteria',
      stage_label: 'Reviewing case file',
    });
    render(<SubagentActivityPanel agents={[parent, child]} />);

    // Child id and stage label must be visible.
    expect(screen.getByText('AGENT-02')).toBeInTheDocument();
    expect(screen.getByText('Reviewing case file')).toBeInTheDocument();
  });

  it('groups multiple sub-agents under the correct parent header', () => {
    const parent = makeAgent({ agent_id: 'AGENT-01', spawned_by: null });
    const childA = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-01',
      stage_label: 'Stage A work',
    });
    const childB = makeAgent({
      agent_id: 'AGENT-03',
      spawned_by: 'AGENT-01',
      stage_label: 'Stage B work',
    });
    render(<SubagentActivityPanel agents={[parent, childA, childB]} />);

    // Both children appear; parent id appears as section header.
    expect(screen.getByText('AGENT-02')).toBeInTheDocument();
    expect(screen.getByText('AGENT-03')).toBeInTheDocument();
    // Section header shows the parent id.
    expect(screen.getByText('AGENT-01')).toBeInTheDocument();
    // Sub-agent count label.
    expect(screen.getByText(/2 sub-agents/iu)).toBeInTheDocument();
  });

  it('shows 1 SUB-AGENT (singular) when only one child exists', () => {
    render(
      <SubagentActivityPanel
        agents={[
          makeAgent({ agent_id: 'AGENT-01', spawned_by: null }),
          makeAgent({ agent_id: 'AGENT-02', spawned_by: 'AGENT-01' }),
        ]}
      />
    );
    expect(screen.getByText(/1 sub-agent$/iu)).toBeInTheDocument();
  });

  it('shows the parent task as subtitle in the section header', () => {
    const parent = makeAgent({
      agent_id: 'AGENT-01',
      task: 'Draft veteran buddy letter',
      spawned_by: null,
    });
    const child = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-01',
    });
    render(<SubagentActivityPanel agents={[parent, child]} />);
    expect(screen.getByText('Draft veteran buddy letter')).toBeInTheDocument();
  });

  it('applies data-level="warn" when context is at the warn threshold', () => {
    const parent = makeAgent({ agent_id: 'AGENT-01', spawned_by: null });
    const child = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-01',
      context_pct_used: 70, // exactly CONTEXT_WARN_PCT
    });
    render(<SubagentActivityPanel agents={[parent, child]} />);
    const ctxEl = screen.getByLabelText(/context used: 70%/iu);
    expect(ctxEl).toHaveAttribute('data-level', 'warn');
  });

  it('applies data-level="crit" when context is at the crit threshold', () => {
    const parent = makeAgent({ agent_id: 'AGENT-01', spawned_by: null });
    const child = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-01',
      context_pct_used: 90, // exactly CONTEXT_CRIT_PCT
    });
    render(<SubagentActivityPanel agents={[parent, child]} />);
    const ctxEl = screen.getByLabelText(/context used: 90%/iu);
    expect(ctxEl).toHaveAttribute('data-level', 'crit');
  });

  it('renders the error banner only when status is error and error_msg is set', () => {
    const parent = makeAgent({ agent_id: 'AGENT-01', spawned_by: null });
    const child = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-01',
      status: 'error',
      error_msg: 'FileWriteError: Could not write agents.json at stage 2',
    });
    render(<SubagentActivityPanel agents={[parent, child]} />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(
      screen.getByText(/filewriteerror/iu)
    ).toBeInTheDocument();
  });

  it('does not render an error banner when status is active even with error_msg', () => {
    const parent = makeAgent({ agent_id: 'AGENT-01', spawned_by: null });
    const child = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-01',
      status: 'active',
      error_msg: 'stale error that must not show',
    });
    render(<SubagentActivityPanel agents={[parent, child]} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('handles sub-agents whose parent is not in the agents list', () => {
    // Parent not present — section header shows the id from spawned_by
    // with no task subtitle (parentAgent === undefined).
    const orphan = makeAgent({
      agent_id: 'AGENT-02',
      spawned_by: 'AGENT-UNKNOWN',
      stage_label: 'Orphaned stage work',
    });
    render(<SubagentActivityPanel agents={[orphan]} />);
    expect(screen.getByText('AGENT-02')).toBeInTheDocument();
    expect(screen.getByText('AGENT-UNKNOWN')).toBeInTheDocument();
  });
});
