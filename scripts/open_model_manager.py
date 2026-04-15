# open_model_manager.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Install approved skills to the OpenModel and sync to GitHub

"""
OpenModel manager for the OwlWatcher intelligence pipeline.

Installs approved Quad Skills to all configured install targets,
manages SKILL.md generation, handles rollbacks via timestamped backups,
and triggers GitHub sync after installations.
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from log_config import configure_logging
from sync_utils import atomic_write, backup_file

configure_logging()
logger = logging.getLogger("open_model_manager")

BASE_DIR = Path("C:/ClaudeSkills")
BACKUP_DIR = BASE_DIR / "backups"


class OpenModelManager:
    """Installs approved skills and manages the OpenModel state."""

    INSTALL_TARGETS: list[Path] = [
        Path("C:/Users/daley/.claude/skills"),
        Path("C:/ClaudeSkills/skills"),
    ]

    def __init__(self, safety_guard_module: Any = None) -> None:
        """Initialize with optional safety guard reference."""
        self._safety_guard = safety_guard_module
        self._data_dir = BASE_DIR / "data"
        self._approved_dir = self._data_dir / "approved"
        self._training_log = self._data_dir / "training_log.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def install_skill(self, skill_dict: dict, validation_dict: dict | None = None) -> bool:
        """Install an approved skill to all install targets.

        Steps:
        1. Run safety guard check if available
        2. Create skill directory in each install target
        3. Write SKILL.md from skill dict
        4. Update training log
        5. Trigger GitHub sync
        """
        skill_id = skill_dict.get("skill_id", "unknown")
        skill_name = skill_dict.get("name", skill_id)

        # 1. Safety guard check
        if self._safety_guard is not None:
            try:
                result = self._safety_guard.check_install(skill_dict, validation_dict)
                if result and getattr(result, "level", None) in ("CRITICAL", "HIGH"):
                    logger.warning(
                        "Safety guard blocked install of %s: %s",
                        skill_id, getattr(result, "detail", "blocked"),
                    )
                    self._append_training_log(
                        "install_blocked", skill_id,
                        f"Safety guard blocked: {getattr(result, 'detail', 'blocked')}",
                    )
                    return False
            except Exception as exc:
                logger.error("Safety guard check failed for %s: %s", skill_id, exc)
                return False

        # 2-3. Install to each target
        md_content = self._generate_skill_md(skill_dict)
        installed_to: list[str] = []

        for target in self.INSTALL_TARGETS:
            if not target.exists():
                logger.debug("Install target %s does not exist, skipping", target)
                continue

            skill_dir = target / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"

            # Backup existing file before overwrite
            if skill_path.exists():
                backup_file(skill_path)

            atomic_write(skill_path, md_content)
            installed_to.append(str(target))
            logger.info("Installed skill %s to %s", skill_name, target)

        if not installed_to:
            logger.warning("No install targets available for skill %s", skill_id)
            self._append_training_log(
                "install_failed", skill_id, "No install targets available",
            )
            return False

        # 4. Update training log
        self._append_training_log(
            "installed", skill_id,
            f"Installed to {len(installed_to)} target(s): {', '.join(installed_to)}",
        )

        # 5. Trigger GitHub sync
        self.sync_to_github()

        return True

    def uninstall_skill(self, skill_id: str) -> bool:
        """Remove an installed skill from all targets."""
        removed_from: list[str] = []

        for target in self.INSTALL_TARGETS:
            if not target.exists():
                continue

            # Search for directories matching the skill_id or skill name.
            for child in target.iterdir():
                if child.is_dir() and child.name == skill_id:
                    # Backup before removal
                    skill_md = child / "SKILL.md"
                    if skill_md.exists():
                        backup_file(skill_md)
                    shutil.rmtree(str(child), ignore_errors=True)
                    removed_from.append(str(target))
                    logger.info("Uninstalled skill %s from %s", skill_id, target)

        if not removed_from:
            logger.warning("Skill %s not found in any install target", skill_id)
            return False

        self._append_training_log(
            "uninstalled", skill_id,
            f"Removed from {len(removed_from)} target(s)",
        )
        self.sync_to_github()
        return True

    def update_memory(self, project: str, patterns: list[str]) -> bool:
        """Append patterns to project's MEMORY.md."""
        memory_dir = Path(f"C:/Users/daley/.claude/projects/{project}/memory")
        memory_path = memory_dir / "MEMORY.md"

        if not memory_dir.exists():
            logger.warning("Memory directory not found for project %s", project)
            return False

        existing = ""
        if memory_path.exists():
            existing = memory_path.read_text(encoding="utf-8")

        new_lines: list[str] = []
        for pattern in patterns:
            if pattern not in existing:
                new_lines.append(f"- {pattern}")

        if not new_lines:
            logger.debug("No new patterns to add for project %s", project)
            return True

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        section = f"\n## Learned Patterns ({timestamp})\n" + "\n".join(new_lines) + "\n"
        atomic_write(memory_path, existing + section)
        logger.info("Updated MEMORY.md for project %s with %d patterns", project, len(new_lines))
        return True

    def sync_to_github(self) -> bool:
        """Trigger GitHub sync for the ClaudeSkills repo."""
        try:
            from github_sync import sync as github_sync
            result = github_sync(dry_run=False)
            if result:
                logger.info("GitHub sync completed successfully")
                self._append_training_log("github_sync", "all", "Sync successful")
            else:
                logger.warning("GitHub sync reported failure")
                self._append_training_log("github_sync", "all", "Sync failed")
            return result
        except ImportError:
            logger.debug("github_sync module not available, skipping sync")
            return False
        except Exception as exc:
            logger.error("GitHub sync error: %s", exc)
            self._append_training_log("github_sync_error", "all", str(exc))
            return False

    def rollback(self, skill_id: str) -> bool:
        """Rollback a skill installation using backups."""
        if not BACKUP_DIR.exists():
            logger.warning("Backup directory does not exist")
            return False

        # Find the most recent backup containing this skill.
        # Backups are stored as {BACKUP_DIR}/{timestamp}/{relative_path}
        backup_timestamps = sorted(
            [d for d in BACKUP_DIR.iterdir() if d.is_dir()],
            reverse=True,
        )

        for ts_dir in backup_timestamps:
            # Search for skill files in this backup timestamp.
            for skill_file in ts_dir.rglob("*.md"):
                if skill_id in str(skill_file):
                    # Found a backup -- determine original location from relative path.
                    # The backup structure mirrors the original path relative to BASE_DIR.
                    rel_parts = skill_file.relative_to(ts_dir)
                    original = BASE_DIR / rel_parts

                    original.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(skill_file), str(original))
                    logger.info(
                        "Rolled back skill %s from backup %s",
                        skill_id, ts_dir.name,
                    )
                    self._append_training_log(
                        "rollback", skill_id,
                        f"Restored from backup {ts_dir.name}",
                    )
                    return True

        logger.warning("No backup found for skill %s", skill_id)
        return False

    def get_installed_skills(self) -> list[dict]:
        """List all currently installed Quad Skills."""
        skills: list[dict] = []
        seen: set[str] = set()

        for target in self.INSTALL_TARGETS:
            if not target.exists():
                continue
            for child in sorted(target.iterdir()):
                if not child.is_dir():
                    continue
                skill_md = child / "SKILL.md"
                if not skill_md.exists():
                    continue
                if child.name in seen:
                    continue
                seen.add(child.name)

                # Parse YAML front matter for metadata.
                content = skill_md.read_text(encoding="utf-8")
                meta = self._parse_front_matter(content)
                meta["name"] = meta.get("name", child.name)
                meta["install_path"] = str(child)
                skills.append(meta)

        return skills

    def get_model_state(self) -> dict:
        """Return a snapshot of the current OpenModel state."""
        installed = self.get_installed_skills()
        approved_count = len(list(self._approved_dir.glob("*.json"))) if self._approved_dir.exists() else 0

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "installed_skill_count": len(installed),
            "installed_skills": [s.get("name", "unknown") for s in installed],
            "approved_pending_install": approved_count,
            "install_targets": [str(t) for t in self.INSTALL_TARGETS],
            "install_targets_available": [str(t) for t in self.INSTALL_TARGETS if t.exists()],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_skill_md(self, skill_dict: dict) -> str:
        """Convert skill dict to SKILL.md format with YAML front matter."""
        name = skill_dict.get("name", "Unnamed Skill")
        intent = skill_dict.get("intent", "")
        version = skill_dict.get("version", "1")
        confidence = skill_dict.get("confidence_score", 0.0)
        security = skill_dict.get("security_classification", "standard")
        source_project = skill_dict.get("source_project", "")
        extracted_at = skill_dict.get("extracted_at", "")
        context = skill_dict.get("context", "")
        input_pattern = skill_dict.get("input_pattern", "")
        execution_logic = skill_dict.get("execution_logic", "")
        constraints = skill_dict.get("constraints", "")
        expected_output = skill_dict.get("expected_output", "")
        failure_modes = skill_dict.get("failure_modes", "")

        # Build constraints bullet list
        if isinstance(constraints, list):
            constraints_text = "\n".join(f"- {c}" for c in constraints)
        else:
            constraints_text = str(constraints)

        # Build failure modes bullet list
        if isinstance(failure_modes, list):
            failures_text = "\n".join(f"- {f}" for f in failure_modes)
        else:
            failures_text = str(failure_modes)

        return (
            f"---\n"
            f"name: {name}\n"
            f"description: {intent}\n"
            f"user-invocable: false\n"
            f"quad-version: {version}\n"
            f"confidence: {confidence}\n"
            f"security: {security}\n"
            f"source-project: {source_project}\n"
            f"extracted-at: {extracted_at}\n"
            f"---\n"
            f"# {name}\n\n"
            f"## Context\n{context}\n\n"
            f"## When to Use\n{input_pattern}\n\n"
            f"## Logic\n{execution_logic}\n\n"
            f"## Constraints\n{constraints_text}\n\n"
            f"## Expected Output\n{expected_output}\n\n"
            f"## Known Failure Modes\n{failures_text}\n"
        )

    def _append_training_log(self, action: str, skill_id: str, details: str) -> None:
        """Log action to training_log.json as an append-only JSON line."""
        entry = {
            "action": action,
            "skill_id": skill_id,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._training_log.parent.mkdir(parents=True, exist_ok=True)
        with self._training_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")

    @staticmethod
    def _parse_front_matter(content: str) -> dict[str, str]:
        """Extract YAML-like front matter from SKILL.md content."""
        meta: dict[str, str] = {}
        if not content.startswith("---"):
            return meta
        lines = content.split("\n")
        in_front_matter = False
        for line in lines:
            if line.strip() == "---":
                if in_front_matter:
                    break
                in_front_matter = True
                continue
            if in_front_matter and ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
        return meta
