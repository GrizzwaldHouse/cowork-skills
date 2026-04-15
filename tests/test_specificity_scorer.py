# test_specificity_scorer.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Tests for specificity scoring — detects too-generic or too-project-locked skills

import unittest
import sys

sys.path.insert(0, "C:/ClaudeSkills")

from scripts.scoring.specificity_scorer import SpecificityScorer, SpecificityResult


class TestSpecificityScorer(unittest.TestCase):
    """Test suite for SpecificityScorer — validates generic/specific detection."""

    def setUp(self) -> None:
        """Initialize scorer for each test."""
        self.scorer = SpecificityScorer()

    def test_well_scoped_skill(self) -> None:
        """Well-scoped skill should score high with no flags set."""
        skill = {
            "name": "python-code-reviewer",
            "intent": "Review Python code for architectural quality and adherence to coding standards",
            "execution_logic": (
                "Parse Python files using AST analysis, check for patterns like "
                "unrestricted mutable public state, magic numbers, missing access control, "
                "and polling loops. Generate structured feedback with line numbers and severity."
            ),
            "context": "Applied to production Python codebases",
        }

        result = self.scorer.score(skill)

        self.assertGreaterEqual(result.score, 0.8)
        self.assertFalse(result.too_generic)
        self.assertFalse(result.too_specific)
        self.assertEqual(len(result.issues), 0)

    def test_too_generic(self) -> None:
        """Skill with generic indicators should be flagged and penalized."""
        skill = {
            "name": "generic-helper",
            "intent": "Handle everything you need and do things well",
            "execution_logic": (
                "Process inputs and produce good outputs following best practices "
                "for general purpose tasks in any situation"
            ),
            "context": "Universal tool",
        }

        result = self.scorer.score(skill)

        self.assertTrue(result.too_generic)
        self.assertLess(result.score, 1.0)
        self.assertTrue(any("Too generic" in issue for issue in result.issues))

    def test_too_specific(self) -> None:
        """Skill with project-locked indicators should be flagged and penalized."""
        skill = {
            "name": "project-locked-tool",
            "intent": "This tool is only for this project and not portable to other codebases",
            "execution_logic": (
                "Hardcoded for this specific application only with paths and "
                "configuration that only works with this repo"
            ),
            "context": "Single-use utility",
        }

        result = self.scorer.score(skill)

        self.assertTrue(result.too_specific)
        self.assertLess(result.score, 1.0)
        self.assertTrue(any("Too project-locked" in issue for issue in result.issues))

    def test_brief_intent(self) -> None:
        """Intent with fewer than 5 words should be penalized."""
        skill = {
            "name": "brief-intent",
            "intent": "Fix it",  # Only 2 words
            "execution_logic": (
                "Analyze the codebase, identify issues, apply fixes using "
                "best practices, and generate a report with changes made"
            ),
            "context": "Development tool",
        }

        result = self.scorer.score(skill)

        # Should have deduction for brief intent (0.2) and too_generic flag set
        self.assertTrue(result.too_generic)  # < 3 words triggers generic flag
        self.assertTrue(any("Intent too brief" in issue for issue in result.issues))
        self.assertLess(result.score, 1.0)

    def test_brief_logic(self) -> None:
        """Execution logic with fewer than 15 words should be penalized."""
        skill = {
            "name": "brief-logic",
            "intent": "Review code for quality and standards compliance issues",
            "execution_logic": "Parse files and check rules",  # Only 5 words
            "context": "Code review assistant",
        }

        result = self.scorer.score(skill)

        self.assertTrue(
            any("Execution logic too brief" in issue for issue in result.issues)
        )
        self.assertLess(result.score, 1.0)

    def test_high_filler_ratio(self) -> None:
        """Text with high filler word ratio should be penalized and flagged generic."""
        skill = {
            "name": "filler-heavy",
            "intent": "Properly ensure good correct appropriate suitable proper effective results",
            "execution_logic": (
                "Use best optimal efficient great nice proper appropriate suitable "
                "correct right good well methods for effective proper good results"
            ),
            "context": "Quality tool",
        }

        result = self.scorer.score(skill)

        self.assertTrue(result.too_generic)  # Filler triggers generic flag
        self.assertTrue(any("High filler word ratio" in issue for issue in result.issues))
        self.assertLess(result.score, 1.0)

    def test_both_flags(self) -> None:
        """Skill with both generic AND specific indicators should flag both."""
        skill = {
            "name": "confused-skill",
            "intent": "Handle everything in any situation but only for this project",
            "execution_logic": (
                "Do whatever is needed as a general purpose tool but hardcoded "
                "for this specific codebase and not portable to other repositories"
            ),
            "context": "Contradictory design",
        }

        result = self.scorer.score(skill)

        self.assertTrue(result.too_generic)
        self.assertTrue(result.too_specific)
        # Two 0.30 deductions = 0.60 total minimum
        self.assertLessEqual(result.score, 0.40)
        self.assertGreaterEqual(len(result.issues), 2)

    def test_custom_indicators(self) -> None:
        """Custom generic/specific indicators via config should work."""
        config = {
            "generic_indicators": ["magic bullet"],
            "specific_indicators": ["acme corp only"],
        }
        scorer = SpecificityScorer(config)

        skill_generic = {
            "name": "custom-generic",
            "intent": "This is a magic bullet that solves all problems",
            "execution_logic": (
                "Apply universal solution that works everywhere automatically "
                "without configuration or customization needed"
            ),
            "context": "Universal",
        }

        result_generic = scorer.score(skill_generic)
        self.assertTrue(result_generic.too_generic)
        self.assertTrue(any("magic bullet" in issue for issue in result_generic.issues))

        skill_specific = {
            "name": "custom-specific",
            "intent": "Process data for Acme Corp only with custom logic",
            "execution_logic": (
                "Uses Acme Corp proprietary formats and internal systems that "
                "are specific to their infrastructure and cannot be reused"
            ),
            "context": "Corporate tool",
        }

        result_specific = scorer.score(skill_specific)
        self.assertTrue(result_specific.too_specific)
        self.assertTrue(
            any("acme corp only" in issue for issue in result_specific.issues)
        )

    def test_empty_skill(self) -> None:
        """Empty skill dict should produce low score with multiple issues."""
        skill = {}

        result = self.scorer.score(skill)

        # Empty strings: intent < 5 words, logic < 15 words
        # Two deductions: -0.2 (intent) + -0.2 (logic) = 0.6
        self.assertLessEqual(result.score, 0.6)
        self.assertGreaterEqual(len(result.issues), 2)

    def test_normal_filler_ratio(self) -> None:
        """Reasonable text with normal filler usage should not be penalized."""
        skill = {
            "name": "balanced-skill",
            "intent": "Parse TypeScript files to extract interface definitions and type annotations",
            "execution_logic": (
                "Use TypeScript compiler API to build AST, traverse nodes to find "
                "InterfaceDeclaration and TypeAliasDeclaration, extract properties "
                "with types, modifiers, and JSDoc comments, serialize to JSON"
            ),
            "context": "TypeScript analysis",
        }

        result = self.scorer.score(skill)

        self.assertFalse(any("filler" in issue for issue in result.issues))
        # No filler deduction, both word counts good
        self.assertGreaterEqual(result.score, 0.9)

    def test_score_clamped(self) -> None:
        """Extreme deductions should clamp score between 0.0 and 1.0."""
        # Construct skill that triggers multiple large deductions
        skill = {
            "name": "extreme-bad",
            "intent": "Do",  # 1 word: -0.2, too_generic from < 3
            "execution_logic": "Handle everything and only for this project works",  # < 15 words: -0.2, generic: -0.3, specific: -0.3
            "context": "",
        }

        result = self.scorer.score(skill)

        # Score should be clamped to 0.0 minimum
        self.assertGreaterEqual(result.score, 0.0)
        self.assertLessEqual(result.score, 1.0)
        self.assertTrue(result.too_generic)
        self.assertTrue(result.too_specific)

    def test_result_immutability(self) -> None:
        """SpecificityResult should be immutable (frozen dataclass)."""
        skill = {
            "name": "test-skill",
            "intent": "Test immutability of result objects with frozen dataclass",
            "execution_logic": (
                "Create a SpecificityResult and attempt to modify fields to "
                "verify that the dataclass decorator enforces immutability"
            ),
            "context": "Unit testing",
        }

        result = self.scorer.score(skill)

        with self.assertRaises(AttributeError):
            result.score = 0.5  # type: ignore

        with self.assertRaises(AttributeError):
            result.too_generic = True  # type: ignore

    def test_case_insensitive_matching(self) -> None:
        """Indicator matching should be case-insensitive."""
        skill = {
            "name": "case-test",
            "intent": "HANDLE EVERYTHING in ANY SITUATION",  # Uppercase generic indicators
            "execution_logic": (
                "Process all inputs with GENERAL PURPOSE logic that works "
                "universally across different contexts and requirements"
            ),
            "context": "Universal",
        }

        result = self.scorer.score(skill)

        self.assertTrue(result.too_generic)
        self.assertTrue(any("Too generic" in issue for issue in result.issues))

    def test_partial_deductions_accumulate(self) -> None:
        """Multiple small deductions should accumulate correctly."""
        skill = {
            "name": "accumulate-test",
            "intent": "Code",  # 1 word: -0.2, < 3 words: too_generic flag
            "execution_logic": "Check code quality",  # 3 words, < 15: -0.2
            "context": "",
        }

        result = self.scorer.score(skill)

        # Deductions: -0.2 (intent) + -0.2 (logic) = -0.4 total
        # Expected score: 1.0 - 0.4 = 0.6
        self.assertAlmostEqual(result.score, 0.6, places=2)
        self.assertEqual(len(result.issues), 2)


if __name__ == "__main__":
    # Self-test block
    unittest.main(verbosity=2)
