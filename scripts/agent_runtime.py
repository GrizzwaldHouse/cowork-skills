# agent_runtime.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Top-level runtime orchestrator for the multi-agent system

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any

from scripts.agent_event_bus import EventBus
from scripts.agent_registry import AgentRegistry
from scripts.agent_protocol import AgentInfo, AgentStatus

logger = logging.getLogger("agent.runtime")

_CONFIG_PATH: Path = Path("C:/ClaudeSkills/config/agent_config.json")


class AgentRuntime:
    """Top-level orchestrator for the multi-agent system.

    Manages the lifecycle of all agents: creates EventBus and Registry,
    bootstraps agent instances, configures from agent_config.json, and
    provides start/stop controls.

    Usage:
        runtime = AgentRuntime()
        runtime.bootstrap()
        runtime.start()
        # ... events flow through the pipeline ...
        runtime.stop()
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path: Path = config_path or _CONFIG_PATH
        self._config: dict[str, Any] = {}
        self._event_bus: EventBus = EventBus()
        self._registry: AgentRegistry = AgentRegistry()
        self._bootstrapped: bool = False

    @property
    def event_bus(self) -> EventBus:
        """Public access to the shared event bus for external event injection."""
        return self._event_bus

    @property
    def registry(self) -> AgentRegistry:
        """Public access to the registry for status queries."""
        return self._registry

    @property
    def is_running(self) -> bool:
        """True if any agent is in RUNNING status."""
        return any(
            a.status == AgentStatus.RUNNING for a in self._registry.get_all()
        )

    def bootstrap(self) -> None:
        """Create and configure all agents from config.

        Loads agent_config.json, instantiates all 4 agents, registers
        them, and applies configuration. After bootstrap, agents are
        in CONFIGURED status ready to start.
        """
        if self._bootstrapped:
            logger.warning("Runtime already bootstrapped — skipping")
            return

        self._config = self._load_config()

        # Lazy imports to avoid circular dependencies
        from scripts.agents.extractor_agent import ExtractorAgent
        from scripts.agents.validator_agent import ValidatorAgent
        from scripts.agents.refactor_agent import RefactorAgent
        from scripts.agents.sync_agent import SyncAgent
        from scripts.agents.pruner_agent import PrunerAgent

        # Create agents — each receives the shared EventBus
        agents = [
            ExtractorAgent(self._event_bus),
            ValidatorAgent(self._event_bus),
            RefactorAgent(self._event_bus),
            SyncAgent(self._event_bus),
            PrunerAgent(self._event_bus),
        ]

        # Register and configure each agent
        for agent in agents:
            self._registry.register(agent)
            agent.configure(self._config)
            logger.info(
                "Bootstrapped %s (%s) — status: %s",
                agent.name, agent.agent_type, agent.status.value,
            )

        self._bootstrapped = True
        logger.info(
            "Runtime bootstrapped: %d agents configured", self._registry.count
        )

    def start(self) -> list[str]:
        """Start all configured agents. Returns names of agents started."""
        if not self._bootstrapped:
            raise RuntimeError("Must call bootstrap() before start()")

        started = self._registry.start_all()
        logger.info("Started %d agents: %s", len(started), ", ".join(started))
        return started

    def stop(self) -> list[str]:
        """Stop all running agents. Returns names of agents stopped."""
        stopped = self._registry.stop_all()
        logger.info("Stopped %d agents: %s", len(stopped), ", ".join(stopped))
        return stopped

    def get_status(self) -> list[AgentInfo]:
        """Return status snapshots for all agents."""
        return self._registry.get_all_info()

    def get_status_summary(self) -> str:
        """Human-readable status summary for CLI output."""
        infos = self._registry.get_all_info()
        if not infos:
            return "No agents registered"

        lines = ["Agent System Status", "=" * 40]
        for info in infos:
            lines.append(
                f"  {info.name:<20s} {info.status.value:<12s} "
                f"processed={info.events_processed} "
                f"emitted={info.events_emitted} "
                f"errors={info.error_count}"
            )

        bus_info = f"EventBus: {self._event_bus.handler_count} handlers registered"
        audit = self._event_bus.get_audit_log(limit=5)
        recent = f"Recent events: {len(audit)}"

        lines.append("=" * 40)
        lines.append(bus_info)
        lines.append(recent)
        return "\n".join(lines)

    def inject_event(self, event: Any) -> None:
        """Inject an external event into the bus (for watcher integration)."""
        self._event_bus.publish(event)

    def _load_config(self) -> dict[str, Any]:
        """Load agent_config.json, return empty dict on failure."""
        try:
            if self._config_path.exists():
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                logger.info("Loaded config from %s", self._config_path)
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load agent config: %s", exc)
        return {}
