// AgentCard.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Per-agent instrument panel card. Composes StatusPill,
//          SonarHUD, ProgressBar, ContextMeter, ApprovalButtons, and
//          ReviewerPanel into the layout from spec section 6. Pure
//          presentational; all state flows in via props, all decisions
//          flow out via the onApprove callback.

import type { FC } from 'react';
import type { AgentState, ApprovalKind } from '@/types/agent';
import {
  formatDomainLabel,
  formatStageLabel,
  formatTimestamp,
} from '@/utils/formatters';
import { StatusPill } from '@/components/StatusPill/StatusPill';
import { SonarHUD } from '@/components/SonarHUD/SonarHUD';
import { ProgressBar } from '@/components/ProgressBar/ProgressBar';
import { ContextMeter } from '@/components/ContextMeter/ContextMeter';
import { ApprovalButtons } from '@/components/ApprovalButtons/ApprovalButtons';
import { ReviewerPanel } from '@/components/ReviewerPanel/ReviewerPanel';
import { DOMAIN_COLORS } from '@/components/AIArchGuide';
import './AgentCard.css';

interface AgentCardProps {
  // The agent state to render. Required; cards never exist without one.
  readonly agent: AgentState;

  // True while a POST is in-flight for this specific agent.
  readonly isLoading: boolean;

  // Last POST error for this agent, null if clean.
  readonly postError: string | null;

  // Bubbles up to App; receives agent_id + decision so the parent can
  // pick the right endpoint and track loading per agent.
  readonly onApprove: (agentId: string, decision: ApprovalKind) => void;
}

// Stateless. Why no useMemo on the formatted strings: they're tiny pure
// calls; memoizing them would cost more than it saves and add noise.
export const AgentCard: FC<AgentCardProps> = ({
  agent,
  isLoading,
  postError,
  onApprove,
}) => {
  // Compose the display labels once per render.
  const domainLabel = formatDomainLabel(agent.domain);
  const stageLine = formatStageLabel(
    agent.stage,
    agent.total_stages,
    agent.stage_label
  );
  const updatedAt = formatTimestamp(agent.updated_at);

  // Wrap the parent's callback so the buttons do not need to know the
  // agent_id; AgentCard injects it once here.
  const handleApprove = (decision: ApprovalKind): void => {
    onApprove(agent.agent_id, decision);
  };

  const domainColor = DOMAIN_COLORS[agent.domain] ?? '#8b5cf6';

  return (
    <article
      className="agent-card"
      data-status={agent.status}
      data-domain={agent.domain}
      aria-label={`Agent card for ${agent.agent_id}`}
      style={{ '--domain-color': domainColor } as React.CSSProperties}
    >
      {/* Header row: ID + domain on the left, status pill on the right. */}
      <header className="agent-card__header">
        <div className="agent-card__identity">
          <span className="agent-card__id mono">{agent.agent_id}</span>
          <span className="agent-card__domain tactical-label">
            [{domainLabel}]
          </span>
        </div>
        <StatusPill status={agent.status} />
      </header>

      <hr className="agent-card__divider" aria-hidden="true" />

      {/* Stage info and overall task description. */}
      <p className="agent-card__stage-line">{stageLine}</p>
      <p className="agent-card__task">{agent.task}</p>

      {/* Sonar HUD: Plan 4 wires the Spline scene. The component now takes
          an agents array so a single global HUD can drive every panel; here
          inside AgentCard we wrap the one agent in a single-element array
          so the existing per-card layout still composes. A future refactor
          may hoist the SonarHUD up to the App level and remove this usage. */}
      <SonarHUD agents={[agent]} />

      {/* Stage progress bar. Label is omitted because the stage line
          above already names the stage; the bar is purely visual here. */}
      <ProgressBar
        value={agent.progress_pct}
        ariaLabel={`Stage progress for ${agent.agent_id}`}
      />

      {/* Approval row. Disabled unless the agent is actually waiting. */}
      <ApprovalButtons
        agent={agent}
        isLoading={isLoading}
        postError={postError}
        onApprove={handleApprove}
      />

      {/* Context meter and last-update timestamp share a row to keep the
          card vertically compact. Timestamps use mono so digits align. */}
      <div className="agent-card__telemetry">
        <span className="agent-card__telemetry-label tactical-label">
          CONTEXT
        </span>
        <ContextMeter pctUsed={agent.context_pct_used} />
        <span
          className="agent-card__updated mono"
          aria-label={`Last update at ${updatedAt} UTC`}
        >
          {updatedAt}
        </span>
      </div>

      {/* Error banner. Only rendered when status === 'error' AND a
          message exists; either condition alone leaves it hidden. */}
      {agent.status === 'error' && agent.error_msg !== null && (
        <p className="agent-card__error" role="alert">
          {agent.error_msg}
        </p>
      )}

      {/* Reviewer verdict panel. Hides itself when verdict is null. */}
      <ReviewerPanel verdict={agent.reviewer_verdict} />
    </article>
  );
};
