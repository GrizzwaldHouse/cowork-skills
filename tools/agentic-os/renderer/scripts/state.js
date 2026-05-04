// state.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Canonical AgentOS state — single source of truth for all renderer state.
//   Mutations only via setState(). Never mutate _state directly.
//   Subscribers are notified synchronously after every mutation.
//   All public methods are exported on window.AgentState.

'use strict';

// _state — the canonical private state object for the entire renderer.
// Shape:
//   phase: number             — 0-based index of the currently active pipeline phase
//   phases: Array<{           — ordered list of pipeline phases
//     name: string,
//     status: 'pending'|'active'|'completed',
//     progress: number        — 0-100 percent complete for this phase
//   }>
//   agents: Array<{           — all agents participating in the current run
//     id: string,             — stable unique identifier (e.g. "researcher", "implementer")
//     name: string,           — human-readable display name
//     status: 'idle'|'running'|'blocked'|'done'|'error',
//     task: string,           — current task description shown under the agent name
//     progress: number,       — 0-100 task-level progress
//     pendingAction: string|null — non-null when agent is waiting for user approval
//   }>
//   log: Array<{              — bounded activity log (max 200 entries)
//     ts: string,             — ISO 8601 timestamp
//     type: 'user'|'agent'|'warn'|'err',
//     message: string
//   }>
//   toolApproval: {           — populated when an agent requests permission for a tool call
//     agentId: string,
//     action: string,
//     description: string
//   } | null
//   overallProgress: number   — 0-100 computed average across all phase progress values
const _state = {
  phase: 0,
  phases: [],
  agents: [],
  log: [],
  toolApproval: null,
  overallProgress: 0,
};

// _subscribers — array of listener functions registered via subscribe().
// Each function receives a deep copy of state after every mutation.
// Private to this module — never exposed externally.
const _subscribers = [];

// _LOG_CAP — maximum number of log entries retained in _state.log.
// Oldest entries are dropped when this limit is exceeded.
// Kept as a named constant so it is easy to tune without hunting magic numbers.
const _LOG_CAP = 200;

// getState — returns a deep copy of the canonical state.
// Purpose: Prevents callers from mutating internal state by reference.
//   Always use this instead of accessing _state directly.
// Params: none
// Returns: Object — deep copy of _state with all current values
// Notes: Uses JSON round-trip which is safe because state contains only
//   JSON-serialisable primitives, arrays, and plain objects. No Date objects,
//   functions, or circular references exist in _state.
function getState() {
  return JSON.parse(JSON.stringify(_state));
}

// setState — merges a partial object into _state and notifies all subscribers.
// Purpose: The only permitted mutation pathway. Enforces single-source-of-truth
//   discipline by routing all writes through one function.
// Params:
//   partial (Object) — any subset of _state keys with new values.
//     Top-level keys are merged shallowly (Object.assign behaviour).
//     Nested arrays/objects are replaced, not deep-merged.
// Returns: void
// Notes: Calls _notifySubscribers() synchronously after the merge.
//   Callers that need to batch multiple updates should call setState() once
//   with all changed keys rather than calling it multiple times.
function setState(partial) {
  Object.assign(_state, partial);
  _notifySubscribers();
}

// subscribe — registers a callback to receive state updates.
// Purpose: Allows renderer modules (render.js, ipc.js, etc.) to react to
//   state changes without polling or coupling to setState() directly.
// Params:
//   fn (Function) — called with a deep copy of _state after every mutation.
//     Signature: fn(state) => void
// Returns: Function — unsubscribe function. Call it to stop receiving updates.
// Notes: The returned unsubscribe function is idempotent — calling it multiple
//   times is safe (splice on a non-present index is a no-op).
function subscribe(fn) {
  _subscribers.push(fn);

  // Return a closure that removes this specific subscriber from the array.
  // Uses indexOf + splice rather than filtering to a new array so that
  // other subscribers are not disrupted mid-notification loop.
  return function unsubscribe() {
    const idx = _subscribers.indexOf(fn);
    if (idx !== -1) {
      _subscribers.splice(idx, 1);
    }
  };
}

// _notifySubscribers — internal function that calls every registered subscriber.
// Purpose: Centralise the notification dispatch so setState, addLogEntry,
//   updateAgent, setPhaseProgress, and recalcOverallProgress all use
//   the same code path.
// Params: none
// Returns: void
// Notes: Never throws — individual subscriber errors are caught and logged to
//   console.error so a broken subscriber cannot prevent other subscribers from
//   receiving updates. Passes a deep copy so subscribers cannot corrupt _state.
function _notifySubscribers() {
  const snapshot = getState();
  for (const fn of _subscribers) {
    try {
      fn(snapshot);
    } catch (err) {
      // Log but do not rethrow — one broken subscriber must not silence others.
      console.error('[AgentState] Subscriber threw an error:', err);
    }
  }
}

// addLogEntry — appends a new entry to _state.log and enforces the 200-entry cap.
// Purpose: Centralised log append with automatic overflow protection.
//   Always call this instead of pushing to _state.log directly.
// Params:
//   type    (string) — one of 'user' | 'agent' | 'warn' | 'err'
//   message (string) — human-readable log line
// Returns: void
// Notes: If the log grows beyond _LOG_CAP after the push, the oldest entry
//   (index 0) is removed with shift(). This is O(n) but the log is bounded
//   so it remains negligible. Calls _notifySubscribers() once after the mutation.
function addLogEntry(type, message) {
  _state.log.push({
    ts: new Date().toISOString(),
    type,
    message,
  });

  // Trim oldest entries when the cap is exceeded.
  while (_state.log.length > _LOG_CAP) {
    _state.log.shift();
  }

  _notifySubscribers();
}

// updateAgent — finds an agent by id and merges a partial update into it.
// Purpose: Targeted agent mutations without replacing the entire agents array.
//   Useful for incremental progress updates and status transitions.
// Params:
//   id      (string) — the stable agent identifier (matches agent.id)
//   partial (Object) — subset of agent keys to update (e.g. { status: 'done', progress: 100 })
// Returns: void
// Notes: No-ops silently if no agent with the given id exists.
//   Shallow-merges the partial so nested objects are replaced, not deep-merged.
//   Calls _notifySubscribers() only when a matching agent is found.
function updateAgent(id, partial) {
  const agent = _state.agents.find(a => a.id === id);
  if (!agent) {
    // Agent not found — no-op. Avoids throwing on race conditions where
    // an update arrives before the agent list has been populated.
    return;
  }
  Object.assign(agent, partial);
  _notifySubscribers();
}

// setPhaseProgress — updates the progress value for a specific phase by index.
// Purpose: Allows the extraction pipeline to report incremental phase completion
//   without replacing the entire phases array.
// Params:
//   phaseIndex (number) — 0-based index into _state.phases
//   progress   (number) — 0-100 completion percentage for this phase
// Returns: void
// Notes: No-ops silently if phaseIndex is out of bounds.
//   Does NOT automatically call recalcOverallProgress() — callers should do
//   that explicitly when they want the ring widget to update, to allow batching
//   multiple phase updates before triggering a recompute.
function setPhaseProgress(phaseIndex, progress) {
  if (!_state.phases[phaseIndex]) {
    // Phase index out of bounds — no-op.
    return;
  }
  _state.phases[phaseIndex].progress = progress;
  _notifySubscribers();
}

// recalcOverallProgress — recomputes overallProgress as the mean of all phase progress values.
// Purpose: Keeps the progress ring widget in sync after phase progress mutations.
//   Call this after setPhaseProgress() or any batch of phase updates.
// Params: none
// Returns: void
// Notes: If phases is empty, overallProgress is set to 0 to avoid NaN.
//   Sets _state.overallProgress directly then calls _notifySubscribers().
function recalcOverallProgress() {
  if (_state.phases.length === 0) {
    _state.overallProgress = 0;
    _notifySubscribers();
    return;
  }

  const sum = _state.phases.reduce((acc, p) => acc + (p.progress || 0), 0);
  _state.overallProgress = Math.round(sum / _state.phases.length);
  _notifySubscribers();
}

// Export the public API on window.AgentState so all renderer scripts can access
// the state without ES module imports (renderer loads scripts via <script> tags).
window.AgentState = {
  getState,
  setState,
  subscribe,
  addLogEntry,
  updateAgent,
  setPhaseProgress,
  recalcOverallProgress,
};
