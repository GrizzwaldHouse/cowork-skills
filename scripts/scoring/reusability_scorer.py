# reusability_scorer.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Dedicated 95/5 reusability rule scorer — deduction-based rubric for portable skill assessment

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("scoring.reusability")

# Deduction amounts per violation category
_DEDUCTION_PROJECT_PATH: float = 0.30
_DEDUCTION_HARDCODED_NAME: float = 0.20
_DEDUCTION_FRAMEWORK_LOCKED: float = 0.15
_DEDUCTION_PLATFORM_SPECIFIC: float = 0.10
_DEDUCTION_MISSING_CONSTRAINTS: float = 0.10
_DEDUCTION_MISSING_FAILURE_MODES: float = 0.10
_DEDUCTION_THIN_LOGIC: float = 0.15
_DEDUCTION_NO_INPUT_PATTERN: float = 0.10

# Minimum execution_logic length to avoid thin-logic deduction
_MIN_LOGIC_CHARS: int = 100

# Allowed path prefixes that do NOT trigger the project-specific deduction
_ALLOWED_PATH_PREFIXES: tuple[str, ...] = (
    "c:/claudeskills",
    "~/.claude",
)

# Regex for detecting absolute paths in text
_PATH_PATTERN: re.Pattern[str] = re.compile(
    r'[A-Za-z]:\\[^\s"\']+|/(?:home|Users|usr|etc|var|opt|tmp)/[^\s"\']+',
    re.IGNORECASE,
)

# Indicators of framework-locked patterns
_FRAMEWORK_LOCK_INDICATORS: tuple[str, ...] = (
    "only works with react",
    "requires next.js",
    "django-only",
    "flask-specific",
    "angular only",
    "vue-specific",
    "tailwind required",
)

# Indicators of platform-specific commands
_PLATFORM_INDICATORS: tuple[str, ...] = (
    "powershell",
    "cmd.exe",
    "reg add",
    "choco install",
    "apt-get",
    "brew install",
    "yum install",
    "systemctl",
    "launchctl",
)


@dataclass(frozen=True)
class ReusabilityResult:
    """Result of a reusability scoring pass."""

    score: float
    deductions: tuple[str, ...]
    passed: bool


class ReusabilityScorer:
    """Implements the 95/5 reusability rule as a measurable deduction-based score.

    Starts at 1.0 and deducts per violation found. The rubric is:
    - Project-specific file paths (not C:/ClaudeSkills or ~/.claude): -0.30
    - Hardcoded project names in execution_logic:                     -0.20
    - Framework-locked patterns (only works with one framework):      -0.15
    - Platform-specific commands (Windows-only or Linux-only):        -0.10
    - Missing constraints field:                                      -0.10
    - Missing failure_modes field:                                    -0.10
    - Execution logic < 100 chars:                                    -0.15
    - No input_pattern defined:                                       -0.10

    Score interpretation:
    - 0.85+ → Highly reusable (APPROVED)
    - 0.70-0.84 → Mostly reusable, minor fixes (NEEDS_REFACTOR)
    - Below 0.70 → Too project-specific (REJECTED)
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        scoring_cfg = cfg.get("scoring", {})

        self._min_reusability: float = scoring_cfg.get(
            "min_reusability_score", 0.85
        )

        # Allow config to override hardcoded project name indicators
        self._project_name_indicators: list[str] = cfg.get(
            "project_name_indicators", []
        )

    def score(self, skill_dict: dict[str, Any]) -> ReusabilityResult:
        """Score a skill dict against the 95/5 reusability rubric.

        Returns a ReusabilityResult with the score, deductions, and pass/fail.
        """
        score = 1.0
        deductions: list[str] = []

        # Concatenate all scannable text fields
        text_fields = [
            str(skill_dict.get("intent", "")),
            str(skill_dict.get("execution_logic", "")),
            str(skill_dict.get("context", "")),
            str(skill_dict.get("expected_output", "")),
        ]
        full_text = " ".join(text_fields)
        full_text_lower = full_text.lower()

        # Check 1: Project-specific file paths
        score, deductions = self._check_paths(full_text, score, deductions)

        # Check 2: Hardcoded project names
        score, deductions = self._check_project_names(
            full_text_lower, score, deductions
        )

        # Check 3: Framework-locked patterns
        score, deductions = self._check_framework_lock(
            full_text_lower, score, deductions
        )

        # Check 4: Platform-specific commands
        score, deductions = self._check_platform_specific(
            full_text_lower, score, deductions
        )

        # Check 5: Missing constraints
        constraints = skill_dict.get("constraints", [])
        if not constraints:
            score -= _DEDUCTION_MISSING_CONSTRAINTS
            deductions.append(
                f"Missing constraints field (-{_DEDUCTION_MISSING_CONSTRAINTS})"
            )

        # Check 6: Missing failure_modes
        failure_modes = skill_dict.get("failure_modes", [])
        if not failure_modes:
            score -= _DEDUCTION_MISSING_FAILURE_MODES
            deductions.append(
                f"Missing failure_modes field (-{_DEDUCTION_MISSING_FAILURE_MODES})"
            )

        # Check 7: Thin execution logic
        logic = str(skill_dict.get("execution_logic", ""))
        if len(logic) < _MIN_LOGIC_CHARS:
            score -= _DEDUCTION_THIN_LOGIC
            deductions.append(
                f"Execution logic too short ({len(logic)} < {_MIN_LOGIC_CHARS} chars) "
                f"(-{_DEDUCTION_THIN_LOGIC})"
            )

        # Check 8: No input_pattern
        input_pattern = str(skill_dict.get("input_pattern", ""))
        if len(input_pattern) < 10:
            score -= _DEDUCTION_NO_INPUT_PATTERN
            deductions.append(
                f"No input_pattern defined (-{_DEDUCTION_NO_INPUT_PATTERN})"
            )

        score = max(0.0, min(1.0, score))
        passed = score >= self._min_reusability

        result = ReusabilityResult(
            score=round(score, 4),
            deductions=tuple(deductions),
            passed=passed,
        )

        logger.info(
            "Reusability score for '%s': %.2f (%s) — %d deductions",
            skill_dict.get("name", skill_dict.get("skill_name", "unnamed")),
            result.score,
            "PASS" if passed else "FAIL",
            len(deductions),
        )
        return result

    def _check_paths(
        self, text: str, score: float, deductions: list[str]
    ) -> tuple[float, list[str]]:
        """Deduct for hardcoded paths outside allowed prefixes."""
        for match in _PATH_PATTERN.finditer(text):
            found = match.group(0).replace("\\", "/").lower()
            is_allowed = any(
                found.startswith(prefix) for prefix in _ALLOWED_PATH_PREFIXES
            )
            if not is_allowed:
                score -= _DEDUCTION_PROJECT_PATH
                deductions.append(
                    f"Project-specific path: '{match.group(0)}' "
                    f"(-{_DEDUCTION_PROJECT_PATH})"
                )
                break  # Only deduct once per skill
        return score, deductions

    def _check_project_names(
        self, text_lower: str, score: float, deductions: list[str]
    ) -> tuple[float, list[str]]:
        """Deduct for hardcoded project names."""
        for indicator in self._project_name_indicators:
            if indicator.lower() in text_lower:
                score -= _DEDUCTION_HARDCODED_NAME
                deductions.append(
                    f"Hardcoded project name: '{indicator}' "
                    f"(-{_DEDUCTION_HARDCODED_NAME})"
                )
                break  # Only deduct once per skill
        return score, deductions

    def _check_framework_lock(
        self, text_lower: str, score: float, deductions: list[str]
    ) -> tuple[float, list[str]]:
        """Deduct for framework-locked patterns."""
        for indicator in _FRAMEWORK_LOCK_INDICATORS:
            if indicator in text_lower:
                score -= _DEDUCTION_FRAMEWORK_LOCKED
                deductions.append(
                    f"Framework-locked: '{indicator}' "
                    f"(-{_DEDUCTION_FRAMEWORK_LOCKED})"
                )
                break
        return score, deductions

    def _check_platform_specific(
        self, text_lower: str, score: float, deductions: list[str]
    ) -> tuple[float, list[str]]:
        """Deduct for platform-specific commands."""
        for indicator in _PLATFORM_INDICATORS:
            if indicator in text_lower:
                score -= _DEDUCTION_PLATFORM_SPECIFIC
                deductions.append(
                    f"Platform-specific: '{indicator}' "
                    f"(-{_DEDUCTION_PLATFORM_SPECIFIC})"
                )
                break
        return score, deductions
