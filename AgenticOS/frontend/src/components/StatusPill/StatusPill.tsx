// StatusPill.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Renders the lifecycle status of an agent as a colored pill in
//          the card header. Five status values map to five token-driven
//          color schemes via a data attribute; CSS owns the actual hex
//          values so a token change automatically propagates here.

import type { FC } from 'react';
import type { AgentStatus } from '@/types/agent';
import { formatStatusLabel } from '@/utils/formatters';
import './StatusPill.css';

interface StatusPillProps {
  // Lifecycle status from the AgentState. Required, never null because
  // every agent always has a status.
  readonly status: AgentStatus;
}

// StatusPill is a stateless presentational component. The colored dot
// before the label is a Unicode bullet rather than a styled span so the
// pill collapses nicely if CSS fails to load (degrades to plain text).
export const StatusPill: FC<StatusPillProps> = ({ status }) => {
  // Look up the human label once per render. Cheap, no need to memo.
  const label = formatStatusLabel(status);

  return (
    <span
      className="status-pill"
      data-status={status}
      role="status"
      aria-label={`Agent status: ${label}`}
    >
      <span className="status-pill__dot" aria-hidden="true" />
      <span className="status-pill__label">{label}</span>
    </span>
  );
};
