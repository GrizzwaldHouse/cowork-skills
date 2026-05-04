# ollama_runner.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Submits handoff work to local Ollama and writes results to
#          state/outputs/ so Claude can review them on resume.

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from AgenticOS.config import LOGGER_NAME, OLLAMA_BASE_URL, OUTPUTS_DIR
from AgenticOS.handoff_writer import update_handoff_status

_logger = logging.getLogger(f"{LOGGER_NAME}.ollama_runner")


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class OllamaError(Exception):
    """Raised when the Ollama API returns an error or is unreachable."""


# ---------------------------------------------------------------------------
# Output file writer (atomic)
# ---------------------------------------------------------------------------

def _write_output_file(agent_id: str, model: str, timestamp: str, text: str) -> Path:
    """Write Ollama's response to a markdown file atomically. Returns the path."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUTS_DIR / f"handoff-{agent_id}-ollama.md"

    content = (
        f"# Ollama Handoff Output\n"
        f"**Agent:** {agent_id}\n"
        f"**Model:** {model}\n"
        f"**Completed at:** {timestamp}\n"
        f"\n---\n\n"
        f"{text}"
    )

    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=OUTPUTS_DIR, prefix=".ollama_out_", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path_str, str(target))
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise

    return target


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def submit_to_ollama(manifest: dict[str, Any]) -> str:
    """POST the resume_instructions to Ollama and write the result to outputs/.

    Uses the model name from the manifest (originally set from OLLAMA_HANDOFF_MODEL).
    Updates the handoff manifest status to 'ollama_complete' on success.

    Raises OllamaError on HTTP failure or connection error.
    """
    agent_id: str = manifest["agent_id"]
    model: str = manifest["ollama_model"]
    prompt: str = manifest["resume_instructions"]
    base_url: str = OLLAMA_BASE_URL.rstrip("/")

    _logger.info("Submitting handoff for agent '%s' to Ollama model '%s'", agent_id, model)

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{base_url}/api/generate", json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise OllamaError(
            f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text[:200]}"
        ) from exc
    except httpx.RequestError as exc:
        raise OllamaError(f"Could not connect to Ollama at {base_url}: {exc}") from exc

    response_text: str = response.json().get("response", "")

    timestamp = datetime.now(timezone.utc).isoformat()
    output_path = _write_output_file(agent_id, model, timestamp, response_text)

    # Update the manifest to record completion and the output file path.
    update_handoff_status(
        "ollama_complete",
        ollama_output_ref=str(output_path),
        ollama_completed_at=timestamp,
    )

    _logger.info(
        "Ollama handoff complete for agent '%s'; output written to %s",
        agent_id,
        output_path,
    )
    return response_text
