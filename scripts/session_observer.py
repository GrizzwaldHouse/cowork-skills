# session_observer.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Detect Claude Code session activity from file system events for the intelligence pipeline

"""
Session observer for the OwlWatcher intelligence pipeline.

Detects Claude Code session activity from file system events, tracks active
sessions per project, and emits structured ``SessionEvent`` objects for
downstream processing by the QuadSkill engine.

Mirrors the ``SecurityEngine.scan_event()`` pattern: a single ``observe_event``
entry point classifies file changes into session signals.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from log_config import configure_logging

configure_logging()
logger = logging.getLogger("session_observer")

BASE_DIR = Path("C:/ClaudeSkills")
DATA_DIR = BASE_DIR / "data" / "sessions"


class SessionSignal(str, Enum):
    """Signals emitted by the session observer."""

    SESSION_START = "session_start"
    SESSION_ACTIVE = "session_active"
    SESSION_IDLE = "session_idle"
    SESSION_END = "session_end"
    PLAN_CREATED = "plan_created"
    SKILL_USED = "skill_used"
    MEMORY_UPDATED = "memory_updated"
    CODE_COMMITTED = "code_committed"


@dataclass(frozen=True)
class SessionEvent:
    """Immutable record of a session-relevant event."""

    signal: SessionSignal
    project: str
    timestamp: str
    artifacts: list[str]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "signal": self.signal.value,
            "project": self.project,
            "timestamp": self.timestamp,
            "artifacts": list(self.artifacts),
            "details": self.details,
        }


class SessionObserver:
    """Detects Claude Code session activity from file system events.

    Watches for:
    - ``.claude/plans/*.md`` creation/modification -> SESSION_START / PLAN_CREATED
    - ``CLAUDE.md`` / ``MEMORY.md`` changes -> MEMORY_UPDATED
    - ``.git/COMMIT_EDITMSG`` changes -> CODE_COMMITTED
    - Rapid file changes in watched project dirs -> SESSION_ACTIVE
    - No events for ``idle_timeout_seconds`` -> SESSION_IDLE
    """

    def __init__(self, config: dict) -> None:
        session_cfg = config.get("session_detection", {})
        self._idle_timeout: int = session_cfg.get("idle_timeout_seconds", 300)
        self._min_activity: int = session_cfg.get("min_activity_events", 3)
        self._watched_projects: list[str] = config.get("watched_projects", [])

        # project -> {"start_time", "start_ts", "last_event", "event_count", "artifacts", "idle_emitted"}
        self._sessions: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe_event(self, event_type: str, file_path: str) -> SessionEvent | None:
        """Process a file event and return a ``SessionEvent`` if relevant.

        Called from the watcher pipeline for every file change.
        Returns ``None`` if the event is not session-relevant.
        """
        path = Path(file_path)
        project = self._identify_project(path)
        if project is None:
            return None

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        now_ts = now.timestamp()

        # Detect specific signal types
        signal = self._classify_signal(path, event_type)
        if signal is None:
            # Generic file activity -- track for session detection
            return self._track_activity(project, file_path, now_iso, now_ts)

        # Update session tracking
        session = self._ensure_session(project, now_iso, now_ts)
        session["last_event"] = now_ts
        session["event_count"] += 1
        session["artifacts"].append(file_path)
        session["idle_emitted"] = False

        self._log_session_event(signal, project, file_path, now_iso)

        return SessionEvent(
            signal=signal,
            project=project,
            timestamp=now_iso,
            artifacts=[file_path],
            details={"event_type": event_type, "file": str(path.name)},
        )

    def get_active_sessions(self) -> list[dict]:
        """Return all currently tracked sessions with status info."""
        now = time.time()
        result = []
        for project, session in self._sessions.items():
            elapsed = now - session["last_event"]
            status = "idle" if elapsed > self._idle_timeout else "active"
            result.append({
                "project": project,
                "status": status,
                "start_time": session["start_time"],
                "event_count": session["event_count"],
                "idle_seconds": int(elapsed),
            })
        return result

    def get_session_artifacts(self, project: str) -> list[Path]:
        """Return all artifacts collected for a project session."""
        session = self._sessions.get(project)
        if session is None:
            return []
        return [Path(a) for a in session.get("artifacts", [])]

    def check_idle_sessions(self) -> list[SessionEvent]:
        """Check for sessions that have gone idle.  Call periodically."""
        now = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        idle_events: list[SessionEvent] = []

        for project, session in list(self._sessions.items()):
            elapsed = now - session["last_event"]
            if elapsed > self._idle_timeout and not session.get("idle_emitted"):
                session["idle_emitted"] = True
                idle_events.append(SessionEvent(
                    signal=SessionSignal.SESSION_END,
                    project=project,
                    timestamp=now_iso,
                    artifacts=session.get("artifacts", []),
                    details={
                        "event_count": session["event_count"],
                        "duration_seconds": int(now - session.get("start_ts", now)),
                    },
                ))
        return idle_events

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _identify_project(self, path: Path) -> str | None:
        """Determine which watched project a file path belongs to."""
        path_str = str(path).replace("\\", "/")
        for project in self._watched_projects:
            proj_normalized = project.replace("\\", "/")
            if path_str.startswith(proj_normalized):
                return project
        return None

    def _classify_signal(self, path: Path, event_type: str) -> SessionSignal | None:
        """Classify a file event into a specific session signal."""
        path_str = str(path).replace("\\", "/")
        name = path.name.lower()

        # .claude/plans/*.md
        if ".claude/plans/" in path_str and name.endswith(".md"):
            return SessionSignal.PLAN_CREATED if event_type == "created" else SessionSignal.SESSION_ACTIVE

        # CLAUDE.md changes
        if name == "claude.md":
            return SessionSignal.SESSION_ACTIVE

        # MEMORY.md changes
        if name == "memory.md":
            return SessionSignal.MEMORY_UPDATED

        # Git commit
        if name == "commit_editmsg" and ".git" in path_str.lower():
            return SessionSignal.CODE_COMMITTED

        return None

    def _track_activity(
        self, project: str, file_path: str, now_iso: str, now_ts: float,
    ) -> SessionEvent | None:
        """Track generic file activity and return SESSION_ACTIVE if threshold met."""
        session = self._ensure_session(project, now_iso, now_ts)
        session["last_event"] = now_ts
        session["event_count"] += 1
        session["artifacts"].append(file_path)
        session["idle_emitted"] = False  # Reset idle flag on new activity

        if session["event_count"] == self._min_activity:
            return SessionEvent(
                signal=SessionSignal.SESSION_ACTIVE,
                project=project,
                timestamp=now_iso,
                artifacts=session["artifacts"][-self._min_activity:],
                details={"event_count": session["event_count"]},
            )
        return None

    def _ensure_session(self, project: str, now_iso: str, now_ts: float) -> dict:
        """Get or create a session for the given project."""
        if project not in self._sessions:
            self._sessions[project] = {
                "start_time": now_iso,
                "start_ts": now_ts,
                "last_event": now_ts,
                "event_count": 0,
                "artifacts": [],
                "idle_emitted": False,
            }
            self._log_session_event(SessionSignal.SESSION_START, project, "", now_iso)
        return self._sessions[project]

    def _log_session_event(
        self, signal: SessionSignal, project: str, file_path: str, timestamp: str,
    ) -> None:
        """Log session event to ``data/sessions/`` directory."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        log_file = DATA_DIR / "session_log.jsonl"
        entry = {
            "signal": signal.value,
            "project": project,
            "file": file_path,
            "timestamp": timestamp,
        }
        try:
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except OSError as exc:
            logger.warning("Failed to log session event: %s", exc)
