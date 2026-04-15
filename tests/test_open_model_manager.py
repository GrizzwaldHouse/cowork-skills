# test_open_model_manager.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Unit tests for the open_model_manager module

"""
Unit tests for open_model_manager.py.

Tests cover skill installation, uninstallation, SKILL.md generation,
rollback from backups, training log updates, safety guard blocking,
model state reporting, and installed skill listing.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts directory is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from open_model_manager import OpenModelManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an isolated directory tree mirroring production layout."""
    data_dir = tmp_path / "data"
    (data_dir / "approved").mkdir(parents=True)
    (tmp_path / "backups").mkdir(parents=True)

    # Patch BASE_DIR and BACKUP_DIR
    monkeypatch.setattr("open_model_manager.BASE_DIR", tmp_path)
    monkeypatch.setattr("open_model_manager.BACKUP_DIR", tmp_path / "backups")
    return tmp_path


@pytest.fixture()
def install_targets(tmp_path: Path) -> list[Path]:
    """Create two temporary install target directories."""
    t1 = tmp_path / "target_a" / "skills"
    t2 = tmp_path / "target_b" / "skills"
    t1.mkdir(parents=True)
    t2.mkdir(parents=True)
    return [t1, t2]


@pytest.fixture()
def manager(work_dir: Path, install_targets: list[Path], monkeypatch: pytest.MonkeyPatch) -> OpenModelManager:
    """Return an OpenModelManager wired to temporary directories."""
    mgr = OpenModelManager(safety_guard_module=None)
    monkeypatch.setattr(type(mgr), "INSTALL_TARGETS", install_targets)
    return mgr


def _make_skill(
    skill_id: str = "skill-001",
    name: str = "test-skill",
) -> dict[str, Any]:
    """Return a minimal skill dict."""
    return {
        "skill_id": skill_id,
        "name": name,
        "intent": "Test intent",
        "context": "Test context",
        "input_pattern": "When testing",
        "execution_logic": "Run tests",
        "constraints": ["constraint-a", "constraint-b"],
        "expected_output": "All tests pass",
        "failure_modes": ["timeout", "missing dep"],
        "security_classification": "standard",
        "source_session": "sess-1",
        "source_project": "test-project",
        "confidence_score": 0.85,
        "reuse_frequency": 1,
        "extracted_at": "2026-03-23T00:00:00Z",
        "version": "1",
    }


# ---------------------------------------------------------------------------
# install_skill tests
# ---------------------------------------------------------------------------

class TestInstallSkill:
    """Test install_skill creates SKILL.md in target directories."""

    def test_creates_skill_md_in_targets(
        self, manager: OpenModelManager, install_targets: list[Path]
    ) -> None:
        skill = _make_skill()

        with patch.object(manager, "sync_to_github", return_value=True):
            result = manager.install_skill(skill)

        assert result is True
        for target in install_targets:
            skill_md = target / "test-skill" / "SKILL.md"
            assert skill_md.exists()
            content = skill_md.read_text(encoding="utf-8")
            assert "name: test-skill" in content
            assert "## Context" in content

    def test_blocked_by_safety_guard(self, work_dir: Path, install_targets: list[Path], monkeypatch: pytest.MonkeyPatch) -> None:
        mock_guard = MagicMock()
        alert = MagicMock()
        alert.level = "CRITICAL"
        alert.detail = "Dangerous pattern detected"
        mock_guard.check_install.return_value = alert

        mgr = OpenModelManager(safety_guard_module=mock_guard)
        monkeypatch.setattr(type(mgr), "INSTALL_TARGETS", install_targets)

        skill = _make_skill()
        result = mgr.install_skill(skill, {"result": "approved"})

        assert result is False
        # SKILL.md should NOT be created
        for target in install_targets:
            assert not (target / "test-skill" / "SKILL.md").exists()

    def test_no_targets_available(self, work_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = OpenModelManager()
        # Point to non-existent targets
        monkeypatch.setattr(
            type(mgr), "INSTALL_TARGETS",
            [Path("/nonexistent/a"), Path("/nonexistent/b")],
        )

        with patch.object(mgr, "sync_to_github", return_value=True):
            result = mgr.install_skill(_make_skill())

        assert result is False

    def test_backs_up_existing_skill(
        self, manager: OpenModelManager, install_targets: list[Path]
    ) -> None:
        # Pre-create an existing SKILL.md
        skill_dir = install_targets[0] / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        existing = skill_dir / "SKILL.md"
        existing.write_text("old content", encoding="utf-8")

        with patch("open_model_manager.backup_file") as mock_backup, \
             patch.object(manager, "sync_to_github", return_value=True):
            manager.install_skill(_make_skill())

        mock_backup.assert_called()

    def test_updates_training_log(
        self, manager: OpenModelManager, work_dir: Path
    ) -> None:
        with patch.object(manager, "sync_to_github", return_value=True):
            manager.install_skill(_make_skill())

        log_path = work_dir / "data" / "training_log.json"
        assert log_path.exists()
        lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["action"] == "installed"


# ---------------------------------------------------------------------------
# uninstall_skill tests
# ---------------------------------------------------------------------------

class TestUninstallSkill:
    """Test uninstall_skill removes skill from targets."""

    def test_removes_from_targets(
        self, manager: OpenModelManager, install_targets: list[Path]
    ) -> None:
        # First install
        with patch.object(manager, "sync_to_github", return_value=True):
            manager.install_skill(_make_skill())

        # Then uninstall (mock backup_file to avoid path resolution issues in temp dirs)
        with patch.object(manager, "sync_to_github", return_value=True), \
             patch("open_model_manager.backup_file", return_value=None):
            result = manager.uninstall_skill("test-skill")

        assert result is True
        for target in install_targets:
            assert not (target / "test-skill").exists()

    def test_uninstall_nonexistent(self, manager: OpenModelManager) -> None:
        result = manager.uninstall_skill("nonexistent-skill")
        assert result is False


# ---------------------------------------------------------------------------
# rollback tests
# ---------------------------------------------------------------------------

class TestRollback:
    """Test rollback restores from backup."""

    def test_rollback_restores_backup(
        self, manager: OpenModelManager, work_dir: Path, install_targets: list[Path]
    ) -> None:
        # Create a fake backup structure
        backup_ts = work_dir / "backups" / "20260323T000000Z"
        # Backup mirrors the relative path from BASE_DIR
        rel_target = install_targets[0].relative_to(work_dir.parent)
        backup_skill = backup_ts / rel_target / "test-skill" / "SKILL.md"
        backup_skill.parent.mkdir(parents=True)
        backup_skill.write_text("---\nname: old-backup\n---\n# Old\n", encoding="utf-8")

        result = manager.rollback("test-skill")
        assert result is True

    def test_rollback_no_backup(self, manager: OpenModelManager) -> None:
        result = manager.rollback("ghost-skill")
        assert result is False


# ---------------------------------------------------------------------------
# get_installed_skills tests
# ---------------------------------------------------------------------------

class TestGetInstalledSkills:
    """Test listing installed skills."""

    def test_lists_installed_skills(
        self, manager: OpenModelManager, install_targets: list[Path]
    ) -> None:
        with patch.object(manager, "sync_to_github", return_value=True):
            manager.install_skill(_make_skill("s1", "skill-alpha"))
            manager.install_skill(_make_skill("s2", "skill-beta"))

        skills = manager.get_installed_skills()
        names = {s["name"] for s in skills}
        assert "skill-alpha" in names
        assert "skill-beta" in names

    def test_empty_when_nothing_installed(self, manager: OpenModelManager) -> None:
        skills = manager.get_installed_skills()
        assert skills == []


# ---------------------------------------------------------------------------
# get_model_state tests
# ---------------------------------------------------------------------------

class TestGetModelState:
    """Test model state snapshot."""

    def test_returns_snapshot(self, manager: OpenModelManager) -> None:
        state = manager.get_model_state()
        assert "timestamp" in state
        assert "installed_skill_count" in state
        assert "installed_skills" in state
        assert "install_targets" in state
        assert isinstance(state["installed_skill_count"], int)

    def test_reflects_installations(
        self, manager: OpenModelManager, install_targets: list[Path]
    ) -> None:
        with patch.object(manager, "sync_to_github", return_value=True):
            manager.install_skill(_make_skill("s1", "alpha"))

        state = manager.get_model_state()
        assert state["installed_skill_count"] >= 1
        assert "alpha" in state["installed_skills"]


# ---------------------------------------------------------------------------
# _generate_skill_md tests
# ---------------------------------------------------------------------------

class TestGenerateSkillMd:
    """Test SKILL.md generation."""

    def test_produces_valid_format(self, manager: OpenModelManager) -> None:
        skill = _make_skill()
        md = manager._generate_skill_md(skill)

        assert md.startswith("---\n")
        assert "name: test-skill" in md
        assert "description: Test intent" in md
        assert "user-invocable: false" in md
        assert "quad-version: 1" in md
        assert "confidence: 0.85" in md
        assert "security: standard" in md
        assert "source-project: test-project" in md
        assert "# test-skill" in md
        assert "## Context" in md
        assert "## When to Use" in md
        assert "## Logic" in md
        assert "## Constraints" in md
        assert "- constraint-a" in md
        assert "- constraint-b" in md
        assert "## Expected Output" in md
        assert "## Known Failure Modes" in md
        assert "- timeout" in md
        assert "- missing dep" in md

    def test_handles_string_constraints(self, manager: OpenModelManager) -> None:
        skill = _make_skill()
        skill["constraints"] = "single constraint"
        skill["failure_modes"] = "single failure"
        md = manager._generate_skill_md(skill)

        assert "single constraint" in md
        assert "single failure" in md


# ---------------------------------------------------------------------------
# training log tests
# ---------------------------------------------------------------------------

class TestTrainingLog:
    """Test training log updates."""

    def test_log_updated_on_install(
        self, manager: OpenModelManager, work_dir: Path
    ) -> None:
        with patch.object(manager, "sync_to_github", return_value=True):
            manager.install_skill(_make_skill())

        log_path = work_dir / "data" / "training_log.json"
        assert log_path.exists()
        lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        actions = [json.loads(l)["action"] for l in lines]
        assert "installed" in actions

    def test_log_updated_on_uninstall(
        self, manager: OpenModelManager, work_dir: Path
    ) -> None:
        with patch.object(manager, "sync_to_github", return_value=True), \
             patch("open_model_manager.backup_file", return_value=None):
            manager.install_skill(_make_skill())
            manager.uninstall_skill("test-skill")

        log_path = work_dir / "data" / "training_log.json"
        lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        actions = [json.loads(l)["action"] for l in lines]
        assert "uninstalled" in actions


# ---------------------------------------------------------------------------
# sync_to_github tests
# ---------------------------------------------------------------------------

class TestSyncToGithub:
    """Test GitHub sync triggering."""

    def test_sync_success(self, manager: OpenModelManager) -> None:
        mock_module = MagicMock()
        mock_module.sync.return_value = True
        with patch.dict("sys.modules", {"github_sync": mock_module}):
            result = manager.sync_to_github()
            assert result is True

    def test_sync_import_error(self, manager: OpenModelManager, monkeypatch: pytest.MonkeyPatch) -> None:
        # Remove github_sync from sys.modules if present, and make import fail
        def fail_import(name: str, *args: Any, **kwargs: Any) -> None:
            if name == "github_sync":
                raise ImportError("no module")
            return original_import(name, *args, **kwargs)

        import builtins
        original_import = builtins.__import__
        monkeypatch.setattr(builtins, "__import__", fail_import)

        result = manager.sync_to_github()
        assert result is False
