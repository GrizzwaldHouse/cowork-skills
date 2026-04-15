# test_feedback_loop.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for the self-improving feedback loop metrics system

import unittest
import sys
import tempfile
import shutil
import logging
from pathlib import Path

# Configure logging to prevent hang
logging.basicConfig(level=logging.WARNING)

sys.path.insert(0, "C:/ClaudeSkills")
from scripts.feedback_loop import FeedbackLoop, TrendReport, ImprovementTarget


class TestFeedbackLoop(unittest.TestCase):
    """Test suite for FeedbackLoop metrics tracking and trend analysis."""

    def setUp(self):
        """Create temporary directory for test metrics persistence."""
        self.temp_dir = tempfile.mkdtemp()
        self.metrics_path = Path(self.temp_dir) / "test_metrics.json"
        self.config = {
            "feedback": {
                "metrics_path": str(self.metrics_path),
                "trend_window": 5,
                "rejection_rate_alert": 0.40,
                "auto_adjust_thresholds": False,
            }
        }

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_record_cycle(self):
        """Record a cycle dict and verify global metrics updated."""
        loop = FeedbackLoop(self.config)

        cycle_result = {
            "skills_extracted": 3,
            "skills_validated": 3,
            "skills_approved": 2,
            "skills_rejected": 1,
            "skills_refactored": 0,
            "skills_synced": 2,
            "refactor_failures": 0,
        }

        loop.record_cycle(cycle_result)

        summary = loop.get_summary()
        self.assertEqual(summary["global"]["total_cycles"], 1)
        self.assertEqual(summary["global"]["total_extracted"], 3)
        self.assertEqual(summary["global"]["total_validated"], 3)
        self.assertEqual(summary["global"]["total_approved"], 2)
        self.assertEqual(summary["global"]["total_rejected"], 1)
        self.assertEqual(summary["global"]["total_synced"], 2)
        # Rejection rate: 1 rejected / (2 approved + 1 rejected) = 0.333...
        self.assertAlmostEqual(summary["global"]["rejection_rate"], 1 / 3, places=2)

    def test_record_skill_score(self):
        """Record score and verify skill_metrics populated."""
        loop = FeedbackLoop(self.config)

        loop.record_skill_score(
            skill_id="test-skill-1",
            skill_name="Test Skill One",
            score=0.87,
            disposition="approved",
        )

        summary = loop.get_summary()
        self.assertEqual(summary["skills_tracked"], 1)
        self.assertAlmostEqual(summary["global"]["avg_quality_score"], 0.87, places=2)

        # Verify trend exists
        trend = loop.get_trend("test-skill-1")
        self.assertEqual(trend.skill_id, "test-skill-1")
        self.assertAlmostEqual(trend.avg_score, 0.87, places=2)
        self.assertEqual(trend.cycles_tracked, 1)

    def test_trend_improving(self):
        """Record ascending scores and verify direction='improving'."""
        loop = FeedbackLoop(self.config)
        scores = [0.60, 0.65, 0.70, 0.75, 0.80]

        for idx, score in enumerate(scores):
            loop.record_skill_score(
                skill_id="skill-improving",
                skill_name="Improving Skill",
                score=score,
                disposition="approved",
            )

        trend = loop.get_trend("skill-improving")
        self.assertEqual(trend.direction, "improving")
        self.assertGreater(trend.avg_delta, 0.01)
        self.assertEqual(trend.cycles_tracked, 5)

    def test_trend_declining(self):
        """Record descending scores and verify direction='declining'."""
        loop = FeedbackLoop(self.config)
        scores = [0.80, 0.75, 0.70, 0.65, 0.60]

        for score in scores:
            loop.record_skill_score(
                skill_id="skill-declining",
                skill_name="Declining Skill",
                score=score,
                disposition="rejected",
            )

        trend = loop.get_trend("skill-declining")
        self.assertEqual(trend.direction, "declining")
        self.assertLess(trend.avg_delta, -0.01)
        self.assertEqual(trend.cycles_tracked, 5)

    def test_trend_stable(self):
        """Record same scores and verify direction='stable'."""
        loop = FeedbackLoop(self.config)
        scores = [0.75, 0.75, 0.76, 0.75, 0.75]

        for score in scores:
            loop.record_skill_score(
                skill_id="skill-stable",
                skill_name="Stable Skill",
                score=score,
                disposition="approved",
            )

        trend = loop.get_trend("skill-stable")
        self.assertEqual(trend.direction, "stable")
        # avg_delta should be very close to 0
        self.assertGreaterEqual(trend.avg_delta, -0.01)
        self.assertLessEqual(trend.avg_delta, 0.01)
        self.assertEqual(trend.cycles_tracked, 5)

    def test_trend_no_data(self):
        """Unknown skill_id returns direction='none'."""
        loop = FeedbackLoop(self.config)

        trend = loop.get_trend("nonexistent-skill")
        self.assertEqual(trend.skill_id, "nonexistent-skill")
        self.assertEqual(trend.direction, "none")
        self.assertEqual(trend.avg_score, 0.0)
        self.assertEqual(trend.cycles_tracked, 0)
        self.assertEqual(len(trend.score_history), 0)

    def test_weak_patterns_high_rejection(self):
        """Set rejection_rate > alert threshold and verify pattern identified."""
        loop = FeedbackLoop(self.config)

        # Create 10 decisions: 7 rejected, 3 approved = 70% rejection rate
        cycle_result = {
            "skills_extracted": 10,
            "skills_validated": 10,
            "skills_approved": 3,
            "skills_rejected": 7,
            "skills_refactored": 0,
            "skills_synced": 3,
            "refactor_failures": 0,
        }
        loop.record_cycle(cycle_result)

        patterns = loop.identify_weak_patterns()
        # Should contain pattern about high rejection rate (70% > 40% threshold)
        self.assertTrue(any("High rejection rate" in p for p in patterns))

    def test_weak_patterns_persistent_rejection(self):
        """Skill with many rejections and 0 approvals identified as weak pattern."""
        loop = FeedbackLoop(self.config)

        # Record 5 rejections, 0 approvals for same skill
        for i in range(5):
            loop.record_skill_score(
                skill_id="bad-skill",
                skill_name="Persistently Bad Skill",
                score=0.45,
                disposition="rejected",
            )

        patterns = loop.identify_weak_patterns()
        # Should identify skill with >3 rejections and 0 approvals
        self.assertTrue(
            any("Persistently rejected" in p and "Persistently Bad Skill" in p for p in patterns)
        )

    def test_improvement_targets(self):
        """Skills below 0.85 generate targets with correct priorities."""
        loop = FeedbackLoop(self.config)

        # Priority 1: below 0.5
        loop.record_skill_score("skill-p1", "Priority 1 Skill", 0.45, "rejected")

        # Priority 2: 0.5-0.7
        loop.record_skill_score("skill-p2", "Priority 2 Skill", 0.65, "needs_refactor")

        # Priority 3: 0.7-0.85
        loop.record_skill_score("skill-p3", "Priority 3 Skill", 0.80, "approved")

        # No target: >= 0.85
        loop.record_skill_score("skill-ok", "Good Skill", 0.90, "approved")

        targets = loop.generate_improvement_targets()

        # Should have 3 targets (skill-ok excluded)
        self.assertEqual(len(targets), 3)

        # Verify sorted by priority, then score
        self.assertEqual(targets[0].skill_id, "skill-p1")
        self.assertEqual(targets[0].priority, 1)
        self.assertIn("Below minimum quality", targets[0].reason)

        self.assertEqual(targets[1].skill_id, "skill-p2")
        self.assertEqual(targets[1].priority, 2)
        self.assertIn("Below reusability", targets[1].reason)

        self.assertEqual(targets[2].skill_id, "skill-p3")
        self.assertEqual(targets[2].priority, 3)
        self.assertIn("Close to approval", targets[2].reason)

        # All targets should have target_score 0.85
        for target in targets:
            self.assertEqual(target.target_score, 0.85)

    def test_adjust_thresholds_disabled(self):
        """auto_adjust=False returns None."""
        loop = FeedbackLoop(self.config)

        # Record enough cycles to normally trigger adjustment
        for i in range(15):
            loop.record_cycle({
                "skills_extracted": 1,
                "skills_validated": 1,
                "skills_approved": 1,
                "skills_rejected": 0,
                "skills_refactored": 0,
                "skills_synced": 1,
                "refactor_failures": 0,
            })
            loop.record_skill_score(f"skill-{i}", f"Skill {i}", 0.95, "approved")

        # auto_adjust is False in config
        result = loop.adjust_thresholds()
        self.assertIsNone(result)

    def test_get_summary(self):
        """Verify summary structure contains expected keys."""
        loop = FeedbackLoop(self.config)

        loop.record_cycle({
            "skills_extracted": 2,
            "skills_validated": 2,
            "skills_approved": 1,
            "skills_rejected": 1,
            "skills_refactored": 0,
            "skills_synced": 1,
            "refactor_failures": 0,
        })

        loop.record_skill_score("skill-a", "Skill A", 0.70, "needs_refactor")

        summary = loop.get_summary()

        # Verify structure
        self.assertIn("global", summary)
        self.assertIn("skills_tracked", summary)
        self.assertIn("weak_patterns", summary)
        self.assertIn("improvement_targets", summary)

        self.assertEqual(summary["skills_tracked"], 1)
        self.assertIsInstance(summary["global"], dict)
        self.assertIsInstance(summary["weak_patterns"], list)
        self.assertIsInstance(summary["improvement_targets"], list)

        # Global should have expected fields
        self.assertIn("total_cycles", summary["global"])
        self.assertIn("rejection_rate", summary["global"])
        self.assertIn("avg_quality_score", summary["global"])

    def test_persistence_roundtrip(self):
        """Record data, create new FeedbackLoop, verify data loaded."""
        # First loop: record data
        loop1 = FeedbackLoop(self.config)

        loop1.record_cycle({
            "skills_extracted": 5,
            "skills_validated": 5,
            "skills_approved": 4,
            "skills_rejected": 1,
            "skills_refactored": 0,
            "skills_synced": 4,
            "refactor_failures": 0,
        })

        loop1.record_skill_score("persistent-skill", "Persistent Skill", 0.88, "approved")
        loop1.record_skill_score("persistent-skill", "Persistent Skill", 0.90, "approved")

        summary1 = loop1.get_summary()

        # Create new loop with same metrics path
        loop2 = FeedbackLoop(self.config)
        summary2 = loop2.get_summary()

        # Verify persistence
        self.assertEqual(summary1["global"]["total_cycles"], summary2["global"]["total_cycles"])
        self.assertEqual(summary1["skills_tracked"], summary2["skills_tracked"])
        self.assertEqual(
            summary1["global"]["total_extracted"],
            summary2["global"]["total_extracted"],
        )

        # Verify skill history persisted
        trend = loop2.get_trend("persistent-skill")
        self.assertEqual(trend.cycles_tracked, 2)
        self.assertEqual(len(trend.score_history), 2)
        self.assertAlmostEqual(trend.score_history[0], 0.88, places=2)
        self.assertAlmostEqual(trend.score_history[1], 0.90, places=2)


if __name__ == "__main__":
    # Run tests with verbose output
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFeedbackLoop)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
