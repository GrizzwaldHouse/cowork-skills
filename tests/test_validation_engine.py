# test_validation_engine.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Unit tests for ValidationEngine architecture, security, quality, and dedup checks

"""
Unit tests for the Validation Engine.

Covers approval/rejection logic, architecture checks (polling, globals),
security checks (blocked patterns, credentials, paths), quality checks
(content length, constraints, confidence), and duplicate detection.
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Ensure scripts directory is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from validation_engine import ValidationEngine, ValidationReport, ValidationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ValidationEngine:
    """Create a ValidationEngine with skill store in a temp directory."""
    monkeypatch.setattr("validation_engine.BASE_DIR", tmp_path)
    (tmp_path / "data" / "quad_skills").mkdir(parents=True)
    config: dict = {
        "extraction": {
            "auto_approve_threshold": 0.7,
            "dedup_similarity_threshold": 0.85,
        },
        "safety": {
            "blocked_patterns": [
                "os.system", "subprocess", "eval", "exec",
                "__import__", "rm -rf", "format c:",
            ],
            "core_skills": [],
        },
    }
    return ValidationEngine(config)


def _make_skill(
    *,
    intent: str = "A valid test skill for unit testing purposes",
    execution_logic: str = (
        "This is a well-structured execution logic block that describes "
        "the step-by-step process for accomplishing the task with enough "
        "content to pass all quality checks and validation."
    ),
    constraints: list[str] | None = None,
    failure_modes: list[str] | None = None,
    confidence_score: float = 0.8,
    security_classification: str = "SAFE",
    **overrides: object,
) -> dict:
    """Create a minimal valid skill dict for testing."""
    skill: dict = {
        "skill_id": str(uuid.uuid4()),
        "name": "test-skill",
        "intent": intent,
        "context": "Test context for validation",
        "input_pattern": "Test trigger",
        "execution_logic": execution_logic,
        "constraints": constraints if constraints is not None else ["Must validate input"],
        "expected_output": "Successful result",
        "failure_modes": failure_modes if failure_modes is not None else ["Timeout possible"],
        "security_classification": security_classification,
        "source_session": "test-session",
        "source_project": "test-project",
        "confidence_score": confidence_score,
        "reuse_frequency": 1,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }
    skill.update(overrides)
    return skill


# ---------------------------------------------------------------------------
# Approval / rejection tests
# ---------------------------------------------------------------------------
class TestValidationResult:
    """Test overall validation result determination."""

    def test_valid_skill_approved(self, engine: ValidationEngine) -> None:
        """Test a well-formed skill with high confidence is APPROVED."""
        skill = _make_skill(confidence_score=0.8)
        report = engine.validate(skill)
        assert report.result == ValidationResult.APPROVED

    def test_skill_with_eval_rejected(self, engine: ValidationEngine) -> None:
        """Test a skill containing eval() is REJECTED."""
        skill = _make_skill(
            execution_logic="result = eval(user_input) to compute the expression dynamically"
        )
        report = engine.validate(skill)
        assert report.result == ValidationResult.REJECTED

    def test_skill_with_exec_rejected(self, engine: ValidationEngine) -> None:
        """Test a skill containing exec is REJECTED."""
        skill = _make_skill(
            execution_logic="exec(code_string) runs arbitrary Python code for processing"
        )
        report = engine.validate(skill)
        assert report.result == ValidationResult.REJECTED

    def test_skill_with_os_system_rejected(self, engine: ValidationEngine) -> None:
        """Test a skill containing os.system is REJECTED."""
        skill = _make_skill(
            execution_logic="Use os.system to run the shell command for cleanup"
        )
        report = engine.validate(skill)
        assert report.result == ValidationResult.REJECTED

    def test_skill_with_low_confidence_needs_review(
        self, engine: ValidationEngine
    ) -> None:
        """Test a skill with low confidence gets NEEDS_REVIEW."""
        skill = _make_skill(confidence_score=0.5)
        report = engine.validate(skill)
        # Confidence 0.5 < 0.7 threshold, so not auto-approved
        assert report.result == ValidationResult.NEEDS_REVIEW

    def test_auto_approve_threshold_respected(self, engine: ValidationEngine) -> None:
        """Test auto-approve only triggers at or above the threshold."""
        below_threshold = _make_skill(confidence_score=0.69)
        report_below = engine.validate(below_threshold)
        assert report_below.result != ValidationResult.APPROVED

        at_threshold = _make_skill(confidence_score=0.7)
        report_at = engine.validate(at_threshold)
        assert report_at.result == ValidationResult.APPROVED


# ---------------------------------------------------------------------------
# Architecture check tests
# ---------------------------------------------------------------------------
class TestArchitectureChecks:
    """Test architecture validation rules."""

    def test_polling_pattern_deduction(self, engine: ValidationEngine) -> None:
        """Test while True polling pattern reduces architecture score."""
        skill = _make_skill(
            execution_logic="Run a loop with while True to continuously check for updates "
                "and process them as they arrive in the queue."
        )
        score, violations = engine.check_architecture(skill)
        assert score <= 0.8
        assert any("polling" in v.lower() for v in violations)

    def test_time_sleep_deduction(self, engine: ValidationEngine) -> None:
        """Test time.sleep polling pattern reduces architecture score."""
        skill = _make_skill(
            execution_logic="Wait using time.sleep(5) between each iteration to avoid "
                "overwhelming the API with requests."
        )
        score, violations = engine.check_architecture(skill)
        assert score <= 0.8
        assert any("polling" in v.lower() for v in violations)

    def test_global_variable_deduction(self, engine: ValidationEngine) -> None:
        """Test global variable usage reduces architecture score."""
        skill = _make_skill(
            execution_logic="Use global counter to track the total number of processed items "
                "across all function calls in the module."
        )
        score, violations = engine.check_architecture(skill)
        assert score <= 0.8
        assert any("global" in v.lower() for v in violations)

    def test_monolithic_block_deduction(self, engine: ValidationEngine) -> None:
        """Test monolithic block without separation reduces score."""
        # Create a long block with no ## headers and no def statements
        long_block = "Process the data by reading each record. " * 30  # > 500 chars
        skill = _make_skill(execution_logic=long_block)
        score, violations = engine.check_architecture(skill)
        assert score <= 0.9
        assert any("monolithic" in v.lower() for v in violations)

    def test_clean_architecture_full_score(self, engine: ValidationEngine) -> None:
        """Test clean code gets full architecture score."""
        skill = _make_skill(
            execution_logic="Handle event with a short focused function."
        )
        score, violations = engine.check_architecture(skill)
        assert score == 1.0
        assert violations == []


# ---------------------------------------------------------------------------
# Security check tests
# ---------------------------------------------------------------------------
class TestSecurityChecks:
    """Test security validation rules."""

    def test_blocked_pattern_subprocess(self, engine: ValidationEngine) -> None:
        """Test subprocess pattern is caught."""
        skill = _make_skill(
            execution_logic="Use subprocess to run the build command on the server."
        )
        score, violations = engine.check_security(skill)
        assert score <= 0.5
        assert any("subprocess" in v for v in violations)

    def test_blocked_pattern_rm_rf(self, engine: ValidationEngine) -> None:
        """Test rm -rf pattern is caught."""
        skill = _make_skill(
            execution_logic="Clean up with rm -rf /tmp/build to remove temporary files."
        )
        score, violations = engine.check_security(skill)
        assert score <= 0.5
        assert any("rm -rf" in v for v in violations)

    def test_hardcoded_external_path(self, engine: ValidationEngine) -> None:
        """Test hardcoded paths outside allowed directories are flagged."""
        skill = _make_skill(
            execution_logic='Read config from "D:\\Projects\\secret\\config.ini" for setup.'
        )
        score, violations = engine.check_security(skill)
        assert score < 1.0
        assert any("hardcoded path" in v.lower() for v in violations)

    def test_allowed_path_no_deduction(self, engine: ValidationEngine) -> None:
        """Test paths within C:\\ClaudeSkills are not flagged."""
        skill = _make_skill(
            execution_logic="Read from C:/ClaudeSkills/data/config.json for settings."
        )
        score, violations = engine.check_security(skill)
        # Only check that no path-related violations exist
        assert not any("hardcoded path" in v.lower() for v in violations)

    def test_credential_pattern_detected(self, engine: ValidationEngine) -> None:
        """Test hardcoded credential patterns are flagged."""
        skill = _make_skill(
            execution_logic='Connect with password="secret123" to the database.'
        )
        score, violations = engine.check_security(skill)
        assert score < 1.0
        assert any("credential" in v.lower() for v in violations)

    def test_critical_violation_on_low_score(self, engine: ValidationEngine) -> None:
        """Test CRITICAL prefix is added when security score drops below 0.5."""
        skill = _make_skill(
            execution_logic="Use eval(data) and exec(code) to dynamically process input."
        )
        score, violations = engine.check_security(skill)
        assert score < 0.5
        assert any("CRITICAL" in v for v in violations)

    def test_clean_security_full_score(self, engine: ValidationEngine) -> None:
        """Test clean content gets full security score."""
        skill = _make_skill(
            execution_logic="Parse JSON data and return structured results."
        )
        score, violations = engine.check_security(skill)
        assert score == 1.0
        assert violations == []


# ---------------------------------------------------------------------------
# Quality check tests
# ---------------------------------------------------------------------------
class TestQualityChecks:
    """Test quality validation rules."""

    def test_short_execution_logic_deduction(self, engine: ValidationEngine) -> None:
        """Test short execution_logic reduces quality score."""
        skill = _make_skill(execution_logic="Do it.")
        score, violations = engine.check_quality(skill)
        assert score <= 0.7
        assert any("too short" in v.lower() for v in violations)

    def test_empty_constraints_deduction(self, engine: ValidationEngine) -> None:
        """Test empty constraints reduce quality score."""
        skill = _make_skill(constraints=[])
        score, violations = engine.check_quality(skill)
        assert score <= 0.8
        assert any("no constraints" in v.lower() for v in violations)

    def test_empty_failure_modes_deduction(self, engine: ValidationEngine) -> None:
        """Test empty failure_modes reduce quality score."""
        skill = _make_skill(failure_modes=[])
        score, violations = engine.check_quality(skill)
        assert score <= 0.8
        assert any("no failure_modes" in v.lower() for v in violations)

    def test_low_confidence_deduction(self, engine: ValidationEngine) -> None:
        """Test confidence < 0.3 reduces quality score."""
        skill = _make_skill(confidence_score=0.2)
        score, violations = engine.check_quality(skill)
        assert score <= 0.8
        assert any("low confidence" in v.lower() for v in violations)

    def test_short_intent_deduction(self, engine: ValidationEngine) -> None:
        """Test short intent reduces quality score."""
        skill = _make_skill(intent="Do it")
        score, violations = engine.check_quality(skill)
        assert score <= 0.9
        assert any("intent too short" in v.lower() for v in violations)

    def test_full_quality_score(self, engine: ValidationEngine) -> None:
        """Test well-formed skill gets full quality score."""
        skill = _make_skill()
        score, violations = engine.check_quality(skill)
        assert score == 1.0
        assert violations == []


# ---------------------------------------------------------------------------
# Duplicate detection tests
# ---------------------------------------------------------------------------
class TestDuplicateDetection:
    """Test duplicate detection against existing skills."""

    def test_detects_duplicate(self, engine: ValidationEngine, tmp_path: Path) -> None:
        """Test duplicate is detected when existing skill matches."""
        # Save an existing skill
        existing_id = str(uuid.uuid4())
        existing = _make_skill(
            skill_id=existing_id,
            intent="Deploy Docker containers to production",
            execution_logic="Build Docker images tag and push to registry then update Kubernetes",
        )
        store = tmp_path / "data" / "quad_skills"
        with (store / f"{existing_id}.json").open("w") as fh:
            json.dump(existing, fh)

        # Check a nearly identical skill
        candidate = _make_skill(
            intent="Deploy Docker containers to production",
            execution_logic="Build Docker images tag and push to registry then update Kubernetes",
        )
        dup_id = engine.check_duplicates(candidate)
        assert dup_id == existing_id

    def test_no_false_positive(self, engine: ValidationEngine, tmp_path: Path) -> None:
        """Test different skills are not marked as duplicates."""
        existing_id = str(uuid.uuid4())
        existing = _make_skill(
            skill_id=existing_id,
            intent="Configure centralized logging with rotation",
            execution_logic="Set up Python logging with RotatingFileHandler and StreamHandler",
        )
        store = tmp_path / "data" / "quad_skills"
        with (store / f"{existing_id}.json").open("w") as fh:
            json.dump(existing, fh)

        candidate = _make_skill(
            intent="Deploy containers to production cluster",
            execution_logic="Build Docker images and push to registry update Kubernetes manifests",
        )
        dup_id = engine.check_duplicates(candidate)
        assert dup_id is None

    def test_no_duplicates_in_empty_store(self, engine: ValidationEngine) -> None:
        """Test no duplicates found with empty store."""
        skill = _make_skill()
        dup_id = engine.check_duplicates(skill)
        assert dup_id is None

    def test_duplicate_adds_violation(self, engine: ValidationEngine, tmp_path: Path) -> None:
        """Test duplicate detection produces a violation in the report."""
        existing_id = str(uuid.uuid4())
        existing = _make_skill(
            skill_id=existing_id,
            intent="Parse configuration from YAML files",
            execution_logic="Parse configuration from YAML files using PyYAML library",
        )
        store = tmp_path / "data" / "quad_skills"
        with (store / f"{existing_id}.json").open("w") as fh:
            json.dump(existing, fh)

        candidate = _make_skill(
            intent="Parse configuration from YAML files",
            execution_logic="Parse configuration from YAML files using PyYAML library",
        )
        report = engine.validate(candidate)
        assert report.duplicate_of == existing_id
        assert any("Duplicate" in v for v in report.violations)


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------
class TestEdgeCases:
    """Test edge cases."""

    def test_empty_skill(self, engine: ValidationEngine) -> None:
        """Test validation handles an empty skill dict gracefully."""
        report = engine.validate({})
        assert isinstance(report, ValidationReport)
        assert report.result in (ValidationResult.NEEDS_REVIEW, ValidationResult.REJECTED)

    def test_minimal_skill(self, engine: ValidationEngine) -> None:
        """Test validation handles a minimal skill dict."""
        skill = {"skill_id": "min-1", "intent": "Minimal"}
        report = engine.validate(skill)
        assert isinstance(report, ValidationReport)
        assert report.skill_id == "min-1"

    def test_validation_report_to_dict(self) -> None:
        """Test ValidationReport.to_dict serializes correctly."""
        report = ValidationReport(
            skill_id="test-id",
            result=ValidationResult.APPROVED,
            architecture_score=1.0,
            security_score=1.0,
            quality_score=1.0,
            duplicate_of=None,
            violations=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        data = report.to_dict()
        assert data["result"] == "approved"
        assert data["architecture_score"] == 1.0
        assert data["duplicate_of"] is None

    def test_validation_report_rejected_to_dict(self) -> None:
        """Test ValidationReport.to_dict for rejected result."""
        report = ValidationReport(
            skill_id="bad-id",
            result=ValidationResult.REJECTED,
            architecture_score=0.5,
            security_score=0.0,
            quality_score=0.3,
            duplicate_of="existing-123",
            violations=["CRITICAL: Security: blocked pattern found: eval"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        data = report.to_dict()
        assert data["result"] == "rejected"
        assert data["duplicate_of"] == "existing-123"
        assert len(data["violations"]) == 1

    def test_multiple_security_violations_stack(self, engine: ValidationEngine) -> None:
        """Test multiple blocked patterns each deduct independently."""
        skill = _make_skill(
            execution_logic=(
                "Use eval(data) then pass to os.system for processing "
                "and exec(code) for dynamic evaluation."
            ),
        )
        score, violations = engine.check_security(skill)
        # eval, os.system, exec = 3 * 0.5 = 1.5 deduction, clamped to 0.0
        assert score == 0.0
        assert len(violations) >= 3
