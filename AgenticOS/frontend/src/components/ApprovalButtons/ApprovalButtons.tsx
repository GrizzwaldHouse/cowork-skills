// ApprovalButtons.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Three-button approval row at the bottom of an AgentCard. Each
//          button posts a different ApprovalKind. Buttons are enabled
//          only when the agent's status === 'waiting_approval' AND no
//          POST is currently in flight, which prevents double-posts and
//          out-of-band gate decisions.

import type { FC } from 'react';
import type { AgentState, ApprovalKind } from '@/types/agent';
import './ApprovalButtons.css';

interface ApprovalButtonsProps {
  // The agent this button row belongs to. Drives gate-open logic and
  // is the source of agent_id for the parent's onApprove callback.
  readonly agent: AgentState;

  // True while a POST is in-flight for this agent. Disables all three
  // buttons regardless of status to prevent double submission.
  readonly isLoading: boolean;

  // Last error from useApproval for this agent, null when clean.
  readonly postError: string | null;

  // Callback that triggers the POST. The parent (AgentCard) injects the
  // agent_id; this component only ships the decision kind.
  readonly onApprove: (decision: ApprovalKind) => void;
}

// Stateless. All UI state derives from props; loading and error live in
// useApproval which is owned higher up the tree.
export const ApprovalButtons: FC<ApprovalButtonsProps> = ({
  agent,
  isLoading,
  postError,
  onApprove,
}) => {
  // Gate is "open" when the agent has actually paused for approval AND
  // no concurrent POST is already in flight.
  const gateOpen = agent.status === 'waiting_approval' && !isLoading;

  return (
    <div className="approval-buttons" data-gate-open={gateOpen}>
      <button
        type="button"
        className="approval-btn approval-btn--proceed tactical-label"
        disabled={!gateOpen}
        aria-label="Proceed to the next stage"
        onClick={() => onApprove('proceed')}
      >
        PROCEED
      </button>

      <button
        type="button"
        className="approval-btn approval-btn--research tactical-label"
        disabled={!gateOpen}
        aria-label="Research more before continuing"
        onClick={() => onApprove('research')}
      >
        RESEARCH MORE
      </button>

      <button
        type="button"
        className="approval-btn approval-btn--review tactical-label"
        disabled={!gateOpen}
        aria-label="Review by agent"
        onClick={() => onApprove('review')}
      >
        REVIEW BY AGENT
      </button>

      {/* In-flight indicator. aria-live so screen readers announce. */}
      {isLoading && (
        <span
          className="approval-buttons__loading tactical-label"
          aria-live="polite"
        >
          SENDING
        </span>
      )}

      {/* Error message. role=alert so screen readers announce loudly. */}
      {postError !== null && (
        <p className="approval-buttons__error" role="alert">
          {postError}
        </p>
      )}
    </div>
  );
};
