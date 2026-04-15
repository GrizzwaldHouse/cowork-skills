# Minimal test to isolate the hang
import sys
import tempfile
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(message)s')

sys.path.insert(0, "C:/ClaudeSkills")

print("Starting minimal test...")

temp_dir = tempfile.mkdtemp()
metrics_path = Path(temp_dir) / "test_metrics.json"

print(f"Temp dir: {temp_dir}")
print(f"Metrics path: {metrics_path}")

config = {
    "feedback": {
        "metrics_path": str(metrics_path),
        "trend_window": 5,
        "rejection_rate_alert": 0.40,
        "auto_adjust_thresholds": False,
    }
}

print("Creating FeedbackLoop...")
from scripts.feedback_loop import FeedbackLoop

loop = FeedbackLoop(config)
print("FeedbackLoop created successfully")

print("Recording cycle...")
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
print("Cycle recorded successfully")

print("Getting summary...")
summary = loop.get_summary()
print(f"Summary: {summary}")

print("Test completed successfully!")
