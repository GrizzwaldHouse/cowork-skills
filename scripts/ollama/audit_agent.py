# audit_agent.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: AI model audit agent for evaluating Ollama model outputs and performance

"""
Audit agent for Ollama model evaluation.

Provides dataclasses and analysis tools for classifying errors, tracking model
performance, and generating audit reports. Used by training_adjuster.py to
identify improvement opportunities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ErrorCategory(Enum):
    """Classification of error types in AI-generated code."""

    LOGIC_ERROR = "logic_error"
    STANDARDS_VIOLATION = "standards_violation"
    POOR_STRUCTURE = "poor_structure"
    INCORRECT_OUTPUT = "incorrect_output"
    TIMEOUT = "timeout"
    RUNTIME_ERROR = "runtime_error"


# ---------------------------------------------------------------------------
# Dataclasses (frozen for immutability)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ErrorClassification:
    """Single error instance with category and description."""

    category: ErrorCategory
    description: str
    severity: str  # "critical", "high", "medium", "low"
    line_number: int | None = None


@dataclass(frozen=True)
class AuditReport:
    """Complete audit report for a model evaluation session."""

    model: str
    task_type: str
    accuracy: float  # 0.0 to 1.0
    code_quality: float  # 0.0 to 1.0
    consistency: float  # 0.0 to 1.0
    efficiency: float  # 0.0 to 1.0
    error_classifications: tuple[ErrorClassification, ...]
    total_tests: int
    passed_tests: int
    timestamp: str
