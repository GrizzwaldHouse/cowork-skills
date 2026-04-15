# skill_eval_runner.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Runs test prompts through a skill and grades output against binary assertions using claude -p subprocess

"""
Skill Evaluation Runner.

Executes test prompts from eval.json through ``claude -p`` with the target skill
loaded, then grades each output against binary TRUE/FALSE assertions using a
separate grader subprocess. Results are written to eval/results/ in a structured
JSON format.

Usage::

    runner = EvalRunner("canva-designer")
    report = runner.run()
    print(f"Pass rate: {report['summary']['pass_rate']}")
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval_config import (
    BASE_DIR,
    EVAL_TIMEOUT_SECONDS,
    GRADER_TIMEOUT_SECONDS,
    NEUTRAL_CWD,
    SKILLS_DIR,
    get_results_dir,
    load_eval_json,
    resolve_claude_cli,
)

logger = logging.getLogger("claude-skills.eval.runner")

# ---------------------------------------------------------------------------
# Grader system prompt — forces binary TRUE/FALSE responses
# ---------------------------------------------------------------------------
GRADER_SYSTEM_PROMPT = (
    "You are a strict binary grader. You will be given an AI-generated output "
    "and an assertion to check. Respond with EXACTLY one of these formats:\n\n"
    "TRUE: <one sentence of evidence from the output>\n"
    "FALSE: <one sentence explaining what is missing or wrong>\n\n"
    "Do NOT add any other text, explanation, or caveats. Just TRUE or FALSE "
    "followed by a colon and one sentence."
)


class EvalRunner:
    """
    Runs eval assertions against a skill's output using claude -p.

    Loads eval.json, executes each test prompt through the skill, then
    grades every assertion via a separate grader call. Writes results
    to the skill's eval/results/ directory.

    Args:
        skill_name: Name of the skill directory under skills/.
        timeout: Seconds to wait for each test case subprocess.
        grader_timeout: Seconds to wait for each grader subprocess.
    """

    def __init__(
        self,
        skill_name: str,
        timeout: int = EVAL_TIMEOUT_SECONDS,
        grader_timeout: int = GRADER_TIMEOUT_SECONDS,
    ) -> None:
        self._skill_name = skill_name
        self._timeout = timeout
        self._grader_timeout = grader_timeout
        self._skill_dir = SKILLS_DIR / skill_name
        self._eval_config: dict[str, Any] = {}
        self._claude_cli = resolve_claude_cli()

    @property
    def skill_name(self) -> str:
        """Read-only access to the target skill name."""
        return self._skill_name

    def run(self) -> dict[str, Any]:
        """
        Execute the full eval run across all test cases.

        Returns:
            Complete grading report dictionary with per-case results and summary.
        """
        self._eval_config = load_eval_json(self._skill_name)

        test_cases = self._eval_config["test_cases"]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        logger.info(
            "Starting eval run for '%s': %d test cases",
            self._skill_name,
            len(test_cases),
        )

        case_results: list[dict[str, Any]] = []
        total_assertions = 0
        total_passed = 0

        for case in test_cases:
            result = self._run_test_case(case)
            case_results.append(result)

            passed = sum(1 for a in result["assertion_results"] if a["passed"])
            total = len(result["assertion_results"])
            total_assertions += total
            total_passed += passed

            logger.info(
                "  Case %d: %d/%d assertions passed",
                case["id"],
                passed,
                total,
            )

        pass_rate = total_passed / total_assertions if total_assertions > 0 else 0.0

        report = self._build_grading_report(
            case_results=case_results,
            timestamp=timestamp,
            total_assertions=total_assertions,
            total_passed=total_passed,
            pass_rate=pass_rate,
        )

        # Write results to disk
        self._write_results(report, timestamp)

        logger.info(
            "Eval complete for '%s': %d/%d passed (%.1f%%)",
            self._skill_name,
            total_passed,
            total_assertions,
            pass_rate * 100,
        )

        return report

    def _run_test_case(self, case: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a single test case: run prompt, grade all assertions.

        Args:
            case: Test case dictionary from eval.json.

        Returns:
            Dictionary with output text and per-assertion grading results.
        """
        prompt = case["prompt"]
        case_id = case["id"]

        logger.info("  Running test case %d...", case_id)

        # Run the prompt through claude -p with the skill loaded
        output = self._execute_prompt(prompt)

        if output is None:
            # Subprocess failed — mark all assertions as failed
            return {
                "case_id": case_id,
                "prompt": prompt,
                "output": "[ERROR: subprocess failed or timed out]",
                "assertion_results": [
                    {
                        "assertion_id": a["id"],
                        "check": a["check"],
                        "category": a["category"],
                        "passed": False,
                        "evidence": "Test case execution failed",
                    }
                    for a in case["assertions"]
                ],
            }

        # Grade each assertion against the output
        assertion_results = self._grade_assertions(output, case["assertions"])

        return {
            "case_id": case_id,
            "prompt": prompt,
            "output": output,
            "assertion_results": assertion_results,
        }

    def _execute_prompt(self, prompt: str) -> str | None:
        """
        Run a prompt through claude -p as a subprocess.

        Combines the skill SKILL.md content and the test prompt into a single
        -p argument piped via stdin. Avoids --system-prompt to prevent
        Windows command-line length and pipe buffering issues.

        Args:
            prompt: The test prompt to execute.

        Returns:
            The claude output text, or None if execution failed.
        """
        skill_md_path = self._skill_dir / "SKILL.md"

        # Combine skill context + prompt into a single user message
        combined_prompt = (
            "You have the following skill loaded. Follow its rules "
            "and patterns when responding to the request below.\n\n"
            "<skill>\n"
            + skill_md_path.read_text(encoding="utf-8")
            + "\n</skill>\n\n"
            "REQUEST:\n" + prompt
        )

        return self._call_claude(
            prompt=combined_prompt,
            timeout=self._timeout,
            model="sonnet",
        )

    def _grade_assertions(
        self,
        output: str,
        assertions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Grade each assertion against the output using a grader subprocess.

        Args:
            output: The full text output from the test prompt.
            assertions: List of assertion dictionaries from eval.json.

        Returns:
            List of grading result dictionaries with passed/evidence fields.
        """
        results: list[dict[str, Any]] = []

        for assertion in assertions:
            grader_prompt = (
                f"## Output to evaluate\n\n{output}\n\n"
                f"## Assertion to check\n\n{assertion['check']}\n\n"
                f"Is the above assertion TRUE or FALSE about the output? "
                f"Respond with exactly: TRUE: <evidence> or FALSE: <evidence>"
            )

            passed, evidence = self._call_grader(grader_prompt)

            results.append({
                "assertion_id": assertion["id"],
                "check": assertion["check"],
                "category": assertion["category"],
                "passed": passed,
                "evidence": evidence,
            })

        return results

    def _call_claude(
        self,
        prompt: str,
        timeout: int,
        model: str = "sonnet",
    ) -> str | None:
        """
        Call claude -p with proper isolation for eval subprocess.

        Pipes the prompt via stdin to avoid Windows command-line length limits.
        Uses --tools "" (no tools), --no-session-persistence, and runs from
        a neutral temp directory to avoid loading project CLAUDE.md context.

        Args:
            prompt: Combined prompt to send (includes all context).
            timeout: Seconds before timing out.
            model: Model to use (sonnet, haiku, opus).

        Returns:
            The claude output text, or None if execution failed.
        """
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        try:
            result = subprocess.run(
                [
                    self._claude_cli, "-p",
                    "--tools", "",
                    "--no-session-persistence",
                    "--model", model,
                ],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env,
                cwd=NEUTRAL_CWD,
            )

            if result.returncode != 0:
                logger.warning(
                    "claude -p returned code %d: %s",
                    result.returncode,
                    result.stderr[:200] if result.stderr else "(no stderr)",
                )
                return None

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.warning("claude -p timed out after %ds", timeout)
            return None
        except FileNotFoundError:
            logger.error("claude CLI not found at '%s'", self._claude_cli)
            return None

    def _call_grader(self, grader_prompt: str) -> tuple[bool, str]:
        """
        Call the grader via claude -p with strict TRUE/FALSE instructions.

        Combines the grading system instructions with the grader prompt
        into a single message piped via stdin.

        Args:
            grader_prompt: The grading prompt with output and assertion.

        Returns:
            Tuple of (passed: bool, evidence: str).
        """
        combined = f"{GRADER_SYSTEM_PROMPT}\n\n{grader_prompt}"

        response = self._call_claude(
            prompt=combined,
            timeout=self._grader_timeout,
            model="haiku",
        )

        if response is None:
            return False, "Grader subprocess failed or timed out"

        return self._parse_grader_response(response)

    def _parse_grader_response(self, response: str) -> tuple[bool, str]:
        """
        Parse the grader's TRUE/FALSE response.

        Handles variations in formatting (case, whitespace, punctuation).

        Args:
            response: Raw grader output string.

        Returns:
            Tuple of (passed: bool, evidence: str).
        """
        response = response.strip()

        # Handle multi-line responses — take the first meaningful line
        first_line = ""
        for line in response.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith(("TRUE", "FALSE")):
                first_line = stripped
                break
        if not first_line:
            first_line = response.splitlines()[0] if response else ""

        upper = first_line.upper()

        if upper.startswith("TRUE"):
            evidence = first_line.split(":", 1)[1].strip() if ":" in first_line else ""
            return True, evidence

        if upper.startswith("FALSE"):
            evidence = first_line.split(":", 1)[1].strip() if ":" in first_line else ""
            return False, evidence

        # Ambiguous response — treat as failure with the raw response as evidence
        logger.warning("Ambiguous grader response: %s", first_line[:100])
        return False, f"Ambiguous grader response: {first_line[:100]}"

    def _build_grading_report(
        self,
        case_results: list[dict[str, Any]],
        timestamp: str,
        total_assertions: int,
        total_passed: int,
        pass_rate: float,
    ) -> dict[str, Any]:
        """
        Assemble the full grading report.

        Args:
            case_results: Per-case grading results.
            timestamp: ISO timestamp for this run.
            total_assertions: Total number of assertions evaluated.
            total_passed: Number of assertions that passed.
            pass_rate: Pass rate as a float between 0.0 and 1.0.

        Returns:
            Complete grading report dictionary.
        """
        # Build per-category breakdown
        category_stats: dict[str, dict[str, int]] = {}
        for case in case_results:
            for ar in case["assertion_results"]:
                cat = ar["category"]
                if cat not in category_stats:
                    category_stats[cat] = {"passed": 0, "total": 0}
                category_stats[cat]["total"] += 1
                if ar["passed"]:
                    category_stats[cat]["passed"] += 1

        # Build list of failed assertions for easy analysis
        failed_assertions: list[dict[str, Any]] = []
        for case in case_results:
            for ar in case["assertion_results"]:
                if not ar["passed"]:
                    failed_assertions.append({
                        "case_id": case["case_id"],
                        "assertion_id": ar["assertion_id"],
                        "check": ar["check"],
                        "category": ar["category"],
                        "evidence": ar["evidence"],
                    })

        return {
            "skill_name": self._skill_name,
            "timestamp": timestamp,
            "eval_version": self._eval_config.get("version", "unknown"),
            "summary": {
                "total_assertions": total_assertions,
                "total_passed": total_passed,
                "pass_rate": round(pass_rate, 4),
                "total_test_cases": len(case_results),
                "category_breakdown": {
                    cat: {
                        "passed": stats["passed"],
                        "total": stats["total"],
                        "rate": round(stats["passed"] / stats["total"], 4)
                        if stats["total"] > 0
                        else 0.0,
                    }
                    for cat, stats in sorted(category_stats.items())
                },
            },
            "failed_assertions": failed_assertions,
            "test_cases": case_results,
        }

    def _write_results(self, report: dict[str, Any], timestamp: str) -> None:
        """
        Write grading results to the eval/results/ directory.

        Uses atomic temp-then-rename for crash safety.

        Args:
            report: Complete grading report dictionary.
            timestamp: ISO timestamp used in the filename.
        """
        results_dir = get_results_dir(self._skill_name)
        target_path = results_dir / f"run-{timestamp}.json"

        # Atomic write: write to temp file, then rename
        fd, tmp_path = tempfile.mkstemp(
            suffix=".json",
            dir=str(results_dir),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            Path(tmp_path).replace(target_path)
            logger.info("Results written to %s", target_path)
        except Exception:
            # Clean up temp file on failure
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
            raise


def run_eval(skill_name: str) -> dict[str, Any]:
    """
    Convenience function: run eval for a skill and return the report.

    Args:
        skill_name: Name of the skill to evaluate.

    Returns:
        Complete grading report dictionary.
    """
    runner = EvalRunner(skill_name)
    return runner.run()


def print_eval_summary(report: dict[str, Any]) -> None:
    """
    Print a human-readable eval summary to stdout.

    Args:
        report: Grading report from EvalRunner.run().
    """
    summary = report["summary"]

    print(f"\n{'='*60}")
    print(f"  EVAL RESULTS: {report['skill_name']}")
    print(f"{'='*60}")
    print(f"  Pass Rate:  {summary['pass_rate']*100:.1f}%")
    print(f"  Passed:     {summary['total_passed']}/{summary['total_assertions']}")
    print(f"  Test Cases: {summary['total_test_cases']}")
    print()

    if summary["category_breakdown"]:
        print("  Category Breakdown:")
        for cat, stats in summary["category_breakdown"].items():
            bar = "#" * int(stats["rate"] * 20) + "-" * (20 - int(stats["rate"] * 20))
            print(f"    {cat:<12} [{bar}] {stats['passed']}/{stats['total']}")
        print()

    failed = report.get("failed_assertions", [])
    if failed:
        print(f"  Failed Assertions ({len(failed)}):")
        for fa in failed:
            print(f"    Case {fa['case_id']}: [{fa['category']}] {fa['assertion_id']}")
            print(f"      Check: {fa['check'][:80]}...")
            print(f"      Evidence: {fa['evidence'][:80]}")
            print()
    else:
        print("  All assertions passed!")

    print(f"{'='*60}\n")
