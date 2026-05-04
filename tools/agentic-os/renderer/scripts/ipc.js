// ipc.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Renderer-side IPC initialisation for the Agentic OS dashboard.
//   Reads initial state from main process via window.dashboard.readState(),
//   then subscribes to pushed state updates via window.dashboard.onStateUpdated().
//   Bridges main-process state into AgentState so the renderer stays in sync.
//   Loaded after state.js and render.js in index.html so window.AgentState is
//   guaranteed to be available when initIpc() runs.

'use strict';

// initIpc — async function that seeds renderer state from the main process and
//   subscribes to all future state push events for the lifetime of the window.
// Purpose: Called once on DOMContentLoaded (or immediately if the document is
//   already parsed). Performs two operations:
//     1. One-time pull: calls window.dashboard.readState() to get the full current
//        state from the main process and seeds window.AgentState with it.
//     2. Push subscription: registers an onStateUpdated callback so every future
//        main-process state mutation is automatically reflected in the renderer.
//   This two-step approach handles the race between IPC bridge initialisation and
//   any state mutations that occur between app launch and renderer load.
// Params: none
// Returns: Promise<void> — resolves after the initial state is seeded and the
//   push subscription is registered. Errors are caught and logged so a failure
//   here (e.g. main process not yet ready) degrades gracefully rather than
//   blocking render.js from displaying the initial state.
// Notes: window.dashboard is the contextBridge surface defined in preload.js.
//   window.AgentState is the canonical renderer state defined in state.js.
//   Both must be available before initIpc() is called — load order in index.html
//   (state.js → render.js → ipc.js) guarantees this.
async function initIpc() {
  // Guard: both IPC bridge and AgentState must be available before proceeding.
  // If either is missing, log a warning and return early so the dashboard still
  // renders with its default empty state rather than throwing a runtime error.
  if (typeof window.dashboard === 'undefined') {
    console.warn('[ipc] window.dashboard is not available — IPC bridge degraded. Running without main-process state.');
    return;
  }

  if (typeof window.AgentState === 'undefined') {
    console.warn('[ipc] window.AgentState is not available — cannot seed renderer state. Check load order in index.html.');
    return;
  }

  // Step 1 — Pull: fetch the current canonical state from the main process.
  // dashboard.readState() invokes the 'state:read' IPC channel (ipc-handlers.js)
  // which returns JSON.stringify(_state). Parse it and hand it to AgentState.setState()
  // so the renderer's in-memory state matches the main process from the first frame.
  try {
    const raw = await window.dashboard.readState();

    // readState may return an empty string (before ipc-handlers.js is registered)
    // or a JSON string. Guard against both cases before calling JSON.parse.
    if (typeof raw === 'string' && raw.trim().length > 0) {
      const parsed = JSON.parse(raw);

      // setState merges the parsed object into AgentState so only defined keys
      // are updated — existing renderer defaults for missing keys are preserved.
      window.AgentState.setState(parsed);
      console.log('[ipc] Initial state seeded from main process');
    } else {
      // Main process returned empty state (e.g. _state is {} on first launch).
      // This is normal — the renderer starts with its own defaults from state.js.
      console.log('[ipc] Main process returned empty state — using renderer defaults');
    }
  } catch (pullErr) {
    // IPC call failed — likely the main process is not yet ready or ipc-handlers.js
    // has not been registered. Renderer continues with its default state.
    console.error('[ipc] Failed to pull initial state from main process:', pullErr);
  }

  // Step 2 — Push subscription: register a callback for all future state updates.
  // onStateUpdated registers an ipcRenderer.on listener for 'state:updated' events
  // pushed by _broadcastState() in ipc-handlers.js after every mutation.
  // The callback merges the pushed state into AgentState which in turn notifies
  // all renderer subscribers (including render.js) to re-render.
  //
  // Design note: we do NOT use a polling interval here. The push subscription is
  // the Observer pattern — the main process is the subject, the renderer is the
  // observer. React Query invalidation would be the equivalent in a web context;
  // here the AgentState subscriber chain fulfils the same role.
  try {
    window.dashboard.onStateUpdated(function onPush(state) {
      // Merge the pushed state into AgentState — this triggers _notifySubscribers()
      // which calls render.js renderAll() with the updated snapshot.
      window.AgentState.setState(state);

      // Log the push event so it appears in the activity log panel.
      // Using 'agent' type so it renders with the agent colour in log-entry.js.
      window.AgentState.addLogEntry('agent', 'State updated from main process');
    });

    console.log('[ipc] Push subscription registered via window.dashboard.onStateUpdated');
  } catch (subErr) {
    // Subscription registration failed — renderer will not receive future pushes
    // but the initial state pull (Step 1) still applied correctly.
    console.error('[ipc] Failed to register push subscription:', subErr);
  }

  console.log('[ipc] IPC bridge initialised');
}

// Auto-call initIpc() after the DOM is ready, matching the same pattern used by
// render.js so both modules initialise in a consistent, predictable order.
// initIpc() is async but its return value is not needed here — errors are handled
// internally. The void wrapper suppresses the floating-Promise lint warning.
if (document.readyState === 'loading') {
  // Document is still parsing — defer until DOMContentLoaded fires.
  document.addEventListener('DOMContentLoaded', function () {
    initIpc().catch(function (err) {
      console.error('[ipc] Unhandled error during initIpc():', err);
    });
  });
} else {
  // Document already parsed (script loaded with defer or after body close tag).
  initIpc().catch(function (err) {
    console.error('[ipc] Unhandled error during initIpc():', err);
  });
}

// Export initIpc on window so it can be called manually during testing or from
// a dev-mode console session to re-sync renderer state with the main process.
window.initIpc = initIpc;
