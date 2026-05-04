// actions.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: User action handlers for the Agentic OS dashboard renderer.
//   Defines window.AgentActions — the object render.js calls when the user
//   interacts with agent cards (approve) or the tool-approval overlay (approve/reject).
//   All actions go through the IPC bridge (window.dashboard) to the main process
//   and also apply optimistic local state updates via window.AgentState so the UI
//   responds immediately without waiting for the IPC round-trip to complete.

'use strict';

// onApprove — handles user approval of a pending agent action.
// Purpose: Called by render.js event delegation when the user clicks an "Approve"
//   button on an agent card OR the approve button inside the tool-approval overlay.
//   Sends the approval to the main process via the 'action:approve' IPC channel,
//   then immediately applies an optimistic local state update so the button
//   disappears and the agent resumes 'running' status without waiting for the
//   main-process broadcast to come back.
//
//   Why optimistic update?
//   IPC round-trips through Electron's async bridge take a few milliseconds.
//   Without a local update the user would see the approve button persist briefly
//   after clicking, which feels broken. Applying the update locally first makes
//   the UI feel instant. The subsequent main-process broadcast (via _broadcastState
//   in ipc-handlers.js) will reconcile any discrepancy — in practice the values
//   should be identical.
//
// Params:
//   agentId (string) — stable unique identifier of the agent whose action is approved
//   action  (string) — the action identifier string that was pending approval
// Returns: void
// Notes: Both window.dashboard and window.AgentState are guarded with typeof checks
//   so this function degrades gracefully if called before those objects are available
//   (e.g. during very early initialisation or in a test harness).
function onApprove(agentId, action) {
  // Forward approval to the main process.
  // dashboard.approveAction invokes the 'action:approve' IPC channel which:
  //   1. Logs the approval to the terminal
  //   2. Clears agent.pendingAction in _state.agents
  //   3. Broadcasts updated state to all renderer windows
  // We do not await the returned Promise — the optimistic update below handles
  // the immediate visual feedback; the broadcast reconciles any delta later.
  if (typeof window.dashboard !== 'undefined' && typeof window.dashboard.approveAction === 'function') {
    window.dashboard.approveAction(agentId, action).catch(function (err) {
      console.error(`[actions] approveAction IPC call failed for agent "${agentId}":`, err);
    });
  } else {
    console.warn('[actions] window.dashboard.approveAction is not available — IPC call skipped');
  }

  // Optimistic local state update: clear pendingAction and set status to 'running'
  // immediately so the approve button disappears and the status dot turns green
  // before the main-process broadcast arrives.
  if (typeof window.AgentState !== 'undefined') {
    window.AgentState.updateAgent(agentId, { pendingAction: null, status: 'running' });
    window.AgentState.addLogEntry('user', `Approved: ${action} for agent ${agentId}`);
  } else {
    console.warn('[actions] window.AgentState is not available — optimistic update skipped');
  }
}

// onReject — handles user rejection of a pending agent tool call.
// Purpose: Called by render.js event delegation when the user clicks the "Reject"
//   button inside the tool-approval overlay.
//   Sends the rejection to the main process via the 'tool:decide' IPC channel
//   (with decision: 'reject'), then immediately applies an optimistic local state
//   update marking the agent as 'blocked' so the UI reflects the rejection at once.
//
//   Why 'tool:decide' rather than a dedicated reject channel?
//   The tool:decide channel is designed as a general decision channel (approve or
//   reject). Using it for rejection keeps the IPC surface minimal and gives the
//   main process the full decision context (agentId + action + decision value)
//   in a single payload, which simplifies future agent-process integration.
//
//   Why set status to 'blocked'?
//   A rejected tool call leaves the agent in a state where it cannot proceed —
//   it is waiting for human intervention (either a retry or a task cancellation).
//   'blocked' accurately communicates this to the user via the status dot colour
//   in panels.css and matches the agent status enum in state.js.
//
// Params:
//   agentId (string) — stable unique identifier of the agent whose action was rejected
//   action  (string) — the action identifier string that was rejected
// Returns: void
// Notes: Both window.dashboard and window.AgentState are guarded for safe degradation.
function onReject(agentId, action) {
  // Forward rejection decision to the main process via tool:decide channel.
  // The main process logs the decision; no _state mutation occurs on the main-process
  // side for MVP — the renderer's optimistic update below is the authoritative UI change.
  if (typeof window.dashboard !== 'undefined' && typeof window.dashboard.decideTool === 'function') {
    window.dashboard.decideTool({ agentId, action, decision: 'reject' }).catch(function (err) {
      console.error(`[actions] decideTool IPC call failed for agent "${agentId}":`, err);
    });
  } else {
    console.warn('[actions] window.dashboard.decideTool is not available — IPC call skipped');
  }

  // Optimistic local state update: clear pendingAction and set status to 'blocked'
  // immediately so the overlay can be dismissed and the agent card reflects the rejection.
  if (typeof window.AgentState !== 'undefined') {
    window.AgentState.updateAgent(agentId, { pendingAction: null, status: 'blocked' });
    window.AgentState.addLogEntry('user', `Rejected: ${action} for agent ${agentId}`);
  } else {
    console.warn('[actions] window.AgentState is not available — optimistic update skipped');
  }
}

// onAdvancePhase — manually advances the dashboard to the next pipeline phase.
// Purpose: Called from phase strip UI (future implementation) or developer tooling
//   when the user manually progresses the pipeline. Delegates to the 'phase:advance'
//   IPC channel in ipc-handlers.js which increments _state.phase (with clamp) and
//   broadcasts the updated state. Also logs the advance action locally for traceability.
// Params: none
// Returns: void
// Notes: No optimistic local update is applied here because the phase index is
//   owned authoritatively by the main process (_state.phase in ipc-handlers.js).
//   The main-process broadcast (via _broadcastState) will update the renderer's
//   phase immediately — the IPC latency (<5ms) is acceptable for a user-initiated
//   action like phase advancement where there is no per-frame visual feedback needed.
function onAdvancePhase() {
  if (typeof window.dashboard !== 'undefined' && typeof window.dashboard.advancePhase === 'function') {
    window.dashboard.advancePhase()
      .then(function (newPhase) {
        console.log(`[actions] Phase advanced to index ${newPhase}`);
      })
      .catch(function (err) {
        console.error('[actions] advancePhase IPC call failed:', err);
      });
  } else {
    console.warn('[actions] window.dashboard.advancePhase is not available — IPC call skipped');
  }

  // Log the user-initiated advance so it appears in the activity log panel.
  if (typeof window.AgentState !== 'undefined') {
    window.AgentState.addLogEntry('user', 'Phase advancement requested');
  }
}

// Export all action handlers on window.AgentActions so render.js event delegation
// (bindAgentPanelEvents, bindToolApprovalEvents) can call them without ES module imports.
// render.js guards all calls with typeof checks, matching the defensive pattern here.
// typeof guard prevents double-registration if actions.js is ever evaluated more than once
// (e.g., Electron reloads or test harnesses that re-inject renderer scripts).
if (typeof window.AgentActions === 'undefined') {
  window.AgentActions = {
    onApprove,
    onReject,
    onAdvancePhase,
  };
}
