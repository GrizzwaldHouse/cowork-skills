// diffMerge.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Pure functions that fold a SnapshotMessage or DiffMessage into
//          an immutable Map<string, AgentState>. Kept as a free function
//          rather than a hook method so it is trivially testable in
//          isolation and can be reused if a future worker thread ingests
//          frames off the main thread.

import type { AgentState } from '@/types/agent';
import type { DiffMessage, SnapshotMessage } from '@/types/messages';

// ---------------------------------------------------------------------------
// AgentMap
//
// Read-only view of the agent map. We use a plain Map rather than a
// Record because (a) Map iteration order is insertion order, which we
// rely on for stable card ordering, and (b) Map handles arbitrary string
// keys without prototype-pollution concerns.
// ---------------------------------------------------------------------------

export type AgentMap = ReadonlyMap<string, AgentState>;

// ---------------------------------------------------------------------------
// applySnapshot
//
// Returns a brand-new Map populated from the snapshot's agents object.
// The previous map is discarded entirely; snapshot semantics imply the
// server's view is authoritative and any stale entries should drop.
// ---------------------------------------------------------------------------

export function applySnapshot(snapshot: SnapshotMessage): AgentMap {
  // Build a fresh Map. Entries are inserted in the order the server
  // provided them so the UI ordering matches the server's intent.
  const next = new Map<string, AgentState>();
  for (const [agentId, state] of Object.entries(snapshot.agents)) {
    next.set(agentId, state);
  }
  return next;
}

// ---------------------------------------------------------------------------
// applyDiff
//
// Folds a DiffMessage into an existing map. Returns a new Map (never
// mutates the input) so React's reference-equality change detection can
// see the update. Order of operations: removed first (so a renamed agent
// can be re-added cleanly), then added, then updated.
// ---------------------------------------------------------------------------

export function applyDiff(previous: AgentMap, diff: DiffMessage): AgentMap {
  // Short circuit: empty diff returns the same reference. This is a
  // legitimate no-op the server may send to confirm liveness; rebuilding
  // the map would force unnecessary re-renders.
  if (
    diff.removed.length === 0 &&
    Object.keys(diff.added).length === 0 &&
    Object.keys(diff.updated).length === 0
  ) {
    return previous;
  }

  // Copy the previous map. Map's constructor accepts an iterable of
  // entries; previous is itself iterable. The new Map preserves key
  // ordering for any keys we do not touch.
  const next = new Map<string, AgentState>(previous);

  // Removals first. A subsequent add for the same id is allowed and
  // appends at the end of the iteration order, which matches the
  // semantic of "this is a new agent" on the UI.
  for (const agentId of diff.removed) {
    next.delete(agentId);
  }

  // Adds. Set semantics on Map mean re-adding an existing key updates
  // the value but does not change the iteration position. Server should
  // not duplicate ids across added/updated, but we tolerate it.
  for (const [agentId, state] of Object.entries(diff.added)) {
    next.set(agentId, state);
  }

  // Updates. Same set semantics; updates do not reorder.
  for (const [agentId, state] of Object.entries(diff.updated)) {
    next.set(agentId, state);
  }

  return next;
}

// ---------------------------------------------------------------------------
// agentMapToArray
//
// Convenience for components that want a stable array, sorted by agent_id
// for deterministic rendering. The hook keeps the Map for O(1) lookups;
// components that render a grid prefer arrays for keyed mapping.
// ---------------------------------------------------------------------------

export function agentMapToArray(map: AgentMap): AgentState[] {
  // Spread the values into an array, then sort lexicographically by id.
  // Stable order across renders prevents React from unmounting and
  // remounting cards when an unrelated agent updates.
  const list = Array.from(map.values());
  list.sort((left, right) => left.agent_id.localeCompare(right.agent_id));
  return list;
}
