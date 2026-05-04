// messages.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Discriminated union for WebSocket frames sent by the FastAPI
//          state bus. Two frame kinds are defined: a full snapshot on
//          connection open, and incremental diffs on every state change.
//          The 'type' field is the discriminator; consumers narrow on it.

import type { AgentState } from '@/types/agent';
import {
  MESSAGE_TYPE_SNAPSHOT,
  MESSAGE_TYPE_DIFF,
} from '@/config';

// ---------------------------------------------------------------------------
// SnapshotMessage
//
// Sent immediately after the WebSocket open handshake. Carries the entire
// current set of agents keyed by agent_id, plus a monotonic sequence number
// so the client can detect dropped diffs and request a fresh snapshot.
// ---------------------------------------------------------------------------

export interface SnapshotMessage {
  readonly type: typeof MESSAGE_TYPE_SNAPSHOT;

  // Monotonically increasing sequence number assigned by the server. The
  // client stores this and compares it against incoming diff sequences.
  readonly seq: number;

  // Full set of agents at the moment the snapshot was generated. We model
  // this as Record<agent_id, AgentState> rather than AgentState[] so the
  // hook can build a Map without a separate index pass.
  readonly agents: Readonly<Record<string, AgentState>>;
}

// ---------------------------------------------------------------------------
// DiffMessage
//
// Sent on every state mutation. Three independent buckets: agents added,
// agents updated (full replacement of the AgentState by id), and agent
// ids removed. A single mutation can populate any combination of buckets.
// ---------------------------------------------------------------------------

export interface DiffMessage {
  readonly type: typeof MESSAGE_TYPE_DIFF;

  // Sequence number of this diff. Must equal previous seq + 1; if it does
  // not, the client requests a fresh snapshot to recover.
  readonly seq: number;

  // Agents created since the previous frame. Treated as upserts; a server
  // that sent the id under both added and updated would not be invalid,
  // but it would be wasteful.
  readonly added: Readonly<Record<string, AgentState>>;

  // Agents whose state changed since the previous frame. Always carries
  // the full AgentState, not a partial; this avoids deep-merge ambiguity.
  readonly updated: Readonly<Record<string, AgentState>>;

  // agent_ids that no longer exist (terminal state pruned, parent killed).
  readonly removed: ReadonlyArray<string>;
}

// ---------------------------------------------------------------------------
// WireMessage
//
// Discriminated union of all frame types accepted by the client. Hook
// code switches on `message.type` and the compiler narrows the rest of
// the shape automatically.
// ---------------------------------------------------------------------------

export type WireMessage = SnapshotMessage | DiffMessage;

// ---------------------------------------------------------------------------
// Type guards
//
// Hand-rolled narrowing helpers used after JSON.parse, where TypeScript
// only sees `unknown`. These are pure runtime checks; the type predicate
// return informs the compiler of the narrowed shape.
// ---------------------------------------------------------------------------

// True when the parsed payload is a recognizable SnapshotMessage.
export function isSnapshotMessage(value: unknown): value is SnapshotMessage {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const candidate = value as { type?: unknown };
  return candidate.type === MESSAGE_TYPE_SNAPSHOT;
}

// True when the parsed payload is a recognizable DiffMessage.
export function isDiffMessage(value: unknown): value is DiffMessage {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const candidate = value as { type?: unknown };
  return candidate.type === MESSAGE_TYPE_DIFF;
}
