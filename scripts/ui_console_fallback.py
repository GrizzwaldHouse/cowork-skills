"""
Console-based progress display for the Claude Skills sync UI.

Used as a fallback when pythonnet/WPF is not available.  Provides a text-based
progress bar, file change list, and accept/cancel prompt.
"""

from __future__ import annotations

import os
import sys
from typing import Any


# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------

_SUPPORTS_ANSI: bool | None = None


def _ansi_supported() -> bool:
    """Return True if the terminal likely supports ANSI escape codes."""
    global _SUPPORTS_ANSI
    if _SUPPORTS_ANSI is not None:
        return _SUPPORTS_ANSI

    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        _SUPPORTS_ANSI = False
        return False

    # Windows 10+ supports ANSI if we enable virtual terminal processing.
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            _SUPPORTS_ANSI = True
        except Exception:
            _SUPPORTS_ANSI = False
    else:
        _SUPPORTS_ANSI = True

    return _SUPPORTS_ANSI


def _color(text: str, code: str) -> str:
    """Wrap *text* in ANSI color codes if supported."""
    if _ansi_supported():
        return f"\033[{code}m{text}\033[0m"
    return text


def gold(text: str) -> str:
    return _color(text, "33")  # yellow as gold proxy


def green(text: str) -> str:
    return _color(text, "32")


def red(text: str) -> str:
    return _color(text, "31")


def dim(text: str) -> str:
    return _color(text, "90")


# ---------------------------------------------------------------------------
# Console progress bar
# ---------------------------------------------------------------------------

def render_progress_bar(
    percent: float,
    width: int = 40,
    fill_char: str = "#",
    empty_char: str = "-",
) -> str:
    """Return a text-based progress bar string."""
    filled = int(width * percent / 100)
    bar = fill_char * filled + empty_char * (width - filled)
    pct = f"{percent:5.1f}%"
    return f"[{gold(bar[:filled])}{dim(bar[filled:])}] {pct}"


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_CHANGE_TYPE_LABELS = {
    "Added": green("[+]"),
    "Modified": gold("[~]"),
    "Deleted": red("[-]"),
    "created": green("[+]"),
    "modified": gold("[~]"),
    "deleted": red("[-]"),
}


def display_header(title: str) -> None:
    """Print a themed header bar."""
    try:
        width = min(os.get_terminal_size().columns, 70)
    except OSError:
        width = 70
    border = gold("=" * width)
    print(border)
    print(gold(f"  {title}"))
    print(border)
    print()


def display_file_changes(changes: list[dict[str, str]]) -> None:
    """Print a list of file changes."""
    if not changes:
        print(dim("  (no file changes)"))
        return

    print(f"  File Changes ({len(changes)} file(s)):")
    print(dim("  " + "-" * 50))

    for change in changes:
        change_type = change.get("change_type", change.get("action", "?"))
        file_path = change.get("file_path", change.get("file", "?"))
        label = _CHANGE_TYPE_LABELS.get(change_type, dim(f"[{change_type}]"))
        print(f"  {label} {file_path}")

    print()


def display_progress(
    current_file: str,
    percent: float,
    status: str,
) -> None:
    """Print a progress update line (overwrites previous line)."""
    bar = render_progress_bar(percent)
    file_display = current_file if len(current_file) < 40 else "..." + current_file[-37:]
    line = f"\r  {bar}  {gold(file_display)}  {dim(status)}"
    # Pad to overwrite previous longer lines.
    padding = " " * max(0, 80 - len(line))
    sys.stdout.write(line + padding)
    sys.stdout.flush()


def display_complete(status: str = "Sync complete.") -> None:
    """Print completion message on a new line."""
    print()
    print()
    print(green(f"  {status}"))
    print()


# ---------------------------------------------------------------------------
# User decision prompt
# ---------------------------------------------------------------------------

def prompt_accept_cancel(changes: list[dict[str, str]]) -> bool:
    """Show pending changes and ask the user to accept or cancel.

    Returns True if the user accepts, False if they cancel.
    """
    display_header("Claude Skills - Sync Preview")
    display_file_changes(changes)

    if not changes:
        print(dim("  Nothing to sync."))
        return False

    while True:
        try:
            answer = input(gold("  Accept these changes? [y/N]: ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False

        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no", ""):
            return False
        print(dim("  Please enter 'y' or 'n'."))


# ---------------------------------------------------------------------------
# Full console UI flow (mirrors the WPF window workflow)
# ---------------------------------------------------------------------------

def show_sync_ui(
    changes: list[dict[str, str]],
    title: str = "Syncing Skills...",
) -> bool:
    """Display the console-based sync UI.

    Parameters
    ----------
    changes:
        List of dicts with keys ``change_type`` and ``file_path``.
    title:
        Header title.

    Returns True if the user accepted, False if cancelled.
    """
    display_header(title)
    display_file_changes(changes)

    if not changes:
        print(dim("  No changes to apply."))
        return False

    accepted = prompt_accept_cancel(changes)

    if accepted:
        total = len(changes)
        for i, change in enumerate(changes, 1):
            percent = (i / total) * 100
            file_path = change.get("file_path", change.get("file", "?"))
            display_progress(file_path, percent, f"{i}/{total}")

        display_complete()
    else:
        print()
        print(dim("  Sync cancelled by user."))
        print()

    return accepted
