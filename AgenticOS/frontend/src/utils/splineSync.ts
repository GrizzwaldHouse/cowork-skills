// splineSync.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Pure utility that maps the AgentState[] prop into Spline scene
//          variable writes. Lives outside the React tree so it can be unit
//          tested with a mock Application object and zero JSX. Single
//          source of truth for the variable-name-to-state mapping the
//          designer sees in public/spline/README.md.

import type { Application } from '@splinetool/runtime';
import type { AgentState, AgentStatus } from '../types/agent';
import { MAX_AGENT_SLOTS } from '../config';

// Re-export so component code that already imports from splineSync does not
// need a second import path for the slot ceiling. Keeps the module a single
// import surface for the SonarHUD chain.
export { MAX_AGENT_SLOTS };

// Per-slot variable name suffixes. The Spline designer creates variables
// using the pattern agent_{n}_{suffix}; centralizing the suffix table here
// guarantees the React side and the .splinecode file never drift.
const VARIABLE_SUFFIX_PROGRESS = 'progress' as const;
const VARIABLE_SUFFIX_STATE = 'state' as const;
const VARIABLE_SUFFIX_ACTIVE = 'active' as const;

// Global scene variable name. Drives the count of visible sonar contacts
// shown on the radar sweep at the top of the HUD.
const VARIABLE_NAME_GLOBAL_COUNT = 'global_agent_count' as const;

// Default values written to slots that have no agent assigned. Writing
// explicit defaults rather than skipping the slot prevents stale data from
// a previous render from continuing to drive the scene.
const INACTIVE_PROGRESS = 0 as const;
const INACTIVE_STATE = 'active' as const;
const INACTIVE_ACTIVE = false as const;

// Lower and upper bounds for progress percentage. The wire schema promises
// 0..100 but defensive clamping protects the scene from a future server
// change that lets the bound drift.
const PROGRESS_MIN = 0 as const;
const PROGRESS_MAX = 100 as const;

// Slot indices in the Spline scene are 1-based (agent_1_..., agent_2_...,
// ...). React arrays are 0-based; this offset bridges the two without
// scattering "+ 1" expressions through the loop body.
const SLOT_INDEX_OFFSET = 1 as const;

// Mapping table from the AgentStatus union to the string the Spline state
// machine reads. Today every member of the union maps to its own string
// verbatim; declaring the table explicitly makes a future divergence
// (for example, a designer-friendly label) a single-line edit here.
const STATUS_TO_SPLINE_STATE: Readonly<Record<AgentStatus, string>> = {
  active: 'active',
  waiting_approval: 'waiting_approval',
  waiting_review: 'waiting_review',
  complete: 'complete',
  error: 'error',
};

// buildSlotVariableName — composes a per-slot Spline variable name from a
// 1-based slot index and a known suffix. Defined as a named helper rather
// than inline string templates because the Spline designer has to type
// these names exactly; one helper means one place to audit the format.
function buildSlotVariableName(slotNumber: number, suffix: string): string {
  return `agent_${slotNumber}_${suffix}`;
}

// clampProgress — bounds the progress value to PROGRESS_MIN..PROGRESS_MAX.
// Explicit named function rather than an inline Math.min/Math.max so the
// intent is documented in the call site.
function clampProgress(value: number): number {
  if (Number.isNaN(value)) {
    return PROGRESS_MIN;
  }
  if (value < PROGRESS_MIN) {
    return PROGRESS_MIN;
  }
  if (value > PROGRESS_MAX) {
    return PROGRESS_MAX;
  }
  return value;
}

// mapStatusToSplineState — converts the AgentStatus union value to its
// Spline variable string. Falls back to the inactive default if a future
// status string somehow escapes the mapping table; defensive but cheap.
function mapStatusToSplineState(status: AgentStatus): string {
  const mapped = STATUS_TO_SPLINE_STATE[status];
  return mapped !== undefined ? mapped : INACTIVE_STATE;
}

// writeSlotVariables — writes the three per-slot variables for a single
// agent (or zeroes the slot when agent is null). Pulled out of the loop
// body for readability and so a future migration to a different scene API
// (Spline events, for example) only touches this one function.
function writeSlotVariables(
  spline: Application,
  slotNumber: number,
  agent: AgentState | null
): void {
  const progressName = buildSlotVariableName(slotNumber, VARIABLE_SUFFIX_PROGRESS);
  const stateName = buildSlotVariableName(slotNumber, VARIABLE_SUFFIX_STATE);
  const activeName = buildSlotVariableName(slotNumber, VARIABLE_SUFFIX_ACTIVE);

  if (agent === null) {
    // Empty slot: explicit defaults so the scene resets cleanly between
    // renders. Skipping the write would leave whatever value was last set.
    spline.setVariable(progressName, INACTIVE_PROGRESS);
    spline.setVariable(stateName, INACTIVE_STATE);
    spline.setVariable(activeName, INACTIVE_ACTIVE);
    return;
  }

  // Live slot: clamp progress, look up the spline state string, mark active.
  spline.setVariable(progressName, clampProgress(agent.progress_pct));
  spline.setVariable(stateName, mapStatusToSplineState(agent.status));
  spline.setVariable(activeName, true);
}

// syncSplineState — top-level entry point. Iterates every slot the scene
// exposes (regardless of how many agents are currently present) so unused
// slots are explicitly zeroed and the global agent count is always set.
//
// Pure function: no React hooks, no module-level state, no side effects
// beyond the spline.setVariable calls. Tested in isolation with a mock
// Application object — see tests/splineSync.test.ts.
export function syncSplineState(
  spline: Application,
  agents: readonly AgentState[],
  maxSlots: number = MAX_AGENT_SLOTS
): void {
  // Cap the visible agent count at the slot ceiling. Agents beyond this
  // index are dropped silently because the scene physically does not have
  // an instrument panel for them.
  const visibleAgentCount = Math.min(agents.length, maxSlots);

  for (let slotIndex = 0; slotIndex < maxSlots; slotIndex += 1) {
    const slotNumber = slotIndex + SLOT_INDEX_OFFSET;
    // agents[slotIndex] is undefined for slots past the array end; coerce
    // to null so the helper has a single sentinel to branch on.
    const agent = agents[slotIndex] ?? null;
    writeSlotVariables(spline, slotNumber, agent);
  }

  // Drives the radar sweep contact count. Always written, even when zero,
  // so the scene UI never displays a stale count from a previous session.
  spline.setVariable(VARIABLE_NAME_GLOBAL_COUNT, visibleAgentCount);
}
