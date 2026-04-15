# performance_optimizer.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Performance optimization for Ollama model inference using historical metrics

"""
Performance optimizer for Ollama-based intelligence pipeline.

Manages performance profiles (fast, balanced, quality), tracks historical
metrics (accuracy, latency, tokens/sec), and tunes generation parameters
based on model+task performance history. All data persisted to JSON for
cross-session learning.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROFILE_FAST = "fast"
PROFILE_BALANCED = "balanced"
PROFILE_QUALITY = "quality"
DEFAULT_PROFILE = PROFILE_BALANCED
OPTIMIZATION_DATA_DIR = Path("C:/ClaudeSkills/data/ollama")

# Profile-specific parameter presets for Ollama generation
PROFILE_PARAMETERS: dict[str, dict[str, Any]] = {
    PROFILE_FAST: {
        "temperature": 0.1,
        "top_p": 0.5,
        "num_ctx": 2048,
        "repeat_penalty": 1.0,
        "num_predict": 256,
    },
    PROFILE_BALANCED: {
        "temperature": 0.3,
        "top_p": 0.8,
        "num_ctx": 4096,
        "repeat_penalty": 1.1,
        "num_predict": 512,
    },
    PROFILE_QUALITY: {
        "temperature": 0.7,
        "top_p": 0.95,
        "num_ctx": 8192,
        "repeat_penalty": 1.2,
        "num_predict": 1024,
    },
}

# Thresholds for profile suggestion based on historical accuracy
HIGH_ACCURACY_THRESHOLD = 0.85
LOW_ACCURACY_THRESHOLD = 0.65

# ---------------------------------------------------------------------------
# Dataclasses (frozen for immutability)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerformanceProfile:
    """Aggregated performance metrics for a model+task combination."""

    model: str
    task_type: str
    avg_accuracy: float
    avg_latency_ms: float
    avg_tokens_per_second: float
    sample_count: int


@dataclass(frozen=True)
class OptimizedConfig:
    """Tuned configuration for Ollama generation based on profile."""

    model: str
    profile: str
    parameters: dict[str, Any]
    expected_quality: float
    expected_latency_ms: float


@dataclass(frozen=True)
class OptimizationRecord:
    """Single performance measurement record for persistence."""

    model: str
    task_type: str
    profile: str
    parameters: dict[str, Any]
    result_accuracy: float
    result_latency_ms: float
    timestamp: str


# ---------------------------------------------------------------------------
# PerformanceOptimizer
# ---------------------------------------------------------------------------


class PerformanceOptimizer:
    """Manages performance profiling and optimization for Ollama models.

    Tracks historical performance metrics per model+task, suggests optimal
    profiles based on accuracy trends, and returns tuned generation configs.
    All records persisted to optimization_history.json for continuous learning.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize optimizer with optional configuration.

        Args:
            config: Optional dict with keys:
                - default_profile: str (default: PROFILE_BALANCED)
                - profiles: dict[str, dict] (default: PROFILE_PARAMETERS)
                - history_path: Path (default: OPTIMIZATION_DATA_DIR / optimization_history.json)
        """
        if config is None:
            config = {}

        self._default_profile: str = config.get("default_profile", DEFAULT_PROFILE)
        self._profiles: dict[str, dict[str, Any]] = config.get("profiles", PROFILE_PARAMETERS)
        self._history_path: Path = config.get(
            "history_path",
            OPTIMIZATION_DATA_DIR / "optimization_history.json",
        )

        # Ensure data directory exists
        self._history_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(
        self,
        model: str,
        task_type: str,
        profile: str = DEFAULT_PROFILE,
    ) -> OptimizedConfig:
        """Generate optimized configuration for model+task+profile.

        Analyzes historical performance data and returns tuned parameters.
        If no history exists, returns default parameters for the profile.

        Args:
            model: Model identifier (e.g. "llama2:7b")
            task_type: Task category (e.g. "code_review", "summarization")
            profile: Performance profile (fast/balanced/quality)

        Returns:
            OptimizedConfig with parameters and expected metrics.
        """
        # Get base parameters for profile
        parameters = self.get_profile_parameters(profile)

        # Analyze historical performance for this model+task
        perf_profile = self.analyze_history(model, task_type)

        if perf_profile is None:
            # No history -- return defaults with conservative estimates
            return OptimizedConfig(
                model=model,
                profile=profile,
                parameters=parameters,
                expected_quality=0.7,
                expected_latency_ms=1000.0,
            )

        # Use historical averages for expected metrics
        return OptimizedConfig(
            model=model,
            profile=profile,
            parameters=parameters,
            expected_quality=perf_profile.avg_accuracy,
            expected_latency_ms=perf_profile.avg_latency_ms,
        )

    def get_profile_parameters(self, profile: str) -> dict[str, Any]:
        """Retrieve Ollama generation parameters for a performance profile.

        Args:
            profile: Profile name (fast/balanced/quality)

        Returns:
            Dict of Ollama generation parameters (temperature, top_p, etc.)
        """
        return self._profiles.get(profile, self._profiles[PROFILE_BALANCED]).copy()

    def analyze_history(
        self,
        model: str,
        task_type: str,
    ) -> PerformanceProfile | None:
        """Analyze historical performance records for model+task.

        Args:
            model: Model identifier
            task_type: Task category

        Returns:
            PerformanceProfile with aggregated metrics, or None if no history.
        """
        records = self._load_history()
        matching = [
            r for r in records
            if r.model == model and r.task_type == task_type
        ]

        if not matching:
            return None

        # Calculate averages across all matching records
        avg_accuracy = sum(r.result_accuracy for r in matching) / len(matching)
        avg_latency = sum(r.result_latency_ms for r in matching) / len(matching)

        # Calculate avg tokens/sec (stored in parameters if available)
        # For now, derive from latency (inverse relationship approximation)
        avg_tokens_per_sec = 1000.0 / avg_latency if avg_latency > 0 else 0.0

        return PerformanceProfile(
            model=model,
            task_type=task_type,
            avg_accuracy=avg_accuracy,
            avg_latency_ms=avg_latency,
            avg_tokens_per_second=avg_tokens_per_sec,
            sample_count=len(matching),
        )

    def record_result(
        self,
        model: str,
        task_type: str,
        profile: str,
        parameters: dict[str, Any],
        accuracy: float,
        latency_ms: float,
    ) -> None:
        """Record a performance measurement for future optimization.

        Args:
            model: Model identifier
            task_type: Task category
            profile: Performance profile used
            parameters: Ollama generation parameters used
            accuracy: Measured accuracy (0.0-1.0)
            latency_ms: Total inference latency in milliseconds
        """
        record = OptimizationRecord(
            model=model,
            task_type=task_type,
            profile=profile,
            parameters=parameters,
            result_accuracy=accuracy,
            result_latency_ms=latency_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._save_record(record)

    def suggest_profile(self, model: str, task_type: str) -> str:
        """Suggest optimal profile based on historical performance.

        Strategy:
        - If avg accuracy >= HIGH_ACCURACY_THRESHOLD: suggest "fast"
        - If avg accuracy <= LOW_ACCURACY_THRESHOLD: suggest "quality"
        - Otherwise: suggest "balanced"

        Args:
            model: Model identifier
            task_type: Task category

        Returns:
            Suggested profile name (fast/balanced/quality)
        """
        perf_profile = self.analyze_history(model, task_type)

        if perf_profile is None:
            return PROFILE_BALANCED

        if perf_profile.avg_accuracy >= HIGH_ACCURACY_THRESHOLD:
            return PROFILE_FAST
        elif perf_profile.avg_accuracy <= LOW_ACCURACY_THRESHOLD:
            return PROFILE_QUALITY
        else:
            return PROFILE_BALANCED

    def get_available_profiles(self) -> list[str]:
        """Return list of all available performance profiles.

        Returns:
            List of profile names.
        """
        return [PROFILE_FAST, PROFILE_BALANCED, PROFILE_QUALITY]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_history(self) -> list[OptimizationRecord]:
        """Load all optimization records from JSON file.

        Returns:
            List of OptimizationRecord objects (may be empty).
        """
        if not self._history_path.exists():
            return []

        try:
            with self._history_path.open("r", encoding="utf-8") as fh:
                lines = fh.readlines()

            records: list[OptimizationRecord] = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                records.append(
                    OptimizationRecord(
                        model=data["model"],
                        task_type=data["task_type"],
                        profile=data["profile"],
                        parameters=data["parameters"],
                        result_accuracy=data["result_accuracy"],
                        result_latency_ms=data["result_latency_ms"],
                        timestamp=data["timestamp"],
                    ),
                )
            return records
        except (OSError, json.JSONDecodeError):
            # File corrupted or unreadable -- return empty list
            return []

    def _save_record(self, record: OptimizationRecord) -> None:
        """Append a single optimization record to the history file.

        Args:
            record: OptimizationRecord to persist.
        """
        # Convert record to dict for JSON serialization
        data = {
            "model": record.model,
            "task_type": record.task_type,
            "profile": record.profile,
            "parameters": record.parameters,
            "result_accuracy": record.result_accuracy,
            "result_latency_ms": record.result_latency_ms,
            "timestamp": record.timestamp,
        }

        # Append as newline-delimited JSON
        with self._history_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(data) + "\n")
