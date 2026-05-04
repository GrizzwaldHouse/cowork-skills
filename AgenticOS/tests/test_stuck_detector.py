# test_stuck_detector.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Unit tests for stuck_detector.py. Covers all six policy
#          branches: idle past threshold, idle within threshold, exact
#          loop, no loop, silent failure detected, silent failure not
#          detected. Pure functions => no fixtures needed.

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from AgenticOS.stuck_detector import (
    detect_silent_failure,
    is_looping,
    is_stuck,
)


# ---------------------------------------------------------------------------
# is_stuck
# ---------------------------------------------------------------------------

def test_is_stuck_when_idle_past_threshold():
    # 200 seconds ago vs. a 90-second threshold => stuck.
    now = datetime(2026, 4, 29, 12, 0, 0, tzinfo=timezone.utc)
    last_progress = now - timedelta(seconds=200)
    assert is_stuck(last_progress, now, threshold_s=90) is True


def test_is_not_stuck_within_threshold():
    # 30 seconds ago vs. a 90-second threshold => fine.
    now = datetime(2026, 4, 29, 12, 0, 0, tzinfo=timezone.utc)
    last_progress = now - timedelta(seconds=30)
    assert is_stuck(last_progress, now, threshold_s=90) is False


def test_is_stuck_returns_false_for_never_observed():
    # last_progress_at None means "no observations yet"; never stuck.
    now = datetime(2026, 4, 29, 12, 0, 0, tzinfo=timezone.utc)
    assert is_stuck(None, now, threshold_s=90) is False


def test_is_stuck_normalises_naive_datetimes():
    # Naive datetimes must not crash; they are coerced to UTC.
    now = datetime(2026, 4, 29, 12, 0, 0)
    last_progress = datetime(2026, 4, 29, 11, 58, 0)  # 2 minutes ago
    assert is_stuck(last_progress, now, threshold_s=90) is True


# ---------------------------------------------------------------------------
# is_looping
# ---------------------------------------------------------------------------

def test_is_looping_with_exact_repeat():
    # Five identical entries with default thresholds.
    timeline = [
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
    ]
    assert is_looping(timeline, window=5, threshold=5) is True


def test_is_not_looping_with_mixed_entries():
    # Four matching plus one different => below threshold.
    timeline = [
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "thinking",  "agent": "AGENT-01"},
    ]
    assert is_looping(timeline, window=5, threshold=5) is False


def test_is_looping_returns_false_for_short_history():
    # Fewer entries than the window means we cannot decide; not a loop.
    timeline = [{"kind": "tool_use", "agent": "AGENT-01"}]
    assert is_looping(timeline, window=5, threshold=5) is False


def test_is_looping_handles_non_dict_entries():
    # Garbage entries are skipped, do not crash.
    timeline = [
        "not a dict",
        {"kind": "tool_use", "agent": "AGENT-01"},
        {"kind": "tool_use", "agent": "AGENT-01"},
    ]
    # Window 3, threshold 2 -> two matching entries triggers True.
    assert is_looping(timeline, window=3, threshold=2) is True


def test_is_looping_zero_window_is_safe():
    # Defensive policy: window <= 0 cannot produce a loop classification.
    timeline = [{"kind": "x", "agent": "y"}] * 10
    assert is_looping(timeline, window=0, threshold=1) is False


# ---------------------------------------------------------------------------
# detect_silent_failure
# ---------------------------------------------------------------------------

def test_silent_failure_detected_when_in_progress_no_process():
    # The classic silent failure: mission says working, no process.
    assert detect_silent_failure("in_progress", has_running_process=False) is True


def test_silent_failure_not_detected_when_complete():
    # Done is done; no process is the expected post-state.
    assert (
        detect_silent_failure("complete", has_running_process=False) is False
    )


def test_silent_failure_not_detected_when_process_alive():
    # Mission says working, process is alive => healthy.
    assert detect_silent_failure("in_progress", has_running_process=True) is False


def test_silent_failure_recognises_alternative_status_aliases():
    # Cowork may emit other in-progress spellings; be permissive.
    for status in ("running", "active", "working"):
        assert detect_silent_failure(status, has_running_process=False) is True
