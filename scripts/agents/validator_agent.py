# validator_agent.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Validation agent — wraps ValidationEngine + AISafetyGuard + QualityScoringEngine

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.agent_base import BaseAgent
from scripts.agent_events import (
    SkillExtractedEvent,
    SkillImprovedEvent,
    SkillValidatedEvent,
    SkillRefactorRequestedEvent,
)
from scripts.agent_event_bus import EventBus

logger = logging.getLogger("agent.validator")

# Path to persisted quad skills data
_QUAD_SKILLS_DIR: Path = Path("C:/ClaudeSkills/data/quad_skills")


class ValidatorAgent(BaseAgent):
    """Validates and scores extracted or improved skills.

    Wraps ValidationEngine (architecture/security/quality checks),
    AISafetyGuard (safety gate), and QualityScoringEngine (5-dimension
    weighted scoring with 95/5 reusability rule). Routes skills to
    approved/needs_refactor/needs_review/rejected dispositions.
    """

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(name="validator-agent", agent_type="validator")
        self._event_bus: EventBus = event_bus
        self._validation_engine: Any = None
        self._safety_guard: Any = None
        self._scoring_engine: Any = None

    # -- Lifecycle hooks ---------------------------------------------------

    def on_configure(self, config: dict[str, Any]) -> None:
        """Instantiate validation, safety, and scoring modules."""
        from scripts.validation_engine import ValidationEngine
        from scripts.ai_safety_guard import AISafetyGuard
        from scripts.quality_scoring import QualityScoringEngine

        self._validation_engine = ValidationEngine(config)
        self._safety_guard = AISafetyGuard()
        self._scoring_engine = QualityScoringEngine(config)

        self._event_bus.subscribe(SkillExtractedEvent, self._handle_extracted)
        self._event_bus.subscribe(SkillImprovedEvent, self._handle_improved)

    def on_stop(self) -> None:
        """Unsubscribe from events on shutdown."""
        self._event_bus.unsubscribe(SkillExtractedEvent, self._handle_extracted)
        self._event_bus.unsubscribe(SkillImprovedEvent, self._handle_improved)

    # -- Event handlers ----------------------------------------------------

    def _handle_extracted(self, event: SkillExtractedEvent) -> None:
        """Validate a freshly extracted skill."""
        self._validate_skill(event.skill_id, event.skill_name, event.skill_data)

    def _handle_improved(self, event: SkillImprovedEvent) -> None:
        """Re-validate an improved skill by loading its data from disk."""
        skill_data = self._load_skill_data(event.skill_id)
        if skill_data:
            self._validate_skill(event.skill_id, event.skill_name, skill_data)

    # -- Core validation pipeline ------------------------------------------

    def _validate_skill(
        self, skill_id: str, skill_name: str, skill_data: dict[str, Any]
    ) -> None:
        """Run the full validation pipeline on a skill.

        Steps:
        1. Run ValidationEngine.validate() for arch/sec/qual scores
        2. Run AISafetyGuard.check_install() — rejects if safety blocked
        3. Run QualityScoringEngine.score() for 5-dimension composite
        4. Publish SkillValidatedEvent with disposition
        5. If disposition == needs_refactor, also publish SkillRefactorRequestedEvent
        """
        if self.status.value != "running":
            return

        try:
            self._record_processed()

            # Step 1: Structural validation
            validation_report = self._validation_engine.validate(skill_data)
            vr_dict = (
                asdict(validation_report)
                if hasattr(validation_report, "__dataclass_fields__")
                else validation_report.to_dict()
                if hasattr(validation_report, "to_dict")
                else vars(validation_report)
                if hasattr(validation_report, "__dict__")
                else validation_report
            )

            # Step 2: Safety gate — returns SafetyAlert or None
            safety_alert = self._safety_guard.check_install(skill_data, vr_dict)

            if safety_alert is not None:
                self._event_bus.publish(SkillValidatedEvent(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    disposition="rejected",
                    composite_score=0.0,
                    violations=(
                        f"Safety blocked: {getattr(safety_alert, 'message', str(safety_alert))}",
                    ),
                ))
                self._record_emitted()
                logger.warning("Skill '%s' rejected by safety guard", skill_name)
                return

            # Step 3: Quality scoring (5-dimension weighted)
            quality_report = self._scoring_engine.score(skill_data, vr_dict)

            dimension_scores = {
                d.dimension: d.score for d in quality_report.dimensions
            }

            # Step 4: Publish validation result
            self._event_bus.publish(SkillValidatedEvent(
                skill_id=skill_id,
                skill_name=skill_name,
                disposition=quality_report.disposition,
                composite_score=quality_report.composite_score,
                dimension_scores=dimension_scores,
                violations=quality_report.violations,
                quality_report=(
                    asdict(quality_report)
                    if hasattr(quality_report, "__dataclass_fields__")
                    else {}
                ),
            ))
            self._record_emitted()

            # Step 5: If needs_refactor, route to refactor agent
            if quality_report.disposition == "needs_refactor":
                self._event_bus.publish(SkillRefactorRequestedEvent(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    current_score=quality_report.composite_score,
                    dimension_scores=dimension_scores,
                    violations=quality_report.violations,
                ))
                self._record_emitted()
                logger.info(
                    "Skill '%s' scored %.2f — requesting refactor",
                    skill_name, quality_report.composite_score,
                )
            else:
                logger.info(
                    "Skill '%s' scored %.2f — disposition: %s",
                    skill_name, quality_report.composite_score,
                    quality_report.disposition,
                )

        except Exception as exc:
            self._set_error(f"Validation failed: {exc}")
            logger.exception("Validation error for skill '%s'", skill_name)

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _load_skill_data(skill_id: str) -> dict[str, Any] | None:
        """Load skill data from the quad_skills data directory."""
        skill_path = _QUAD_SKILLS_DIR / f"{skill_id}.json"
        try:
            if skill_path.exists():
                return json.loads(skill_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load skill %s: %s", skill_id, exc)
        return None
