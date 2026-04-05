# test_improvement_tracker.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Tests for improvement tracking and refactor cooldown

import pytest
import time
from scripts.improvement_tracker import (
    ImprovementTrendTracker,
    RefactorCooldownTracker,
    ImprovementRecord,
)


@pytest.fixture
def trend_tracker(tmp_path, monkeypatch):
    """Tracker with temp data directory."""
    import scripts.improvement_tracker as mod
    monkeypatch.setattr(mod, "_DATA_DIR", tmp_path)
    return ImprovementTrendTracker({"improvement": {"regression_tolerance": 0.0}})


@pytest.fixture
def cooldown_tracker():
    """Cooldown tracker with 1-second cooldown for fast testing."""
    return RefactorCooldownTracker({
        "improvement": {"cooldown_seconds": 1, "max_consecutive_failures": 3}
    })


class TestImprovementTrendTracker:

    def test_record_and_get_best_score(self, trend_tracker):
        trend_tracker.record(ImprovementRecord(
            skill_id="s1", skill_name="test", previous_score=0.5,
            new_score=0.7, improved=True, iterations=3,
        ))
        assert trend_tracker.get_best_score("s1") == 0.7

    def test_best_score_monotonic(self, trend_tracker):
        trend_tracker.record(ImprovementRecord(
            skill_id="s1", skill_name="test", previous_score=0.5,
            new_score=0.8, improved=True, iterations=3,
        ))
        trend_tracker.record(ImprovementRecord(
            skill_id="s1", skill_name="test", previous_score=0.8,
            new_score=0.6, improved=False, iterations=1,
        ))
        assert trend_tracker.get_best_score("s1") == 0.8

    def test_regression_detected(self, trend_tracker):
        trend_tracker.record(ImprovementRecord(
            skill_id="s1", skill_name="test", previous_score=0.5,
            new_score=0.8, improved=True, iterations=3,
        ))
        assert trend_tracker.check_regression("s1", 0.7) is True
        assert trend_tracker.check_regression("s1", 0.8) is False
        assert trend_tracker.check_regression("s1", 0.9) is False

    def test_no_regression_for_unknown_skill(self, trend_tracker):
        assert trend_tracker.check_regression("unknown", 0.5) is False

    def test_history_persists(self, tmp_path, monkeypatch):
        import scripts.improvement_tracker as mod
        monkeypatch.setattr(mod, "_DATA_DIR", tmp_path)

        tracker1 = ImprovementTrendTracker()
        tracker1.record(ImprovementRecord(
            skill_id="s1", skill_name="test", previous_score=0.5,
            new_score=0.8, improved=True, iterations=3,
        ))

        tracker2 = ImprovementTrendTracker()
        assert tracker2.get_best_score("s1") == 0.8

    def test_trend_direction(self, trend_tracker):
        for score in [0.5, 0.6, 0.7, 0.8]:
            trend_tracker.record(ImprovementRecord(
                skill_id="s1", skill_name="test",
                previous_score=score - 0.1, new_score=score,
                improved=True, iterations=1,
            ))
        trend = trend_tracker.get_trend("s1")
        assert trend["direction"] == "improving"


class TestRefactorCooldownTracker:

    def test_not_on_cooldown_initially(self, cooldown_tracker):
        assert cooldown_tracker.is_on_cooldown("s1") is False

    def test_on_cooldown_after_failure(self, cooldown_tracker):
        cooldown_tracker.record_failure("s1")
        assert cooldown_tracker.is_on_cooldown("s1") is True

    def test_cooldown_expires(self, cooldown_tracker):
        cooldown_tracker.record_failure("s1")
        time.sleep(1.1)  # Wait for 1s cooldown to expire
        assert cooldown_tracker.is_on_cooldown("s1") is False

    def test_consecutive_failures_counted(self, cooldown_tracker):
        cooldown_tracker.record_failure("s1")
        cooldown_tracker.record_failure("s1")
        assert cooldown_tracker.get_failure_count("s1") == 2

    def test_success_resets_count(self, cooldown_tracker):
        cooldown_tracker.record_failure("s1")
        cooldown_tracker.record_failure("s1")
        cooldown_tracker.record_success("s1")
        assert cooldown_tracker.get_failure_count("s1") == 0

    def test_escalation_after_max_failures(self, cooldown_tracker):
        cooldown_tracker.record_failure("s1")
        cooldown_tracker.record_failure("s1")
        cooldown_tracker.record_failure("s1")
        assert cooldown_tracker.should_escalate("s1") is True

    def test_no_escalation_before_max(self, cooldown_tracker):
        cooldown_tracker.record_failure("s1")
        cooldown_tracker.record_failure("s1")
        assert cooldown_tracker.should_escalate("s1") is False
