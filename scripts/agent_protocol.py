# agent_protocol.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Agent protocol (structural typing) and status definitions

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class AgentStatus(Enum):
    """Lifecycle states for agents."""
    UNINITIALIZED = "uninitialized"
    CONFIGURED = "configured"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True)
class AgentInfo:
    """Immutable snapshot of agent state."""
    name: str
    agent_type: str
    status: AgentStatus
    events_processed: int = 0
    events_emitted: int = 0
    error_count: int = 0
    last_activity: str = ""
    uptime_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Agent(Protocol):
    """Structural typing protocol for all agents.

    Any class implementing these methods/properties satisfies the protocol
    without explicit inheritance — Python's structural subtyping.
    """

    @property
    def name(self) -> str:
        """Unique agent identifier."""
        ...

    @property
    def agent_type(self) -> str:
        """Category of agent (extractor, validator, refactor, sync)."""
        ...

    @property
    def status(self) -> AgentStatus:
        """Current lifecycle status."""
        ...

    def configure(self, config: dict[str, Any]) -> None:
        """Apply configuration. Transitions UNINITIALIZED → CONFIGURED."""
        ...

    def start(self) -> None:
        """Begin processing. Transitions CONFIGURED/STOPPED → RUNNING."""
        ...

    def stop(self) -> None:
        """Cease processing. Transitions any → STOPPED."""
        ...

    def pause(self) -> None:
        """Temporarily suspend. Transitions RUNNING → PAUSED."""
        ...

    def resume(self) -> None:
        """Resume from pause. Transitions PAUSED → RUNNING."""
        ...

    def get_info(self) -> AgentInfo:
        """Return immutable snapshot of current state."""
        ...
