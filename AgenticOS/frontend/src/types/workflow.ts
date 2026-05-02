// workflow.ts
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: TypeScript mirror of WorkflowEvent from AgenticOS/models.py and
//          derived view types consumed by useWorkflowEvents and WorkflowStatusPanel.

// ---------------------------------------------------------------------------
// Wire shape — mirrors WorkflowEvent(extra="allow") from models.py
// ---------------------------------------------------------------------------

export type WorkflowEventKind =
  | 'workflow.started'
  | 'workflow.phase_started'
  | 'workflow.phase_complete'
  | 'workflow.vote_cast'
  | 'workflow.complete'
  | 'workflow.failed';

export type VoteResult = 'PASS' | 'FAIL' | 'BLOCKED';

// Intersection type avoids readonly/index-signature conflict in strict TS.
export type WorkflowEvent = {
  readonly event: WorkflowEventKind;
  readonly workflow_id: string;
  readonly timestamp: string;
  readonly task?: string;
  readonly phase?: string;
  readonly decision?: string;
  readonly result?: VoteResult;
  readonly voters?: readonly string[];
  readonly phases_run?: number;
  readonly reason?: string;
} & Record<string, unknown>;

// ---------------------------------------------------------------------------
// Derived view types — produced by groupWorkflowEvents()
// ---------------------------------------------------------------------------

export type WorkflowTerminalStatus = 'active' | 'complete' | 'failed';

export interface PhaseRecord {
  readonly name: string;
  readonly started: boolean;
  readonly complete: boolean;
  readonly voteResult: VoteResult | null;
}

export interface WorkflowGroup {
  readonly workflowId: string;
  readonly task: string | null;
  readonly events: readonly WorkflowEvent[];
  readonly phases: readonly PhaseRecord[];
  readonly terminalStatus: WorkflowTerminalStatus;
  readonly failureReason: string | null;
  readonly startedAt: string;
  readonly updatedAt: string;
}

// ---------------------------------------------------------------------------
// REST response shape — mirrors GET /workflow-events response body
// ---------------------------------------------------------------------------

export interface WorkflowEventsResponse {
  readonly since: number;
  readonly count: number;
  readonly events: readonly WorkflowEvent[];
}
