"""
QThread wrapper for the watchdog file observer.

Runs the file-system watcher on a background thread and emits Qt signals
for every file event and security alert.  Reuses the existing
:class:`observer.SkillChangeHandler` and integrates the
:class:`SecurityEngine` for real-time threat scanning.

Usage::

    thread = WatcherThread(config)
    thread.file_event.connect(on_event)
    thread.security_alert.connect(on_alert)
    thread.start()
    ...
    thread.requestInterruption()
    thread.wait()
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("watcher_thread")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
CONFIG_PATH = BASE_DIR / "config" / "watch_config.json"


# ---------------------------------------------------------------------------
# Qt-aware event handler
# ---------------------------------------------------------------------------
class _QtChangeHandler(FileSystemEventHandler):
    """Watchdog handler that emits events through a Qt signal bridge.

    Parameters
    ----------
    signal_bridge:
        The :class:`WatcherThread` whose signals should be emitted.
    ignored_patterns:
        Patterns (directory names or ``*.ext`` globs) to ignore.
    enabled_skills:
        If non-empty, only process paths containing one of these names.
    sync_interval:
        Minimum seconds between events for the same path (throttle).
    """

    def __init__(
        self,
        signal_bridge: WatcherThread,
        ignored_patterns: list[str],
        enabled_skills: list[str],
        sync_interval: float,
    ) -> None:
        super().__init__()
        self._bridge = signal_bridge
        self._ignored_patterns = ignored_patterns
        self._enabled_skills = enabled_skills
        self._sync_interval = sync_interval
        self._last_event_time: dict[str, float] = {}

    # -- filtering --------------------------------------------------------

    def _should_process(self, path: Path) -> bool:
        path_str = str(path)

        for pattern in self._ignored_patterns:
            if pattern in path.parts:
                return False
            if pattern.startswith("*") and path_str.endswith(pattern[1:]):
                return False

        if self._enabled_skills:
            if not any(part in self._enabled_skills for part in path.parts):
                return False

        now = time.monotonic()
        key = str(path)
        last = self._last_event_time.get(key, 0.0)
        if now - last < self._sync_interval:
            return False
        self._last_event_time[key] = now
        return True

    # -- event dispatch ---------------------------------------------------

    def _handle(self, event: FileSystemEvent, event_type: str) -> None:
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if not self._should_process(file_path):
            return

        payload: dict[str, Any] = {
            "event_type": event_type,
            "path": str(file_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Emit the file event (thread-safe via Qt signal mechanism)
        self._bridge.file_event.emit(payload)

        # Notify the broadcaster (best-effort)
        try:
            from broadcaster import broadcast_change
            broadcast_change(event_type, str(file_path))
        except Exception:
            pass

        # Run security scan
        self._bridge._scan_event(event_type, str(file_path))

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle(event, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        self._handle(event, "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._handle(event, "deleted")

    def on_moved(self, event: FileSystemEvent) -> None:
        self._handle(event, "moved")


# ---------------------------------------------------------------------------
# Watcher thread
# ---------------------------------------------------------------------------
class WatcherThread(QThread):
    """Background thread that runs the watchdog file observer.

    Signals
    -------
    file_event(dict):
        Emitted for every file-system event. Dict keys: ``event_type``,
        ``path``, ``timestamp``.
    security_alert(dict):
        Emitted when the security engine flags an event. Contains the
        alert serialised via ``SecurityAlert.to_dict()``.
    error_occurred(str):
        Emitted when an unrecoverable error occurs in the thread.
    started_watching():
        Emitted once the observer is running.
    stopped_watching():
        Emitted after the observer has been shut down.
    """

    file_event = pyqtSignal(dict)
    security_alert = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    started_watching = pyqtSignal()
    stopped_watching = pyqtSignal()

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        parent: Any | None = None,
    ) -> None:
        super().__init__(parent)

        if config is None:
            config = self._load_config()
        self._config = config

        self._security_engine: Any = None
        self._init_security_engine()

    # -- config -----------------------------------------------------------

    @staticmethod
    def _load_config() -> dict[str, Any]:
        """Load watch configuration from the standard config path."""
        import json

        if CONFIG_PATH.exists():
            try:
                with CONFIG_PATH.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception as exc:
                logger.warning("Could not read config: %s", exc)

        return {
            "watched_paths": [str(BASE_DIR)],
            "ignored_patterns": [
                "__pycache__", ".git", "*.pyc", "backups", "logs", "dist",
            ],
            "sync_interval": 5,
            "enabled_skills": [],
        }

    # -- security engine --------------------------------------------------

    def _init_security_engine(self) -> None:
        """Lazily initialise the security engine."""
        try:
            from gui.security_engine import SecurityEngine
            self._security_engine = SecurityEngine()
        except Exception as exc:
            logger.warning("SecurityEngine not available: %s", exc)
            self._security_engine = None

    def _scan_event(self, event_type: str, file_path: str) -> None:
        """Run the security engine scan and emit an alert if needed."""
        if self._security_engine is None:
            return
        try:
            alert = self._security_engine.scan_event(event_type, file_path)
            if alert is not None:
                self.security_alert.emit(alert.to_dict())
        except Exception as exc:
            logger.debug("Security scan error: %s", exc)

    # -- thread run -------------------------------------------------------

    def run(self) -> None:
        """Thread entry point -- runs the watchdog observer loop."""
        watched_paths: list[str] = self._config.get(
            "watched_paths", [str(BASE_DIR)],
        )
        ignored: list[str] = self._config.get("ignored_patterns", [])
        interval: float = float(self._config.get("sync_interval", 5))
        skills: list[str] = self._config.get("enabled_skills", [])

        handler = _QtChangeHandler(
            signal_bridge=self,
            ignored_patterns=ignored,
            enabled_skills=skills,
            sync_interval=interval,
        )

        observer = Observer()

        scheduled = 0
        for dir_str in watched_paths:
            dir_path = Path(dir_str)
            if dir_path.exists():
                observer.schedule(handler, str(dir_path), recursive=True)
                scheduled += 1
                logger.info("Watching: %s", dir_path)
            else:
                logger.warning("Skipping non-existent path: %s", dir_path)

        if scheduled == 0:
            self.error_occurred.emit("No valid watched paths configured.")
            return

        try:
            observer.start()
        except Exception as exc:
            self.error_occurred.emit(f"Observer failed to start: {exc}")
            return

        self.started_watching.emit()
        logger.info("Watcher thread running (%d dirs).", scheduled)

        # Poll for interruption request
        try:
            while not self.isInterruptionRequested():
                time.sleep(0.5)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            observer.stop()
            observer.join(timeout=5)
            self.stopped_watching.emit()
            logger.info("Watcher thread stopped.")
