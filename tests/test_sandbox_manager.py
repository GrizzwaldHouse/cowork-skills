# test_sandbox_manager.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Comprehensive unit tests for SandboxManager isolated testing environment with scenario validation

"""
Unit tests for SandboxManager.

Tests cover sandbox lifecycle (create, cleanup), scenario population (good/bad/
injection/empty skills), file operations (inject, modify, delete), activity
logging, and Qt signal emissions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure scripts directory is on sys.path for imports
sys.path.insert(0, "C:/ClaudeSkills")
sys.path.insert(0, "C:/ClaudeSkills/scripts")

# Initialize PyQt6 application for SandboxManager tests
from PyQt6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

# Module imports after sys.path setup
from testing.sandbox_manager import (
    SandboxManager,
    SCENARIO_GOOD_SKILL,
    SCENARIO_BAD_SKILL,
    SCENARIO_INJECTION_SKILL,
    SCENARIO_EMPTY_SKILL,
    DEFAULT_SANDBOX_PREFIX,
)


class TestSandboxManager:
    """Test SandboxManager isolated testing environment."""

    def test_create_sandbox(self):
        """Test sandbox directory exists after create()."""
        manager = SandboxManager()
        sandbox_path = manager.create()

        assert sandbox_path.exists()
        assert sandbox_path.is_dir()
        assert DEFAULT_SANDBOX_PREFIX in sandbox_path.name

        # Cleanup
        manager.cleanup()

    def test_sandbox_path_property(self):
        """Test sandbox_path property returns Path when active, None when not."""
        manager = SandboxManager()

        # Before creation
        assert manager.sandbox_path is None

        # After creation
        sandbox = manager.create()
        assert manager.sandbox_path == sandbox
        assert isinstance(manager.sandbox_path, Path)

        # After cleanup
        manager.cleanup()
        assert manager.sandbox_path is None

    def test_is_active(self):
        """Test is_active property True after create, False after cleanup."""
        manager = SandboxManager()

        # Before creation
        assert manager.is_active is False

        # After creation
        manager.create()
        assert manager.is_active is True

        # After cleanup
        manager.cleanup()
        assert manager.is_active is False

    def test_populate_good_skill(self):
        """Test populate creates SKILL.md with valid, reusable content."""
        manager = SandboxManager()
        manager.create()

        files = manager.populate(SCENARIO_GOOD_SKILL)

        assert len(files) == 1
        skill_file = files[0]
        assert skill_file.exists()
        assert skill_file.name == "SKILL.md"

        content = skill_file.read_text(encoding="utf-8")
        # Verify high-quality skill characteristics
        assert "universal-error-handler" in content
        assert "Framework-agnostic" in content or "framework-agnostic" in content
        assert "Reusable" in content or "reusable" in content
        assert len(content) > 500  # Substantial content
        assert "## Intent" in content
        assert "## Execution Logic" in content
        assert "## Constraints" in content
        assert "## Failure Modes" in content

        # Should NOT contain project-specific hardcoded paths
        assert "C:/Users" not in content
        assert "localhost" not in content or "example" in content.lower()

        # Cleanup
        manager.cleanup()

    def test_populate_bad_skill(self):
        """Test populate creates SKILL.md with hardcoded paths and magic numbers."""
        manager = SandboxManager()
        manager.create()

        files = manager.populate(SCENARIO_BAD_SKILL)

        assert len(files) == 1
        skill_file = files[0]
        content = skill_file.read_text(encoding="utf-8")

        # Verify bad skill anti-patterns
        assert "C:/Users" in content or "hardcoded" in content.lower()
        assert "localhost" in content or "magic" in content.lower()
        assert "Quick and dirty" in content or "my project" in content.lower()

        # Cleanup
        manager.cleanup()

    def test_populate_injection_skill(self):
        """Test populate creates SKILL.md with unsafe patterns (os.system, eval, etc.)."""
        manager = SandboxManager()
        manager.create()

        files = manager.populate(SCENARIO_INJECTION_SKILL)

        assert len(files) == 1
        skill_file = files[0]
        content = skill_file.read_text(encoding="utf-8")

        # Verify dangerous patterns present
        assert "os.system" in content or "eval" in content or "__import__" in content
        assert "subprocess" in content or "shell=True" in content or "rm -rf" in content

        # Cleanup
        manager.cleanup()

    def test_populate_empty_skill(self):
        """Test populate creates minimal SKILL.md with missing fields."""
        manager = SandboxManager()
        manager.create()

        files = manager.populate(SCENARIO_EMPTY_SKILL)

        assert len(files) == 1
        skill_file = files[0]
        content = skill_file.read_text(encoding="utf-8")

        # Verify minimal content (name present, most fields missing)
        assert "minimal-skill" in content
        assert len(content) < 200  # Very short

        # Cleanup
        manager.cleanup()

    def test_populate_unknown_scenario_raises(self):
        """Test populate raises ValueError for unknown scenario."""
        manager = SandboxManager()
        manager.create()

        with pytest.raises(ValueError, match="Unknown scenario"):
            manager.populate("nonexistent_scenario")

        # Cleanup
        manager.cleanup()

    def test_populate_without_active_sandbox_raises(self):
        """Test populate raises ValueError when sandbox not active."""
        manager = SandboxManager()

        with pytest.raises(ValueError, match="Sandbox is not active"):
            manager.populate(SCENARIO_GOOD_SKILL)

    def test_inject_file_event(self):
        """Test inject_file_event creates file and logs in activity."""
        manager = SandboxManager()
        manager.create()

        file_path = manager.inject_file_event("test.txt", "Hello, sandbox!")

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "Hello, sandbox!"

        # Verify logged
        activity = manager.get_activity_log()
        file_actions = [a for a in activity if a["filename"] == "test.txt"]
        assert len(file_actions) == 1
        assert file_actions[0]["action"] == "file_created"

        # Cleanup
        manager.cleanup()

    def test_inject_file_event_overwrites_existing(self):
        """Test inject_file_event overwrites existing file and emits file_modified."""
        manager = SandboxManager()
        manager.create()

        # Create file
        file_path = manager.inject_file_event("existing.txt", "Original content")
        assert file_path.read_text(encoding="utf-8") == "Original content"

        # Overwrite file
        file_path = manager.inject_file_event("existing.txt", "Updated content")
        assert file_path.read_text(encoding="utf-8") == "Updated content"

        # Verify both actions logged
        activity = manager.get_activity_log()
        file_actions = [a for a in activity if a["filename"] == "existing.txt"]
        assert len(file_actions) == 2
        assert file_actions[0]["action"] == "file_created"
        assert file_actions[1]["action"] == "file_modified"

        # Cleanup
        manager.cleanup()

    def test_modify_file(self):
        """Test modify_file updates existing file and logs modification."""
        manager = SandboxManager()
        manager.create()

        # Create file first
        manager.inject_file_event("modify_test.txt", "Initial")

        # Modify file
        modified_path = manager.modify_file("modify_test.txt", "Modified")

        assert modified_path.read_text(encoding="utf-8") == "Modified"

        # Verify modification logged
        activity = manager.get_activity_log()
        file_actions = [a for a in activity if a["filename"] == "modify_test.txt"]
        # Should have 1 create + 1 modify
        modify_actions = [a for a in file_actions if a["action"] == "file_modified"]
        assert len(modify_actions) >= 1

        # Cleanup
        manager.cleanup()

    def test_modify_file_nonexistent_raises(self):
        """Test modify_file raises ValueError for nonexistent file."""
        manager = SandboxManager()
        manager.create()

        with pytest.raises(ValueError, match="File does not exist"):
            manager.modify_file("nonexistent.txt", "Content")

        # Cleanup
        manager.cleanup()

    def test_delete_file(self):
        """Test delete_file removes file and logs deletion."""
        manager = SandboxManager()
        manager.create()

        # Create file
        file_path = manager.inject_file_event("delete_test.txt", "To be deleted")
        assert file_path.exists()

        # Delete file
        manager.delete_file("delete_test.txt")
        assert not file_path.exists()

        # Verify deletion logged
        activity = manager.get_activity_log()
        delete_actions = [a for a in activity if a["action"] == "file_deleted"]
        assert len(delete_actions) == 1
        assert delete_actions[0]["filename"] == "delete_test.txt"

        # Cleanup
        manager.cleanup()

    def test_delete_file_nonexistent_raises(self):
        """Test delete_file raises ValueError for nonexistent file."""
        manager = SandboxManager()
        manager.create()

        with pytest.raises(ValueError, match="File does not exist"):
            manager.delete_file("nonexistent.txt")

        # Cleanup
        manager.cleanup()

    def test_cleanup(self):
        """Test cleanup removes sandbox directory completely."""
        manager = SandboxManager()
        sandbox_path = manager.create()

        # Create some files
        manager.inject_file_event("file1.txt", "Content 1")
        manager.inject_file_event("file2.txt", "Content 2")

        assert sandbox_path.exists()

        # Cleanup
        manager.cleanup()

        # Sandbox should be gone
        assert not sandbox_path.exists()
        assert manager.sandbox_path is None
        assert manager.is_active is False

    def test_activity_log(self):
        """Test operations are tracked correctly in activity log."""
        manager = SandboxManager()
        manager.create()

        # Perform various operations
        manager.inject_file_event("log_test.txt", "Content")
        manager.modify_file("log_test.txt", "Modified")
        manager.delete_file("log_test.txt")

        activity = manager.get_activity_log()

        # Should have: sandbox_created, file_created, file_modified, file_deleted
        assert len(activity) >= 4

        # Verify each entry has required fields
        for entry in activity:
            assert "timestamp" in entry
            assert "action" in entry
            assert "filename" in entry
            assert "path" in entry

        # Verify action sequence
        actions = [a["action"] for a in activity]
        assert "sandbox_created" in actions
        assert "file_created" in actions
        assert "file_modified" in actions
        assert "file_deleted" in actions

        # Cleanup
        manager.cleanup()

    def test_signal_sandbox_ready(self):
        """Test sandbox_ready signal emitted on create()."""
        manager = SandboxManager()

        # Track signal emissions
        signals_received = []
        manager.sandbox_ready.connect(lambda path: signals_received.append(path))

        sandbox_path = manager.create()

        assert len(signals_received) == 1
        assert signals_received[0] == str(sandbox_path)

        # Cleanup
        manager.cleanup()

    def test_signal_file_created(self):
        """Test file_created signal emitted on new file."""
        manager = SandboxManager()
        manager.create()

        # Track signal emissions
        signals_received = []
        manager.file_created.connect(lambda path: signals_received.append(path))

        file_path = manager.inject_file_event("signal_test.txt", "Content")

        assert len(signals_received) == 1
        assert signals_received[0] == str(file_path)

        # Cleanup
        manager.cleanup()

    def test_signal_file_modified(self):
        """Test file_modified signal emitted on file overwrite."""
        manager = SandboxManager()
        manager.create()

        # Create file first
        manager.inject_file_event("modify_signal_test.txt", "Original")

        # Track modification signal
        signals_received = []
        manager.file_modified.connect(lambda path: signals_received.append(path))

        # Overwrite file
        file_path = manager.inject_file_event("modify_signal_test.txt", "Updated")

        assert len(signals_received) == 1
        assert signals_received[0] == str(file_path)

        # Cleanup
        manager.cleanup()

    def test_signal_file_deleted(self):
        """Test file_deleted signal emitted on file deletion."""
        manager = SandboxManager()
        manager.create()

        # Create file
        file_path = manager.inject_file_event("delete_signal_test.txt", "Content")

        # Track deletion signal
        signals_received = []
        manager.file_deleted.connect(lambda path: signals_received.append(path))

        manager.delete_file("delete_signal_test.txt")

        assert len(signals_received) == 1
        assert signals_received[0] == str(file_path)

        # Cleanup
        manager.cleanup()

    def test_signal_sandbox_destroyed(self):
        """Test sandbox_destroyed signal emitted on cleanup."""
        manager = SandboxManager()
        manager.create()

        # Track signal emissions
        signals_received = []
        manager.sandbox_destroyed.connect(lambda: signals_received.append("destroyed"))

        manager.cleanup()

        assert len(signals_received) == 1
        assert signals_received[0] == "destroyed"

    def test_multiple_sandboxes_sequential(self):
        """Test creating multiple sandboxes sequentially works correctly."""
        manager = SandboxManager()

        # First sandbox
        sandbox1 = manager.create()
        manager.inject_file_event("file1.txt", "Sandbox 1")
        assert sandbox1.exists()
        manager.cleanup()
        assert not sandbox1.exists()

        # Second sandbox
        sandbox2 = manager.create()
        manager.inject_file_event("file2.txt", "Sandbox 2")
        assert sandbox2.exists()
        assert sandbox1 != sandbox2  # Different paths
        manager.cleanup()
        assert not sandbox2.exists()


if __name__ == "__main__":
    # Allow running tests directly with pytest
    pytest.main([__file__, "-v", "--tb=short"])
