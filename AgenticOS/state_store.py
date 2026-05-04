# state_store.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Thread-safe, crash-safe JSON state I/O for AgenticOS. All reads
#          and writes of agents.json and approval_queue.json must go
#          through this module. Implements three guarantees:
#              1. Atomic writes via temp-then-rename (Marcus's standard).
#              2. Advisory file locks (msvcrt on Windows, fcntl on POSIX)
#                 so concurrent writers do not interleave.
#              3. Schema validation on read via Pydantic models, so
#                 malformed JSON or missing fields are caught early.

from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import IO, Iterator, Type, TypeVar

from pydantic import BaseModel, ValidationError

from AgenticOS.config import (
    AGENTS_JSON,
    APPROVAL_QUEUE_JSON,
    ATOMIC_WRITE_TEMP_SUFFIX,
    LOCK_ACQUIRE_TIMEOUT_SECONDS,
    LOCK_RETRY_INTERVAL_SECONDS,
    LOGGER_NAME,
)
from AgenticOS.models import AgentState, ApprovalQueueEntry


# Module logger; child of the project-wide AgenticOS logger.
_logger = logging.getLogger(f"{LOGGER_NAME}.state_store")


# Pydantic model parameter used by the read helpers below.
_ModelT = TypeVar("_ModelT", bound=BaseModel)


# In-process re-entrant lock per file path. Prevents two threads in the
# *same* process from racing each other on the read-modify-write cycle
# even before they reach the OS-level advisory lock.
_process_locks: dict[str, threading.RLock] = {}
_process_locks_guard = threading.Lock()


def _process_lock_for(path: Path) -> threading.RLock:
    """Return (and cache) the process-local RLock that protects ``path``.
    Uses a tiny critical section to keep the cache thread-safe itself."""
    key = str(path.resolve())
    with _process_locks_guard:
        lock = _process_locks.get(key)
        if lock is None:
            # First touch: create and remember the lock for this path.
            lock = threading.RLock()
            _process_locks[key] = lock
        return lock


# ---------------------------------------------------------------------------
# Cross-platform advisory file locking
# ---------------------------------------------------------------------------

class StateLockError(RuntimeError):
    """Raised when an advisory lock cannot be acquired in time."""


@contextlib.contextmanager
def _advisory_lock(handle: IO[str]) -> Iterator[None]:
    """Acquire an exclusive advisory lock on ``handle`` for the duration
    of the with-block. Uses msvcrt on Windows and fcntl elsewhere; both
    are released automatically when the file handle closes, but we
    release explicitly so re-use of the handle is safe."""
    if sys.platform == "win32":
        # Windows path. msvcrt.locking locks bytes starting at the
        # current file pointer; we lock from byte 0 for a fixed length.
        import msvcrt

        # Number of bytes to lock. The exact value does not matter as
        # long as every caller uses the same constant: msvcrt enforces
        # a per-region lock and cooperative consumers all agree to lock
        # the same region.
        lock_bytes = 1

        # Move to byte zero so the lock covers the same region every time.
        handle.seek(0)
        deadline = time.monotonic() + LOCK_ACQUIRE_TIMEOUT_SECONDS
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, lock_bytes)
                break
            except OSError:
                # Lock currently held; retry until the deadline.
                if time.monotonic() >= deadline:
                    raise StateLockError(
                        f"Could not acquire advisory lock on {handle.name} "
                        f"within {LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
                    )
                time.sleep(LOCK_RETRY_INTERVAL_SECONDS)
        try:
            yield
        finally:
            # Always release: failing to do so would leak the lock to
            # the next caller of this same handle.
            with contextlib.suppress(OSError):
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, lock_bytes)
    else:
        # POSIX path. fcntl.flock is whole-file and advisory; perfect
        # for our coarse-grained read-modify-write contract.
        import fcntl

        deadline = time.monotonic() + LOCK_ACQUIRE_TIMEOUT_SECONDS
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise StateLockError(
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
# Atomic write helper
# ---------------------------------------------------------------------------

def _atomic_write_json(target: Path, payload: object) -> None:
    """Serialize ``payload`` to JSON and write it to ``target`` atomically.
    The temp file lives in the same directory as the target so that
    os.replace is a same-volume rename and therefore atomic on every
    supported filesystem."""
    target.parent.mkdir(parents=True, exist_ok=True)

    # NamedTemporaryFile with delete=False so we control the rename
    # explicitly. Suffix carries the PID so concurrent writers (in
    # different processes) cannot collide on the temp filename even
    # within the millisecond window before rename.
    suffix = f"{ATOMIC_WRITE_TEMP_SUFFIX}.{os.getpid()}"
    fd, temp_name = tempfile.mkstemp(
        prefix=target.name + ".",
        suffix=suffix,
        dir=str(target.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        # os.fdopen wraps the low-level fd returned by mkstemp so we
        # can write text without re-opening the file by path.
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(payload, out, indent=2, default=str)
            out.flush()
            # fsync ensures the bytes hit the platter before rename.
            # Without this, a crash between rename and flush could
            # leave the new name pointing at zero bytes.
            os.fsync(out.fileno())

        # os.replace is atomic on the same filesystem on every supported
        # platform; it overwrites the destination if it exists.
        os.replace(temp_path, target)
    except Exception:
        # Best-effort cleanup of the temp file. If this also fails the
        # original exception is the one we want to surface.
        with contextlib.suppress(OSError):
            temp_path.unlink()
        raise


# ---------------------------------------------------------------------------
# Generic typed read / write
# ---------------------------------------------------------------------------

class StateSchemaError(ValueError):
    """Raised when the on-disk JSON does not match the expected schema."""


def _read_validated_list(path: Path, model: Type[_ModelT]) -> list[_ModelT]:
    """Read ``path``, parse it as a JSON list, and validate every entry
    against ``model``. Returns ``[]`` if the file is missing, since the
    bus treats missing state as empty state by design (sub-agents may
    boot before any state has been written)."""
    process_lock = _process_lock_for(path)
    with process_lock:
        if not path.exists():
            # Missing state file is a valid first-run condition.
            return []

        # Coordinate with writers via the sibling lockfile so a reader
        # never observes a half-written file. Holding the lock during
        # the brief read is far cheaper than retrying on parse errors.
        with _file_lock_for_path(path):
            raw = path.read_text(encoding="utf-8")

    if not raw.strip():
        # Empty file is treated identically to "[]".
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StateSchemaError(
            f"{path} is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise StateSchemaError(
            f"{path} top-level value must be a JSON array, got {type(data).__name__}"
        )

    try:
        # model_validate is the Pydantic v2 entry point. We validate
        # every entry so a single bad row surfaces immediately.
        return [model.model_validate(item) for item in data]
    except ValidationError as exc:
        raise StateSchemaError(
            f"{path} contains entries that do not match {model.__name__}: {exc}"
        ) from exc


def _lock_path_for(path: Path) -> Path:
    """Return the sibling lockfile path used to coordinate access to
    ``path``. We lock a separate file rather than the data file
    itself because Windows refuses ``os.replace`` against an open
    target, and the atomic-write helper relies on os.replace."""
    return path.with_suffix(path.suffix + ".lock")


@contextlib.contextmanager
def _file_lock_for_path(path: Path) -> Iterator[None]:
    """Take the OS-level advisory lock on the sibling lockfile of
    ``path``. Creates the lockfile on first use and leaves it on
    disk afterwards so subsequent acquisitions are cheap."""
    lock_path = _lock_path_for(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # 'a+' creates the file if missing and opens it for read/write
    # without truncating, which is what we want for a long-lived lock.
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        with _advisory_lock(handle):
            yield
    finally:
        handle.close()


def _write_validated_list(path: Path, items: list[BaseModel]) -> None:
    """Serialize ``items`` (already-validated Pydantic models) to ``path``
    atomically. Acquires both the in-process and OS-level locks so that
    a concurrent reader sees either the old contents or the new, never
    a partial mix. The OS lock is taken on a sibling .lock file so
    Windows can still rename the temp file onto the data file."""
    process_lock = _process_lock_for(path)
    with process_lock:
        # Guarantee the parent directory exists before the lock helper
        # tries to open its sibling lockfile.
        path.parent.mkdir(parents=True, exist_ok=True)

        with _file_lock_for_path(path):
            payload = [item.model_dump(mode="json") for item in items]
            _atomic_write_json(path, payload)


# ---------------------------------------------------------------------------
# Public API: agents.json
# ---------------------------------------------------------------------------

def read_agents(path: Path = AGENTS_JSON) -> list[AgentState]:
    """Return the current contents of agents.json as validated models."""
    _logger.debug("Reading agents from %s", path)
    return _read_validated_list(path, AgentState)


def write_agents(agents: list[AgentState], path: Path = AGENTS_JSON) -> None:
    """Replace the contents of agents.json with the provided models."""
    _logger.debug("Writing %d agents to %s", len(agents), path)
    _write_validated_list(path, list(agents))


# ---------------------------------------------------------------------------
# Public API: approval_queue.json
# ---------------------------------------------------------------------------

def read_approval_queue(path: Path = APPROVAL_QUEUE_JSON) -> list[ApprovalQueueEntry]:
    """Return the current pending approval queue as validated models."""
    _logger.debug("Reading approval queue from %s", path)
    return _read_validated_list(path, ApprovalQueueEntry)


def write_approval_queue(
    entries: list[ApprovalQueueEntry],
    path: Path = APPROVAL_QUEUE_JSON,
) -> None:
    """Replace the contents of approval_queue.json with the provided entries."""
    _logger.debug("Writing %d approval entries to %s", len(entries), path)
    _write_validated_list(path, list(entries))


def append_approval_entry(
    entry: ApprovalQueueEntry,
    path: Path = APPROVAL_QUEUE_JSON,
) -> None:
    """Append a single entry to approval_queue.json under the same lock
    used by read/write so the read-modify-write cycle is atomic."""
    process_lock = _process_lock_for(path)
    with process_lock:
        # Read existing entries through the validated path so a corrupt
        # queue file is detected before we overwrite it with new data.
        existing = read_approval_queue(path)
        existing.append(entry)
        write_approval_queue(existing, path)


# ---------------------------------------------------------------------------
# Bootstrap helper
# ---------------------------------------------------------------------------

def bootstrap_state_files(
    agents_path: Path = AGENTS_JSON,
    queue_path: Path = APPROVAL_QUEUE_JSON,
) -> None:
    """Create empty state files if they do not already exist. Called by
    the FastAPI lifespan handler on startup so first-run users do not
    have to manually seed the directory."""
    for path in (agents_path, queue_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("[]", encoding="utf-8")
            _logger.info("Initialized empty state file at %s", path)
