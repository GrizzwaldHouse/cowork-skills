# observer.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Real-time file system monitoring using watchdog to trigger sync operations on detected changes

"""
File watcher and observer for the Claude Skills system.

Monitors configured directories for file changes (create, modify, delete)
and logs events to sync_log.json. Triggers the broadcaster module when
changes are detected. Compares modification times to prevent overwriting
newer files during bidirectional sync.
"""

from __future__ import annotations

import json
import logging
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from config_manager import load_config
from log_config import configure_logging
from watcher_core import should_process

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
SYNC_LOG_PATH = BASE_DIR / "logs" / "sync_log.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()
logger = logging.getLogger("observer")


# ---------------------------------------------------------------------------
# Sync log persistence
# ---------------------------------------------------------------------------

def _read_sync_log() -> list[dict[str, Any]]:
    """Read the existing sync log entries from disk."""
    if not SYNC_LOG_PATH.exists():
        return []
    try:
        with SYNC_LOG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read sync log: %s", exc)
    return []


def _write_sync_log(entries: list[dict[str, Any]]) -> None:
    """Persist sync log entries to disk."""
    SYNC_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SYNC_LOG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, default=str)


def append_sync_entry(entry: dict[str, Any]) -> None:
    """Append a single entry to the sync log."""
    entries = _read_sync_log()
    entries.append(entry)
    _write_sync_log(entries)


# ---------------------------------------------------------------------------
# Modification-time comparison
# ---------------------------------------------------------------------------

def is_newer_than_logged(file_path: Path) -> bool:
    """Return True if *file_path* is newer than the last logged mtime.

    This prevents overwriting a newer version during bidirectional sync.
    If no prior log entry exists for the path, it is always considered new.
    """
    if not file_path.exists():
        return True  # deleted files are always "new" events

    current_mtime = file_path.stat().st_mtime
    entries = _read_sync_log()
    # Walk backwards to find the most recent entry for this path.
    for entry in reversed(entries):
        if entry.get("path") == str(file_path):
            last_mtime = entry.get("mtime")
            if last_mtime is not None and current_mtime <= last_mtime:
                logger.debug(
                    "Skipping %s: current mtime %.3f <= logged mtime %.3f",
                    file_path, current_mtime, last_mtime,
                )
                return False
            break
    return True


# ---------------------------------------------------------------------------
# Broadcaster integration
# ---------------------------------------------------------------------------

def _notify_broadcaster(event_type: str, file_path: str) -> None:
    """Forward change event to the broadcaster module, if available."""
    try:
        from broadcaster import broadcast_change  # type: ignore[import-not-found]
        broadcast_change(event_type, file_path)
    except ImportError:
        logger.debug("Broadcaster module not available; skipping notification")
    except Exception as exc:
        logger.warning("Broadcaster notification failed: %s", exc)


# ---------------------------------------------------------------------------
# Watchdog event handler
# ---------------------------------------------------------------------------

class SkillChangeHandler(FileSystemEventHandler):
    """Handles file-system events for watched directories."""

    def __init__(
        self,
        ignored_patterns: list[str],
        enabled_skills: list[str],
        sync_interval: float,
    ) -> None:
        super().__init__()
        self.ignored_patterns = ignored_patterns
        self.enabled_skills = enabled_skills
        self.sync_interval = sync_interval
        self._last_event_time: dict[str, float] = {}

    def _should_process(self, path: Path) -> bool:
        """Delegate to shared watcher_core filter."""
        return should_process(
            path,
            self.ignored_patterns,
            self.enabled_skills,
            self.sync_interval,
            self._last_event_time,
        )

    def _handle_event(self, event: FileSystemEvent, event_type: str) -> None:
        """Central handler called for every relevant event type."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if not self._should_process(file_path):
            return

        # Modification-time guard (skip if file hasn't actually changed).
        if event_type in ("created", "modified") and not is_newer_than_logged(file_path):
            return

        mtime: float | None = None
        if file_path.exists():
            mtime = file_path.stat().st_mtime

        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "path": str(file_path),
            "mtime": mtime,
        }

        logger.info("%s: %s", event_type.upper(), file_path)
        append_sync_entry(entry)
        _notify_broadcaster(event_type, str(file_path))

    # -- FileSystemEventHandler overrides ----------------------------------

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle_event(event, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        self._handle_event(event, "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._handle_event(event, "deleted")

    def on_moved(self, event: FileSystemEvent) -> None:
        self._handle_event(event, "moved")


# ---------------------------------------------------------------------------
# Observer lifecycle
# ---------------------------------------------------------------------------

_running = True


def _shutdown_handler(signum: int, frame: Any) -> None:
    """Signal handler for graceful shutdown."""
    global _running
    logger.info("Received signal %s, shutting down...", signum)
    _running = False


def start_observer(config: dict[str, Any] | None = None) -> None:
    """Start the file-system observer loop.

    Parameters
    ----------
    config:
        Optional pre-loaded config dict.  If *None*, the config is loaded
        from :data:`CONFIG_PATH`.
    """
    global _running
    _running = True

    if config is None:
        config = load_config()

    watched_paths: list[str] = config.get("watched_paths", [str(BASE_DIR)])
    ignored_patterns: list[str] = config.get("ignored_patterns", [])
    sync_interval: float = float(config.get("sync_interval", 5))
    enabled_skills: list[str] = config.get("enabled_skills", [])

    handler = SkillChangeHandler(
        ignored_patterns=ignored_patterns,
        enabled_skills=enabled_skills,
        sync_interval=sync_interval,
    )

    observer = Observer()

    for dir_str in watched_paths:
        dir_path = Path(dir_str)
        if not dir_path.exists():
            logger.warning("Watched path does not exist, skipping: %s", dir_path)
            continue
        observer.schedule(handler, str(dir_path), recursive=True)
        logger.info("Watching: %s", dir_path)

    if not observer.emitters:
        logger.error("No valid watched paths configured. Exiting.")
        return

    # Register signal handlers for graceful shutdown.
    signal.signal(signal.SIGINT, _shutdown_handler)
    signal.signal(signal.SIGTERM, _shutdown_handler)

    observer.start()
    logger.info("Observer started. Press Ctrl+C to stop.")

    try:
        while _running:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
        logger.info("Observer stopped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    config = load_config()

    # Allow a secondary watch path (e.g. D:/Portfolio/Projects) if it exists.
    secondary = Path("D:/Portfolio/Projects")
    if secondary.exists() and str(secondary) not in config.get("watched_paths", []):
        config.setdefault("watched_paths", []).append(str(secondary))
        logger.info("Auto-added secondary watch path: %s", secondary)

    start_observer(config)


if __name__ == "__main__":
    main()
