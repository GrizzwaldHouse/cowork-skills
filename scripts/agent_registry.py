# agent_registry.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Central registry for agent lifecycle management

from __future__ import annotations
import logging
import threading
from typing import Any

from scripts.agent_protocol import Agent, AgentInfo, AgentStatus

logger = logging.getLogger("agent.registry")


class AgentRegistry:
    """Central registry for managing agent instances.

    Thread-safe storage for agent references. Provides bulk lifecycle
    operations and status queries. Agents are keyed by their unique name.
    """

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Add an agent to the registry. Raises if name already registered."""
        with self._lock:
            if agent.name in self._agents:
                raise ValueError(f"Agent '{agent.name}' is already registered")
            self._agents[agent.name] = agent
            logger.info("Registered agent: %s (%s)", agent.name, agent.agent_type)

    def unregister(self, name: str) -> None:
        """Remove an agent from the registry."""
        with self._lock:
            if name in self._agents:
                del self._agents[name]
                logger.info("Unregistered agent: %s", name)

    def get(self, name: str) -> Agent | None:
        """Retrieve an agent by name, or None if not found."""
        with self._lock:
            return self._agents.get(name)

    def get_all(self) -> list[Agent]:
        """Return all registered agents."""
        with self._lock:
            return list(self._agents.values())

    def get_by_type(self, agent_type: str) -> list[Agent]:
        """Return all agents matching the given type."""
        with self._lock:
            return [a for a in self._agents.values() if a.agent_type == agent_type]

    def get_by_status(self, status: AgentStatus) -> list[Agent]:
        """Return all agents in the given status."""
        with self._lock:
            return [a for a in self._agents.values() if a.status == status]

    def get_all_info(self) -> list[AgentInfo]:
        """Return AgentInfo snapshots for all registered agents."""
        with self._lock:
            return [a.get_info() for a in self._agents.values()]

    def start_all(self) -> list[str]:
        """Start all agents in CONFIGURED or STOPPED status.

        Returns list of agent names that were started.
        """
        started: list[str] = []
        with self._lock:
            agents = list(self._agents.values())
        for agent in agents:
            if agent.status in (AgentStatus.CONFIGURED, AgentStatus.STOPPED):
                try:
                    agent.start()
                    started.append(agent.name)
                except Exception:
                    logger.exception("Failed to start agent: %s", agent.name)
        return started

    def stop_all(self) -> list[str]:
        """Stop all running or paused agents.

        Returns list of agent names that were stopped.
        """
        stopped: list[str] = []
        with self._lock:
            agents = list(self._agents.values())
        for agent in agents:
            if agent.status in (AgentStatus.RUNNING, AgentStatus.PAUSED):
                try:
                    agent.stop()
                    stopped.append(agent.name)
                except Exception:
                    logger.exception("Failed to stop agent: %s", agent.name)
        return stopped

    @property
    def count(self) -> int:
        """Number of registered agents."""
        with self._lock:
            return len(self._agents)
