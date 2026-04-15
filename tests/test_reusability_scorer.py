# test_reusability_scorer.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for the 95/5 reusability scoring rubric

import unittest
import sys
sys.path.insert(0, "C:/ClaudeSkills")
from scripts.scoring.reusability_scorer import ReusabilityScorer, ReusabilityResult


class TestReusabilityScorer(unittest.TestCase):
    """Test suite for the 95/5 reusability scoring rubric."""

    def setUp(self) -> None:
        """Initialize a fresh scorer for each test."""
        self.scorer = ReusabilityScorer()

    def test_perfect_skill_scores_high(self) -> None:
        """All fields present with no violations should score >= 0.85 and pass."""
        perfect_skill = {
            "name": "generic-validator",
            "skill_name": "generic-validator",
            "intent": "Validate structured data against a schema using configurable rules",
            "execution_logic": (
                "1. Load schema from provided configuration file path\n"
                "2. Parse input data structure into memory\n"
                "3. Apply validation rules iteratively to each field\n"
                "4. Collect all validation errors with field paths and error messages\n"
                "5. Return structured validation result with pass/fail status and detailed error list\n"
                "6. Log validation summary to configured output destination"
            ),
            "context": "Works with any schema-based validation framework",
            "expected_output": "ValidationResult object with status and error details",
            "input_pattern": "User provides: schema config path, input data structure",
            "constraints": [
                "Schema must be valid JSON or YAML format",
                "Input data must be parseable",
            ],
            "failure_modes": [
                "Schema file not found",
                "Malformed input data",
                "Type mismatch in validation rules",
            ],
        }

        result = self.scorer.score(perfect_skill)

        self.assertGreaterEqual(result.score, 0.85, "Perfect skill should score >= 0.85")
        self.assertTrue(result.passed, "Perfect skill should pass")
        self.assertEqual(len(result.deductions), 0, "Perfect skill should have no deductions")

    def test_missing_constraints_deduction(self) -> None:
        """Empty constraints field should apply -0.10 deduction."""
        skill_missing_constraints = {
            "name": "test-skill",
            "execution_logic": "Perform a series of configuration-driven validation steps on the provided input data structure",
            "input_pattern": "User provides configuration file and data structure",
            "constraints": [],  # Missing
            "failure_modes": ["Config not found", "Invalid data format"],
        }

        result = self.scorer.score(skill_missing_constraints)

        self.assertIn(
            "Missing constraints field",
            " ".join(result.deductions),
            "Should detect missing constraints",
        )
        self.assertLessEqual(result.score, 0.90, "Score should be reduced by constraint deduction")

    def test_missing_failure_modes_deduction(self) -> None:
        """Empty failure_modes field should apply -0.10 deduction."""
        skill_missing_failure_modes = {
            "name": "test-skill",
            "execution_logic": "Execute a series of validation steps using schema-driven rules to verify data integrity",
            "input_pattern": "User provides schema and input data",
            "constraints": ["Schema must be valid", "Data must be parseable"],
            "failure_modes": [],  # Missing
        }

        result = self.scorer.score(skill_missing_failure_modes)

        self.assertIn(
            "Missing failure_modes field",
            " ".join(result.deductions),
            "Should detect missing failure_modes",
        )
        self.assertLessEqual(result.score, 0.90, "Score should be reduced by failure_modes deduction")

    def test_thin_execution_logic(self) -> None:
        """Execution logic < 100 chars should apply -0.15 deduction."""
        skill_thin_logic = {
            "name": "test-skill",
            "execution_logic": "Validate data",  # Only 13 chars
            "input_pattern": "User provides data to validate",
            "constraints": ["Data must exist"],
            "failure_modes": ["Data missing"],
        }

        result = self.scorer.score(skill_thin_logic)

        self.assertIn(
            "Execution logic too short",
            " ".join(result.deductions),
            "Should detect thin execution logic",
        )
        self.assertIn(
            "(-0.15)",
            " ".join(result.deductions),
            "Deduction amount should be -0.15",
        )

    def test_no_input_pattern(self) -> None:
        """Missing or short input_pattern should apply -0.10 deduction."""
        skill_no_input = {
            "name": "test-skill",
            "execution_logic": (
                "Load configuration from file, parse input data, apply validation rules, "
                "collect errors, return structured result"
            ),
            "input_pattern": "data",  # Too short (< 10 chars)
            "constraints": ["Valid schema required"],
            "failure_modes": ["Schema not found"],
        }

        result = self.scorer.score(skill_no_input)

        self.assertIn(
            "No input_pattern defined",
            " ".join(result.deductions),
            "Should detect missing input_pattern",
        )
        self.assertIn(
            "(-0.1)",
            " ".join(result.deductions),
            "Deduction amount should be -0.10",
        )

    def test_project_specific_path_deduction(self) -> None:
        """Hardcoded project-specific path should apply -0.30 deduction."""
        skill_project_path = {
            "name": "test-skill",
            "execution_logic": "Read file from D:\\MyProject\\config\\settings.json and validate it",
            "input_pattern": "User provides validation schema",
            "constraints": ["File must exist at path"],
            "failure_modes": ["File not found"],
        }

        result = self.scorer.score(skill_project_path)

        self.assertIn(
            "Project-specific path",
            " ".join(result.deductions),
            "Should detect project-specific path",
        )
        self.assertIn(
            "(-0.3)",
            " ".join(result.deductions),
            "Deduction amount should be -0.30",
        )

    def test_allowed_path_no_deduction(self) -> None:
        """Allowed paths (C:/ClaudeSkills or ~/.claude) should not trigger deduction."""
        skill_allowed_path = {
            "name": "test-skill",
            "execution_logic": (
                "Load configuration from C:/ClaudeSkills/skills/generic-validator/config.json "
                "and apply validation rules to the input data structure"
            ),
            "input_pattern": "User provides input data and validation schema",
            "constraints": ["Config file must be valid JSON"],
            "failure_modes": ["Config parse error"],
        }

        result = self.scorer.score(skill_allowed_path)

        deductions_text = " ".join(result.deductions)
        self.assertNotIn(
            "Project-specific path",
            deductions_text,
            "Should NOT deduct for allowed ClaudeSkills path",
        )

    def test_framework_locked_deduction(self) -> None:
        """Framework-locked patterns should apply -0.15 deduction."""
        skill_framework_locked = {
            "name": "test-skill",
            "execution_logic": (
                "This skill only works with react and Next.js to validate form inputs "
                "using the built-in validation hooks and state management"
            ),
            "input_pattern": "User provides form schema and validation rules",
            "constraints": ["React hooks must be available"],
            "failure_modes": ["Hooks not initialized"],
        }

        result = self.scorer.score(skill_framework_locked)

        self.assertIn(
            "Framework-locked",
            " ".join(result.deductions),
            "Should detect framework-locked pattern",
        )
        self.assertIn(
            "(-0.15)",
            " ".join(result.deductions),
            "Deduction amount should be -0.15",
        )

    def test_platform_specific_deduction(self) -> None:
        """Platform-specific commands should apply -0.10 deduction."""
        skill_platform_specific = {
            "name": "test-skill",
            "execution_logic": (
                "Use PowerShell to execute validation scripts against the provided data files "
                "and collect output into a structured report"
            ),
            "input_pattern": "User provides data files and validation script paths",
            "constraints": ["PowerShell must be installed"],
            "failure_modes": ["Script execution failed"],
        }

        result = self.scorer.score(skill_platform_specific)

        self.assertIn(
            "Platform-specific",
            " ".join(result.deductions),
            "Should detect platform-specific command",
        )
        self.assertIn(
            "(-0.1)",
            " ".join(result.deductions),
            "Deduction amount should be -0.10",
        )

    def test_multiple_deductions_stack(self) -> None:
        """Multiple violations should stack deductions and significantly reduce score."""
        skill_multiple_violations = {
            "name": "test-skill",
            "execution_logic": "Use PowerShell to read D:\\MyProject\\data.json and validate with react hooks",
            "input_pattern": "data",  # Too short
            # Missing constraints and failure_modes
        }

        result = self.scorer.score(skill_multiple_violations)

        # Should have multiple deductions
        self.assertGreater(
            len(result.deductions),
            3,
            "Should have multiple deductions for multiple violations",
        )
        self.assertLess(
            result.score,
            0.50,
            "Multiple violations should significantly reduce score",
        )
        self.assertFalse(result.passed, "Multiple violations should fail the skill")

    def test_completely_empty_skill(self) -> None:
        """Empty skill dict should trigger multiple deductions."""
        empty_skill = {}

        result = self.scorer.score(empty_skill)

        # Should have deductions for: constraints, failure_modes, thin logic, no input_pattern
        self.assertGreaterEqual(
            len(result.deductions),
            4,
            "Empty skill should trigger at least 4 deductions",
        )
        self.assertLess(
            result.score,
            0.70,
            "Empty skill should score poorly",
        )
        self.assertFalse(result.passed, "Empty skill should not pass")

    def test_config_override_project_names(self) -> None:
        """Custom project_name_indicators in config should trigger deduction."""
        config = {
            "project_name_indicators": ["MyCustomProject", "AcmeApp"],
        }
        custom_scorer = ReusabilityScorer(config=config)

        skill_with_project_name = {
            "name": "test-skill",
            "execution_logic": (
                "Load configuration for MyCustomProject and apply validation rules "
                "to ensure data integrity across all modules"
            ),
            "input_pattern": "User provides data to validate against project rules",
            "constraints": ["Project config must exist"],
            "failure_modes": ["Config not found"],
        }

        result = custom_scorer.score(skill_with_project_name)

        self.assertIn(
            "Hardcoded project name",
            " ".join(result.deductions),
            "Should detect custom project name from config",
        )
        self.assertIn(
            "(-0.2)",
            " ".join(result.deductions),
            "Deduction amount should be -0.20",
        )

    def test_score_clamped_to_zero(self) -> None:
        """Enough violations to go negative should clamp score to 0.0."""
        skill_extreme_violations = {
            "name": "test-skill",
            "execution_logic": (
                "This only works with react and uses PowerShell to access "
                "D:\\MySpecificProject\\data.json for validation"
            ),
            "input_pattern": "x",  # Too short
            # Missing constraints and failure_modes
        }

        # Add custom project names to push even lower
        config = {"project_name_indicators": ["MySpecificProject"]}
        custom_scorer = ReusabilityScorer(config=config)

        result = custom_scorer.score(skill_extreme_violations)

        self.assertGreaterEqual(
            result.score,
            0.0,
            "Score should never go below 0.0",
        )
        self.assertLessEqual(
            result.score,
            1.0,
            "Score should never exceed 1.0",
        )
        self.assertFalse(result.passed, "Extreme violations should fail")


def _print_test_summary(result: unittest.TestResult) -> None:
    """Print a formatted summary of test results."""
    print("\n" + "=" * 70)
    print("REUSABILITY SCORER TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:  {len(result.failures)}")
    print(f"Errors:    {len(result.errors)}")
    print("=" * 70)

    if result.wasSuccessful():
        print("RESULT: ALL TESTS PASSED")
    else:
        print("RESULT: SOME TESTS FAILED")
        if result.failures:
            print("\nFailed tests:")
            for test, _ in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\nTests with errors:")
            for test, _ in result.errors:
                print(f"  - {test}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Run tests with detailed output
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestReusabilityScorer)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    # Print self-test summary
    _print_test_summary(test_result)

    # Exit with appropriate code
    sys.exit(0 if test_result.wasSuccessful() else 1)
