# terminal_control.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Windows terminal inventory and safe control helpers for the
#          AgenticOS Universal Hub. Exposes visible command prompt,
#          PowerShell, and Windows Terminal windows to the dashboard so
#          operator agents can be monitored without unsafe screen scraping.

from __future__ import annotations

import ctypes
import logging
import platform
from ctypes import wintypes
from datetime import datetime, timezone
from typing import Callable, Iterable, Optional

import psutil

from AgenticOS.config import (
    LOGGER_NAME,
    TERMINAL_CONTROL_AGENT_TITLE_KEYWORDS,
    TERMINAL_CONTROL_PROCESS_NAMES,
)
from AgenticOS.models import TerminalActionResult, TerminalWindow


_logger = logging.getLogger(f"{LOGGER_NAME}.terminal_control")

_WM_CLOSE = 0x0010
_SW_RESTORE = 9


class TerminalControlError(RuntimeError):
    """Raised when a terminal action cannot be completed safely."""


def _is_windows() -> bool:
    """Return true when Win32 window APIs are available."""
    return platform.system().lower() == "windows"


def _normalise_process_name(name: str) -> str:
    return name.strip().lower()


def _is_terminal_process(process_name: str) -> bool:
    """Return true when the process is part of the configured terminal set."""
    return _normalise_process_name(process_name) in TERMINAL_CONTROL_PROCESS_NAMES


def _is_agent_like(title: str, process_name: str, command_line: Optional[str]) -> bool:
    """Detect likely agent terminals from human-visible metadata."""
    haystack = " ".join(
        value.lower()
        for value in (title, process_name, command_line or "")
        if value
    )
    return any(keyword in haystack for keyword in TERMINAL_CONTROL_AGENT_TITLE_KEYWORDS)


def _user32() -> ctypes.WinDLL:
    if not _is_windows():
        raise TerminalControlError("Terminal control is only available on Windows")
    return ctypes.WinDLL("user32", use_last_error=True)


def _window_title(user32: ctypes.WinDLL, hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def _process_metadata(pid: int) -> dict[str, Optional[str]]:
    try:
        process = psutil.Process(pid)
        process_name = process.name()
    except (psutil.Error, OSError) as exc:
        _logger.debug("Could not read process name for pid %s: %s", pid, exc)
        return {
            "process_name": f"pid-{pid}",
            "executable": None,
            "cwd": None,
            "command_line": None,
        }

    try:
        executable = process.exe()
    except (psutil.Error, OSError):
        executable = None

    try:
        cwd = process.cwd()
    except (psutil.Error, OSError):
        cwd = None

    try:
        command_line = " ".join(process.cmdline())
    except (psutil.Error, OSError):
        command_line = None

    return {
        "process_name": process_name,
        "executable": executable,
        "cwd": cwd,
        "command_line": command_line,
    }


def _iter_windows() -> Iterable[int]:
    """Yield visible top-level window handles through EnumWindows."""
    user32 = _user32()
    handles: list[int] = []

    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _callback(hwnd: int, _lparam: int) -> bool:
        if user32.IsWindowVisible(hwnd):
            handles.append(int(hwnd))
        return True

    user32.EnumWindows(enum_proc(_callback), 0)
    return handles


def _window_pid(hwnd: int) -> int:
    user32 = _user32()
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    return int(pid.value)


def _build_terminal_window(
    hwnd: int,
    now: datetime,
    metadata_reader: Callable[[int], dict[str, Optional[str]]] = _process_metadata,
) -> Optional[TerminalWindow]:
    user32 = _user32()
    pid = _window_pid(hwnd)
    metadata = metadata_reader(pid)
    process_name = metadata["process_name"] or f"pid-{pid}"
    title = _window_title(user32, hwnd) or process_name

    if not _is_terminal_process(process_name):
        return None

    command_line = metadata["command_line"]
    return TerminalWindow(
        hwnd=hwnd,
        pid=pid,
        title=title,
        process_name=process_name,
        executable=metadata["executable"],
        cwd=metadata["cwd"],
        command_line=command_line,
        is_visible=True,
        is_agent_like=_is_agent_like(title, process_name, command_line),
        detected_at=now,
    )


def list_terminal_windows(agent_only: bool = False) -> list[TerminalWindow]:
    """Return visible terminal windows sorted with likely agents first."""
    if not _is_windows():
        return []

    now = datetime.now(timezone.utc)
    windows: list[TerminalWindow] = []
    for hwnd in _iter_windows():
        try:
            terminal = _build_terminal_window(hwnd, now)
        except Exception as exc:
            _logger.debug("Skipping terminal window %s: %s", hwnd, exc)
            continue
        if terminal is None:
            continue
        if agent_only and not terminal.is_agent_like:
            continue
        windows.append(terminal)

    windows.sort(
        key=lambda w: (
            not w.is_agent_like,
            w.process_name.lower(),
            w.title.lower(),
            w.hwnd,
        )
    )
    return windows


def focus_terminal_window(hwnd: int) -> TerminalActionResult:
    """Restore and foreground one terminal window by Win32 handle."""
    try:
        user32 = _user32()
        if not user32.IsWindow(wintypes.HWND(hwnd)):
            return TerminalActionResult(
                ok=False,
                hwnd=hwnd,
                message=f"Window handle {hwnd} no longer exists",
            )
        user32.ShowWindow(wintypes.HWND(hwnd), _SW_RESTORE)
        focused = bool(user32.SetForegroundWindow(wintypes.HWND(hwnd)))
        return TerminalActionResult(
            ok=focused,
            hwnd=hwnd,
            message=(
                f"Focused terminal window {hwnd}"
                if focused
                else f"Restored terminal window {hwnd}; Windows denied foreground focus"
            ),
        )
    except TerminalControlError as exc:
        return TerminalActionResult(ok=False, hwnd=hwnd, message=str(exc))


def close_terminal_window(hwnd: int) -> TerminalActionResult:
    """Ask a terminal window to close through WM_CLOSE."""
    try:
        user32 = _user32()
        if not user32.IsWindow(wintypes.HWND(hwnd)):
            return TerminalActionResult(
                ok=False,
                hwnd=hwnd,
                message=f"Window handle {hwnd} no longer exists",
            )
        posted = bool(user32.PostMessageW(wintypes.HWND(hwnd), _WM_CLOSE, 0, 0))
        return TerminalActionResult(
            ok=posted,
            hwnd=hwnd,
            message=(
                f"Close requested for terminal window {hwnd}"
                if posted
                else f"Windows rejected close request for terminal window {hwnd}"
            ),
        )
    except TerminalControlError as exc:
        return TerminalActionResult(ok=False, hwnd=hwnd, message=str(exc))


def terminate_terminal_process(pid: int) -> TerminalActionResult:
    """Terminate a terminal process after REST confirmation has been checked."""
    try:
        process = psutil.Process(pid)
        process.terminate()
        return TerminalActionResult(
            ok=True,
            pid=pid,
            message=f"Terminate requested for terminal process {pid}",
        )
    except psutil.NoSuchProcess:
        return TerminalActionResult(
            ok=False,
            pid=pid,
            message=f"Process {pid} no longer exists",
        )
    except (psutil.AccessDenied, OSError) as exc:
        return TerminalActionResult(
            ok=False,
            pid=pid,
            message=f"Could not terminate process {pid}: {exc}",
        )
