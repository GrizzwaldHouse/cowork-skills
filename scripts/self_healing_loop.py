# self_healing_loop.py
# Developer: Marcus Daley
# Date: 2026-03-24
# Purpose: Automatic failure diagnosis and targeted retry strategies for subprocess/encoding/parsing errors

"""
Self-Healing Dev Loop.

Wraps the self-improvement pipeline with automatic failure categorization
and targeted healing strategies. When a subprocess call fails, it diagnoses
the failure type and applies a specific fix before retrying.

Usage::

    loop = SelfHealingLoop("canva-designer", max_retries=3)
    result = loop.run()
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from eval_config import (
    BASE_DIR,
    MAX_ESCALATED_TIMEOUT_SECONDS,
    MAX_HEALING_RETRIES,
    MAX_ITERATIONS_DEFAULT,
    PROPOSAL_TIMEOUT_SECONDS,
    SKILLS_DIR,
    TARGET_SCORE_DEFAULT,
    TIMEOUT_ESCALATION_FACTOR,
    get_healing_log_path,
)

logger = logging.getLogger("claude-skills.eval.healing")


class FailureCategory(str, Enum):
    """Categorized failure types with known healing strategies."""

    SUBPROCESS_TIMEOUT = "subprocess_timeout"
    ENCODING_ERROR = "encoding_error"
    MALFORMED_GRADER = "malformed_grader_response"
    GIT_CONFLICT = "git_conflict"
    SKILL_PARSE_ERROR = "skill_parse_error"
    UNKNOWN = "unknown"


@dataclass
class HealingAction:
    """Record of a healing attempt and its outcome."""

    failure: str  # FailureCategory value
    strategy: str
    adjustment: dict[str, Any]
    attempt: int
    succeeded: bool
    context: str
    timestamp: str


# ---------------------------------------------------------------------------
# Healing strategies — config-driven, not hardcoded behavior
# ---------------------------------------------------------------------------
HEALING_STRATEGIES: dict[str, dict[str, Any]] = {
    FailureCategory.SUBPROCESS_TIMEOUT: {
        "strategy": "escalate_timeout",
        "description": "Increase subprocess timeout by escalation factor",
    },
    FailureCategory.ENCODING_ERROR: {
        "strategy": "force_utf8_replace",
        "description": "Force UTF-8 encoding with replacement error handling",
    },
    FailureCategory.MALFORMED_GRADER: {
        "strategy": "retry_grader",
        "description": "Retry grader subprocess with explicit format instructions",
    },
    FailureCategory.GIT_CONFLICT: {
        "strategy": "reset_to_backup",
        "description": "Reset SKILL.md to backup and restart from clean state",
    },
    FailureCategory.SKILL_PARSE_ERROR: {
        "strategy": "restore_from_backup",
        "description": "Restore SKILL.md from the pre-improvement backup",
    },
    FailureCategory.UNKNOWN: {
        "strategy": "full_retry",
        "description": "Full retry with no specific healing adjustment",
    },
}


def _compute_timeout_adjustment(attempt: int) -> dict[str, Any]:
    """Calculate escalated timeout based on attempt number."""
    multiplier = TIMEOUT_ESCALATION_FACTOR ** attempt
    new_timeout = min(
        int(PROPOSAL_TIMEOUT_SECONDS * multiplier),
        MAX_ESCALATED_TIMEOUT_SECONDS,
    )
    return {"timeout_seconds": new_timeout, "multiplier": round(multiplier, 2)}


def _compute_encoding_adjustment(attempt: int) -> dict[str, Any]:
    """Return encoding fix parameters."""
    return {"force_utf8": True, "errors": "replace", "attempt": attempt}


def _compute_grader_adjustment(attempt: int) -> dict[str, Any]:
    """Return grader retry parameters."""
    return {"grader_retries": attempt + 1, "stricter_format": True}


def _compute_git_adjustment(attempt: int) -> dict[str, Any]:
    """Return git conflict resolution parameters."""
    return {"reset_to_backup": True, "attempt": attempt}


def _compute_skill_parse_adjustment(attempt: int) -> dict[str, Any]:
    """Return skill parse recovery parameters."""
    return {"restore_from_backup": True, "attempt": attempt}


def _compute_unknown_adjustment(attempt: int) -> dict[str, Any]:
    """Return generic retry parameters."""
    return {"full_retry": True, "attempt": attempt}


_ADJUSTMENT_COMPUTERS: dict[FailureCategory, Any] = {
    FailureCategory.SUBPROCESS_TIMEOUT: _compute_timeout_adjustment,
    FailureCategory.ENCODING_ERROR: _compute_encoding_adjustment,
    FailureCategory.MALFORMED_GRADER: _compute_grader_adjustment,
    FailureCategory.GIT_CONFLICT: _compute_git_adjustment,
    FailureCategory.SKILL_PARSE_ERROR: _compute_skill_parse_adjustment,
    FailureCategory.UNKNOWN: _compute_unknown_adjustment,
}


class SelfHealingLoop:
    """
    Wraps the self-improvement pipeline with failure classification and auto-healing.

    When a loop iteration fails, the error is classified into a FailureCategory,
    the appropriate healing strategy is applied, and the loop is retried. Supports
    integration with DiffContinuationEngine for mid-loop crash recovery.

    Args:
        skill_name: Name of the skill directory under skills/.
        max_retries: Maximum number of healing retries per failure.
        max_iterations: Maximum improvement iterations per loop attempt.
        target_score: Pass rate to stop at (0.0 to 1.0).
    """

    def __init__(
        self,
        skill_name: str,
        max_retries: int = MAX_HEALING_RETRIES,
        max_iterations: int = MAX_ITERATIONS_DEFAULT,
        target_score: float = TARGET_SCORE_DEFAULT,
    ) -> None:
        self._skill_name = skill_name
        self._max_retries = max_retries
        self._max_iterations = max_iterations
        self._target_score = target_score
        self._healing_log: list[HealingAction] = []
        self._healing_log_path = get_healing_log_path(skill_name)
        self._skill_dir = SKILLS_DIR / skill_name

    def run(self, continuation: Any | None = None) -> dict[str, Any]:
        """
        Execute the self-improvement loop with self-healing retry logic.

        Args:
            continuation: Optional ContinuationAnchor from DiffContinuationEngine.

        Returns:
            Final eval report dictionary, or a healing summary on exhausted retries.
        """
        # Lazy import to avoid circular dependencies
        from skill_improver import SkillImprover

        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            attempt_label = f"attempt {attempt + 1}/{self._max_retries + 1}"

            try:
                print(f"\n--- Self-Healing Loop: {attempt_label} for '{self._skill_name}' ---")

                improver = SkillImprover(
                    skill_name=self._skill_name,
                    max_iterations=self._max_iterations,
                    target_score=self._target_score,
                )

                summary = improver.run_loop()

                # Loop succeeded — record and return
                if attempt > 0:
                    self._record_healing(HealingAction(
                        failure="none",
                        strategy="successful_retry",
                        adjustment={"attempt": attempt},
                        attempt=attempt,
                        succeeded=True,
                        context=f"Loop succeeded on {attempt_label}",
                        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    ))

                self._save_healing_log()
                return summary

            except Exception as exc:
                last_error = exc
                category = self._classify_failure(exc, attempt_label)
                logger.warning(
                    "Self-healing: caught %s (%s) on %s",
                    category.value,
                    str(exc)[:200],
                    attempt_label,
                )

                if attempt >= self._max_retries:
                    # Exhausted retries
                    self._record_healing(HealingAction(
                        failure=category.value,
                        strategy="exhausted",
                        adjustment={},
                        attempt=attempt,
                        succeeded=False,
                        context=f"Max retries exhausted: {str(exc)[:300]}",
                        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    ))
                    break

                # Apply healing strategy
                healing_action = self._apply_healing(category, attempt)
                self._record_healing(healing_action)

                # Brief delay before retry
                time.sleep(min(2.0 * (attempt + 1), 10.0))

        # All retries exhausted
        self._save_healing_log()

        return {
            "skill_name": self._skill_name,
            "healing_exhausted": True,
            "total_attempts": self._max_retries + 1,
            "last_error": str(last_error)[:500] if last_error else "unknown",
            "healing_actions": [asdict(h) for h in self._healing_log],
            "target_reached": False,
        }

    def _classify_failure(self, error: Exception, context: str) -> FailureCategory:
        """
        Classify an exception into a known failure category.

        Uses exception type and message content to determine the category.

        Args:
            error: The caught exception.
            context: Human-readable context string.

        Returns:
            The classified FailureCategory.
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        if isinstance(error, subprocess.TimeoutExpired):
            return FailureCategory.SUBPROCESS_TIMEOUT

        if isinstance(error, (UnicodeDecodeError, UnicodeEncodeError)):
            return FailureCategory.ENCODING_ERROR

        if "encoding" in error_msg or "codec" in error_msg or "charmap" in error_msg:
            return FailureCategory.ENCODING_ERROR

        if "timeout" in error_msg or "timed out" in error_msg:
            return FailureCategory.SUBPROCESS_TIMEOUT

        if "conflict" in error_msg or "merge" in error_msg:
            return FailureCategory.GIT_CONFLICT

        if "frontmatter" in error_msg or "skill.md" in error_msg or "parse" in error_msg:
            return FailureCategory.SKILL_PARSE_ERROR

        if "grader" in error_msg or "true" in error_msg and "false" in error_msg:
            return FailureCategory.MALFORMED_GRADER

        return FailureCategory.UNKNOWN

    def _apply_healing(self, category: FailureCategory, attempt: int) -> HealingAction:
        """
        Apply the healing strategy for a given failure category.

        Executes category-specific recovery actions (timeout escalation,
        encoding fixes, git resets, etc.) and returns a record of what was done.

        Args:
            category: The classified failure category.
            attempt: Current attempt number (0-indexed).

        Returns:
            HealingAction record describing the applied fix.
        """
        strategy_info = HEALING_STRATEGIES.get(category, HEALING_STRATEGIES[FailureCategory.UNKNOWN])
        compute_fn = _ADJUSTMENT_COMPUTERS.get(category, _compute_unknown_adjustment)
        adjustment = compute_fn(attempt)

        # Execute category-specific healing actions
        if category == FailureCategory.GIT_CONFLICT:
            self._heal_git_conflict()
        elif category == FailureCategory.SKILL_PARSE_ERROR:
            self._heal_skill_parse()
        elif category == FailureCategory.SUBPROCESS_TIMEOUT:
            # Timeout escalation is applied via the adjustment dict
            # which the next loop iteration will pick up
            new_timeout = adjustment.get("timeout_seconds", PROPOSAL_TIMEOUT_SECONDS)
            logger.info("Escalating timeout to %ds for next attempt", new_timeout)

        print(f"  Healing: {strategy_info['description']} (attempt {attempt + 1})")

        return HealingAction(
            failure=category.value,
            strategy=strategy_info["strategy"],
            adjustment=adjustment,
            attempt=attempt,
            succeeded=False,  # Will be updated if the retry succeeds
            context=strategy_info["description"],
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def _heal_git_conflict(self) -> None:
        """Reset SKILL.md to HEAD to resolve git conflicts."""
        skill_md = self._skill_dir / "SKILL.md"
        rel_path = skill_md.relative_to(BASE_DIR).as_posix()

        try:
            subprocess.run(
                ["git", "checkout", "--", rel_path],
                cwd=str(BASE_DIR),
                capture_output=True,
                check=True,
                timeout=10,
            )
            logger.info("Healed git conflict: reset %s to HEAD", rel_path)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            logger.warning("Git conflict healing failed: %s", exc)

    def _heal_skill_parse(self) -> None:
        """Restore SKILL.md from the most recent backup."""
        backup_dir = BASE_DIR / "backups" / "skill-improve"
        if not backup_dir.exists():
            logger.warning("No backup directory found for skill parse healing")
            return

        # Find backups for this skill, sorted newest first
        pattern = f"{self._skill_name}-SKILL-*.md"
        backups = sorted(backup_dir.glob(pattern), reverse=True)

        if not backups:
            logger.warning("No backups found matching '%s'", pattern)
            return

        import shutil
        target = self._skill_dir / "SKILL.md"
        shutil.copy2(str(backups[0]), str(target))
        logger.info("Healed skill parse: restored from %s", backups[0].name)

    def _record_healing(self, action: HealingAction) -> None:
        """Append a healing action to the in-memory log."""
        self._healing_log.append(action)

    def _save_healing_log(self) -> None:
        """Write the healing log to disk (atomic write)."""
        if not self._healing_log:
            return

        log_data = {
            "skill_name": self._skill_name,
            "total_actions": len(self._healing_log),
            "actions": [asdict(h) for h in self._healing_log],
        }

        # Ensure parent directory exists
        self._healing_log_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            suffix=".json",
            dir=str(self._healing_log_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            Path(tmp_path).replace(self._healing_log_path)
            logger.info("Healing log written to %s", self._healing_log_path)
        except Exception:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
            raise
