# test_session_observer.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Comprehensive unit tests for session_observer module

"""
Unit tests for the SessionObserver class.

Covers signal classification, project identification, session lifecycle,
activity thresholds, idle detection, and artifact tracking.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

# Ensure scripts directory is on sys.path for imports
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from session_observer import SessionObserver, SessionEvent, SessionSignal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_config(
    watched_projects: list[str] | None = None,
    idle_timeout: int = 300,
    min_activity: int = 3,
) -> dict:
    """Build a minimal config dict for SessionObserver."""
    return {
        "watched_projects": watched_projects or ["C:/Projects/alpha", "C:/Projects/beta"],
        "session_detection": {
            "idle_timeout_seconds": idle_timeout,
            "min_activity_events": min_activity,
        },
    }


@pytest.fixture()
def observer() -> SessionObserver:
    """Return a SessionObserver with default test config."""
    return SessionObserver(_make_config())


# ---------------------------------------------------------------------------
# Signal classification tests
# ---------------------------------------------------------------------------

class TestSignalClassification:
    """Test _classify_signal via observe_event."""

    def test_plan_created(self, observer: SessionObserver) -> None:
        """Creating a plan file emits PLAN_CREATED."""
        event = observer.observe_event(
            "created", "C:/Projects/alpha/.claude/plans/fix-auth.md",
        )
        assert event is not None
        assert event.signal == SessionSignal.PLAN_CREATED

    def test_plan_modified(self, observer: SessionObserver) -> None:
        """Modifying a plan file emits SESSION_ACTIVE."""
        event = observer.observe_event(
            "modified", "C:/Projects/alpha/.claude/plans/fix-auth.md",
        )
        assert event is not None
        assert event.signal == SessionSignal.SESSION_ACTIVE

    def test_memory_updated(self, observer: SessionObserver) -> None:
        """Changing MEMORY.md emits MEMORY_UPDATED."""
        event = observer.observe_event(
            "modified", "C:/Projects/alpha/MEMORY.md",
        )
        assert event is not None
        assert event.signal == SessionSignal.MEMORY_UPDATED

    def test_code_committed(self, observer: SessionObserver) -> None:
        """Changing .git/COMMIT_EDITMSG emits CODE_COMMITTED."""
        event = observer.observe_event(
            "modified", "C:/Projects/alpha/.git/COMMIT_EDITMSG",
        )
        assert event is not None
        assert event.signal == SessionSignal.CODE_COMMITTED

    def test_claude_md_returns_session_active(self, observer: SessionObserver) -> None:
        """Changing CLAUDE.md emits SESSION_ACTIVE."""
        event = observer.observe_event(
            "modified", "C:/Projects/alpha/CLAUDE.md",
        )
        assert event is not None
        assert event.signal == SessionSignal.SESSION_ACTIVE


# ---------------------------------------------------------------------------
# Project identification tests
# ---------------------------------------------------------------------------

class TestProjectIdentification:
    """Test _identify_project behavior."""

    def test_file_in_watched_project(self, observer: SessionObserver) -> None:
        """Files inside a watched project are identified correctly."""
        event = observer.observe_event(
            "modified", "C:/Projects/alpha/MEMORY.md",
        )
        assert event is not None
        assert event.project == "C:/Projects/alpha"

    def test_file_in_second_project(self, observer: SessionObserver) -> None:
        """Files in the second watched project are identified correctly."""
        event = observer.observe_event(
            "modified", "C:/Projects/beta/MEMORY.md",
        )
        assert event is not None
        assert event.project == "C:/Projects/beta"

    def test_file_outside_all_projects_returns_none(self, observer: SessionObserver) -> None:
        """Files outside all watched projects return None."""
        event = observer.observe_event(
            "modified", "C:/Other/project/file.py",
        )
        assert event is None

    def test_backslash_paths_normalized(self) -> None:
        """Windows backslash paths are normalized for matching."""
        obs = SessionObserver(_make_config(watched_projects=["C:/Projects/alpha"]))
        event = obs.observe_event(
            "modified", "C:\\Projects\\alpha\\MEMORY.md",
        )
        assert event is not None
        assert event.signal == SessionSignal.MEMORY_UPDATED


# ---------------------------------------------------------------------------
# Session lifecycle tests
# ---------------------------------------------------------------------------

class TestSessionLifecycle:
    """Test session start -> active -> idle -> end flow."""

    def test_first_event_creates_session(self, observer: SessionObserver) -> None:
        """The first event for a project creates a session."""
        observer.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        sessions = observer.get_active_sessions()
        assert len(sessions) == 1
        assert sessions[0]["project"] == "C:/Projects/alpha"

    def test_session_tracks_event_count(self, observer: SessionObserver) -> None:
        """Session event_count increments with each event."""
        for i in range(5):
            observer.observe_event("modified", f"C:/Projects/alpha/file{i}.py")
        sessions = observer.get_active_sessions()
        assert sessions[0]["event_count"] == 5

    def test_active_status_within_timeout(self, observer: SessionObserver) -> None:
        """Sessions within idle_timeout report as active."""
        observer.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        sessions = observer.get_active_sessions()
        assert sessions[0]["status"] == "active"

    def test_idle_status_after_timeout(self) -> None:
        """Sessions past idle_timeout report as idle."""
        obs = SessionObserver(_make_config(idle_timeout=0))
        obs.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        # Let the clock tick past the 0-second timeout
        time.sleep(0.05)
        sessions = obs.get_active_sessions()
        assert sessions[0]["status"] == "idle"


# ---------------------------------------------------------------------------
# Activity threshold tests
# ---------------------------------------------------------------------------

class TestActivityThreshold:
    """Test minimum activity event threshold for SESSION_ACTIVE signals."""

    def test_below_threshold_returns_none(self) -> None:
        """Generic events below min_activity threshold return None."""
        obs = SessionObserver(_make_config(min_activity=3))
        # Events 1 and 2 are below threshold
        result1 = obs.observe_event("modified", "C:/Projects/alpha/src/a.py")
        result2 = obs.observe_event("modified", "C:/Projects/alpha/src/b.py")
        assert result1 is None
        assert result2 is None

    def test_at_threshold_returns_session_active(self) -> None:
        """Reaching min_activity threshold emits SESSION_ACTIVE."""
        obs = SessionObserver(_make_config(min_activity=3))
        obs.observe_event("modified", "C:/Projects/alpha/src/a.py")
        obs.observe_event("modified", "C:/Projects/alpha/src/b.py")
        result = obs.observe_event("modified", "C:/Projects/alpha/src/c.py")
        assert result is not None
        assert result.signal == SessionSignal.SESSION_ACTIVE

    def test_above_threshold_returns_none(self) -> None:
        """Events beyond the threshold return None (only fires once at threshold)."""
        obs = SessionObserver(_make_config(min_activity=3))
        for i in range(3):
            obs.observe_event("modified", f"C:/Projects/alpha/src/{i}.py")
        # Fourth event is above threshold -- no second SESSION_ACTIVE
        result = obs.observe_event("modified", "C:/Projects/alpha/src/d.py")
        assert result is None


# ---------------------------------------------------------------------------
# Idle timeout detection tests
# ---------------------------------------------------------------------------

class TestIdleDetection:
    """Test check_idle_sessions behavior."""

    def test_no_idle_events_within_timeout(self, observer: SessionObserver) -> None:
        """check_idle_sessions returns empty list when sessions are active."""
        observer.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        idle = observer.check_idle_sessions()
        assert idle == []

    def test_idle_event_emitted_after_timeout(self) -> None:
        """check_idle_sessions emits SESSION_END after idle_timeout."""
        obs = SessionObserver(_make_config(idle_timeout=0))
        obs.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        time.sleep(0.05)
        idle = obs.check_idle_sessions()
        assert len(idle) == 1
        assert idle[0].signal == SessionSignal.SESSION_END
        assert idle[0].project == "C:/Projects/alpha"

    def test_idle_event_not_emitted_twice(self) -> None:
        """check_idle_sessions does not re-emit SESSION_END for same session."""
        obs = SessionObserver(_make_config(idle_timeout=0))
        obs.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        time.sleep(0.05)
        first = obs.check_idle_sessions()
        assert len(first) == 1
        second = obs.check_idle_sessions()
        assert len(second) == 0

    def test_idle_flag_reset_on_new_activity(self) -> None:
        """New activity resets idle flag so SESSION_END can fire again."""
        obs = SessionObserver(_make_config(idle_timeout=0, min_activity=100))
        obs.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        time.sleep(0.05)
        obs.check_idle_sessions()  # Marks idle_emitted
        # New activity resets the flag
        obs.observe_event("modified", "C:/Projects/alpha/src/new.py")
        time.sleep(0.05)
        idle = obs.check_idle_sessions()
        assert len(idle) == 1

    def test_idle_event_contains_duration(self) -> None:
        """SESSION_END details include duration_seconds."""
        obs = SessionObserver(_make_config(idle_timeout=0))
        obs.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        time.sleep(0.05)
        idle = obs.check_idle_sessions()
        assert "duration_seconds" in idle[0].details
        assert idle[0].details["duration_seconds"] >= 0


# ---------------------------------------------------------------------------
# Artifact tracking tests
# ---------------------------------------------------------------------------

class TestArtifacts:
    """Test get_session_artifacts behavior."""

    def test_artifacts_tracked(self, observer: SessionObserver) -> None:
        """Artifacts are collected for each session."""
        observer.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        observer.observe_event("modified", "C:/Projects/alpha/src/main.py")
        artifacts = observer.get_session_artifacts("C:/Projects/alpha")
        assert len(artifacts) == 2
        assert Path("C:/Projects/alpha/MEMORY.md") in artifacts
        assert Path("C:/Projects/alpha/src/main.py") in artifacts

    def test_artifacts_empty_for_unknown_project(self, observer: SessionObserver) -> None:
        """get_session_artifacts returns empty list for unknown projects."""
        artifacts = observer.get_session_artifacts("C:/Unknown/project")
        assert artifacts == []

    def test_artifacts_are_path_objects(self, observer: SessionObserver) -> None:
        """get_session_artifacts returns Path objects."""
        observer.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        artifacts = observer.get_session_artifacts("C:/Projects/alpha")
        assert all(isinstance(a, Path) for a in artifacts)


# ---------------------------------------------------------------------------
# SessionEvent tests
# ---------------------------------------------------------------------------

class TestSessionEvent:
    """Test SessionEvent dataclass behavior."""

    def test_to_dict(self) -> None:
        """to_dict serializes all fields correctly."""
        event = SessionEvent(
            signal=SessionSignal.PLAN_CREATED,
            project="C:/Projects/alpha",
            timestamp="2026-03-23T12:00:00+00:00",
            artifacts=["file1.md", "file2.py"],
            details={"event_type": "created"},
        )
        d = event.to_dict()
        assert d["signal"] == "plan_created"
        assert d["project"] == "C:/Projects/alpha"
        assert d["artifacts"] == ["file1.md", "file2.py"]
        assert d["details"] == {"event_type": "created"}

    def test_frozen_immutability(self) -> None:
        """SessionEvent is frozen and cannot be mutated."""
        event = SessionEvent(
            signal=SessionSignal.SESSION_START,
            project="test",
            timestamp="now",
            artifacts=[],
            details={},
        )
        with pytest.raises(AttributeError):
            event.signal = SessionSignal.SESSION_END  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Multiple projects tests
# ---------------------------------------------------------------------------

class TestMultipleProjects:
    """Test observer with multiple watched projects."""

    def test_separate_sessions_per_project(self, observer: SessionObserver) -> None:
        """Each project gets its own session."""
        observer.observe_event("modified", "C:/Projects/alpha/MEMORY.md")
        observer.observe_event("modified", "C:/Projects/beta/MEMORY.md")
        sessions = observer.get_active_sessions()
        projects = {s["project"] for s in sessions}
        assert projects == {"C:/Projects/alpha", "C:/Projects/beta"}

    def test_artifacts_isolated_per_project(self, observer: SessionObserver) -> None:
        """Artifacts are tracked separately per project."""
        observer.observe_event("modified", "C:/Projects/alpha/a.py")
        observer.observe_event("modified", "C:/Projects/beta/b.py")
        alpha_artifacts = observer.get_session_artifacts("C:/Projects/alpha")
        beta_artifacts = observer.get_session_artifacts("C:/Projects/beta")
        assert len(alpha_artifacts) == 1
        assert len(beta_artifacts) == 1
        assert Path("C:/Projects/alpha/a.py") in alpha_artifacts
        assert Path("C:/Projects/beta/b.py") in beta_artifacts
