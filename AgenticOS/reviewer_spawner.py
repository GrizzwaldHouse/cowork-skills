# reviewer_spawner.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Spawn a Claude Haiku 4.5 subprocess to review an agent's output
#          file. The verdict is written to state/outputs/agent-{id}-review.md
#          and an asyncio.Future resolves with the verdict path so the
#          server can await completion without blocking the event loop.

from __future__ import annotations

import asyncio
import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Optional

from AgenticOS.config import (
    CLAUDE_CLI_EXECUTABLE,
    LOGGER_NAME,
    OUTPUTS_DIR,
    REVIEWER_MODEL,
    REVIEWER_OUTPUT_TEMPLATE,
    REVIEWER_PROMPT_TEMPLATE,
    REVIEWER_TIMEOUT_SECONDS,
)
from AgenticOS.models import ReviewerOutcome, ReviewerVerdict


# Module logger; child of the project-wide AgenticOS logger.
_logger = logging.getLogger(f"{LOGGER_NAME}.reviewer_spawner")


# Regex used to extract the top-line verdict (PASS/REVISE/REJECT) from
# the reviewer's free-form response. Matches the first occurrence of
# any of the three keywords as a whole word, case-insensitive at the
# start of a line is preferred but anywhere is accepted.
_VERDICT_REGEX: Final[re.Pattern[str]] = re.compile(
    r"\b(PASS|REVISE|REJECT)\b"
)


class ReviewerSpawnError(RuntimeError):
    """Raised when the reviewer subprocess cannot be spawned or fails."""


def build_reviewer_prompt(reviewer_context_path: str) -> str:
    """Read the agent's output file and substitute it into the configured
    reviewer prompt template. Raises FileNotFoundError if the file is
    missing, since reviewing nothing would be a silent no-op."""
    context_path = Path(reviewer_context_path)
    if not context_path.exists():
        raise FileNotFoundError(
            f"Reviewer context file not found: {context_path}"
        )

    # Read the agent output verbatim; the template handles framing.
    content = context_path.read_text(encoding="utf-8")

    # Substitute via the template from config so the prompt itself is
    # not hardcoded inside this module.
    return REVIEWER_PROMPT_TEMPLATE.format(content=content)


def _parse_outcome(verdict_text: str) -> ReviewerOutcome:
    """Extract the structured outcome enum from the free-form reviewer
    response. Defaults to REVISE on no match: better to flag for human
    inspection than to silently pretend the reviewer said PASS."""
    match = _VERDICT_REGEX.search(verdict_text)
    if not match:
        _logger.warning(
            "Could not parse PASS/REVISE/REJECT from reviewer output; "
            "defaulting to REVISE for safety"
        )
        return ReviewerOutcome.REVISE
    return ReviewerOutcome(match.group(1).upper())


def _write_verdict_file(
    agent_id: str,
    verdict_text: str,
    reviewer_context: str,
    outputs_dir: Path,
) -> Path:
    """Write the markdown verdict file with a metadata header for
    traceability and return its path. Caller is responsible for the
    outputs_dir argument; the function does not consult global config
    so tests can redirect the output directory."""
    outputs_dir.mkdir(parents=True, exist_ok=True)

    verdict_filename = REVIEWER_OUTPUT_TEMPLATE.format(agent_id=agent_id)
    verdict_path = outputs_dir / verdict_filename
    timestamp = datetime.now(timezone.utc).isoformat()

    # Compose the header block then the verdict body. Header lines are
    # comment-style so the file remains valid Markdown.
    header = (
        f"<!--\n"
        f"  agent_id: {agent_id}\n"
        f"  reviewed_at: {timestamp}\n"
        f"  model: {REVIEWER_MODEL}\n"
        f"  context_file: {reviewer_context}\n"
        f"-->\n\n"
        f"# Reviewer Verdict for {agent_id}\n\n"
    )
    verdict_path.write_text(header + verdict_text + "\n", encoding="utf-8")
    return verdict_path


def spawn_reviewer(
    agent_id: str,
    reviewer_context: str,
    outputs_dir: Path = OUTPUTS_DIR,
) -> ReviewerVerdict:
    """Run the Claude Haiku reviewer synchronously and return the
    structured verdict. ``outputs_dir`` is parameterised for tests but
    defaults to the configured location for production use.

    Raises:
        FileNotFoundError: if ``reviewer_context`` does not exist.
        ReviewerSpawnError: if the subprocess fails or times out.
    """
    # Build prompt first so a missing context file fails fast before
    # we spend a subprocess on it.
    prompt = build_reviewer_prompt(reviewer_context)

    cmd: list[str] = [
        CLAUDE_CLI_EXECUTABLE,
        "--model", REVIEWER_MODEL,
        # --print runs Claude non-interactively and returns the response
        # on stdout. Required because we are not attached to a TTY.
        "--print",
        prompt,
    ]

    _logger.info(
        "Spawning reviewer for %s with model %s (timeout=%ds)",
        agent_id,
        REVIEWER_MODEL,
        REVIEWER_TIMEOUT_SECONDS,
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=REVIEWER_TIMEOUT_SECONDS,
            encoding="utf-8",
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReviewerSpawnError(
            f"Reviewer subprocess for {agent_id} timed out after "
            f"{REVIEWER_TIMEOUT_SECONDS}s"
        ) from exc
    except FileNotFoundError as exc:
        # The Claude CLI is not on PATH; surface a precise message so
        # ops knows exactly what to fix.
        raise ReviewerSpawnError(
            f"Claude CLI executable '{CLAUDE_CLI_EXECUTABLE}' not found on PATH"
        ) from exc

    if result.returncode != 0:
        # Surface stderr verbatim; the CLI's own error messages are
        # usually the most actionable diagnostic.
        raise ReviewerSpawnError(
            f"Reviewer subprocess failed for {agent_id} "
            f"(exit {result.returncode}): {result.stderr.strip()}"
        )

    verdict_text = result.stdout.strip()
    verdict_path = _write_verdict_file(
        agent_id=agent_id,
        verdict_text=verdict_text,
        reviewer_context=reviewer_context,
        outputs_dir=outputs_dir,
    )
    outcome = _parse_outcome(verdict_text)

    _logger.info(
        "Reviewer verdict for %s = %s; written to %s",
        agent_id,
        outcome.value,
        verdict_path,
    )

    return ReviewerVerdict(
        agent_id=agent_id,
        outcome=outcome,
        notes=verdict_text,
        reviewed_context=reviewer_context,
        verdict_path=str(verdict_path),
        reviewed_at=datetime.now(timezone.utc),
    )


async def spawn_reviewer_async(
    agent_id: str,
    reviewer_context: str,
    outputs_dir: Path = OUTPUTS_DIR,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> ReviewerVerdict:
    """Async wrapper around ``spawn_reviewer``. Runs the blocking
    subprocess on the default executor so the FastAPI event loop is
    not stalled while Claude responds. The returned coroutine
    completes when the verdict file has been written."""
    target_loop = loop or asyncio.get_running_loop()
    # run_in_executor with executor=None uses the loop's default thread
    # pool, which is appropriate for short-to-medium blocking calls.
    return await target_loop.run_in_executor(
        None,
        spawn_reviewer,
        agent_id,
        reviewer_context,
        outputs_dir,
    )
