# models.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Pydantic v2 models for every cross-process state shape used by
#          the AgenticOS Command Center. These are the only types allowed
#          on the wire (WebSocket frames, REST request bodies, JSON state
#          files); never serialise raw dicts in production code paths.

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerations
#
# Pydantic v2 accepts either the enum member or its string value during
# validation, which lets sub-agents write plain strings into agents.json
# while the server still has type-safe access to the same set.
# ---------------------------------------------------------------------------

class AgentStatus(str, Enum):
    """Lifecycle state of a single agent."""

    # Agent is actively executing its current stage.
    ACTIVE = "active"

    # Agent has paused at a gate and is waiting for human approval.
    WAITING_APPROVAL = "waiting_approval"

    # Agent is waiting for an independent reviewer agent to finish.
    WAITING_REVIEW = "waiting_review"

    # Agent has finished all stages successfully; terminal state.
    COMPLETE = "complete"

    # Agent encountered an unrecoverable error; error_msg is populated.
    ERROR = "error"


class AgentDomain(str, Enum):
    """Discipline tag used by the UI to colour cards and filter views."""

    # Veterans Affairs benefits advisory work.
    VA_ADVISORY = "va-advisory"

    # Game development (Unreal, Unity, gameplay systems).
    GAME_DEV = "game-dev"

    # General software engineering.
    SOFTWARE_ENG = "software-eng"

    # 3D content creation and asset pipelines.
    CONTENT_3D = "3d-content"

    # Domain-agnostic catch-all.
    GENERAL = "general"


class ApprovalKind(str, Enum):
    """The three approval decisions a human can record at a gate."""

    # Resume normal execution.
    PROCEED = "proceed"

    # Spawn a research sub-agent before resuming.
    RESEARCH = "research"

    # Spawn an independent reviewer agent before resuming.
    REVIEW = "review"


class ReviewerOutcome(str, Enum):
    """Top-line verdict produced by a reviewer agent."""

    # Output passes review; the parent agent may proceed.
    PASS = "PASS"

    # Output needs changes; reviewer notes describe what.
    REVISE = "REVISE"

    # Output is unrecoverable; do not proceed.
    REJECT = "REJECT"


class TaskStatus(str, Enum):
    """Lifecycle state of one canonical AgenticOS task file."""

    # Ready to be claimed when dependencies are resolved.
    PENDING = "pending"

    # Waiting on one or more dependencies to complete.
    BLOCKED = "blocked"

    # Claimed by a worker with an authoritative lock file.
    IN_PROGRESS = "in_progress"

    # Finished successfully; terminal state.
    COMPLETE = "complete"

    # Failed with context recorded in output; terminal state.
    FAILED = "failed"


# ---------------------------------------------------------------------------
# AgentState — written by sub-agents, broadcast to React clients
# ---------------------------------------------------------------------------

class AgentState(BaseModel):
    """A single agent's published state, one entry per agent in agents.json."""

    # Pydantic v2 config: be strict about extra fields so a typo in an
    # agent's writer surfaces immediately instead of silently dropping data.
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    # Stable identifier for this agent instance, e.g. "AGENT-01".
    agent_id: str = Field(min_length=1)

    # Discipline tag used by the UI for filtering and colour theming.
    domain: AgentDomain

    # One-line human description of what this agent is doing overall.
    task: str = Field(min_length=1)

    # Human-readable label for the current stage.
    stage_label: str = Field(min_length=1)

    # Current stage number, 1-indexed.
    stage: int = Field(ge=1)

    # Total stages this agent expects to execute.
    total_stages: int = Field(ge=1)

    # Overall progress percentage, bounded so a writer cannot send junk.
    progress_pct: int = Field(ge=0, le=100)

    # Current lifecycle status (active, waiting_*, complete, error).
    status: AgentStatus

    # Percentage of the agent's context window consumed so far.
    context_pct_used: int = Field(ge=0, le=100)

    # Optional path (relative to AgenticOS/) to the latest output file.
    output_ref: Optional[str] = None

    # Which approval kind the agent is currently waiting on; None when
    # status is not waiting_approval or waiting_review.
    awaiting: Optional[ApprovalKind] = None

    # Populated only when status == ERROR; describes the failure.
    error_msg: Optional[str] = None

    # agent_id of the parent that spawned this one (research/reviewer).
    spawned_by: Optional[str] = None

    # Verdict written by a reviewer agent; None until review completes.
    reviewer_verdict: Optional[str] = None

    # ISO 8601 UTC timestamp of the last update written by the agent.
    updated_at: datetime

    # ----- Phase 2 expansion (2026-04-29) -----
    # Optional flags written by stuck_detector.py. Default False so that
    # existing writers and existing agents.json files continue to validate
    # without modification. Consumers that don't know about these fields
    # simply ignore them; consumers that do gain stuck/loop visibility.

    # True when last_progress_at is older than STUCK_IDLE_THRESHOLD_S.
    is_stuck: bool = False

    # True when the agent's recent timeline entries are all identical
    # (indicating a tight loop on the same action).
    is_looping: bool = False

    # Timestamp of the most recent forward-progress event for this agent.
    # Set by session_bridge whenever it observes a new mission-state.json
    # mtime or new lines in the agent's replay file.
    last_progress_at: Optional[datetime] = None

    # Count of sub-agent processes spawned by this session. Read from
    # subagent-tracking.json by the bridge.
    sub_agent_count: int = 0

    # Links a bridge-discovered AgentState back to its Cowork session.
    # None for manually-registered agents that never came from discovery.
    discovered_session_id: Optional[str] = None

    @model_validator(mode="after")
    def _stage_within_total(self) -> "AgentState":
        # Cross-field rule: stage cannot exceed total_stages. Caught here
        # rather than at every writer because writers are not trusted.
        if self.stage > self.total_stages:
            raise ValueError(
                f"stage ({self.stage}) must not exceed total_stages "
                f"({self.total_stages}) for agent {self.agent_id}"
            )
        return self


# ---------------------------------------------------------------------------
# ApprovalDecision — request body posted by the React client
# ---------------------------------------------------------------------------

class ApprovalDecision(BaseModel):
    """Body shape for POST /approve/{agent_id}, /research/{agent_id},
    and /review/{agent_id}. Reviewer_context is optional and only
    consulted by /review/{agent_id}."""

    # Forbid extra keys: catches client-side typos at validation time.
    model_config = ConfigDict(extra="forbid")

    # The decision the human selected at the gate.
    decision: ApprovalKind

    # Optional path to the agent output the reviewer should read. Only
    # meaningful for /review/{agent_id}; ignored elsewhere.
    reviewer_context: Optional[str] = None


# ---------------------------------------------------------------------------
# ApprovalQueueEntry — shape persisted to approval_queue.json
# ---------------------------------------------------------------------------

class ApprovalQueueEntry(BaseModel):
    """One row in approval_queue.json. Waiting agents poll this file,
    find their agent_id, read the decision, and clear their entry."""

    model_config = ConfigDict(extra="forbid")

    # Which agent this decision targets.
    agent_id: str = Field(min_length=1)

    # The recorded decision.
    decision: ApprovalKind

    # Path to the output file the reviewer should assess; None for
    # non-review decisions.
    reviewer_context: Optional[str] = None

    # UTC timestamp when the decision was recorded by the server.
    decided_at: datetime


# ---------------------------------------------------------------------------
# ReviewerVerdict -- structured form of the reviewer subprocess output
# ---------------------------------------------------------------------------

class ReviewerVerdict(BaseModel):
    """Structured representation of a reviewer agent's verdict.
    Stored alongside the raw markdown verdict file for programmatic
    consumption by the UI and waiting agents."""

    model_config = ConfigDict(extra="forbid")

    # The agent whose work was reviewed.
    agent_id: str = Field(min_length=1)

    # Top-line outcome (PASS / REVISE / REJECT).
    outcome: ReviewerOutcome

    # Free-form reviewer notes, taken verbatim from the subprocess output.
    notes: str

    # Path to the file the reviewer assessed, for traceability.
    reviewed_context: str

    # Path to the markdown verdict file written to disk.
    verdict_path: str

    # ISO 8601 UTC timestamp when the verdict was written.
    reviewed_at: datetime


# ---------------------------------------------------------------------------
# Canonical task runtime models -- Hybrid AgenticOS layer
# ---------------------------------------------------------------------------

class AgenticTask(BaseModel):
    """Strict JSON contract for files in agentic-os/tasks."""

    model_config = ConfigDict(extra="forbid")

    # Stable task id. File path is tasks/{id}.json.
    id: str = Field(min_length=1)

    # Operator-readable task title.
    title: str = Field(min_length=1)

    # Current task lifecycle status.
    status: TaskStatus

    # Worker that owns or last owned the task. None before claim.
    assigned_to: Optional[str] = None

    # Task ids that must be complete before this task can run.
    dependencies: list[str] = Field(default_factory=list)

    # Lower numbers are selected first by workers.
    priority: int = Field(ge=0)

    # Mirrors the authoritative lock owner while in_progress.
    locked_by: Optional[str] = None

    # Creation and last-update timestamps.
    created_at: datetime
    updated_at: datetime

    # Meaningful progress checkpoints written by the owning worker.
    checkpoints: list[dict[str, Any]] = Field(default_factory=list)

    # Final output payload or error context.
    output: Optional[Any] = None


class TaskLock(BaseModel):
    """Authoritative ownership file in agentic-os/locks."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    created_at: datetime


class TaskTransitionEvent(BaseModel):
    """Structured form of a task runtime log event."""

    model_config = ConfigDict(extra="forbid")

    task_id: Optional[str] = None
    event: str = Field(min_length=1)
    agent_id: Optional[str] = None
    message: str = Field(min_length=1)
    created_at: datetime


class TaskSnapshot(BaseModel):
    """Dashboard/tool snapshot of tasks plus active locks."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    tasks: list[AgenticTask]
    locks: list[TaskLock]


class TerminalWindow(BaseModel):
    """Visible Windows terminal window exposed to the operator panel."""

    model_config = ConfigDict(extra="forbid")

    hwnd: int = Field(ge=1)
    pid: int = Field(ge=1)
    title: str
    process_name: str = Field(min_length=1)
    executable: Optional[str] = None
    cwd: Optional[str] = None
    command_line: Optional[str] = None
    is_visible: bool = True
    is_agent_like: bool = False
    detected_at: datetime


class TerminalActionResult(BaseModel):
    """Result returned after a terminal-control command is attempted."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    hwnd: Optional[int] = None
    pid: Optional[int] = None
    message: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# DiscoveredSession -- Phase 2 expansion (2026-04-29)
#
# Read-only translation of a single mission-state.json on disk into a
# typed view that session_bridge.py can map to AgentState. Never written
# back to a session directory. Path objects are allowed because every
# consumer is in-process and serialization happens through a separate
# AgentState payload.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# WorkflowEvent -- one-way push from the autonomous-workflow skill
# ---------------------------------------------------------------------------

class WorkflowEvent(BaseModel):
    """Lifecycle event posted by the autonomous-workflow skill via POST /events.

    Extra fields (phase, task, reason, etc.) are accepted so the skill can
    attach context-specific keys without a schema change on the server side.
    """

    # Allow extra keys: the skill may attach phase, task, reason, etc.
    model_config = ConfigDict(extra="allow")

    # Short machine-readable event name, e.g. "workflow.started".
    event: str = Field(min_length=1)

    # Stable identifier for the originating workflow run.
    workflow_id: str = Field(min_length=1)

    # ISO 8601 UTC timestamp produced by the skill at emit time.
    timestamp: str = Field(min_length=1)


class DiscoveredSession(BaseModel):
    """One Cowork session discovered on disk by session_discovery.py.

    Read-only view of mission-state.json plus filesystem metadata. The
    bridge translates each instance into an AgentState before any data
    leaves the process; this model is internal and never serialized to
    agents.json or the WebSocket.
    """

    # Allow Path on the model. Permitted because instances live entirely
    # in-process; nothing serializes them through state_store.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Cowork session id (the directory name under the plugin dir).
    session_id: str = Field(min_length=1)

    # Plugin id the session belongs to (the immediate parent directory
    # under COWORK_SESSIONS_ROOT). Useful for filtering by tooling.
    plugin_id: str = Field(min_length=1)

    # Mission objective string read from mission-state.json. Falls back
    # to a placeholder if the JSON omits an explicit objective field.
    objective: str

    # Status string verbatim from mission-state.json. Cowork uses values
    # like "in_progress", "complete", etc.; we do not coerce so a future
    # status added by Cowork still flows through unchanged.
    status: str

    # Most recent activity timestamp. Computed from mission-state.json
    # mtime, not from any field inside the file, so an idle session
    # cannot lie about being active.
    last_active_at: datetime

    # Absolute path to the mission-state.json this session was parsed from.
    mission_state_path: Path

    # Output directory for this session, when one is referenced from
    # mission-state.json. Used by the terminal stream endpoint to locate
    # the agent-replay file; None when the session has not produced output.
    output_dir: Optional[Path] = None

    # Number of live claude.exe / claude processes whose cwd is under the
    # plugin's directory tree. Counted by psutil at scan time.
    sub_agent_count: int = 0

    # Last few entries from the timeline array in mission-state.json.
    # Bounded by config (LOOP_WINDOW_SIZE) so the bridge can detect a
    # loop without dragging the entire history into memory.
    timeline_tail: list[dict[str, Any]] = Field(default_factory=list)
