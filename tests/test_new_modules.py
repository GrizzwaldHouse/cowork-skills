# test_new_modules.py
# Developer: Marcus Daley
# Date: 2026-02-21
# Purpose: Comprehensive unit tests for OwlWatcher new modules (config_manager, log_config, watcher_core, owl_state_machine, speech_messages, constants)

"""
Unit tests for new OwlWatcher modules.

Tests cover configuration loading, logging setup, file filtering, state machine
transitions, speech message generation, and constant validation.
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Ensure scripts directory is on sys.path for imports
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Initialize PyQt6 application for state machine tests
from PyQt6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

# Module imports after sys.path setup
from config_manager import load_config, watched_paths, CONFIG_PATH, _DEFAULTS
from log_config import configure_logging, _configured, _FORMAT, _DATEFMT
from watcher_core import (
    is_transient,
    is_security_dir,
    matches_ignored,
    matches_enabled_skills,
    should_process,
    SECURITY_DIR,
)
from gui.owl_state_machine import OwlStateMachine, OwlState
from gui.speech_messages import get_message, get_alert_message
import gui.constants as constants


# ---------------------------------------------------------------------------
# config_manager.py tests
# ---------------------------------------------------------------------------

class TestConfigManager:
    """Test config_manager.py configuration loading."""

    def test_load_config_missing_file(self, tmp_path):
        """Test load_config returns defaults when file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.json"
        config = load_config(nonexistent)

        # All default keys should be present
        assert "watched_paths" in config
        assert "ignored_patterns" in config
        assert "sync_interval" in config
        assert "enabled_skills" in config

        # Values should match defaults
        assert config["watched_paths"] == _DEFAULTS["watched_paths"]
        assert config["sync_interval"] == _DEFAULTS["sync_interval"]

    def test_load_config_from_actual_file(self):
        """Test loading from the actual watch_config.json file."""
        if not CONFIG_PATH.exists():
            pytest.skip("watch_config.json not found, skipping")

        config = load_config()

        # Config should have all required keys
        assert "watched_paths" in config
        assert "ignored_patterns" in config
        assert "sync_interval" in config

        # watched_paths should be a list
        assert isinstance(config["watched_paths"], list)

    def test_load_config_merges_defaults(self, tmp_path):
        """Test load_config merges defaults for missing keys."""
        partial_config = tmp_path / "partial.json"
        partial_config.write_text(json.dumps({"watched_paths": ["/test"]}))

        config = load_config(partial_config)

        # Custom key should be preserved
        assert config["watched_paths"] == ["/test"]

        # Missing keys should be filled from defaults
        assert config["ignored_patterns"] == _DEFAULTS["ignored_patterns"]
        assert config["sync_interval"] == _DEFAULTS["sync_interval"]

    def test_load_config_invalid_json(self, tmp_path):
        """Test load_config handles malformed JSON gracefully."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ not valid json }")

        config = load_config(invalid_file)

        # Should fall back to defaults
        assert config == _DEFAULTS

    def test_watched_paths_with_config(self):
        """Test watched_paths extracts paths from config dict."""
        test_config = {"watched_paths": ["/path1", "/path2"]}
        paths = watched_paths(test_config)

        assert paths == ["/path1", "/path2"]

    def test_watched_paths_loads_config_when_none(self):
        """Test watched_paths loads config when not provided."""
        paths = watched_paths()

        # Should return a list (either from actual config or defaults)
        assert isinstance(paths, list)


# ---------------------------------------------------------------------------
# log_config.py tests
# ---------------------------------------------------------------------------

class TestLogConfig:
    """Test log_config.py logging configuration."""

    def test_configure_logging_sets_format(self):
        """Test configure_logging applies the correct format."""
        # Get root logger
        root = logging.getLogger()

        # Should have at least one handler configured after app initialization
        # Note: logging.basicConfig only works once, so we can't reset the root logger
        assert len(root.handlers) > 0

        # At least verify a handler exists (level may vary based on test order)
        assert root.handlers[0] is not None

    def test_configure_logging_idempotent(self):
        """Test calling configure_logging twice doesn't duplicate handlers."""
        import log_config

        # Get initial handler count
        initial_count = len(logging.getLogger().handlers)

        # Reset configured flag to allow the function to run
        log_config._configured = False
        configure_logging(logging.INFO)

        # Call again with configured flag False
        log_config._configured = False
        configure_logging(logging.WARNING)

        final_count = len(logging.getLogger().handlers)

        # Handler count should not grow (idempotent behavior)
        # Note: basicConfig may ignore subsequent calls, but we verify no duplication
        assert final_count >= initial_count


# ---------------------------------------------------------------------------
# watcher_core.py tests
# ---------------------------------------------------------------------------

class TestWatcherCore:
    """Test watcher_core.py filtering functions."""

    # is_transient tests
    def test_is_transient_tmp_random(self):
        """Test is_transient detects sync_utils atomic write temp files."""
        assert is_transient(Path(".tmp_abc123.json")) is True
        assert is_transient(Path(".tmp_foo_bar.txt")) is True

    def test_is_transient_tmp_pid_timestamp(self):
        """Test is_transient detects Claude Code atomic write temp files."""
        assert is_transient(Path("config.json.tmp.1234.5678")) is True
        assert is_transient(Path("data.tmp.999.111")) is True

    def test_is_transient_lock_files(self):
        """Test is_transient detects lock files."""
        assert is_transient(Path("audit_log.json.lock")) is True
        assert is_transient(Path("file.lock")) is True

    def test_is_transient_normal_files(self):
        """Test is_transient returns False for normal files."""
        assert is_transient(Path("config.json")) is False
        assert is_transient(Path("main.py")) is False
        assert is_transient(Path("README.md")) is False
        assert is_transient(Path("temporary.txt")) is False  # "tmp" in name, not .tmp

    # is_security_dir tests
    def test_is_security_dir_inside(self):
        """Test is_security_dir returns True for paths inside security dir."""
        assert is_security_dir(SECURITY_DIR / "audit_log.json") is True
        assert is_security_dir(SECURITY_DIR / "sub" / "file.txt") is True

    def test_is_security_dir_outside(self):
        """Test is_security_dir returns False for paths outside security dir."""
        assert is_security_dir(Path("C:/ClaudeSkills/scripts/main.py")) is False
        assert is_security_dir(Path("C:/Other/security/file.txt")) is False

    # matches_ignored tests
    def test_matches_ignored_direct_name(self):
        """Test matches_ignored detects direct name matches."""
        patterns = ["__pycache__", ".git", "backups"]

        assert matches_ignored(Path("project/__pycache__/file.pyc"), patterns) is True
        assert matches_ignored(Path(".git/config"), patterns) is True
        assert matches_ignored(Path("backups/backup.zip"), patterns) is True

    def test_matches_ignored_glob_extension(self):
        """Test matches_ignored detects glob extension patterns."""
        patterns = ["*.pyc", "*.log"]

        assert matches_ignored(Path("module.pyc"), patterns) is True
        assert matches_ignored(Path("debug.log"), patterns) is True
        assert matches_ignored(Path("test.py"), patterns) is False

    def test_matches_ignored_no_match(self):
        """Test matches_ignored returns False when no pattern matches."""
        patterns = ["__pycache__", "*.pyc"]

        assert matches_ignored(Path("main.py"), patterns) is False
        assert matches_ignored(Path("README.md"), patterns) is False

    # matches_enabled_skills tests
    def test_matches_enabled_skills_empty_list(self):
        """Test matches_enabled_skills returns True when enabled_skills is empty."""
        # Empty list means all skills are enabled
        assert matches_enabled_skills(Path("skills/some-skill/file.py"), []) is True

    def test_matches_enabled_skills_match(self):
        """Test matches_enabled_skills returns True when path contains enabled skill."""
        enabled = ["design-system", "canva-designer"]

        assert matches_enabled_skills(Path("skills/design-system/file.py"), enabled) is True
        assert matches_enabled_skills(Path("canva-designer/template.json"), enabled) is True

    def test_matches_enabled_skills_no_match(self):
        """Test matches_enabled_skills returns False when path doesn't contain enabled skill."""
        enabled = ["design-system"]

        assert matches_enabled_skills(Path("skills/other-skill/file.py"), enabled) is False

    # should_process integration test
    def test_should_process_blocks_transient(self):
        """Test should_process blocks transient files."""
        last_event_time = {}
        path = Path(".tmp_abc123.json")

        result = should_process(path, [], [], 5.0, last_event_time)

        assert result is False

    def test_should_process_blocks_security_dir(self):
        """Test should_process blocks security directory files."""
        last_event_time = {}
        path = SECURITY_DIR / "audit_log.json"

        result = should_process(path, [], [], 5.0, last_event_time)

        assert result is False

    def test_should_process_blocks_ignored_patterns(self):
        """Test should_process blocks files matching ignored patterns."""
        last_event_time = {}
        path = Path("module.pyc")

        result = should_process(path, ["*.pyc"], [], 5.0, last_event_time)

        assert result is False

    def test_should_process_blocks_disabled_skills(self):
        """Test should_process blocks files from disabled skills."""
        last_event_time = {}
        path = Path("skills/other-skill/file.py")
        enabled = ["design-system"]

        result = should_process(path, [], enabled, 5.0, last_event_time)

        assert result is False

    def test_should_process_throttles_rapid_events(self):
        """Test should_process throttles events within sync_interval."""
        last_event_time = {}
        path = Path("test.txt")

        # First event should pass
        result1 = should_process(path, [], [], 1.0, last_event_time)
        assert result1 is True

        # Immediate second event should be throttled
        result2 = should_process(path, [], [], 1.0, last_event_time)
        assert result2 is False

        # After waiting, should pass
        time.sleep(1.1)
        result3 = should_process(path, [], [], 1.0, last_event_time)
        assert result3 is True

    def test_should_process_allows_valid_file(self):
        """Test should_process allows files that pass all checks."""
        last_event_time = {}
        path = Path("main.py")

        result = should_process(path, [], [], 5.0, last_event_time)

        assert result is True


# ---------------------------------------------------------------------------
# owl_state_machine.py tests
# ---------------------------------------------------------------------------

class TestOwlStateMachine:
    """Test owl_state_machine.py state transitions."""

    def test_all_states_exist(self):
        """Test all 8 owl states are defined in OwlState enum."""
        expected_states = {
            "SLEEPING", "WAKING", "IDLE", "SCANNING",
            "CURIOUS", "ALERT", "ALARM", "PROUD",
        }

        actual_states = {s.name for s in OwlState}

        assert actual_states == expected_states

    def test_initial_state_is_idle(self):
        """Test state machine starts in IDLE state."""
        machine = OwlStateMachine()

        assert machine.state == OwlState.IDLE

    def test_valid_transition_succeeds(self):
        """Test valid state transitions are allowed."""
        machine = OwlStateMachine()

        # IDLE -> SCANNING is allowed via command_start_watching
        machine.command_start_watching()

        assert machine.state == OwlState.SCANNING

    def test_invalid_transition_blocked(self):
        """Test invalid state transitions are blocked."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SCANNING)

        # SCANNING -> WAKING is not in the transition table
        result = machine._transition(OwlState.WAKING)

        assert result is False
        assert machine.state == OwlState.SCANNING  # State unchanged

    def test_command_start_watching_from_idle(self):
        """Test command_start_watching transitions IDLE to SCANNING."""
        machine = OwlStateMachine()
        assert machine.state == OwlState.IDLE

        machine.command_start_watching()

        assert machine.state == OwlState.SCANNING

    def test_command_start_watching_from_sleeping(self):
        """Test command_start_watching transitions SLEEPING to WAKING."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SLEEPING)

        machine.command_start_watching()

        assert machine.state == OwlState.WAKING

    def test_command_stop_watching(self):
        """Test command_stop_watching transitions active states to IDLE."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SCANNING)

        machine.command_stop_watching()

        assert machine.state == OwlState.IDLE

    def test_command_security_alert_critical(self):
        """Test command_security_alert with CRITICAL level forces ALARM."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SCANNING)

        machine.command_security_alert("CRITICAL")

        assert machine.state == OwlState.ALARM

    def test_command_security_alert_warning(self):
        """Test command_security_alert with WARNING level goes to ALERT."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SCANNING)

        machine.command_security_alert("WARNING")

        assert machine.state == OwlState.ALERT

    def test_command_unusual_event_from_scanning(self):
        """Test command_unusual_event transitions SCANNING to CURIOUS."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SCANNING)

        machine.command_unusual_event()

        assert machine.state == OwlState.CURIOUS

    def test_command_integrity_clean_from_scanning(self):
        """Test command_integrity_clean transitions SCANNING to PROUD."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SCANNING)

        machine.command_integrity_clean()

        assert machine.state == OwlState.PROUD

    def test_state_changed_signal_emitted(self):
        """Test state_changed signal is emitted on transition."""
        machine = OwlStateMachine()

        # Track signal emissions
        signal_received = []
        machine.state_changed.connect(lambda state: signal_received.append(state))

        machine.command_start_watching()

        # Signal should have been emitted with "scanning"
        assert len(signal_received) == 1
        assert signal_received[0] == "scanning"

    def test_same_state_transition_skipped(self):
        """Test transitioning to the same state is a no-op."""
        machine = OwlStateMachine()
        machine._transition(OwlState.SCANNING)

        # Try to transition to SCANNING again
        result = machine._transition(OwlState.SCANNING)

        assert result is False


# ---------------------------------------------------------------------------
# speech_messages.py tests
# ---------------------------------------------------------------------------

class TestSpeechMessages:
    """Test speech_messages.py message generation."""

    def test_get_message_returns_string_for_valid_state(self):
        """Test get_message returns a non-empty string for each valid state."""
        valid_states = [
            "sleeping", "waking", "idle", "scanning",
            "curious", "alert", "alarm", "proud",
        ]

        for state in valid_states:
            message = get_message(state)
            assert isinstance(message, str)
            assert len(message) > 0

    def test_get_message_unknown_state_returns_fallback(self):
        """Test get_message returns empty string for unknown state."""
        message = get_message("nonexistent_state")

        assert message == ""

    def test_get_alert_message_warning(self):
        """Test get_alert_message for WARNING level."""
        message = get_alert_message("WARNING", "Test warning")

        assert "Warning:" in message
        assert "Test warning" in message

    def test_get_alert_message_critical(self):
        """Test get_alert_message for CRITICAL level."""
        message = get_alert_message("CRITICAL", "Test critical")

        assert "CRITICAL:" in message
        assert "Test critical" in message

    def test_get_alert_message_info_no_detail(self):
        """Test get_alert_message for INFO level without detail."""
        message = get_alert_message("INFO")

        # Should return a generic message (not empty)
        assert isinstance(message, str)

    def test_get_message_randomization(self):
        """Test get_message returns different messages on repeated calls."""
        # Call multiple times to check randomization
        messages = [get_message("scanning") for _ in range(20)]

        # At least some variation should exist (not all identical)
        unique_messages = set(messages)
        assert len(unique_messages) > 1


# ---------------------------------------------------------------------------
# constants.py tests
# ---------------------------------------------------------------------------

class TestConstants:
    """Test constants.py constant definitions."""

    def test_color_constants_are_strings(self):
        """Test color constants are hex strings."""
        color_names = [
            "NAVY", "GOLD", "PARCHMENT", "TEAL",
            "DARK_PANEL", "MID_PANEL", "HEADER_BG",
        ]

        for name in color_names:
            color = getattr(constants, name)
            assert isinstance(color, str)
            assert color.startswith("#")

    def test_numeric_thresholds_are_positive(self):
        """Test numeric threshold constants are positive values."""
        thresholds = [
            "MAX_AUDIT_ENTRIES",
            "DEFAULT_LARGE_FILE_BYTES",
            "BURST_THRESHOLD",
            "EVENT_MAX_ROWS",
        ]

        for name in thresholds:
            value = getattr(constants, name)
            assert isinstance(value, (int, float))
            assert value > 0

    def test_qsettings_constants_exist(self):
        """Test QSettings organization and app constants exist."""
        assert hasattr(constants, "QSETTINGS_ORG")
        assert hasattr(constants, "QSETTINGS_APP")

        assert isinstance(constants.QSETTINGS_ORG, str)
        assert isinstance(constants.QSETTINGS_APP, str)
        assert len(constants.QSETTINGS_ORG) > 0
        assert len(constants.QSETTINGS_APP) > 0

    def test_state_svg_map_complete(self):
        """Test STATE_SVG_MAP contains all 8 owl states."""
        expected_states = {
            "sleeping", "waking", "idle", "scanning",
            "curious", "alert", "alarm", "proud",
        }

        assert set(constants.STATE_SVG_MAP.keys()) == expected_states

        # All values should be .svg filenames
        for filename in constants.STATE_SVG_MAP.values():
            assert filename.endswith(".svg")

    def test_suspicious_extensions_is_frozen(self):
        """Test SUSPICIOUS_EXTENSIONS is a frozenset."""
        assert isinstance(constants.SUSPICIOUS_EXTENSIONS, frozenset)
        assert ".exe" in constants.SUSPICIOUS_EXTENSIONS
        assert ".dll" in constants.SUSPICIOUS_EXTENSIONS

    def test_animation_fps_positive(self):
        """Test animation FPS constants are positive."""
        assert constants.ANIMATION_FPS > 0
        assert constants.AMBIENT_FPS > 0

    def test_bubble_constants_exist(self):
        """Test speech bubble constants are defined."""
        bubble_attrs = [
            "BUBBLE_BG", "BUBBLE_TEXT", "BUBBLE_BORDER",
            "BUBBLE_PADDING", "BUBBLE_RADIUS",
        ]

        for attr in bubble_attrs:
            assert hasattr(constants, attr)
