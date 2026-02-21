# sync_utils.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Crash-safe file operations with atomic writes and advisory locking to prevent sync corruption

"""
Shared utilities for the Claude Skills sync system.

Provides file hashing, timestamp comparison, path resolution, atomic file
writes, and file locking helpers used by the broadcaster and other modules.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
CLOUD_PATH = BASE_DIR / "cloud" / "main_cloud.json"
BACKUP_DIR = BASE_DIR / "backups"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("sync_utils")


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def file_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def file_mtime_iso(path: Path) -> str:
    """Return the file's modification time as an ISO-8601 UTC string."""
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()


def format_timestamp() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def iso_to_timestamp(iso_str: str) -> float:
    """Convert an ISO-8601 string to a POSIX timestamp (float)."""
    dt = datetime.fromisoformat(iso_str)
    return dt.timestamp()


def is_file_newer(source: Path, target: Path) -> bool:
    """Return True if *source* is strictly newer than *target*.

    If *target* does not exist, *source* is always considered newer.
    """
    if not target.exists():
        return True
    return source.stat().st_mtime > target.stat().st_mtime


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def relative_skill_path(full_path: Path) -> str:
    """Return a POSIX-style path relative to BASE_DIR."""
    try:
        return full_path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return full_path.as_posix()


def resolve_from_base(relative: str) -> Path:
    """Resolve a relative POSIX path back to an absolute Path.

    Raises :class:`ValueError` if the resolved path escapes *BASE_DIR*
    (e.g. via ``../`` traversal).
    """
    resolved = (BASE_DIR / relative).resolve()
    if not resolved.is_relative_to(BASE_DIR.resolve()):
        raise ValueError(
            f"Path traversal blocked: {relative!r} resolves outside BASE_DIR"
        )
    return resolved


# ---------------------------------------------------------------------------
# Atomic file writes
# ---------------------------------------------------------------------------

def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write *content* to *path* atomically (write to temp, then rename).

    On Windows, os.replace is used which is atomic on NTFS when source and
    destination are on the same volume.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=".tmp_",
        suffix=path.suffix,
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON data atomically to *path*."""
    content = json.dumps(data, indent=2, default=str) + "\n"
    atomic_write(path, content)


# ---------------------------------------------------------------------------
# File locking (advisory, cooperative)
# ---------------------------------------------------------------------------

class FileLock:
    """Simple advisory file lock using a .lock sidecar file.

    Uses an atomic create-or-fail approach to prevent concurrent writes.
    This is cooperative -- all writers must use the same locking mechanism.
    """

    def __init__(self, path: Path, timeout: float = 10.0) -> None:
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self.timeout = timeout
        self._fd: int | None = None

    def acquire(self) -> None:
        """Acquire the lock, waiting up to *timeout* seconds."""
        import time

        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._fd = os.open(
                    str(self.lock_path),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                # Write PID for debugging stale locks.
                os.write(self._fd, str(os.getpid()).encode())
                return
            except FileExistsError:
                if time.monotonic() >= deadline:
                    # Check for stale lock (older than 60 seconds).
                    try:
                        age = time.time() - self.lock_path.stat().st_mtime
                        if age > 60:
                            logger.warning(
                                "Removing stale lock file (%.0fs old): %s",
                                age, self.lock_path,
                            )
                            self.lock_path.unlink(missing_ok=True)
                            continue
                    except OSError:
                        pass
                    raise TimeoutError(
                        f"Could not acquire lock on {self.lock_path} "
                        f"within {self.timeout}s"
                    )
                time.sleep(0.1)

    def release(self) -> None:
        """Release the lock."""
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        self.lock_path.unlink(missing_ok=True)

    def __enter__(self) -> FileLock:
        self.acquire()
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


# ---------------------------------------------------------------------------
# Backup helpers
# ---------------------------------------------------------------------------

def backup_file(path: Path) -> Path | None:
    """Create a timestamped backup of *path* before overwriting.

    Returns the backup path, or None if the source doesn't exist.
    """
    if not path.exists():
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rel = relative_skill_path(path)
    backup_path = BACKUP_DIR / timestamp / rel

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(path), str(backup_path))
    logger.info("Backed up %s -> %s", path, backup_path)
    return backup_path


# ---------------------------------------------------------------------------
# Cloud JSON helpers
# ---------------------------------------------------------------------------

def load_cloud(path: Path = CLOUD_PATH) -> dict[str, Any]:
    """Load main_cloud.json, returning the parsed dict."""
    if not path.exists():
        return {
            "version": 1,
            "skills": {},
            "last_updated": None,
            "sync_log": [],
        }
    with path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def save_cloud(data: dict[str, Any], path: Path = CLOUD_PATH) -> None:
    """Save main_cloud.json atomically with file locking."""
    lock = FileLock(path)
    with lock:
        atomic_write_json(path, data)
    logger.debug("Saved cloud state to %s", path)
