# agent_base.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Optional composition helper for agents — lifecycle state machine and metrics

from __future__ import annotations
import logging
import threading
from datetime import datetime, timezone
from typing import Any

from scripts.agent_protocol import Agent, AgentInfo, AgentStatus

# Valid state transitions — most restrictive set that allows normal lifecycle
_VALID_TRANSITIONS: dict[AgentStatus, frozenset[AgentStatus]] = {
    AgentStatus.UNINITIALIZED: frozenset({AgentStatus.CONFIGURED, AgentStatus.ERROR}),
    AgentStatus.CONFIGURED: frozenset({AgentStatus.RUNNING, AgentStatus.ERROR}),
    AgentStatus.RUNNING: frozenset({AgentStatus.PAUSED, AgentStatus.STOPPED, AgentStatus.ERROR}),
    AgentStatus.PAUSED: frozenset({AgentStatus.RUNNING, AgentStatus.STOPPED, AgentStatus.ERROR}),
    AgentStatus.STOPPED: frozenset({AgentStatus.CONFIGURED, AgentStatus.ERROR}),
    AgentStatus.ERROR: frozenset({AgentStatus.CONFIGURED, AgentStatus.STOPPED}),
}


class BaseAgent:
    """Optional composition helper providing lifecycle + metrics.

    Wraps the Agent protocol with a validated state machine,
    thread-safe counters, and activity tracking. Subclasses override
    on_configure/on_start/on_stop/on_pause/on_resume for behavior.
    """

    def __init__(self, name: str, agent_type: str) -> None:
        self._name: str = name
        self._agent_type: str = agent_type
        self._status: AgentStatus = AgentStatus.UNINITIALIZED
        self._config: dict[str, Any] = {}
        self._logger: logging.Logger = logging.getLogger(f"agent.{name}")

        # Metrics — guarded by _lock
        self._lock: threading.Lock = threading.Lock()
        self._events_processed: int = 0
        self._events_emitted: int = 0
        self._error_count: int = 0
        self._started_at: str = ""
        self._last_activity: str = ""

    # -- Protocol properties --------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def agent_type(self) -> str:
        return self._agent_type

    @property
    def status(self) -> AgentStatus:
        return self._status

    # -- Lifecycle methods -----------------------------------------------------

    def configure(self, config: dict[str, Any]) -> None:
        self._transition(AgentStatus.CONFIGURED)
        self._config = dict(config)
        self.on_configure(config)
        self._logger.info("Configured with %d keys", len(config))

    def start(self) -> None:
        self._transition(AgentStatus.RUNNING)
        self._started_at = datetime.now(timezone.utc).isoformat()
        self.on_start()
        self._logger.info("Started")

    def stop(self) -> None:
        self._transition(AgentStatus.STOPPED)
        self.on_stop()
        self._logger.info("Stopped")

    def pause(self) -> None:
        self._transition(AgentStatus.PAUSED)
        self.on_pause()
        self._logger.info("Paused")

    def resume(self) -> None:
        self._transition(AgentStatus.RUNNING)
        self.on_resume()
        self._logger.info("Resumed")

    def get_info(self) -> AgentInfo:
        with self._lock:
            uptime = 0.0
            if self._started_at and self._status == AgentStatus.RUNNING:
                started = datetime.fromisoformat(self._started_at)
                uptime = (datetime.now(timezone.utc) - started).total_seconds()
            return AgentInfo(
                name=self._name,
                agent_type=self._agent_type,
                status=self._status,
                events_processed=self._events_processed,
                events_emitted=self._events_emitted,
                error_count=self._error_count,
                last_activity=self._last_activity,
                uptime_seconds=uptime,
            )

    # -- Hooks for subclasses --------------------------------------------------

    def on_configure(self, config: dict[str, Any]) -> None:
        """Override to handle configuration."""

    def on_start(self) -> None:
        """Override to handle start."""

    def on_stop(self) -> None:
        """Override to handle stop."""

    def on_pause(self) -> None:
        """Override to handle pause."""

    def on_resume(self) -> None:
        """Override to handle resume."""

    # -- Metrics helpers -------------------------------------------------------

    def _record_processed(self) -> None:
        with self._lock:
            self._events_processed += 1
            self._last_activity = datetime.now(timezone.utc).isoformat()

    def _record_emitted(self) -> None:
        with self._lock:
            self._events_emitted += 1

    def _record_error(self) -> None:
        with self._lock:
            self._error_count += 1

    def _set_error(self, reason: str) -> None:
        self._record_error()
        self._status = AgentStatus.ERROR
        self._logger.error("Error: %s", reason)

    # -- Internal state machine ------------------------------------------------

    def _transition(self, target: AgentStatus) -> None:
        allowed = _VALID_TRANSITIONS.get(self._status, frozenset())
        if target not in allowed:
            raise RuntimeError(
                f"Agent '{self._name}': invalid transition "
                f"{self._status.value} → {target.value}"
            )
        previous = self._status
        self._status = target
        self._logger.debug("Transition: %s → %s", previous.value, target.value)
