# agent_events.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Typed event definitions for multi-agent communication via EventBus

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass(frozen=True)
class AgentEvent:
    """Base event - all agent events inherit from this."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class FileChangeEvent(AgentEvent):
    """A file change detected by the watcher."""
    file_path: str = ""
    event_type: str = ""  # created, modified, deleted
    project: str = ""


@dataclass(frozen=True)
class SessionDetectedEvent(AgentEvent):
    """A Claude session was detected by SessionObserver."""
    signal: str = ""  # SESSION_START, SESSION_ACTIVE, etc.
    project: str = ""
    artifacts: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillExtractedEvent(AgentEvent):
    """Skills were extracted from session artifacts."""
    skill_id: str = ""
    skill_name: str = ""
    skill_data: dict[str, Any] = field(default_factory=dict)
    source_project: str = ""
    confidence: float = 0.0


@dataclass(frozen=True)
class SkillValidatedEvent(AgentEvent):
    """A skill passed validation with a disposition."""
    skill_id: str = ""
    skill_name: str = ""
    disposition: str = ""  # approved, needs_refactor, needs_review, rejected
    composite_score: float = 0.0
    dimension_scores: dict[str, float] = field(default_factory=dict)
    violations: tuple[str, ...] = ()
    quality_report: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillRefactorRequestedEvent(AgentEvent):
    """A skill needs automated refactoring to meet quality threshold."""
    skill_id: str = ""
    skill_name: str = ""
    current_score: float = 0.0
    target_score: float = 0.80
    dimension_scores: dict[str, float] = field(default_factory=dict)
    violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillImprovedEvent(AgentEvent):
    """A skill was improved by the refactor agent."""
    skill_id: str = ""
    skill_name: str = ""
    previous_score: float = 0.0
    new_score: float = 0.0
    iterations_used: int = 0
    branch_name: str = ""


@dataclass(frozen=True)
class SkillRefactorFailedEvent(AgentEvent):
    """Refactoring failed to improve the skill."""
    skill_id: str = ""
    skill_name: str = ""
    reason: str = ""
    attempts: int = 0
    last_score: float = 0.0


@dataclass(frozen=True)
class SkillSyncedEvent(AgentEvent):
    """A skill was synced/installed to targets."""
    skill_id: str = ""
    skill_name: str = ""
    targets: tuple[str, ...] = ()
    sync_type: str = ""  # install, update, rollback


@dataclass(frozen=True)
class AgentStatusChangedEvent(AgentEvent):
    """An agent changed its operational status."""
    agent_name: str = ""
    previous_status: str = ""
    new_status: str = ""
    detail: str = ""
