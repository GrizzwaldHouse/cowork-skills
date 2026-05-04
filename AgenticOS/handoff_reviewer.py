# handoff_reviewer.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Loads Ollama's handoff output and produces a structured review
#          for Claude to read when resuming after a context reset.

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from AgenticOS.config import LOGGER_NAME
from AgenticOS.handoff_writer import read_handoff_manifest

_logger = logging.getLogger(f"{LOGGER_NAME}.handoff_reviewer")


def review_handoff_output() -> Optional[dict[str, Any]]:
    """Load the Ollama handoff output and return a structured review dict.

    Returns None when no manifest exists or its status is not 'ollama_complete'.
    The returned dict includes a ready-to-use review_prompt so Claude can
    immediately continue work from the correct stage without re-deriving context.
    """
    manifest = read_handoff_manifest()

    if manifest is None:
        _logger.debug("review_handoff_output: no agent manifest found.")
        return None

    if manifest.get("status") != "ollama_complete":
        _logger.debug(
            "review_handoff_output: manifest status is '%s', expected 'ollama_complete'.",
            manifest.get("status"),
        )
        return None

    agent_id: str = manifest.get("agent_id", "unknown")
    ollama_model: str = manifest.get("ollama_model", "unknown")
    output_ref: Optional[str] = manifest.get("ollama_output_ref")
    last_completed_stage: int = manifest.get("last_completed_stage", 0)
    task: str = manifest.get("task", "")
    domain: str = manifest.get("domain", "")

    # Read the Ollama output file if the path is recorded.
    output_text: str = ""
    if output_ref:
        output_path = Path(output_ref)
        if output_path.exists():
            try:
                output_text = output_path.read_text(encoding="utf-8")
            except OSError as exc:
                _logger.warning(
                    "Could not read Ollama output file at %s: %s", output_path, exc
                )
        else:
            _logger.warning(
                "Ollama output_ref points to missing file: %s", output_ref
            )

    # Stage Claude should resume from (one past the last completed stage).
    resume_from: int = last_completed_stage + 1

    review_prompt: str = (
        f"You are resuming work on task: {task}. "
        f"Ollama completed stage {last_completed_stage}. "
        f"Review its output below and continue from stage {resume_from}:\n\n"
        f"{output_text}"
    )

    return {
        "agent_id": agent_id,
        "ollama_model": ollama_model,
        "ollama_output_ref": output_ref,
        "ollama_output_text": output_text,
        "resume_from_stage": resume_from,
        "task": task,
        "domain": domain,
        "review_prompt": review_prompt,
    }
