# test_validator_agent.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for the validator agent — scoring and disposition routing

import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
import sys

sys.path.insert(0, "C:/ClaudeSkills")
sys.path.insert(0, "C:/ClaudeSkills/scripts")

from scripts.agent_event_bus import EventBus
from scripts.agent_events import (
    SkillExtractedEvent,
    SkillValidatedEvent,
    SkillRefactorRequestedEvent,
    SkillImprovedEvent,
)
from scripts.agents.validator_agent import ValidatorAgent
from scripts.quality_scoring import DimensionScore, QualityReport


def _make_quality_report(
    skill_id: str = "test",
    skill_name: str = "test",
    composite: float = 0.85,
    disposition: str = "approved",
    dimensions: tuple = (),
    violations: tuple = (),
) -> QualityReport:
    """Build a real QualityReport dataclass (avoids asdict mock issues)."""
    if not dimensions:
        dimensions = (
            DimensionScore("architecture", 0.9, 0.20, 0.18),
            DimensionScore("security", 0.95, 0.25, 0.2375),
            DimensionScore("quality", 0.8, 0.15, 0.12),
            DimensionScore("reusability", 0.85, 0.25, 0.2125),
            DimensionScore("completeness", 0.9, 0.15, 0.135),
        )
    return QualityReport(
        skill_id=skill_id,
        skill_name=skill_name,
        composite_score=composite,
        disposition=disposition,
        dimensions=dimensions,
        violations=violations,
    )


class TestValidatorAgent(unittest.TestCase):
    """Test suite for ValidatorAgent — validates and scores skills."""

    def setUp(self) -> None:
        """Create event bus and agent."""
        self.event_bus = EventBus()
        self.agent = ValidatorAgent(self.event_bus)
        self.config = {
            "extraction": {"auto_approve_threshold": 0.7},
            "safety": {"blocked_patterns": [], "core_skills": []},
            "quality_scoring": {},
        }

    def _configure_and_mock(self) -> None:
        """Configure agent normally, then replace internals with mocks."""
        self.agent.configure(self.config)

        self.mock_validation_engine = MagicMock()
        self.mock_safety_guard = MagicMock()
        self.mock_scoring_engine = MagicMock()

        self.agent._validation_engine = self.mock_validation_engine
        self.agent._safety_guard = self.mock_safety_guard
        self.agent._scoring_engine = self.mock_scoring_engine

    def _setup_validation_mocks(
        self,
        safety_alert=None,
        quality_report: QualityReport | None = None,
    ) -> None:
        """Set up standard mock returns for the validation pipeline."""
        # ValidationEngine.validate() returns something with to_dict()
        mock_vr = MagicMock()
        mock_vr.to_dict.return_value = {
            "architecture_score": 0.9,
            "security_score": 0.95,
            "quality_score": 0.8,
            "violations": [],
        }
        # Make hasattr check for __dataclass_fields__ return False
        mock_vr.__dataclass_fields__ = None
        del mock_vr.__dataclass_fields__
        self.mock_validation_engine.validate.return_value = mock_vr

        # AISafetyGuard.check_install()
        self.mock_safety_guard.check_install.return_value = safety_alert

        # QualityScoringEngine.score()
        if quality_report is None:
            quality_report = _make_quality_report()
        self.mock_scoring_engine.score.return_value = quality_report

    # -- Initialization tests -----------------------------------------------

    def test_agent_initial_state(self) -> None:
        """Agent starts in uninitialized state."""
        self.assertEqual(self.agent.name, "validator-agent")
        self.assertEqual(self.agent.agent_type, "validator")
        self.assertEqual(self.agent.status.value, "uninitialized")

    def test_configure_subscribes(self) -> None:
        """on_configure subscribes to SkillExtractedEvent and SkillImprovedEvent."""
        self.agent.configure(self.config)

        extracted_handlers = self.event_bus._handlers.get(SkillExtractedEvent, [])
        improved_handlers = self.event_bus._handlers.get(SkillImprovedEvent, [])

        self.assertIn(self.agent._handle_extracted, extracted_handlers)
        self.assertIn(self.agent._handle_improved, improved_handlers)

    # -- Disposition routing tests ------------------------------------------

    def test_skill_approved(self) -> None:
        """High-scoring skill receives 'approved' disposition."""
        self._configure_and_mock()
        qr = _make_quality_report(
            composite=0.87, disposition="approved"
        )
        self._setup_validation_mocks(quality_report=qr)
        self.agent.start()

        published = []
        self.event_bus.subscribe(SkillValidatedEvent, published.append)

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-001",
            skill_name="approved-skill",
            skill_data={"skill_id": "skill-001", "name": "approved-skill"},
        ))

        self.assertEqual(len(published), 1)
        self.assertEqual(published[0].disposition, "approved")
        self.assertAlmostEqual(published[0].composite_score, 0.87, places=2)

    def test_skill_needs_refactor(self) -> None:
        """Mid-scoring skill receives 'needs_refactor' and triggers refactor request."""
        self._configure_and_mock()
        qr = _make_quality_report(
            composite=0.55,
            disposition="needs_refactor",
            violations=("Quality: low completeness",),
        )
        self._setup_validation_mocks(quality_report=qr)
        self.agent.start()

        validated = []
        refactored = []
        self.event_bus.subscribe(SkillValidatedEvent, validated.append)
        self.event_bus.subscribe(SkillRefactorRequestedEvent, refactored.append)

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-002",
            skill_name="refactor-skill",
            skill_data={"skill_id": "skill-002", "name": "refactor-skill"},
        ))

        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0].disposition, "needs_refactor")

        self.assertEqual(len(refactored), 1)
        self.assertEqual(refactored[0].skill_id, "skill-002")
        self.assertAlmostEqual(refactored[0].current_score, 0.55, places=2)

    def test_skill_rejected(self) -> None:
        """Low-scoring skill receives 'rejected' disposition."""
        self._configure_and_mock()
        qr = _make_quality_report(
            composite=0.35,
            disposition="rejected",
            violations=("CRITICAL: multiple violations",),
        )
        self._setup_validation_mocks(quality_report=qr)
        self.agent.start()

        published = []
        self.event_bus.subscribe(SkillValidatedEvent, published.append)

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-003",
            skill_name="rejected-skill",
            skill_data={"skill_id": "skill-003", "name": "rejected-skill"},
        ))

        self.assertEqual(len(published), 1)
        self.assertEqual(published[0].disposition, "rejected")
        self.assertAlmostEqual(published[0].composite_score, 0.35, places=2)

    def test_safety_blocked(self) -> None:
        """Safety guard blocks skill — rejected immediately, scoring skipped."""
        self._configure_and_mock()
        alert = MagicMock()
        alert.message = "Blocked pattern: os.system"
        self._setup_validation_mocks(safety_alert=alert)
        self.agent.start()

        published = []
        self.event_bus.subscribe(SkillValidatedEvent, published.append)

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-004",
            skill_name="unsafe-skill",
            skill_data={"skill_id": "skill-004", "name": "unsafe-skill"},
        ))

        self.assertEqual(len(published), 1)
        self.assertEqual(published[0].disposition, "rejected")
        self.assertEqual(published[0].composite_score, 0.0)
        self.assertIn("Safety blocked", published[0].violations[0])
        self.mock_scoring_engine.score.assert_not_called()

    # -- State and lifecycle tests ------------------------------------------

    def test_not_running_ignores(self) -> None:
        """Events ignored when agent is not in running state."""
        self._configure_and_mock()
        self._setup_validation_mocks()
        # Agent is configured but NOT started

        published = []
        self.event_bus.subscribe(SkillValidatedEvent, published.append)

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-005",
            skill_name="ignored-skill",
            skill_data={"skill_id": "skill-005"},
        ))

        self.assertEqual(len(published), 0)
        self.mock_validation_engine.validate.assert_not_called()

    def test_improved_skill_revalidated(self) -> None:
        """SkillImprovedEvent triggers re-validation via _load_skill_data."""
        self._configure_and_mock()
        qr = _make_quality_report(composite=0.90, disposition="approved")
        self._setup_validation_mocks(quality_report=qr)
        self.agent.start()

        # Mock _load_skill_data to return skill data
        with patch.object(
            ValidatorAgent,
            "_load_skill_data",
            return_value={
                "skill_id": "skill-006",
                "name": "improved-skill",
                "intent": "Improved intent",
            },
        ):
            published = []
            self.event_bus.subscribe(SkillValidatedEvent, published.append)

            self.event_bus.publish(SkillImprovedEvent(
                skill_id="skill-006",
                skill_name="improved-skill",
                previous_score=0.50,
                new_score=0.90,
            ))

            self.assertEqual(len(published), 1)
            self.assertEqual(published[0].disposition, "approved")

    def test_error_handling(self) -> None:
        """Exception in validation pipeline sets agent to error state."""
        self._configure_and_mock()
        self.mock_validation_engine.validate.side_effect = RuntimeError("Test error")
        self.agent.start()

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-007",
            skill_name="error-skill",
            skill_data={"skill_id": "skill-007"},
        ))

        self.assertEqual(self.agent.status.value, "error")
        info = self.agent.get_info()
        self.assertGreater(info.error_count, 0)

    # -- Data forwarding tests ----------------------------------------------

    def test_dimension_scores_forwarded(self) -> None:
        """Dimension scores from quality report appear in validated event."""
        self._configure_and_mock()
        dims = (
            DimensionScore("architecture", 0.9, 0.20, 0.18),
            DimensionScore("security", 0.95, 0.25, 0.2375),
            DimensionScore("reusability", 0.80, 0.25, 0.20),
        )
        qr = _make_quality_report(
            composite=0.87, disposition="approved", dimensions=dims
        )
        self._setup_validation_mocks(quality_report=qr)
        self.agent.start()

        published = []
        self.event_bus.subscribe(SkillValidatedEvent, published.append)

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-008",
            skill_name="dimensions-skill",
            skill_data={"skill_id": "skill-008", "name": "dimensions-skill"},
        ))

        self.assertEqual(len(published), 1)
        scores = published[0].dimension_scores
        self.assertAlmostEqual(scores["architecture"], 0.9, places=2)
        self.assertAlmostEqual(scores["security"], 0.95, places=2)
        self.assertAlmostEqual(scores["reusability"], 0.80, places=2)

    def test_metrics_tracked(self) -> None:
        """Events processed and emitted counters increment correctly."""
        self._configure_and_mock()
        qr = _make_quality_report(composite=0.85, disposition="approved")
        self._setup_validation_mocks(quality_report=qr)
        self.agent.start()

        self.event_bus.publish(SkillExtractedEvent(
            skill_id="skill-009",
            skill_name="metrics-skill",
            skill_data={"skill_id": "skill-009"},
        ))

        info = self.agent.get_info()
        self.assertGreaterEqual(info.events_processed, 1)
        self.assertGreaterEqual(info.events_emitted, 1)

    def test_stop_unsubscribes(self) -> None:
        """Stop removes event handlers from the bus."""
        self._configure_and_mock()
        self.agent.start()

        handlers_before = len(self.event_bus._handlers.get(SkillExtractedEvent, []))
        self.agent.stop()
        handlers_after = len(self.event_bus._handlers.get(SkillExtractedEvent, []))

        self.assertLess(handlers_after, handlers_before)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestValidatorAgent)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'=' * 60}")
    print(f"Tests: {result.testsRun} | "
          f"Pass: {result.testsRun - len(result.failures) - len(result.errors)} | "
          f"Fail: {len(result.failures)} | Errors: {len(result.errors)}")
    print(f"{'=' * 60}")
    sys.exit(0 if result.wasSuccessful() else 1)
