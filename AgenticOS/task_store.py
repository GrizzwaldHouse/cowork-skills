# task_store.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Canonical filesystem task runtime for the AgenticOS Hub. Owns
#          every read, write, lock transition, dependency refresh, snapshot
#          write, and dashboard bridge for C:/ClaudeSkills/agentic-os.

from __future__ import annotations

import contextlib
import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from AgenticOS.config import (
    AGENTIC_TASK_RUNTIME_DIR,
    LOGGER_NAME,
)
from AgenticOS.models import (
    AgentDomain,
    AgentState,
    AgentStatus,
    AgenticTask,
    TaskLock,
    TaskSnapshot,
    TaskStatus,
)
from AgenticOS.state_store import (
    StateSchemaError,
    _atomic_write_json,
    _file_lock_for_path,
    _process_lock_for,
    read_agents,
    write_agents,
)


_logger = logging.getLogger(f"{LOGGER_NAME}.task_store")
_log_guard = threading.Lock()


class TaskRuntimeError(RuntimeError):
    """Base class for task runtime failures."""


class TaskSchemaError(TaskRuntimeError):
    """Raised when a task or lock JSON file violates the strict schema."""


class TaskNotFoundError(TaskRuntimeError):
    """Raised when a requested task id does not exist."""


class TaskConflictError(TaskRuntimeError):
    """Raised when a transition would violate task ownership."""


@dataclass(frozen=True)
class TaskRuntimePaths:
    """Resolved path bundle for one task runtime root."""

    base_dir: Path
    tasks_dir: Path
    locks_dir: Path
    logs_dir: Path
    events_log: Path
    errors_log: Path
    state_dir: Path
    snapshot_json: Path
    agents_dir: Path
    agent_registry_json: Path
    config_dir: Path
    system_json: Path


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _paths(base_dir: Path | None = None) -> TaskRuntimePaths:
    """Resolve the canonical runtime paths from the current base dir.

    Tests monkeypatch AGENTIC_TASK_RUNTIME_DIR, so paths are derived at
    call time rather than frozen as module-level constants.
    """
    root = Path(base_dir) if base_dir is not None else AGENTIC_TASK_RUNTIME_DIR
    return TaskRuntimePaths(
        base_dir=root,
        tasks_dir=root / "tasks",
        locks_dir=root / "locks",
        logs_dir=root / "logs",
        events_log=root / "logs" / "events.log",
        errors_log=root / "logs" / "errors.log",
        state_dir=root / "state",
        snapshot_json=root / "state" / "snapshot.json",
        agents_dir=root / "agents",
        agent_registry_json=root / "agents" / "agent-registry.json",
        config_dir=root / "config",
        system_json=root / "config" / "system.json",
    )


def bootstrap_task_runtime(base_dir: Path | None = None) -> TaskRuntimePaths:
    """Create the canonical runtime directory tree and starter files."""
    paths = _paths(base_dir)
    for directory in (
        paths.tasks_dir,
        paths.locks_dir,
        paths.logs_dir,
        paths.state_dir,
        paths.agents_dir,
        paths.config_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    for log_path in (paths.events_log, paths.errors_log):
        if not log_path.exists():
            log_path.write_text("", encoding="utf-8")

    if not paths.agent_registry_json.exists():
        _atomic_write_json(paths.agent_registry_json, [])

    if not paths.system_json.exists():
        _atomic_write_json(
            paths.system_json,
            {
                "runtime": "agentic-os",
                "coordination_mode": "file-based-event-driven",
                "created_at": _utcnow().isoformat(),
            },
        )

    if not paths.snapshot_json.exists():
        _atomic_write_json(
            paths.snapshot_json,
            {
                "timestamp": _utcnow().isoformat(),
                "tasks": [],
                "locks": [],
            },
        )

    return paths


def _task_path(task_id: str, paths: TaskRuntimePaths) -> Path:
    return paths.tasks_dir / f"{task_id}.json"


def _lock_path(task_id: str, paths: TaskRuntimePaths) -> Path:
    return paths.locks_dir / f"{task_id}.lock"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TaskSchemaError(f"{path} is not valid JSON: {exc}") from exc
    except OSError as exc:
        raise TaskRuntimeError(f"Could not read {path}: {exc}") from exc


def _read_task_file(path: Path) -> AgenticTask:
    try:
        return AgenticTask.model_validate(_read_json(path))
    except ValidationError as exc:
        raise TaskSchemaError(f"{path} does not match AgenticTask: {exc}") from exc


def _read_lock_file(path: Path) -> TaskLock:
    try:
        return TaskLock.model_validate(_read_json(path))
    except ValidationError as exc:
        raise TaskSchemaError(f"{path} does not match TaskLock: {exc}") from exc


def read_tasks(base_dir: Path | None = None) -> list[AgenticTask]:
    """Read every task file, sorted by priority then id."""
    paths = bootstrap_task_runtime(base_dir)
    tasks = [
        _read_task_file(path)
        for path in sorted(paths.tasks_dir.glob("*.json"))
    ]
    return sorted(tasks, key=lambda task: (task.priority, task.id))


def read_task(task_id: str, base_dir: Path | None = None) -> AgenticTask:
    """Read one task by id."""
    paths = bootstrap_task_runtime(base_dir)
    path = _task_path(task_id, paths)
    if not path.exists():
        raise TaskNotFoundError(f"Task {task_id} does not exist")
    return _read_task_file(path)


def write_task(task: AgenticTask, base_dir: Path | None = None) -> AgenticTask:
    """Write one validated task document atomically."""
    paths = bootstrap_task_runtime(base_dir)
    path = _task_path(task.id, paths)
    process_lock = _process_lock_for(path)
    with process_lock:
        with _file_lock_for_path(path):
            _atomic_write_json(path, task.model_dump(mode="json"))
    return task


def read_locks(base_dir: Path | None = None) -> list[TaskLock]:
    """Read every authoritative task lock file."""
    paths = bootstrap_task_runtime(base_dir)
    locks = [
        _read_lock_file(path)
        for path in sorted(paths.locks_dir.glob("*.lock"))
    ]
    return sorted(locks, key=lambda lock: lock.task_id)


def _append_log(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{_utcnow().isoformat()} | {message}\n"
    with _log_guard:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()


def log_event(message: str, base_dir: Path | None = None) -> None:
    """Append one meaningful task transition to events.log."""
    _append_log(bootstrap_task_runtime(base_dir).events_log, message)


def log_error(message: str, base_dir: Path | None = None) -> None:
    """Append one task runtime error to errors.log."""
    _append_log(bootstrap_task_runtime(base_dir).errors_log, message)


def _update_task(
    task_id: str,
    mutator: Callable[[AgenticTask], AgenticTask],
    base_dir: Path | None = None,
) -> AgenticTask:
    paths = bootstrap_task_runtime(base_dir)
    path = _task_path(task_id, paths)
    if not path.exists():
        raise TaskNotFoundError(f"Task {task_id} does not exist")

    process_lock = _process_lock_for(path)
    with process_lock:
        with _file_lock_for_path(path):
            task = _read_task_file(path)
            updated = mutator(task)
            updated.updated_at = _utcnow()
            _atomic_write_json(path, updated.model_dump(mode="json"))
            return updated


def _write_lock_file(lock: TaskLock, paths: TaskRuntimePaths) -> None:
    """Create a lock file atomically and fail if one already exists."""
    path = _lock_path(lock.task_id, paths)
    payload = json.dumps(lock.model_dump(mode="json"), indent=2).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        with contextlib.suppress(OSError):
            path.unlink()
        raise


def claim_task(
    task_id: str,
    agent_id: str,
    base_dir: Path | None = None,
) -> AgenticTask:
    """Claim a pending task by creating its authoritative lock file."""
    paths = bootstrap_task_runtime(base_dir)
    task = read_task(task_id, base_dir)
    existing_lock_path = _lock_path(task_id, paths)

    if existing_lock_path.exists():
        existing_lock = _read_lock_file(existing_lock_path)
        if existing_lock.agent_id == agent_id:
            return task
        raise TaskConflictError(
            f"Task {task_id} is locked by {existing_lock.agent_id}"
        )

    if task.status == TaskStatus.BLOCKED:
        raise TaskConflictError(f"Task {task_id} is blocked by dependencies")
    if task.status in {TaskStatus.COMPLETE, TaskStatus.FAILED}:
        raise TaskConflictError(f"Task {task_id} is already {task.status.value}")

    lock = TaskLock(task_id=task_id, agent_id=agent_id, created_at=_utcnow())
    try:
        _write_lock_file(lock, paths)
    except FileExistsError as exc:
        raise TaskConflictError(f"Task {task_id} was claimed concurrently") from exc

    try:
        updated = _update_task(
            task_id,
            lambda current: current.model_copy(
                update={
                    "status": TaskStatus.IN_PROGRESS,
                    "assigned_to": agent_id,
                    "locked_by": agent_id,
                }
            ),
            base_dir,
        )
    except Exception:
        with contextlib.suppress(OSError):
            existing_lock_path.unlink()
        raise

    log_event(f"CLAIMED {task_id} by {agent_id}", base_dir)
    write_snapshot(base_dir)
    return updated


def release_task_lock(
    task_id: str,
    agent_id: str,
    base_dir: Path | None = None,
) -> AgenticTask:
    """Release the authoritative lock for a task owned by agent_id."""
    paths = bootstrap_task_runtime(base_dir)
    lock_path = _lock_path(task_id, paths)
    if not lock_path.exists():
        raise TaskConflictError(f"Task {task_id} has no active lock")

    lock = _read_lock_file(lock_path)
    if lock.agent_id != agent_id:
        raise TaskConflictError(
            f"Task {task_id} lock belongs to {lock.agent_id}, not {agent_id}"
        )

    lock_path.unlink()
    updated = _update_task(
        task_id,
        lambda current: current.model_copy(update={"locked_by": None}),
        base_dir,
    )
    log_event(f"RELEASED {task_id} by {agent_id}", base_dir)
    write_snapshot(base_dir)
    return updated


def _current_lock(task_id: str, base_dir: Path | None = None) -> TaskLock:
    paths = bootstrap_task_runtime(base_dir)
    lock_path = _lock_path(task_id, paths)
    if not lock_path.exists():
        raise TaskConflictError(f"Task {task_id} has no active lock")
    return _read_lock_file(lock_path)


def update_task_checkpoint(
    task_id: str,
    checkpoint: Any,
    base_dir: Path | None = None,
) -> AgenticTask:
    """Append one progress checkpoint to an in-progress task."""
    lock = _current_lock(task_id, base_dir)

    def _mutate(current: AgenticTask) -> AgenticTask:
        if current.status != TaskStatus.IN_PROGRESS:
            raise TaskConflictError(f"Task {task_id} is not in_progress")
        payload = checkpoint if isinstance(checkpoint, dict) else {"message": checkpoint}
        entry = {
            "agent_id": lock.agent_id,
            "created_at": _utcnow().isoformat(),
            **payload,
        }
        return current.model_copy(update={"checkpoints": [*current.checkpoints, entry]})

    updated = _update_task(task_id, _mutate, base_dir)
    log_event(f"CHECKPOINT {task_id} by {lock.agent_id}", base_dir)
    write_snapshot(base_dir)
    return updated


def complete_task(
    task_id: str,
    output: Any,
    base_dir: Path | None = None,
) -> AgenticTask:
    """Mark an owned task complete, persist output, and release its lock."""
    lock = _current_lock(task_id, base_dir)
    updated = _update_task(
        task_id,
        lambda current: current.model_copy(
            update={
                "status": TaskStatus.COMPLETE,
                "output": output,
                "locked_by": None,
            }
        ),
        base_dir,
    )
    with contextlib.suppress(OSError):
        _lock_path(task_id, bootstrap_task_runtime(base_dir)).unlink()
    log_event(f"COMPLETED {task_id} by {lock.agent_id}", base_dir)
    refresh_task_readiness(base_dir)
    write_snapshot(base_dir)
    return updated


def fail_task(
    task_id: str,
    error_context: Any,
    base_dir: Path | None = None,
) -> AgenticTask:
    """Mark an owned task failed, persist context, and release its lock."""
    lock = _current_lock(task_id, base_dir)
    updated = _update_task(
        task_id,
        lambda current: current.model_copy(
            update={
                "status": TaskStatus.FAILED,
                "output": error_context,
                "locked_by": None,
            }
        ),
        base_dir,
    )
    with contextlib.suppress(OSError):
        _lock_path(task_id, bootstrap_task_runtime(base_dir)).unlink()
    message = f"FAILED {task_id} by {lock.agent_id}"
    log_event(message, base_dir)
    log_error(f"{message}: {error_context}", base_dir)
    write_snapshot(base_dir)
    return updated


def validate_locks(base_dir: Path | None = None) -> list[str]:
    """Repair lock/task mismatches where locks are authoritative."""
    paths = bootstrap_task_runtime(base_dir)
    events: list[str] = []
    task_ids = {task.id for task in read_tasks(base_dir)}

    for lock_path in sorted(paths.locks_dir.glob("*.lock")):
        try:
            lock = _read_lock_file(lock_path)
        except TaskSchemaError as exc:
            log_error(str(exc), base_dir)
            continue

        if lock.task_id not in task_ids:
            lock_path.unlink()
            message = f"REMOVED stale lock for missing task {lock.task_id}"
            log_event(message, base_dir)
            events.append(message)
            continue

        task = read_task(lock.task_id, base_dir)
        if task.status in {TaskStatus.COMPLETE, TaskStatus.FAILED}:
            lock_path.unlink()
            message = f"REMOVED terminal lock for {lock.task_id}"
            log_event(message, base_dir)
            events.append(message)
            continue

        if task.locked_by != lock.agent_id or task.status != TaskStatus.IN_PROGRESS:
            updated = _update_task(
                task.id,
                lambda current, owner=lock.agent_id: current.model_copy(
                    update={
                        "status": TaskStatus.IN_PROGRESS,
                        "assigned_to": current.assigned_to or owner,
                        "locked_by": owner,
                    }
                ),
                base_dir,
            )
            message = f"REALIGNED {updated.id} to lock owner {lock.agent_id}"
            log_event(message, base_dir)
            events.append(message)

    return events


def recover_orphaned_tasks(base_dir: Path | None = None) -> list[str]:
    """Recover in-progress tasks that no longer have a lock file."""
    paths = bootstrap_task_runtime(base_dir)
    lock_ids = {
        path.name.removesuffix(".lock")
        for path in paths.locks_dir.glob("*.lock")
    }
    events: list[str] = []

    for task in read_tasks(base_dir):
        if task.status == TaskStatus.IN_PROGRESS and task.id not in lock_ids:
            _update_task(
                task.id,
                lambda current: current.model_copy(
                    update={"status": TaskStatus.PENDING, "locked_by": None}
                ),
                base_dir,
            )
            message = f"RECOVERED orphaned task {task.id}"
            log_event(message, base_dir)
            events.append(message)

    return events


def refresh_task_readiness(base_dir: Path | None = None) -> list[str]:
    """Update pending/blocked tasks from dependency completion state."""
    tasks = read_tasks(base_dir)
    by_id = {task.id: task for task in tasks}
    complete_ids = {
        task.id for task in tasks if task.status == TaskStatus.COMPLETE
    }
    events: list[str] = []

    for task in tasks:
        if task.status not in {TaskStatus.PENDING, TaskStatus.BLOCKED}:
            continue

        blocked = any(dep not in complete_ids for dep in task.dependencies)
        if blocked and task.status == TaskStatus.PENDING:
            _update_task(
                task.id,
                lambda current: current.model_copy(update={"status": TaskStatus.BLOCKED}),
                base_dir,
            )
            message = f"BLOCKED {task.id}; unresolved dependencies"
            log_event(message, base_dir)
            events.append(message)
        elif not blocked and task.status == TaskStatus.BLOCKED:
            missing = [dep for dep in task.dependencies if dep not in by_id]
            if missing:
                continue
            _update_task(
                task.id,
                lambda current: current.model_copy(update={"status": TaskStatus.PENDING}),
                base_dir,
            )
            message = f"UNBLOCKED {task.id}"
            log_event(message, base_dir)
            events.append(message)

    return events


def _task_card_id(task_id: str) -> str:
    lowered = task_id.lower()
    if lowered.startswith("task-"):
        return f"TASK-{task_id[5:].upper()}"
    return f"TASK-{task_id.upper()}"


def _agent_status_for(task: AgenticTask) -> AgentStatus:
    if task.status == TaskStatus.COMPLETE:
        return AgentStatus.COMPLETE
    if task.status == TaskStatus.FAILED:
        return AgentStatus.ERROR
    return AgentStatus.ACTIVE


def _progress_for(task: AgenticTask) -> int:
    if task.status == TaskStatus.COMPLETE:
        return 100
    if task.status == TaskStatus.FAILED:
        return 100
    if task.status == TaskStatus.IN_PROGRESS:
        return 50
    return 0


def sync_tasks_to_agent_state(tasks: list[AgenticTask]) -> None:
    """Mirror canonical tasks into dashboard AgentState cards."""
    task_session_prefix = "agentic-task:"
    try:
        existing = read_agents()
    except StateSchemaError as exc:
        _logger.warning("Skipping task dashboard bridge; agents.json invalid: %s", exc)
        return

    preserved = [
        agent for agent in existing
        if not (agent.discovered_session_id or "").startswith(task_session_prefix)
    ]

    cards: list[AgentState] = []
    for task in tasks:
        agent_id = _task_card_id(task.id)
        cards.append(
            AgentState(
                agent_id=agent_id,
                domain=AgentDomain.GENERAL,
                task=f"{task.title} (owner: {task.assigned_to or 'unassigned'})",
                stage_label=f"{task.status.value}: {task.title}",
                stage=1,
                total_stages=1,
                progress_pct=_progress_for(task),
                status=_agent_status_for(task),
                context_pct_used=0,
                output_ref=str(_task_path(task.id, _paths()).as_posix()),
                awaiting=None,
                error_msg=(
                    str(task.output)[:240]
                    if task.status == TaskStatus.FAILED and task.output is not None
                    else None
                ),
                spawned_by=task.assigned_to,
                reviewer_verdict=None,
                updated_at=task.updated_at,
                discovered_session_id=f"{task_session_prefix}{task.id}",
            )
        )

    write_agents([*preserved, *cards])


def write_snapshot(base_dir: Path | None = None) -> TaskSnapshot:
    """Write state/snapshot.json and update dashboard task cards."""
    paths = bootstrap_task_runtime(base_dir)
    snapshot = TaskSnapshot(
        timestamp=_utcnow(),
        tasks=read_tasks(base_dir),
        locks=read_locks(base_dir),
    )
    _atomic_write_json(paths.snapshot_json, snapshot.model_dump(mode="json"))
    if base_dir is None or Path(base_dir) == AGENTIC_TASK_RUNTIME_DIR:
        sync_tasks_to_agent_state(snapshot.tasks)
    return snapshot


def read_snapshot(base_dir: Path | None = None) -> TaskSnapshot:
    """Read the current task runtime snapshot."""
    paths = bootstrap_task_runtime(base_dir)
    if not paths.snapshot_json.exists():
        return write_snapshot(base_dir)
    try:
        return TaskSnapshot.model_validate(_read_json(paths.snapshot_json))
    except ValidationError as exc:
        raise TaskSchemaError(
            f"{paths.snapshot_json} does not match TaskSnapshot: {exc}"
        ) from exc


def reconcile_task_runtime(base_dir: Path | None = None) -> TaskSnapshot:
    """Run one event-driven reconciliation pass and write a snapshot."""
    bootstrap_task_runtime(base_dir)
    validate_locks(base_dir)
    recover_orphaned_tasks(base_dir)
    refresh_task_readiness(base_dir)
    return write_snapshot(base_dir)
