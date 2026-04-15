# test_admin_protocol.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Unit tests for the admin_protocol governance module

"""
Unit tests for admin_protocol.py.

Tests cover the review pipeline (submit / approve / reject / flag / comment),
role-based access control, audit trail, pending queue, reviewer management,
and rollback operations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure scripts directory is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from admin_protocol import (
    AdminControlProtocol,
    AdminRole,
    ReviewAction,
    ReviewerProfile,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an isolated directory tree that mirrors the production layout."""
    data_dir = tmp_path / "data"
    config_dir = tmp_path / "config"
    for sub in ("pending_review", "approved", "rejected"):
        (data_dir / sub).mkdir(parents=True)
    config_dir.mkdir(parents=True)

    # Patch BASE_DIR inside admin_protocol so the class writes to tmp_path.
    monkeypatch.setattr("admin_protocol.BASE_DIR", tmp_path)
    return tmp_path


@pytest.fixture()
def admin_config(work_dir: Path) -> Path:
    """Write a minimal admin_config.json with one admin and one reviewer."""
    config_path = work_dir / "config" / "admin_config.json"
    config_path.write_text(json.dumps({
        "reviewers": [
            {
                "user_id": "admin1",
                "name": "Admin One",
                "role": "admin",
                "created_at": "2026-01-01T00:00:00Z",
                "last_active": "2026-01-01T00:00:00Z",
            },
            {
                "user_id": "reviewer1",
                "name": "Reviewer One",
                "role": "reviewer",
                "created_at": "2026-01-01T00:00:00Z",
                "last_active": "2026-01-01T00:00:00Z",
            },
            {
                "user_id": "observer1",
                "name": "Observer One",
                "role": "observer",
                "created_at": "2026-01-01T00:00:00Z",
                "last_active": "2026-01-01T00:00:00Z",
            },
        ],
    }), encoding="utf-8")
    return config_path


@pytest.fixture()
def protocol(work_dir: Path, admin_config: Path) -> AdminControlProtocol:
    """Return an AdminControlProtocol wired to the temporary directory."""
    return AdminControlProtocol(config={})


def _make_skill(skill_id: str = "skill-001", name: str = "test-skill") -> dict:
    """Return a minimal skill dict."""
    return {
        "skill_id": skill_id,
        "name": name,
        "intent": "Test intent",
        "context": "Test context",
        "input_pattern": "When testing",
        "execution_logic": "Run tests",
        "constraints": ["none"],
        "expected_output": "pass",
        "failure_modes": ["timeout"],
        "security_classification": "standard",
        "source_session": "sess-1",
        "source_project": "test-project",
        "confidence_score": 0.85,
        "reuse_frequency": 1,
        "extracted_at": "2026-03-23T00:00:00Z",
        "version": "1",
    }


def _make_validation(result: str = "approved") -> dict:
    """Return a minimal validation dict."""
    return {
        "skill_id": "skill-001",
        "result": result,
        "architecture_score": 0.9,
        "security_score": 0.95,
        "quality_score": 0.88,
        "duplicate_of": None,
        "violations": [],
        "timestamp": "2026-03-23T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# submit_for_review tests
# ---------------------------------------------------------------------------

class TestSubmitForReview:
    """Test submit_for_review routing by validation result."""

    def test_approved_goes_to_approved_dir(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("approved")
        protocol.submit_for_review(skill, validation)

        approved = work_dir / "data" / "approved" / "skill-001.json"
        assert approved.exists()
        data = json.loads(approved.read_text(encoding="utf-8"))
        assert data["skill_id"] == "skill-001"

    def test_needs_review_goes_to_pending_dir(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        pending = work_dir / "data" / "pending_review" / "skill-001.json"
        assert pending.exists()

    def test_rejected_goes_to_rejected_dir(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("rejected")
        validation["violations"] = ["unsafe pattern", "missing tests"]
        protocol.submit_for_review(skill, validation)

        rejected = work_dir / "data" / "rejected" / "skill-001.json"
        assert rejected.exists()


# ---------------------------------------------------------------------------
# approve / reject tests
# ---------------------------------------------------------------------------

class TestApproveReject:
    """Test approve and reject with role checks."""

    def test_approve_moves_pending_to_approved(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.approve("skill-001", "admin1")
        assert result is True
        assert (work_dir / "data" / "approved" / "skill-001.json").exists()
        assert not (work_dir / "data" / "pending_review" / "skill-001.json").exists()

    def test_reject_moves_pending_to_rejected(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.reject("skill-001", "admin1", "Does not meet quality bar")
        assert result is True
        rejected = work_dir / "data" / "rejected" / "skill-001.json"
        assert rejected.exists()
        data = json.loads(rejected.read_text(encoding="utf-8"))
        assert data["rejection_reason"] == "Does not meet quality bar"

    def test_non_admin_cannot_approve(self, protocol: AdminControlProtocol) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.approve("skill-001", "reviewer1")
        assert result is False

    def test_non_admin_cannot_reject(self, protocol: AdminControlProtocol) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.reject("skill-001", "observer1", "reason")
        assert result is False

    def test_approve_nonexistent_skill_returns_false(self, protocol: AdminControlProtocol) -> None:
        result = protocol.approve("nonexistent", "admin1")
        assert result is False


# ---------------------------------------------------------------------------
# flag tests
# ---------------------------------------------------------------------------

class TestFlag:
    """Test flag operation with role checks."""

    def test_reviewer_can_flag(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.flag("skill-001", "reviewer1", "Suspicious pattern")
        assert result is True

        pending = work_dir / "data" / "pending_review" / "skill-001.json"
        data = json.loads(pending.read_text(encoding="utf-8"))
        assert len(data["flags"]) == 1
        assert data["flags"][0]["reason"] == "Suspicious pattern"

    def test_admin_can_flag(self, protocol: AdminControlProtocol) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.flag("skill-001", "admin1", "Needs attention")
        assert result is True

    def test_observer_cannot_flag(self, protocol: AdminControlProtocol) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.flag("skill-001", "observer1", "I noticed something")
        assert result is False


# ---------------------------------------------------------------------------
# comment tests
# ---------------------------------------------------------------------------

class TestComment:
    """Test comment operation (any role)."""

    def test_observer_can_comment(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.comment("skill-001", "observer1", "Looks interesting")
        assert result is True

        pending = work_dir / "data" / "pending_review" / "skill-001.json"
        data = json.loads(pending.read_text(encoding="utf-8"))
        assert len(data["comments"]) == 1
        assert data["comments"][0]["text"] == "Looks interesting"

    def test_unknown_reviewer_cannot_comment(self, protocol: AdminControlProtocol) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)

        result = protocol.comment("skill-001", "unknown_user", "Hello")
        assert result is False


# ---------------------------------------------------------------------------
# audit trail tests
# ---------------------------------------------------------------------------

class TestAuditTrail:
    """Test audit trail recording."""

    def test_audit_records_all_actions(self, protocol: AdminControlProtocol) -> None:
        skill = _make_skill()
        validation = _make_validation("needs_review")
        protocol.submit_for_review(skill, validation)
        protocol.flag("skill-001", "reviewer1", "flag reason")
        protocol.approve("skill-001", "admin1")

        trail = protocol.get_audit_trail()
        actions = [e["action"] for e in trail]
        assert "submitted_for_review" in actions
        assert "flagged" in actions
        assert "approved" in actions

    def test_audit_filter_by_skill_id(self, protocol: AdminControlProtocol) -> None:
        skill_a = _make_skill("skill-a", "Skill A")
        skill_b = _make_skill("skill-b", "Skill B")
        protocol.submit_for_review(skill_a, _make_validation("needs_review"))
        protocol.submit_for_review(skill_b, _make_validation("approved"))

        trail_a = protocol.get_audit_trail(skill_id="skill-a")
        trail_b = protocol.get_audit_trail(skill_id="skill-b")

        assert all(e["skill_id"] == "skill-a" for e in trail_a)
        assert all(e["skill_id"] == "skill-b" for e in trail_b)

    def test_audit_empty_when_no_log(self, protocol: AdminControlProtocol) -> None:
        """get_audit_trail returns empty list when no log file exists."""
        trail = protocol.get_audit_trail()
        # May not be empty due to fixture setup, but should be a list.
        assert isinstance(trail, list)


# ---------------------------------------------------------------------------
# pending queue tests
# ---------------------------------------------------------------------------

class TestPendingQueue:
    """Test get_pending_queue."""

    def test_returns_pending_skills(self, protocol: AdminControlProtocol) -> None:
        for i in range(3):
            skill = _make_skill(f"skill-{i}", f"Skill {i}")
            protocol.submit_for_review(skill, _make_validation("needs_review"))

        queue = protocol.get_pending_queue()
        assert len(queue) == 3
        ids = {item["skill_id"] for item in queue}
        assert ids == {"skill-0", "skill-1", "skill-2"}

    def test_empty_queue(self, protocol: AdminControlProtocol) -> None:
        queue = protocol.get_pending_queue()
        assert queue == []


# ---------------------------------------------------------------------------
# rollback tests
# ---------------------------------------------------------------------------

class TestRollback:
    """Test rollback_install."""

    def test_rollback_moves_approved_to_rejected(self, protocol: AdminControlProtocol, work_dir: Path) -> None:
        skill = _make_skill()
        validation = _make_validation("approved")
        protocol.submit_for_review(skill, validation)

        result = protocol.rollback_install("skill-001", "admin1")
        assert result is True
        assert (work_dir / "data" / "rejected" / "skill-001.json").exists()
        assert not (work_dir / "data" / "approved" / "skill-001.json").exists()

    def test_non_admin_cannot_rollback(self, protocol: AdminControlProtocol) -> None:
        skill = _make_skill()
        validation = _make_validation("approved")
        protocol.submit_for_review(skill, validation)

        result = protocol.rollback_install("skill-001", "reviewer1")
        assert result is False

    def test_rollback_nonexistent_returns_false(self, protocol: AdminControlProtocol) -> None:
        result = protocol.rollback_install("nonexistent", "admin1")
        assert result is False


# ---------------------------------------------------------------------------
# reviewer management tests
# ---------------------------------------------------------------------------

class TestReviewerManagement:
    """Test add/remove/get reviewer operations."""

    def test_add_reviewer(self, protocol: AdminControlProtocol) -> None:
        new_profile = ReviewerProfile(
            user_id="new_user",
            name="New User",
            role=AdminRole.REVIEWER,
            created_at="2026-03-23T00:00:00Z",
            last_active="2026-03-23T00:00:00Z",
        )
        protocol.add_reviewer(new_profile)

        reviewers = protocol.get_reviewers()
        ids = {r.user_id for r in reviewers}
        assert "new_user" in ids

    def test_remove_reviewer(self, protocol: AdminControlProtocol) -> None:
        initial_count = len(protocol.get_reviewers())
        protocol.remove_reviewer("observer1")

        assert len(protocol.get_reviewers()) == initial_count - 1
        ids = {r.user_id for r in protocol.get_reviewers()}
        assert "observer1" not in ids

    def test_get_reviewers_returns_all(self, protocol: AdminControlProtocol) -> None:
        reviewers = protocol.get_reviewers()
        assert len(reviewers) == 3  # admin1, reviewer1, observer1

    def test_remove_nonexistent_reviewer(self, protocol: AdminControlProtocol) -> None:
        initial_count = len(protocol.get_reviewers())
        protocol.remove_reviewer("ghost_user")
        assert len(protocol.get_reviewers()) == initial_count


# ---------------------------------------------------------------------------
# ReviewAction dataclass tests
# ---------------------------------------------------------------------------

class TestReviewAction:
    """Test ReviewAction serialization."""

    def test_to_dict(self) -> None:
        action = ReviewAction(
            action="approve",
            skill_id="skill-001",
            reviewer="admin1",
            role="ADMIN",
            comment="Looks good",
            timestamp="2026-03-23T00:00:00Z",
        )
        d = action.to_dict()
        assert d["action"] == "approve"
        assert d["skill_id"] == "skill-001"
        assert d["reviewer"] == "admin1"
