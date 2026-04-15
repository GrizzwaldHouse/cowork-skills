# test_agent_coordinator.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for the pipeline coordinator and configuration

import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

sys.path.insert(0, "C:/ClaudeSkills")

from scripts.agent_coordinator import (
    AgentCoordinator,
    PipelineConfig,
    PipelineCycleResult,
)
from scripts.agent_events import (
    SkillExtractedEvent,
    SkillValidatedEvent,
    SkillImprovedEvent,
    SkillRefactorFailedEvent,
    SkillSyncedEvent,
    FileChangeEvent,
)


class TestPipelineConfig(unittest.TestCase):
    """Test PipelineConfig dataclass and loading."""

    def test_pipeline_config_defaults(self):
        """PipelineConfig() has correct defaults."""
        config = PipelineConfig()

        self.assertTrue(config.auto_extract)
        self.assertTrue(config.auto_refactor)
        self.assertFalse(config.auto_sync)
        self.assertEqual(config.min_quality_score, 0.7)
        self.assertEqual(config.min_reusability_score, 0.85)
        self.assertEqual(config.max_refactor_iterations, 10)
        self.assertTrue(config.feedback_enabled)

    def test_pipeline_config_from_dict(self):
        """PipelineConfig.from_dict(data) works correctly."""
        data = {
            "auto_extract": False,
            "auto_sync": True,
            "min_quality_score": 0.8,
            "max_refactor_iterations": 5,
        }

        config = PipelineConfig.from_dict(data)

        self.assertFalse(config.auto_extract)
        self.assertTrue(config.auto_sync)
        self.assertEqual(config.min_quality_score, 0.8)
        self.assertEqual(config.max_refactor_iterations, 5)
        # Defaults preserved for fields not in dict
        self.assertTrue(config.auto_refactor)
        self.assertEqual(config.min_reusability_score, 0.85)

    def test_pipeline_config_ignores_unknown(self):
        """Unknown keys in from_dict don't cause errors."""
        data = {
            "auto_extract": True,
            "unknown_field": "should_be_ignored",
            "another_unknown": 999,
        }

        config = PipelineConfig.from_dict(data)

        self.assertTrue(config.auto_extract)
        # Unknown fields silently ignored
        self.assertFalse(hasattr(config, "unknown_field"))
        self.assertFalse(hasattr(config, "another_unknown"))

    def test_pipeline_config_load_missing_file(self):
        """load() returns defaults when file missing."""
        non_existent = Path("C:/ClaudeSkills/config/missing_config.json")

        config = PipelineConfig.load(non_existent)

        # Should return default config
        self.assertTrue(config.auto_extract)
        self.assertTrue(config.auto_refactor)
        self.assertFalse(config.auto_sync)

    def test_pipeline_config_load_valid_file(self):
        """load() parses valid JSON file correctly."""
        test_data = {
            "auto_extract": False,
            "auto_sync": True,
            "min_quality_score": 0.9,
        }

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(test_data)

        with patch("scripts.agent_coordinator.Path", return_value=mock_path):
            config = PipelineConfig.load(mock_path)

        self.assertFalse(config.auto_extract)
        self.assertTrue(config.auto_sync)
        self.assertEqual(config.min_quality_score, 0.9)

    def test_pipeline_config_load_invalid_json(self):
        """load() returns defaults when JSON is invalid."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "{ invalid json }"

        config = PipelineConfig.load(mock_path)

        # Should fallback to defaults on parse error
        self.assertTrue(config.auto_extract)
        self.assertFalse(config.auto_sync)


class TestPipelineCycleResult(unittest.TestCase):
    """Test PipelineCycleResult dataclass."""

    def test_pipeline_cycle_result_defaults(self):
        """PipelineCycleResult has zero/empty defaults."""
        result = PipelineCycleResult()

        self.assertEqual(result.cycle_id, "")
        self.assertEqual(result.started_at, "")
        self.assertEqual(result.completed_at, "")
        self.assertEqual(result.skills_extracted, 0)
        self.assertEqual(result.skills_validated, 0)
        self.assertEqual(result.skills_approved, 0)
        self.assertEqual(result.skills_refactored, 0)
        self.assertEqual(result.skills_rejected, 0)
        self.assertEqual(result.skills_synced, 0)
        self.assertEqual(result.refactor_failures, 0)
        self.assertEqual(result.events_processed, 0)

    def test_pipeline_cycle_result_initialization(self):
        """PipelineCycleResult initializes with provided values."""
        result = PipelineCycleResult(
            cycle_id="test-123",
            started_at="2026-04-05T10:00:00Z",
            skills_extracted=5,
            skills_approved=3,
        )

        self.assertEqual(result.cycle_id, "test-123")
        self.assertEqual(result.started_at, "2026-04-05T10:00:00Z")
        self.assertEqual(result.skills_extracted, 5)
        self.assertEqual(result.skills_approved, 3)
        # Defaults for fields not specified
        self.assertEqual(result.skills_rejected, 0)


class TestAgentCoordinator(unittest.TestCase):
    """Test AgentCoordinator lifecycle and methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_runtime_patcher = patch("scripts.agent_coordinator.AgentRuntime")
        self.mock_runtime_class = self.mock_runtime_patcher.start()
        self.mock_runtime = MagicMock()
        self.mock_runtime_class.return_value = self.mock_runtime

        # Mock event bus
        self.mock_event_bus = MagicMock()
        self.mock_runtime.event_bus = self.mock_event_bus
        self.mock_runtime.get_status.return_value = []
        self.mock_runtime.start.return_value = ["agent1", "agent2", "agent3", "agent4"]

    def tearDown(self):
        """Clean up patches."""
        self.mock_runtime_patcher.stop()

    def test_coordinator_not_running_initially(self):
        """is_running is False before start()."""
        config = PipelineConfig()
        coordinator = AgentCoordinator(config)

        self.assertFalse(coordinator.is_running)

    def test_coordinator_config_accessible(self):
        """config property returns PipelineConfig."""
        config = PipelineConfig(auto_sync=True, min_quality_score=0.9)
        coordinator = AgentCoordinator(config)

        retrieved = coordinator.config

        self.assertIsInstance(retrieved, PipelineConfig)
        self.assertTrue(retrieved.auto_sync)
        self.assertEqual(retrieved.min_quality_score, 0.9)

    def test_coordinator_runtime_accessible(self):
        """runtime property returns AgentRuntime."""
        coordinator = AgentCoordinator()

        runtime = coordinator.runtime

        self.assertEqual(runtime, self.mock_runtime)

    def test_coordinator_get_status_before_start(self):
        """get_status() returns valid dict with running=False before start."""
        coordinator = AgentCoordinator()

        status = coordinator.get_status()

        self.assertIsInstance(status, dict)
        self.assertFalse(status["running"])
        self.assertIn("config", status)
        self.assertIn("agents", status)
        self.assertIsNone(status["current_cycle"])
        self.assertEqual(status["completed_cycles"], 0)

    def test_coordinator_cycle_history_empty(self):
        """get_cycle_history() returns empty list before any cycles."""
        coordinator = AgentCoordinator()

        history = coordinator.get_cycle_history()

        self.assertEqual(history, [])

    def test_coordinator_cycle_history_limit(self):
        """get_cycle_history(limit) respects limit parameter."""
        coordinator = AgentCoordinator()

        # Manually populate history for testing
        for i in range(20):
            coordinator._cycle_history.append(
                PipelineCycleResult(cycle_id=f"cycle-{i}")
            )

        history = coordinator.get_cycle_history(limit=5)

        self.assertEqual(len(history), 5)
        # Should return last 5 cycles
        self.assertEqual(history[0]["cycle_id"], "cycle-15")
        self.assertEqual(history[-1]["cycle_id"], "cycle-19")

    @patch("scripts.agent_coordinator.logger")
    def test_coordinator_start_stop(self, mock_logger):
        """start() and stop() work correctly with mocked runtime."""
        coordinator = AgentCoordinator()

        # Start coordinator
        coordinator.start()

        self.assertTrue(coordinator.is_running)
        self.mock_runtime.bootstrap.assert_called_once()
        self.mock_runtime.start.assert_called_once()
        # Should subscribe to events
        self.assertGreater(self.mock_event_bus.subscribe.call_count, 0)

        # Stop coordinator
        coordinator.stop()

        self.assertFalse(coordinator.is_running)
        self.mock_runtime.stop.assert_called_once()
        # Should unsubscribe from events
        self.assertGreater(self.mock_event_bus.unsubscribe.call_count, 0)

    @patch("scripts.agent_coordinator.logger")
    def test_coordinator_start_already_running(self, mock_logger):
        """start() logs warning if already running."""
        coordinator = AgentCoordinator()

        coordinator.start()
        self.mock_runtime.bootstrap.reset_mock()

        # Try to start again
        coordinator.start()

        # Should not bootstrap again
        self.mock_runtime.bootstrap.assert_not_called()
        # Should log warning
        mock_logger.warning.assert_called_with(
            "Pipeline already running — skipping start"
        )

    @patch("scripts.agent_coordinator.logger")
    def test_coordinator_inject_without_running(self, mock_logger):
        """inject_file_event() logs warning when not running."""
        coordinator = AgentCoordinator()

        coordinator.inject_file_event("test.py", "modified", "C:/TestProject")

        # Should log warning
        mock_logger.warning.assert_called_with(
            "Pipeline not running — ignoring file event"
        )
        # Should not inject event
        self.mock_runtime.inject_event.assert_not_called()

    def test_coordinator_inject_with_running(self):
        """inject_file_event() injects event when running."""
        coordinator = AgentCoordinator()
        coordinator.start()

        coordinator.inject_file_event("test.py", "modified", "C:/TestProject")

        # Should inject event
        self.mock_runtime.inject_event.assert_called_once()
        call_args = self.mock_runtime.inject_event.call_args[0][0]
        self.assertIsInstance(call_args, FileChangeEvent)
        self.assertEqual(call_args.file_path, "test.py")
        self.assertEqual(call_args.event_type, "modified")
        self.assertEqual(call_args.project, "C:/TestProject")

    def test_coordinator_inject_default_project(self):
        """inject_file_event() uses default project when not specified."""
        coordinator = AgentCoordinator()
        coordinator.start()

        coordinator.inject_file_event("test.py", "created")

        call_args = self.mock_runtime.inject_event.call_args[0][0]
        self.assertEqual(call_args.project, "C:/ClaudeSkills")

    def test_coordinator_get_status_after_start(self):
        """get_status() returns accurate status after start."""
        mock_agent_info = MagicMock()
        mock_agent_info.name = "TestAgent"
        mock_agent_info.agent_type = "extractor"
        mock_agent_info.status.value = "running"
        mock_agent_info.events_processed = 10
        mock_agent_info.events_emitted = 5
        mock_agent_info.error_count = 0

        self.mock_runtime.get_status.return_value = [mock_agent_info]
        self.mock_event_bus.handler_count = 12

        coordinator = AgentCoordinator()
        coordinator.start()

        status = coordinator.get_status()

        self.assertTrue(status["running"])
        self.assertEqual(len(status["agents"]), 1)
        self.assertEqual(status["agents"][0]["name"], "TestAgent")
        self.assertEqual(status["agents"][0]["type"], "extractor")
        self.assertEqual(status["agents"][0]["status"], "running")
        self.assertEqual(status["event_bus_handlers"], 12)

    def test_coordinator_event_handler_skill_extracted(self):
        """_on_skill_extracted updates cycle metrics."""
        coordinator = AgentCoordinator()
        coordinator.start()

        # Should have started a cycle
        self.assertIsNotNone(coordinator._current_cycle)
        initial_extracted = coordinator._current_cycle.skills_extracted

        event = SkillExtractedEvent(
            skill_id="skill-123",
            skill_name="test-skill",
            skill_data={"type": "test"},
            source_project="C:/TestProject",
            confidence=0.95,
        )

        coordinator._on_skill_extracted(event)

        self.assertEqual(
            coordinator._current_cycle.skills_extracted, initial_extracted + 1
        )
        self.assertEqual(
            coordinator._current_cycle.events_processed, 1
        )

    def test_coordinator_event_handler_skill_validated_approved(self):
        """_on_skill_validated updates cycle metrics for approved skill."""
        coordinator = AgentCoordinator()
        coordinator.start()

        event = SkillValidatedEvent(
            skill_id="skill-123",
            skill_name="test-skill",
            disposition="approved",
            composite_score=0.85,
            dimension_scores={"quality": 0.85, "reusability": 0.9},
            violations=(),
            quality_report={"notes": "Looks good"},
        )

        coordinator._on_skill_validated(event)

        self.assertEqual(coordinator._current_cycle.skills_validated, 1)
        self.assertEqual(coordinator._current_cycle.skills_approved, 1)
        self.assertEqual(coordinator._current_cycle.skills_rejected, 0)

    def test_coordinator_event_handler_skill_validated_rejected(self):
        """_on_skill_validated updates cycle metrics for rejected skill."""
        coordinator = AgentCoordinator()
        coordinator.start()

        event = SkillValidatedEvent(
            skill_id="skill-123",
            skill_name="test-skill",
            disposition="rejected",
            composite_score=0.5,
            dimension_scores={"quality": 0.5, "reusability": 0.6},
            violations=("too_complex", "missing_docs"),
            quality_report={"notes": "Quality too low"},
        )

        coordinator._on_skill_validated(event)

        self.assertEqual(coordinator._current_cycle.skills_validated, 1)
        self.assertEqual(coordinator._current_cycle.skills_approved, 0)
        self.assertEqual(coordinator._current_cycle.skills_rejected, 1)

    def test_coordinator_event_handler_skill_improved(self):
        """_on_skill_improved updates cycle metrics."""
        coordinator = AgentCoordinator()
        coordinator.start()

        event = SkillImprovedEvent(
            skill_id="skill-123",
            skill_name="test-skill",
            previous_score=0.7,
            new_score=0.9,
            iterations_used=1,
            branch_name="refactor/test-skill",
        )

        coordinator._on_skill_improved(event)

        self.assertEqual(coordinator._current_cycle.skills_refactored, 1)

    def test_coordinator_event_handler_refactor_failed(self):
        """_on_refactor_failed updates cycle metrics."""
        coordinator = AgentCoordinator()
        coordinator.start()

        event = SkillRefactorFailedEvent(
            skill_id="skill-123",
            skill_name="test-skill",
            reason="Max iterations exceeded",
            attempts=3,
            last_score=0.65,
        )

        coordinator._on_refactor_failed(event)

        self.assertEqual(coordinator._current_cycle.refactor_failures, 1)

    def test_coordinator_event_handler_skill_synced(self):
        """_on_skill_synced updates cycle metrics."""
        config = PipelineConfig(feedback_enabled=False)
        coordinator = AgentCoordinator(config)
        coordinator.start()

        event = SkillSyncedEvent(
            skill_id="skill-123",
            skill_name="test-skill",
            targets=("git", "local"),
            sync_type="install",
        )

        coordinator._on_skill_synced(event)

        self.assertEqual(coordinator._current_cycle.skills_synced, 1)

    def test_coordinator_feedback_loop_disabled(self):
        """Coordinator respects feedback_enabled=False."""
        config = PipelineConfig(feedback_enabled=False)
        coordinator = AgentCoordinator(config)

        coordinator.start()

        # Feedback loop should not be initialized
        self.assertIsNone(coordinator._feedback_loop)

    def test_coordinator_feedback_loop_enabled(self):
        """Coordinator initializes FeedbackLoop when enabled."""
        with patch("scripts.feedback_loop.FeedbackLoop") as mock_feedback_class:
            config = PipelineConfig(feedback_enabled=True)
            coordinator = AgentCoordinator(config)

            coordinator.start()

            # Should attempt to initialize feedback loop
            # (Will fail if module not found, but we're mocking it)
            mock_feedback_class.assert_called_once()


class TestAgentCoordinatorThreadSafety(unittest.TestCase):
    """Test thread-safety of AgentCoordinator methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_runtime_patcher = patch("scripts.agent_coordinator.AgentRuntime")
        self.mock_runtime_class = self.mock_runtime_patcher.start()
        self.mock_runtime = MagicMock()
        self.mock_runtime_class.return_value = self.mock_runtime

        self.mock_event_bus = MagicMock()
        self.mock_runtime.event_bus = self.mock_event_bus
        self.mock_runtime.get_status.return_value = []
        self.mock_runtime.start.return_value = ["agent1"]

    def tearDown(self):
        """Clean up patches."""
        self.mock_runtime_patcher.stop()

    def test_coordinator_concurrent_event_handlers(self):
        """Event handlers can be called concurrently without corruption."""
        coordinator = AgentCoordinator()
        coordinator.start()

        # Simulate concurrent event handler calls
        threads = []
        for i in range(10):
            event = SkillExtractedEvent(
                skill_id=f"skill-{i}",
                skill_name=f"skill-{i}",
                skill_data={"index": i},
                source_project="C:/TestProject",
                confidence=0.95,
            )
            t = threading.Thread(target=coordinator._on_skill_extracted, args=(event,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All events should be counted
        self.assertEqual(coordinator._current_cycle.skills_extracted, 10)

    def test_coordinator_concurrent_get_cycle_history(self):
        """get_cycle_history() is thread-safe."""
        coordinator = AgentCoordinator()

        # Populate history
        for i in range(50):
            coordinator._cycle_history.append(
                PipelineCycleResult(cycle_id=f"cycle-{i}")
            )

        # Concurrent reads
        results = []

        def read_history():
            results.append(coordinator.get_cycle_history(limit=10))

        threads = [threading.Thread(target=read_history) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should succeed and return correct data
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(len(result), 10)


if __name__ == "__main__":
    # Self-test block
    print("Running AgentCoordinator and PipelineConfig tests...\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineCycleResult))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentCoordinator))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentCoordinatorThreadSafety))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'=' * 70}")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"{'=' * 70}\n")

    sys.exit(0 if result.wasSuccessful() else 1)
