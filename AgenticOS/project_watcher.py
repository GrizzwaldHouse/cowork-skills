# project_watcher.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Daemon that auto-discovers Claude Code projects across all of
#          Marcus's machines and registers them with the project registry.
#          Watches configured root paths for CLAUDE.md / .env / .git/HEAD
#          creation events, and polls psutil for claude.exe processes whose
#          cwd is not yet registered. Runs as a background asyncio task
#          started by the FastAPI lifespan handler.

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional

import psutil
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from AgenticOS.config import (
    LOGGER_NAME,
    PROCESS_SCAN_INTERVAL_S,
    PROJECT_WATCH_ROOTS,
    PROJECT_STALE_THRESHOLD_S,
)
from AgenticOS.project_registry import (
    ProjectRegistry,
    extract_project_metadata,
    registry as _global_registry,
)

_logger = logging.getLogger(f"{LOGGER_NAME}.project_watcher")

# Files whose creation/modification signals a new Claude Code project.
_TRIGGER_FILENAMES = frozenset({"CLAUDE.md", ".env", "AGENTS.md"})

# git HEAD path fragment (watchdog delivers full paths).
_GIT_HEAD_SUFFIX = ".git/HEAD"


# ---------------------------------------------------------------------------
# Stable project ID derivation
# ---------------------------------------------------------------------------

def _project_id(project_root: Path) -> str:
    """Derive a stable, collision-resistant project ID from the root path.

    Uses SHA-256 of the absolute path string so the ID survives renames
    of parent directories but changes when the project itself moves.
    The first 16 hex chars are sufficient for uniqueness across a single
    machine.
    """
    digest = hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()
    return digest[:16]


# ---------------------------------------------------------------------------
# Asyncio-safe registration helper
# ---------------------------------------------------------------------------

async def _register_path(path: Path, reg: ProjectRegistry) -> None:
    """Find the CLAUDE.md for *path*, parse it, and upsert the registry.

    *path* may be the CLAUDE.md itself, its parent, or any file under
    the project root — we walk up until we find a CLAUDE.md or give up.
    """
    # Normalise: if path is a file, start from its parent.
    candidate = path if path.is_dir() else path.parent
    claude_md: Optional[Path] = None

    # Walk up to 5 levels to find CLAUDE.md (avoids infinite loops on
    # weird symlink trees without traversing the whole filesystem).
    for _ in range(5):
        probe = candidate / "CLAUDE.md"
        if probe.exists():
            claude_md = probe
            break
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent

    if claude_md is None:
        _logger.debug("No CLAUDE.md found near %s; skipping registration", path)
        return

    project_root = claude_md.parent
    meta = extract_project_metadata(claude_md)
    project_id = _project_id(project_root)

    await reg.upsert(
        project_id=project_id,
        path=str(project_root),
        name=meta["name"],
        tech_stack=meta["tech_stack"],
        skills=meta["skills"],
    )
    _logger.info("Registered project '%s' at %s", meta["name"], project_root)


# ---------------------------------------------------------------------------
# Watchdog event handler (runs on the watchdog thread)
# ---------------------------------------------------------------------------

class _ClaudeProjectHandler(FileSystemEventHandler):
    """Watchdog handler that detects new Claude Code projects.

    The handler is intentionally thin: it just puts discovered paths onto
    an asyncio Queue so the main event loop can do the actual DB work.
    This avoids running async code on the watchdog thread.
    """

    def __init__(self, queue: asyncio.Queue[Path], loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()
        self._queue = queue
        self._loop = loop

    def _enqueue(self, path_str: str) -> None:
        p = Path(path_str)
        name = p.name
        # Trigger on CLAUDE.md, .env, .git/HEAD creation.
        if name in _TRIGGER_FILENAMES or path_str.endswith(_GIT_HEAD_SUFFIX):
            self._loop.call_soon_threadsafe(self._queue.put_nowait, p)

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_modified(self, event: FileModifiedEvent) -> None:  # type: ignore[override]
        if not event.is_directory and event.src_path.endswith("CLAUDE.md"):
            # Re-register on CLAUDE.md modification: skills/tech may have changed.
            self._enqueue(event.src_path)


# ---------------------------------------------------------------------------
# Process scanner
# ---------------------------------------------------------------------------

async def _scan_processes(reg: ProjectRegistry) -> None:
    """Scan running processes for claude.exe / claude instances whose cwd
    represents an unregistered project root.

    Runs on the thread pool (psutil is synchronous) and posts results
    through the same registration path used by watchdog events.
    """
    def _find_claude_cwds() -> list[Path]:
        results: list[Path] = []
        try:
            for proc in psutil.process_iter(["name", "cwd"]):
                name = (proc.info.get("name") or "").lower()
                if "claude" not in name:
                    continue
                cwd_str = proc.info.get("cwd")
                if cwd_str:
                    results.append(Path(cwd_str))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return results

    cwds = await asyncio.to_thread(_find_claude_cwds)
    for cwd in cwds:
        existing = await reg.get_by_path(str(cwd))
        if existing is None:
            # Treat the cwd as a potential project root and let the
            # normal registration path find the CLAUDE.md.
            await _register_path(cwd, reg)


# ---------------------------------------------------------------------------
# Stale project mark-inactive sweep
# ---------------------------------------------------------------------------

async def _sweep_stale(reg: ProjectRegistry) -> None:
    """Mark projects as inactive when they have not been seen recently.

    A project is stale when its ``last_seen`` timestamp is older than
    PROJECT_STALE_THRESHOLD_S and no CLAUDE.md exists at its path.
    We never delete rows — only mark inactive — so the UI can show a
    'last seen' indicator without losing history.
    """
    from datetime import datetime, timezone
    import json

    active = await reg.list_active()
    now = datetime.now(timezone.utc)

    for proj in active:
        claude_md = Path(proj.path) / "CLAUDE.md"
        if not claude_md.exists():
            # Parse ISO timestamp.
            try:
                last_seen = datetime.fromisoformat(proj.last_seen.replace("Z", "+00:00"))
                age_s = (now - last_seen).total_seconds()
                if age_s > PROJECT_STALE_THRESHOLD_S:
                    await reg.set_inactive(proj.id)
                    _logger.info(
                        "Marked project '%s' inactive (unseen %.0fs)", proj.name, age_s
                    )
            except ValueError:
                pass


# ---------------------------------------------------------------------------
# Main daemon coroutine
# ---------------------------------------------------------------------------

async def run_project_watcher(
    stop_event: asyncio.Event,
    reg: Optional[ProjectRegistry] = None,
) -> None:
    """Watch configured root paths and register discovered projects.

    Designed to run as an asyncio task alongside the FastAPI lifespan.
    Uses an asyncio.Queue as the bridge between the watchdog thread and
    the async registration logic — watchdog puts paths; we consume them.

    Parameters
    ----------
    stop_event:
        Set by the lifespan shutdown handler to stop the loop cleanly.
    reg:
        Override for testing; defaults to the module-level singleton.
    """
    if reg is None:
        reg = _global_registry

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Path] = asyncio.Queue()

    handler = _ClaudeProjectHandler(queue=queue, loop=loop)
    observer = Observer()

    roots_scheduled = 0
    for root_str in PROJECT_WATCH_ROOTS:
        root = Path(root_str)
        if root.exists():
            observer.schedule(handler, str(root), recursive=True)
            roots_scheduled += 1
            _logger.info("Project watcher watching: %s", root)
        else:
            _logger.debug("Watch root does not exist, skipping: %s", root)

    if roots_scheduled == 0:
        _logger.warning("No valid project watch roots found; discovery disabled")
        return

    observer.start()
    _logger.info("Project watcher started (%d roots)", roots_scheduled)

    process_scan_counter = 0.0

    try:
        while not stop_event.is_set():
            # Drain queue with a short timeout so we also handle the
            # process scan timer and the stop_event check regularly.
            try:
                path = await asyncio.wait_for(queue.get(), timeout=1.0)
                await _register_path(path, reg)
                queue.task_done()
            except asyncio.TimeoutError:
                pass

            # Process scan runs every PROCESS_SCAN_INTERVAL_S seconds.
            process_scan_counter += 1.0
            if process_scan_counter >= PROCESS_SCAN_INTERVAL_S:
                process_scan_counter = 0.0
                try:
                    await _scan_processes(reg)
                    await _sweep_stale(reg)
                except Exception as exc:  # noqa: BLE001
                    _logger.warning("Process scan error: %s", exc)

    finally:
        observer.stop()
        observer.join()
        _logger.info("Project watcher stopped")
