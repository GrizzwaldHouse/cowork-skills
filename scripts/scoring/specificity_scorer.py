# specificity_scorer.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Catches skills that are too generic or too project-locked to be reusable

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("scoring.specificity")

# Indicators of overly generic skills ("do good things" syndrome)
_TOO_GENERIC_INDICATORS: tuple[str, ...] = (
    "do things well",
    "be a good",
    "general purpose",
    "do whatever",
    "handle everything",
    "all tasks",
    "any situation",
    "everything you need",
    "always follow best practices",
)

# Indicators of project-locked skills
_TOO_SPECIFIC_INDICATORS: tuple[str, ...] = (
    "only for this project",
    "specific to this codebase",
    "only works with this repo",
    "this application only",
    "hardcoded for this",
    "not portable",
    "single-use",
)

# Minimum word count for meaningful intent/logic
_MIN_INTENT_WORDS: int = 5
_MIN_LOGIC_WORDS: int = 15

# Maximum ratio of filler words to total words (generic detector)
_MAX_FILLER_RATIO: float = 0.40

# Common filler words that indicate vagueness
_FILLER_WORDS: frozenset[str] = frozenset({
    "good", "nice", "great", "proper", "appropriate", "suitable",
    "correct", "right", "best", "optimal", "effective", "efficient",
    "well", "properly", "correctly", "appropriately",
})


@dataclass(frozen=True)
class SpecificityResult:
    """Result of a specificity scoring pass."""

    score: float
    too_generic: bool
    too_specific: bool
    issues: tuple[str, ...]


class SpecificityScorer:
    """Detects skills that are too generic or too project-locked.

    Scoring approach:
    - Start at 1.0
    - Deduct 0.3 per generic indicator found (max 1 deduction)
    - Deduct 0.3 per project-lock indicator found (max 1 deduction)
    - Deduct 0.2 if intent has fewer than 5 words
    - Deduct 0.15 if filler word ratio exceeds threshold
    - Deduct 0.2 if execution_logic has fewer than 15 words

    A healthy skill is specific enough to be actionable but generic
    enough to apply across projects.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self._custom_generic: list[str] = cfg.get("generic_indicators", [])
        self._custom_specific: list[str] = cfg.get("specific_indicators", [])

    def score(self, skill_dict: dict[str, Any]) -> SpecificityResult:
        """Score a skill dict for appropriate specificity.

        Returns SpecificityResult with score, flags, and issue details.
        """
        score = 1.0
        issues: list[str] = []
        too_generic = False
        too_specific = False

        intent = str(skill_dict.get("intent", ""))
        logic = str(skill_dict.get("execution_logic", ""))
        context = str(skill_dict.get("context", ""))
        full_text = f"{intent} {logic} {context}".lower()

        # Check for overly generic indicators
        all_generic = list(_TOO_GENERIC_INDICATORS) + self._custom_generic
        for indicator in all_generic:
            if indicator.lower() in full_text:
                score -= 0.30
                too_generic = True
                issues.append(f"Too generic: found '{indicator}'")
                break

        # Check for project-locked indicators
        all_specific = list(_TOO_SPECIFIC_INDICATORS) + self._custom_specific
        for indicator in all_specific:
            if indicator.lower() in full_text:
                score -= 0.30
                too_specific = True
                issues.append(f"Too project-locked: found '{indicator}'")
                break

        # Check intent word count
        intent_words = intent.split()
        if len(intent_words) < _MIN_INTENT_WORDS:
            score -= 0.20
            issues.append(
                f"Intent too brief: {len(intent_words)} words "
                f"(minimum: {_MIN_INTENT_WORDS})"
            )
            if len(intent_words) < 3:
                too_generic = True

        # Check filler word ratio in intent + logic
        score, issues, filler_flag = self._check_filler_ratio(
            full_text, score, issues
        )
        if filler_flag:
            too_generic = True

        # Check execution_logic word count
        logic_words = logic.split()
        if len(logic_words) < _MIN_LOGIC_WORDS:
            score -= 0.20
            issues.append(
                f"Execution logic too brief: {len(logic_words)} words "
                f"(minimum: {_MIN_LOGIC_WORDS})"
            )

        score = max(0.0, min(1.0, score))

        result = SpecificityResult(
            score=round(score, 4),
            too_generic=too_generic,
            too_specific=too_specific,
            issues=tuple(issues),
        )

        logger.info(
            "Specificity score for '%s': %.2f (generic=%s, specific=%s)",
            skill_dict.get("name", skill_dict.get("skill_name", "unnamed")),
            result.score,
            too_generic,
            too_specific,
        )
        return result

    @staticmethod
    def _check_filler_ratio(
        text: str, score: float, issues: list[str]
    ) -> tuple[float, list[str], bool]:
        """Check if the text has too many filler words relative to total words."""
        words = re.findall(r"\b\w+\b", text.lower())
        if len(words) < 10:
            return score, issues, False

        filler_count = sum(1 for w in words if w in _FILLER_WORDS)
        ratio = filler_count / len(words)

        if ratio > _MAX_FILLER_RATIO:
            score -= 0.15
            issues.append(
                f"High filler word ratio: {ratio:.0%} "
                f"(threshold: {_MAX_FILLER_RATIO:.0%})"
            )
            return score, issues, True

        return score, issues, False
