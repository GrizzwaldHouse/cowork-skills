# completeness_scorer.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Ensures skills have all required fields at sufficient depth for production use

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("scoring.completeness")

# Default required sections with minimum thresholds
_DEFAULT_REQUIRED_SECTIONS: dict[str, dict[str, Any]] = {
    "intent": {"type": "text", "min_chars": 20, "weight": 0.15},
    "execution_logic": {"type": "text", "min_chars": 200, "weight": 0.30},
    "constraints": {"type": "list", "min_items": 2, "weight": 0.15},
    "failure_modes": {"type": "list", "min_items": 2, "weight": 0.15},
    "expected_output": {"type": "text", "min_chars": 20, "weight": 0.10},
    "context": {"type": "text", "min_chars": 10, "weight": 0.10},
    "input_pattern": {"type": "text", "min_chars": 10, "weight": 0.05},
}


@dataclass(frozen=True)
class CompletenessResult:
    """Result of a completeness scoring pass."""

    score: float
    missing_sections: tuple[str, ...]
    weak_sections: tuple[str, ...]
    details: tuple[str, ...]


class CompletenessScorer:
    """Scores skill completeness — all required fields present and substantive.

    Each required section contributes a weighted portion of the total score.
    Sections are evaluated as either text (minimum character count) or
    list (minimum item count). Partial credit is given for sections that
    exist but fall short of the minimum.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        sections_cfg = cfg.get("completeness_sections")

        if sections_cfg and isinstance(sections_cfg, dict):
            self._sections = sections_cfg
        else:
            self._sections = _DEFAULT_REQUIRED_SECTIONS

    def score(self, skill_dict: dict[str, Any]) -> CompletenessResult:
        """Score a skill dict for completeness.

        Returns CompletenessResult with overall score, missing sections,
        weak sections, and detail messages.
        """
        total_weight = sum(
            sec.get("weight", 0.0) for sec in self._sections.values()
        )
        if total_weight == 0:
            return CompletenessResult(
                score=1.0, missing_sections=(), weak_sections=(), details=()
            )

        weighted_score = 0.0
        missing: list[str] = []
        weak: list[str] = []
        details: list[str] = []

        for section_name, requirements in self._sections.items():
            weight = requirements.get("weight", 0.0)
            section_type = requirements.get("type", "text")
            value = skill_dict.get(section_name, "")

            section_score = self._score_section(
                section_name, value, section_type, requirements
            )

            if section_score == 0.0:
                missing.append(section_name)
                details.append(f"Missing: '{section_name}'")
            elif section_score < 1.0:
                weak.append(section_name)
                details.append(
                    f"Weak: '{section_name}' (score: {section_score:.2f})"
                )

            weighted_score += section_score * (weight / total_weight)

        final_score = max(0.0, min(1.0, weighted_score))

        result = CompletenessResult(
            score=round(final_score, 4),
            missing_sections=tuple(missing),
            weak_sections=tuple(weak),
            details=tuple(details),
        )

        logger.info(
            "Completeness score for '%s': %.2f — %d missing, %d weak",
            skill_dict.get("name", skill_dict.get("skill_name", "unnamed")),
            result.score,
            len(missing),
            len(weak),
        )
        return result

    @staticmethod
    def _score_section(
        name: str,
        value: Any,
        section_type: str,
        requirements: dict[str, Any],
    ) -> float:
        """Score a single section. Returns 0.0 to 1.0."""
        if section_type == "list":
            min_items = requirements.get("min_items", 1)
            items = value if isinstance(value, (list, tuple)) else []
            if not items:
                return 0.0
            return min(1.0, len(items) / min_items)

        # Text-based section
        min_chars = requirements.get("min_chars", 1)
        text = str(value).strip()
        if not text:
            return 0.0
        return min(1.0, len(text) / min_chars)
