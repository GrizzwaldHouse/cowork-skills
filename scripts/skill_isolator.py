# skill_isolator.py
# Developer: Marcus Daley
# Date: 2026-04-06
# Purpose: Per-agent skill isolation for multi-agent team execution

from __future__ import annotations
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent.skill_isolator")

# Default location for team skill manifests
_TEAMS_DIR: Path = Path("C:/Users/daley/.claude/teams")

# Strict allowlist for team_name and agent_name segments used in filesystem paths.
# Must start with alphanumeric, then alphanumeric/underscore/dash/dot, max 64 chars.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

# Windows reserved device names (case-insensitive, with or without extension).
_WINDOWS_RESERVED = frozenset({
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})


class SkillIsolator:
    """Maps agent roles to skill bundles for isolated multi-agent execution.

    When spawning agent teams, this isolator creates per-agent skill manifests
    so each agent only sees the skills relevant to its role. This keeps the
    active skill count low even when many agents are running concurrently.
    """

    # Maps Claude Code subagent_type values to skill bundle names
    ROLE_BUNDLE_MAP: dict[str, list[str]] = {
        "frontend-builder": ["portfolio-dev", "design-creative"],
        "researcher": ["devops-standards"],
        "content-creator": ["content-marketing", "portfolio-dev"],
        "business-advisor": ["business", "content-marketing"],
        "reviewer": ["devops-standards"],
        "implementer": ["portfolio-dev", "devops-standards"],
        "dotnet-builder": ["devops-standards"],
        "Explore": [],
        "Plan": [],
        "general-purpose": ["devops-standards"],
        "planner": ["devops-standards"],
    }

    def __init__(
        self,
        bundles: dict[str, Any],
        config: dict[str, Any],
        teams_dir: Path | None = None,
    ) -> None:
        self._bundles: dict[str, Any] = bundles
        self._config: dict[str, Any] = config
        # Resolve once at construction so containment checks are stable.
        base = teams_dir or _TEAMS_DIR
        self._teams_dir: Path = Path(base).resolve()
        self._core_bundle: str = config.get("core_bundle", "core")

    # ------------------------------------------------------------------
    # Path traversal validation (Issue #3)
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_name(name: str, field: str) -> None:
        """Reject any name that could escape the teams directory.

        Raises ValueError with a descriptive message on any failure.
        """
        if not isinstance(name, str):
            raise ValueError(f"{field} must be a string, got {type(name).__name__}")
        if not name or not name.strip():
            raise ValueError(f"{field} must not be empty")
        # Reject trailing dots or spaces. Windows normalizes these away in
        # several filesystem APIs, which can cause two distinct names to map
        # to the same directory. Reject at the boundary (CWE-41).
        if name != name.rstrip(". "):
            raise ValueError(
                f"{field} must not end with a dot or space (got {name!r})"
            )
        # Reject control characters and null bytes.
        if any(ord(ch) < 32 for ch in name) or "\x00" in name:
            raise ValueError(f"{field} contains control characters")
        # Reject path separators and drive letters outright — defense in depth
        # on top of the allowlist regex below.
        for bad in ("/", "\\", ":", ".."):
            if bad in name:
                raise ValueError(f"{field} contains forbidden sequence {bad!r}")
        # Reject absolute paths (catches cases the substring check might miss).
        if Path(name).is_absolute():
            raise ValueError(f"{field} must not be an absolute path")
        # Enforce the allowlist.
        if not _NAME_RE.match(name):
            raise ValueError(
                f"{field} must match {_NAME_RE.pattern} (got {name!r})"
            )
        # Reject Windows reserved device names (stem only, case-insensitive).
        stem = name.split(".", 1)[0].lower()
        if stem in _WINDOWS_RESERVED:
            raise ValueError(f"{field} is a reserved device name: {name!r}")

    def _resolve_manifest_path(self, team_name: str, agent_name: str) -> Path:
        """Validate names and return the resolved, contained manifest path.

        Every filesystem method must route through this helper so validation
        cannot be bypassed. Raises ValueError on any traversal attempt.
        """
        self._validate_name(team_name, "team_name")
        self._validate_name(agent_name, "agent_name")

        candidate = (
            self._teams_dir / team_name / "skills" / f"{agent_name}.json"
        ).resolve()

        # Final containment check — catches symlink-based escapes and any
        # other resolution surprises.
        try:
            candidate.relative_to(self._teams_dir)
        except ValueError as exc:
            raise ValueError(
                f"resolved manifest path escapes teams directory: {candidate}"
            ) from exc

        return candidate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_agent_skills(self, agent_role: str) -> list[str]:
        """Resolve an agent role to the full list of skills it needs.

        Always includes the core bundle. Returns a deduplicated, sorted list.
        Unknown roles get only the core bundle.
        """
        bundle_names: list[str] = [self._core_bundle]
        bundle_names.extend(self.ROLE_BUNDLE_MAP.get(agent_role, []))

        skills: set[str] = set()
        bundles_data: dict[str, Any] = self._bundles.get("bundles", {})
        for bundle_name in bundle_names:
            bundle = bundles_data.get(bundle_name, {})
            for skill in bundle.get("skills", []):
                skills.add(skill)

        return sorted(skills)

    def create_agent_manifest(
        self,
        team_name: str,
        agent_name: str,
        agent_role: str,
    ) -> dict[str, Any]:
        """Build a per-agent skill manifest dict (does not write to disk)."""
        # Validate at the earliest ingress so callers that build a manifest
        # and pass it around cannot inject traversal sequences later.
        self._validate_name(team_name, "team_name")
        self._validate_name(agent_name, "agent_name")

        bundle_names: list[str] = [self._core_bundle]
        bundle_names.extend(self.ROLE_BUNDLE_MAP.get(agent_role, []))
        skills = self.get_agent_skills(agent_role)

        return {
            "schema_version": "1.0",
            "team_name": team_name,
            "agent_name": agent_name,
            "agent_role": agent_role,
            "bundles": bundle_names,
            "skills": skills,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def save_agent_manifest(
        self,
        team_name: str,
        agent_name: str,
        manifest: dict[str, Any],
    ) -> Path:
        """Persist the manifest to disk and return the path."""
        manifest_path = self._resolve_manifest_path(team_name, agent_name)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        # Defense in depth against a TOCTOU race where an attacker plants a
        # symlink between _resolve_manifest_path and write_text. We refuse
        # to follow a symlink at the final target.
        if manifest_path.is_symlink():
            raise ValueError(
                f"manifest path is a symlink, refusing to write: {manifest_path}"
            )
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        logger.info(
            "Saved manifest for %s/%s with %d skills",
            team_name, agent_name, len(manifest.get("skills", [])),
        )
        return manifest_path

    def load_agent_manifest(
        self,
        team_name: str,
        agent_name: str,
    ) -> dict[str, Any] | None:
        """Load a previously saved manifest, or None if missing."""
        manifest_path = self._resolve_manifest_path(team_name, agent_name)
        if not manifest_path.exists():
            return None
        # Refuse to read through a symlink — it could have been planted after
        # our resolve/containment check.
        if manifest_path.is_symlink():
            raise ValueError(
                f"manifest path is a symlink, refusing to read: {manifest_path}"
            )
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load manifest %s: %s", manifest_path, exc)
            return None

    def cleanup_agent_manifest(self, team_name: str, agent_name: str) -> bool:
        """Remove an agent's manifest file. Returns True if removed."""
        manifest_path = self._resolve_manifest_path(team_name, agent_name)
        if manifest_path.exists():
            # Refuse to unlink through a symlink — we might delete a file
            # outside the teams directory that the symlink points to.
            if manifest_path.is_symlink():
                raise ValueError(
                    f"manifest path is a symlink, refusing to unlink: {manifest_path}"
                )
            try:
                manifest_path.unlink()
                logger.info("Removed manifest for %s/%s", team_name, agent_name)
                return True
            except OSError as exc:
                logger.warning("Failed to remove manifest: %s", exc)
        return False
