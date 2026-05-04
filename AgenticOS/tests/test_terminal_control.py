# test_terminal_control.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Unit tests for terminal-control classification helpers. The
#          Win32 enumeration itself is exercised through the REST surface
#          when AgenticOS runs on Windows.

from __future__ import annotations

from AgenticOS.terminal_control import _is_agent_like, _is_terminal_process


def test_terminal_process_classifier_accepts_configured_shells() -> None:
    """Common Windows shell process names are treated as terminals."""
    assert _is_terminal_process("cmd.exe")
    assert _is_terminal_process("PowerShell.EXE")
    assert _is_terminal_process("WindowsTerminal.exe")


def test_terminal_process_classifier_rejects_unrelated_processes() -> None:
    """Non-terminal app windows are not exposed through the control panel."""
    assert not _is_terminal_process("notepad.exe")
    assert not _is_terminal_process("explorer.exe")


def test_agent_like_classifier_uses_title_and_command_line() -> None:
    """Agent terminal highlighting can come from title or command line."""
    assert _is_agent_like("CLAW worker 1", "cmd.exe", None)
    assert _is_agent_like(
        "Windows PowerShell",
        "powershell.exe",
        "ollama run codellama:13b",
    )
    assert not _is_agent_like("Build tools", "cmd.exe", "npm run build")
