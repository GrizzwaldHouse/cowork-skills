// phase-pill.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Factory function that produces the HTML string for a single phase pill
//   in the phase strip. Used by render.js renderPhaseStrip().
//   Phase pills use inline styles for all pill-specific styling so there is no
//   dependency on a separate CSS class — only the strip container layout comes
//   from layout.css. All user-supplied strings go through escHtml.

'use strict';

// _escHtml — local XSS-safe HTML escaper used before window.escHtml is defined.
// Purpose: phase-pill.js loads before render.js so window.escHtml does not exist yet.
//   This local copy provides identical escaping. render.js later sets window.escHtml.
// Params:
//   str (any) — value to escape; coerced to string
// Returns: string — str with HTML special characters replaced by entities
function _escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// _esc — resolves the best available escHtml function at call time.
// Purpose: Prefer window.escHtml when available (set by render.js) so future
//   escaping improvements apply here automatically. Falls back to local _escHtml.
// Params:
//   str (any) — value to escape
// Returns: string — HTML-escaped string
function _esc(str) {
  const escFn = (typeof window !== 'undefined' && typeof window.escHtml === 'function')
    ? window.escHtml
    : _escHtml;
  return escFn(str);
}

// _pillStyles — computes the inline style string for a phase pill based on status.
// Purpose: Encapsulates all pill-specific visual styling so there is no external
//   CSS dependency. Uses CSS custom properties from variables.css so the pill
//   stays in sync with the design token system.
// Params:
//   status (string) — one of 'active' | 'completed' | 'pending'
// Returns: string — CSS inline style attribute value
// Notes: Opacity-tinted background + matching border per status.
//   active    → accent purple  (var(--accent))  at 20% opacity
//   completed → accent teal    (var(--accent2)) at 15% opacity
//   pending   → surface glass  (var(--surface)) with standard border
function _pillStyles(status) {
  const base = [
    'display:inline-flex',
    'flex-direction:column',
    'align-items:center',
    'gap:4px',
    'padding:6px 14px',
    'border-radius:var(--radius-sm)',
    'font-size:11px',
    'font-weight:600',
    'white-space:nowrap',
    'border-width:1px',
    'border-style:solid',
    'transition:background 0.2s ease',
  ];

  if (status === 'active') {
    base.push('background:rgba(108,99,255,0.20)');
    base.push('border-color:var(--accent)');
    base.push('color:var(--accent)');
  } else if (status === 'completed') {
    base.push('background:rgba(0,212,170,0.15)');
    base.push('border-color:var(--accent2)');
    base.push('color:var(--accent2)');
  } else {
    // pending
    base.push('background:var(--surface)');
    base.push('border-color:var(--border)');
    base.push('color:var(--text-muted)');
  }

  return base.join(';');
}

// _miniProgressBar — returns an inline SVG-less mini progress bar for active phases.
// Purpose: Visually communicates in-progress phase completion without requiring a
//   separate component or CSS class. Only rendered when status is 'active'.
// Params:
//   progress (number) — 0-100 completion percentage for this phase
// Returns: string — HTML for a slim progress bar; empty string when not applicable
// Notes: Uses inline styles only; height 2px to be unobtrusive inside the pill.
function _miniProgressBar(progress) {
  const pct = Math.min(100, Math.max(0, Number(progress) || 0));
  return `<div style="width:100%;height:2px;background:var(--border);border-radius:1px;overflow:hidden;">
    <div style="height:100%;width:${pct}%;background:var(--accent);border-radius:1px;transition:width 0.4s ease;"></div>
  </div>`;
}

// phasePill — builds the HTML string for a single phase pill element.
// Purpose: Produces a self-contained pill fragment that render.js concatenates
//   into #phase-strip. Active phases show a name label plus a mini progress bar.
//   Completed and pending phases show the name only.
// Params:
//   phase        (Object) — phase data:
//     name     (string) — display label for this phase
//     status   (string) — 'pending' | 'active' | 'completed'
//     progress (number) — 0-100 completion percentage (used only when active)
//   index        (number) — 0-based position in the phases array (available for
//                           future use, e.g. numbering pills or aria labels)
//   currentPhase (number) — 0-based index of the currently active phase
//                           (available for additional active-phase logic if needed)
// Returns: string — HTML markup for one phase pill span element
// Notes: All inline styles come from _pillStyles() + _miniProgressBar().
//   No CSS class dependencies beyond what the parent strip container provides.
function phasePill(phase, index, currentPhase) {
  const styles = _pillStyles(phase.status);
  const progressBar = phase.status === 'active' ? _miniProgressBar(phase.progress) : '';

  return `<span style="${styles}" data-phase-index="${index}">
  ${_esc(phase.name)}
  ${progressBar}
</span>`;
}

// Export on window so render.js can call window.phasePill() after this script loads.
window.phasePill = phasePill;
