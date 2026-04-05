# improvement_tracker.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Improvement trend tracking and refactor cooldown management

from __future__ import annotations
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent.improvement_tracker")

_DATA_DIR: Path = Path("C:/ClaudeSkills/data/improvement_history")


@dataclass(frozen=True)
class ImprovementRecord:
    """Single improvement attempt record."""
    skill_id: str
    skill_name: str
    previous_score: float
    new_score: float
    improved: bool
    iterations: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ImprovementTrendTracker:
    """Tracks per-skill improvement history for regression prevention.

    Maintains a monotonic best-score record per skill. A refactored skill
    must score at or above its historical best (within tolerance) to be
    accepted. Persists history to disk for cross-session continuity.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        improvement_cfg = cfg.get("improvement", {})
        self._regression_tolerance: float = improvement_cfg.get("regression_tolerance", 0.0)
        self._data_dir: Path = _DATA_DIR
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._lock: threading.Lock = threading.Lock()
        # skill_id → list of ImprovementRecord
        self._history: dict[str, list[ImprovementRecord]] = {}
        # skill_id → best composite score ever achieved
        self._best_scores: dict[str, float] = {}

        self._load_history()

    def record(self, record: ImprovementRecord) -> None:
        """Record an improvement attempt and update best score."""
        with self._lock:
            if record.skill_id not in self._history:
                self._history[record.skill_id] = []
            self._history[record.skill_id].append(record)

            current_best = self._best_scores.get(record.skill_id, 0.0)
            if record.new_score > current_best:
                self._best_scores[record.skill_id] = record.new_score

            self._save_history()

        logger.info(
            "Recorded improvement for '%s': %.2f → %.2f (%s)",
            record.skill_name, record.previous_score, record.new_score,
            "improved" if record.improved else "no improvement",
        )

    def check_regression(self, skill_id: str, new_score: float) -> bool:
        """Check if a new score represents regression from historical best.

        Returns True if score is a regression (below best - tolerance).
        Returns False if score is acceptable.
        """
        with self._lock:
            best = self._best_scores.get(skill_id, 0.0)
        threshold = best - self._regression_tolerance
        is_regression = new_score < threshold
        if is_regression:
            logger.warning(
                "Regression detected for '%s': %.2f < best %.2f (tolerance: %.2f)",
                skill_id, new_score, best, self._regression_tolerance,
            )
        return is_regression

    def get_best_score(self, skill_id: str) -> float:
        """Return the historical best score for a skill."""
        with self._lock:
            return self._best_scores.get(skill_id, 0.0)

    def get_history(self, skill_id: str) -> list[ImprovementRecord]:
        """Return all improvement records for a skill."""
        with self._lock:
            return list(self._history.get(skill_id, []))

    def get_trend(self, skill_id: str, window: int = 5) -> dict[str, Any]:
        """Compute trend statistics over the last N records."""
        with self._lock:
            records = self._history.get(skill_id, [])

        if not records:
            return {"direction": "none", "records": 0, "avg_delta": 0.0}

        recent = records[-window:]
        deltas = [r.new_score - r.previous_score for r in recent]
        avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

        if avg_delta > 0.01:
            direction = "improving"
        elif avg_delta < -0.01:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "records": len(recent),
            "avg_delta": round(avg_delta, 4),
            "best_score": self.get_best_score(skill_id),
            "latest_score": recent[-1].new_score if recent else 0.0,
        }

    def _load_history(self) -> None:
        """Load persisted history from disk."""
        history_file = self._data_dir / "improvement_history.json"
        try:
            if history_file.exists():
                data = json.loads(history_file.read_text(encoding="utf-8"))
                for skill_id, records in data.get("history", {}).items():
                    self._history[skill_id] = [
                        ImprovementRecord(**r) for r in records
                    ]
                self._best_scores = dict(data.get("best_scores", {}))
                logger.info(
                    "Loaded improvement history: %d skills tracked",
                    len(self._history),
                )
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            logger.warning("Failed to load improvement history: %s", exc)

    def _save_history(self) -> None:
        """Persist history to disk."""
        history_file = self._data_dir / "improvement_history.json"
        try:
            data = {
                "history": {
                    sid: [asdict(r) for r in records]
                    for sid, records in self._history.items()
                },
                "best_scores": dict(self._best_scores),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            history_file.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Failed to save improvement history: %s", exc)


class RefactorCooldownTracker:
    """Prevents rapid-fire refactoring of the same skill.

    After a failed refactor attempt, the skill enters a cooldown period
    during which no further refactoring is attempted. Consecutive failures
    escalate to needs_review status.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        improvement_cfg = cfg.get("improvement", {})
        self._cooldown_seconds: float = improvement_cfg.get("cooldown_seconds", 300.0)
        self._max_consecutive_failures: int = improvement_cfg.get(
            "max_consecutive_failures", 3
        )

        self._lock: threading.Lock = threading.Lock()
        # skill_id → last failure timestamp (ISO string)
        self._last_failure: dict[str, str] = {}
        # skill_id → consecutive failure count
        self._failure_counts: dict[str, int] = {}

    def is_on_cooldown(self, skill_id: str) -> bool:
        """Check if a skill is still in cooldown period."""
        with self._lock:
            last = self._last_failure.get(skill_id)
            if last is None:
                return False

            last_dt = datetime.fromisoformat(last)
            elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
            return elapsed < self._cooldown_seconds

    def record_failure(self, skill_id: str) -> int:
        """Record a refactor failure. Returns consecutive failure count."""
        with self._lock:
            self._last_failure[skill_id] = datetime.now(timezone.utc).isoformat()
            count = self._failure_counts.get(skill_id, 0) + 1
            self._failure_counts[skill_id] = count
            logger.info(
                "Refactor failure #%d for '%s' — cooldown %.0fs",
                count, skill_id, self._cooldown_seconds,
            )
            return count

    def record_success(self, skill_id: str) -> None:
        """Reset failure tracking for a skill after successful refactor."""
        with self._lock:
            self._failure_counts.pop(skill_id, None)
            self._last_failure.pop(skill_id, None)

    def should_escalate(self, skill_id: str) -> bool:
        """Check if skill has exceeded max consecutive failures."""
        with self._lock:
            count = self._failure_counts.get(skill_id, 0)
            return count >= self._max_consecutive_failures

    def get_failure_count(self, skill_id: str) -> int:
        """Return current consecutive failure count."""
        with self._lock:
            return self._failure_counts.get(skill_id, 0)

    def get_cooldown_remaining(self, skill_id: str) -> float:
        """Return seconds remaining in cooldown, or 0.0 if not on cooldown."""
        with self._lock:
            last = self._last_failure.get(skill_id)
            if last is None:
                return 0.0
            last_dt = datetime.fromisoformat(last)
            elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
            remaining = self._cooldown_seconds - elapsed
            return max(0.0, remaining)
