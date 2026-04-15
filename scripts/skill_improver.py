# skill_improver.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Autonomous Karpathy-style self-improvement loop for Claude Code skills using binary assertion eval

"""
Skill Self-Improvement Loop.

Implements the Karpathy-style pattern: eval → analyze failures → propose ONE
targeted SKILL.md change → re-eval → keep if improved, revert if not → repeat.

All changes happen on a dedicated git branch for safety. Every iteration is
logged to history.json for a full audit trail.

Usage::

    improver = SkillImprover("canva-designer", max_iterations=50, target_score=1.0)
    improver.run_loop()
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval_config import (
    BASE_DIR,
    IMPROVEMENT_BRANCH_PREFIX,
    MAX_CONSECUTIVE_FAILURES,
    MAX_FAILED_ASSERTIONS_IN_PROMPT,
    MAX_ITERATIONS_DEFAULT,
    MAX_PREVIOUS_FAILURES_IN_PROMPT,
    NEUTRAL_CWD,
    PROPOSAL_TIMEOUT_SECONDS,
    SKILLS_DIR,
    TARGET_SCORE_DEFAULT,
    get_history_path,
    resolve_claude_cli,
)
from skill_eval_runner import EvalRunner, print_eval_summary
from supervisor_audit import SupervisorAuditor

logger = logging.getLogger("claude-skills.eval.improver")


class SkillImprover:
    """
    Autonomous self-improvement loop for a skill's SKILL.md.

    Creates a git branch, runs baseline eval, then iteratively proposes
    single-change modifications to SKILL.md. Changes that improve the pass
    rate are committed; changes that don't are reverted.

    Args:
        skill_name: Name of the skill directory under skills/.
        max_iterations: Maximum number of improvement iterations.
        target_score: Pass rate to stop at (0.0 to 1.0).
    """

    def __init__(
        self,
        skill_name: str,
        max_iterations: int = MAX_ITERATIONS_DEFAULT,
        target_score: float = TARGET_SCORE_DEFAULT,
    ) -> None:
        self._skill_name = skill_name
        self._max_iterations = max_iterations
        self._target_score = target_score
        self._skill_dir = SKILLS_DIR / skill_name
        self._skill_md_path = self._skill_dir / "SKILL.md"
        self._history_path = get_history_path(skill_name)
        self._history: list[dict[str, Any]] = []
        self._branch_name = ""
        self._baseline_score = 0.0
        self._current_score = 0.0
        self._start_time: datetime | None = None
        self._claude_cli = resolve_claude_cli()
        self._auditor = SupervisorAuditor(skill_name)

    @property
    def skill_name(self) -> str:
        """Read-only access to the target skill name."""
        return self._skill_name

    def run_loop(self, continuation: Any | None = None) -> dict[str, Any]:
        """
        Execute the full self-improvement loop.

        Args:
            continuation: Optional ContinuationAnchor from DiffContinuationEngine.
                When provided, the loop resumes from the anchor's iteration
                instead of starting from scratch.

        Returns:
            Summary dictionary with baseline/final scores, iterations, and timing.
        """
        self._start_time = datetime.now(timezone.utc)

        # Verify SKILL.md exists
        if not self._skill_md_path.exists():
            raise FileNotFoundError(f"SKILL.md not found at {self._skill_md_path}")

        # Determine starting state based on continuation anchor
        start_iteration = 1
        if continuation is not None:
            # Resuming — reuse existing branch and history
            self._branch_name = continuation.branch_name
            start_iteration = continuation.resume_iteration
            self._current_score = continuation.last_score
            self._baseline_score = continuation.last_score

            # Reload history from disk
            if self._history_path.exists():
                try:
                    with self._history_path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._history = data.get("iterations", [])
                    self._baseline_score = data.get("baseline_score", continuation.last_score)
                except (json.JSONDecodeError, OSError):
                    pass

            logger.info(
                "Resuming loop for '%s' at iteration %d (score: %.2f)",
                self._skill_name,
                start_iteration,
                self._current_score,
            )
        else:
            # Fresh start — create branch and backup
            self._branch_name = self._create_branch()
            logger.info("Created branch: %s", self._branch_name)
            self._backup_original()

        try:
            if continuation is None:
                # Run baseline eval only on fresh starts
                print(f"\n--- Baseline Eval for '{self._skill_name}' ---")
                baseline_report = self._run_eval()
                self._baseline_score = baseline_report["summary"]["pass_rate"]
                self._current_score = self._baseline_score

                self._record_history(
                    version="v0",
                    action="baseline",
                    score=self._baseline_score,
                    grading_result="baseline",
                    change_description="Initial baseline evaluation",
                )

                print_eval_summary(baseline_report)

                if self._baseline_score >= self._target_score:
                    print(f"Baseline score {self._baseline_score:.2%} already meets "
                          f"target {self._target_score:.2%}. No improvement needed.")
                    return self._build_summary(iterations=0)

                last_report = baseline_report
            else:
                # On resume, run a fresh eval to get current state
                print(f"\n--- Resume Eval for '{self._skill_name}' (iteration {start_iteration}) ---")
                last_report = self._run_eval()
                self._current_score = last_report["summary"]["pass_rate"]
                print_eval_summary(last_report)

            # Main improvement loop
            consecutive_failures = 0
            iteration = start_iteration

            for iteration in range(start_iteration, self._max_iterations + 1):
                print(f"\n--- Iteration {iteration}/{self._max_iterations} "
                      f"(current: {self._current_score:.2%}) ---")

                # Analyze failures from last run
                failed_assertions = last_report.get("failed_assertions", [])
                if not failed_assertions:
                    print("No failed assertions. Stopping.")
                    break

                # Propose a change
                change_description = self._propose_change(
                    failed_assertions=failed_assertions,
                    iteration=iteration,
                )

                if change_description is None:
                    logger.warning("Failed to get change proposal at iteration %d", iteration)
                    consecutive_failures += 1
                    self._record_history(
                        version=f"v{iteration}",
                        action="proposal_failed",
                        score=self._current_score,
                        grading_result="lost",
                        change_description="Failed to generate proposal",
                    )

                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        print(f"Hit {MAX_CONSECUTIVE_FAILURES} consecutive failures. "
                              f"Trying different strategy...")
                        consecutive_failures = 0
                    continue

                # Run eval on modified SKILL.md
                new_report = self._run_eval()
                new_score = new_report["summary"]["pass_rate"]

                # Compare scores
                if new_score > self._current_score:
                    # Improvement — run supervisor audit before accepting
                    diff = self._get_skill_diff()
                    verdict = self._auditor.review_proposal(diff, new_report)
                    print(f"  Supervisor: {verdict.verdict} (score: {verdict.overall_score})")

                    if verdict.verdict != "APPROVED":
                        # Supervisor rejected — revert despite score improvement
                        self._git_revert()
                        self._record_history(
                            version=f"v{iteration}",
                            action="modify",
                            score=new_score,
                            grading_result="supervisor_rejected",
                            change_description=f"[SUPERVISOR {verdict.verdict}] {change_description}",
                            parent_version=f"v{iteration - 1}" if iteration > start_iteration else "v0",
                        )
                        print(f"  Supervisor rejected: {new_score:.2%} improvement reverted")
                        for issue in verdict.issues[:3]:
                            print(f"    - [{issue.get('severity', '?')}] {issue.get('description', '')[:80]}")
                        consecutive_failures += 1
                        continue

                    # Supervisor approved — commit the change
                    self._git_commit(
                        f"Improve {self._skill_name}: {change_description[:60]}"
                    )
                    self._record_history(
                        version=f"v{iteration}",
                        action="modify",
                        score=new_score,
                        grading_result="won",
                        change_description=change_description,
                        parent_version=f"v{iteration - 1}" if iteration > start_iteration else "v0",
                    )

                    print(f"  Score improved: {self._current_score:.2%} -> {new_score:.2%}")
                    self._current_score = new_score
                    last_report = new_report
                    consecutive_failures = 0

                    # Check if we hit the target
                    if self._current_score >= self._target_score:
                        print(f"\n  Target score {self._target_score:.2%} reached!")
                        break
                else:
                    # No improvement — revert
                    self._git_revert()
                    self._record_history(
                        version=f"v{iteration}",
                        action="modify",
                        score=new_score,
                        grading_result="lost",
                        change_description=change_description,
                        parent_version=f"v{iteration - 1}" if iteration > start_iteration else "v0",
                    )

                    print(f"  No improvement: {self._current_score:.2%} -> {new_score:.2%} (reverted)")
                    consecutive_failures += 1

                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        print(f"  Hit {MAX_CONSECUTIVE_FAILURES} consecutive failures. "
                              f"Trying different strategy...")
                        consecutive_failures = 0

            # Save final history
            self._save_history()

            return self._build_summary(iterations=iteration if 'iteration' in dir() else 0)

        except KeyboardInterrupt:
            print("\n\nInterrupted! Cleaning up...")
            # Revert any uncommitted changes
            self._git_revert()
            self._save_history()
            return self._build_summary(
                iterations=len(self._history) - 1,
                interrupted=True,
            )

    def _run_eval(self) -> dict[str, Any]:
        """
        Delegate to EvalRunner for a full eval pass.

        Returns:
            Grading report dictionary.
        """
        runner = EvalRunner(self._skill_name)
        return runner.run()

    def _propose_change(
        self,
        failed_assertions: list[dict[str, Any]],
        iteration: int,
    ) -> str | None:
        """
        Use Claude to propose ONE targeted SKILL.md change based on failed assertions.

        Reads the current SKILL.md, includes failed assertion details and previous
        failed attempts, and asks for exactly one change.

        Args:
            failed_assertions: List of failed assertion dictionaries from eval report.
            iteration: Current iteration number.

        Returns:
            Description of the change made, or None if proposal failed.
        """
        current_skill_md = self._skill_md_path.read_text(encoding="utf-8")

        # Build failed assertions summary
        failure_lines = []
        for fa in failed_assertions[:MAX_FAILED_ASSERTIONS_IN_PROMPT]:
            failure_lines.append(
                f"- [{fa['category']}] {fa['check']}\n"
                f"  Evidence: {fa['evidence'][:120]}"
            )
        failures_text = "\n".join(failure_lines)

        # Build previous failed attempts summary
        prev_failures = [
            h for h in self._history
            if h.get("grading_result") == "lost" and h.get("action") == "modify"
        ]
        prev_text = ""
        if prev_failures:
            prev_lines = []
            for pf in prev_failures[-MAX_PREVIOUS_FAILURES_IN_PROMPT:]:
                prev_lines.append(
                    f"- {pf['version']}: \"{pf['change_description']}\" "
                    f"-> score {pf['score']:.2%}"
                )
            prev_text = (
                "\n\nPREVIOUS FAILED ATTEMPTS (do not repeat these):\n"
                + "\n".join(prev_lines)
            )

        system_prompt = (
            "You are a skill improvement specialist. You modify Claude Code SKILL.md "
            "files to improve their output quality. Follow the instructions exactly. "
            "Return ONLY the complete modified file content followed by a CHANGE_SUMMARY line."
        )

        user_prompt = (
            f"CURRENT SKILL.md:\n```\n{current_skill_md}\n```\n\n"
            f"FAILED ASSERTIONS (from last eval run):\n{failures_text}"
            f"{prev_text}\n\n"
            "INSTRUCTIONS:\n"
            "1. Make exactly ONE change. Not two. Not zero.\n"
            "2. The change must directly address the most impactful failing assertion.\n"
            "3. Do not modify parts of the SKILL.md that correspond to passing assertions.\n"
            "4. Return the COMPLETE modified SKILL.md content.\n"
            "5. After the SKILL.md content, add a line starting with 'CHANGE_SUMMARY: ' "
            "followed by a one-line summary of what you changed and why.\n\n"
            "Return the complete file content now:"
        )

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        try:
            result = subprocess.run(
                [
                    self._claude_cli, "-p", user_prompt,
                    "--system-prompt", system_prompt,
                    "--tools", "",
                    "--no-session-persistence",
                    "--model", "sonnet",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=PROPOSAL_TIMEOUT_SECONDS,
                env=env,
                cwd=NEUTRAL_CWD,
            )

            if result.returncode != 0:
                logger.warning("Proposal subprocess failed: %s", result.stderr[:200])
                return None

            output = result.stdout.strip()
            return self._apply_proposal(output)

        except subprocess.TimeoutExpired:
            logger.warning("Proposal subprocess timed out")
            return None
        except FileNotFoundError:
            logger.error("claude CLI not found on PATH")
            return None

    def _apply_proposal(self, raw_output: str) -> str | None:
        """
        Parse the proposal output and apply the modified SKILL.md.

        Extracts the SKILL.md content and change summary from the proposal.
        Writes the modified content using atomic temp-then-rename.

        Args:
            raw_output: Raw output from the proposal subprocess.

        Returns:
            Change summary string, or None if parsing failed.
        """
        # Extract change summary
        change_summary = "Unknown change"
        content = raw_output

        if "CHANGE_SUMMARY:" in raw_output:
            parts = raw_output.rsplit("CHANGE_SUMMARY:", 1)
            content = parts[0].strip()
            change_summary = parts[1].strip().split("\n")[0]

        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```markdown or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        # Validate the content looks like a SKILL.md (has frontmatter)
        if not content.strip().startswith("---"):
            logger.warning("Proposed content does not start with frontmatter (---)")
            return None

        if len(content.strip()) < 100:
            logger.warning("Proposed content is suspiciously short (%d chars)", len(content))
            return None

        # Atomic write
        self._write_skill_md(content)
        logger.info("Applied proposal: %s", change_summary)

        return change_summary

    def _write_skill_md(self, content: str) -> None:
        """
        Write modified SKILL.md content using atomic temp-then-rename.

        Args:
            content: New SKILL.md content.
        """
        fd, tmp_path = tempfile.mkstemp(
            suffix=".md",
            dir=str(self._skill_dir),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            Path(tmp_path).replace(self._skill_md_path)
        except Exception:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def _get_skill_diff(self) -> str:
        """
        Get the uncommitted diff of SKILL.md for supervisor review.

        Returns:
            Diff text, or a fallback message if git diff fails.
        """
        rel_path = self._skill_md_path.relative_to(BASE_DIR).as_posix()
        try:
            result = subprocess.run(
                ["git", "diff", "--", rel_path],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            # No diff means changes are staged — try staged diff
            result = subprocess.run(
                ["git", "diff", "--cached", "--", rel_path],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else "(diff unavailable)"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "(diff unavailable)"

    def _create_branch(self) -> str:
        """
        Create a new git branch for this improvement session.

        Returns:
            The branch name created.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        branch = f"{IMPROVEMENT_BRANCH_PREFIX}/{self._skill_name}-{timestamp}"

        subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=str(BASE_DIR),
            capture_output=True,
            check=True,
        )

        return branch

    def _backup_original(self) -> None:
        """Create a backup of the original SKILL.md before any modifications."""
        backup_dir = BASE_DIR / "backups" / "skill-improve"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_dir / f"{self._skill_name}-SKILL-{timestamp}.md"

        shutil.copy2(str(self._skill_md_path), str(backup_path))
        logger.info("Backed up SKILL.md to %s", backup_path)

    def _git_commit(self, message: str) -> None:
        """
        Stage and commit the modified SKILL.md.

        Args:
            message: Commit message.
        """
        rel_path = self._skill_md_path.relative_to(BASE_DIR).as_posix()

        subprocess.run(
            ["git", "add", rel_path],
            cwd=str(BASE_DIR),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(BASE_DIR),
            capture_output=True,
            check=True,
        )
        logger.info("Committed: %s", message)

    def _git_revert(self) -> None:
        """Revert SKILL.md to the last committed version."""
        rel_path = self._skill_md_path.relative_to(BASE_DIR).as_posix()

        subprocess.run(
            ["git", "checkout", "--", rel_path],
            cwd=str(BASE_DIR),
            capture_output=True,
        )
        logger.info("Reverted SKILL.md to last committed version")

    def _record_history(
        self,
        version: str,
        action: str,
        score: float,
        grading_result: str,
        change_description: str,
        parent_version: str | None = None,
    ) -> None:
        """
        Append an iteration record to the in-memory history.

        Args:
            version: Version label (v0, v1, v2...).
            action: Action type (baseline, modify, proposal_failed).
            score: Pass rate after this iteration.
            grading_result: Result category (baseline, won, lost).
            change_description: Description of the change attempted.
            parent_version: The version this iteration was based on.
        """
        record = {
            "version": version,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "action": action,
            "score": round(score, 4),
            "grading_result": grading_result,
            "change_description": change_description,
        }
        if parent_version:
            record["parent_version"] = parent_version

        self._history.append(record)

        # Write history after every iteration for crash resilience
        self._save_history()

    def _save_history(self) -> None:
        """Write the current history to eval/history.json (atomic write)."""
        history_data = {
            "skill_name": self._skill_name,
            "branch": self._branch_name,
            "baseline_score": round(self._baseline_score, 4),
            "current_score": round(self._current_score, 4),
            "iterations": self._history,
        }

        # Ensure parent directory exists
        self._history_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            suffix=".json",
            dir=str(self._history_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            Path(tmp_path).replace(self._history_path)
        except Exception:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def _build_summary(
        self,
        iterations: int,
        interrupted: bool = False,
    ) -> dict[str, Any]:
        """
        Build and print the final summary.

        Args:
            iterations: Number of iterations completed.
            interrupted: Whether the loop was interrupted by user.

        Returns:
            Summary dictionary.
        """
        elapsed = (
            (datetime.now(timezone.utc) - self._start_time).total_seconds()
            if self._start_time
            else 0.0
        )

        wins = sum(1 for h in self._history if h.get("grading_result") == "won")
        losses = sum(1 for h in self._history if h.get("grading_result") == "lost")

        summary = {
            "skill_name": self._skill_name,
            "branch": self._branch_name,
            "baseline_score": round(self._baseline_score, 4),
            "final_score": round(self._current_score, 4),
            "improvement": round(self._current_score - self._baseline_score, 4),
            "iterations": iterations,
            "wins": wins,
            "losses": losses,
            "elapsed_seconds": round(elapsed, 1),
            "interrupted": interrupted,
            "target_reached": self._current_score >= self._target_score,
        }

        # Print summary
        print(f"\n{'='*60}")
        print(f"  SELF-IMPROVEMENT SUMMARY: {self._skill_name}")
        print(f"{'='*60}")
        print(f"  Branch:     {self._branch_name}")
        print(f"  Baseline:   {self._baseline_score:.2%}")
        print(f"  Final:      {self._current_score:.2%}")
        print(f"  Change:     {'+' if summary['improvement'] >= 0 else ''}"
              f"{summary['improvement']:.2%}")
        print(f"  Iterations: {iterations} ({wins} wins, {losses} losses)")
        print(f"  Time:       {elapsed:.0f}s")
        if interrupted:
            print(f"  Status:     INTERRUPTED (Ctrl+C)")
        elif self._current_score >= self._target_score:
            print(f"  Status:     TARGET REACHED")
        else:
            print(f"  Status:     MAX ITERATIONS REACHED")
        print(f"\n  Branch left at: {self._branch_name}")
        print(f"  Review and merge when ready.")
        print(f"{'='*60}\n")

        return summary
