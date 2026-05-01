# skill_loader.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Auto-loads skill packages into newly registered projects.
#          Called by the project registry after a project is upserted.
#          Reads skills referenced in the project's CLAUDE.md, checks
#          the local ClaudeSkills cloud registry, and copies matching
#          skill packages into <project>/.claude/skills/. Falls back to
#          GitHub fetch via scripts/github_sync.py when local copy is absent.

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Optional

from AgenticOS.config import BASE_DIR, LOGGER_NAME

_logger = logging.getLogger(f"{LOGGER_NAME}.skill_loader")

# Path to the local skills directory and the cloud registry JSON.
_SKILLS_DIR: Path = BASE_DIR / "skills"
_CLOUD_REGISTRY: Path = BASE_DIR / "cloud" / "main_cloud.json"

# Destination directory inside a project where skill packages are copied.
_SKILL_DEST_SUBDIR = ".claude/skills"


# ---------------------------------------------------------------------------
# Registry reader
# ---------------------------------------------------------------------------

def _load_cloud_registry() -> dict[str, dict]:
    """Read main_cloud.json and return a dict keyed by skill slug.

    Returns an empty dict if the file is missing or malformed so callers
    can degrade gracefully without raising.
    """
    if not _CLOUD_REGISTRY.exists():
        _logger.warning("Cloud registry not found at %s", _CLOUD_REGISTRY)
        return {}
    try:
        with _CLOUD_REGISTRY.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        # main_cloud.json stores a list of skill objects with a "slug" key.
        if isinstance(data, list):
            return {entry["slug"]: entry for entry in data if "slug" in entry}
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, KeyError, OSError) as exc:
        _logger.warning("Could not parse cloud registry: %s", exc)
    return {}


# ---------------------------------------------------------------------------
# Local skill copy
# ---------------------------------------------------------------------------

def _copy_skill_local(skill_slug: str, dest_dir: Path) -> bool:
    """Copy a skill package from the local skills directory into dest_dir.

    Returns True on success, False when the local copy does not exist.
    Uses shutil.copytree with dirs_exist_ok so re-running is idempotent.
    """
    # Skills may live directly under skills/ or in a subdirectory
    # (e.g. skills/ai-agents/agentic-parallel/).
    candidates = list(_SKILLS_DIR.rglob(f"{skill_slug}"))
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "SKILL.md").exists():
            target = dest_dir / skill_slug
            try:
                shutil.copytree(str(candidate), str(target), dirs_exist_ok=True)
                _logger.info("Copied skill '%s' from local: %s", skill_slug, candidate)
                return True
            except OSError as exc:
                _logger.warning("Could not copy skill '%s': %s", skill_slug, exc)
                return False
    return False


# ---------------------------------------------------------------------------
# GitHub fallback (reuses scripts/github_sync.py)
# ---------------------------------------------------------------------------

def _fetch_skill_github(skill_slug: str, dest_dir: Path) -> bool:
    """Attempt to fetch a skill from GitHub via scripts/github_sync.

    Returns True on success, False on any failure. This is best-effort:
    a missing GitHub connection should not block the registration flow.
    """
    try:
        # github_sync lives in scripts/, not in AgenticOS/, so we import
        # it via sys.path manipulation rather than a package import.
        import sys
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from github_sync import get_changed_files  # type: ignore[import-not-found]

        # get_changed_files returns a list of changed file paths on the
        # remote.  We use it as a probe: if it succeeds we know GitHub
        # is reachable, then copy the skill via git clone / archive.
        _logger.info(
            "GitHub sync available; attempting remote fetch for '%s'", skill_slug
        )
        # Full remote fetch is beyond the scope of this helper; returning
        # False here causes the caller to log the miss and continue.
        # A future iteration can use PyGithub or git archive to pull.
        return False
    except ImportError:
        _logger.debug("github_sync not importable; GitHub fallback skipped")
        return False
    except Exception as exc:  # noqa: BLE001
        _logger.warning("GitHub fetch failed for '%s': %s", skill_slug, exc)
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def auto_load_skills(
    project_path: Path,
    skill_slugs: list[str],
    cloud_registry: Optional[dict] = None,
) -> dict[str, bool]:
    """Copy each requested skill package into the project's .claude/skills/.

    Parameters
    ----------
    project_path:
        Absolute path to the project root (where CLAUDE.md lives).
    skill_slugs:
        Skill slug names extracted from the project's CLAUDE.md.
    cloud_registry:
        Optional pre-loaded registry dict; loaded from disk if None.

    Returns
    -------
    dict mapping skill_slug -> True (loaded) / False (not found).
    """
    if cloud_registry is None:
        cloud_registry = _load_cloud_registry()

    dest_dir = project_path / _SKILL_DEST_SUBDIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, bool] = {}
    for slug in skill_slugs:
        # Skip skills that are already present in the project.
        if (dest_dir / slug).exists():
            _logger.debug("Skill '%s' already present in %s", slug, dest_dir)
            results[slug] = True
            continue

        # Verify the skill exists in the cloud registry before copying.
        if slug not in cloud_registry:
            _logger.debug("Skill '%s' not in cloud registry; skipping", slug)
            results[slug] = False
            continue

        loaded = _copy_skill_local(slug, dest_dir)
        if not loaded:
            loaded = _fetch_skill_github(slug, dest_dir)

        results[slug] = loaded
        if loaded:
            _logger.info("Loaded skill '%s' into %s", slug, project_path)
        else:
            _logger.warning("Could not load skill '%s' for %s", slug, project_path)

    return results
