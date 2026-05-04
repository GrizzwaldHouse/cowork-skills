// ProgressBar.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Animated horizontal progress bar showing 0..100 stage progress
//          for an agent. Pure presentational; the parent passes the raw
//          percentage and the bar clamps and animates. Used by AgentCard
//          beneath the SonarHUD.

import type { FC } from 'react';
import { clampPercentage, formatPercentage } from '@/utils/formatters';
import './ProgressBar.css';

interface ProgressBarProps {
  // Whole-number percentage from AgentState.progress_pct.
  readonly value: number;

  // Optional label, e.g. "Stage 2/5". Rendered above the bar when set.
  readonly label?: string;

  // Optional accessible name override; defaults to "Stage progress".
  readonly ariaLabel?: string;
}

// ProgressBar uses the WAI-ARIA progressbar role so screen readers
// announce changes. Visual fill is driven by inline width style; color
// is owned by ProgressBar.css.
export const ProgressBar: FC<ProgressBarProps> = ({
  value,
  label,
  ariaLabel,
}) => {
  // Clamp once. Avoids overflow visual when wire data is malformed.
  const clamped = clampPercentage(value);
  const accessibleName = ariaLabel ?? 'Stage progress';

  return (
    <div className="progress-bar">
      {/* Optional label row. Hidden when undefined to keep the layout
          tight when used inside compact card sections. */}
      {label !== undefined && (
        <div className="progress-bar__label-row">
          <span className="progress-bar__label">{label}</span>
          <span className="progress-bar__pct mono">
            {formatPercentage(clamped)}
          </span>
        </div>
      )}

      <div
        className="progress-bar__track"
        role="progressbar"
        aria-label={accessibleName}
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="progress-bar__fill"
          style={{ width: `${clamped}%` }}
          data-value={clamped}
        />
      </div>
    </div>
  );
};
