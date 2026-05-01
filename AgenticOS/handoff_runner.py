# handoff_runner.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Ollama-powered handoff runner that reads the handoff manifest
#          written by Claude Code (or another AI agent), continues the
#          pending tasks using a local Ollama model, and writes progress
#          back to the manifest so the next session (Claude Code or another
#          Ollama invocation) can review and continue seamlessly.
#
#          This implements the continuous-work loop Marcus requested:
#            Claude Code (writes manifest) → Ollama (runs pending tasks)
#            → Claude Code (reviews + continues) → repeat until done.
#
#          Run via: python -m AgenticOS.handoff_runner
#          Or auto-start via AgenticOS process_supervisor when manifest appears.

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

from AgenticOS.config import (
    HANDOFF_MANIFEST_PATH,
    LOGGER_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_HANDOFF_MODEL,
)
from AgenticOS.handoff_writer import (
    HandoffManifest,
    read_handoff,
    write_handoff,
)

_logger = logging.getLogger(f"{LOGGER_NAME}.handoff_runner")


# ---------------------------------------------------------------------------
# Ollama client
# ---------------------------------------------------------------------------

class OllamaClient:
    """Minimal async Ollama HTTP client (no extra deps beyond httpx)."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    async def is_available(self) -> bool:
        """Return True if Ollama is reachable and the model is present."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code != 200:
                    return False
                tags = resp.json()
                models = [m["name"] for m in tags.get("models", [])]
                return any(OLLAMA_HANDOFF_MODEL.split(":")[0] in m for m in models)
        except httpx.HTTPError:
            return False

    async def pull_model(self) -> None:
        """Pull the handoff model if not already present."""
        _logger.info("Pulling Ollama model %s ...", OLLAMA_HANDOFF_MODEL)
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/pull",
                json={"name": OLLAMA_HANDOFF_MODEL, "stream": True},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                _logger.info("Pull: %s", data["status"])
                        except json.JSONDecodeError:
                            pass

    async def generate(self, prompt: str, system: str = "") -> str:
        """Run a completion and return the full response text."""
        payload: dict[str, Any] = {
            "model": OLLAMA_HANDOFF_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")


# ---------------------------------------------------------------------------
# Task executor
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an AI coding assistant continuing work on behalf of Claude Code.
You have been given a handoff manifest describing what has been completed and what remains.
Your job is to execute the next pending task, write any code changes as unified diffs or
complete file contents, and report what you did so the next session can review and continue.
Be precise, complete, and follow the project's coding standards exactly as described.
Output format: First line must be TASK_COMPLETE or TASK_PARTIAL, then a description."""


async def _execute_task(
    client: OllamaClient,
    task: dict[str, Any],
    manifest: HandoffManifest,
) -> tuple[str, str]:
    """Execute one pending task via Ollama. Returns (status, output)."""
    prompt = f"""
HANDOFF MANIFEST CONTEXT:
Project: {manifest.project_name} at {manifest.project_path}
Plan: {manifest.plan_summary}

COMPLETED TASKS:
{json.dumps(manifest.completed_tasks, indent=2)}

CONTEXT NOTES FROM PREVIOUS SESSION:
{manifest.context_notes}

FILES ALREADY MODIFIED:
{', '.join(manifest.files_modified) or 'none'}

YOUR TASK:
{task.get('task', 'No task description provided.')}

Execute this task now. If you need to write code, provide complete file contents.
"""
    _logger.info("Executing task via Ollama: %s", task.get("task", "")[:80])
    try:
        output = await client.generate(prompt, system=_SYSTEM_PROMPT)
        status = "completed" if output.startswith("TASK_COMPLETE") else "partial"
        return status, output
    except httpx.HTTPError as exc:
        _logger.error("Ollama generation failed: %s", exc)
        return "failed", str(exc)


# ---------------------------------------------------------------------------
# Main runner loop
# ---------------------------------------------------------------------------

async def run_handoff_loop(
    manifest_path: Path = HANDOFF_MANIFEST_PATH,
    max_tasks: int = 5,
) -> None:
    """Read the handoff manifest, execute pending tasks, write progress back.

    Designed to run autonomously when Claude Code's context resets.
    Stops after max_tasks to prevent runaway execution; the next
    Claude Code session reviews and optionally continues.
    """
    manifest = read_handoff(manifest_path)
    if manifest is None:
        _logger.info("No handoff manifest found at %s; nothing to do.", manifest_path)
        return

    _logger.info(
        "Handoff runner starting. Project: %s | %d pending tasks",
        manifest.project_name,
        len(manifest.pending_tasks),
    )

    client = OllamaClient()

    # Ensure Ollama is available; pull model if needed.
    if not await client.is_available():
        _logger.warning(
            "Ollama model '%s' not found. Attempting pull...", OLLAMA_HANDOFF_MODEL
        )
        try:
            await client.pull_model()
        except Exception as exc:  # noqa: BLE001
            _logger.error("Could not pull Ollama model: %s", exc)
            return

    tasks_done = 0
    while manifest.pending_tasks and tasks_done < max_tasks:
        # Pop the first pending task.
        task = manifest.pending_tasks.pop(0)
        manifest.current_task = task

        # Write manifest with current_task marked in_progress before executing.
        task["status"] = "in_progress"
        write_handoff(manifest)

        status, output = await _execute_task(client, task, manifest)

        # Record completion.
        task["status"] = status
        task["output"] = output[:2000]  # Truncate to keep manifest readable.
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        manifest.completed_tasks.append(task)
        manifest.current_task = None
        manifest.written_by = f"ollama/{OLLAMA_HANDOFF_MODEL}"
        manifest.written_at = datetime.now(timezone.utc).isoformat()
        manifest.context_notes = (
            f"Ollama completed '{task.get('task', '')}' with status '{status}'. "
            f"Review output before continuing.\n{manifest.context_notes}"
        )

        if manifest.pending_tasks:
            manifest.next_action = (
                f"Review Ollama's work on '{task.get('task', '')}', "
                f"then continue with: {manifest.pending_tasks[0].get('task', '')}"
            )
        else:
            manifest.next_action = "All tasks complete. Review Ollama's work and verify."

        write_handoff(manifest)
        tasks_done += 1
        _logger.info("Task completed (%s): %s", status, task.get("task", "")[:60])

    if not manifest.pending_tasks:
        _logger.info("All pending tasks complete. Handoff done.")
    else:
        _logger.info(
            "Stopped after %d tasks (limit). %d tasks remain.",
            tasks_done,
            len(manifest.pending_tasks),
        )


def main() -> None:
    """CLI entry point: ``python -m AgenticOS.handoff_runner``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        stream=sys.stderr,
    )
    asyncio.run(run_handoff_loop())


if __name__ == "__main__":
    main()
