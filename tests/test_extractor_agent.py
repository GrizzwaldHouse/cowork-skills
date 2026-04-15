# test_extractor_agent.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for the extractor agent — skill extraction from session events

"""
Comprehensive unit tests for the ExtractorAgent class.

Tests lifecycle management, event handling, session detection,
skill extraction, error handling, and metrics tracking.
"""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock
from dataclasses import dataclass
from typing import Any

# Ensure scripts directory is on sys.path for imports
sys.path.insert(0, "C:/ClaudeSkills")
sys.path.insert(0, "C:/ClaudeSkills/scripts")

from scripts.agent_event_bus import EventBus
from scripts.agent_events import (
    FileChangeEvent,
    SessionDetectedEvent,
    SkillExtractedEvent,
)
from scripts.agent_protocol import AgentStatus
from scripts.agents.extractor_agent import ExtractorAgent


# ---------------------------------------------------------------------------
# Mock objects for testing
# ---------------------------------------------------------------------------

@dataclass
class MockSessionEvent:
    """Mock SessionEvent returned by SessionObserver."""
    signal: str
    project: str
    artifacts: list[str]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "project": self.project,
            "artifacts": self.artifacts,
            "details": self.details,
        }


@dataclass
class MockQuadSkill:
    """Mock QuadSkill returned by QuadSkillEngine."""
    skill_id: str
    name: str
    source_project: str
    confidence_score: float
    category: str = "test-category"

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "source_project": self.source_project,
            "confidence_score": self.confidence_score,
            "category": self.category,
        }


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestExtractorAgentInitialization(unittest.TestCase):
    """Test agent initialization and basic properties."""

    def test_agent_initial_state(self) -> None:
        """Agent starts in UNINITIALIZED status."""
        bus = EventBus()
        agent = ExtractorAgent(bus)

        self.assertEqual(agent.name, "extractor-agent")
        self.assertEqual(agent.agent_type, "extractor")
        self.assertEqual(agent.status, AgentStatus.UNINITIALIZED)

    def test_agent_stores_event_bus(self) -> None:
        """Agent stores reference to event bus."""
        bus = EventBus()
        agent = ExtractorAgent(bus)

        self.assertIs(agent._event_bus, bus)

    def test_agent_observer_and_engine_none_before_configure(self) -> None:
        """Observer and engine are None before configure."""
        bus = EventBus()
        agent = ExtractorAgent(bus)

        self.assertIsNone(agent._observer)
        self.assertIsNone(agent._engine)


class TestExtractorAgentLifecycle(unittest.TestCase):
    """Test agent lifecycle transitions."""

    def setUp(self) -> None:
        self.bus = EventBus()
        self.agent = ExtractorAgent(self.bus)
        self.config = {
            "watched_projects": ["C:/Projects/alpha"],
            "session_detection": {
                "idle_timeout_seconds": 300,
                "min_activity_events": 3,
            },
        }

    def test_configure_creates_observer_and_engine(self) -> None:
        """configure() instantiates SessionObserver and QuadSkillEngine."""
        self.agent.configure(self.config)

        # Verify observer and engine were created
        self.assertIsNotNone(self.agent._observer)
        self.assertIsNotNone(self.agent._engine)

    def test_configure_subscribes_to_file_change_event(self) -> None:
        """configure() subscribes to FileChangeEvent on event bus."""
        self.agent.configure(self.config)

        # Verify subscription by checking handler count
        handlers = self.bus._handlers.get(FileChangeEvent, set())
        self.assertEqual(len(handlers), 1)

    def test_configure_sets_configured_status(self) -> None:
        """configure() transitions agent to CONFIGURED status."""
        self.agent.configure(self.config)

        self.assertEqual(self.agent.status, AgentStatus.CONFIGURED)

    def test_start_sets_running_status(self) -> None:
        """start() transitions agent to RUNNING status."""
        self.agent.configure(self.config)
        self.agent.start()

        self.assertEqual(self.agent.status, AgentStatus.RUNNING)

    def test_stop_unsubscribes_from_events(self) -> None:
        """stop() unsubscribes from FileChangeEvent."""
        self.agent.configure(self.config)
        self.agent.start()

        # Verify subscription exists
        handlers_before = self.bus._handlers.get(FileChangeEvent, set())
        self.assertEqual(len(handlers_before), 1)

        self.agent.stop()

        # Verify subscription removed
        handlers_after = self.bus._handlers.get(FileChangeEvent, set())
        self.assertEqual(len(handlers_after), 0)

    def test_stop_sets_stopped_status(self) -> None:
        """stop() transitions agent to STOPPED status."""
        self.agent.configure(self.config)
        self.agent.start()
        self.agent.stop()

        self.assertEqual(self.agent.status, AgentStatus.STOPPED)


class TestExtractorAgentEventHandling(unittest.TestCase):
    """Test event handling logic."""

    def setUp(self) -> None:
        self.bus = EventBus()
        self.agent = ExtractorAgent(self.bus)
        self.config = {
            "watched_projects": ["C:/Projects/alpha"],
            "session_detection": {
                "idle_timeout_seconds": 300,
                "min_activity_events": 3,
            },
        }

        # Mock observer and engine instances
        self.mock_observer = MagicMock()
        self.mock_engine = MagicMock()

    def _configure_with_mocks(self) -> None:
        """Helper to configure agent and inject mocks."""
        self.agent.configure(self.config)
        self.agent._observer = self.mock_observer
        self.agent._engine = self.mock_engine
        self.agent.start()

    def test_file_change_no_session_detected(self) -> None:
        """When observer returns None, no events are published."""
        # Observer returns None (no session detected)
        self.mock_observer.observe_event.return_value = None

        self._configure_with_mocks()

        # Collect published events
        published_events: list[Any] = []
        def capture_event(event: Any) -> None:
            published_events.append(event)

        self.bus.subscribe(SessionDetectedEvent, capture_event)
        self.bus.subscribe(SkillExtractedEvent, capture_event)

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # No events should be published
        self.assertEqual(len(published_events), 0)
        self.mock_engine.extract_from_session.assert_not_called()

    def test_file_change_session_detected(self) -> None:
        """When observer returns SessionEvent, SessionDetectedEvent is published."""
        # Observer returns a session event
        session_event = MockSessionEvent(
            signal="SESSION_START",
            project="C:/Projects/alpha",
            artifacts=["file1.py", "file2.py"],
            details={"event_count": 1},
        )
        self.mock_observer.observe_event.return_value = session_event

        # Engine returns no skills
        self.mock_engine.extract_from_session.return_value = []

        self._configure_with_mocks()

        # Collect published SessionDetectedEvents
        published_events: list[SessionDetectedEvent] = []
        def capture_event(event: SessionDetectedEvent) -> None:
            published_events.append(event)

        self.bus.subscribe(SessionDetectedEvent, capture_event)

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # SessionDetectedEvent should be published
        self.assertEqual(len(published_events), 1)
        self.assertEqual(published_events[0].signal, "SESSION_START")
        self.assertEqual(published_events[0].project, "C:/Projects/alpha")
        self.assertEqual(len(published_events[0].artifacts), 2)

    def test_file_change_skills_extracted(self) -> None:
        """When engine returns skills, SkillExtractedEvent is published per skill."""
        # Observer returns a session event
        session_event = MockSessionEvent(
            signal="SESSION_ACTIVE",
            project="C:/Projects/alpha",
            artifacts=["file1.py"],
            details={},
        )
        self.mock_observer.observe_event.return_value = session_event

        # Engine returns one skill
        skill = MockQuadSkill(
            skill_id="skill-001",
            name="Test Skill",
            source_project="C:/Projects/alpha",
            confidence_score=0.95,
        )
        self.mock_engine.extract_from_session.return_value = [skill]

        self._configure_with_mocks()

        # Collect published SkillExtractedEvents
        published_events: list[SkillExtractedEvent] = []
        def capture_event(event: SkillExtractedEvent) -> None:
            published_events.append(event)

        self.bus.subscribe(SkillExtractedEvent, capture_event)

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # SkillExtractedEvent should be published
        self.assertEqual(len(published_events), 1)
        self.assertEqual(published_events[0].skill_id, "skill-001")
        self.assertEqual(published_events[0].skill_name, "Test Skill")
        self.assertEqual(published_events[0].source_project, "C:/Projects/alpha")
        self.assertEqual(published_events[0].confidence, 0.95)

    def test_file_change_multiple_skills_extracted(self) -> None:
        """When engine returns multiple skills, one event per skill is published."""
        # Observer returns a session event
        session_event = MockSessionEvent(
            signal="SESSION_ACTIVE",
            project="C:/Projects/alpha",
            artifacts=["file1.py"],
            details={},
        )
        self.mock_observer.observe_event.return_value = session_event

        # Engine returns three skills
        skills = [
            MockQuadSkill(
                skill_id=f"skill-{i:03d}",
                name=f"Test Skill {i}",
                source_project="C:/Projects/alpha",
                confidence_score=0.80 + (i * 0.05),
            )
            for i in range(1, 4)
        ]
        self.mock_engine.extract_from_session.return_value = skills

        self._configure_with_mocks()

        # Collect published SkillExtractedEvents
        published_events: list[SkillExtractedEvent] = []
        def capture_event(event: SkillExtractedEvent) -> None:
            published_events.append(event)

        self.bus.subscribe(SkillExtractedEvent, capture_event)

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # Three SkillExtractedEvents should be published
        self.assertEqual(len(published_events), 3)
        self.assertEqual(published_events[0].skill_id, "skill-001")
        self.assertEqual(published_events[1].skill_id, "skill-002")
        self.assertEqual(published_events[2].skill_id, "skill-003")
        self.assertAlmostEqual(published_events[0].confidence, 0.85, places=2)
        self.assertAlmostEqual(published_events[1].confidence, 0.90, places=2)
        self.assertAlmostEqual(published_events[2].confidence, 0.95, places=2)

    def test_not_running_ignores_events(self) -> None:
        """Agent in non-running state ignores FileChangeEvents."""
        # Observer returns a session event
        session_event = MockSessionEvent(
            signal="SESSION_ACTIVE",
            project="C:/Projects/alpha",
            artifacts=["file1.py"],
            details={},
        )
        self.mock_observer.observe_event.return_value = session_event

        self.agent.configure(self.config)
        self.agent._observer = self.mock_observer
        self.agent._engine = self.mock_engine
        # Don't call start() - agent is CONFIGURED, not RUNNING

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # Observer should not be called
        self.mock_observer.observe_event.assert_not_called()


class TestExtractorAgentErrorHandling(unittest.TestCase):
    """Test error handling and error state transitions."""

    def setUp(self) -> None:
        self.bus = EventBus()
        self.agent = ExtractorAgent(self.bus)
        self.config = {
            "watched_projects": ["C:/Projects/alpha"],
            "session_detection": {
                "idle_timeout_seconds": 300,
                "min_activity_events": 3,
            },
        }

        self.mock_observer = MagicMock()
        self.mock_engine = MagicMock()

    def _configure_with_mocks(self) -> None:
        """Helper to configure agent and inject mocks."""
        self.agent.configure(self.config)
        self.agent._observer = self.mock_observer
        self.agent._engine = self.mock_engine
        self.agent.start()

    def test_error_in_observer_sets_error_state(self) -> None:
        """When observer throws exception, agent enters ERROR state."""
        # Observer throws exception
        self.mock_observer.observe_event.side_effect = RuntimeError("Observer failed")

        self._configure_with_mocks()

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # Agent should be in ERROR state
        self.assertEqual(self.agent.status, AgentStatus.ERROR)

    def test_error_in_engine_sets_error_state(self) -> None:
        """When engine throws exception, agent enters ERROR state."""
        # Observer returns a session event
        session_event = MockSessionEvent(
            signal="SESSION_ACTIVE",
            project="C:/Projects/alpha",
            artifacts=["file1.py"],
            details={},
        )
        self.mock_observer.observe_event.return_value = session_event

        # Engine throws exception
        self.mock_engine.extract_from_session.side_effect = ValueError("Engine failed")

        self._configure_with_mocks()

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # Agent should be in ERROR state
        self.assertEqual(self.agent.status, AgentStatus.ERROR)


class TestExtractorAgentMetrics(unittest.TestCase):
    """Test metrics tracking."""

    def setUp(self) -> None:
        self.bus = EventBus()
        self.agent = ExtractorAgent(self.bus)
        self.config = {
            "watched_projects": ["C:/Projects/alpha"],
            "session_detection": {
                "idle_timeout_seconds": 300,
                "min_activity_events": 3,
            },
        }

        self.mock_observer = MagicMock()
        self.mock_engine = MagicMock()

    def _configure_with_mocks(self) -> None:
        """Helper to configure agent and inject mocks."""
        self.agent.configure(self.config)
        self.agent._observer = self.mock_observer
        self.agent._engine = self.mock_engine
        self.agent.start()

    def test_events_processed_increments(self) -> None:
        """events_processed counter increments for each FileChangeEvent."""
        # Observer returns None (no session)
        self.mock_observer.observe_event.return_value = None

        self._configure_with_mocks()

        # Publish three file change events
        for i in range(3):
            file_event = FileChangeEvent(
                file_path=f"C:/Projects/alpha/src/file{i}.py",
                event_type="modified",
                project="C:/Projects/alpha",
            )
            self.bus.publish(file_event)

        # Check metrics
        info = self.agent.get_info()
        self.assertEqual(info.events_processed, 3)

    def test_events_emitted_increments_for_session_detected(self) -> None:
        """events_emitted increments when SessionDetectedEvent is published."""
        # Observer returns a session event
        session_event = MockSessionEvent(
            signal="SESSION_ACTIVE",
            project="C:/Projects/alpha",
            artifacts=["file1.py"],
            details={},
        )
        self.mock_observer.observe_event.return_value = session_event

        # Engine returns no skills
        self.mock_engine.extract_from_session.return_value = []

        self._configure_with_mocks()

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # Check metrics: 1 processed, 1 emitted (SessionDetectedEvent)
        info = self.agent.get_info()
        self.assertEqual(info.events_processed, 1)
        self.assertEqual(info.events_emitted, 1)

    def test_events_emitted_increments_for_skills_extracted(self) -> None:
        """events_emitted increments for each SkillExtractedEvent published."""
        # Observer returns a session event
        session_event = MockSessionEvent(
            signal="SESSION_ACTIVE",
            project="C:/Projects/alpha",
            artifacts=["file1.py"],
            details={},
        )
        self.mock_observer.observe_event.return_value = session_event

        # Engine returns three skills
        skills = [
            MockQuadSkill(
                skill_id=f"skill-{i:03d}",
                name=f"Test Skill {i}",
                source_project="C:/Projects/alpha",
                confidence_score=0.85,
            )
            for i in range(1, 4)
        ]
        self.mock_engine.extract_from_session.return_value = skills

        self._configure_with_mocks()

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # Check metrics: 1 processed, 4 emitted (1 SessionDetected + 3 SkillExtracted)
        info = self.agent.get_info()
        self.assertEqual(info.events_processed, 1)
        self.assertEqual(info.events_emitted, 4)

    def test_error_count_increments_on_exception(self) -> None:
        """error_count increments when an exception occurs."""
        # Observer throws exception
        self.mock_observer.observe_event.side_effect = RuntimeError("Observer failed")

        self._configure_with_mocks()

        # Publish file change event
        file_event = FileChangeEvent(
            file_path="C:/Projects/alpha/src/main.py",
            event_type="modified",
            project="C:/Projects/alpha",
        )
        self.bus.publish(file_event)

        # Check metrics
        info = self.agent.get_info()
        self.assertEqual(info.error_count, 1)


# ---------------------------------------------------------------------------
# Self-test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
