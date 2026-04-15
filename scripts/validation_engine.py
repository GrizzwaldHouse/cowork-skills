# validation_engine.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Validate Quad Skills against architecture, security, and quality rules with dedup

"""
Validation engine for the OwlWatcher AI Self-Improvement Pipeline.

Checks extracted Quad Skills against architecture constraints, security
policies, and quality thresholds before they are approved for use.  Also
performs duplicate detection against the existing skill store.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from log_config import configure_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()
logger = logging.getLogger("validation_engine")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
class ValidationResult(str, Enum):
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ValidationReport:
    """Immutable report produced by a validation run."""

    skill_id: str
    result: ValidationResult
    architecture_score: float
    security_score: float
    quality_score: float
    duplicate_of: str | None
    violations: list[str]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        data = asdict(self)
        data["result"] = self.result.value
        return data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _jaccard_similarity(text_a: str, text_b: str) -> float:
    """Compute Jaccard similarity over word sets of two strings."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class ValidationEngine:
    """Validates Quad Skills against architecture, security, and quality rules."""

    def __init__(self, config: dict[str, Any]) -> None:
        extraction_cfg = config.get("extraction", {})
        self._auto_approve_threshold = extraction_cfg.get("auto_approve_threshold", 0.7)
        self._dedup_threshold = extraction_cfg.get("dedup_similarity_threshold", 0.85)

        safety_cfg = config.get("safety", {})
        self._blocked_patterns: list[str] = safety_cfg.get("blocked_patterns", [
            "os.system", "subprocess", "eval", "exec",
            "__import__", "rm -rf", "format c:",
        ])
        self._core_skills: list[str] = safety_cfg.get("core_skills", [])

        self._skill_store = BASE_DIR / "data" / "quad_skills"

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------
    def validate(self, skill_dict: dict[str, Any]) -> ValidationReport:
        """Run all validation checks and return a comprehensive report."""
        arch_score, arch_violations = self.check_architecture(skill_dict)
        sec_score, sec_violations = self.check_security(skill_dict)
        qual_score, qual_violations = self.check_quality(skill_dict)
        duplicate_of = self.check_duplicates(skill_dict)

        all_violations = arch_violations + sec_violations + qual_violations
        if duplicate_of:
            all_violations.append(f"Duplicate of existing skill: {duplicate_of}")

        # Determine result
        confidence = float(skill_dict.get("confidence_score", 0.0))
        if sec_score <= 0.5 or any("CRITICAL" in v for v in all_violations):
            result = ValidationResult.REJECTED
        elif (
            confidence >= self._auto_approve_threshold
            and sec_score >= 0.9
            and not all_violations
        ):
            result = ValidationResult.APPROVED
        else:
            result = ValidationResult.NEEDS_REVIEW

        report = ValidationReport(
            skill_id=skill_dict.get("skill_id", ""),
            result=result,
            architecture_score=arch_score,
            security_score=sec_score,
            quality_score=qual_score,
            duplicate_of=duplicate_of,
            violations=all_violations,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Validated skill %s: %s (arch=%.2f sec=%.2f qual=%.2f)",
            report.skill_id,
            report.result.value,
            arch_score,
            sec_score,
            qual_score,
        )
        return report

    # ------------------------------------------------------------------
    # Architecture checks
    # ------------------------------------------------------------------
    def check_architecture(self, skill_dict: dict[str, Any]) -> tuple[float, list[str]]:
        """Check against architecture rules.

        Rules:
        - Deduct 0.2 if execution_logic contains ``while True`` or ``time.sleep`` (polling)
        - Deduct 0.2 if execution_logic contains global variable assignments
        - Deduct 0.1 if no clear separation (monolithic block > 500 chars without sections)
        - Base score 1.0, clamp to 0.0
        """
        score = 1.0
        violations: list[str] = []
        logic = skill_dict.get("execution_logic", "")

        # Polling detection
        if re.search(r"\bwhile\s+True\b", logic) or re.search(r"\btime\.sleep\b", logic):
            score -= 0.2
            violations.append("Architecture: contains polling pattern (while True / time.sleep)")

        # Global variable assignments
        if re.search(r"\bglobal\s+\w+", logic):
            score -= 0.2
            violations.append("Architecture: uses global variable assignments")

        # Monolithic block check
        if len(logic) > 500 and "##" not in logic and "\ndef " not in logic:
            score -= 0.1
            violations.append("Architecture: monolithic block without clear separation")

        score = max(score, 0.0)
        return score, violations

    # ------------------------------------------------------------------
    # Security checks
    # ------------------------------------------------------------------
    def check_security(self, skill_dict: dict[str, Any]) -> tuple[float, list[str]]:
        """Check for security violations.

        Rules:
        - Deduct 0.5 per blocked pattern found
        - Deduct 0.3 if contains hardcoded paths outside C:\\ClaudeSkills or ~/.claude
        - Deduct 0.2 if contains credential patterns (password=, api_key=, secret=)
        - Mark as CRITICAL violation if score < 0.5
        - Base score 1.0, clamp to 0.0
        """
        score = 1.0
        violations: list[str] = []
        logic = skill_dict.get("execution_logic", "")
        full_text = f"{logic} {skill_dict.get('intent', '')} {skill_dict.get('context', '')}"

        # Blocked patterns -- use word-boundary matching to avoid false
        # positives like "exec" matching inside "execution" or "process".
        for pattern in self._blocked_patterns:
            # Escape the pattern for regex, then wrap in word boundaries
            escaped = re.escape(pattern)
            if re.search(rf"\b{escaped}\b", full_text, re.IGNORECASE):
                score -= 0.5
                violations.append(f"Security: blocked pattern found: {pattern}")

        # Path traversal sequences (relative escapes like ../.. or ..\..)
        # WHY: These never resolve to a stable file location and are a classic
        # signal of attempted sandbox escape, regardless of which directory the
        # skill is launched from. Detect them before the absolute-path check so
        # the violation message accurately calls out the traversal pattern.
        if re.search(r"(?:\.\./|\.\.\\){2,}", full_text):
            score -= 0.3
            violations.append("Security: path traversal sequence detected")

        # Hardcoded paths outside allowed directories
        path_re = re.compile(r'["\']?([A-Za-z]:\\[^\s"\']+|/(?:usr|etc|var|home|opt|tmp)/[^\s"\']+)["\']?')
        for match in path_re.finditer(full_text):
            found_path = match.group(1).replace("\\", "/")
            if not (
                found_path.startswith("C:/ClaudeSkills")
                or found_path.startswith("c:/ClaudeSkills")
                or "/.claude" in found_path
            ):
                score -= 0.3
                violations.append(f"Security: hardcoded path outside allowed directories: {found_path}")
                break  # Only deduct once for path violations

        # Credential patterns
        # WHY: The original \b(password|api_key|secret|token)\b regex missed
        # AWS-style identifiers like AWS_SECRET_ACCESS_KEY because the leading
        # underscore is a word character, so \b never fires before "secret".
        # We add a second pattern that matches all-caps env-var style credentials
        # (AWS_*, *_TOKEN, *_PASSWORD, *_API_KEY) plus a Bearer/Basic auth header
        # heuristic to cover the common leak shapes.
        cred_re = re.compile(r"\b(password|api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE)
        env_cred_re = re.compile(
            r"\b[A-Z][A-Z0-9_]*(?:SECRET|PASSWORD|TOKEN|API_KEY|ACCESS_KEY)[A-Z0-9_]*\s*=\s*['\"][^'\"]+['\"]"
        )
        if cred_re.search(full_text) or env_cred_re.search(full_text):
            score -= 0.2
            violations.append("Security: possible hardcoded credentials detected")

        score = max(score, 0.0)

        # Mark CRITICAL if at or below threshold
        if score <= 0.5:
            violations = [f"CRITICAL: {v}" if not v.startswith("CRITICAL") else v for v in violations]

        return score, violations

    # ------------------------------------------------------------------
    # Quality checks
    # ------------------------------------------------------------------
    def check_quality(self, skill_dict: dict[str, Any]) -> tuple[float, list[str]]:
        """Check quality metrics.

        Rules:
        - Deduct 0.3 if execution_logic < 50 chars
        - Deduct 0.2 if constraints list is empty
        - Deduct 0.2 if failure_modes list is empty
        - Deduct 0.2 if confidence_score < 0.3
        - Deduct 0.1 if intent < 10 chars
        - Base score 1.0, clamp to 0.0
        """
        score = 1.0
        violations: list[str] = []

        logic = skill_dict.get("execution_logic", "")
        if len(logic) < 50:
            score -= 0.3
            violations.append("Quality: execution_logic too short (< 50 chars)")

        constraints = skill_dict.get("constraints", [])
        if not constraints:
            score -= 0.2
            violations.append("Quality: no constraints defined")

        failure_modes = skill_dict.get("failure_modes", [])
        if not failure_modes:
            score -= 0.2
            violations.append("Quality: no failure_modes defined")

        confidence = float(skill_dict.get("confidence_score", 0.0))
        if confidence < 0.3:
            score -= 0.2
            violations.append(f"Quality: low confidence score ({confidence:.2f} < 0.3)")

        intent = skill_dict.get("intent", "")
        if len(intent) < 10:
            score -= 0.1
            violations.append("Quality: intent too short (< 10 chars)")

        score = max(score, 0.0)
        return score, violations

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------
    def check_duplicates(self, skill_dict: dict[str, Any]) -> str | None:
        """Check Jaccard similarity against existing skills.

        Returns the ``skill_id`` of the duplicate if similarity exceeds
        the configured threshold, otherwise ``None``.
        """
        candidate_text = (
            f"{skill_dict.get('intent', '')} {skill_dict.get('execution_logic', '')}"
        )

        if not self._skill_store.exists():
            return None

        for json_path in self._skill_store.glob("*.json"):
            try:
                with json_path.open("r", encoding="utf-8") as fh:
                    existing = json.load(fh)
            except (json.JSONDecodeError, OSError):
                continue

            existing_id = existing.get("skill_id", "")
            # Skip self-comparison
            if existing_id == skill_dict.get("skill_id", ""):
                continue

            existing_text = (
                f"{existing.get('intent', '')} {existing.get('execution_logic', '')}"
            )
            similarity = _jaccard_similarity(candidate_text, existing_text)
            if similarity >= self._dedup_threshold:
                logger.info(
                    "Skill %s is duplicate of %s (similarity=%.3f)",
                    skill_dict.get("skill_id", "?"),
                    existing_id,
                    similarity,
                )
                return existing_id

        return None
