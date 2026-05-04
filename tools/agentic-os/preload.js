// preload.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Electron preload script for Agentic OS.
//   Runs in the renderer process but with Node/Electron access. Exposes a
//   narrow, typed IPC surface to the renderer via contextBridge — the raw
//   ipcRenderer object is NEVER placed on window. This is the only file that
//   may call ipcRenderer directly.

'use strict';

const { contextBridge, ipcRenderer } = require('electron');

// dashboard — the IPC surface exposed to all renderer scripts as window.dashboard.
// Purpose: Provide a safe, typed API for renderer code to communicate with the
//   main process without ever touching ipcRenderer directly.
// Security: contextBridge copies these functions into an isolated context so
//   renderer scripts cannot reach back through them to access ipcRenderer or
//   any other Node API.
contextBridge.exposeInMainWorld('dashboard', {

  // readState — fetches the current canonical AgentOS state from the main process.
  // Params: none
  // Returns: Promise<object> — the full state object (see state.js for shape)
  // Notes: Invokes the 'state:read' IPC channel handled by ipc-handlers.js.
  readState: () => ipcRenderer.invoke('state:read'),

  // onStateUpdated — subscribes to state-push events from the main process.
  // Purpose: The main process pushes state deltas over 'state:updated' whenever
  //   an agent, session manager, or IPC handler mutates state. This keeps the
  //   renderer in sync without polling.
  // Params: callback (function) — called with the updated state object each time
  //   the main process emits 'state:updated'. Signature: (state: object) => void
  // Returns: void
  // Notes: Removes all prior 'state:updated' listeners before registering the new
  //   one. This prevents listener accumulation if the caller re-registers (e.g.
  //   during a dev-mode reload or future component remount), which would cause
  //   every event to fire all stacked callbacks.
  onStateUpdated: (callback) => {
    ipcRenderer.removeAllListeners('state:updated');
    ipcRenderer.on('state:updated', (_event, data) => callback(data));
  },

  // approveAction — approves a pending agent action awaiting human confirmation.
  // Params: agentId (string) — the id of the agent whose action is being approved
  //         action (string)  — the action identifier to approve
  // Returns: Promise — resolves when the main process acknowledges the approval
  // Notes: Invokes 'action:approve'. The main process forwards the approval to
  //   the session manager which unblocks the waiting agent.
  approveAction: (agentId, action) =>
    ipcRenderer.invoke('action:approve', { agentId, action }),

  // decideTool — submits a human tool-use decision for a pending agent request.
  // Params: decision (object) — the tool decision payload, shape defined by the
  //   tool-approval UI and consumed by ipc-handlers.js
  // Returns: Promise — resolves when the main process records the decision
  // Notes: Invokes 'tool:decide'. Used by the tool-approval overlay in the
  //   right panel (see actions.js onToolDecide).
  decideTool: (decision) => ipcRenderer.invoke('tool:decide', decision),

  // advancePhase — manually advances the dashboard to the next phase.
  // Params: none
  // Returns: Promise — resolves when the main process has updated phase state
  // Notes: Invokes 'phase:advance'. Typically called from the phase strip UI
  //   when the user manually moves the pipeline forward (see actions.js).
  advancePhase: () => ipcRenderer.invoke('phase:advance'),
});
