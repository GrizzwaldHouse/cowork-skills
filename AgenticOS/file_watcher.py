# file_watcher.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Watchdog-based filesystem observer that fires asyncio events
#          when AgenticOS state files change. Strictly event-driven; no
#          polling loops anywhere. The FastAPI lifespan handler owns the
#          observer lifecycle and is responsible for stopping it on
#          shutdown.

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Awaitable, Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

from AgenticOS.config import (
    AGENTS_JSON,
    LOGGER_NAME,
    WATCHER_RECURSIVE,
)


# Type alias for the broadcast callback. Spelled out so the signature
# is documented at the top of the module.
BroadcastCallable = Callable[[], Awaitable[None]]


# Module logger; child of the project-wide AgenticOS logger.
_logger = logging.getLogger(f"{LOGGER_NAME}.file_watcher")


class _AgentsJsonHandler(FileSystemEventHandler):
    """Watchdog event handler that schedules an async broadcast whenever
    the watched JSON file is modified. Other files in the same directory
    are ignored; we filter on the resolved absolute path so symlinks
    cannot fool us into broadcasting on the wrong file."""

    def __init__(
        self,
        broadcast_callback: BroadcastCallable,
        loop: asyncio.AbstractEventLoop,
        watched_file: Path,
    ) -> None:
        # Coroutine factory invoked on every relevant change event.
        self._callback: BroadcastCallable = broadcast_callback

        # The asyncio loop running the FastAPI app. Watchdog dispatches
        # events on a background thread, so we must marshal coroutine
        # scheduling back onto the main loop with run_coroutine_threadsafe.
        self._loop: asyncio.AbstractEventLoop = loop

        # Resolve once at construction so per-event comparisons are cheap
        # and unambiguous. Resolve also normalises slashes on Windows.
        self._watched_file: Path = watched_file.resolve()

    def _is_watched_file(self, event: FileSystemEvent) -> bool:
        """True iff the event refers to our specific file."""
        # Directory events never carry meaningful state changes for us.
        if event.is_directory:
            return False
        try:
            # FileSystemEvent.src_path may be bytes on some platforms;
            # str() is safe and idempotent for both bytes and str.
            return Path(str(event.src_path)).resolve() == self._watched_file
        except OSError:
            # Resolve can raise on Windows for short-lived temp paths
            # created by atomic-write helpers. Treat as not-our-file.
            return False

    def _schedule_broadcast(self) -> None:
        """Schedule the async broadcast on the FastAPI event loop in a
        thread-safe way. Must never raise: watchdog dispatch threads
        do not handle exceptions cleanly."""
        try:
            asyncio.run_coroutine_threadsafe(self._callback(), self._loop)
        except RuntimeError as exc:
            # The loop is closed (server is shutting down). Log and move
            # on rather than crash the watchdog thread.
            _logger.warning(
                "Could not schedule broadcast on closed loop: %s", exc
            )

    def on_modified(self, event: FileSystemEvent) -> None:
        """Trigger on file content modification."""
        if not self._is_watched_file(event):
            return
        _logger.debug("Detected modification on %s", self._watched_file)
        self._schedule_broadcast()

    def on_created(self, event: FileSystemEvent) -> None:
        """Trigger on file creation. Atomic writes via os.replace cause
        editors and watchdog to see a create-then-modify pattern, so
        we must respond to creates as well as modifies."""
        if not self._is_watched_file(event):
            return
        _logger.debug("Detected creation of %s", self._watched_file)
        self._schedule_broadcast()

    def on_moved(self, event: FileSystemEvent) -> None:
        """Trigger on rename-into-place. The atomic_write_json helper
        in state_store renames a temp file onto the watched path; on
        some filesystems watchdog reports this as a moved event whose
        ``dest_path`` is our watched file."""
        # Re-use the same filtering logic against dest_path.
        try:
            dest = Path(str(getattr(event, "dest_path", ""))).resolve()
        except OSError:
            return
        if dest != self._watched_file:
            return
        _logger.debug("Detected move-into-place of %s", self._watched_file)
        self._schedule_broadcast()


def start_file_watcher(
    broadcast_callback: BroadcastCallable,
    loop: asyncio.AbstractEventLoop,
    watched_file: Path = AGENTS_JSON,
) -> BaseObserver:
    """Create, start, and return a watchdog Observer that invokes
    ``broadcast_callback`` whenever ``watched_file`` is modified. The
    caller owns the returned Observer and must call ``observer.stop()``
    followed by ``observer.join()`` on shutdown."""
    handler = _AgentsJsonHandler(
        broadcast_callback=broadcast_callback,
        loop=loop,
        watched_file=watched_file,
    )

    observer: BaseObserver = Observer()

    # watchdog watches directories, not individual files. We schedule
    # the parent directory non-recursively and the handler filters
    # events down to the specific file we care about.
    watch_dir = str(watched_file.resolve().parent)
    observer.schedule(
        event_handler=handler,
        path=watch_dir,
        recursive=WATCHER_RECURSIVE,
    )
    observer.start()

    _logger.info(
        "File watcher started; observing %s for changes (recursive=%s)",
        watched_file,
        WATCHER_RECURSIVE,
    )
    return observer
