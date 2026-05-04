# task_watcher.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Watchdog-based referee for the canonical agentic-os task runtime.
#          Reacts to task/lock filesystem events, reconciles ownership, and
#          emits snapshots without a polling loop.

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Awaitable, Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

from AgenticOS.config import LOGGER_NAME
from AgenticOS import config
from AgenticOS.task_store import bootstrap_task_runtime, reconcile_task_runtime


TaskRuntimeCallback = Callable[[], Awaitable[None]]
_logger = logging.getLogger(f"{LOGGER_NAME}.task_watcher")


class _TaskRuntimeHandler(FileSystemEventHandler):
    """Schedule one reconciliation pass for relevant task runtime events."""

    def __init__(
        self,
        callback: TaskRuntimeCallback,
        loop: asyncio.AbstractEventLoop,
        runtime_root: Path,
    ) -> None:
        self._callback = callback
        self._loop = loop
        self._runtime_root = runtime_root.resolve()
        self._scheduled = False

    def _is_relevant(self, event: FileSystemEvent) -> bool:
        if event.is_directory:
            return False

        raw_paths = [str(event.src_path)]
        dest_path = getattr(event, "dest_path", None)
        if dest_path:
            raw_paths.append(str(dest_path))

        for raw_path in raw_paths:
            try:
                path = Path(raw_path).resolve()
            except OSError:
                continue

            parent = path.parent
            if parent == self._runtime_root / "tasks" and path.suffix == ".json":
                return True
            if parent == self._runtime_root / "locks" and path.suffix == ".lock":
                return True
        return False

    async def _run_once(self) -> None:
        await asyncio.sleep(0.05)
        try:
            await self._callback()
        finally:
            self._scheduled = False

    def _schedule(self) -> None:
        if self._scheduled:
            return
        self._scheduled = True
        try:
            asyncio.run_coroutine_threadsafe(self._run_once(), self._loop)
        except RuntimeError as exc:
            self._scheduled = False
            _logger.warning("Could not schedule task reconciliation: %s", exc)

    def on_created(self, event: FileSystemEvent) -> None:
        if self._is_relevant(event):
            self._schedule()

    def on_modified(self, event: FileSystemEvent) -> None:
        if self._is_relevant(event):
            self._schedule()

    def on_moved(self, event: FileSystemEvent) -> None:
        if self._is_relevant(event):
            self._schedule()

    def on_deleted(self, event: FileSystemEvent) -> None:
        if self._is_relevant(event):
            self._schedule()


async def reconcile_and_broadcast(
    broadcast_callback: TaskRuntimeCallback,
    runtime_root: Path | None = None,
) -> None:
    """Run reconciliation, then broadcast dashboard state."""
    reconcile_task_runtime(runtime_root)
    await broadcast_callback()


def start_task_watcher(
    broadcast_callback: TaskRuntimeCallback,
    loop: asyncio.AbstractEventLoop,
    runtime_root: Path | None = None,
) -> BaseObserver:
    """Start a watchdog observer for task and lock state transitions."""
    root = runtime_root or config.AGENTIC_TASK_RUNTIME_DIR
    paths = bootstrap_task_runtime(root)

    async def _callback() -> None:
        await reconcile_and_broadcast(broadcast_callback, runtime_root)

    handler = _TaskRuntimeHandler(
        callback=_callback,
        loop=loop,
        runtime_root=paths.base_dir,
    )
    observer: BaseObserver = Observer()
    observer.schedule(handler, str(paths.tasks_dir), recursive=False)
    observer.schedule(handler, str(paths.locks_dir), recursive=False)
    observer.start()

    _logger.info(
        "Task watcher started; observing %s and %s",
        paths.tasks_dir,
        paths.locks_dir,
    )
    return observer
