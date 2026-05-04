// agent-card.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Factory function that produces the HTML string for a single agent card.
//   Used by render.js renderAgents() to build the agent panel DOM.
//   All user-supplied strings are passed through escHtml() to prevent XSS.
//   Exports window.agentCard for consumption by render.js.

'use strict';

// _escHtml — local XSS-safe HTML escaper for use before window.escHtml is defined.
// Purpose: Component factory files load before render.js in index.html, so
//   window.escHtml is not yet available at parse time. This local copy provides
//   the same escaping behaviour. render.js will later set window.escHtml to its
//   own implementation. Both implementations are identical in behaviour.
// Params:
//   str (any) — value to escape; coerced to string if not already
// Returns: string — str with &, <, >, ", and ' replaced by HTML entities
// Notes: Called on every user-controlled field before insertion into innerHTML.
function _escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// _esc — resolves the best available escHtml function at call time.
// Purpose: Prefer window.escHtml (set by render.js) when available so that
//   any future improvements to escaping apply everywhere. Falls back to the
//   local _escHtml so the component works even when loaded standalone.
// Params:
//   str (any) — value to escape
// Returns: string — HTML-escaped string
// Notes: Called inline inside template literals rather than calling _escHtml
//   directly, so the delegation to window.escHtml is always current.
function _esc(str) {
  const escFn = (typeof window !== 'undefined' && typeof window.escHtml === 'function')
    ? window.escHtml
    : _escHtml;
  return escFn(str);
}

// agentCard — builds the HTML string for a single agent row card.
// Purpose: Produces a fully self-contained card fragment that render.js can
//   concatenate into #agent-panel without additional DOM manipulation per card.
//   The approve button is conditionally rendered only when the agent has a
//   pending action awaiting user confirmation.
// Params:
//   agent (Object) — agent data object with the following shape:
//     id           (string)      — stable unique agent identifier
//     name         (string)      — human-readable display name
//     status       (string)      — one of: 'idle' | 'running' | 'blocked' | 'done' | 'error'
//     task         (string)      — current task description
//     progress     (number)      — 0-100 task completion percentage
//     pendingAction (string|null) — action label when waiting for user approval; null otherwise
// Returns: string — HTML markup string for one .agent-card element
// Notes: CSS classes reference panels.css definitions (.agent-card, .agent-header,
//   .status-dot, .agent-name, .agent-task, .progress-bar-wrap, .progress-bar-fill,
//   .agent-actions, .btn-approve). The approve button carries data-agent-id and
//   data-action attributes consumed by render.js event delegation.
function agentCard(agent) {
  // Build the approve button HTML only when the agent has a pending action.
  // Keeping this as a separate variable keeps the main template readable.
  const approveBtn = agent.pendingAction
    ? `<div class="agent-actions">
        <button
          class="btn-approve"
          data-agent-id="${_esc(agent.id)}"
          data-action="${_esc(agent.pendingAction)}"
        >Approve: ${_esc(agent.pendingAction)}</button>
      </div>`
    : '';

  // Clamp progress to 0-100 so a bad value never produces an invalid CSS width.
  const pct = Math.min(100, Math.max(0, Number(agent.progress) || 0));

  return `<div class="agent-card fade-in" data-agent-id="${_esc(agent.id)}">
  <div class="agent-header">
    <span class="status-dot ${_esc(agent.status)}"></span>
    <span class="agent-name">${_esc(agent.name)}</span>
  </div>
  <div class="agent-task">${_esc(agent.task)}</div>
  <div class="progress-bar-wrap">
    <div class="progress-bar-fill" style="width:${pct}%"></div>
  </div>
  ${approveBtn}
</div>`;
}

// Export on window so render.js can call window.agentCard() after this script loads.
window.agentCard = agentCard;
