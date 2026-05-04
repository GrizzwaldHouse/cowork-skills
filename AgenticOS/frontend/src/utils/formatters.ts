// formatters.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Pure formatting helpers for agent state. Pure so they are
//          trivially testable and side-effect free; React components call
//          them inline without memoization. Kept tiny on purpose; once a
//          formatter grows beyond a few lines it earns its own module.

import type { AgentDomain, AgentStatus } from '@/types/agent';
import {
  CONTEXT_CRIT_PCT,
  CONTEXT_WARN_PCT,
  DOMAIN_LABELS,
  STATUS_LABELS,
} from '@/config';

// ---------------------------------------------------------------------------
// clampPercentage
//
// Server output is bounded by Pydantic, but malformed wire data could
// still arrive (a future server bug, a downgrade attack). Clamp to keep
// the UI bars in their visual containers no matter what.
// ---------------------------------------------------------------------------

export function clampPercentage(value: number): number {
  if (Number.isNaN(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, value));
}

// ---------------------------------------------------------------------------
// formatPercentage
//
// Returns "NN%" with the percentage clamped. Used by progress bars and
// the context meter readouts where the trailing % sign is part of the
// label.
// ---------------------------------------------------------------------------

export function formatPercentage(value: number): string {
  return `${clampPercentage(value)}%`;
}

// ---------------------------------------------------------------------------
// formatStageLabel
//
// "Stage 2/5 · Analyzing CFR Title 38" formatting used in the card
// header. The middle dot (·) is encoded so this file stays free of
// special characters that could be mis-saved on Windows.
// ---------------------------------------------------------------------------

export function formatStageLabel(
  stage: number,
  totalStages: number,
  stageLabel: string
): string {
  return `Stage ${stage}/${totalStages} · ${stageLabel}`;
}

// ---------------------------------------------------------------------------
// formatStatusLabel
//
// Returns the human-readable uppercase label for a status. Falls back to
// the raw status string upper-cased if the table is missing an entry,
// which prevents a UI crash if the server ships a new status before the
// client is updated.
// ---------------------------------------------------------------------------

export function formatStatusLabel(status: AgentStatus): string {
  const fromTable = STATUS_LABELS[status];
  return fromTable !== undefined ? fromTable : status.toUpperCase();
}

// ---------------------------------------------------------------------------
// formatDomainLabel
//
// Same pattern as formatStatusLabel but for domain.
// ---------------------------------------------------------------------------

export function formatDomainLabel(domain: AgentDomain): string {
  const fromTable = DOMAIN_LABELS[domain];
  return fromTable !== undefined ? fromTable : domain.toUpperCase();
}

// ---------------------------------------------------------------------------
// formatTimestamp
//
// Renders an ISO-8601 string as a short HH:MM:SS UTC readout. We avoid
// locale formatting because the dashboard is fundamentally an instrument
// readout; consistency across machines matters more than localization.
// Returns the raw string if parsing fails so the user sees something
// meaningful rather than "Invalid Date".
// ---------------------------------------------------------------------------

export function formatTimestamp(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) {
    return iso;
  }
  // toISOString is deterministic; we slice the time portion only.
  return parsed.toISOString().slice(11, 19);
}

// ---------------------------------------------------------------------------
// resolveContextThreshold
//
// Categorizes a context_pct_used value into a named threshold so callers
// can pick a token color without reaching into config. The thresholds
// themselves still live in src/config.ts; this is just the lookup.
// ---------------------------------------------------------------------------

export type ContextThreshold = 'normal' | 'warn' | 'critical';

export function resolveContextThreshold(pctUsed: number): ContextThreshold {
  const clamped = clampPercentage(pctUsed);
  if (clamped >= CONTEXT_CRIT_PCT) {
    return 'critical';
  }
  if (clamped >= CONTEXT_WARN_PCT) {
    return 'warn';
  }
  return 'normal';
}
