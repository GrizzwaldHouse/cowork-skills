# model_benchmark.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Benchmark framework for Ollama model evaluation and performance scoring

"""
Model benchmark system for evaluating Ollama LLM performance.

Provides standardized tasks across multiple categories (code generation, review,
refactoring, documentation, debugging), scoring mechanisms, and historical report
management. Designed to support data-driven model selection in the intelligence
pipeline.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ollama.ollama_client import GenerateResult, OllamaClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_RUNS_PER_TASK = 3
BENCHMARK_DATA_DIR = Path("C:/ClaudeSkills/data/benchmarks")

# ---------------------------------------------------------------------------
# Dataclasses (frozen for immutability)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BenchmarkTask:
    """Single benchmark task with prompt and expected output."""

    name: str
    category: str  # code_generation/code_review/refactoring/documentation/debugging
    prompt: str
    expected_output: str
    max_score: float = 100.0


@dataclass(frozen=True)
class TaskResult:
    """Result from executing a benchmark task."""

    task_name: str
    model: str
    accuracy: float
    code_quality: float
    latency_ms: float
    tokens_per_second: float
    runs: int


@dataclass(frozen=True)
class ModelScore:
    """Aggregate score for a model across all tasks."""

    model: str
    overall: float
    accuracy: float
    code_quality: float
    consistency: float
    efficiency: float
    tasks_completed: int


@dataclass(frozen=True)
class BenchmarkReport:
    """Complete benchmark report with all models and results."""

    timestamp: str
    models_tested: tuple[str, ...]
    task_count: int
    model_scores: tuple[ModelScore, ...]
    task_results: tuple[TaskResult, ...]
    best_model_per_task: dict[str, str]
    overall_rankings: tuple[str, ...]


# ---------------------------------------------------------------------------
# Benchmark Engine
# ---------------------------------------------------------------------------


class ModelBenchmark:
    """Benchmark engine for evaluating Ollama model performance.

    Executes standardized tasks across multiple models, scores results using
    accuracy and code quality metrics, and generates comprehensive reports.
    Supports historical tracking for data-driven model selection.
    """

    def __init__(
        self,
        client: OllamaClient | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize benchmark engine.

        Args:
            client: Optional OllamaClient instance (creates default if None)
            config: Optional configuration dict with runs_per_task and timeout
        """
        self._client = client if client is not None else OllamaClient()
        self._config = config if config is not None else {}
        self._runs_per_task = self._config.get("runs_per_task", DEFAULT_RUNS_PER_TASK)
        self._timeout = self._config.get("timeout", 120)

    def run_benchmark(
        self,
        models: list[str],
        tasks: list[BenchmarkTask] | None = None,
    ) -> BenchmarkReport:
        """Execute benchmark across all models and tasks.

        Args:
            models: List of model names to benchmark
            tasks: Optional task list (uses default tasks if None)

        Returns:
            BenchmarkReport with complete results and rankings.
        """
        if tasks is None:
            tasks = self.get_default_tasks()

        if not models:
            # Return empty report for no models
            return BenchmarkReport(
                timestamp=datetime.now(timezone.utc).isoformat(),
                models_tested=tuple(),
                task_count=len(tasks),
                model_scores=tuple(),
                task_results=tuple(),
                best_model_per_task={},
                overall_rankings=tuple(),
            )

        all_results: list[TaskResult] = []
        model_results_map: dict[str, list[TaskResult]] = {m: [] for m in models}

        # Execute all tasks for all models
        for model in models:
            for task in tasks:
                task_runs: list[tuple[float, float, float, float]] = []

                for _ in range(self._runs_per_task):
                    try:
                        start_ns = time.perf_counter_ns()
                        result = self._client.generate(model=model, prompt=task.prompt)
                        end_ns = time.perf_counter_ns()

                        latency_ms = (end_ns - start_ns) / 1_000_000
                        accuracy, quality = self._score_task_result(
                            result.response, task
                        )
                        task_runs.append(
                            (accuracy, quality, latency_ms, result.tokens_per_second)
                        )
                    except Exception:
                        # On error, record zero scores
                        task_runs.append((0.0, 0.0, 0.0, 0.0))

                # Aggregate across runs
                avg_accuracy = sum(r[0] for r in task_runs) / len(task_runs)
                avg_quality = sum(r[1] for r in task_runs) / len(task_runs)
                avg_latency = sum(r[2] for r in task_runs) / len(task_runs)
                avg_tps = sum(r[3] for r in task_runs) / len(task_runs)

                task_result = TaskResult(
                    task_name=task.name,
                    model=model,
                    accuracy=avg_accuracy,
                    code_quality=avg_quality,
                    latency_ms=avg_latency,
                    tokens_per_second=avg_tps,
                    runs=self._runs_per_task,
                )

                all_results.append(task_result)
                model_results_map[model].append(task_result)

        # Calculate model scores
        model_scores: list[ModelScore] = []
        for model in models:
            score = self._calculate_model_score(model_results_map[model])
            model_scores.append(score)

        # Determine best model per task
        best_per_task: dict[str, str] = {}
        for task in tasks:
            task_results_for_task = [r for r in all_results if r.task_name == task.name]
            if task_results_for_task:
                best = max(task_results_for_task, key=lambda r: r.accuracy)
                best_per_task[task.name] = best.model

        # Overall rankings (sorted by overall score descending)
        sorted_scores = sorted(model_scores, key=lambda s: s.overall, reverse=True)
        rankings = tuple(s.model for s in sorted_scores)

        return BenchmarkReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            models_tested=tuple(models),
            task_count=len(tasks),
            model_scores=tuple(model_scores),
            task_results=tuple(all_results),
            best_model_per_task=best_per_task,
            overall_rankings=rankings,
        )

    def _score_task_result(
        self, output: str, task: BenchmarkTask
    ) -> tuple[float, float]:
        """Score a task result using accuracy and code quality heuristics.

        Args:
            output: Model-generated output text
            expected: Expected output text from task definition

        Returns:
            Tuple of (accuracy, code_quality) both in range [0.0, 100.0]
        """
        expected = task.expected_output

        # Accuracy: word overlap ratio
        output_words = set(output.lower().split())
        expected_words = set(expected.lower().split())

        if not expected_words:
            accuracy = 0.0
        else:
            overlap = len(output_words & expected_words)
            accuracy = min(100.0, (overlap / len(expected_words)) * 100.0)

        # Code quality: heuristic checks
        quality_score = 0.0
        max_quality = 100.0

        # Check for code block markers
        if "```" in output or "def " in output or "class " in output:
            quality_score += 20.0

        # Check for comments
        if "#" in output or "//" in output:
            quality_score += 15.0

        # Check for type hints (Python)
        if "->" in output or ": " in output:
            quality_score += 15.0

        # Check for proper formatting (indentation)
        lines = output.split("\n")
        indented_lines = [l for l in lines if l.startswith("    ") or l.startswith("\t")]
        if len(indented_lines) > 0:
            quality_score += 20.0

        # Check for error handling
        if "try" in output.lower() or "except" in output.lower() or "error" in output.lower():
            quality_score += 15.0

        # Check for documentation strings
        if '"""' in output or "'''" in output:
            quality_score += 15.0

        return (accuracy, min(max_quality, quality_score))

    def _calculate_model_score(self, results: list[TaskResult]) -> ModelScore:
        """Calculate aggregate score for a model across all tasks.

        Args:
            results: List of TaskResult for a single model

        Returns:
            ModelScore with averaged metrics.
        """
        if not results:
            return ModelScore(
                model="unknown",
                overall=0.0,
                accuracy=0.0,
                code_quality=0.0,
                consistency=0.0,
                efficiency=0.0,
                tasks_completed=0,
            )

        model = results[0].model
        avg_accuracy = sum(r.accuracy for r in results) / len(results)
        avg_quality = sum(r.code_quality for r in results) / len(results)

        # Consistency: inverse coefficient of variation for accuracy
        accuracies = [r.accuracy for r in results]
        mean_acc = sum(accuracies) / len(accuracies)
        if mean_acc > 0:
            variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)
            std_dev = variance**0.5
            cv = std_dev / mean_acc
            consistency = max(0.0, 100.0 - (cv * 100.0))
        else:
            consistency = 0.0

        # Efficiency: normalized tokens per second (cap at 100)
        avg_tps = sum(r.tokens_per_second for r in results) / len(results)
        efficiency = min(100.0, avg_tps)

        # Overall: weighted average
        overall = (
            avg_accuracy * 0.40
            + avg_quality * 0.30
            + consistency * 0.15
            + efficiency * 0.15
        )

        return ModelScore(
            model=model,
            overall=overall,
            accuracy=avg_accuracy,
            code_quality=avg_quality,
            consistency=consistency,
            efficiency=efficiency,
            tasks_completed=len(results),
        )

    def save_report(self, report: BenchmarkReport) -> Path:
        """Save benchmark report to JSON file.

        Args:
            report: BenchmarkReport to save

        Returns:
            Path to saved report file.
        """
        BENCHMARK_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename from timestamp
        ts = datetime.fromisoformat(report.timestamp)
        filename = f"benchmark_{ts.strftime('%Y%m%dT%H%M%SZ')}.json"
        filepath = BENCHMARK_DATA_DIR / filename

        # Convert report to dict
        report_dict = {
            "timestamp": report.timestamp,
            "models_tested": list(report.models_tested),
            "task_count": report.task_count,
            "model_scores": [
                {
                    "model": s.model,
                    "overall": s.overall,
                    "accuracy": s.accuracy,
                    "code_quality": s.code_quality,
                    "consistency": s.consistency,
                    "efficiency": s.efficiency,
                    "tasks_completed": s.tasks_completed,
                }
                for s in report.model_scores
            ],
            "task_results": [
                {
                    "task_name": r.task_name,
                    "model": r.model,
                    "accuracy": r.accuracy,
                    "code_quality": r.code_quality,
                    "latency_ms": r.latency_ms,
                    "tokens_per_second": r.tokens_per_second,
                    "runs": r.runs,
                }
                for r in report.task_results
            ],
            "best_model_per_task": report.best_model_per_task,
            "overall_rankings": list(report.overall_rankings),
        }

        filepath.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
        return filepath

    def load_history(self, limit: int = 10) -> list[BenchmarkReport]:
        """Load recent benchmark reports from disk.

        Args:
            limit: Maximum number of reports to load (default: 10)

        Returns:
            List of BenchmarkReport objects sorted by timestamp descending.
        """
        if not BENCHMARK_DATA_DIR.exists():
            return []

        report_files = sorted(
            BENCHMARK_DATA_DIR.glob("benchmark_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        reports: list[BenchmarkReport] = []
        for filepath in report_files[:limit]:
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))

                model_scores = tuple(
                    ModelScore(
                        model=s["model"],
                        overall=s["overall"],
                        accuracy=s["accuracy"],
                        code_quality=s["code_quality"],
                        consistency=s["consistency"],
                        efficiency=s["efficiency"],
                        tasks_completed=s["tasks_completed"],
                    )
                    for s in data["model_scores"]
                )

                task_results = tuple(
                    TaskResult(
                        task_name=r["task_name"],
                        model=r["model"],
                        accuracy=r["accuracy"],
                        code_quality=r["code_quality"],
                        latency_ms=r["latency_ms"],
                        tokens_per_second=r["tokens_per_second"],
                        runs=r["runs"],
                    )
                    for r in data["task_results"]
                )

                report = BenchmarkReport(
                    timestamp=data["timestamp"],
                    models_tested=tuple(data["models_tested"]),
                    task_count=data["task_count"],
                    model_scores=model_scores,
                    task_results=task_results,
                    best_model_per_task=data["best_model_per_task"],
                    overall_rankings=tuple(data["overall_rankings"]),
                )
                reports.append(report)
            except Exception:
                continue

        return reports

    def get_default_tasks(self) -> list[BenchmarkTask]:
        """Get standard benchmark tasks for model evaluation.

        Returns:
            List of 5 BenchmarkTask objects covering all categories.
        """
        return [
            BenchmarkTask(
                name="code_gen_fibonacci",
                category="code_generation",
                prompt="Write a Python function to calculate the nth Fibonacci number using memoization.",
                expected_output="def fibonacci(n: int, memo: dict = None) -> int:\n    if memo is None:\n        memo = {}\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)\n    return memo[n]",
                max_score=100.0,
            ),
            BenchmarkTask(
                name="code_review_security",
                category="code_review",
                prompt="Review this code for security issues: def login(username, password): query = f\"SELECT * FROM users WHERE username='{username}' AND password='{password}'\"",
                expected_output="SQL injection vulnerability detected. Never use string interpolation for SQL queries. Use parameterized queries instead. The f-string allows arbitrary SQL code injection through username or password fields. Replace with cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))",
                max_score=100.0,
            ),
            BenchmarkTask(
                name="refactor_dry",
                category="refactoring",
                prompt="Refactor this code to follow DRY principle: def calc_area_rect(w, h): return w * h\ndef calc_area_square(s): return s * s\ndef calc_area_triangle(b, h): return 0.5 * b * h",
                expected_output="from enum import Enum\n\nclass ShapeType(Enum):\n    RECTANGLE = 'rectangle'\n    SQUARE = 'square'\n    TRIANGLE = 'triangle'\n\ndef calculate_area(shape_type: ShapeType, **dimensions: float) -> float:\n    if shape_type == ShapeType.RECTANGLE:\n        return dimensions['width'] * dimensions['height']\n    elif shape_type == ShapeType.SQUARE:\n        return dimensions['side'] ** 2\n    elif shape_type == ShapeType.TRIANGLE:\n        return 0.5 * dimensions['base'] * dimensions['height']\n    raise ValueError(f'Unknown shape: {shape_type}')",
                max_score=100.0,
            ),
            BenchmarkTask(
                name="docs_api_endpoint",
                category="documentation",
                prompt="Write API documentation for this function: def create_user(username: str, email: str, role: str = 'user') -> dict:",
                expected_output="Create a new user account.\n\nArgs:\n    username: Unique username for the account (alphanumeric, 3-20 chars)\n    email: User's email address (must be valid format)\n    role: User role (default: 'user', options: 'user', 'admin', 'moderator')\n\nReturns:\n    dict: User object with keys: id, username, email, role, created_at\n\nRaises:\n    ValueError: If username or email format is invalid\n    ConflictError: If username or email already exists\n\nExample:\n    >>> create_user('alice', 'alice@example.com')\n    {'id': 1, 'username': 'alice', 'email': 'alice@example.com', 'role': 'user', 'created_at': '2026-04-05T12:00:00Z'}",
                max_score=100.0,
            ),
            BenchmarkTask(
                name="debug_index_error",
                category="debugging",
                prompt="Debug this code: def get_last_item(items): return items[len(items)]\nWhat's the bug and how to fix it?",
                expected_output="Index out of bounds error. Array indices are zero-based, so the last element is at index len(items)-1, not len(items). Fix: return items[len(items)-1] or use items[-1] for Pythonic access to last element. Also add empty list check: if not items: raise ValueError('Cannot get last item from empty list')",
                max_score=100.0,
            ),
        ]
