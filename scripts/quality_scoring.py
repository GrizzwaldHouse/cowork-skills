# quality_scoring.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: 5-dimension weighted quality scoring engine enforcing the 95/5 reusability rule

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent.quality_scoring")

# Default config path — overridable via constructor
_CONFIG_PATH: Path = Path("C:/ClaudeSkills/config/agent_config.json")


@dataclass(frozen=True)
class DimensionScore:
    """Score for a single quality dimension."""
    dimension: str
    score: float
    weight: float
    weighted_score: float
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class QualityReport:
    """Complete quality assessment for a skill."""
    skill_id: str
    skill_name: str
    composite_score: float
    disposition: str  # approved, needs_refactor, needs_review, rejected
    dimensions: tuple[DimensionScore, ...] = ()
    violations: tuple[str, ...] = ()
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QualityScoringEngine:
    """5-dimension weighted scoring engine.

    Combines architecture, security, and quality scores from ValidationEngine
    with new reusability and completeness dimensions. Produces a composite
    score and disposition based on configurable thresholds.

    Enforces Marcus's 95/5 Rule: 95% of code should be reusable across
    projects without modification.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        if config is None:
            config = self._load_config()
        scoring_cfg = config.get("quality_scoring", {})

        # Dimension weights — must sum to 1.0
        weights = scoring_cfg.get("weights", {})
        self._weight_architecture: float = weights.get("architecture", 0.20)
        self._weight_security: float = weights.get("security", 0.25)
        self._weight_quality: float = weights.get("quality", 0.15)
        self._weight_reusability: float = weights.get("reusability", 0.25)
        self._weight_completeness: float = weights.get("completeness", 0.15)

        # Disposition thresholds — descending order
        dispositions = scoring_cfg.get("dispositions", {})
        self._threshold_approved: float = dispositions.get("approved", 0.80)
        self._threshold_needs_refactor: float = dispositions.get("needs_refactor", 0.50)
        self._threshold_needs_review: float = dispositions.get("needs_review", 0.40)

        # Reusability config
        reuse_cfg = scoring_cfg.get("reusability", {})
        self._deduction_per_indicator: float = reuse_cfg.get("deduction_per_indicator", 0.15)
        self._bonus_per_indicator: float = reuse_cfg.get("bonus_per_indicator", 0.05)
        self._max_bonus: float = reuse_cfg.get("max_bonus", 0.15)
        self._project_specific_indicators: list[str] = reuse_cfg.get(
            "project_specific_indicators", []
        )
        self._hardcoded_path_patterns: list[str] = reuse_cfg.get(
            "hardcoded_path_patterns", []
        )
        self._allowed_path_prefixes: list[str] = reuse_cfg.get(
            "allowed_path_prefixes", []
        )
        self._reusable_indicators: list[str] = reuse_cfg.get(
            "reusable_indicators", []
        )

        # Completeness config
        self._completeness_sections: dict[str, dict] = scoring_cfg.get(
            "completeness", {}
        ).get("required_sections", {})

    def score(
        self,
        skill_dict: dict[str, Any],
        validation_report: dict[str, Any] | None = None,
    ) -> QualityReport:
        """Produce a full quality report for a skill.

        Accepts an optional validation_report dict containing pre-computed
        architecture_score, security_score, quality_score from ValidationEngine.
        If not provided, those dimensions score 0.5 (neutral).
        """
        skill_id = skill_dict.get("skill_id", "unknown")
        skill_name = skill_dict.get("name", skill_dict.get("skill_name", "unnamed"))

        # Gather pre-computed scores from ValidationEngine
        vr = validation_report or {}
        arch_raw = vr.get("architecture_score", 0.5)
        sec_raw = vr.get("security_score", 0.5)
        qual_raw = vr.get("quality_score", 0.5)
        existing_violations = list(vr.get("violations", []))

        # Compute new dimensions
        reuse_score, reuse_details = self._score_reusability(skill_dict)
        comp_score, comp_details = self._score_completeness(skill_dict)

        # Build dimension scores
        dimensions = (
            DimensionScore(
                dimension="architecture",
                score=arch_raw,
                weight=self._weight_architecture,
                weighted_score=arch_raw * self._weight_architecture,
            ),
            DimensionScore(
                dimension="security",
                score=sec_raw,
                weight=self._weight_security,
                weighted_score=sec_raw * self._weight_security,
            ),
            DimensionScore(
                dimension="quality",
                score=qual_raw,
                weight=self._weight_quality,
                weighted_score=qual_raw * self._weight_quality,
            ),
            DimensionScore(
                dimension="reusability",
                score=reuse_score,
                weight=self._weight_reusability,
                weighted_score=reuse_score * self._weight_reusability,
                details=tuple(reuse_details),
            ),
            DimensionScore(
                dimension="completeness",
                score=comp_score,
                weight=self._weight_completeness,
                weighted_score=comp_score * self._weight_completeness,
                details=tuple(comp_details),
            ),
        )

        composite = sum(d.weighted_score for d in dimensions)
        composite = max(0.0, min(1.0, composite))

        all_violations = existing_violations + reuse_details + comp_details
        disposition = self._determine_disposition(composite)

        report = QualityReport(
            skill_id=skill_id,
            skill_name=skill_name,
            composite_score=round(composite, 4),
            disposition=disposition,
            dimensions=dimensions,
            violations=tuple(all_violations),
        )

        logger.info(
            "Quality report for '%s': %.2f (%s) — arch=%.2f sec=%.2f qual=%.2f reuse=%.2f comp=%.2f",
            skill_name, composite, disposition,
            arch_raw, sec_raw, qual_raw, reuse_score, comp_score,
        )
        return report

    def _score_reusability(self, skill_dict: dict[str, Any]) -> tuple[float, list[str]]:
        """Score reusability dimension — enforces the 95/5 rule.

        Starts at 1.0, deducts per project-specific indicator found,
        deducts per hardcoded path outside allowed directories,
        deducts if no parameterized inputs, adds bonus per reusable indicator.
        """
        score = 1.0
        details: list[str] = []

        # Concatenate all text fields for scanning
        text_fields = [
            str(skill_dict.get("intent", "")),
            str(skill_dict.get("execution_logic", "")),
            str(skill_dict.get("context", "")),
            str(skill_dict.get("expected_output", "")),
        ]
        full_text = " ".join(text_fields).lower()

        # Deduct per project-specific indicator
        for indicator in self._project_specific_indicators:
            if indicator.lower() in full_text:
                score -= self._deduction_per_indicator
                details.append(f"Reusability: project-specific indicator found: '{indicator}'")

        # Deduct per hardcoded path outside allowed directories
        for pattern in self._hardcoded_path_patterns:
            try:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    is_allowed = any(
                        match.lower().startswith(prefix.lower().replace("\\", "/"))
                        for prefix in self._allowed_path_prefixes
                    )
                    if not is_allowed:
                        score -= self._deduction_per_indicator
                        details.append(f"Reusability: hardcoded path found: '{match}'")
            except re.error:
                logger.warning("Invalid regex pattern in config: %s", pattern)

        # Deduct if no parameterized inputs detected
        input_pattern = skill_dict.get("input_pattern", "")
        if not input_pattern or len(str(input_pattern)) < 10:
            score -= 0.10
            details.append("Reusability: no parameterized input_pattern defined")

        # Bonus per reusable indicator
        bonus = 0.0
        for indicator in self._reusable_indicators:
            if indicator.lower() in full_text:
                bonus += self._bonus_per_indicator
        bonus = min(bonus, self._max_bonus)
        score += bonus
        if bonus > 0:
            details.append(f"Reusability: +{bonus:.2f} bonus for reusable indicators")

        return max(0.0, min(1.0, score)), details

    def _score_completeness(self, skill_dict: dict[str, Any]) -> tuple[float, list[str]]:
        """Score completeness — checks all SKILL.md sections present and substantive."""
        if not self._completeness_sections:
            return 1.0, []

        score = 0.0
        details: list[str] = []
        total_weight = sum(
            sec.get("weight", 0.0) for sec in self._completeness_sections.values()
        )

        for section_name, requirements in self._completeness_sections.items():
            weight = requirements.get("weight", 0.0)
            value = skill_dict.get(section_name, "")

            min_chars = requirements.get("min_chars", 0)
            min_items = requirements.get("min_items", 0)

            section_score = 0.0

            if min_chars > 0:
                # Text-based section
                text = str(value)
                if len(text) >= min_chars:
                    section_score = 1.0
                elif len(text) > 0:
                    section_score = len(text) / min_chars
                else:
                    details.append(f"Completeness: missing section '{section_name}'")

            elif min_items > 0:
                # List-based section
                items = value if isinstance(value, (list, tuple)) else []
                if len(items) >= min_items:
                    section_score = 1.0
                elif len(items) > 0:
                    section_score = len(items) / min_items
                else:
                    details.append(f"Completeness: missing section '{section_name}'")

            if total_weight > 0:
                score += section_score * (weight / total_weight)

        return max(0.0, min(1.0, score)), details

    def _determine_disposition(self, composite: float) -> str:
        """Map composite score to disposition string."""
        if composite >= self._threshold_approved:
            return "approved"
        elif composite >= self._threshold_needs_refactor:
            return "needs_refactor"
        elif composite >= self._threshold_needs_review:
            return "needs_review"
        else:
            return "rejected"

    @staticmethod
    def _load_config() -> dict[str, Any]:
        """Load config from default path, return empty dict on failure."""
        try:
            if _CONFIG_PATH.exists():
                return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load agent config: %s", exc)
        return {}
