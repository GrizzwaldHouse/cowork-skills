# test_quad_skill_engine.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Unit tests for QuadSkillEngine extraction, dedup, serialization, and persistence

"""
Unit tests for the Quad Skill extraction engine.

Covers plan extraction, memory extraction, deduplication, SKILL.md
generation, save/load round-trip, and session cap enforcement.
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

from quad_skill_engine import QuadSkill, QuadSkillEngine, _slugify, _jaccard_similarity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QuadSkillEngine:
    """Create a QuadSkillEngine with skill store in a temp directory."""
    monkeypatch.setattr(
        "quad_skill_engine.BASE_DIR", tmp_path,
    )
    config: dict = {
        "extraction": {
            "min_confidence": 0.3,
            "max_skills_per_session": 5,
            "dedup_similarity_threshold": 0.85,
        },
    }
    return QuadSkillEngine(config)


@pytest.fixture
def sample_skill() -> QuadSkill:
    """Create a sample QuadSkill for testing."""
    return QuadSkill(
        skill_id=str(uuid.uuid4()),
        name="test-skill",
        intent="A test skill for validation",
        context="Unit testing context",
        input_pattern="Test trigger pattern",
        execution_logic="This is a moderately long execution logic block that "
            "describes how to accomplish the task step by step with enough "
            "content to pass quality checks.",
        constraints=["Must not exceed time limit", "Should always validate input"],
        expected_output="Successful test result",
        failure_modes=["Timeout on slow systems", "Invalid input causes error"],
        security_classification="SAFE",
        source_session="test-session-001",
        source_project="test-project",
        confidence_score=0.7,
        reuse_frequency=1,
        extracted_at=datetime.now(timezone.utc).isoformat(),
        version=1,
    )


@pytest.fixture
def sample_plan(tmp_path: Path) -> Path:
    """Create a temporary plan markdown file."""
    plan_dir = tmp_path / ".claude" / "plans"
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / "test-plan.md"
    plan_file.write_text(
        "# Test Plan\n\n"
        "## Setup Environment\n\n"
        "Install all required dependencies and configure the dev environment.\n\n"
        "- Must install Python 3.12+\n"
        "- Should always use virtual environments\n\n"
        "## Implement Feature\n\n"
        "Build the feature according to the specification.\n\n"
        "- Handle edge case where input is empty causing error\n"
        "- Never hardcode credentials\n\n"
        "## Run Tests\n\n"
        "Execute the full test suite to validate changes.\n\n"
        "- Timeout on slow CI systems may fail\n",
        encoding="utf-8",
    )
    return plan_file


@pytest.fixture
def sample_memory(tmp_path: Path) -> Path:
    """Create a temporary MEMORY.md file."""
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text(
        "# Project Memory\n\n"
        "- Always use `from __future__ import annotations` first -- confirmed pattern\n"
        "- Never commit .env files to git -- convention enforced by CI\n"
        "- Use BASE_DIR for all paths -- always required for portability\n"
        "- This is a regular note without stable keywords\n"
        "- Logging must use configure_logging() at module level\n",
        encoding="utf-8",
    )
    return memory_file


# ---------------------------------------------------------------------------
# QuadSkill dataclass tests
# ---------------------------------------------------------------------------
class TestQuadSkill:
    """Test QuadSkill data structure."""

    def test_to_dict_returns_all_fields(self, sample_skill: QuadSkill) -> None:
        """Test to_dict includes every field."""
        data = sample_skill.to_dict()
        assert data["skill_id"] == sample_skill.skill_id
        assert data["name"] == "test-skill"
        assert data["intent"] == sample_skill.intent
        assert data["constraints"] == sample_skill.constraints
        assert data["confidence_score"] == sample_skill.confidence_score
        assert data["version"] == 1

    def test_from_dict_roundtrip(self, sample_skill: QuadSkill) -> None:
        """Test from_dict restores the same object."""
        data = sample_skill.to_dict()
        restored = QuadSkill.from_dict(data)
        assert restored.skill_id == sample_skill.skill_id
        assert restored.name == sample_skill.name
        assert restored.intent == sample_skill.intent
        assert restored.constraints == sample_skill.constraints
        assert restored.confidence_score == sample_skill.confidence_score

    def test_from_dict_handles_missing_keys(self) -> None:
        """Test from_dict fills defaults for missing keys."""
        partial: dict = {"name": "partial-skill", "intent": "Partially defined"}
        skill = QuadSkill.from_dict(partial)
        assert skill.name == "partial-skill"
        assert skill.constraints == []
        assert skill.version == 1
        assert skill.security_classification == "SAFE"

    def test_from_dict_preserves_types(self) -> None:
        """Test from_dict coerces numeric types correctly."""
        data: dict = {
            "skill_id": "abc-123",
            "name": "typed",
            "intent": "type check",
            "confidence_score": "0.75",  # string should be coerced to float
            "version": "3",             # string should be coerced to int
            "reuse_frequency": "5",
        }
        skill = QuadSkill.from_dict(data)
        assert isinstance(skill.confidence_score, float)
        assert skill.confidence_score == 0.75
        assert isinstance(skill.version, int)
        assert skill.version == 3


# ---------------------------------------------------------------------------
# Plan extraction tests
# ---------------------------------------------------------------------------
class TestExtractFromPlan:
    """Test plan-based skill extraction."""

    def test_extract_from_plan_creates_skills(
        self, engine: QuadSkillEngine, sample_plan: Path
    ) -> None:
        """Test extraction from a plan file produces skills."""
        skills = engine.extract_from_plan(sample_plan, "test-project")
        assert len(skills) == 3  # Three ## sections

    def test_plan_skills_have_correct_names(
        self, engine: QuadSkillEngine, sample_plan: Path
    ) -> None:
        """Test extracted skill names are slugified section titles."""
        skills = engine.extract_from_plan(sample_plan, "test-project")
        names = [s.name for s in skills]
        assert "setup-environment" in names
        assert "implement-feature" in names
        assert "run-tests" in names

    def test_plan_skills_have_medium_confidence(
        self, engine: QuadSkillEngine, sample_plan: Path
    ) -> None:
        """Test plan-extracted skills have confidence 0.6."""
        skills = engine.extract_from_plan(sample_plan, "test-project")
        for skill in skills:
            assert skill.confidence_score == 0.6

    def test_plan_skills_have_context(
        self, engine: QuadSkillEngine, sample_plan: Path
    ) -> None:
        """Test plan-extracted skills reference the plan file."""
        skills = engine.extract_from_plan(sample_plan, "test-project")
        for skill in skills:
            assert "plan" in skill.context.lower()

    def test_extract_from_nonexistent_plan(self, engine: QuadSkillEngine) -> None:
        """Test extraction from a missing file returns empty list."""
        skills = engine.extract_from_plan(Path("/nonexistent/plan.md"), "proj")
        assert skills == []

    def test_plan_extracts_constraints(
        self, engine: QuadSkillEngine, sample_plan: Path
    ) -> None:
        """Test that constraint-like bullets are captured."""
        skills = engine.extract_from_plan(sample_plan, "test-project")
        setup_skill = [s for s in skills if s.name == "setup-environment"][0]
        # The plan has "Must install" and "Should always" bullets
        assert len(setup_skill.constraints) >= 1


# ---------------------------------------------------------------------------
# Memory extraction tests
# ---------------------------------------------------------------------------
class TestExtractFromMemory:
    """Test MEMORY.md-based skill extraction."""

    def test_extract_from_memory_finds_stable_patterns(
        self, engine: QuadSkillEngine, sample_memory: Path
    ) -> None:
        """Test extraction picks up lines with stable keywords."""
        skills = engine.extract_from_memory(sample_memory, "test-project")
        # Should find lines with confirmed, convention, always, must/required
        assert len(skills) >= 3

    def test_memory_skills_have_high_confidence(
        self, engine: QuadSkillEngine, sample_memory: Path
    ) -> None:
        """Test memory-extracted skills have confidence 0.8."""
        skills = engine.extract_from_memory(sample_memory, "test-project")
        for skill in skills:
            assert skill.confidence_score == 0.8

    def test_memory_skips_non_stable_lines(
        self, engine: QuadSkillEngine, sample_memory: Path
    ) -> None:
        """Test that lines without stable keywords are skipped."""
        skills = engine.extract_from_memory(sample_memory, "test-project")
        intents = [s.intent for s in skills]
        # The line "This is a regular note" should NOT be extracted
        assert not any("regular note" in i for i in intents)

    def test_extract_from_nonexistent_memory(self, engine: QuadSkillEngine) -> None:
        """Test extraction from a missing file returns empty list."""
        skills = engine.extract_from_memory(Path("/nonexistent/MEMORY.md"), "proj")
        assert skills == []


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------
class TestDeduplicate:
    """Test skill deduplication."""

    def test_deduplicate_removes_near_duplicates(self, engine: QuadSkillEngine) -> None:
        """Test that near-identical skills are collapsed."""
        skill_a = QuadSkill(
            skill_id="aaa",
            name="skill-a",
            intent="Install Python dependencies for the project",
            context="Setup",
            input_pattern="trigger",
            execution_logic="Install Python dependencies for the project using pip install",
            constraints=[],
            expected_output="installed",
            failure_modes=[],
            security_classification="SAFE",
            source_session="s1",
            source_project="p1",
            confidence_score=0.6,
            reuse_frequency=1,
            extracted_at=datetime.now(timezone.utc).isoformat(),
            version=1,
        )
        # Nearly identical skill
        skill_b = QuadSkill(
            skill_id="bbb",
            name="skill-b",
            intent="Install Python dependencies for the project",
            context="Setup",
            input_pattern="trigger",
            execution_logic="Install Python dependencies for the project using pip install",
            constraints=[],
            expected_output="installed",
            failure_modes=[],
            security_classification="SAFE",
            source_session="s2",
            source_project="p1",
            confidence_score=0.8,
            reuse_frequency=1,
            extracted_at=datetime.now(timezone.utc).isoformat(),
            version=1,
        )
        result = engine.deduplicate([skill_a, skill_b])
        assert len(result) == 1
        # Higher-confidence skill_b should be kept
        assert result[0].skill_id == "bbb"

    def test_deduplicate_keeps_distinct_skills(self, engine: QuadSkillEngine) -> None:
        """Test that sufficiently different skills are both kept."""
        skill_a = QuadSkill(
            skill_id="aaa",
            name="skill-a",
            intent="Configure logging for the application server",
            context="Logging",
            input_pattern="setup",
            execution_logic="Set up logging with rotating file handlers and console output",
            constraints=[],
            expected_output="logs",
            failure_modes=[],
            security_classification="SAFE",
            source_session="s1",
            source_project="p1",
            confidence_score=0.6,
            reuse_frequency=1,
            extracted_at=datetime.now(timezone.utc).isoformat(),
            version=1,
        )
        skill_b = QuadSkill(
            skill_id="bbb",
            name="skill-b",
            intent="Deploy Docker containers to production cluster",
            context="Deployment",
            input_pattern="deploy",
            execution_logic="Build Docker images tag and push to registry then update Kubernetes",
            constraints=[],
            expected_output="deployed",
            failure_modes=[],
            security_classification="SAFE",
            source_session="s2",
            source_project="p1",
            confidence_score=0.7,
            reuse_frequency=1,
            extracted_at=datetime.now(timezone.utc).isoformat(),
            version=1,
        )
        result = engine.deduplicate([skill_a, skill_b])
        assert len(result) == 2

    def test_deduplicate_empty_list(self, engine: QuadSkillEngine) -> None:
        """Test deduplication of empty list."""
        assert engine.deduplicate([]) == []


# ---------------------------------------------------------------------------
# SKILL.md generation tests
# ---------------------------------------------------------------------------
class TestToSkillMd:
    """Test SKILL.md markdown generation."""

    def test_to_skill_md_has_frontmatter(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill
    ) -> None:
        """Test generated markdown contains YAML frontmatter."""
        md = engine.to_skill_md(sample_skill)
        assert md.startswith("---\n")
        assert "name: test-skill" in md
        assert "user-invocable: false" in md
        assert "quad-version: 1" in md

    def test_to_skill_md_has_sections(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill
    ) -> None:
        """Test generated markdown has all required sections."""
        md = engine.to_skill_md(sample_skill)
        assert "## Context" in md
        assert "## When to Use" in md
        assert "## Logic" in md
        assert "## Constraints" in md
        assert "## Expected Output" in md
        assert "## Known Failure Modes" in md

    def test_to_skill_md_includes_constraints_as_bullets(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill
    ) -> None:
        """Test constraints are rendered as bullet points."""
        md = engine.to_skill_md(sample_skill)
        assert "- Must not exceed time limit" in md
        assert "- Should always validate input" in md

    def test_to_skill_md_includes_failure_modes(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill
    ) -> None:
        """Test failure modes are rendered as bullet points."""
        md = engine.to_skill_md(sample_skill)
        assert "- Timeout on slow systems" in md

    def test_to_skill_md_includes_confidence(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill
    ) -> None:
        """Test confidence score is in frontmatter."""
        md = engine.to_skill_md(sample_skill)
        assert "confidence: 0.7" in md


# ---------------------------------------------------------------------------
# Save / load round-trip tests
# ---------------------------------------------------------------------------
class TestPersistence:
    """Test skill save and load round-trip."""

    def test_save_creates_json_file(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill, tmp_path: Path
    ) -> None:
        """Test save_skill creates a JSON file."""
        path = engine.save_skill(sample_skill)
        assert path.exists()
        assert path.suffix == ".json"

    def test_save_load_roundtrip(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill
    ) -> None:
        """Test saving and loading preserves all data."""
        engine.save_skill(sample_skill)
        loaded = engine.load_existing_skills()
        assert len(loaded) == 1
        assert loaded[0].skill_id == sample_skill.skill_id
        assert loaded[0].name == sample_skill.name
        assert loaded[0].intent == sample_skill.intent
        assert loaded[0].confidence_score == sample_skill.confidence_score

    def test_load_empty_store(self, engine: QuadSkillEngine) -> None:
        """Test loading from an empty store returns empty list."""
        loaded = engine.load_existing_skills()
        assert loaded == []

    def test_save_multiple_skills(
        self, engine: QuadSkillEngine, sample_skill: QuadSkill
    ) -> None:
        """Test saving multiple skills and loading them all."""
        engine.save_skill(sample_skill)

        second = QuadSkill.from_dict({
            **sample_skill.to_dict(),
            "skill_id": str(uuid.uuid4()),
            "name": "second-skill",
        })
        engine.save_skill(second)

        loaded = engine.load_existing_skills()
        assert len(loaded) == 2


# ---------------------------------------------------------------------------
# Confidence scoring tests
# ---------------------------------------------------------------------------
class TestConfidenceScoring:
    """Test confidence scores from different extraction sources."""

    def test_plan_confidence_is_medium(
        self, engine: QuadSkillEngine, sample_plan: Path
    ) -> None:
        """Test plan extraction yields confidence 0.6."""
        skills = engine.extract_from_plan(sample_plan, "proj")
        assert all(s.confidence_score == 0.6 for s in skills)

    def test_memory_confidence_is_high(
        self, engine: QuadSkillEngine, sample_memory: Path
    ) -> None:
        """Test memory extraction yields confidence 0.8."""
        skills = engine.extract_from_memory(sample_memory, "proj")
        assert all(s.confidence_score == 0.8 for s in skills)


# ---------------------------------------------------------------------------
# Max skills per session cap
# ---------------------------------------------------------------------------
class TestMaxPerSession:
    """Test max_skills_per_session cap."""

    def test_session_cap_enforced(
        self, engine: QuadSkillEngine, tmp_path: Path
    ) -> None:
        """Test extract_from_session caps results to max_per_session."""
        # Create a plan with many sections (more than 5)
        plan_dir = tmp_path / "project" / ".claude" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "big-plan.md"

        sections = "\n\n".join(
            f"## Section {i}\n\nContent for section {i} with enough words to be meaningful."
            for i in range(10)
        )
        plan_file.write_text(f"# Big Plan\n\n{sections}", encoding="utf-8")

        event = {
            "signal": "plan_created",
            "artifacts": [str(plan_file)],
            "project": "test-project",
        }
        skills = engine.extract_from_session(event)
        assert len(skills) <= 5


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------
class TestHelpers:
    """Test helper functions."""

    def test_slugify_basic(self) -> None:
        """Test slugify converts text to kebab-case."""
        assert _slugify("Setup Environment") == "setup-environment"
        assert _slugify("Run Tests!") == "run-tests"
        assert _slugify("  Multiple   Spaces  ") == "multiple-spaces"

    def test_jaccard_identical(self) -> None:
        """Test Jaccard similarity of identical strings is 1.0."""
        assert _jaccard_similarity("hello world", "hello world") == 1.0

    def test_jaccard_disjoint(self) -> None:
        """Test Jaccard similarity of disjoint strings is 0.0."""
        assert _jaccard_similarity("hello world", "foo bar") == 0.0

    def test_jaccard_partial(self) -> None:
        """Test Jaccard similarity of partially overlapping strings."""
        sim = _jaccard_similarity("hello world foo", "hello world bar")
        # Intersection: {hello, world} = 2, Union: {hello, world, foo, bar} = 4
        assert abs(sim - 0.5) < 0.01

    def test_jaccard_empty(self) -> None:
        """Test Jaccard similarity of two empty strings is 1.0."""
        assert _jaccard_similarity("", "") == 1.0

    def test_jaccard_one_empty(self) -> None:
        """Test Jaccard similarity when one string is empty is 0.0."""
        assert _jaccard_similarity("hello", "") == 0.0
