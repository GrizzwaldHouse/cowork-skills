# watcher_core.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Deduplicate file watcher filtering and throttling to eliminate divergent implementations

"""
Shared watcher filtering and throttling logic.

Extracted from the duplicated implementations in ``observer.py`` and
``watcher_thread.py``.  Both modules now delegate to this shared core.
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("watcher_core")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
SECURITY_DIR = BASE_DIR / "security"

# ---------------------------------------------------------------------------
# Transient file regex
# ---------------------------------------------------------------------------
TRANSIENT_FILE_RE = re.compile(
    r"(^\.tmp_[a-z0-9_]+\..+$)"      # sync_utils atomic writes: .tmp_<rand>.json
    r"|(\.tmp\.\d+\.\d+$)"            # Claude Code atomic writes: *.tmp.<pid>.<ts>
    r"|(\.lock$)",                     # advisory lock sidecars: *.lock
)


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def is_transient(path: Path) -> bool:
    """Return True if *path* is a transient file (atomic write, lock, etc.)."""
    return bool(TRANSIENT_FILE_RE.search(path.name))


def is_security_dir(path: Path) -> bool:
    """Return True if *path* is inside the security directory."""
    try:
        path.relative_to(SECURITY_DIR)
        return True
    except ValueError:
        return False


def matches_ignored(path: Path, patterns: list[str]) -> bool:
    """Return True if *path* matches any of the ignored patterns.

    Supports two pattern forms:
    - Direct name match: ``"__pycache__"``, ``".git"``, ``"backups"``
    - Glob extension match: ``"*.pyc"``
    """
    path_str = str(path)
    for pattern in patterns:
        if pattern in path.parts:
            return True
        if pattern.startswith("*") and path_str.endswith(pattern[1:]):
            return True
    return False


def matches_enabled_skills(path: Path, enabled_skills: list[str]) -> bool:
    """Return True if *path* belongs to an enabled skill folder.

    If *enabled_skills* is empty every path is considered enabled.
    """
    if not enabled_skills:
        return True
    return any(part in enabled_skills for part in path.parts)


def should_process(
    path: Path,
    ignored_patterns: list[str],
    enabled_skills: list[str],
    sync_interval: float,
    last_event_time: dict[str, float],
) -> bool:
    """Full filter check: transient files, security dir, patterns, skills, throttle.

    Updates *last_event_time* in-place when the event passes all checks.
    """
    if is_transient(path):
        return False
    if is_security_dir(path):
        return False
    if matches_ignored(path, ignored_patterns):
        return False
    if not matches_enabled_skills(path, enabled_skills):
        return False

    # Throttle: skip if we saw this path too recently.
    now = time.monotonic()
    key = str(path)
    last = last_event_time.get(key, 0.0)
    if now - last < sync_interval:
        logger.debug("Throttled event for %s", path)
        return False
    last_event_time[key] = now
    return True
