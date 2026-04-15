# agent_coordinator.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Central pipeline orchestrator wiring 4 agents into an event-driven self-improving pipeline

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.agent_event_bus import EventBus
from scripts.agent_events import (
    AgentEvent,
    FileChangeEvent,
    SessionDetectedEvent,
    SkillExtractedEvent,
    SkillValidatedEvent,
    SkillRefactorRequestedEvent,
    SkillImprovedEvent,
    SkillRefactorFailedEvent,
    SkillSyncedEvent,
)
from scripts.agent_registry import AgentRegistry
from scripts.agent_runtime import AgentRuntime

logger = logging.getLogger("agent.coordinator")

_PIPELINE_CONFIG_PATH: Path = Path("C:/ClaudeSkills/config/pipeline_config.json")
_CYCLE_LOG_PATH: Path = Path("C:/ClaudeSkills/data/pipeline_cycles.json")


@dataclass(frozen=True)
class PipelineConfig:
    """Immutable pipeline configuration loaded from pipeline_config.json."""

    auto_extract: bool = True
    auto_refactor: bool = True
    auto_sync: bool = False
    min_quality_score: float = 0.7
    min_reusability_score: float = 0.85
    max_refactor_iterations: int = 10
    feedback_enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        """Create PipelineConfig from a dict, ignoring unknown keys."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    @classmethod
    def load(cls, path: Path | None = None) -> PipelineConfig:
        """Load config from JSON file, falling back to defaults."""
        config_path = path or _PIPELINE_CONFIG_PATH
        try:
            if config_path.exists():
                data = json.loads(config_path.read_text(encoding="utf-8"))
                return cls.from_dict(data)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load pipeline config: %s", exc)
        return cls()


@dataclass
class PipelineCycleResult:
    """Result of a single pipeline cycle (extraction → validation → sync)."""

    cycle_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    skills_extracted: int = 0
    skills_validated: int = 0
    skills_approved: int = 0
    skills_refactored: int = 0
    skills_rejected: int = 0
    skills_synced: int = 0
    refactor_failures: int = 0
    events_processed: int = 0


class AgentCoordinator:
    """Central orchestrator wiring 4 agents into an event-driven pipeline.

    Lifecycle:
    1. Load PipelineConfig from pipeline_config.json
    2. Bootstrap AgentRuntime (creates EventBus, Registry, all 4 agents)
    3. Subscribe to pipeline events for coordination and metrics
    4. Start all agents via Registry
    5. Monitor event flow, collect cycle metrics, feed to FeedbackLoop

    The coordinator does NOT duplicate agent logic — it observes events
    published by agents and maintains pipeline-level state.
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self._config: PipelineConfig = config or PipelineConfig.load()
        self._runtime: AgentRuntime = AgentRuntime()
        self._lock: threading.Lock = threading.Lock()
        self._running: bool = False
        self._current_cycle: PipelineCycleResult | None = None
        self._cycle_history: list[PipelineCycleResult] = []
        self._feedback_loop: Any = None  # Lazy-loaded FeedbackLoop

    @property
    def config(self) -> PipelineConfig:
        """Current pipeline configuration."""
        return self._config

    @property
    def runtime(self) -> AgentRuntime:
        """Underlying AgentRuntime for direct access."""
        return self._runtime

    @property
    def is_running(self) -> bool:
        """True if the pipeline is active."""
        return self._running

    def start(self) -> None:
        """Bootstrap and start the full pipeline.

        Steps:
        1. Bootstrap runtime (creates and configures all 4 agents)
        2. Subscribe coordinator to pipeline events
        3. Start all agents
        4. Initialize FeedbackLoop if enabled
        """
        if self._running:
            logger.warning("Pipeline already running — skipping start")
            return

        # Bootstrap runtime
        self._runtime.bootstrap()

        # Subscribe to pipeline events for coordination metrics
        bus = self._runtime.event_bus
        bus.subscribe(SkillExtractedEvent, self._on_skill_extracted)
        bus.subscribe(SkillValidatedEvent, self._on_skill_validated)
        bus.subscribe(SkillImprovedEvent, self._on_skill_improved)
        bus.subscribe(SkillRefactorFailedEvent, self._on_refactor_failed)
        bus.subscribe(SkillSyncedEvent, self._on_skill_synced)

        # Start all agents
        started = self._runtime.start()
        self._running = True

        # Initialize feedback loop
        if self._config.feedback_enabled:
            self._init_feedback_loop()

        # Begin first cycle
        self._begin_cycle()

        logger.info(
            "Pipeline started: %d agents, feedback=%s, auto_sync=%s",
            len(started),
            self._config.feedback_enabled,
            self._config.auto_sync,
        )

    def stop(self) -> None:
        """Stop the pipeline and all agents gracefully."""
        if not self._running:
            return

        # Complete current cycle
        self._complete_cycle()

        # Unsubscribe coordinator
        bus = self._runtime.event_bus
        bus.unsubscribe(SkillExtractedEvent, self._on_skill_extracted)
        bus.unsubscribe(SkillValidatedEvent, self._on_skill_validated)
        bus.unsubscribe(SkillImprovedEvent, self._on_skill_improved)
        bus.unsubscribe(SkillRefactorFailedEvent, self._on_refactor_failed)
        bus.unsubscribe(SkillSyncedEvent, self._on_skill_synced)

        # Stop all agents
        self._runtime.stop()
        self._running = False

        logger.info("Pipeline stopped")

    def inject_file_event(
        self, file_path: str, event_type: str, project: str = ""
    ) -> None:
        """Inject a file change event to trigger the extraction pipeline."""
        if not self._running:
            logger.warning("Pipeline not running — ignoring file event")
            return

        self._runtime.inject_event(FileChangeEvent(
            file_path=file_path,
            event_type=event_type,
            project=project or "C:/ClaudeSkills",
        ))

    def get_status(self) -> dict[str, Any]:
        """Return comprehensive pipeline status."""
        agent_infos = self._runtime.get_status()
        cycle = self._current_cycle

        return {
            "running": self._running,
            "config": asdict(self._config),
            "agents": [
                {
                    "name": info.name,
                    "type": info.agent_type,
                    "status": info.status.value,
                    "events_processed": info.events_processed,
                    "events_emitted": info.events_emitted,
                    "errors": info.error_count,
                }
                for info in agent_infos
            ],
            "current_cycle": asdict(cycle) if cycle else None,
            "completed_cycles": len(self._cycle_history),
            "event_bus_handlers": self._runtime.event_bus.handler_count,
        }

    def get_cycle_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent pipeline cycle results."""
        with self._lock:
            recent = self._cycle_history[-limit:]
        return [asdict(c) for c in recent]

    # -- Event handlers (coordinator-level observation) --------------------

    def _on_skill_extracted(self, event: SkillExtractedEvent) -> None:
        """Track extraction in current cycle metrics."""
        with self._lock:
            if self._current_cycle:
                self._current_cycle.skills_extracted += 1
                self._current_cycle.events_processed += 1

    def _on_skill_validated(self, event: SkillValidatedEvent) -> None:
        """Track validation result in current cycle metrics."""
        with self._lock:
            if self._current_cycle:
                self._current_cycle.skills_validated += 1
                self._current_cycle.events_processed += 1

                if event.disposition == "approved":
                    self._current_cycle.skills_approved += 1
                elif event.disposition == "rejected":
                    self._current_cycle.skills_rejected += 1

    def _on_skill_improved(self, event: SkillImprovedEvent) -> None:
        """Track successful refactoring in current cycle metrics."""
        with self._lock:
            if self._current_cycle:
                self._current_cycle.skills_refactored += 1
                self._current_cycle.events_processed += 1

    def _on_refactor_failed(self, event: SkillRefactorFailedEvent) -> None:
        """Track refactor failure in current cycle metrics."""
        with self._lock:
            if self._current_cycle:
                self._current_cycle.refactor_failures += 1
                self._current_cycle.events_processed += 1

    def _on_skill_synced(self, event: SkillSyncedEvent) -> None:
        """Track sync completion in current cycle metrics."""
        with self._lock:
            if self._current_cycle:
                self._current_cycle.skills_synced += 1
                self._current_cycle.events_processed += 1

        # After sync, feed results to feedback loop
        if self._feedback_loop and self._config.feedback_enabled:
            self._complete_cycle()
            self._begin_cycle()

    # -- Cycle management -------------------------------------------------

    def _begin_cycle(self) -> None:
        """Start a new pipeline cycle for metrics tracking."""
        import uuid

        with self._lock:
            self._current_cycle = PipelineCycleResult(
                cycle_id=str(uuid.uuid4())[:8],
                started_at=datetime.now(timezone.utc).isoformat(),
            )

    def _complete_cycle(self) -> None:
        """Complete the current cycle and feed to feedback loop."""
        with self._lock:
            if self._current_cycle is None:
                return

            self._current_cycle.completed_at = (
                datetime.now(timezone.utc).isoformat()
            )
            cycle = self._current_cycle
            self._cycle_history.append(cycle)
            self._current_cycle = None

            # Keep history bounded
            if len(self._cycle_history) > 100:
                self._cycle_history = self._cycle_history[-100:]

        # Feed to feedback loop
        if self._feedback_loop and self._config.feedback_enabled:
            try:
                self._feedback_loop.record_cycle(cycle)
            except Exception as exc:
                logger.warning("Feedback loop recording failed: %s", exc)

        # Persist cycle log
        self._save_cycle_log()

        logger.info(
            "Cycle %s complete: extracted=%d validated=%d approved=%d "
            "refactored=%d rejected=%d synced=%d",
            cycle.cycle_id,
            cycle.skills_extracted,
            cycle.skills_validated,
            cycle.skills_approved,
            cycle.skills_refactored,
            cycle.skills_rejected,
            cycle.skills_synced,
        )

    def _init_feedback_loop(self) -> None:
        """Lazy-initialize the FeedbackLoop."""
        try:
            from scripts.feedback_loop import FeedbackLoop

            self._feedback_loop = FeedbackLoop(asdict(self._config))
            logger.info("FeedbackLoop initialized")
        except ImportError:
            logger.debug("FeedbackLoop not available — feedback disabled")

    def _save_cycle_log(self) -> None:
        """Persist cycle history to disk."""
        try:
            _CYCLE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "total_cycles": len(self._cycle_history),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "cycles": [asdict(c) for c in self._cycle_history[-50:]],
                }
            _CYCLE_LOG_PATH.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("Failed to save cycle log: %s", exc)
