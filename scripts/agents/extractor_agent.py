# extractor_agent.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Extraction agent — wraps SessionObserver + QuadSkillEngine for skill discovery

from __future__ import annotations

import logging
from typing import Any

from scripts.agent_base import BaseAgent
from scripts.agent_events import (
    FileChangeEvent,
    SessionDetectedEvent,
    SkillExtractedEvent,
)
from scripts.agent_event_bus import EventBus

logger = logging.getLogger("agent.extractor")


class ExtractorAgent(BaseAgent):
    """Discovers skills from file system activity.

    Wraps SessionObserver (detects Claude sessions from file events) and
    QuadSkillEngine (extracts reusable skill patterns from session artifacts).
    Subscribes to FileChangeEvent, publishes SessionDetectedEvent and
    SkillExtractedEvent.
    """

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(name="extractor-agent", agent_type="extractor")
        self._event_bus: EventBus = event_bus
        self._observer: Any = None  # SessionObserver instance
        self._engine: Any = None    # QuadSkillEngine instance

    # -- Lifecycle hooks ---------------------------------------------------

    def on_configure(self, config: dict[str, Any]) -> None:
        """Instantiate wrapped modules with provided config."""
        from scripts.session_observer import SessionObserver
        from scripts.quad_skill_engine import QuadSkillEngine

        self._observer = SessionObserver(config)
        self._engine = QuadSkillEngine(config)

        self._event_bus.subscribe(FileChangeEvent, self._handle_file_change)

    def on_stop(self) -> None:
        """Unsubscribe from events on shutdown."""
        self._event_bus.unsubscribe(FileChangeEvent, self._handle_file_change)

    # -- Event handler -----------------------------------------------------

    def _handle_file_change(self, event: FileChangeEvent) -> None:
        """Process a file change through the extraction pipeline.

        Pipeline steps:
        1. Feed event to SessionObserver.observe_event()
        2. If session signal returned, publish SessionDetectedEvent
        3. Convert session event to dict, feed to QuadSkillEngine.extract_from_session()
        4. For each extracted skill, publish SkillExtractedEvent with skill data
        """
        if self.status.value != "running":
            return

        try:
            self._record_processed()

            # Step 1: Feed to SessionObserver
            session_event = self._observer.observe_event(
                event.event_type, event.file_path
            )

            if session_event is None:
                return

            # Step 2: Publish session detection
            # SessionEvent has a to_dict() method per the protocol
            se_dict = (
                session_event.to_dict()
                if hasattr(session_event, "to_dict")
                else vars(session_event)
                if hasattr(session_event, "__dict__")
                else {}
            )

            self._event_bus.publish(SessionDetectedEvent(
                signal=str(se_dict.get("signal", "")),
                project=se_dict.get("project", event.project),
                artifacts=tuple(str(a) for a in se_dict.get("artifacts", [])),
                details=se_dict.get("details", {}),
            ))
            self._record_emitted()

            # Step 3: Extract skills from session
            skills = self._engine.extract_from_session(se_dict)

            # Step 4: Publish each extracted skill
            for skill in skills:
                # QuadSkill has a to_dict() method
                skill_dict = (
                    skill.to_dict()
                    if hasattr(skill, "to_dict")
                    else vars(skill)
                    if hasattr(skill, "__dict__")
                    else skill
                )
                self._event_bus.publish(SkillExtractedEvent(
                    skill_id=skill_dict.get("skill_id", ""),
                    skill_name=skill_dict.get("name", ""),
                    skill_data=skill_dict,
                    source_project=skill_dict.get("source_project", event.project),
                    confidence=float(skill_dict.get("confidence_score", 0.0)),
                ))
                self._record_emitted()

            if skills:
                logger.info(
                    "Extracted %d skills from %s", len(skills), event.file_path
                )

        except Exception as exc:
            self._set_error(f"Extraction failed: {exc}")
            logger.exception("Extraction pipeline error for %s", event.file_path)
