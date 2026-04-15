# diff_continuation.py
# Developer: Marcus Daley
# Date: 2026-03-24
# Purpose: Crash-resilient session recovery that resumes interrupted improvement loops from the exact iteration

"""
Diff-Based Continuation Engine.

When a self-improvement loop is interrupted (crash, timeout, Ctrl+C), this module
reconstructs the loop state from git history, history.json, and eval results so the
loop resumes at the correct iteration rather than starting over.

Usage::

    engine = DiffContinuationEngine("canva-designer")
    anchor = engine.detect_interrupted_loop()
    if anchor:
        print(f"Resume from iteration {anchor.resume_iteration}")
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval_config import (
    BASE_DIR,
    IMPROVEMENT_BRANCH_PREFIX,
    RESULTS_DIR_NAME,
    SKILLS_DIR,
    EVAL_DIR_NAME,
    get_history_path,
    get_results_dir,
)

logger = logging.getLogger("claude-skills.eval.continuation")


@dataclass(frozen=True)
class ContinuationAnchor:
    """Immutable snapshot of an interrupted loop's state for resumption."""

    skill_name: str
    resume_iteration: int
    last_score: float
    pending_failures: list[dict[str, str]]  # from last eval
    skill_state: str  # "CLEAN" | "MODIFIED" | "DIRTY"
    branch_name: str
    last_history_entry: dict[str, Any] | None
    timestamp: str


class DiffContinuationEngine:
    """
    Detects and reconstructs state from interrupted self-improvement loops.

    Inspects git branches, history.json, and eval results to determine
    whether an interrupted loop exists and where to resume.

    Args:
        skill_name: Name of the skill directory under skills/.
    """

    def __init__(self, skill_name: str) -> None:
        self._skill_name = skill_name
        self._skill_dir = SKILLS_DIR / skill_name
        self._history_path = get_history_path(skill_name)

    def detect_interrupted_loop(self) -> ContinuationAnchor | None:
        """
        Attempt to detect an interrupted improvement loop.

        Checks for improvement branches, reads history.json, finds the latest
        eval results, and determines the skill file state.

        Returns:
            ContinuationAnchor if an interrupted loop is found, None otherwise.
        """
        # Check for an improvement branch
        branch_name, skill_state = self._check_git_state()

        if not branch_name:
            logger.info("No improvement branch found for '%s'", self._skill_name)
            return None

        # Read history.json
        history_entries = self._read_history()
        if not history_entries:
            logger.info("No history entries found for '%s'", self._skill_name)
            return None

        # Find the last entry and extract iteration number/score
        last_entry = history_entries[-1]
        last_version = last_entry.get("version", "v0")

        # Parse iteration number from version string (e.g. "v3" -> 3)
        try:
            resume_iteration = int(last_version.lstrip("v")) + 1
        except ValueError:
            resume_iteration = len(history_entries)

        last_score = last_entry.get("score", 0.0)

        # Find pending failures from latest results
        latest_results = self._find_latest_results()
        pending_failures = self._extract_pending_failures(latest_results) if latest_results else []

        logger.info(
            "Detected interrupted loop for '%s': branch=%s, resume_at=%d, score=%.2f, state=%s",
            self._skill_name,
            branch_name,
            resume_iteration,
            last_score,
            skill_state,
        )

        return ContinuationAnchor(
            skill_name=self._skill_name,
            resume_iteration=resume_iteration,
            last_score=last_score,
            pending_failures=pending_failures,
            skill_state=skill_state,
            branch_name=branch_name,
            last_history_entry=last_entry,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def _read_history(self) -> list[dict[str, Any]]:
        """
        Read and return the iterations list from history.json.

        Returns:
            List of iteration records, or empty list if unavailable.
        """
        if not self._history_path.exists():
            return []

        try:
            with self._history_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("iterations", [])
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read history.json: %s", exc)
            return []

    def _find_latest_results(self) -> dict[str, Any] | None:
        """
        Find and load the most recent eval results file.

        Returns:
            Parsed results dictionary, or None if no results found.
        """
        results_dir = self._skill_dir / EVAL_DIR_NAME / RESULTS_DIR_NAME
        if not results_dir.exists():
            return None

        # Find run-*.json files sorted by name (timestamp-based)
        result_files = sorted(results_dir.glob("run-*.json"), reverse=True)
        if not result_files:
            return None

        try:
            with result_files[0].open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read latest results file: %s", exc)
            return None

    def _check_git_state(self) -> tuple[str, str]:
        """
        Check for an improvement branch and the working tree state.

        Returns:
            Tuple of (branch_name, skill_state). branch_name is empty string
            if no improvement branch is checked out.
            skill_state: "CLEAN" | "MODIFIED" | "DIRTY"
        """
        # Get current branch name
        current_branch = self._run_git("git", "rev-parse", "--abbrev-ref", "HEAD")
        if not current_branch:
            return "", "CLEAN"

        # Check if we're on an improvement branch for this skill
        expected_prefix = f"{IMPROVEMENT_BRANCH_PREFIX}/{self._skill_name}-"
        if not current_branch.startswith(expected_prefix):
            # Not on an improvement branch — check if one exists
            branch_list = self._run_git(
                "git", "branch", "--list", f"{IMPROVEMENT_BRANCH_PREFIX}/{self._skill_name}-*"
            )
            if branch_list:
                # Found improvement branches — use the most recent one
                branches = [b.strip().lstrip("* ") for b in branch_list.splitlines() if b.strip()]
                if branches:
                    # Sort by timestamp suffix (descending)
                    branches.sort(reverse=True)
                    current_branch = branches[0]
                else:
                    return "", "CLEAN"
            else:
                return "", "CLEAN"

        # Determine skill file state via git status
        rel_path = self._skill_dir.relative_to(BASE_DIR).as_posix()
        status_output = self._run_git("git", "status", "--porcelain", rel_path)

        if not status_output:
            skill_state = "CLEAN"
        else:
            # Parse porcelain output: first two chars indicate staging/working tree state
            for line in status_output.splitlines():
                if not line.strip():
                    continue
                index_status = line[0] if len(line) > 0 else " "
                worktree_status = line[1] if len(line) > 1 else " "

                if index_status != " " and index_status != "?":
                    skill_state = "MODIFIED"  # Staged changes
                    break
                elif worktree_status != " ":
                    skill_state = "DIRTY"  # Unstaged changes
                    break
            else:
                skill_state = "CLEAN"

        return current_branch, skill_state

    def _extract_pending_failures(self, results: dict[str, Any]) -> list[dict[str, str]]:
        """
        Extract failed assertions from an eval results dictionary.

        Args:
            results: Parsed eval results JSON.

        Returns:
            List of failure dictionaries with check/evidence/category fields.
        """
        failed = results.get("failed_assertions", [])
        pending: list[dict[str, str]] = []

        for fa in failed:
            pending.append({
                "assertion_id": str(fa.get("assertion_id", "")),
                "check": str(fa.get("check", "")),
                "category": str(fa.get("category", "")),
                "evidence": str(fa.get("evidence", ""))[:200],
            })

        return pending

    def _run_git(self, *args: str) -> str | None:
        """
        Execute a git command and return stdout, or None on failure.

        Args:
            *args: Command and arguments (e.g. "git", "status").

        Returns:
            Stripped stdout string, or None if the command failed.
        """
        try:
            result = subprocess.run(
                list(args),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                cwd=str(BASE_DIR),
            )
            if result.returncode != 0:
                return None
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
