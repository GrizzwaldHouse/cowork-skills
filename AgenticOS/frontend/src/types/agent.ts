// agent.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: TypeScript mirrors of the Pydantic models in AgenticOS/models.py.
//          AgentState here is the wire shape WebSocket frames carry; the
//          Python class is the canonical schema and any divergence is a
//          bug. Types in this file are imported by hooks, components, and
//          tests; never duplicate them locally.

// ---------------------------------------------------------------------------
// Enumerations
//
// Python AgentStatus / AgentDomain / ApprovalKind use string-valued enums.
// On the wire they appear as their string values, so we model each as a
// string-literal union here. Keep the literals in lockstep with the Python
// enum members.
// ---------------------------------------------------------------------------

// Lifecycle status of a single agent. Mirrors AgenticOS.models.AgentStatus.
export type AgentStatus =
  | 'active'
  | 'waiting_approval'
  | 'waiting_review'
  | 'complete'
  | 'error';

// Discipline tag used by the UI for filtering and color theming. Mirrors
// AgenticOS.models.AgentDomain.
export type AgentDomain =
  | 'va-advisory'
  | 'game-dev'
  | 'software-eng'
  | '3d-content'
  | 'general';

// The three approval decisions a human can post at a gate. Mirrors
// AgenticOS.models.ApprovalKind.
export type ApprovalKind = 'proceed' | 'research' | 'review';

// Reviewer verdict outcome. Mirrors AgenticOS.models.ReviewerOutcome. The
// Python class uses uppercase values intentionally; preserved here.
export type ReviewerOutcome = 'PASS' | 'REVISE' | 'REJECT';

// ---------------------------------------------------------------------------
// AgentState
//
// One-to-one mirror of AgenticOS.models.AgentState. Optional Pydantic
// fields appear here as `field: T | null` rather than `field?: T` because
// the Python serializer emits explicit nulls; the wire shape always has
// the key present. exactOptionalPropertyTypes in tsconfig enforces this.
// ---------------------------------------------------------------------------

export interface AgentState {
  // Stable identifier, used as Map key and URL path segment.
  readonly agent_id: string;

  // Discipline tag drives card accent color and filter chips.
  readonly domain: AgentDomain;

  // Human-readable description of the overall task.
  readonly task: string;

  // Label of the current stage shown above the progress bar.
  readonly stage_label: string;

  // 1-indexed current stage number.
  readonly stage: number;

  // Total stage count this agent expects to execute.
  readonly total_stages: number;

  // Whole-percentage progress through total_stages (0..100).
  readonly progress_pct: number;

  // Lifecycle status; drives buttons, glow, and pill.
  readonly status: AgentStatus;

  // Whole-percentage of the agent's context window already consumed.
  readonly context_pct_used: number;

  // Optional file path the reviewer would read on a review decision.
  readonly output_ref: string | null;

  // Which approval is open right now; null when not at a gate.
  readonly awaiting: ApprovalKind | null;

  // Populated only when status === 'error'.
  readonly error_msg: string | null;

  // agent_id of the parent that spawned this agent (research / review).
  readonly spawned_by: string | null;

  // Reviewer verdict markdown; populated after a reviewer subprocess.
  readonly reviewer_verdict: string | null;

  // ISO 8601 UTC timestamp of the last write by the agent itself.
  readonly updated_at: string;

  // ----- Phase 2 expansion (2026-04-29) -----
  // Optional; default false on the server. Strict typing here mirrors
  // the Pydantic shape: server emits explicit values, not omissions.

  // True when the agent has not made forward progress past the
  // STUCK_IDLE_THRESHOLD_S window. Drives a red pulsing border.
  readonly is_stuck?: boolean;

  // True when the last LOOP_WINDOW_SIZE timeline entries are all the
  // same kind+agent. Drives a 'looping' badge on the card.
  readonly is_looping?: boolean;

  // Last forward-progress timestamp captured by the bridge. Server
  // emits null if no progress has been observed yet.
  readonly last_progress_at?: string | null;

  // Number of sub-agent processes spawned by this session.
  readonly sub_agent_count?: number;

  // Cowork session id this agent was discovered from. Null for
  // manually-registered agents that did not come from discovery.
  readonly discovered_session_id?: string | null;
}

// ---------------------------------------------------------------------------
// ApprovalPayload
//
// Body shape for POST /approve|/research|/review/{agent_id}. Mirrors the
// ApprovalDecision Pydantic model. reviewer_context is a separate optional
// key so that /review can carry the file path the reviewer should read.
// ---------------------------------------------------------------------------

export interface ApprovalPayload {
  readonly decision: ApprovalKind;

  // Only meaningful for /review. Optional because the other two endpoints
  // ignore it. Marked optional rather than `| null` because the server
  // accepts the key being absent (Pydantic default None).
  readonly reviewer_context?: string;
}
