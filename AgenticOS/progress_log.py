# progress_log.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Append-only NDJSON progress log for the AgenticOS state bus.
#          Every state transition (added / updated / removed / stuck-flagged
#          / loop-flagged / silent-failure) writes a single line containing
#          a monotonic seq, an ISO 8601 UTC timestamp, and the event payload.
#          Consumers read with read_since(seq) to replay events after a
#          reconnect without dropping any.
#
# Why a separate log alongside the WebSocket diff broadcaster:
# - The WS broadcaster is "current state plus deltas"; that loses history
#   on disconnect. The progress log is the audit trail and is durable.
# - Append-only means crash safety: a corrupt ProgressLog still has all
#   the records up to the crash, no rewrite-in-place can lose them.
#
# This module reuses the cross-platform advisory lock pattern from
# state_store.py exactly: msvcrt.locking on Windows, fcntl.flock on POSIX,
# coordinated through a sibling .lock file so the data file is never
# held open across rename windows.

from __future__ import annotations

import contextlib
import json
import logging
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any, Iterator, Optional

from AgenticOS.config import (
    LOCK_ACQUIRE_TIMEOUT_SECONDS,
    LOCK_RETRY_INTERVAL_SECONDS,
    LOGGER_NAME,
    PROGRESS_LOG_PATH,
)


# Module logger; child of the project-wide AgenticOS logger.
_logger = logging.getLogger(f"{LOGGER_NAME}.progress_log")


# ---------------------------------------------------------------------------
# Cross-platform advisory file locking -- copied verbatim from state_store.py
#
# Why duplicate rather than import: state_store.py's _advisory_lock is a
# private helper (leading underscore). Importing it would couple two
# unrelated modules through a private API. Copying keeps both files
# independently reviewable. If the locking strategy ever changes, both
# files update together -- they share the same constants from config.
# ---------------------------------------------------------------------------

class ProgressLogLockError(RuntimeError):
    """Raised when the progress log advisory lock cannot be acquired in time."""


@contextlib.contextmanager
def _advisory_lock(handle: IO[str]) -> Iterator[None]:
    """Acquire an exclusive advisory lock on ``handle`` for the duration
    of the with-block. Mirrors state_store._advisory_lock so both
    modules behave identically under the same OS conventions."""
    if sys.platform == "win32":
        # Windows: msvcrt.locking holds a per-region lock.
        import msvcrt

        # Lock 1 byte starting at byte 0 -- arbitrary but every caller
        # agrees on the region so cooperative consumers all see each
        # other's locks.
        lock_bytes = 1
        handle.seek(0)
        deadline = time.monotonic() + LOCK_ACQUIRE_TIMEOUT_SECONDS
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, lock_bytes)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise ProgressLogLockError(
                        f"Could not acquire advisory lock on {handle.name} "
                        f"within {LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
                    )
                time.sleep(LOCK_RETRY_INTERVAL_SECONDS)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, lock_bytes)
    else:
        # POSIX: fcntl.flock is whole-file and advisory.
        import fcntl

        deadline = time.monotonic() + LOCK_ACQUIRE_TIMEOUT_SECONDS
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise ProgressLogLockError(
                        f"Could not acquire advisory lock on {handle.name} "
                        f"within {LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
                    )
                time.sleep(LOCK_RETRY_INTERVAL_SECONDS)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# ProgressLog class
# ---------------------------------------------------------------------------

class ProgressLog:
    """Append-only NDJSON writer keyed by a monotonic sequence number.

    Thread-safe within a process via a Python RLock and across processes
    via the OS-level advisory lock on a sibling .lock file. Writes are
    flushed and fsynced before the lock is released so a crash never
    leaves a half-written line.
    """

    def __init__(self, path: Path = PROGRESS_LOG_PATH) -> None:
        # Resolve once so the lock path computation is stable even if a
        # caller changes cwd later in the process lifetime.
        self._path: Path = path
        self._lock_path: Path = path.with_suffix(path.suffix + ".lock")

        # In-process lock guards seq generation and the file handle so
        # two threads can't interleave appends inside this process. The
        # OS lock guards inter-process; both layers are needed.
        self._mutex: threading.RLock = threading.RLock()

        # Make sure the directory exists at construction time; creating
        # it lazily during the first append complicated the lock dance.
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize seq from existing file contents so a process
        # restart resumes the count rather than re-using zero.
        self._next_seq: int = self._compute_next_seq()

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def append(self, event: dict[str, Any]) -> int:
        """Append ``event`` to the log and return the assigned seq.

        ``event`` is shallow-copied: the seq and timestamp fields are
        added by the writer so callers cannot accidentally collide with
        an existing seq. Returns the seq written so the caller can echo
        it to the WebSocket clients for debugging.
        """
        with self._mutex:
            seq = self._next_seq
            self._next_seq += 1

            # Compose the record with metadata first so a human reading
            # the file sees the seq + timestamp at the start of each line.
            record: dict[str, Any] = {
                "seq": seq,
                "ts": datetime.now(timezone.utc).isoformat(),
                **event,
            }

            # Take the OS lock through the sibling lockfile. The data
            # file itself is opened in append mode; we never seek so
            # other writers cannot collide with our offset.
            with self._file_lock():
                # Open in append mode (a) so concurrent processes see
                # each other's writes when they re-open. utf-8 encoding
                # mirrors the rest of AgenticOS.
                with open(self._path, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, default=str) + "\n")
                    handle.flush()
                    # fsync is necessary because the audit trail must
                    # survive a power loss; without it Windows can hold
                    # several seconds of writes in cache.
                    import os
                    os.fsync(handle.fileno())

            _logger.debug(
                "Appended progress event seq=%d kind=%s",
                seq, event.get("kind", "unknown"),
            )
            return seq

    def read_since(self, seq: int) -> list[dict[str, Any]]:
        """Return every record with seq >= ``seq``, in seq order.

        Reads run without taking the OS lock because the file is
        append-only: the worst a concurrent appender can do is race us
        to the EOF, which we tolerate by re-reading on parse failure.
        Malformed lines (e.g. mid-write tear that fsync should prevent
        but we still defend against) are logged and skipped.
        """
        with self._mutex:
            if not self._path.exists():
                return []

            # Read the entire file. NDJSON files at AgenticOS scale stay
            # under a few MB; a streaming parse is overkill until the
            # progress log itself becomes a bottleneck.
            try:
                raw = self._path.read_text(encoding="utf-8")
            except OSError as exc:
                _logger.warning(
                    "Could not read progress log %s: %s", self._path, exc
                )
                return []

        records: list[dict[str, Any]] = []
        for line_no, line in enumerate(raw.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                _logger.warning(
                    "Skipping malformed progress log line %d: %s",
                    line_no, exc,
                )
                continue
            if not isinstance(record, dict):
                # Defensive: NDJSON rules require an object per line.
                continue
            record_seq = record.get("seq")
            if isinstance(record_seq, int) and record_seq >= seq:
                records.append(record)

        return records

    def latest_seq(self) -> Optional[int]:
        """Return the seq of the most recent entry, or None if empty."""
        with self._mutex:
            if self._next_seq <= 0:
                return None
            return self._next_seq - 1

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    def _compute_next_seq(self) -> int:
        """Determine the next seq by scanning existing records once.
        Called only from __init__; subsequent reads of self._next_seq
        come from the in-memory counter, not the file."""
        if not self._path.exists():
            return 0

        max_seq = -1
        try:
            with open(self._path, "r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        record = json.loads(stripped)
                    except json.JSONDecodeError:
                        # Corrupt line: do not abort startup, just skip.
                        continue
                    record_seq = record.get("seq") if isinstance(record, dict) else None
                    if isinstance(record_seq, int) and record_seq > max_seq:
                        max_seq = record_seq
        except OSError as exc:
            _logger.warning(
                "Could not read existing progress log %s: %s",
                self._path, exc,
            )
            return 0

        return max_seq + 1

    @contextlib.contextmanager
    def _file_lock(self) -> Iterator[None]:
        """Take the OS-level advisory lock through the sibling lockfile.
        Mirrors state_store._file_lock_for_path so the two systems behave
        identically when run in the same process."""
        # 'a+' creates if missing; never truncates an existing lockfile.
        handle = open(self._lock_path, "a+", encoding="utf-8")
        try:
            with _advisory_lock(handle):
                yield
        finally:
            handle.close()


# ---------------------------------------------------------------------------
# Module-level singleton
#
# A single shared ProgressLog instance is exposed because the bridge,
# the FastAPI routes, and any future audit consumer all want the same
# log. Tests that need an isolated log instantiate ProgressLog directly
# with a tmp_path.
# ---------------------------------------------------------------------------

progress_log: ProgressLog = ProgressLog(PROGRESS_LOG_PATH)
