// ContextMeter.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Gauge bar showing what percentage of an agent's Claude
//          context window has been consumed. The color follows three
//          named thresholds (normal / warn / critical) so context
//          pressure is visible at a glance without reading the number.

import type { FC } from 'react';
import {
  clampPercentage,
  formatPercentage,
  resolveContextThreshold,
} from '@/utils/formatters';
import './ContextMeter.css';

interface ContextMeterProps {
  // Whole-percentage from AgentState.context_pct_used.
  readonly pctUsed: number;
}

// ContextMeter renders a track with a colored fill plus a numeric
// readout to the right. Threshold and color selection live in
// formatters.ts so the policy is reviewable in one place.
export const ContextMeter: FC<ContextMeterProps> = ({ pctUsed }) => {
  const clamped = clampPercentage(pctUsed);
  const threshold = resolveContextThreshold(clamped);

  return (
    <div className="context-meter" data-threshold={threshold}>
      <div
        className="context-meter__track"
        role="progressbar"
        aria-label={`Context window used: ${clamped}%`}
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="context-meter__fill"
          style={{ width: `${clamped}%` }}
        />
      </div>
      <span className="context-meter__readout mono">
        {formatPercentage(clamped)}
      </span>
    </div>
  );
};
