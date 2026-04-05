# test_quality_scoring.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Tests for 5-dimension weighted quality scoring engine

import pytest
from scripts.quality_scoring import QualityScoringEngine, QualityReport


@pytest.fixture
def engine():
    """Engine with default config from agent_config.json."""
    return QualityScoringEngine()


@pytest.fixture
def perfect_skill():
    """A skill that should score highly across all dimensions."""
    return {
        "skill_id": "test-perfect",
        "name": "Universal Code Formatter",
        "intent": "Format code in any language using configurable rules for universal, cross-project use",
        "execution_logic": "Parse AST, apply formatting rules from config file, write output. " * 10,
        "context": "Works with any project, framework-agnostic, portable across all environments",
        "input_pattern": "source_file: Path, config: dict[str, Any], language: str",
        "constraints": ["Must not modify semantics", "Must be idempotent", "Must handle UTF-8"],
        "expected_output": "Formatted source code matching configured style rules",
        "failure_modes": ["Parse error on malformed input", "Unsupported language"],
    }


@pytest.fixture
def poor_skill():
    """A skill with project-specific hardcoding and missing sections."""
    return {
        "skill_id": "test-poor",
        "name": "My Hack",
        "intent": "Fix",
        "execution_logic": "do stuff",
        "context": "this repo only, works only with C:\\Users\\bob\\project",
        "input_pattern": "",
        "constraints": [],
        "expected_output": "",
        "failure_modes": [],
    }


class TestReusabilityScoring:
    """95/5 rule enforcement via reusability dimension."""

    def test_clean_skill_high_reusability(self, engine, perfect_skill):
        report = engine.score(perfect_skill, {
            "architecture_score": 1.0, "security_score": 1.0, "quality_score": 1.0,
        })
        reuse_dim = next(d for d in report.dimensions if d.dimension == "reusability")
        assert reuse_dim.score >= 0.8

    def test_project_specific_deduction(self, engine, poor_skill):
        report = engine.score(poor_skill, {
            "architecture_score": 1.0, "security_score": 1.0, "quality_score": 1.0,
        })
        reuse_dim = next(d for d in report.dimensions if d.dimension == "reusability")
        assert reuse_dim.score < 0.8

    def test_no_input_pattern_deduction(self, engine):
        skill = {"skill_id": "x", "name": "y", "input_pattern": ""}
        report = engine.score(skill, {"architecture_score": 1.0, "security_score": 1.0, "quality_score": 1.0})
        reuse_dim = next(d for d in report.dimensions if d.dimension == "reusability")
        assert reuse_dim.score < 1.0


class TestCompletenessScoring:
    """SKILL.md section completeness checks."""

    def test_complete_skill_high_completeness(self, engine, perfect_skill):
        report = engine.score(perfect_skill)
        comp_dim = next(d for d in report.dimensions if d.dimension == "completeness")
        assert comp_dim.score >= 0.8

    def test_missing_sections_low_completeness(self, engine, poor_skill):
        report = engine.score(poor_skill)
        comp_dim = next(d for d in report.dimensions if d.dimension == "completeness")
        assert comp_dim.score < 0.5


class TestCompositeScoring:
    """Weighted composite and disposition gates."""

    def test_weights_sum_to_one(self, engine):
        total = (
            engine._weight_architecture + engine._weight_security +
            engine._weight_quality + engine._weight_reusability +
            engine._weight_completeness
        )
        assert abs(total - 1.0) < 0.001

    def test_approved_disposition(self, engine, perfect_skill):
        report = engine.score(perfect_skill, {
            "architecture_score": 0.95, "security_score": 0.95, "quality_score": 0.95,
        })
        assert report.disposition == "approved"
        assert report.composite_score >= 0.80

    def test_rejected_disposition(self, engine, poor_skill):
        report = engine.score(poor_skill, {
            "architecture_score": 0.1, "security_score": 0.1, "quality_score": 0.1,
        })
        assert report.disposition == "rejected"
        assert report.composite_score < 0.40

    def test_score_clamped_zero_to_one(self, engine):
        skill = {"skill_id": "x", "name": "y"}
        report = engine.score(skill, {
            "architecture_score": 0.0, "security_score": 0.0, "quality_score": 0.0,
        })
        assert 0.0 <= report.composite_score <= 1.0

    def test_report_is_frozen(self, engine, perfect_skill):
        report = engine.score(perfect_skill)
        with pytest.raises(AttributeError):
            report.composite_score = 0.0
