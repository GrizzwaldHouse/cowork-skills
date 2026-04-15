# Quick validation script for feedback_loop tests
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, "C:/ClaudeSkills")
from scripts.feedback_loop import FeedbackLoop

def test_basic():
    """Quick smoke test."""
    temp_dir = tempfile.mkdtemp()
    try:
        metrics_path = Path(temp_dir) / "test_metrics.json"
        config = {
            "feedback": {
                "metrics_path": str(metrics_path),
                "trend_window": 5,
                "rejection_rate_alert": 0.40,
                "auto_adjust_thresholds": False,
            }
        }

        loop = FeedbackLoop(config)

        # Test record_cycle
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

        # Test record_skill_score
        loop.record_skill_score("test-skill", "Test Skill", 0.87, "approved")

        # Test get_trend
        trend = loop.get_trend("test-skill")
        assert trend.direction in ["improving", "declining", "stable", "none"]

        # Test get_summary
        summary = loop.get_summary()
        assert "global" in summary
        assert "skills_tracked" in summary

        print("All basic tests passed!")
        return True

    finally:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_basic()
