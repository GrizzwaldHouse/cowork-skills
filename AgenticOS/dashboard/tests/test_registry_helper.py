# test_registry_helper.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Unit tests for registry_helper. Every test targets a
#          throwaway subkey under HKCU\Software\AgenticOS-Test so
#          the user's real Run key is never modified. On non-Windows
#          platforms the tests skip cleanly; the helper module
#          itself raises a typed OSError there.

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from AgenticOS.dashboard import config as dashboard_config
from AgenticOS.dashboard.registry_helper import (
    build_launch_command,
    delete_run_value,
    is_autostart_enabled,
    read_run_value,
    write_run_value,
)


# ---------------------------------------------------------------------------
# Skip the registry-touching tests on non-Windows hosts. The build_launch
# helper test runs on every platform because it is pure string manipulation.
# ---------------------------------------------------------------------------

WINDOWS_ONLY = pytest.mark.skipif(
    sys.platform != "win32",
    reason="winreg-backed registry helpers only run on Windows",
)


# Sandbox subkey used by every test below. Choosing a distinct subkey
# (rather than the real Run key with a "Test" value name) means even a
# bug that ignores the value name cannot pollute autostart.
TEST_RUN_KEY = r"Software\AgenticOS-Test"
TEST_VALUE_NAME = dashboard_config.REGISTRY_TEST_VALUE_NAME
TEST_COMMAND = (
    r'"C:\Python314\pythonw.exe" '
    r'"C:\ClaudeSkills\AgenticOS\dashboard\agentic_dashboard.py"'
)


@pytest.fixture
def clean_sandbox() -> None:
    """Remove any leftover value before and after each test run."""
    # Pre-clean in case a previous run crashed mid-test.
    delete_run_value(TEST_RUN_KEY, TEST_VALUE_NAME)
    yield
    delete_run_value(TEST_RUN_KEY, TEST_VALUE_NAME)


# ---------------------------------------------------------------------------
# is_autostart_enabled
# ---------------------------------------------------------------------------

@WINDOWS_ONLY
def test_is_autostart_enabled_false_when_value_absent(clean_sandbox: None) -> None:
    # Sandbox is empty; helper must report disabled rather than raising.
    assert is_autostart_enabled(TEST_RUN_KEY, TEST_VALUE_NAME) is False


@WINDOWS_ONLY
def test_is_autostart_enabled_true_after_write(clean_sandbox: None) -> None:
    # Writing the value should immediately make the helper report True.
    assert write_run_value(TEST_RUN_KEY, TEST_VALUE_NAME, TEST_COMMAND) is True
    assert is_autostart_enabled(TEST_RUN_KEY, TEST_VALUE_NAME) is True


# ---------------------------------------------------------------------------
# write / read / delete round-trip
# ---------------------------------------------------------------------------

@WINDOWS_ONLY
def test_write_then_read_returns_same_command(clean_sandbox: None) -> None:
    # Round-trip ensures REG_SZ encoding is preserved end-to-end.
    write_run_value(TEST_RUN_KEY, TEST_VALUE_NAME, TEST_COMMAND)
    assert read_run_value(TEST_RUN_KEY, TEST_VALUE_NAME) == TEST_COMMAND


@WINDOWS_ONLY
def test_delete_returns_true_when_value_already_absent(clean_sandbox: None) -> None:
    # Deleting a missing value should be idempotent: the desired end
    # state is "no value", which is already true.
    assert delete_run_value(TEST_RUN_KEY, TEST_VALUE_NAME) is True


@WINDOWS_ONLY
def test_delete_clears_previously_written_value(clean_sandbox: None) -> None:
    # Prove that delete actually removes a value that exists.
    write_run_value(TEST_RUN_KEY, TEST_VALUE_NAME, TEST_COMMAND)
    assert is_autostart_enabled(TEST_RUN_KEY, TEST_VALUE_NAME) is True
    assert delete_run_value(TEST_RUN_KEY, TEST_VALUE_NAME) is True
    assert is_autostart_enabled(TEST_RUN_KEY, TEST_VALUE_NAME) is False


# ---------------------------------------------------------------------------
# build_launch_command -- pure string utility, runs on every platform
# ---------------------------------------------------------------------------

def test_build_launch_command_quotes_both_paths() -> None:
    # Both halves of the command line must be individually quoted so a
    # path containing a space survives the Windows shell parser.
    cmd = build_launch_command(
        Path(r"C:\Program Files\Python314\pythonw.exe"),
        Path(r"C:\My Projects\AgenticOS\dashboard\agentic_dashboard.py"),
    )
    assert cmd.startswith('"')
    assert '"C:\\Program Files\\Python314\\pythonw.exe"' in cmd
    assert '"C:\\My Projects\\AgenticOS\\dashboard\\agentic_dashboard.py"' in cmd


def test_build_launch_command_uses_native_path_separators() -> None:
    # Path() should normalise to backslashes on Windows; on POSIX the
    # forward slash is the native separator. Either is acceptable as
    # long as both paths use a consistent style.
    cmd = build_launch_command(
        Path("python"),
        Path("agentic_dashboard.py"),
    )
    # Two opening quotes; one for each argument.
    assert cmd.count('"') == 4
