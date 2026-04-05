# refactor_agent.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Refactor agent — autonomous skill improvement with regression prevention

from __future__ import annotations

import logging
from typing import Any

from scripts.agent_base import BaseAgent
from scripts.agent_events import (
    SkillRefactorRequestedEvent,
    SkillImprovedEvent,
    SkillRefactorFailedEvent,
)
from scripts.agent_event_bus import EventBus
from scripts.improvement_tracker import (
    ImprovementTrendTracker,
    RefactorCooldownTracker,
    ImprovementRecord,
)

logger = logging.getLogger("agent.refactor")


class RefactorAgent(BaseAgent):
    """Autonomous skill improvement agent with regression prevention.

    Wraps SkillImprover (Karpathy-style eval loop) and SelfHealingLoop
    (failure recovery). Uses ImprovementTrendTracker for monotonic best-score
    enforcement and RefactorCooldownTracker to prevent rapid-fire retries.

    Self-improving loop:
    1. Receive SkillRefactorRequestedEvent -> check cooldown
    2. Run SkillImprover targeting quality threshold via SelfHealingLoop
    3. Check regression (score must not decrease from historical best)
    4. If improved: publish SkillImprovedEvent -> re-enters ValidatorAgent
    5. If failed: publish SkillRefactorFailedEvent, enter cooldown
    6. Max consecutive failures -> escalate to needs_review
    """

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(name="refactor-agent", agent_type="refactor")
        self._event_bus: EventBus = event_bus
        self._trend_tracker: ImprovementTrendTracker | None = None
        self._cooldown_tracker: RefactorCooldownTracker | None = None
        self._target_score: float = 0.80
        self._max_iterations: int = 10

    # -- Lifecycle hooks ---------------------------------------------------

    def on_configure(self, config: dict[str, Any]) -> None:
        """Instantiate trackers and subscribe to refactor requests."""
        improvement_cfg = config.get("improvement", {})
        self._target_score = improvement_cfg.get("target_score", 0.80)
        self._max_iterations = improvement_cfg.get("max_iterations_per_run", 10)

        self._trend_tracker = ImprovementTrendTracker(config)
        self._cooldown_tracker = RefactorCooldownTracker(config)

        self._event_bus.subscribe(
            SkillRefactorRequestedEvent, self._handle_refactor_request
        )

    def on_stop(self) -> None:
        """Unsubscribe from events on shutdown."""
        self._event_bus.unsubscribe(
            SkillRefactorRequestedEvent, self._handle_refactor_request
        )

    # -- Event handler -----------------------------------------------------

    def _handle_refactor_request(self, event: SkillRefactorRequestedEvent) -> None:
        """Process a refactoring request with cooldown and regression checks."""
        if self.status.value != "running":
            return

        try:
            self._record_processed()
            skill_id = event.skill_id
            skill_name = event.skill_name

            # Gate 1: Cooldown check — prevent rapid-fire retries
            if self._cooldown_tracker and self._cooldown_tracker.is_on_cooldown(skill_id):
                remaining = self._cooldown_tracker.get_cooldown_remaining(skill_id)
                logger.info(
                    "Skill '%s' on cooldown (%.0fs remaining) — skipping",
                    skill_name, remaining,
                )
                return

            # Gate 2: Escalation check — max consecutive failures exceeded
            if self._cooldown_tracker and self._cooldown_tracker.should_escalate(skill_id):
                logger.warning(
                    "Skill '%s' exceeded max consecutive failures — escalating to needs_review",
                    skill_name,
                )
                self._event_bus.publish(SkillRefactorFailedEvent(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    reason="Max consecutive failures exceeded — escalated to needs_review",
                    attempts=self._cooldown_tracker.get_failure_count(skill_id),
                    last_score=event.current_score,
                ))
                self._record_emitted()
                return

            # Run the improvement loop with self-healing
            result = self._run_improvement(skill_name)

            if result is None:
                self._handle_failure(
                    skill_id, skill_name,
                    "Improvement loop returned None", event.current_score,
                )
                return

            new_score = result.get("final_score", event.current_score)
            iterations = result.get("iterations", 0)
            improvement = result.get("improvement", 0.0)
            target_reached = result.get("target_reached", False)
            healing_exhausted = result.get("healing_exhausted", False)

            # If healing was exhausted, treat as failure
            if healing_exhausted:
                self._handle_failure(
                    skill_id, skill_name,
                    f"Self-healing retries exhausted: {result.get('last_error', 'unknown')}",
                    event.current_score,
                )
                return

            # Gate 3: Regression check — score must meet or exceed historical best
            if self._trend_tracker and self._trend_tracker.check_regression(skill_id, new_score):
                self._handle_failure(
                    skill_id, skill_name,
                    f"Regression detected: {new_score:.2f} < historical best",
                    new_score,
                )
                return

            improved = improvement > 0 and new_score > event.current_score

            if improved:
                # Success path — record and publish
                if self._trend_tracker:
                    self._trend_tracker.record(ImprovementRecord(
                        skill_id=skill_id,
                        skill_name=skill_name,
                        previous_score=event.current_score,
                        new_score=new_score,
                        improved=True,
                        iterations=iterations,
                    ))
                if self._cooldown_tracker:
                    self._cooldown_tracker.record_success(skill_id)

                self._event_bus.publish(SkillImprovedEvent(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    previous_score=event.current_score,
                    new_score=new_score,
                    iterations_used=iterations,
                    branch_name=result.get("branch", ""),
                ))
                self._record_emitted()
                logger.info(
                    "Skill '%s' improved: %.2f -> %.2f in %d iterations",
                    skill_name, event.current_score, new_score, iterations,
                )
            else:
                self._handle_failure(
                    skill_id, skill_name,
                    f"No improvement: {event.current_score:.2f} -> {new_score:.2f}",
                    new_score,
                )

        except Exception as exc:
            self._set_error(f"Refactor failed: {exc}")
            logger.exception("Refactor error for '%s'", event.skill_name)

    # -- Internal helpers --------------------------------------------------

    def _run_improvement(self, skill_name: str) -> dict[str, Any] | None:
        """Execute the improvement loop wrapped in SelfHealingLoop.

        Returns the summary dict from SkillImprover.run_loop() or
        the healing-exhausted dict from SelfHealingLoop.run(),
        or None on import/crash failure.
        """
        try:
            from scripts.self_healing_loop import SelfHealingLoop

            healer = SelfHealingLoop(
                skill_name=skill_name,
                max_retries=3,
                max_iterations=self._max_iterations,
                target_score=self._target_score,
            )
            return healer.run()
        except ImportError as exc:
            logger.error("Missing dependency for improvement: %s", exc)
            return None
        except Exception as exc:
            logger.exception("Improvement loop crashed for '%s'", skill_name)
            return None

    def _handle_failure(
        self, skill_id: str, skill_name: str, reason: str, last_score: float
    ) -> None:
        """Record failure in trackers and publish SkillRefactorFailedEvent."""
        attempts = 0
        if self._cooldown_tracker:
            attempts = self._cooldown_tracker.record_failure(skill_id)

        if self._trend_tracker:
            self._trend_tracker.record(ImprovementRecord(
                skill_id=skill_id,
                skill_name=skill_name,
                previous_score=last_score,
                new_score=last_score,
                improved=False,
                iterations=0,
            ))

        self._event_bus.publish(SkillRefactorFailedEvent(
            skill_id=skill_id,
            skill_name=skill_name,
            reason=reason,
            attempts=attempts,
            last_score=last_score,
        ))
        self._record_emitted()
        logger.warning("Refactor failed for '%s': %s", skill_name, reason)
