# handoff_writer.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Writes and reads the handoff manifest that enables continuous
#          work across Claude Code context resets. When Claude Code nears
#          its context limit it calls write_handoff() to snapshot current
#          work state. The local Ollama instance reads the manifest via
#          handoff_runner.py, continues the work, and writes progress back.
#          When a new Claude Code session starts, read_handoff() retrieves
#          the state so Claude Code can review and continue from Ollama's
#          checkpoint.
#
#          This is also the foundation for the AgenticOS multi-model
#          handoff feature: any AI agent (Claude, Ollama, GPT) can write
#          and read this manifest format, enabling seamless relay.

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from AgenticOS.config import HANDOFF_MANIFEST_PATH, LOGGER_NAME

_logger = logging.getLogger(f"{LOGGER_NAME}.handoff_writer")


# ---------------------------------------------------------------------------
# Manifest schema (version 1)
# ---------------------------------------------------------------------------

MANIFEST_VERSION = 1


class HandoffManifest:
    """In-memory representation of a handoff manifest.

    Keeps the schema explicit so both writers (Claude Code) and readers
    (Ollama runner) operate on the same field names without drift.
    """

    def __init__(
        self,
        *,
        project_name: str,
        project_path: str,
        written_by: str,
        written_at: str,
        plan_summary: str,
        completed_tasks: list[dict[str, Any]],
        pending_tasks: list[dict[str, Any]],
        current_task: Optional[dict[str, Any]],
        context_notes: str,
        files_modified: list[str],
        next_action: str,
        version: int = MANIFEST_VERSION,
    ) -> None:
        self.version = version
        self.project_name = project_name
        self.project_path = project_path
        self.written_by = written_by
        self.written_at = written_at
        self.plan_summary = plan_summary
        self.completed_tasks = completed_tasks
        self.pending_tasks = pending_tasks
        self.current_task = current_task
        self.context_notes = context_notes
        self.files_modified = files_modified
        self.next_action = next_action

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "written_by": self.written_by,
            "written_at": self.written_at,
            "plan_summary": self.plan_summary,
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "current_task": self.current_task,
            "context_notes": self.context_notes,
            "files_modified": self.files_modified,
            "next_action": self.next_action,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "HandoffManifest":
        return HandoffManifest(
            version=data.get("version", MANIFEST_VERSION),
            project_name=data["project_name"],
            project_path=data["project_path"],
            written_by=data["written_by"],
            written_at=data["written_at"],
            plan_summary=data["plan_summary"],
            completed_tasks=data.get("completed_tasks", []),
            pending_tasks=data.get("pending_tasks", []),
            current_task=data.get("current_task"),
            context_notes=data.get("context_notes", ""),
            files_modified=data.get("files_modified", []),
            next_action=data.get("next_action", ""),
        )


# ---------------------------------------------------------------------------
# Write / read helpers (atomic for crash safety)
# ---------------------------------------------------------------------------

def write_handoff(manifest: HandoffManifest, path: Path = HANDOFF_MANIFEST_PATH) -> None:
    """Atomically write the handoff manifest to disk.

    Uses temp-then-rename so a crash mid-write never corrupts the
    existing manifest. The Ollama runner checks this file on startup.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False)

    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=path.parent, prefix=".handoff_", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp_path_str, str(path))
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise

    _logger.info(
        "Handoff manifest written by '%s' to %s (%d pending tasks)",
        manifest.written_by,
        path,
        len(manifest.pending_tasks),
    )


def read_handoff(path: Path = HANDOFF_MANIFEST_PATH) -> Optional[HandoffManifest]:
    """Read and parse the handoff manifest. Returns None if absent."""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return HandoffManifest.from_dict(data)
    except (json.JSONDecodeError, KeyError, OSError) as exc:
        _logger.warning("Could not parse handoff manifest at %s: %s", path, exc)
        return None


# ---------------------------------------------------------------------------
# Convenience builder — called by Claude Code near context limit
# ---------------------------------------------------------------------------

def snapshot_current_work(
    *,
    project_name: str,
    project_path: str,
    plan_summary: str,
    completed_tasks: list[str],
    pending_tasks: list[str],
    current_task: Optional[str],
    context_notes: str,
    files_modified: list[str],
    next_action: str,
) -> HandoffManifest:
    """Build and write a HandoffManifest from the current session state.

    Designed to be called from Claude Code when context usage is high.
    The Ollama runner (handoff_runner.py) reads the resulting file and
    continues the work autonomously.

    Parameters mirror the plan fields so the caller can pass structured
    task objects directly from the plan.
    """
    manifest = HandoffManifest(
        project_name=project_name,
        project_path=project_path,
        written_by="claude-code",
        written_at=datetime.now(timezone.utc).isoformat(),
        plan_summary=plan_summary,
        completed_tasks=[{"task": t, "status": "completed"} for t in completed_tasks],
        pending_tasks=[{"task": t, "status": "pending"} for t in pending_tasks],
        current_task={"task": current_task, "status": "in_progress"} if current_task else None,
        context_notes=context_notes,
        files_modified=files_modified,
        next_action=next_action,
    )
    write_handoff(manifest)
    return manifest


# ---------------------------------------------------------------------------
# REST endpoint payload helper (used by /handoff routes in agentic_server)
# ---------------------------------------------------------------------------

def handoff_status_payload() -> dict[str, Any]:
    """Read the current manifest and return a summary dict for the REST API."""
    # Check for agent-style manifest first (write_handoff_manifest schema).
    agent_manifest = read_handoff_manifest()
    if agent_manifest is not None:
        return {
            "status": agent_manifest.get("status", "unknown"),
            "manifest_version": agent_manifest.get("manifest_version"),
            "agent_id": agent_manifest.get("agent_id"),
            "domain": agent_manifest.get("domain"),
            "task": agent_manifest.get("task"),
            "last_completed_stage": agent_manifest.get("last_completed_stage"),
            "total_stages": agent_manifest.get("total_stages"),
            "ollama_model": agent_manifest.get("ollama_model"),
            "ollama_output_ref": agent_manifest.get("ollama_output_ref"),
            "created_at": agent_manifest.get("created_at"),
        }
    # Fall back to legacy project-snapshot manifest.
    # Pass HANDOFF_MANIFEST_PATH explicitly so monkeypatching in tests works.
    manifest = read_handoff(path=HANDOFF_MANIFEST_PATH)
    if manifest is None:
        return {"status": "none"}
    return {
        "status": "active",
        "written_by": manifest.written_by,
        "written_at": manifest.written_at,
        "project_name": manifest.project_name,
        "completed_count": len(manifest.completed_tasks),
        "pending_count": len(manifest.pending_tasks),
        "current_task": manifest.current_task,
        "next_action": manifest.next_action,
        "context_notes": manifest.context_notes,
    }


# ---------------------------------------------------------------------------
# Agent-style handoff manifest (write_handoff_manifest schema)
#
# These functions implement the agentic handoff protocol: Claude Code writes
# a structured manifest at context-limit time, Ollama reads and continues,
# and Claude Code reviews on resume.  The schema is versioned (manifest_version)
# and stored at HANDOFF_MANIFEST_PATH alongside the legacy project snapshot.
# ---------------------------------------------------------------------------

from AgenticOS.config import OLLAMA_HANDOFF_MODEL  # noqa: E402 — appended section


def write_handoff_manifest(
    agent_id: str,
    domain: str,
    task: str,
    last_completed_stage: int,
    total_stages: int,
    last_output_ref: Optional[str],
    resume_instructions: str,
    claude_session_id: str,
) -> Path:
    """Write a versioned handoff manifest so Ollama can continue autonomously.

    Uses an atomic temp-then-rename write identical to write_handoff() so a
    crash mid-write never leaves a partial file.  Returns the manifest path.
    """
    path = HANDOFF_MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    manifest: dict[str, Any] = {
        "manifest_version": 1,
        "created_at": now,
        "claude_session_id": claude_session_id,
        "agent_id": agent_id,
        "domain": domain,
        "task": task,
        "last_completed_stage": last_completed_stage,
        "total_stages": total_stages,
        "last_output_ref": last_output_ref,
        "resume_instructions": resume_instructions,
        "ollama_model": OLLAMA_HANDOFF_MODEL,
        "status": "pending_ollama",
        "ollama_output_ref": None,
        "ollama_completed_at": None,
        "claude_reviewed_at": None,
        "claude_verdict": None,
    }

    data = json.dumps(manifest, indent=2, ensure_ascii=False)
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=path.parent, prefix=".handoff_agent_", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp_path_str, str(path))
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise

    _logger.info(
        "Agent handoff manifest written for agent '%s' (stage %d/%d) to %s",
        agent_id,
        last_completed_stage,
        total_stages,
        path,
    )
    return path


def read_handoff_manifest() -> Optional[dict[str, Any]]:
    """Read the agent-style handoff manifest. Returns None if absent or invalid.

    Distinguishes agent manifests (manifest_version key) from legacy project
    snapshots (version key) so callers can branch on schema without guessing.
    """
    path = HANDOFF_MANIFEST_PATH
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            data: dict[str, Any] = json.load(fh)
        # Only return if this is an agent-style manifest.
        if "manifest_version" not in data:
            return None
        return data
    except (json.JSONDecodeError, OSError) as exc:
        _logger.warning("Could not parse agent handoff manifest at %s: %s", path, exc)
        return None


def update_handoff_status(status: str, **kwargs: Any) -> None:
    """Atomically update specific fields in the agent handoff manifest.

    Reads, patches, and rewrites in a single temp-then-rename cycle.
    Raises FileNotFoundError when no manifest exists yet.
    """
    path = HANDOFF_MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"No handoff manifest at {path}")

    with path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)

    # Apply the status and any additional keyword fields.
    data["status"] = status
    for key, value in kwargs.items():
        data[key] = value

    serialised = json.dumps(data, indent=2, ensure_ascii=False)
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=path.parent, prefix=".handoff_upd_", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(serialised)
        os.replace(tmp_path_str, str(path))
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise

    _logger.debug("Handoff manifest status updated to '%s' with fields: %s", status, list(kwargs))
