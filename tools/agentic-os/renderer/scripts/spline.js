// spline.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Spline 3D background viewer state bridge for the AgentOS dashboard.
//   Pushes live dashboard state variables into the <spline-viewer id="spline-bg">
//   element after every AgentState update so the 3D scene reflects real-time
//   pipeline activity (phase transitions, agent count, alert presence, phase progress).
//   All Spline interactions are fire-and-forget — a Spline failure of any kind
//   must NEVER crash, block, or slow the dashboard. Spline is purely decorative.

'use strict';

// ---------------------------------------------------------------------------
// DOM lookup
// ---------------------------------------------------------------------------

// getSplineViewer — finds the <spline-viewer> element in the DOM.
// Purpose: Centralises the DOM lookup so syncSplineState() does not need
//   to call getElementById on every state update from a cached stale reference.
//   The viewer element may be upgraded asynchronously by the Spline custom element
//   registry, so resolving it fresh each call is safer than caching at module load.
// Params: none
// Returns: HTMLElement | null — the spline-viewer element, or null if not found.
// Notes: Called lazily each time syncSplineState() runs rather than cached,
//   because the element may not exist at module parse time (script is deferred)
//   and because the Spline CDN may fail to register the custom element at all.
function getSplineViewer() {
  return document.getElementById('spline-bg');
}

// ---------------------------------------------------------------------------
// Variable derivation
// ---------------------------------------------------------------------------

// deriveSplineVars — computes the four Spline variable values from current state.
// Purpose: Keeps variable derivation logic in one testable, isolated place,
//   separate from the DOM interaction in syncSplineState(). Having a pure
//   function here means the mapping logic can be verified without a live DOM.
// Params:
//   state (object) — the current AgentOS state snapshot from AgentState.getState().
//     Expected shape: { phase, phases, agents, toolApproval, ... }
// Returns: object — { phase, phaseProgress, agentCount, hasAlert }
//   phase        (string)  — state.phase ?? 'idle'; string key of the active
//                            pipeline phase. Drives 3D scene layer visibility.
//   phaseProgress (number 0-100) — state.phases[phase].progress ?? 0,
//                            clamped to [0,100]. state.js stores progress as
//                            0-100 directly; no multiplication applied.
//   agentCount   (number) — count of agents with status 'running' or 'blocked'.
//                            Blocked agents await user approval and represent
//                            active pipeline load — counted alongside running.
//   hasAlert     (boolean) — true when toolApproval is non-null/undefined,
//                            indicating the tool approval overlay is active.
// Notes: All four variables are always present even when state is a partial
//   object — safe defaults keep the Spline scene free of undefined/NaN.
function deriveSplineVars(state) {
  // phase — raw string key of the active phase, falling back to 'idle'.
  // Passed as-is so Spline can use it for string-based state transitions.
  var phase = state.phase != null ? state.phase : 'idle';

  // phaseProgress — 0-100 progress of the active phase, clamped for safety.
  // state.phases is keyed by phase string (object-map bracket-notation access).
  // state.js stores progress as 0-100 directly (see state.js setPhaseProgress),
  // so no multiplication is applied — clamping guards against out-of-range values
  // from partial state pushes or future refactors.
  var phaseProgress = 0;
  if (state.phases != null && state.phases[phase] != null) {
    var rawProgress = state.phases[phase].progress;
    phaseProgress = typeof rawProgress === 'number' ? rawProgress : 0;
    if (phaseProgress < 0) { phaseProgress = 0; }
    if (phaseProgress > 100) { phaseProgress = 100; }
  }

  // agentCount — number of agents in 'running' or 'blocked' state.
  // Blocked agents are waiting for user approval and represent active pipeline
  // load, so they count toward visual activity level in the Spline scene.
  var agentCount = 0;
  if (Array.isArray(state.agents)) {
    agentCount = state.agents.filter(function (a) {
      return a.status === 'running' || a.status === 'blocked';
    }).length;
  }

  // hasAlert — boolean flag indicating whether the tool approval overlay is active.
  // Uses explicit null/undefined check (not falsy) so legitimate falsy non-null
  // values on toolApproval don't incorrectly suppress the alert.
  var hasAlert = state.toolApproval !== null && state.toolApproval !== undefined;

  return {
    phase: phase,
    phaseProgress: phaseProgress,
    agentCount: agentCount,
    hasAlert: hasAlert,
  };
}

// ---------------------------------------------------------------------------
// State sync
// ---------------------------------------------------------------------------

// syncSplineState — pushes current AgentOS state into the Spline 3D scene.
// Purpose: Called after every state update so the 3D scene reflects live
//   dashboard data (phase transitions, agent activity, alert state).
//   Bridges AgentState → Spline variable API with no coupling in either direction.
// Params:
//   state (object) — the current AgentOS state from AgentState.getState().
//     Must contain: phase, phases, agents, toolApproval.
// Returns: void
// Notes: This function is fire-and-forget — all errors are swallowed silently.
//   A Spline sync failure must NEVER crash or slow the dashboard. The viewer's
//   setVariables() method is async but we do not await it for the same reason:
//   awaiting would require this function to be async, adding a micro-task tick
//   that could delay subsequent synchronous dashboard updates.
//   If the viewer element is not found (e.g. Spline CDN blocked or element id
//   changed), this is a no-op with a single console.debug message — never
//   console.error, because a missing Spline viewer is not a dashboard error.
//   The setVariables availability check guards against the case where the custom
//   element is registered in the DOM but its JS class has not yet been upgraded
//   (e.g. Spline runtime still loading in the background).
function syncSplineState(state) {
  try {
    var viewer = getSplineViewer();

    // Viewer not found — Spline CDN blocked, id mismatch, or element not yet
    // inserted. Log at debug level only — this is expected in offline / test envs.
    if (!viewer) {
      console.debug('[spline] viewer not found — skipping sync');
      return;
    }

    // setVariables is provided by the Spline custom element runtime after the
    // element is fully upgraded. If it is missing, the element is still mounting.
    // The next state update will retry — no action needed here.
    if (typeof viewer.setVariables !== 'function') {
      console.debug('[spline] setVariables not available yet — skipping sync');
      return;
    }

    var vars = deriveSplineVars(state);

    // Fire-and-forget — never await, never catch the returned Promise.
    // Spline sync failure must not block or crash the dashboard.
    viewer.setVariables(vars);
  } catch (e) {
    // Swallow all errors silently — Spline is decorative, not functional.
    // Use console.debug not console.error to keep devtools noise minimal.
    console.debug('[spline] sync error (suppressed):', e.message);
  }
}

// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

// _splineInitialized — module-level guard preventing duplicate AgentState subscriptions.
// Mirrors the _initialized flag in render.js: if initSpline() is called a second time
// (Electron renderer reload, dev-console call, or test harness re-injection) the guard
// returns early instead of registering a second subscriber that would fire syncSplineState
// twice per state mutation.
var _splineInitialized = false;

// initSpline — wires AgentState subscription to push state into Spline on every change.
// Purpose: Called once after DOMContentLoaded. Subscribes to AgentState so every
//   future mutation automatically syncs to the Spline scene without any polling.
//   Follows the Observer pattern used throughout the codebase — AgentState is the
//   subject, initSpline is the observer registration point.
// Params: none
// Returns: void
// Notes: The subscription is permanent — no unsubscribe is needed because the
//   dashboard window lives for the full Electron app lifetime. The returned
//   unsubscribe function from AgentState.subscribe() is intentionally discarded.
//   An immediate sync is performed with the current state so the scene reflects
//   initial dashboard state on load, before any IPC messages arrive from the
//   main process. This mirrors the pattern used by initRenderer() in render.js.
function initSpline() {
  if (_splineInitialized) { return; }
  _splineInitialized = true;

  // Immediate sync with current state on load so the 3D scene is not frozen
  // at its default values during the window between DOM ready and first IPC push.
  syncSplineState(window.AgentState.getState());

  // Subscribe so every future state mutation re-syncs the scene.
  // Callback receives a deep copy of state (guaranteed by AgentState.subscribe
  // contract) so there is no risk of mutating internal state here.
  window.AgentState.subscribe(function onStateChange(state) {
    syncSplineState(state);
  });
}

// ---------------------------------------------------------------------------
// Auto-init
// ---------------------------------------------------------------------------

// Auto-call initSpline() after the DOM is ready, using the same readyState guard
// pattern as render.js and ipc.js so all three modules initialise consistently.
// initSpline() is synchronous so no .catch() wrapper is needed (unlike initIpc).
if (document.readyState === 'loading') {
  // Document is still parsing — defer until DOMContentLoaded fires.
  document.addEventListener('DOMContentLoaded', initSpline);
} else {
  // Document already parsed (script loaded with defer or placed after body close tag).
  initSpline();
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

// Export public surface on window so other renderer scripts and dev-console
// sessions can call syncSplineState() for manual testing or targeted resyncs,
// and initSpline() to re-initialise the subscription after a hot reload.
window.syncSplineState = syncSplineState;
window.initSpline      = initSpline;
