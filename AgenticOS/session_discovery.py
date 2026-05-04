# session_discovery.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Scan COWORK_SESSIONS_ROOT for active Cowork sessions and
#          translate each mission-state.json into a DiscoveredSession
#          model. Read-only on every session directory: this module
#          never writes inside a Cowork plugin or session dir, ever.
#
# Why read-only: Cowork is the source of truth for its own state files
# and we are an observer, not a peer. A bug in this module that wrote
# back to a session dir could corrupt a live agent run; the rule is
# enforced by convention here and by code review on every change.

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

import psutil

from AgenticOS.config import (
    COWORK_SESSIONS_ROOT,
    LOGGER_NAME,
    LOOP_WINDOW_SIZE,
    MAX_DISCOVERED_SESSIONS,
    SESSION_ACTIVE_THRESHOLD_S,
)
from AgenticOS.models import DiscoveredSession


# Module logger; child of the project-wide AgenticOS logger so a single
# logger name filter sees every line we emit.
_logger = logging.getLogger(f"{LOGGER_NAME}.session_discovery")


# Process names we treat as "claude sub-agents". Lowercased once at
# module load; matched against psutil Process.name() output, also
# lowercased per-comparison to make the check Windows-friendly.
_CLAUDE_PROCESS_NAMES: frozenset[str] = frozenset({"claude", "claude.exe"})


# Mission-state.json key names that may carry the human-readable
# objective. Cowork's schema has shifted over time, so we tolerate
# multiple spellings rather than break on the first one Cowork rotates.
_OBJECTIVE_KEYS: tuple[str, ...] = ("objective", "task", "mission", "title")

# Status key fallbacks for the same reason.
_STATUS_KEYS: tuple[str, ...] = ("status", "state", "phase")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_active_sessions(
    sessions_root: Path = COWORK_SESSIONS_ROOT,
    active_threshold_s: int = SESSION_ACTIVE_THRESHOLD_S,
    max_sessions: int = MAX_DISCOVERED_SESSIONS,
) -> list[DiscoveredSession]:
    """Walk ``sessions_root`` two levels deep (plugin / session) and
    return a list of DiscoveredSession entries, one per recently-touched
    mission-state.json. Sessions older than ``active_threshold_s``
    seconds are skipped. Output is capped at ``max_sessions``.

    Never raises on a malformed session directory: the bad entry is
    logged and skipped so a single corrupt file cannot break the whole
    scan. The caller is expected to invoke this on a regular interval
    (see SESSION_SCAN_INTERVAL_S) but the function itself is stateless
    and safe to call from any thread.
    """
    if not sessions_root.exists():
        # The root directory may legitimately be missing on a brand-new
        # workstation; treat that as "no sessions" rather than an error.
        _logger.debug(
            "Cowork sessions root not present yet: %s", sessions_root
        )
        return []

    now = datetime.now(timezone.utc)
    threshold_seconds = float(active_threshold_s)

    discovered: list[DiscoveredSession] = []

    # Build the list of plugin-id directories. iterdir is already
    # sorted-by-disk-order on most filesystems, but we sort explicitly
    # so the output is deterministic across runs.
    try:
        plugin_dirs = sorted(p for p in sessions_root.iterdir() if p.is_dir())
    except OSError as exc:
        # Permission errors or vanished root: log and bail.
        _logger.warning(
            "Could not enumerate sessions root %s: %s", sessions_root, exc
        )
        return []

    # claude / claude.exe processes are looked up once per scan; reusing
    # the snapshot across all sessions is much cheaper than asking psutil
    # for every plugin directory in turn.
    process_snapshot = _snapshot_claude_processes()

    for plugin_dir in plugin_dirs:
        # Each plugin directory holds session-id subdirectories.
        try:
            session_dirs = sorted(
                p for p in plugin_dir.iterdir() if p.is_dir()
            )
        except OSError as exc:
            _logger.warning(
                "Could not enumerate plugin dir %s: %s", plugin_dir, exc
            )
            continue

        for session_dir in session_dirs:
            mission_state = _locate_mission_state(session_dir)
            if mission_state is None:
                # No mission-state.json in this session; skip without
                # logging at INFO since it's the common case for old
                # sessions that have been cleaned up.
                continue

            if not _is_recently_modified(
                mission_state, now, threshold_seconds
            ):
                # The file exists but has gone cold. Filtered here so
                # parse_mission_state never has to think about staleness.
                continue

            session = parse_mission_state(mission_state)
            if session is None:
                # parse_mission_state already logged the failure reason.
                continue

            # Replace the placeholder sub_agent_count with the real one
            # using the snapshot we took above.
            session = session.model_copy(
                update={
                    "sub_agent_count": _count_processes_under(
                        process_snapshot, plugin_dir
                    ),
                }
            )

            discovered.append(session)

            if len(discovered) >= max_sessions:
                # Hard cap: refuse to render or track more than N
                # sessions to keep the UI responsive.
                _logger.info(
                    "Hit max_sessions cap (%d); remaining sessions skipped",
                    max_sessions,
                )
                return discovered

    return discovered


def parse_mission_state(path: Path) -> Optional[DiscoveredSession]:
    """Parse a single ``mission-state.json`` and return a DiscoveredSession.

    Returns None on any parse, validation, or filesystem error after
    logging the cause at WARNING. Never raises: the scan loop above
    relies on this function to absorb per-session faults so the rest
    of the scan can keep going.
    """
    try:
        # Resolve once so the path stored on the model is canonical.
        # Symlinks are followed so the bridge always references the
        # real directory, not the symlink.
        resolved = path.resolve()
    except OSError as exc:
        _logger.warning("Could not resolve %s: %s", path, exc)
        return None

    try:
        # mtime is captured BEFORE the read so a writer racing us
        # cannot make the file appear fresh after we have already
        # decided it is stale.
        mtime_seconds = resolved.stat().st_mtime
    except OSError as exc:
        _logger.warning("Could not stat %s: %s", resolved, exc)
        return None

    try:
        raw = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        _logger.warning("Could not read %s: %s", resolved, exc)
        return None

    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        # Malformed JSON: log with the file path so Marcus can find it.
        _logger.warning("Malformed JSON in %s: %s", resolved, exc)
        return None

    if not isinstance(data, dict):
        _logger.warning(
            "%s top-level value must be a JSON object, got %s",
            resolved, type(data).__name__,
        )
        return None

    # Plugin and session ids come from the directory layout, not the
    # JSON: writers can lie about IDs but cannot lie about where they
    # live on disk.
    session_dir = resolved.parent
    plugin_dir = session_dir.parent
    session_id = session_dir.name
    plugin_id = plugin_dir.name

    # Optional fields with friendly defaults.
    objective = _first_string(data, _OBJECTIVE_KEYS, default="(no objective)")
    status = _first_string(data, _STATUS_KEYS, default="unknown")

    # last_active_at uses mtime, not any embedded JSON timestamp, so an
    # agent that froze without updating its own timestamp is correctly
    # flagged as cold rather than appearing fresh.
    last_active_at = datetime.fromtimestamp(mtime_seconds, tz=timezone.utc)

    # Optional output directory. We accept either a relative or absolute
    # path inside the JSON; relative paths are resolved against the
    # session directory so they always point somewhere predictable.
    output_dir = _resolve_output_dir(data, session_dir)

    # Last LOOP_WINDOW_SIZE timeline entries. Cowork stores a "timeline"
    # array; missing or non-list values are treated as no history.
    timeline_tail = _extract_timeline_tail(data, LOOP_WINDOW_SIZE)

    try:
        return DiscoveredSession(
            session_id=session_id,
            plugin_id=plugin_id,
            objective=objective,
            status=status,
            last_active_at=last_active_at,
            mission_state_path=resolved,
            output_dir=output_dir,
            sub_agent_count=0,  # filled in by scan_active_sessions
            timeline_tail=timeline_tail,
        )
    except Exception as exc:  # noqa: BLE001 — bridge must not crash on bad data
        # Pydantic v2 raises ValidationError, but we also catch any
        # subclass to make absolutely sure a malformed session never
        # propagates upward.
        _logger.warning(
            "Could not construct DiscoveredSession from %s: %s",
            resolved, exc,
        )
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _locate_mission_state(session_dir: Path) -> Optional[Path]:
    """Return the path to mission-state.json inside ``session_dir`` or
    None if the file does not exist. Cowork stores the file directly
    in the session directory; we still resolve the candidate so a
    symlinked session dir works the same as a real one.
    """
    candidate = session_dir / "mission-state.json"
    if not candidate.is_file():
        return None
    return candidate


def _is_recently_modified(
    path: Path,
    now: datetime,
    threshold_seconds: float,
) -> bool:
    """True iff ``path`` was modified within ``threshold_seconds`` of
    ``now``. Errors fetching the mtime mean "not active" — a vanished
    file cannot be a live session.
    """
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return False
    age = now.timestamp() - mtime
    return age <= threshold_seconds


def _first_string(
    data: dict[str, Any],
    keys: Iterable[str],
    default: str,
) -> str:
    """Return the first string-valued entry in ``data`` for any key
    in ``keys``. Falls back to ``default`` if every key is missing or
    empty. Why string-only: writers occasionally store dicts here, but
    the UI needs a label, so we coerce or fall back rather than crash.
    """
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return default


def _resolve_output_dir(
    data: dict[str, Any],
    session_dir: Path,
) -> Optional[Path]:
    """Resolve a session's output directory from the JSON, or fall back
    to the standard ``outputs`` subdirectory inside ``session_dir``."""
    raw = data.get("output_dir") or data.get("outputs_dir")
    if isinstance(raw, str) and raw.strip():
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = session_dir / candidate
        return candidate

    # Fallback: many Cowork builds store outputs under a known subdir.
    fallback = session_dir / "outputs"
    if fallback.is_dir():
        return fallback
    return None


def _extract_timeline_tail(
    data: dict[str, Any],
    window: int,
) -> list[dict[str, Any]]:
    """Extract the last ``window`` timeline entries from a parsed
    mission-state.json. Defensively coerces non-list values to []."""
    timeline = data.get("timeline")
    if not isinstance(timeline, list):
        return []
    # Slice the tail. dict() copy on each entry shields the caller
    # against accidental mutation through a shared reference.
    tail = timeline[-window:] if window > 0 else []
    return [dict(item) for item in tail if isinstance(item, dict)]


def _snapshot_claude_processes() -> list[psutil.Process]:
    """Return a list of live psutil.Process objects whose name matches
    a Claude CLI binary. We snapshot once per scan; iterating psutil's
    process table dozens of times per scan would dwarf every other
    cost in this module on Windows.
    """
    snapshot: list[psutil.Process] = []
    try:
        # process_iter caches the requested attrs internally so the
        # subsequent .name() / .cwd() calls are cheap.
        for proc in psutil.process_iter(["name", "cwd"]):
            try:
                name_value = proc.info.get("name") or ""
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if name_value.lower() in _CLAUDE_PROCESS_NAMES:
                snapshot.append(proc)
    except Exception as exc:  # noqa: BLE001 — process table errors are not fatal
        _logger.warning("Process snapshot failed: %s", exc)
        return []
    return snapshot


def _count_processes_under(
    snapshot: list[psutil.Process],
    plugin_dir: Path,
) -> int:
    """Count Processes from ``snapshot`` whose cwd is inside
    ``plugin_dir``. The plugin directory is the granularity Cowork
    actually exposes, so per-session attribution requires falling
    back to "any process inside the plugin tree".
    """
    try:
        plugin_str = str(plugin_dir.resolve())
    except OSError:
        return 0

    count = 0
    for proc in snapshot:
        try:
            cwd = proc.info.get("cwd") or ""
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if not cwd:
            continue
        try:
            cwd_real = os.path.realpath(cwd)
        except OSError:
            continue
        # Use commonpath instead of startswith so subtle path-separator
        # differences ("\" vs "/") on Windows do not cause a false miss.
        try:
            common = os.path.commonpath([cwd_real, plugin_str])
        except ValueError:
            continue
        if common == plugin_str:
            count += 1
    return count
