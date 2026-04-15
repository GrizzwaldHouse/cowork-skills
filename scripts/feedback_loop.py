# feedback_loop.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Self-improving feedback loop — tracks pipeline metrics and adjusts behavior over time

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent.feedback_loop")

_METRICS_PATH: Path = Path("C:/ClaudeSkills/data/feedback_metrics.json")


@dataclass(frozen=True)
class TrendReport:
    """Score trajectory for a skill over a window of cycles."""

    skill_id: str
    direction: str  # improving, declining, stable, none
    avg_score: float
    score_history: tuple[float, ...]
    avg_delta: float
    cycles_tracked: int


@dataclass(frozen=True)
class ImprovementTarget:
    """Prioritized improvement target identified by the feedback loop."""

    skill_id: str
    skill_name: str
    current_score: float
    target_score: float
    priority: int  # 1=highest
    reason: str


@dataclass
class SkillMetrics:
    """Per-skill accumulated metrics."""

    skill_id: str = ""
    skill_name: str = ""
    score_history: list[float] = field(default_factory=list)
    refactor_count: int = 0
    rejection_count: int = 0
    approval_count: int = 0
    sync_count: int = 0
    last_score: float = 0.0
    last_updated: str = ""


@dataclass
class GlobalMetrics:
    """System-wide accumulated metrics."""

    total_cycles: int = 0
    total_extracted: int = 0
    total_validated: int = 0
    total_approved: int = 0
    total_rejected: int = 0
    total_refactored: int = 0
    total_synced: int = 0
    refactor_failures: int = 0
    avg_quality_score: float = 0.0
    rejection_rate: float = 0.0
    auto_refactor_success_rate: float = 0.0
    rolling_scores: list[float] = field(default_factory=list)


class FeedbackLoop:
    """Self-improving feedback loop for the skill pipeline.

    Tracks per-skill and global metrics over pipeline cycles, identifies
    trends, and generates improvement targets. Optionally adjusts
    pipeline thresholds when average quality consistently exceeds minimums.

    Metrics are persisted to data/feedback_metrics.json for cross-session
    continuity.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        feedback_cfg = cfg.get("feedback", {})

        self._trend_window: int = feedback_cfg.get("trend_window", 10)
        self._rejection_alert: float = feedback_cfg.get(
            "rejection_rate_alert", 0.40
        )
        self._auto_adjust: bool = feedback_cfg.get(
            "auto_adjust_thresholds", False
        )
        self._metrics_path: Path = Path(
            feedback_cfg.get("metrics_path", str(_METRICS_PATH))
        )
        if not self._metrics_path.is_absolute():
            self._metrics_path = Path("C:/ClaudeSkills") / self._metrics_path

        self._lock: threading.RLock = threading.RLock()
        self._skill_metrics: dict[str, SkillMetrics] = {}
        self._global: GlobalMetrics = GlobalMetrics()

        self._load_metrics()

    def record_cycle(self, cycle_result: Any) -> None:
        """Record a pipeline cycle result and update all metrics.

        Accepts a PipelineCycleResult (or any object with matching attributes
        or a dict with matching keys).
        """
        # Normalize to dict
        if hasattr(cycle_result, "__dataclass_fields__"):
            data = asdict(cycle_result)
        elif isinstance(cycle_result, dict):
            data = cycle_result
        else:
            data = vars(cycle_result) if hasattr(cycle_result, "__dict__") else {}

        with self._lock:
            g = self._global
            g.total_cycles += 1
            g.total_extracted += data.get("skills_extracted", 0)
            g.total_validated += data.get("skills_validated", 0)
            g.total_approved += data.get("skills_approved", 0)
            g.total_rejected += data.get("skills_rejected", 0)
            g.total_refactored += data.get("skills_refactored", 0)
            g.total_synced += data.get("skills_synced", 0)
            g.refactor_failures += data.get("refactor_failures", 0)

            # Update rates
            total_decisions = g.total_approved + g.total_rejected
            if total_decisions > 0:
                g.rejection_rate = g.total_rejected / total_decisions

            total_refactor_attempts = g.total_refactored + g.refactor_failures
            if total_refactor_attempts > 0:
                g.auto_refactor_success_rate = (
                    g.total_refactored / total_refactor_attempts
                )

        self._save_metrics()

        # Alert if rejection rate exceeds threshold
        if self._global.rejection_rate > self._rejection_alert:
            logger.warning(
                "High rejection rate: %.0f%% (threshold: %.0f%%) — "
                "consider improving extraction prompts",
                self._global.rejection_rate * 100,
                self._rejection_alert * 100,
            )

    def record_skill_score(
        self,
        skill_id: str,
        skill_name: str,
        score: float,
        disposition: str,
    ) -> None:
        """Record an individual skill's validation score."""
        with self._lock:
            metrics = self._skill_metrics.setdefault(
                skill_id, SkillMetrics(skill_id=skill_id, skill_name=skill_name)
            )
            metrics.score_history.append(round(score, 4))
            metrics.last_score = round(score, 4)
            metrics.last_updated = datetime.now(timezone.utc).isoformat()

            if disposition == "approved":
                metrics.approval_count += 1
            elif disposition == "rejected":
                metrics.rejection_count += 1
            elif disposition == "needs_refactor":
                metrics.refactor_count += 1

            # Keep score history bounded
            if len(metrics.score_history) > 100:
                metrics.score_history = metrics.score_history[-100:]

            # Update global rolling scores
            self._global.rolling_scores.append(round(score, 4))
            if len(self._global.rolling_scores) > 100:
                self._global.rolling_scores = self._global.rolling_scores[-100:]

            if self._global.rolling_scores:
                self._global.avg_quality_score = round(
                    sum(self._global.rolling_scores)
                    / len(self._global.rolling_scores),
                    4,
                )

        self._save_metrics()

    def get_trend(self, skill_id: str, window: int | None = None) -> TrendReport:
        """Compute score trajectory for a skill over recent cycles."""
        w = window or self._trend_window

        with self._lock:
            metrics = self._skill_metrics.get(skill_id)
            if not metrics or not metrics.score_history:
                return TrendReport(
                    skill_id=skill_id,
                    direction="none",
                    avg_score=0.0,
                    score_history=(),
                    avg_delta=0.0,
                    cycles_tracked=0,
                )

            recent = metrics.score_history[-w:]
            avg = sum(recent) / len(recent) if recent else 0.0

            # Compute deltas between consecutive scores
            deltas = [
                recent[i] - recent[i - 1] for i in range(1, len(recent))
            ]
            avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

        if avg_delta > 0.01:
            direction = "improving"
        elif avg_delta < -0.01:
            direction = "declining"
        else:
            direction = "stable"

        return TrendReport(
            skill_id=skill_id,
            direction=direction,
            avg_score=round(avg, 4),
            score_history=tuple(recent),
            avg_delta=round(avg_delta, 4),
            cycles_tracked=len(recent),
        )

    def identify_weak_patterns(self) -> list[str]:
        """Identify common failure patterns across all tracked skills."""
        patterns: list[str] = []

        with self._lock:
            # High rejection rate
            if self._global.rejection_rate > self._rejection_alert:
                patterns.append(
                    f"High rejection rate: {self._global.rejection_rate:.0%}"
                )

            # Skills that never pass
            for sid, metrics in self._skill_metrics.items():
                if metrics.rejection_count > 3 and metrics.approval_count == 0:
                    patterns.append(
                        f"Persistently rejected: '{metrics.skill_name}' "
                        f"({metrics.rejection_count} rejections, 0 approvals)"
                    )

            # Low refactor success rate
            if (
                self._global.auto_refactor_success_rate < 0.3
                and self._global.total_refactored + self._global.refactor_failures > 5
            ):
                patterns.append(
                    f"Low refactor success rate: "
                    f"{self._global.auto_refactor_success_rate:.0%}"
                )

        return patterns

    def generate_improvement_targets(self) -> list[ImprovementTarget]:
        """Generate a prioritized list of skills that need improvement."""
        targets: list[ImprovementTarget] = []

        with self._lock:
            for sid, metrics in self._skill_metrics.items():
                if not metrics.score_history:
                    continue

                latest = metrics.score_history[-1]
                if latest < 0.85:
                    # Determine priority: lower score = higher priority
                    if latest < 0.5:
                        priority = 1
                        reason = "Below minimum quality threshold"
                    elif latest < 0.7:
                        priority = 2
                        reason = "Below reusability threshold"
                    else:
                        priority = 3
                        reason = "Close to approval — minor improvements needed"

                    targets.append(ImprovementTarget(
                        skill_id=sid,
                        skill_name=metrics.skill_name,
                        current_score=latest,
                        target_score=0.85,
                        priority=priority,
                        reason=reason,
                    ))

        # Sort by priority (ascending), then by score (ascending)
        targets.sort(key=lambda t: (t.priority, t.current_score))
        return targets

    def adjust_thresholds(self) -> dict[str, float] | None:
        """Suggest threshold adjustments based on accumulated metrics.

        Only suggests changes if auto_adjust is enabled and there's
        enough data. Returns a dict of suggested threshold changes,
        or None if no adjustment is warranted.
        """
        if not self._auto_adjust:
            return None

        with self._lock:
            if self._global.total_cycles < 10:
                return None

            avg = self._global.avg_quality_score
            rejection = self._global.rejection_rate

        suggestions: dict[str, float] = {}

        # If average quality is consistently high, raise the bar
        if avg > 0.90 and rejection < 0.15:
            suggestions["approved"] = min(0.95, 0.85 + 0.05)
            logger.info(
                "Suggesting threshold increase: avg=%.2f, rejection=%.0f%%",
                avg, rejection * 100,
            )

        # If rejection rate is too high, slightly lower the bar
        if rejection > 0.50 and avg > 0.60:
            suggestions["needs_refactor"] = max(0.40, 0.50 - 0.05)
            logger.info(
                "Suggesting threshold decrease: rejection=%.0f%%",
                rejection * 100,
            )

        return suggestions if suggestions else None

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of all feedback metrics."""
        with self._lock:
            return {
                "global": asdict(self._global),
                "skills_tracked": len(self._skill_metrics),
                "weak_patterns": self.identify_weak_patterns(),
                "improvement_targets": [
                    asdict(t)
                    for t in self.generate_improvement_targets()[:5]
                ],
            }

    # -- Persistence -------------------------------------------------------

    def _load_metrics(self) -> None:
        """Load persisted metrics from disk."""
        try:
            if self._metrics_path.exists():
                data = json.loads(
                    self._metrics_path.read_text(encoding="utf-8")
                )
                # Restore global metrics
                global_data = data.get("global", {})
                for key, val in global_data.items():
                    if hasattr(self._global, key):
                        setattr(self._global, key, val)

                # Restore skill metrics
                for sid, sdata in data.get("skills", {}).items():
                    self._skill_metrics[sid] = SkillMetrics(**sdata)

                logger.info(
                    "Loaded feedback metrics: %d skills, %d cycles",
                    len(self._skill_metrics),
                    self._global.total_cycles,
                )
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            logger.warning("Failed to load feedback metrics: %s", exc)

    def _save_metrics(self) -> None:
        """Persist metrics to disk."""
        try:
            self._metrics_path.parent.mkdir(parents=True, exist_ok=True)

            with self._lock:
                data = {
                    "global": asdict(self._global),
                    "skills": {
                        sid: asdict(m)
                        for sid, m in self._skill_metrics.items()
                    },
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }

            self._metrics_path.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("Failed to save feedback metrics: %s", exc)
