// SonarFallback.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: CSS-only sonar rings rendered when WebGL is unavailable. Renders
//          MAX_AGENT_SLOTS instrument panels regardless of how many agents
//          are currently present so the layout never reflows. Mirrors the
//          Spline scene palette via tokens.css for visual continuity.

import type { CSSProperties, FC } from 'react';
import type { AgentState } from '../../types/agent';
import { MAX_AGENT_SLOTS } from '../../utils/splineSync';
import './SonarFallback.css';

// Region label exposed to assistive tech. Phrased so the operator knows
// they are seeing the degraded mode, not a broken HUD.
const FALLBACK_REGION_LABEL = 'Agent status display, CSS render mode' as const;

// Visible heading inside the panel. Lowercase here, CSS uppercases it.
const FALLBACK_HEADING = 'Sonar HUD — CSS Mode' as const;

// Placeholder identifier and status string for empty slots. Kept as named
// constants so a future redesign can change the dash style in one place.
const EMPTY_SLOT_ID = '----' as const;
const EMPTY_SLOT_STATUS = '--' as const;

// Width of a slot identifier (zero-padded) used for the placeholder label
// of empty slots. Two digits matches AGENT-01 ... AGENT-32 layout in the
// rest of the app.
const SLOT_ID_PAD_WIDTH = 2 as const;

// Conversion factor for the --progress CSS custom property: progress_pct
// is already 0..100, so the property holds the raw percentage and the CSS
// conic-gradient multiplies it back into a percentage stop.
const PROGRESS_CSS_VAR = '--progress' as const;

interface SonarFallbackProps {
  // Whole agents list. Entries past MAX_AGENT_SLOTS are silently dropped
  // because there is no slot to render them in.
  readonly agents: readonly AgentState[];

  // When true, the slot identifier text is suppressed so this component
  // can be embedded inside a parent (e.g. AgentCard) that already renders
  // the agent_id, preventing duplicate text nodes that break getByText queries.
  readonly suppressSlotIds?: boolean;
}

// SonarFallback — produces a fixed-length grid of slots (filled where the
// agents array has data, inactive elsewhere). The fixed grid means a fast
// agent flicker does not cause a layout reflow.
export const SonarFallback: FC<SonarFallbackProps> = ({ agents, suppressSlotIds = false }) => {
  // Fixed-length array driven by MAX_AGENT_SLOTS. Mapping over a fixed
  // sentinel array makes the JSX readable and keeps slot keys stable.
  const slotIndices = Array.from({ length: MAX_AGENT_SLOTS }, (_unused, index) => index);

  return (
    <div
      className="sonar-fallback"
      role="region"
      aria-label={FALLBACK_REGION_LABEL}
    >
      <span className="sonar-fallback__label">{FALLBACK_HEADING}</span>
      {slotIndices.map((slotIndex) => {
        // agents[slotIndex] is undefined for empty slots; coerce to null
        // so SonarSlot has a single sentinel to branch on.
        const agent = agents[slotIndex] ?? null;
        return (
          <SonarSlot
            // Index keys are safe here: slot count is fixed, never reordered.
            key={slotIndex}
            slotIndex={slotIndex}
            agent={agent}
            suppressSlotId={suppressSlotIds}
          />
        );
      })}
    </div>
  );
};

interface SonarSlotProps {
  // Zero-based slot index. Used to compose the placeholder label for
  // empty slots so the operator can see which physical slot is empty.
  readonly slotIndex: number;

  // The agent occupying this slot, or null when the slot is empty.
  readonly agent: AgentState | null;

  // When true, the visible agent_id text is omitted from the live slot.
  // Used when SonarFallback is embedded inside a parent that already
  // renders the agent_id, preventing duplicate text nodes in the DOM.
  readonly suppressSlotId: boolean;
}

// SonarSlot — single instrument panel. Branches on agent presence so the
// empty path can opt out of animations entirely (cheaper paint cost).
const SonarSlot: FC<SonarSlotProps> = ({ slotIndex, agent, suppressSlotId }) => {
  // Slot number (1-based) used only in the aria-hidden empty slot label.
  // Using a numeric slot reference instead of AGENT-NN format prevents
  // collisions with real agent_id values rendered in occupied slots.
  const slotNumber = String(slotIndex + 1).padStart(SLOT_ID_PAD_WIDTH, '0');

  if (agent === null) {
    return (
      <div className="sonar-slot" aria-hidden="true">
        <div className="sonar-ring sonar-ring--inactive" />
        <span className="sonar-slot__id">{`SLOT-${slotNumber}`}</span>
        <span className="sonar-slot__status">{EMPTY_SLOT_STATUS}</span>
      </div>
    );
  }

  // CSS class name mirrors the AgentStatus literal exactly so a single
  // table in CSS handles every status without runtime lookups.
  const ringClassName = `sonar-ring sonar-ring--${agent.status}`;

  // The conic-gradient progress arc reads the inline custom property; we
  // cast through CSSProperties because TypeScript does not model custom
  // property keys natively.
  const progressStyle = {
    [PROGRESS_CSS_VAR]: agent.progress_pct,
  } as CSSProperties;

  return (
    <div className="sonar-slot" aria-label={`${agent.agent_id} ${agent.status}`}>
      <div className={ringClassName} style={progressStyle}>
        <div className="sonar-ring__progress" />
      </div>
      {!suppressSlotId && (
        <span className="sonar-slot__id">{agent.agent_id || EMPTY_SLOT_ID}</span>
      )}
      <span className="sonar-slot__status">{agent.status.replace(/_/g, ' ')}</span>
    </div>
  );
};
