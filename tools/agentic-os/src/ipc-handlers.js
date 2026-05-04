// ipc-handlers.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Main-process IPC channel handlers for the Agentic OS dashboard.
//   Exports a single register(ipcMain) function called by main.js at startup.
//   Owns the module-level _state object and all state mutation logic.
//   Broadcasts state updates to all renderer windows via 'state:updated' push events
//   so the renderer stays in sync without polling.
//   Delegates session persistence to session-manager.js and skill artifact generation
//   to skill-artifact.js (loaded lazily — swallowed gracefully if not yet written).

'use strict';

const { BrowserWindow } = require('electron');
const sessionManager    = require('./session-manager');

// _state — module-level canonical state object for the main process.
// Purpose: Single source of truth on the main-process side. The renderer mirrors
//   this via IPC push events rather than maintaining its own authoritative copy.
//   Structured to match the renderer AgentState shape so JSON round-trips are clean.
// Shape:
//   phase   (number)         — 0-based index of the currently active pipeline phase
//   phases  (Array<Object>)  — ordered pipeline phase descriptors
//   agents  (Array<Object>)  — all participating agents with status/task/progress
//   log     (Array<Object>)  — bounded activity log (mirrors renderer log)
//   toolApproval (Object|null) — pending tool call awaiting user decision
//   overallProgress (number) — 0-100 computed overall progress
let _state = {};

// _broadcastState — sends 'state:updated' with the current _state to every open window.
// Purpose: After any mutation to _state, all renderer windows must be notified so
//   their AgentState.setState() call brings them in sync. Uses BrowserWindow.getAllWindows()
//   so this works correctly with multi-window setups and survives window re-creation.
// Params: none
// Returns: void
// Notes: Only sends to windows whose webContents have not been destroyed.
//   The isDestroyed() guard prevents Electron from throwing when a window is mid-close.
//   win.webContents.send() is fire-and-forget — the renderer subscribes via
//   window.dashboard.onStateUpdated (preload.js) and calls AgentState.setState on receipt.
function _broadcastState() {
  const windows = BrowserWindow.getAllWindows();
  for (const win of windows) {
    if (win && win.webContents && !win.webContents.isDestroyed()) {
      win.webContents.send('state:updated', _state);
    }
  }
}

// register — registers all IPC channel handlers on the provided ipcMain instance.
// Purpose: Called once by main.js (registerIpcHandlers) after Electron is ready.
//   Separating registration into this module keeps main.js clean and makes the
//   handler logic independently testable. All channels use ipcMain.handle() so
//   they return Promises — renderer calls via ipcRenderer.invoke() and awaits results.
// Params:
//   ipcMain (Electron.IpcMain) — the ipcMain instance from the main process
// Returns: void
// Notes: Registering the same channel twice throws in Electron — this function
//   must only be called once. main.js guards this via registerIpcHandlers().
function register(ipcMain) {

  // -------------------------------------------------------------------------
  // state:read — returns the current state as a JSON string.
  // Purpose: Called by the renderer on startup (ipc.js initIpc) to seed AgentState
  //   with the current main-process state before any push events have arrived.
  //   Returning a JSON string (not the object) matches the renderer expectation in
  //   preload.js: readState() receives whatever ipcMain.handle returns, and ipc.js
  //   calls JSON.parse on the result.
  // Params: none (event only)
  // Returns: string — JSON.stringify of current _state
  // Notes: JSON.stringify produces a fresh serialisation on each call so the renderer
  //   cannot hold a live reference into _state.
  // -------------------------------------------------------------------------
  ipcMain.handle('state:read', function handleStateRead(_event) {
    console.log('[agentic-os] state:read requested');
    return JSON.stringify(_state);
  });

  // -------------------------------------------------------------------------
  // state:write — merges a partial state object into _state and broadcasts.
  // Purpose: Allows the renderer (or any future main-process service) to push
  //   partial state changes that should become authoritative. Useful for seeding
  //   initial agent/phase data from a config file or orchestration script.
  // Params:
  //   partial (Object) — any subset of _state keys with new values.
  //     Merged shallowly via Object.assign — nested arrays/objects are replaced.
  // Returns: void
  // Notes: After merging, _broadcastState() pushes the full updated state back to
  //   all renderer windows so every subscriber sees the change immediately.
  // -------------------------------------------------------------------------
  ipcMain.handle('state:write', function handleStateWrite(_event, partial) {
    if (partial && typeof partial === 'object') {
      Object.assign(_state, partial);
      console.log('[agentic-os] state:write merged partial state');
      _broadcastState();
    } else {
      console.warn('[agentic-os] state:write received non-object payload — ignored');
    }
  });

  // -------------------------------------------------------------------------
  // action:approve — approves a pending agent action and clears its pendingAction.
  // Purpose: Called when the user clicks "Approve" on an agent card or the tool
  //   approval overlay. Logs the approval, finds the agent in _state.agents, clears
  //   its pendingAction field, and broadcasts the updated state so the renderer
  //   re-renders the agent card without the approve button.
  // Params:
  //   payload (Object) — { agentId: string, action: string }
  //     agentId — the stable id of the agent whose action is being approved
  //     action  — the action identifier string that was pending
  // Returns: void
  // Notes: Mutates _state.agents in place (find + Object.assign) to avoid
  //   replacing the entire array and losing any other agent state.
  //   No-ops gracefully if the agent is not found (logs a warning).
  // -------------------------------------------------------------------------
  ipcMain.handle('action:approve', function handleActionApprove(_event, payload) {
    const { agentId, action } = payload || {};
    console.log(`[agentic-os] APPROVED: ${agentId}/${action}`);

    // Update _state.agents: find the agent and clear its pendingAction.
    if (Array.isArray(_state.agents)) {
      const agent = _state.agents.find(a => a.id === agentId);
      if (agent) {
        Object.assign(agent, { pendingAction: null });
        console.log(`[agentic-os] Cleared pendingAction for agent "${agentId}"`);
      } else {
        console.warn(`[agentic-os] action:approve — agent "${agentId}" not found in _state.agents`);
      }
    } else {
      console.warn('[agentic-os] action:approve — _state.agents is not an array');
    }

    _broadcastState();
  });

  // -------------------------------------------------------------------------
  // tool:decide — records a human tool-use decision for a pending agent request.
  // Purpose: Called when the user approves or rejects a tool call from the overlay.
  //   For MVP this is an acknowledgement channel — the decision is logged and
  //   acknowledged. Future implementations will forward the decision to a running
  //   agent process via a separate IPC or native messaging channel.
  // Params:
  //   decision (Object) — tool decision payload. Minimum shape:
  //     { agentId: string, action: string, decision: 'approve'|'reject' }
  //     Additional fields (description, context) are logged as-is.
  // Returns: string — 'acknowledged' so the renderer Promise resolves cleanly
  // Notes: No _state mutation needed for MVP — the renderer handles optimistic
  //   local state via actions.js onApprove / onReject. If the tool:decide channel
  //   is used for rejection (decision === 'reject'), render.js already set the
  //   agent status to 'blocked' before this IPC call returns.
  // -------------------------------------------------------------------------
  ipcMain.handle('tool:decide', function handleToolDecide(_event, decision) {
    const { agentId, action, decision: dec } = decision || {};
    console.log(`[agentic-os] tool:decide — agentId="${agentId}" action="${action}" decision="${dec}"`);
    // Full decision object logged for traceability during development.
    console.log('[agentic-os] tool:decide payload:', JSON.stringify(decision, null, 2));
    return 'acknowledged';
  });

  // -------------------------------------------------------------------------
  // phase:advance — increments _state.phase by 1, clamped to phases array length.
  // Purpose: Allows the user or orchestration logic to manually advance the pipeline
  //   to the next phase. The clamp prevents phase from exceeding the last valid index.
  // Params: none (event only)
  // Returns: number — the new phase index after advancement
  // Notes: If _state.phase is not yet defined, it is initialised to 0 before
  //   incrementing. If _state.phases is defined and non-empty, phase is clamped to
  //   phases.length - 1 so it can never point past the last phase.
  //   _broadcastState() pushes the updated phase to all renderer windows.
  // -------------------------------------------------------------------------
  ipcMain.handle('phase:advance', function handlePhaseAdvance(_event) {
    // Initialise phase to 0 if it has not been set yet.
    if (typeof _state.phase !== 'number') {
      _state.phase = 0;
    }

    const newPhase = _state.phase + 1;

    // Clamp to the last valid index when phases array is available and non-empty.
    if (Array.isArray(_state.phases) && _state.phases.length > 0) {
      _state.phase = Math.min(newPhase, _state.phases.length - 1);
    } else {
      // No phases array — allow free-running increment.
      _state.phase = newPhase;
    }

    console.log(`[agentic-os] phase:advance — new phase index: ${_state.phase}`);
    _broadcastState();
    return _state.phase;
  });

  // -------------------------------------------------------------------------
  // session:start — creates a new session record and persists it.
  // Purpose: Called when an orchestration run begins. Creates a timestamped session
  //   record with 'in-progress' outcome and delegates persistence to session-manager.
  // Params:
  //   payload (Object) — { agentName: string, tasksPlanned: number, skillsUsed: Array<string> }
  //     agentName    — human-readable name of the primary agent for this session
  //     tasksPlanned — number of tasks expected in this session (0 if unknown)
  //     skillsUsed   — list of skill identifiers active for this session
  // Returns: string — the new session's unique id (Date.now().toString())
  // Notes: The id uses Date.now() as a string so it is sortable chronologically
  //   and unique within any realistic single-process execution context.
  //   The returned id must be supplied back to session:end to close the session.
  // -------------------------------------------------------------------------
  ipcMain.handle('session:start', function handleSessionStart(_event, payload) {
    const { agentName, tasksPlanned, skillsUsed } = payload || {};

    // Build a unique id using the current epoch millisecond timestamp.
    const id = Date.now().toString();

    const record = {
      id,
      startTime:      new Date().toISOString(),
      endTime:        null,
      agentName:      agentName  || 'unknown',
      tasksCompleted: 0,
      tasksPlanned:   tasksPlanned || 0,
      skillsUsed:     Array.isArray(skillsUsed) ? skillsUsed : [],
      outcome:        'in-progress',
    };

    sessionManager.addSession(record);
    console.log(`[agentic-os] session:start — created session id="${id}" for agent="${record.agentName}"`);

    return id;
  });

  // -------------------------------------------------------------------------
  // session:end — closes an existing session and optionally generates skill artifacts.
  // Purpose: Called when an orchestration run completes (success, partial, or failure).
  //   Stamps the session with endTime, tasksCompleted, and outcome, then attempts
  //   to generate skill artifacts via skill-artifact.js.
  // Params:
  //   payload (Object) — { id: string, tasksCompleted: number, outcome: string }
  //     id             — session id returned by session:start
  //     tasksCompleted — number of tasks that completed successfully
  //     outcome        — one of 'success' | 'partial' | 'failed'
  // Returns: string — 'ok' on success, 'not-found' if the session id was not found
  // Notes: skill-artifact.js is required lazily and wrapped in try/catch because
  //   the file does not exist yet at Phase D. Any MODULE_NOT_FOUND or runtime error
  //   is swallowed so a missing artifact module never blocks session closure.
  // -------------------------------------------------------------------------
  ipcMain.handle('session:end', async function handleSessionEnd(_event, payload) {
    const { id, tasksCompleted, outcome } = payload || {};

    const updated = sessionManager.updateSession(id, {
      endTime:        new Date().toISOString(),
      tasksCompleted: typeof tasksCompleted === 'number' ? tasksCompleted : 0,
      outcome:        outcome || 'success',
    });

    if (!updated) {
      console.warn(`[agentic-os] session:end — session id="${id}" not found`);
      return 'not-found';
    }

    console.log(`[agentic-os] session:end — closed session id="${id}" outcome="${updated.outcome}"`);

    // Attempt skill artifact generation. Any error is caught so a broken artifact
    // module never blocks session closure. outputDir sits under data/ alongside
    // sessions.json so all persistent app data lives in one place.
    try {
      const nodePath      = require('node:path');
      const skillArtifact = require('./skill-artifact');
      const outputDir     = nodePath.join(__dirname, '..', 'data', 'artifacts');
      skillArtifact.writeArtifact(updated, outputDir);
      console.log(`[agentic-os] session:end — skill artifact written for session id="${id}"`);
    } catch (artifactErr) {
      if (artifactErr.code === 'MODULE_NOT_FOUND') {
        console.warn('[agentic-os] skill-artifact module not available — artifact generation skipped');
      } else {
        console.error('[agentic-os] skill-artifact.writeArtifact() threw an error:', artifactErr);
      }
    }

    return 'ok';
  });

  console.log('[agentic-os] IPC handlers registered — 7 channels active');
}

// Export the register function so main.js can call register(ipcMain).
module.exports = register;
