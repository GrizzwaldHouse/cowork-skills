# quad_skill_engine.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Extract reusable Quad Skills from Claude session artifacts for knowledge engineering

"""
Quad Skill extraction engine for the OwlWatcher AI Self-Improvement Pipeline.

Analyses Claude session artifacts (plans, diffs, memory files) and extracts
structured, reusable intelligence units called *Quad Skills*.  Each skill
captures intent, context, execution logic, constraints, and failure modes
so the system can learn from prior sessions.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from log_config import configure_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()
logger = logging.getLogger("quad_skill_engine")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class QuadSkill:
    """Standardized unit of reusable AI intelligence."""

    skill_id: str
    name: str
    intent: str
    context: str
    input_pattern: str
    execution_logic: str
    constraints: list[str]
    expected_output: str
    failure_modes: list[str]
    security_classification: str  # SAFE | REVIEW_REQUIRED | RESTRICTED

    # Metadata
    source_session: str
    source_project: str
    confidence_score: float
    reuse_frequency: int
    extracted_at: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuadSkill:
        """Deserialize from a plain dictionary."""
        return cls(
            skill_id=data.get("skill_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            intent=data.get("intent", ""),
            context=data.get("context", ""),
            input_pattern=data.get("input_pattern", ""),
            execution_logic=data.get("execution_logic", ""),
            constraints=data.get("constraints", []),
            expected_output=data.get("expected_output", ""),
            failure_modes=data.get("failure_modes", []),
            security_classification=data.get("security_classification", "SAFE"),
            source_session=data.get("source_session", ""),
            source_project=data.get("source_project", ""),
            confidence_score=float(data.get("confidence_score", 0.0)),
            reuse_frequency=int(data.get("reuse_frequency", 0)),
            extracted_at=data.get("extracted_at", datetime.now(timezone.utc).isoformat()),
            version=int(data.get("version", 1)),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    """Convert *text* to a kebab-case slug."""
    return _SLUG_RE.sub("-", text.strip().lower()).strip("-")


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    """Compute Jaccard similarity over word sets of two strings."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


_UNSAFE_CODE_RE = re.compile(
    r"\b(eval|exec|os\.system|subprocess|__import__|rm\s+-rf|format\s+c:)\b",
    re.IGNORECASE,
)


def _classify_security(text: str) -> str:
    """Classify security level based on content patterns."""
    if _UNSAFE_CODE_RE.search(text):
        return "REVIEW_REQUIRED"
    return "SAFE"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class QuadSkillEngine:
    """Extracts reusable intelligence from Claude session artifacts."""

    def __init__(self, config: dict[str, Any]) -> None:
        extraction_cfg = config.get("extraction", {})
        self._min_confidence = extraction_cfg.get("min_confidence", 0.3)
        self._max_per_session = extraction_cfg.get("max_skills_per_session", 5)
        self._dedup_threshold = extraction_cfg.get("dedup_similarity_threshold", 0.85)
        self._skill_store = BASE_DIR / "data" / "quad_skills"
        self._skill_store.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------
    def extract_from_session(self, session_event_dict: dict[str, Any]) -> list[QuadSkill]:
        """Main entry: dispatch extraction based on session signal type."""
        signal = session_event_dict.get("signal", "")
        artifacts = session_event_dict.get("artifacts", [])
        project = session_event_dict.get("project", "unknown")

        skills: list[QuadSkill] = []
        for artifact_path in artifacts:
            path = Path(artifact_path)
            if not path.exists():
                logger.debug("Artifact not found, skipping: %s", path)
                continue
            if ".claude/plans/" in str(path).replace("\\", "/") and path.suffix == ".md":
                skills.extend(self.extract_from_plan(path, project))
            elif path.name.lower() == "memory.md":
                skills.extend(self.extract_from_memory(path, project))

        # Also try diff extraction on session end
        if signal == "session_end":
            skills.extend(self.extract_from_diff(project))

        # Deduplicate and cap
        skills = self.deduplicate(skills)
        return skills[: self._max_per_session]

    # ------------------------------------------------------------------
    # Plan extraction
    # ------------------------------------------------------------------
    def extract_from_plan(self, plan_path: Path, project: str = "") -> list[QuadSkill]:
        """Extract skills from a ``.claude/plans/*.md`` file.

        Parses markdown ``##`` sections and creates one :class:`QuadSkill`
        per major section.
        """
        try:
            content = plan_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read plan file %s: %s", plan_path, exc)
            return []

        sections = self._split_markdown_sections(content)
        skills: list[QuadSkill] = []

        for title, body in sections:
            if not body.strip():
                continue

            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
            intent = paragraphs[0] if paragraphs else title
            security = _classify_security(body)

            skill = QuadSkill(
                skill_id=str(uuid.uuid4()),
                name=_slugify(title),
                intent=intent,
                context=f"Extracted from plan: {plan_path.name}",
                input_pattern=f"Plan section: {title}",
                execution_logic=body.strip(),
                constraints=self._extract_constraints(body),
                expected_output=f"Implementation of: {title}",
                failure_modes=self._extract_failure_modes(body),
                security_classification=security,
                source_session=str(plan_path),
                source_project=project,
                confidence_score=0.6,
                reuse_frequency=1,
                extracted_at=datetime.now(timezone.utc).isoformat(),
                version=1,
            )
            skills.append(skill)

        logger.info("Extracted %d skills from plan %s", len(skills), plan_path.name)
        return skills

    # ------------------------------------------------------------------
    # Diff extraction
    # ------------------------------------------------------------------
    def extract_from_diff(self, project: str) -> list[QuadSkill]:
        """Extract skills from ``git diff HEAD~1`` in the project directory.

        Looks for new function definitions and config changes.
        """
        project_path = Path(project) if project != "unknown" else BASE_DIR
        if not (project_path / ".git").exists():
            logger.debug("No git repo at %s, skipping diff extraction", project_path)
            return []

        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1"],
                capture_output=True,
                text=True,
                cwd=str(project_path),
                timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("Git diff failed for %s: %s", project_path, exc)
            return []

        if result.returncode != 0 or not result.stdout:
            logger.debug("No diff output for %s", project_path)
            return []

        return self._parse_diff(result.stdout, project)

    def _parse_diff(self, diff_text: str, project: str) -> list[QuadSkill]:
        """Parse git diff output for function definitions and config changes."""
        skills: list[QuadSkill] = []

        # Match added function/method definitions (Python and JS/TS)
        func_re = re.compile(r"^\+\s*(def |async def |function |const \w+ = )\s*(\w+)", re.MULTILINE)
        # Match config-like additions
        config_re = re.compile(r'^\+\s*["\']?(\w+)["\']?\s*[:=]', re.MULTILINE)

        seen_names: set[str] = set()

        for match in func_re.finditer(diff_text):
            func_keyword = match.group(1).strip()
            func_name = match.group(2)
            if func_name in seen_names:
                continue
            seen_names.add(func_name)

            # Extract surrounding diff context (up to 20 lines after the match)
            start = match.start()
            context_end = diff_text.find("\n@@", start + 1)
            if context_end == -1:
                context_end = min(start + 2000, len(diff_text))
            snippet = diff_text[start:context_end]

            skill = QuadSkill(
                skill_id=str(uuid.uuid4()),
                name=_slugify(f"{func_name}-pattern"),
                intent=f"Function pattern: {func_name}",
                context=f"Extracted from git diff in {project}",
                input_pattern=f"New {func_keyword.strip()} definition",
                execution_logic=snippet[:2000],
                constraints=["Extracted from diff -- may lack full context"],
                expected_output=f"Implementation of {func_name}",
                failure_modes=["Partial context from diff"],
                security_classification=_classify_security(snippet),
                source_session="git-diff",
                source_project=project,
                confidence_score=0.4,
                reuse_frequency=1,
                extracted_at=datetime.now(timezone.utc).isoformat(),
                version=1,
            )
            skills.append(skill)

        # Config changes -- only if we haven't already captured them as functions
        config_matches = [
            m.group(1) for m in config_re.finditer(diff_text)
            if m.group(1) not in seen_names
        ]
        if config_matches:
            config_names = ", ".join(sorted(set(config_matches))[:10])
            skill = QuadSkill(
                skill_id=str(uuid.uuid4()),
                name=_slugify("config-change-pattern"),
                intent=f"Configuration change pattern: {config_names}",
                context=f"Config keys modified in {project}",
                input_pattern="Configuration update",
                execution_logic=f"Modified config keys: {config_names}",
                constraints=["Configuration changes may require restart"],
                expected_output="Updated configuration",
                failure_modes=["Invalid config values"],
                security_classification="SAFE",
                source_session="git-diff",
                source_project=project,
                confidence_score=0.4,
                reuse_frequency=1,
                extracted_at=datetime.now(timezone.utc).isoformat(),
                version=1,
            )
            skills.append(skill)

        logger.info("Extracted %d skills from diff for %s", len(skills), project)
        return skills

    # ------------------------------------------------------------------
    # Memory extraction
    # ------------------------------------------------------------------
    def extract_from_memory(self, memory_path: Path, project: str = "") -> list[QuadSkill]:
        """Extract skills from MEMORY.md.

        Looks for stable patterns indicated by keywords such as *confirmed*,
        *always*, *never*, *convention*.
        """
        try:
            content = memory_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read memory file %s: %s", memory_path, exc)
            return []

        stable_re = re.compile(
            r"^[-*]\s+(.+(?:confirmed|always|never|convention|must|required).+)$",
            re.IGNORECASE | re.MULTILINE,
        )

        skills: list[QuadSkill] = []
        seen: set[str] = set()

        for match in stable_re.finditer(content):
            line = match.group(1).strip()
            slug = _slugify(line[:60])
            if slug in seen:
                continue
            seen.add(slug)

            skill = QuadSkill(
                skill_id=str(uuid.uuid4()),
                name=slug,
                intent=line,
                context=f"Stable pattern from MEMORY.md in {project}",
                input_pattern="Memory pattern",
                execution_logic=line,
                constraints=["Established convention -- do not modify without review"],
                expected_output="Consistent behaviour following convention",
                failure_modes=["Convention violated if ignored"],
                security_classification="SAFE",
                source_session=str(memory_path),
                source_project=project,
                confidence_score=0.8,
                reuse_frequency=1,
                extracted_at=datetime.now(timezone.utc).isoformat(),
                version=1,
            )
            skills.append(skill)

        logger.info("Extracted %d skills from memory %s", len(skills), memory_path.name)
        return skills

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------
    def deduplicate(self, skills: list[QuadSkill]) -> list[QuadSkill]:
        """Remove near-duplicate skills using Jaccard similarity.

        When two skills exceed the dedup threshold, the one with the
        higher confidence score is kept.
        """
        if not skills:
            return skills

        unique: list[QuadSkill] = []
        for candidate in skills:
            candidate_text = f"{candidate.intent} {candidate.execution_logic}"
            is_dup = False
            for i, existing in enumerate(unique):
                existing_text = f"{existing.intent} {existing.execution_logic}"
                similarity = _jaccard_similarity(candidate_text, existing_text)
                if similarity >= self._dedup_threshold:
                    # Keep the higher-confidence skill
                    if candidate.confidence_score > existing.confidence_score:
                        unique[i] = candidate
                    is_dup = True
                    break
            if not is_dup:
                unique.append(candidate)

        if len(unique) < len(skills):
            logger.info("Deduplication: %d -> %d skills", len(skills), len(unique))
        return unique

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_skill_md(self, skill: QuadSkill) -> str:
        """Convert a :class:`QuadSkill` to SKILL.md markdown format."""
        constraints_md = "\n".join(f"- {c}" for c in skill.constraints) if skill.constraints else "- None"
        failure_modes_md = "\n".join(f"- {f}" for f in skill.failure_modes) if skill.failure_modes else "- None"

        return (
            f"---\n"
            f"name: {skill.name}\n"
            f"description: {skill.intent}\n"
            f"user-invocable: false\n"
            f"quad-version: {skill.version}\n"
            f"confidence: {skill.confidence_score}\n"
            f"security: {skill.security_classification}\n"
            f"source-project: {skill.source_project}\n"
            f"extracted-at: {skill.extracted_at}\n"
            f"---\n\n"
            f"# {skill.name}\n\n"
            f"## Context\n\n{skill.context}\n\n"
            f"## When to Use\n\n{skill.input_pattern}\n\n"
            f"## Logic\n\n{skill.execution_logic}\n\n"
            f"## Constraints\n\n{constraints_md}\n\n"
            f"## Expected Output\n\n{skill.expected_output}\n\n"
            f"## Known Failure Modes\n\n{failure_modes_md}\n"
        )

    def to_json(self, skill: QuadSkill) -> dict[str, Any]:
        """Convert a :class:`QuadSkill` to a JSON-serializable dict."""
        return skill.to_dict()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_skill(self, skill: QuadSkill) -> Path:
        """Save a skill to ``data/quad_skills/{skill_id}.json``."""
        dest = self._skill_store / f"{skill.skill_id}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8") as fh:
            json.dump(skill.to_dict(), fh, indent=2, default=str)
        logger.info("Saved skill %s to %s", skill.name, dest)
        return dest

    def load_existing_skills(self) -> list[QuadSkill]:
        """Load all existing skills from ``data/quad_skills/*.json``."""
        skills: list[QuadSkill] = []
        if not self._skill_store.exists():
            return skills
        for json_path in self._skill_store.glob("*.json"):
            try:
                with json_path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                skills.append(QuadSkill.from_dict(data))
            except (json.JSONDecodeError, OSError, KeyError) as exc:
                logger.warning("Could not load skill from %s: %s", json_path, exc)
        logger.info("Loaded %d existing skills", len(skills))
        return skills

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _split_markdown_sections(content: str) -> list[tuple[str, str]]:
        """Split markdown content by ``##`` headers.

        Returns a list of ``(title, body)`` tuples.
        """
        sections: list[tuple[str, str]] = []
        header_re = re.compile(r"^##\s+(.+)$", re.MULTILINE)
        matches = list(header_re.finditer(content))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start:end].strip()
            sections.append((title, body))

        return sections

    @staticmethod
    def _extract_constraints(text: str) -> list[str]:
        """Extract constraint-like items from text.

        Looks for bullet points containing restrictive language.
        """
        constraint_re = re.compile(
            r"^[-*]\s+(.+(?:must|should|cannot|never|always|only|limit|restrict|require).+)$",
            re.IGNORECASE | re.MULTILINE,
        )
        return [m.group(1).strip() for m in constraint_re.finditer(text)]

    @staticmethod
    def _extract_failure_modes(text: str) -> list[str]:
        """Extract failure mode indicators from text.

        Looks for references to errors, failures, or edge cases.
        """
        failure_re = re.compile(
            r"^[-*]\s+(.+(?:fail|error|crash|timeout|broken|missing|invalid|edge case).+)$",
            re.IGNORECASE | re.MULTILINE,
        )
        return [m.group(1).strip() for m in failure_re.finditer(text)]
