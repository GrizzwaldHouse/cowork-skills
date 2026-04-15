# test_penetration_tests.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Unit tests for PenetrationTestSuite to verify security boundary enforcement

"""
Unit tests for the Penetration Test Suite.

Validates that the PenetrationTestSuite correctly identifies security
vulnerabilities and that all attack vectors are properly blocked by
the AISafetyGuard and ValidationEngine.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.testing.penetration_tests import (
    PenetrationTestSuite,
    PenTestReport,
    PenTestResult,
    PenTestVector,
)
from scripts.ai_safety_guard import AISafetyGuard
from scripts.validation_engine import ValidationEngine
from scripts.agent_event_bus import EventBus
from scripts.agent_events import SkillExtractedEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def suite() -> PenetrationTestSuite:
    """Create a fresh PenetrationTestSuite for each test."""
    return PenetrationTestSuite()


@pytest.fixture
def safety_guard() -> AISafetyGuard:
    """Create a fresh AISafetyGuard for standalone tests."""
    return AISafetyGuard()


@pytest.fixture
def event_bus() -> EventBus:
    """Create a fresh EventBus for standalone tests."""
    return EventBus()


# ---------------------------------------------------------------------------
# Path traversal tests
# ---------------------------------------------------------------------------

class TestPathTraversalBlocked:
    """Test that path traversal attack vectors are blocked."""

    def test_path_traversal_blocked(self, suite: PenetrationTestSuite) -> None:
        """Test all path traversal vectors are blocked."""
        results = suite.test_path_traversal()

        assert len(results) >= 4  # At least 4 path traversal vectors
        for result in results:
            assert result.passed, (
                f"Path traversal vector '{result.vector_name}' failed: {result.detail}"
            )
            assert result.category == "path_traversal"
            assert result.duration_seconds >= 0.0


# ---------------------------------------------------------------------------
# Injection vector tests
# ---------------------------------------------------------------------------

class TestInjectionBlocked:
    """Test that injection attack vectors are blocked."""

    def test_sql_injection_blocked(self, suite: PenetrationTestSuite) -> None:
        """Test SQL injection is detected and blocked."""
        results = suite.test_injection_vectors()

        sql_results = [r for r in results if r.vector_name == "sql_injection"]
        assert len(sql_results) == 1
        assert sql_results[0].passed, (
            f"SQL injection not blocked: {sql_results[0].detail}"
        )

    def test_command_injection_blocked(self, suite: PenetrationTestSuite) -> None:
        """Test command injection is detected and blocked."""
        results = suite.test_injection_vectors()

        cmd_results = [r for r in results if "command_injection" in r.vector_name]
        # At least one command injection vector should exist
        assert len(cmd_results) >= 1

        # Check the rm -rf variant specifically
        rm_results = [r for r in cmd_results if "rm" in r.vector_name]
        if rm_results:
            assert rm_results[0].passed, (
                f"Command injection (rm -rf) not blocked: {rm_results[0].detail}"
            )

    def test_template_injection_blocked(self, suite: PenetrationTestSuite) -> None:
        """Test template injection vectors are handled correctly."""
        results = suite.test_injection_vectors()

        template_results = [r for r in results if "template_injection" in r.vector_name]
        # Template injection patterns not in current blocked patterns, so they pass if NOT blocked
        for result in template_results:
            assert result.passed, (
                f"Template injection test failed: {result.vector_name} - {result.detail}"
            )

    def test_python_eval_blocked(self, suite: PenetrationTestSuite) -> None:
        """Test Python eval/exec patterns are blocked."""
        results = suite.test_injection_vectors()

        eval_results = [r for r in results if "eval" in r.vector_name or "exec" in r.vector_name]
        assert len(eval_results) >= 2  # At least eval and exec

        for result in eval_results:
            assert result.passed, (
                f"Python eval/exec not blocked: {result.vector_name} - {result.detail}"
            )

    def test_safety_guard_blocks_import(self, safety_guard: AISafetyGuard) -> None:
        """Test __import__ pattern is caught by safety guard."""
        alert = safety_guard.check_content("__import__(\"os\").system(\"calc\")")
        assert alert is not None
        assert alert.violation.value == "unsafe_exec"


# ---------------------------------------------------------------------------
# Credential detection tests
# ---------------------------------------------------------------------------

class TestCredentialDetection:
    """Test credential pattern detection."""

    def test_credential_detection(self, suite: PenetrationTestSuite) -> None:
        """Test secrets are flagged in validation."""
        results = suite.test_credential_scanning()

        assert len(results) >= 3  # password, api_key, AWS secret

        for result in results:
            assert result.passed, (
                f"Credential detection failed for {result.vector_name}: {result.detail}"
            )
            assert result.category == "credential_scanning"


# ---------------------------------------------------------------------------
# Event bus poisoning tests
# ---------------------------------------------------------------------------

class TestEventBusPoisoning:
    """Test event bus resilience to malformed events."""

    def test_event_bus_survives_poisoning(self, suite: PenetrationTestSuite) -> None:
        """Test no crash on malformed events."""
        results = suite.test_event_bus_poisoning()

        assert len(results) >= 3  # None, long string, special chars

        for result in results:
            assert result.passed, (
                f"Event bus poisoning test failed: {result.vector_name} - {result.detail}"
            )

    def test_event_bus_long_strings(self, event_bus: EventBus) -> None:
        """Test EventBus handles 100KB strings gracefully."""
        long_string = "X" * 100_000

        # This should not crash
        event = SkillExtractedEvent(
            skill_id=long_string,
            skill_name=long_string,
        )

        try:
            event_bus.publish(event)
            audit_log = event_bus.get_audit_log(limit=1)
            assert len(audit_log) > 0
        except Exception as exc:
            pytest.fail(f"EventBus crashed on long string: {exc!r}")


# ---------------------------------------------------------------------------
# Sandbox escape tests
# ---------------------------------------------------------------------------

class TestSandboxEscape:
    """Test file operation confinement."""

    def test_sandbox_escape_prevented(self, suite: PenetrationTestSuite) -> None:
        """Test writes outside sandbox fail."""
        results = suite.test_sandbox_escape()

        assert len(results) >= 2  # At least 2 escape attempts

        for result in results:
            assert result.passed, (
                f"Sandbox escape not prevented: {result.vector_name} - {result.detail}"
            )


# ---------------------------------------------------------------------------
# Privilege escalation tests
# ---------------------------------------------------------------------------

class TestPrivilegeEscalation:
    """Test core skill protection."""

    def test_core_skill_protected(self, suite: PenetrationTestSuite) -> None:
        """Test universal-coding-standards cannot be overwritten."""
        results = suite.test_privilege_escalation()

        # Find the universal-coding-standards result
        ucs_results = [r for r in results if "universal_coding_standards" in r.vector_name]
        assert len(ucs_results) == 1
        assert ucs_results[0].passed, (
            f"Core skill not protected: {ucs_results[0].detail}"
        )

    def test_enterprise_secure_ai_protected(self, safety_guard: AISafetyGuard) -> None:
        """Test enterprise-secure-ai-engineering is protected."""
        base_dir = Path("C:/ClaudeSkills")
        path = base_dir / "skills" / "enterprise-secure-ai-engineering" / "rules.md"

        alert = safety_guard.check_overwrite(path)
        assert alert is not None
        assert alert.violation.value == "core_skill_overwrite"
        assert alert.severity == "CRITICAL"


# ---------------------------------------------------------------------------
# Full report tests
# ---------------------------------------------------------------------------

class TestFullReport:
    """Test complete penetration test report generation."""

    def test_full_report_structure(self, suite: PenetrationTestSuite) -> None:
        """Test run_all() produces valid PenTestReport."""
        report = suite.run_all()

        assert isinstance(report, PenTestReport)
        assert report.total_vectors > 0
        assert report.passed >= 0
        assert report.failed >= 0
        assert report.passed + report.failed == report.total_vectors
        assert len(report.results) == report.total_vectors
        assert report.timestamp != ""

        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        try:
            datetime.fromisoformat(report.timestamp)
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {report.timestamp}")

    def test_full_report_all_pass(self, suite: PenetrationTestSuite) -> None:
        """Test that all penetration test vectors pass (security is enforced)."""
        report = suite.run_all()

        # All tests should pass if security is working
        failed_tests = [r for r in report.results if not r.passed]

        if failed_tests:
            failure_msg = "The following penetration tests failed:\n"
            for result in failed_tests:
                failure_msg += f"  - {result.vector_name} ({result.category}): {result.detail}\n"
            pytest.fail(failure_msg)

        assert report.failed == 0, (
            f"{report.failed} penetration tests failed out of {report.total_vectors}"
        )


# ---------------------------------------------------------------------------
# Data structure tests
# ---------------------------------------------------------------------------

class TestDataStructures:
    """Test penetration test data structures."""

    def test_pentest_vector_frozen(self) -> None:
        """Test PenTestVector is immutable."""
        vector = PenTestVector(
            name="test",
            category="test",
            payload="payload",
            expected_blocked=True,
        )

        with pytest.raises(AttributeError):
            vector.name = "changed"  # type: ignore[misc]

    def test_pentest_result_frozen(self) -> None:
        """Test PenTestResult is immutable."""
        result = PenTestResult(
            vector_name="test",
            category="test",
            passed=True,
            detail="detail",
            duration_seconds=0.1,
        )

        with pytest.raises(AttributeError):
            result.passed = False  # type: ignore[misc]

    def test_pentest_report_frozen(self) -> None:
        """Test PenTestReport is immutable."""
        report = PenTestReport(
            total_vectors=10,
            passed=9,
            failed=1,
            results=(),
            timestamp="2026-04-05T00:00:00+00:00",
        )

        with pytest.raises(AttributeError):
            report.passed = 10  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
