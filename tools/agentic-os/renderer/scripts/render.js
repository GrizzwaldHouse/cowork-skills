// render.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: All DOM render functions for the AgentOS dashboard.
//   Ties AgentState to the DOM. All rendering is done via innerHTML assignment
//   (not append loops) for clean full-diffing on each state update.
//   escHtml() is defined here and exported on window for use by component factories
//   that are loaded before this script but call _esc() lazily at render time.
//   Event delegation for all interactive elements is registered once in initRenderer()
//   rather than per-render so handlers are never duplicated across re-renders.

'use strict';

// ---------------------------------------------------------------------------
// XSS Safety
// ---------------------------------------------------------------------------

// escHtml — escapes all HTML-special characters in a string to prevent XSS.
// Purpose: Must be called on every user-controlled or agent-controlled string
//   before it is inserted into innerHTML. Defined here and exported on
//   window.escHtml so component factory files (agent-card.js, etc.) can use
//   the same implementation via their lazy _esc() resolution.
// Params:
//   str (any) — value to escape; non-strings are coerced with String()
// Returns: string — str with &, <, >, ", and ' replaced by their HTML entities
// Notes: Order matters — & must be replaced first to avoid double-escaping
//   e.g. < → &lt; → &amp;lt; if & were handled after <.
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Export escHtml immediately so component factory scripts that resolved to their
// local fallback on first load will now find window.escHtml on subsequent calls.
window.escHtml = escHtml;

// ---------------------------------------------------------------------------
// DOM element cache — resolved once in initRenderer() to avoid repeated
// getElementById calls on every render cycle.
// ---------------------------------------------------------------------------

// _initialized — guards initRenderer() against double-invocation.
// A second call would add a duplicate AgentState subscriber and re-bind event
// listeners, causing every state change to render twice and every approve/reject
// click to fire twice. Reset is intentionally not exposed — the renderer lives
// for the full page lifetime.
let _initialized = false;

// _els — cached references to all DOM elements that render functions write to.
// Purpose: Centralise element lookups so a typo in an id causes a single clear
//   null-check failure rather than a silent no-op scattered across render functions.
// All values start as null; populated by _cacheDomElements().
const _els = {
  agentPanel: null,
  phaseStrip: null,
  progressRingContainer: null,
  logContainer: null,
  toolApprovalOverlay: null,
  toolApprovalCard: null,
  overallProgressWrap: null,
};

// _cacheDomElements — resolves and stores all required DOM element references.
// Purpose: Called once from initRenderer() after DOMContentLoaded.
//   Separating this from initRenderer() makes the lookup testable in isolation.
// Params: none
// Returns: void
// Notes: Logs a warning for any element that cannot be found so misconfigured
//   HTML is caught at startup rather than silently breaking renders.
function _cacheDomElements() {
  _els.agentPanel            = document.getElementById('agent-panel');
  _els.phaseStrip            = document.getElementById('phase-strip');
  _els.progressRingContainer = document.getElementById('progress-ring-container');
  _els.logContainer          = document.getElementById('log-container');
  _els.toolApprovalOverlay   = document.getElementById('tool-approval-overlay');
  _els.toolApprovalCard      = document.getElementById('tool-approval-card');
  _els.overallProgressWrap   = document.getElementById('overall-progress-wrap');

  for (const [key, el] of Object.entries(_els)) {
    if (!el) {
      console.warn(`[render.js] DOM element not found for key: ${key}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Individual render functions
// ---------------------------------------------------------------------------

// renderAgents — replaces #agent-panel contents with the current agents list.
// Purpose: Full innerHTML replacement on every state update. Because agent cards
//   are small and the list is bounded (typically <10 agents), full replacement
//   is simpler and more reliable than incremental patching.
// Params:
//   agents (Array) — array of agent objects from AgentState.
//     Each object: { id, name, status, task, progress, pendingAction }
// Returns: void
// Notes: Requires window.agentCard (from agent-card.js) to be available.
//   If the element or factory is missing, logs a warning and no-ops.
//   Event delegation for .btn-approve is registered once in initRenderer() —
//   NOT here — so that re-renders never duplicate click handlers.
function renderAgents(agents) {
  if (!_els.agentPanel) { return; }
  if (typeof window.agentCard !== 'function') {
    console.warn('[render.js] window.agentCard is not available');
    return;
  }

  if (!agents || agents.length === 0) {
    _els.agentPanel.innerHTML = `<div style="color:var(--text-muted);font-size:12px;padding:16px;">
      No agents registered yet.
    </div>`;
    return;
  }

  _els.agentPanel.innerHTML = agents.map(a => window.agentCard(a)).join('');
}

// renderPhaseStrip — replaces #phase-strip contents with the current phases list.
// Purpose: Renders the horizontal pill row showing pipeline phase status.
//   Active phase pill includes a mini progress bar; completed and pending do not.
// Params:
//   phases      (Array)  — array of phase objects: { name, status, progress }
//   currentPhase (number) — 0-based index of the currently active phase,
//                           passed through to window.phasePill() for context
// Returns: void
// Notes: Requires window.phasePill (from phase-pill.js) to be available.
function renderPhaseStrip(phases, currentPhase) {
  if (!_els.phaseStrip) { return; }
  if (typeof window.phasePill !== 'function') {
    console.warn('[render.js] window.phasePill is not available');
    return;
  }

  if (!phases || phases.length === 0) {
    _els.phaseStrip.innerHTML = '';
    return;
  }

  _els.phaseStrip.innerHTML = phases
    .map((p, i) => window.phasePill(p, i, currentPhase))
    .join('');
}

// renderOverall — replaces #progress-ring-container contents with the SVG ring.
// Purpose: Updates the overall progress ring whenever overallProgress changes.
//   Also renders a compact text fallback in the titlebar #overall-progress-wrap.
// Params:
//   pct (number) — overall progress 0-100
// Returns: void
// Notes: Requires window.progressRing (from progress-ring.js) to be available.
function renderOverall(pct) {
  if (!_els.progressRingContainer) { return; }
  if (typeof window.progressRing !== 'function') {
    console.warn('[render.js] window.progressRing is not available');
    return;
  }

  _els.progressRingContainer.innerHTML = window.progressRing(pct);

  // Also update the compact titlebar widget so progress is visible even when
  // the right panel is out of view. Uses a simple percentage text pill.
  if (_els.overallProgressWrap) {
    _els.overallProgressWrap.innerHTML = `<span style="
      font-size:11px;
      font-weight:600;
      color:var(--accent2);
      background:rgba(0,212,170,0.12);
      border:1px solid var(--accent2);
      border-radius:var(--radius-sm);
      padding:2px 8px;
      -webkit-app-region:no-drag;
    ">${Math.round(pct)}%</span>`;
  }
}

// renderLog — replaces #log-container contents with the last 50 log entries.
// Purpose: Keeps the activity log panel current. Only the last 50 entries are
//   rendered to keep DOM node count low even when the state log has 200 entries.
//   Scrolls to the bottom after rendering so the latest entry is always visible.
// Params:
//   log (Array) — full log array from AgentState (up to 200 entries)
//     Each entry: { ts, type, message }
// Returns: void
// Notes: Requires window.logEntry (from log-entry.js) to be available.
//   Scroll is set via scrollTop = scrollHeight after innerHTML assignment.
function renderLog(log) {
  if (!_els.logContainer) { return; }
  if (typeof window.logEntry !== 'function') {
    console.warn('[render.js] window.logEntry is not available');
    return;
  }

  if (!log || log.length === 0) {
    _els.logContainer.innerHTML = `<div style="color:var(--text-muted);font-size:11px;">
      No activity yet.
    </div>`;
    return;
  }

  // Slice the last 50 entries — state.log is ordered oldest-first so
  // taking from the end gives the most recent entries.
  const visible = log.slice(-50);
  _els.logContainer.innerHTML = visible.map(e => window.logEntry(e)).join('');

  // Scroll to bottom so the newest entry is always in view.
  _els.logContainer.scrollTop = _els.logContainer.scrollHeight;
}

// renderToolApproval — shows or hides the tool approval overlay modal.
// Purpose: When an agent requests a tool call that requires user confirmation,
//   the overlay is displayed with full context (agent id, action, description)
//   and approve / reject buttons. When the request is resolved, the overlay
//   is hidden by passing null.
// Params:
//   toolApproval (Object|null) — approval request data, or null to hide overlay.
//     Shape when non-null: { agentId: string, action: string, description: string }
// Returns: void
// Notes: Buttons carry data attributes consumed by the delegated click handler
//   registered in initRenderer() on #tool-approval-overlay. The handler calls
//   window.AgentActions.onApprove / onReject.
function renderToolApproval(toolApproval) {
  if (!_els.toolApprovalOverlay || !_els.toolApprovalCard) { return; }

  if (!toolApproval) {
    // No pending approval — hide the overlay.
    _els.toolApprovalOverlay.style.display = 'none';
    _els.toolApprovalCard.innerHTML = '';
    return;
  }

  // Build the approval card content. All agent-provided strings are escaped.
  _els.toolApprovalCard.innerHTML = `
    <div class="tool-approval-title">Tool Call Approval Required</div>
    <div class="tool-approval-body">
      Agent <strong>${escHtml(toolApproval.agentId)}</strong> is requesting permission
      to perform the following action:
    </div>
    <div class="tool-approval-code">${escHtml(toolApproval.action)}</div>
    <div class="tool-approval-body">${escHtml(toolApproval.description)}</div>
    <div class="tool-approval-actions">
      <button
        class="btn-deny"
        data-approval-action="reject"
        data-agent-id="${escHtml(toolApproval.agentId)}"
        data-action="${escHtml(toolApproval.action)}"
      >Reject</button>
      <button
        class="btn-approve"
        data-approval-action="approve"
        data-agent-id="${escHtml(toolApproval.agentId)}"
        data-action="${escHtml(toolApproval.action)}"
      >Approve</button>
    </div>`;

  // Show the overlay after content is populated to avoid a flash of empty modal.
  _els.toolApprovalOverlay.style.display = 'flex';
}

// renderAll — top-level render orchestrator; called on every state update.
// Purpose: Distributes state slices to each sub-render function so no single
//   function has to know about the full state shape. Always called with a
//   full state snapshot from AgentState.getState().
// Params:
//   state (Object) — deep copy of AgentState internal state. Shape:
//     { phase, phases, agents, log, toolApproval, overallProgress }
// Returns: void
// Notes: Sub-renders are independent — a failure in one should not block others.
//   Each sub-render has its own null-guard for its DOM element.
function renderAll(state) {
  renderAgents(state.agents);
  renderPhaseStrip(state.phases, state.phase);
  renderOverall(state.overallProgress);
  renderLog(state.log);
  renderToolApproval(state.toolApproval);
}

// ---------------------------------------------------------------------------
// Event delegation — registered once, never re-registered on re-render
// ---------------------------------------------------------------------------

// _bindAgentPanelEvents — registers a single delegated click listener on #agent-panel.
// Purpose: Handles .btn-approve clicks for all agent cards without binding per-button
//   listeners. Since renderAgents() replaces innerHTML on every update, per-button
//   listeners would be lost on re-render. Event delegation survives innerHTML replacement
//   because the listener is on the persistent parent container.
// Params: none
// Returns: void
// Notes: Calls window.AgentActions.onApprove(agentId, action) if available.
//   If AgentActions is not yet loaded (race during init), logs a warning.
function _bindAgentPanelEvents() {
  if (!_els.agentPanel) { return; }

  _els.agentPanel.addEventListener('click', function _agentPanelClick(e) {
    // Walk up from the click target to find a .btn-approve element.
    const btn = e.target.closest('.btn-approve');
    if (!btn) { return; }

    const agentId = btn.dataset.agentId;
    const action  = btn.dataset.action;

    if (!agentId || !action) {
      console.warn('[render.js] .btn-approve clicked but missing data-agent-id or data-action');
      return;
    }

    if (typeof window.AgentActions === 'object' && typeof window.AgentActions.onApprove === 'function') {
      window.AgentActions.onApprove(agentId, action);
    } else {
      console.warn('[render.js] window.AgentActions.onApprove is not available');
    }
  });
}

// _bindToolApprovalEvents — registers a single delegated click listener on the
//   tool approval overlay for approve and reject button handling.
// Purpose: Approval card HTML is replaced by renderToolApproval() on every
//   approval state change, so per-button listeners would be destroyed on re-render.
//   The overlay element itself is persistent, so one delegated listener suffices.
// Params: none
// Returns: void
// Notes: Routes to window.AgentActions.onApprove or window.AgentActions.onReject
//   based on the data-approval-action attribute of the clicked button.
function _bindToolApprovalEvents() {
  if (!_els.toolApprovalOverlay) { return; }

  _els.toolApprovalOverlay.addEventListener('click', function _overlayClick(e) {
    const btn = e.target.closest('[data-approval-action]');
    if (!btn) { return; }

    const approvalAction = btn.dataset.approvalAction;
    const agentId        = btn.dataset.agentId;
    const action         = btn.dataset.action;

    if (!agentId || !action) {
      console.warn('[render.js] Approval button clicked but missing data attributes');
      return;
    }

    const actions = window.AgentActions;
    if (!actions || typeof actions !== 'object') {
      console.warn('[render.js] window.AgentActions is not available');
      return;
    }

    if (approvalAction === 'approve' && typeof actions.onApprove === 'function') {
      actions.onApprove(agentId, action);
    } else if (approvalAction === 'reject' && typeof actions.onReject === 'function') {
      actions.onReject(agentId, action);
    } else {
      console.warn(`[render.js] Unknown approval action: ${approvalAction}`);
    }
  });
}

// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

// initRenderer — bootstraps the renderer: caches DOM elements, binds all event
//   delegation, subscribes to AgentState, and performs an initial render pass.
// Purpose: Single entry point called from DOMContentLoaded (or equivalent).
//   Ensures all wiring happens in the correct order:
//     1. Resolve DOM element references
//     2. Bind persistent event delegation listeners (once, not per-render)
//     3. Subscribe to AgentState so all future mutations trigger renderAll()
//     4. Render the initial state immediately so the UI is never blank on load
// Params: none
// Returns: void
// Notes: Must be called after DOMContentLoaded so all DOM elements exist.
//   Guarded against double-init — a second call would add a duplicate AgentState
//   subscriber and re-bind event listeners, causing every state change to render
//   twice and every approve/reject click to fire twice.
function initRenderer() {
  // Guard: do nothing if already initialised.
  if (_initialized) { return; }
  _initialized = true;

  // Step 1 — cache all DOM element references.
  _cacheDomElements();

  // Step 2 — bind delegated event listeners once.
  _bindAgentPanelEvents();
  _bindToolApprovalEvents();

  // Step 3 — subscribe to state changes so every mutation triggers a full render.
  // The unsubscribe function is not stored because the renderer lives for the
  // entire page lifetime and never needs to unsubscribe.
  window.AgentState.subscribe(function onStateChange(state) {
    renderAll(state);
  });

  // Step 4 — render the current state immediately so the UI is populated on load
  // even before any IPC messages arrive from the main process.
  renderAll(window.AgentState.getState());
}

// Auto-init on DOMContentLoaded so callers don't need to manually invoke initRenderer().
// initRenderer() is also exported on window for cases where the caller wants
// to control timing (e.g. after injecting initial state from the main process).
if (document.readyState === 'loading') {
  // Document is still parsing — wait for it to finish.
  document.addEventListener('DOMContentLoaded', initRenderer);
} else {
  // Document already parsed (script loaded with defer or after DOM is ready).
  initRenderer();
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

// Export the public surface on window so ipc.js, actions.js, and spline.js
// can call render functions without ES module imports.
window.renderAll      = renderAll;
window.escHtml        = escHtml;
window.initRenderer   = initRenderer;

// Individual render functions exported for targeted updates from ipc.js
// (e.g. updating only the log without triggering a full state re-render).
window.renderAgents       = renderAgents;
window.renderPhaseStrip   = renderPhaseStrip;
window.renderOverall      = renderOverall;
window.renderLog          = renderLog;
window.renderToolApproval = renderToolApproval;
