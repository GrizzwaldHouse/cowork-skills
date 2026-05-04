// log-entry.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Factory function for a single activity log entry HTML string.
//   Used by render.js renderLog() to populate the #log-container panel.
//   Entry type maps to CSS colour classes defined in panels.css.
//   All user-supplied strings go through escHtml to prevent XSS.

'use strict';

// _escHtml — local XSS-safe HTML escaper used before window.escHtml is defined.
// Purpose: log-entry.js loads before render.js so window.escHtml does not exist yet.
//   This local copy provides identical escaping behaviour.
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
// Purpose: Prefer window.escHtml (set by render.js) when available so future
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

// _extractHhMmSs — extracts HH:MM:SS from an ISO 8601 timestamp string.
// Purpose: Log entries show only the time portion (not the full date) to keep
//   the log compact. The time is extracted from the ISO string directly to
//   avoid locale-dependent Date formatting that could produce inconsistent output.
// Params:
//   isoString (string) — ISO 8601 timestamp, e.g. "2026-04-30T14:23:07.123Z"
// Returns: string — "HH:MM:SS" extracted from the T-separated time segment,
//   or "??:??:??" if the string does not match the expected format.
// Notes: Slices characters 11-19 from the ISO string (after the 'T' separator)
//   which is always "HH:MM:SS" regardless of timezone suffix format.
function _extractHhMmSs(isoString) {
  if (typeof isoString === 'string' && isoString.length >= 19) {
    // ISO format: "2026-04-30T14:23:07.123Z"
    //              0123456789012345678
    // Characters 11-18 are always HH:MM:SS.
    return isoString.slice(11, 19);
  }
  return '??:??:??';
}

// logEntry — builds the HTML string for a single activity log line.
// Purpose: Produces a self-contained log row fragment that render.js concatenates
//   into #log-container. The CSS type class (user, agent, warn, err) maps to
//   colour rules in panels.css without requiring any additional logic here.
// Params:
//   entry (Object) — log entry data with the following shape:
//     ts      (string) — ISO 8601 timestamp from addLogEntry()
//     type    (string) — 'user' | 'agent' | 'warn' | 'err'
//     message (string) — human-readable log message
// Returns: string — HTML markup for one .log-entry div
// Notes: The timestamp prefix is formatted as "[HH:MM:SS]" with a single
//   space separator before the message. This mirrors traditional syslog/console
//   conventions familiar to developers. Entry type is not escaped separately
//   because it is one of four known values, but _esc() is applied defensively.
function logEntry(entry) {
  const time = _extractHhMmSs(entry.ts);

  return `<div class="log-entry ${_esc(entry.type)}">[${_esc(time)}] ${_esc(entry.message)}</div>`;
}

// Export on window so render.js can call window.logEntry() after this script loads.
window.logEntry = logEntry;
