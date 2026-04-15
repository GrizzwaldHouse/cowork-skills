# test_completeness_scorer.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for the completeness scoring module

import unittest
import sys

sys.path.insert(0, "C:/ClaudeSkills")

from scripts.scoring.completeness_scorer import (
    CompletenessScorer,
    CompletenessResult,
)


class TestCompletenessScorer(unittest.TestCase):
    """Test suite for CompletenessScorer module."""

    def setUp(self) -> None:
        """Create a default scorer instance for each test."""
        self.scorer = CompletenessScorer()

    def test_complete_skill(self) -> None:
        """Test a fully complete skill with all sections above minimums."""
        skill = {
            "name": "complete-skill",
            "intent": "This is a complete intent with enough characters to meet minimum",
            "execution_logic": (
                "This is a comprehensive execution logic section that exceeds "
                "the minimum character requirement of 200 characters. It contains "
                "detailed step-by-step instructions on how to execute the skill "
                "properly including all necessary context and examples."
            ),
            "constraints": [
                "Constraint one",
                "Constraint two",
                "Constraint three",
            ],
            "failure_modes": [
                "Failure mode one",
                "Failure mode two",
                "Failure mode three",
            ],
            "expected_output": "Expected output with sufficient detail here",
            "context": "Context section with enough detail",
            "input_pattern": "Input pattern details",
        }

        result = self.scorer.score(skill)

        self.assertGreaterEqual(result.score, 0.95)
        self.assertEqual(len(result.missing_sections), 0)
        self.assertEqual(len(result.weak_sections), 0)
        self.assertIsInstance(result.details, tuple)

    def test_completely_empty(self) -> None:
        """Test an empty skill dict returns near-zero score with all sections missing."""
        skill = {}

        result = self.scorer.score(skill)

        self.assertLessEqual(result.score, 0.05)
        self.assertEqual(len(result.missing_sections), 7)  # All 7 default sections
        self.assertIn("intent", result.missing_sections)
        self.assertIn("execution_logic", result.missing_sections)
        self.assertIn("constraints", result.missing_sections)
        self.assertIn("failure_modes", result.missing_sections)
        self.assertIn("expected_output", result.missing_sections)
        self.assertIn("context", result.missing_sections)
        self.assertIn("input_pattern", result.missing_sections)

    def test_missing_one_section(self) -> None:
        """Test missing execution_logic reduces score and appears in missing_sections."""
        skill = {
            "name": "partial-skill",
            "intent": "This is a complete intent with enough characters",
            # execution_logic is missing
            "constraints": ["Constraint one", "Constraint two"],
            "failure_modes": ["Failure one", "Failure two"],
            "expected_output": "Expected output here",
            "context": "Context section",
            "input_pattern": "Input pattern",
        }

        result = self.scorer.score(skill)

        self.assertLess(result.score, 1.0)
        self.assertIn("execution_logic", result.missing_sections)
        # Score should be reduced by execution_logic weight (0.30)
        self.assertLess(result.score, 0.75)

    def test_partial_credit(self) -> None:
        """Test execution_logic with 100 chars (below 200 min) receives partial score."""
        skill = {
            "name": "partial-credit-skill",
            "intent": "This is a complete intent with enough characters",
            "execution_logic": (
                "This execution logic has exactly one hundred characters which is "
                "below the minimum requirement."
            ),  # ~100 chars
            "constraints": ["Constraint one", "Constraint two"],
            "failure_modes": ["Failure one", "Failure two"],
            "expected_output": "Expected output here",
            "context": "Context section",
            "input_pattern": "Input pattern",
        }

        result = self.scorer.score(skill)

        # execution_logic should be in weak_sections (partial credit)
        self.assertIn("execution_logic", result.weak_sections)
        self.assertNotIn("execution_logic", result.missing_sections)
        # Score should be less than perfect
        self.assertLess(result.score, 1.0)
        self.assertGreater(result.score, 0.5)

    def test_list_section_partial(self) -> None:
        """Test constraints with 1 item (min 2) receives partial credit."""
        skill = {
            "name": "partial-list-skill",
            "intent": "This is a complete intent with enough characters",
            "execution_logic": (
                "This is a comprehensive execution logic section that exceeds "
                "the minimum character requirement of 200 characters. It contains "
                "detailed step-by-step instructions on how to execute the skill "
                "properly including all necessary context."
            ),
            "constraints": ["Only one constraint"],  # Min is 2
            "failure_modes": ["Failure one", "Failure two"],
            "expected_output": "Expected output here",
            "context": "Context section",
            "input_pattern": "Input pattern",
        }

        result = self.scorer.score(skill)

        # constraints should be in weak_sections
        self.assertIn("constraints", result.weak_sections)
        self.assertNotIn("constraints", result.missing_sections)
        self.assertLess(result.score, 1.0)

    def test_all_lists_empty(self) -> None:
        """Test empty constraints and failure_modes result in deductions."""
        skill = {
            "name": "no-lists-skill",
            "intent": "This is a complete intent with enough characters",
            "execution_logic": (
                "This is a comprehensive execution logic section that exceeds "
                "the minimum character requirement of 200 characters. It contains "
                "detailed step-by-step instructions on how to execute the skill "
                "properly including all necessary context."
            ),
            "constraints": [],  # Empty list
            "failure_modes": [],  # Empty list
            "expected_output": "Expected output here",
            "context": "Context section",
            "input_pattern": "Input pattern",
        }

        result = self.scorer.score(skill)

        self.assertIn("constraints", result.missing_sections)
        self.assertIn("failure_modes", result.missing_sections)
        # Combined weight of constraints (0.15) + failure_modes (0.15) = 0.30
        self.assertLess(result.score, 0.75)

    def test_custom_sections_config(self) -> None:
        """Test custom completeness_sections configuration."""
        custom_config = {
            "completeness_sections": {
                "title": {"type": "text", "min_chars": 5, "weight": 0.5},
                "tags": {"type": "list", "min_items": 3, "weight": 0.5},
            }
        }

        custom_scorer = CompletenessScorer(config=custom_config)

        skill = {
            "title": "Valid Title",
            "tags": ["tag1", "tag2", "tag3"],
        }

        result = custom_scorer.score(skill)

        self.assertGreaterEqual(result.score, 0.95)
        self.assertEqual(len(result.missing_sections), 0)

        # Test partial custom sections
        partial_skill = {
            "title": "OK",  # 2 chars (min 5) = partial
            "tags": ["tag1"],  # 1 item (min 3) = partial
        }

        partial_result = custom_scorer.score(partial_skill)

        self.assertLess(partial_result.score, 1.0)
        self.assertEqual(len(partial_result.weak_sections), 2)

    def test_weak_sections_tracked(self) -> None:
        """Test sections below minimum but not empty appear in weak_sections."""
        skill = {
            "name": "weak-skill",
            "intent": "Short",  # 5 chars (min 20) = weak
            "execution_logic": "Also short here",  # ~15 chars (min 200) = weak
            "constraints": ["One"],  # 1 item (min 2) = weak
            "failure_modes": ["One"],  # 1 item (min 2) = weak
            "expected_output": "Out",  # 3 chars (min 20) = weak
            "context": "Con",  # 3 chars (min 10) = weak
            "input_pattern": "In",  # 2 chars (min 10) = weak
        }

        result = self.scorer.score(skill)

        # All sections present but weak
        self.assertEqual(len(result.missing_sections), 0)
        self.assertEqual(len(result.weak_sections), 7)
        self.assertIn("intent", result.weak_sections)
        self.assertIn("execution_logic", result.weak_sections)
        self.assertIn("constraints", result.weak_sections)

    def test_score_clamped_zero_to_one(self) -> None:
        """Test score is always clamped between 0.0 and 1.0."""
        # Empty skill should give 0.0 or close to it
        empty_result = self.scorer.score({})
        self.assertGreaterEqual(empty_result.score, 0.0)
        self.assertLessEqual(empty_result.score, 1.0)

        # Perfect skill should give 1.0 or close to it
        perfect_skill = {
            "intent": "This is a complete intent with enough characters to meet minimum",
            "execution_logic": (
                "This is a comprehensive execution logic section that exceeds "
                "the minimum character requirement of 200 characters. It contains "
                "detailed step-by-step instructions on how to execute the skill "
                "properly including all necessary context and examples for completeness."
            ),
            "constraints": ["Constraint one", "Constraint two", "Constraint three"],
            "failure_modes": ["Failure one", "Failure two", "Failure three"],
            "expected_output": "Expected output with sufficient detail here",
            "context": "Context section with enough detail",
            "input_pattern": "Input pattern details",
        }

        perfect_result = self.scorer.score(perfect_skill)
        self.assertGreaterEqual(perfect_result.score, 0.0)
        self.assertLessEqual(perfect_result.score, 1.0)

    def test_details_messages(self) -> None:
        """Test details list contains descriptive messages."""
        skill = {
            "intent": "Short",  # Weak
            # execution_logic missing
            "constraints": [],  # Missing
            "failure_modes": ["One"],  # Weak
            "expected_output": "Output",
            "context": "Context",
            "input_pattern": "Input",
        }

        result = self.scorer.score(skill)

        self.assertGreater(len(result.details), 0)
        details_str = " ".join(result.details)
        # Check for missing section message
        self.assertIn("execution_logic", details_str)
        # Check for weak section messages
        self.assertTrue(
            any("Weak" in msg for msg in result.details),
            "Expected at least one weak section message",
        )
        self.assertTrue(
            any("Missing" in msg for msg in result.details),
            "Expected at least one missing section message",
        )

    def test_string_coercion(self) -> None:
        """Test non-string values in skill_dict are handled gracefully."""
        skill = {
            "intent": 12345,  # Integer
            "execution_logic": None,  # None
            "constraints": "not a list",  # String instead of list
            "failure_modes": 42,  # Integer instead of list
            "expected_output": True,  # Boolean
            "context": 3.14159,  # Float
            "input_pattern": ["this", "is", "a", "list"],  # List instead of string
        }

        # Should not raise an exception
        result = self.scorer.score(skill)

        self.assertIsInstance(result, CompletenessResult)
        self.assertGreaterEqual(result.score, 0.0)
        self.assertLessEqual(result.score, 1.0)
        # constraints and failure_modes should be missing (not lists)
        self.assertIn("constraints", result.missing_sections)
        self.assertIn("failure_modes", result.missing_sections)


if __name__ == "__main__":
    # Run tests with verbose output
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompletenessScorer)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
