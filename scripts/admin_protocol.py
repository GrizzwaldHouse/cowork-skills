# admin_protocol.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Multi-reviewer governance system for skill lifecycle management with audit trail

"""
Multi-reviewer governance system for skill lifecycle management.

Provides role-based access control (ADMIN / REVIEWER / OBSERVER), a
three-directory review pipeline (pending_review / approved / rejected),
and an append-only audit trail written to training_log.json.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from log_config import configure_logging
from sync_utils import atomic_write, backup_file

configure_logging()
logger = logging.getLogger("admin_protocol")

BASE_DIR = Path("C:/ClaudeSkills")


# ---------------------------------------------------------------------------
# Enums and data classes
# ---------------------------------------------------------------------------

class AdminRole(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


# Role hierarchy: higher numeric value = more permissions.
_ROLE_RANK: dict[AdminRole, int] = {
    AdminRole.OBSERVER: 0,
    AdminRole.REVIEWER: 1,
    AdminRole.ADMIN: 2,
}


@dataclass
class ReviewerProfile:
    user_id: str
    name: str
    role: AdminRole
    created_at: str
    last_active: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role.value,
            "created_at": self.created_at,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewerProfile:
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            role=AdminRole(data["role"]),
            created_at=data.get("created_at", ""),
            last_active=data.get("last_active", ""),
        )


@dataclass(frozen=True)
class ReviewAction:
    action: str  # "approve" | "reject" | "flag" | "comment"
    skill_id: str
    reviewer: str
    role: str
    comment: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "skill_id": self.skill_id,
            "reviewer": self.reviewer,
            "role": self.role,
            "comment": self.comment,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# AdminControlProtocol
# ---------------------------------------------------------------------------

class AdminControlProtocol:
    """Multi-reviewer governance system for skill lifecycle management."""

    def __init__(self, config: dict) -> None:
        self._config = config
        self._data_dir = BASE_DIR / "data"
        self._pending_dir = self._data_dir / "pending_review"
        self._approved_dir = self._data_dir / "approved"
        self._rejected_dir = self._data_dir / "rejected"
        self._audit_path = self._data_dir / "training_log.json"
        self._admin_config_path = BASE_DIR / "config" / "admin_config.json"

        # Ensure directories exist
        for d in (self._pending_dir, self._approved_dir, self._rejected_dir):
            d.mkdir(parents=True, exist_ok=True)

        self._reviewers: dict[str, ReviewerProfile] = self._load_reviewers()

    # ------------------------------------------------------------------
    # Reviewer management
    # ------------------------------------------------------------------

    def add_reviewer(self, profile: ReviewerProfile) -> None:
        """Register a new reviewer."""
        self._reviewers[profile.user_id] = profile
        self._save_reviewers()
        logger.info("Added reviewer %s (%s)", profile.user_id, profile.role.value)

    def remove_reviewer(self, user_id: str) -> None:
        """Remove a reviewer by user_id."""
        if user_id in self._reviewers:
            del self._reviewers[user_id]
            self._save_reviewers()
            logger.info("Removed reviewer %s", user_id)

    def get_reviewers(self) -> list[ReviewerProfile]:
        """Return all registered reviewers."""
        return list(self._reviewers.values())

    # ------------------------------------------------------------------
    # Review pipeline
    # ------------------------------------------------------------------

    def submit_for_review(self, skill_dict: dict, validation_dict: dict) -> None:
        """Submit a skill to the review queue based on validation result."""
        result = validation_dict.get("result", "needs_review")
        skill_id = skill_dict.get("skill_id", "")

        if result == "approved":
            self._save_to_dir(self._approved_dir, skill_id, skill_dict, validation_dict)
            self._append_audit(
                "auto_approved", skill_id, "system", "ADMIN",
                "Auto-approved by validation engine",
            )
        elif result == "needs_review":
            self._save_to_dir(self._pending_dir, skill_id, skill_dict, validation_dict)
            self._append_audit(
                "submitted_for_review", skill_id, "system", "ADMIN",
                "Awaiting manual review",
            )
        else:
            # Rejected
            self._save_to_dir(self._rejected_dir, skill_id, skill_dict, validation_dict)
            violations = validation_dict.get("violations", [])
            self._append_audit(
                "auto_rejected", skill_id, "system", "ADMIN",
                f"Rejected: {'; '.join(violations)}",
            )

    def approve(self, skill_id: str, reviewer_id: str) -> bool:
        """ADMIN only: Approve a pending skill."""
        if not self._check_role(reviewer_id, AdminRole.ADMIN):
            logger.warning("Reviewer %s lacks ADMIN role for approve", reviewer_id)
            return False

        if not self._move_skill(skill_id, self._pending_dir, self._approved_dir):
            return False

        self._append_audit("approved", skill_id, reviewer_id, "ADMIN", "Approved by admin")
        self._touch_reviewer(reviewer_id)
        logger.info("Skill %s approved by %s", skill_id, reviewer_id)
        return True

    def reject(self, skill_id: str, reviewer_id: str, reason: str) -> bool:
        """ADMIN only: Reject a pending skill."""
        if not self._check_role(reviewer_id, AdminRole.ADMIN):
            logger.warning("Reviewer %s lacks ADMIN role for reject", reviewer_id)
            return False

        # Load the skill data to add rejection reason before moving.
        source = self._pending_dir / f"{skill_id}.json"
        if not source.exists():
            logger.warning("Skill %s not found in pending queue", skill_id)
            return False

        data = json.loads(source.read_text(encoding="utf-8"))
        data["rejection_reason"] = reason
        data["rejected_by"] = reviewer_id
        data["rejected_at"] = datetime.now(timezone.utc).isoformat()
        atomic_write(source, json.dumps(data, indent=2, default=str) + "\n")

        if not self._move_skill(skill_id, self._pending_dir, self._rejected_dir):
            return False

        self._append_audit("rejected", skill_id, reviewer_id, "ADMIN", reason)
        self._touch_reviewer(reviewer_id)
        logger.info("Skill %s rejected by %s: %s", skill_id, reviewer_id, reason)
        return True

    def flag(self, skill_id: str, reviewer_id: str, reason: str) -> bool:
        """REVIEWER+: Flag a skill for attention."""
        if not self._check_role(reviewer_id, AdminRole.REVIEWER):
            logger.warning("Reviewer %s lacks REVIEWER role for flag", reviewer_id)
            return False

        source = self._pending_dir / f"{skill_id}.json"
        if not source.exists():
            logger.warning("Skill %s not found in pending queue for flagging", skill_id)
            return False

        data = json.loads(source.read_text(encoding="utf-8"))
        flags: list[dict[str, str]] = data.get("flags", [])
        flags.append({
            "reviewer": reviewer_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        data["flags"] = flags
        atomic_write(source, json.dumps(data, indent=2, default=str) + "\n")

        self._append_audit("flagged", skill_id, reviewer_id, "REVIEWER", reason)
        self._touch_reviewer(reviewer_id)
        logger.info("Skill %s flagged by %s: %s", skill_id, reviewer_id, reason)
        return True

    def comment(self, skill_id: str, reviewer_id: str, text: str) -> bool:
        """Any role: Add a comment to a skill."""
        if reviewer_id not in self._reviewers:
            logger.warning("Unknown reviewer %s", reviewer_id)
            return False

        # Look in all directories for the skill.
        source = self._find_skill_file(skill_id)
        if source is None:
            logger.warning("Skill %s not found for commenting", skill_id)
            return False

        data = json.loads(source.read_text(encoding="utf-8"))
        comments: list[dict[str, str]] = data.get("comments", [])
        comments.append({
            "reviewer": reviewer_id,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        data["comments"] = comments
        atomic_write(source, json.dumps(data, indent=2, default=str) + "\n")

        self._append_audit("comment", skill_id, reviewer_id,
                           self._reviewers[reviewer_id].role.value, text)
        self._touch_reviewer(reviewer_id)
        return True

    def get_pending_queue(self) -> list[dict]:
        """Return all skills awaiting review."""
        results: list[dict] = []
        if not self._pending_dir.exists():
            return results
        for path in sorted(self._pending_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                results.append(data)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to read pending skill %s: %s", path.name, exc)
        return results

    def get_audit_trail(self, skill_id: str | None = None) -> list[dict]:
        """Return audit trail, optionally filtered by skill_id."""
        entries: list[dict] = []
        if not self._audit_path.exists():
            return entries

        with self._audit_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if skill_id is None or entry.get("skill_id") == skill_id:
                    entries.append(entry)
        return entries

    def rollback_install(self, skill_id: str, admin_id: str) -> bool:
        """ADMIN only: Rollback a previously installed skill.

        Moves the skill from approved/ back to rejected/ with a rollback note.
        """
        if not self._check_role(admin_id, AdminRole.ADMIN):
            logger.warning("Reviewer %s lacks ADMIN role for rollback", admin_id)
            return False

        source = self._approved_dir / f"{skill_id}.json"
        if not source.exists():
            logger.warning("Skill %s not found in approved dir for rollback", skill_id)
            return False

        data = json.loads(source.read_text(encoding="utf-8"))
        data["rolled_back_by"] = admin_id
        data["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        atomic_write(source, json.dumps(data, indent=2, default=str) + "\n")

        if not self._move_skill(skill_id, self._approved_dir, self._rejected_dir):
            return False

        self._append_audit("rollback", skill_id, admin_id, "ADMIN",
                           "Rolled back installed skill")
        self._touch_reviewer(admin_id)
        logger.info("Skill %s rolled back by %s", skill_id, admin_id)
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_reviewers(self) -> dict[str, ReviewerProfile]:
        """Load reviewer profiles from admin_config.json."""
        reviewers: dict[str, ReviewerProfile] = {}
        if not self._admin_config_path.exists():
            return reviewers
        try:
            data = json.loads(self._admin_config_path.read_text(encoding="utf-8"))
            for entry in data.get("reviewers", []):
                profile = ReviewerProfile.from_dict(entry)
                reviewers[profile.user_id] = profile
        except (json.JSONDecodeError, OSError, KeyError) as exc:
            logger.warning("Failed to load admin config: %s", exc)
        return reviewers

    def _save_reviewers(self) -> None:
        """Persist reviewer profiles to admin_config.json."""
        # Load existing config to preserve other sections.
        config_data: dict[str, Any] = {}
        if self._admin_config_path.exists():
            try:
                config_data = json.loads(
                    self._admin_config_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                pass

        config_data["reviewers"] = [
            profile.to_dict() for profile in self._reviewers.values()
        ]
        self._admin_config_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(
            self._admin_config_path,
            json.dumps(config_data, indent=2, default=str) + "\n",
        )

    def _check_role(self, reviewer_id: str, min_role: AdminRole) -> bool:
        """Check if a reviewer has at least the minimum required role."""
        profile = self._reviewers.get(reviewer_id)
        if profile is None:
            return False
        return _ROLE_RANK[profile.role] >= _ROLE_RANK[min_role]

    def _save_to_dir(
        self,
        directory: Path,
        skill_id: str,
        skill_dict: dict,
        validation_dict: dict,
    ) -> None:
        """Save a combined skill + validation payload to a directory."""
        payload = {
            **skill_dict,
            "validation": validation_dict,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        dest = directory / f"{skill_id}.json"
        directory.mkdir(parents=True, exist_ok=True)
        atomic_write(dest, json.dumps(payload, indent=2, default=str) + "\n")
        logger.debug("Saved skill %s to %s", skill_id, directory.name)

    def _move_skill(self, skill_id: str, from_dir: Path, to_dir: Path) -> bool:
        """Move a skill JSON from one directory to another."""
        source = from_dir / f"{skill_id}.json"
        if not source.exists():
            logger.warning("Cannot move %s: not found in %s", skill_id, from_dir.name)
            return False

        dest = to_dir / f"{skill_id}.json"
        to_dir.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8")
        atomic_write(dest, content)
        source.unlink()
        logger.debug("Moved skill %s: %s -> %s", skill_id, from_dir.name, to_dir.name)
        return True

    def _append_audit(
        self,
        action: str,
        skill_id: str,
        reviewer: str,
        role: str,
        comment: str,
    ) -> None:
        """Append a single JSON-line entry to the audit trail."""
        entry = ReviewAction(
            action=action,
            skill_id=skill_id,
            reviewer=reviewer,
            role=role,
            comment=comment,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self._audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict(), default=str) + "\n")

    def _touch_reviewer(self, reviewer_id: str) -> None:
        """Update the last_active timestamp for a reviewer."""
        profile = self._reviewers.get(reviewer_id)
        if profile is not None:
            self._reviewers[reviewer_id] = ReviewerProfile(
                user_id=profile.user_id,
                name=profile.name,
                role=profile.role,
                created_at=profile.created_at,
                last_active=datetime.now(timezone.utc).isoformat(),
            )
            self._save_reviewers()

    def _find_skill_file(self, skill_id: str) -> Path | None:
        """Search all directories for a skill JSON file."""
        for directory in (self._pending_dir, self._approved_dir, self._rejected_dir):
            candidate = directory / f"{skill_id}.json"
            if candidate.exists():
                return candidate
        return None
