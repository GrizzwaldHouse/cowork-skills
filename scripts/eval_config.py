# eval_config.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Shared constants, schema validation, and configuration for the skill eval/self-improvement system

"""
Configuration and schema validation for the skill evaluation system.

Provides centralized constants (no magic numbers), JSON schema validation
for eval.json files, and path resolution utilities. All other eval modules
import their configuration from here.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("claude-skills.eval")

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
SKILLS_DIR = BASE_DIR / "skills"
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"

# ---------------------------------------------------------------------------
# Eval system constants — no magic numbers
# ---------------------------------------------------------------------------
PROPOSAL_TIMEOUT_SECONDS = 180
MAX_FAILED_ASSERTIONS_IN_PROMPT = 10
MAX_PREVIOUS_FAILURES_IN_PROMPT = 5

# Claude CLI resolution — search common install locations on Windows
CLAUDE_CLI_CANDIDATES = [
    "claude",  # If already on PATH
    str(Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"),
    str(Path.home() / "AppData" / "Roaming" / "npm" / "claude"),
    str(Path.home() / ".npm-global" / "bin" / "claude"),
]

# Neutral working directory for subprocess calls — prevents loading project CLAUDE.md.
# Uses system temp dir which has no .claude/ folder or CLAUDE.md.
import tempfile as _tempfile
NEUTRAL_CWD = _tempfile.gettempdir()

EVAL_DIR_NAME = "eval"
EVAL_FILE_NAME = "eval.json"
HISTORY_FILE_NAME = "history.json"
RESULTS_DIR_NAME = "results"

# Timeout configuration (seconds)
EVAL_TIMEOUT_SECONDS = 120
GRADER_TIMEOUT_SECONDS = 30

# Self-improvement loop limits
MAX_ITERATIONS_DEFAULT = 50
MAX_CONSECUTIVE_FAILURES = 5
TARGET_SCORE_DEFAULT = 1.0

# Git branch naming
IMPROVEMENT_BRANCH_PREFIX = "skill-improve"

# Required fields in eval.json
REQUIRED_EVAL_FIELDS = {"skill_name", "version", "test_cases"}
REQUIRED_TEST_CASE_FIELDS = {"id", "prompt", "assertions"}
REQUIRED_ASSERTION_FIELDS = {"id", "check", "category"}

# Valid assertion categories
VALID_CATEGORIES = {"structure", "content", "quality", "format", "compliance"}


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def resolve_claude_cli() -> str:
    """
    Find the claude CLI executable.

    Checks PATH first, then common install locations on Windows.

    Returns:
        Path to the claude executable.

    Raises:
        FileNotFoundError: If claude CLI cannot be found.
    """
    import shutil

    for candidate in CLAUDE_CLI_CANDIDATES:
        if candidate == "claude":
            found = shutil.which("claude")
            if found:
                return found
        elif Path(candidate).exists():
            return candidate

    raise FileNotFoundError(
        "claude CLI not found. Checked PATH and common locations: "
        + ", ".join(CLAUDE_CLI_CANDIDATES)
    )


class EvalConfigError(Exception):
    """Raised when eval.json fails schema validation."""


def validate_eval_config(data: dict[str, Any]) -> list[str]:
    """
    Validate an eval.json dictionary against the expected schema.

    Args:
        data: Parsed eval.json contents.

    Returns:
        List of validation error messages. Empty list means valid.
    """
    errors: list[str] = []

    # Top-level required fields
    missing_top = REQUIRED_EVAL_FIELDS - set(data.keys())
    if missing_top:
        errors.append(f"Missing top-level fields: {missing_top}")
        return errors

    if not isinstance(data["test_cases"], list) or len(data["test_cases"]) == 0:
        errors.append("test_cases must be a non-empty list")
        return errors

    seen_case_ids: set[int] = set()
    for idx, case in enumerate(data["test_cases"]):
        prefix = f"test_cases[{idx}]"

        missing_case = REQUIRED_TEST_CASE_FIELDS - set(case.keys())
        if missing_case:
            errors.append(f"{prefix}: missing fields {missing_case}")
            continue

        case_id = case["id"]
        if case_id in seen_case_ids:
            errors.append(f"{prefix}: duplicate id {case_id}")
        seen_case_ids.add(case_id)

        if not isinstance(case["assertions"], list) or len(case["assertions"]) == 0:
            errors.append(f"{prefix}: assertions must be a non-empty list")
            continue

        seen_assertion_ids: set[str] = set()
        for aidx, assertion in enumerate(case["assertions"]):
            a_prefix = f"{prefix}.assertions[{aidx}]"

            missing_a = REQUIRED_ASSERTION_FIELDS - set(assertion.keys())
            if missing_a:
                errors.append(f"{a_prefix}: missing fields {missing_a}")
                continue

            if assertion["id"] in seen_assertion_ids:
                errors.append(f"{a_prefix}: duplicate assertion id '{assertion['id']}'")
            seen_assertion_ids.add(assertion["id"])

            if assertion["category"] not in VALID_CATEGORIES:
                errors.append(
                    f"{a_prefix}: invalid category '{assertion['category']}', "
                    f"must be one of {VALID_CATEGORIES}"
                )

    return errors


def load_eval_json(skill_name: str) -> dict[str, Any]:
    """
    Load and validate eval.json for a given skill.

    Args:
        skill_name: Name of the skill directory under skills/.

    Returns:
        Validated eval configuration dictionary.

    Raises:
        EvalConfigError: If the file is missing, malformed, or fails validation.
        FileNotFoundError: If the eval.json file does not exist.
    """
    eval_path = SKILLS_DIR / skill_name / EVAL_DIR_NAME / EVAL_FILE_NAME

    if not eval_path.exists():
        raise FileNotFoundError(
            f"No eval.json found at {eval_path}. "
            f"Create {EVAL_DIR_NAME}/{EVAL_FILE_NAME} in the skill directory first."
        )

    try:
        with eval_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise EvalConfigError(f"Invalid JSON in {eval_path}: {exc}") from exc

    errors = validate_eval_config(data)
    if errors:
        error_list = "\n  - ".join(errors)
        raise EvalConfigError(
            f"eval.json validation failed for '{skill_name}':\n  - {error_list}"
        )

    logger.info(
        "Loaded eval config for '%s': %d test cases, %d total assertions",
        skill_name,
        len(data["test_cases"]),
        sum(len(tc["assertions"]) for tc in data["test_cases"]),
    )

    return data


def get_results_dir(skill_name: str) -> Path:
    """
    Return the results directory for a skill, creating it if needed.

    Args:
        skill_name: Name of the skill directory.

    Returns:
        Path to the results directory.
    """
    results_dir = SKILLS_DIR / skill_name / EVAL_DIR_NAME / RESULTS_DIR_NAME
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def get_history_path(skill_name: str) -> Path:
    """
    Return the path to history.json for a skill's eval directory.

    Args:
        skill_name: Name of the skill directory.

    Returns:
        Path to history.json.
    """
    return SKILLS_DIR / skill_name / EVAL_DIR_NAME / HISTORY_FILE_NAME


# ---------------------------------------------------------------------------
# Supervisor audit constants
# ---------------------------------------------------------------------------
SUPERVISOR_PASSING_SCORE = 70
SUPERVISOR_MODEL = "haiku"
SUPERVISOR_TIMEOUT_SECONDS = 60
AUDIT_LOG_NAME = "audit_log.json"
RUBRIC_WEIGHTS: dict[str, int] = {
    "comment_code_alignment": 25,
    "architecture_compliance": 30,
    "build_cleanliness": 20,
    "defensive_programming": 15,
    "documentation_quality": 10,
}

# ---------------------------------------------------------------------------
# Self-healing loop constants
# ---------------------------------------------------------------------------
MAX_HEALING_RETRIES = 3
HEALING_LOG_NAME = "healing_log.json"
TIMEOUT_ESCALATION_FACTOR = 1.5
MAX_ESCALATED_TIMEOUT_SECONDS = 600


def get_audit_log_path(skill_name: str) -> Path:
    """
    Return the path to the supervisor audit log for a skill.

    Args:
        skill_name: Name of the skill directory.

    Returns:
        Path to audit_log.json inside the skill's eval directory.
    """
    audit_dir = SKILLS_DIR / skill_name / EVAL_DIR_NAME
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir / AUDIT_LOG_NAME


def get_healing_log_path(skill_name: str) -> Path:
    """
    Return the path to the healing log for a skill.

    Args:
        skill_name: Name of the skill directory.

    Returns:
        Path to healing_log.json inside the skill's eval directory.
    """
    healing_dir = SKILLS_DIR / skill_name / EVAL_DIR_NAME
    healing_dir.mkdir(parents=True, exist_ok=True)
    return healing_dir / HEALING_LOG_NAME
