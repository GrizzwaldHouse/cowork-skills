# supervisor_audit.py
# Developer: Marcus Daley
# Date: 2026-03-24
# Purpose: Independent supervisor quality gate that reviews proposed SKILL.md changes against the 5-criterion rubric

"""
Supervisor Audit Module.

After each self-improvement proposal, a supervisor agent (claude -p with haiku)
reviews the diff against the 5-criterion rubric from the Supervisor Review Protocol.
Acts as an independent quality gate — changes that fail any criterion below 70 are
reverted automatically.

Usage::

    auditor = SupervisorAuditor("canva-designer")
    verdict = auditor.review_proposal(diff_text, eval_report)
    if verdict.verdict != "APPROVED":
        # revert the change
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval_config import (
    AUDIT_LOG_NAME,
    NEUTRAL_CWD,
    RUBRIC_WEIGHTS,
    SUPERVISOR_MODEL,
    SUPERVISOR_PASSING_SCORE,
    SUPERVISOR_TIMEOUT_SECONDS,
    get_audit_log_path,
    resolve_claude_cli,
)

logger = logging.getLogger("claude-skills.eval.supervisor")


@dataclass(frozen=True)
class SupervisorVerdict:
    """Immutable result of a supervisor review pass."""

    review_id: str
    verdict: str  # "APPROVED" | "REVISION_REQUIRED" | "REJECTED"
    overall_score: int
    criteria_scores: dict[str, int]  # 5 keys matching rubric
    issues: list[dict[str, str]]
    timestamp: str


# ---------------------------------------------------------------------------
# Rubric criteria descriptions — embedded from supervisor_review_protocol.md
# ---------------------------------------------------------------------------
_CRITERIA_DESCRIPTIONS: dict[str, str] = {
    "comment_code_alignment": (
        "Every function has step-comments BEFORE implementation. "
        "Comments explain WHY decisions were made, not WHAT the code does. "
        "Implementation beneath each comment matches the described intent. "
        "If comment and code disagree, the comment was updated (not deleted)."
    ),
    "architecture_compliance": (
        "Event-driven only (no polling loops). Dependency injection (no direct instantiation "
        "in business logic). Separation of concerns. Config-driven (no magic numbers or "
        "hardcoded values). Repository pattern for data access. No public mutable state."
    ),
    "build_cleanliness": (
        "Zero compilation errors. Zero warnings. No deprecated API usage. "
        "Dependencies minimized in headers/declarations."
    ),
    "defensive_programming": (
        "Input validation at system boundaries. Null/undefined checks before dereference. "
        "Typed error handling (no bare catch/except). Fail-fast on invalid state. "
        "Subscription cleanup in destructors/teardown."
    ),
    "documentation_quality": (
        "File headers present (Developer, Date, Purpose). Single-line comment style. "
        "Design decisions documented where non-obvious. No tutorial-style comments."
    ),
}


class SupervisorAuditor:
    """
    Reviews SKILL.md diffs against the 5-criterion rubric.

    Uses a separate claude -p subprocess (haiku model) to perform an independent
    quality review. Results are written to an audit log for traceability.

    Args:
        skill_name: Name of the skill directory under skills/.
    """

    def __init__(self, skill_name: str) -> None:
        self._skill_name = skill_name
        self._claude_cli = resolve_claude_cli()
        self._audit_log_path = get_audit_log_path(skill_name)

    def review_proposal(self, diff: str, eval_report: dict[str, Any]) -> SupervisorVerdict:
        """
        Review a proposed SKILL.md change against the rubric.

        Args:
            diff: The text diff of the proposed change.
            eval_report: The eval report that triggered this improvement iteration.

        Returns:
            SupervisorVerdict with scores and verdict.
        """
        prompt = self._build_review_prompt(diff, eval_report)
        response = self._call_claude(prompt)

        if response is None:
            # Supervisor subprocess failed — conservative REJECTED
            verdict = SupervisorVerdict(
                review_id=f"SR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}",
                verdict="REJECTED",
                overall_score=0,
                criteria_scores={k: 0 for k in RUBRIC_WEIGHTS},
                issues=[{"severity": "HIGH", "criterion": "all", "description": "Supervisor subprocess failed"}],
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
        else:
            verdict = self._parse_verdict(response)

        self._record_audit(verdict)
        return verdict

    def _build_review_prompt(self, diff: str, eval_report: dict[str, Any]) -> str:
        """
        Construct the prompt sent to the supervisor agent.

        Includes the diff, eval context, rubric criteria with weights,
        and exact response format expectations.

        Args:
            diff: The text diff of the proposed change.
            eval_report: The eval report dictionary.

        Returns:
            Complete prompt string.
        """
        # Build criteria section
        criteria_lines = []
        for name, weight in RUBRIC_WEIGHTS.items():
            desc = _CRITERIA_DESCRIPTIONS.get(name, "")
            criteria_lines.append(f"### {name} (Weight: {weight}%)\n{desc}")
        criteria_text = "\n\n".join(criteria_lines)

        # Build eval context summary
        summary = eval_report.get("summary", {})
        pass_rate = summary.get("pass_rate", 0.0)
        failed_count = len(eval_report.get("failed_assertions", []))

        return (
            "You are a supervisor code reviewer. Review the following SKILL.md diff "
            "against the 5-criterion rubric below. Score each criterion 0-100.\n\n"
            f"## Eval Context\n"
            f"- Pass rate before change: {pass_rate:.2%}\n"
            f"- Failed assertions: {failed_count}\n\n"
            f"## Diff to Review\n```\n{diff}\n```\n\n"
            f"## Rubric Criteria\n\n{criteria_text}\n\n"
            "## Scoring Rules\n"
            "- Score each criterion 0-100\n"
            "- 90-100: Exceeds standards. 70-89: Meets standards. 50-69: Below. 0-49: Fails.\n"
            f"- Passing: ALL criteria must be >= {SUPERVISOR_PASSING_SCORE}\n"
            "- overall_score = weighted average using the weights above\n\n"
            "## Required Response Format\n"
            "Respond with ONLY valid JSON matching this schema exactly:\n"
            "```json\n"
            "{\n"
            '  "verdict": "APPROVED | REVISION_REQUIRED | REJECTED",\n'
            '  "overall_score": <int>,\n'
            '  "criteria_scores": {\n'
            '    "comment_code_alignment": <int>,\n'
            '    "architecture_compliance": <int>,\n'
            '    "build_cleanliness": <int>,\n'
            '    "defensive_programming": <int>,\n'
            '    "documentation_quality": <int>\n'
            "  },\n"
            '  "issues": [\n'
            '    {"severity": "HIGH|MEDIUM|LOW", "criterion": "<name>", "description": "<text>"}\n'
            "  ]\n"
            "}\n"
            "```\n\n"
            "APPROVED if all criteria >= 70. REVISION_REQUIRED if any criterion 50-69. "
            "REJECTED if any criterion < 50.\n"
            "Return ONLY the JSON. No explanation, no markdown fences, no extra text."
        )

    def _parse_verdict(self, response: str) -> SupervisorVerdict:
        """
        Parse the supervisor's JSON response into a SupervisorVerdict.

        Handles common formatting issues (markdown fences, extra text).

        Args:
            response: Raw text response from the supervisor subprocess.

        Returns:
            Parsed SupervisorVerdict.
        """
        review_id = f"SR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Strip markdown code fences if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]  # Remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        # Try to extract JSON from the response
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt to find JSON object within the response
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    logger.warning("Failed to parse supervisor response as JSON")
                    return SupervisorVerdict(
                        review_id=review_id,
                        verdict="REJECTED",
                        overall_score=0,
                        criteria_scores={k: 0 for k in RUBRIC_WEIGHTS},
                        issues=[{
                            "severity": "HIGH",
                            "criterion": "all",
                            "description": f"Unparseable supervisor response: {response[:200]}",
                        }],
                        timestamp=timestamp,
                    )
            else:
                logger.warning("No JSON found in supervisor response")
                return SupervisorVerdict(
                    review_id=review_id,
                    verdict="REJECTED",
                    overall_score=0,
                    criteria_scores={k: 0 for k in RUBRIC_WEIGHTS},
                    issues=[{
                        "severity": "HIGH",
                        "criterion": "all",
                        "description": f"No JSON in supervisor response: {response[:200]}",
                    }],
                    timestamp=timestamp,
                )

        # Extract and validate fields
        criteria_scores = data.get("criteria_scores", {})
        validated_scores: dict[str, int] = {}
        for key in RUBRIC_WEIGHTS:
            score = criteria_scores.get(key, 0)
            validated_scores[key] = max(0, min(100, int(score)))

        # Calculate weighted overall score
        overall = sum(
            validated_scores[k] * (w / 100.0)
            for k, w in RUBRIC_WEIGHTS.items()
        )
        overall_score = round(overall)

        # Determine verdict based on individual criterion scores
        min_score = min(validated_scores.values()) if validated_scores else 0
        if min_score >= SUPERVISOR_PASSING_SCORE:
            verdict = "APPROVED"
        elif min_score >= 50:
            verdict = "REVISION_REQUIRED"
        else:
            verdict = "REJECTED"

        issues = data.get("issues", [])
        validated_issues: list[dict[str, str]] = []
        for issue in issues:
            if isinstance(issue, dict):
                validated_issues.append({
                    "severity": str(issue.get("severity", "MEDIUM")),
                    "criterion": str(issue.get("criterion", "unknown")),
                    "description": str(issue.get("description", "")),
                })

        return SupervisorVerdict(
            review_id=review_id,
            verdict=verdict,
            overall_score=overall_score,
            criteria_scores=validated_scores,
            issues=validated_issues,
            timestamp=timestamp,
        )

    def _call_claude(self, prompt: str) -> str | None:
        """
        Call claude -p with the supervisor prompt using haiku model.

        Reuses the isolation pattern from EvalRunner: stdin piping,
        NEUTRAL_CWD, env stripping, no tools.

        Args:
            prompt: The complete review prompt.

        Returns:
            Raw response text, or None if the subprocess failed.
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
                    "--model", SUPERVISOR_MODEL,
                ],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=SUPERVISOR_TIMEOUT_SECONDS,
                env=env,
                cwd=NEUTRAL_CWD,
            )

            if result.returncode != 0:
                logger.warning(
                    "Supervisor subprocess returned code %d: %s",
                    result.returncode,
                    result.stderr[:200] if result.stderr else "(no stderr)",
                )
                return None

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.warning("Supervisor subprocess timed out after %ds", SUPERVISOR_TIMEOUT_SECONDS)
            return None
        except FileNotFoundError:
            logger.error("claude CLI not found at '%s'", self._claude_cli)
            return None

    def _record_audit(self, verdict: SupervisorVerdict) -> None:
        """
        Append a verdict to the audit log (atomic write).

        Loads existing entries, appends the new verdict, and rewrites
        the entire log atomically.

        Args:
            verdict: The SupervisorVerdict to record.
        """
        # Load existing audit log
        existing_entries: list[dict[str, Any]] = []
        if self._audit_log_path.exists():
            try:
                with self._audit_log_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing_entries = data.get("audits", [])
            except (json.JSONDecodeError, OSError):
                logger.warning("Corrupt audit log, starting fresh")

        existing_entries.append(asdict(verdict))

        audit_data = {
            "skill_name": self._skill_name,
            "total_audits": len(existing_entries),
            "audits": existing_entries,
        }

        # Atomic write
        fd, tmp_path = tempfile.mkstemp(
            suffix=".json",
            dir=str(self._audit_log_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(audit_data, f, indent=2, ensure_ascii=False)
            Path(tmp_path).replace(self._audit_log_path)
            logger.info("Audit recorded: %s -> %s", verdict.review_id, verdict.verdict)
        except Exception:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
            raise
