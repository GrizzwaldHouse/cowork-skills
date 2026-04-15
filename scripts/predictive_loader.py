# predictive_loader.py
# Developer: Marcus Daley
# Date: 2026-04-06
# Purpose: Co-occurrence based predictive skill preloading

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger("agent.predictive_loader")


class PredictiveLoader:
    """Predicts which skills should be preloaded based on co-occurrence patterns.

    Uses the co_used_with field in the skill registry to identify skills that
    are frequently used together. When a task starts, this loader can suggest
    additional skills to preload alongside the explicitly requested ones.
    """

    def __init__(self, registry: dict[str, Any], config: dict[str, Any]) -> None:
        self._registry: dict[str, Any] = registry
        self._config: dict[str, Any] = config
        self._threshold: float = float(
            config.get("predictive_preload_threshold", 0.6)
        )
        self._min_co_occurrence: int = int(
            config.get("predictive_co_occurrence_min", 3)
        )

    def get_preload_candidates(
        self,
        loaded_skills: list[str],
        max_slots: int,
    ) -> list[str]:
        """Return a ranked list of skills to preload alongside loaded_skills.

        Algorithm:
            1. For each loaded skill, look up its co_used_with map.
            2. Aggregate counts: how many of the loaded skills each candidate
               has been used with.
            3. Filter: candidate must meet min co-occurrence count threshold.
            4. Compute ratio = co_occurrence_count / len(loaded_skills).
            5. Filter: ratio must meet predictive_preload_threshold.
            6. Score = usage_count * ratio.
            7. Sort by score descending, return top max_slots.
            8. Exclude already-loaded skills.
        """
        if not loaded_skills or max_slots <= 0:
            return []

        skills_data: dict[str, Any] = self._registry.get("skills", {})
        loaded_set: set[str] = set(loaded_skills)
        candidate_counts: dict[str, int] = {}

        # Aggregate co-occurrence counts across all loaded skills
        for skill_name in loaded_skills:
            entry = skills_data.get(skill_name, {})
            co_used = entry.get("co_used_with", {})
            # co_used can be either a dict {name: count} or a list [names]
            if isinstance(co_used, dict):
                for candidate, count in co_used.items():
                    if candidate in loaded_set:
                        continue
                    candidate_counts[candidate] = (
                        candidate_counts.get(candidate, 0) + int(count)
                    )
            elif isinstance(co_used, list):
                for candidate in co_used:
                    if candidate in loaded_set:
                        continue
                    candidate_counts[candidate] = (
                        candidate_counts.get(candidate, 0) + 1
                    )

        # Apply filters and compute scores
        scored: list[tuple[str, float]] = []
        loaded_count = len(loaded_skills)
        for candidate, count in candidate_counts.items():
            if count < self._min_co_occurrence:
                continue
            ratio = count / loaded_count if loaded_count > 0 else 0.0
            if ratio < self._threshold:
                continue
            usage_count = int(skills_data.get(candidate, {}).get("usage_count", 0))
            # Use usage_count + 1 to ensure new skills can still be ranked
            score = (usage_count + 1) * ratio
            scored.append((candidate, score))

        # Sort by score descending, take top N
        scored.sort(key=lambda pair: pair[1], reverse=True)
        result = [name for name, _ in scored[:max_slots]]
        logger.debug(
            "Preload candidates: %d total, %d filtered to top %d",
            len(candidate_counts), len(scored), len(result),
        )
        return result

    def update_co_occurrence(
        self,
        registry: dict[str, Any],
        skills_used: list[str],
    ) -> dict[str, Any]:
        """Update co_used_with counts for all skills in skills_used.

        For each pair (A, B) in skills_used, increments
        registry[A].co_used_with[B] and vice versa.
        """
        if len(skills_used) < 2:
            return registry

        skills_data: dict[str, Any] = registry.setdefault("skills", {})
        for skill_a in skills_used:
            entry = skills_data.setdefault(skill_a, {})
            co_used = entry.get("co_used_with", {})
            # Normalize list form to dict form
            if isinstance(co_used, list):
                co_used = {name: 1 for name in co_used}
            elif not isinstance(co_used, dict):
                co_used = {}

            for skill_b in skills_used:
                if skill_b == skill_a:
                    continue
                co_used[skill_b] = int(co_used.get(skill_b, 0)) + 1

            entry["co_used_with"] = co_used
            skills_data[skill_a] = entry

        return registry
