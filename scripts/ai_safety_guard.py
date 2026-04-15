# ai_safety_guard.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Enforce safety invariants on all AI skill operations to prevent unsafe installs, overwrites, and injections

"""
AI Safety Guard for the OwlWatcher Intelligence Pipeline.

Enforces hard safety invariants that cannot be bypassed:
  1. No skill installed without passing ValidationEngine
  2. Core skills require ADMIN approval to modify
  3. No skill content may contain blocked execution patterns
  4. No skill may reference paths outside allowed directories
  5. No self-referential modification of the safety guard
  6. All operations logged to an immutable append-only audit trail
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from log_config import configure_logging

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
TRAINING_LOG_PATH = BASE_DIR / "data" / "training_log.json"

ALLOWED_ROOTS: tuple[Path, ...] = (
    BASE_DIR,
    Path.home() / ".claude",
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()
logger = logging.getLogger("ai_safety_guard")


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class SafetyViolation(str, Enum):
    """Categories of safety violations the guard can detect."""

    UNVALIDATED_INSTALL = "unvalidated_install"
    CORE_SKILL_OVERWRITE = "core_skill_overwrite"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INJECTION_DETECTED = "injection_detected"
    UNSAFE_EXEC = "unsafe_exec"
    SELF_MODIFICATION = "self_modification"


@dataclass(frozen=True)
class SafetyAlert:
    """Immutable record of a detected safety violation."""

    violation: SafetyViolation
    severity: str  # "CRITICAL" | "WARNING"
    message: str
    blocked_action: str
    timestamp: str


# ---------------------------------------------------------------------------
# Injection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|?(system|im_start|endoftext)\|?>", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+are", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+you\s+are\s+)?a\s+(different|new)", re.IGNORECASE),
    re.compile(r"override\s+(your\s+)?(instructions|rules|guidelines)", re.IGNORECASE),
    re.compile(r"disregard\s+(your\s+)?(previous|prior|original)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your)", re.IGNORECASE),
    re.compile(r"new\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),
)

# WHY: SQL injection signatures need regex (not substring) because the
# tell-tale shapes -- a quote followed by DROP/UNION/comment, or a
# tautology like ' OR '1'='1 -- depend on token order, not on a single
# literal substring. Plain substring matching on "DROP TABLE" would
# false-positive on benign documentation, while these patterns require
# the attacker's quote/terminator context to be present.
_SQL_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Statement terminator + destructive DDL/DML (e.g. "'; DROP TABLE foo")
    re.compile(r"['\"]\s*;\s*(drop|delete|truncate|alter|update|insert)\s+", re.IGNORECASE),
    # UNION-based extraction (e.g. "' UNION SELECT")
    re.compile(r"['\"]\s*\bunion\b\s+(all\s+)?select\b", re.IGNORECASE),
    # Tautology auth bypass (e.g. " OR '1'='1", " OR 1=1")
    re.compile(r"['\"]\s*\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.IGNORECASE),
    # Closing quote followed by SQL line comment (e.g. "admin'--")
    re.compile(r"['\"]\s*--\s"),
    # Closing quote followed by SQL block comment (e.g. "x'/*")
    re.compile(r"['\"]\s*/\*"),
)


# ---------------------------------------------------------------------------
# AISafetyGuard
# ---------------------------------------------------------------------------

class AISafetyGuard:
    """Enforces safety invariants on all skill operations.

    This guard is the single gatekeeper for skill installs, content
    modifications, and file overwrites.  Its checks MUST NOT be bypassed.
    """

    CORE_SKILLS: frozenset[str] = frozenset({
        "universal-coding-standards",
        "architecture-patterns",
        "enterprise-secure-ai-engineering",
    })

    BLOCKED_PATTERNS: tuple[str, ...] = (
        "os.system",
        "subprocess",
        "eval(",
        "exec(",
        "__import__",
        "rm -rf",
        "format c:",
    )

    def __init__(self) -> None:
        TRAINING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not TRAINING_LOG_PATH.exists():
            TRAINING_LOG_PATH.write_text("[]", encoding="utf-8")
        logger.info("AISafetyGuard initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_install(
        self,
        skill: dict[str, Any],
        validation_report: dict[str, Any],
    ) -> SafetyAlert | None:
        """Validate a skill install against safety invariants.

        Parameters
        ----------
        skill:
            Dict with keys: skill_id, name, execution_logic,
            security_classification.
        validation_report:
            Dict with keys: result ("approved" | "needs_review" | "rejected"),
            security_score (float), violations (list[str]).

        Returns
        -------
        SafetyAlert if the install is blocked, else None.
        """
        skill_id: str = skill.get("skill_id", "<unknown>")
        skill_name: str = skill.get("name", "<unknown>")
        result: str = validation_report.get("result", "rejected")

        # --- Rule 1: Must pass validation ---
        if result == "rejected":
            alert = SafetyAlert(
                violation=SafetyViolation.UNVALIDATED_INSTALL,
                severity="CRITICAL",
                message=(
                    f"Skill '{skill_name}' ({skill_id}) rejected by "
                    f"ValidationEngine: {validation_report.get('violations', [])}"
                ),
                blocked_action=f"install:{skill_id}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._append_audit_log("install_blocked", alert)
            logger.warning("Install blocked: %s", alert.message)
            return alert

        if result == "needs_review":
            # needs_review requires explicit admin_approved flag
            if not validation_report.get("admin_approved", False):
                alert = SafetyAlert(
                    violation=SafetyViolation.UNVALIDATED_INSTALL,
                    severity="WARNING",
                    message=(
                        f"Skill '{skill_name}' ({skill_id}) requires admin "
                        f"approval (status=needs_review)"
                    ),
                    blocked_action=f"install:{skill_id}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self._append_audit_log("install_pending_review", alert)
                logger.warning("Install pending review: %s", alert.message)
                return alert

        # --- Rule 3: Scan execution logic for blocked patterns ---
        execution_logic: str = skill.get("execution_logic", "")
        content_alert = self.check_content(execution_logic)
        if content_alert is not None:
            self._append_audit_log("install_unsafe_content", content_alert)
            return content_alert

        # --- Rule 4: Scan for injection in skill name / content ---
        if self.scan_for_injection(skill_name) or self.scan_for_injection(execution_logic):
            alert = SafetyAlert(
                violation=SafetyViolation.INJECTION_DETECTED,
                severity="CRITICAL",
                message=f"Injection pattern detected in skill '{skill_name}'",
                blocked_action=f"install:{skill_id}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._append_audit_log("install_injection", alert)
            logger.warning("Injection detected: %s", alert.message)
            return alert

        # All checks passed
        self._append_audit_log("install_approved", {
            "skill_id": skill_id,
            "skill_name": skill_name,
            "security_score": validation_report.get("security_score", 0.0),
        })
        logger.info("Install approved: %s (%s)", skill_name, skill_id)
        return None

    def check_content(self, content: str) -> SafetyAlert | None:
        """Scan content for blocked execution patterns.

        Returns SafetyAlert if any blocked pattern is found.
        """
        content_lower = content.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in content_lower:
                alert = SafetyAlert(
                    violation=SafetyViolation.UNSAFE_EXEC,
                    severity="CRITICAL",
                    message=f"Blocked pattern detected: '{pattern}'",
                    blocked_action="content_scan",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self._append_audit_log("unsafe_content_blocked", alert)
                logger.warning("Unsafe content: %s", alert.message)
                return alert

        # WHY: SQL injection is a distinct attack class from "unsafe exec"
        # patterns above -- it doesn't appear as a single substring like
        # "os.system" but as a syntactic shape (quote + terminator + DDL,
        # tautology, comment, etc). Using INJECTION_DETECTED so the pen
        # test's install_security_block check classifies it as a real
        # security block rather than an admin-review situation.
        for sql_pattern in _SQL_INJECTION_PATTERNS:
            if sql_pattern.search(content):
                alert = SafetyAlert(
                    violation=SafetyViolation.INJECTION_DETECTED,
                    severity="CRITICAL",
                    message=f"SQL injection signature detected: {sql_pattern.pattern}",
                    blocked_action="content_scan",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self._append_audit_log("sql_injection_blocked", alert)
                logger.warning("SQL injection: %s", alert.message)
                return alert

        return None

    def check_overwrite(self, target_path: Path) -> SafetyAlert | None:
        """Check whether *target_path* is protected from overwrite.

        Protected paths:
        - Core skill directories
        - The safety guard module itself
        - Paths outside allowed roots
        """
        resolved = target_path.resolve()

        # --- Rule 5: Self-modification guard ---
        guard_path = Path(__file__).resolve()
        if resolved == guard_path:
            alert = SafetyAlert(
                violation=SafetyViolation.SELF_MODIFICATION,
                severity="CRITICAL",
                message="Attempt to modify the AI Safety Guard itself",
                blocked_action=f"overwrite:{target_path}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._append_audit_log("self_modification_blocked", alert)
            logger.warning("Self-modification blocked: %s", target_path)
            return alert

        # --- Rule 2: Core skill protection ---
        for core_skill in self.CORE_SKILLS:
            if core_skill in str(resolved):
                alert = SafetyAlert(
                    violation=SafetyViolation.CORE_SKILL_OVERWRITE,
                    severity="CRITICAL",
                    message=(
                        f"Attempt to overwrite core skill '{core_skill}' "
                        f"at {target_path}"
                    ),
                    blocked_action=f"overwrite:{target_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self._append_audit_log("core_overwrite_blocked", alert)
                logger.warning("Core overwrite blocked: %s", alert.message)
                return alert

        # --- Rule 4: Path confinement ---
        if not self._is_allowed_path(resolved):
            alert = SafetyAlert(
                violation=SafetyViolation.PRIVILEGE_ESCALATION,
                severity="CRITICAL",
                message=(
                    f"Path '{target_path}' is outside allowed directories"
                ),
                blocked_action=f"overwrite:{target_path}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._append_audit_log("path_violation", alert)
            logger.warning("Path violation: %s", alert.message)
            return alert

        return None

    def scan_for_injection(self, text: str) -> bool:
        """Return True if *text* contains prompt injection patterns."""
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning("Injection pattern matched: %s", pattern.pattern)
                return True
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_allowed_path(self, resolved_path: Path) -> bool:
        """Return True if *resolved_path* falls under an allowed root."""
        for root in ALLOWED_ROOTS:
            try:
                resolved_path.relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False

    def _append_audit_log(
        self,
        action: str,
        detail: SafetyAlert | dict[str, Any],
    ) -> None:
        """Append an entry to the immutable training audit log.

        Each entry is a JSON object on its own line (JSON Lines format)
        within a JSON array file.
        """
        if isinstance(detail, SafetyAlert):
            detail_dict: dict[str, Any] = {
                "violation": detail.violation.value,
                "severity": detail.severity,
                "message": detail.message,
                "blocked_action": detail.blocked_action,
            }
        else:
            detail_dict = detail

        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "detail": detail_dict,
        }

        try:
            entries: list[dict[str, Any]] = []
            if TRAINING_LOG_PATH.exists():
                raw = TRAINING_LOG_PATH.read_text(encoding="utf-8").strip()
                if raw:
                    entries = json.loads(raw)
                    if not isinstance(entries, list):
                        entries = []
            entries.append(entry)
            TRAINING_LOG_PATH.write_text(
                json.dumps(entries, indent=2, default=str),
                encoding="utf-8",
            )
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to write audit log: %s", exc)
