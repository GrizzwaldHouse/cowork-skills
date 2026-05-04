# registry_helper.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Read, write, and remove a single value under an HKCU subkey
#          so the dashboard tray menu can toggle "Start with Windows".
#          All key paths and value names are passed in as arguments
#          (no module globals) so the same helpers can be reused for
#          the unit tests against a sandboxed test subkey without any
#          risk of mutating the user's real Run key.

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

# Module logger; the dashboard package configures handlers centrally.
_logger = logging.getLogger("AgenticOS.dashboard.registry_helper")


# ---------------------------------------------------------------------------
# Platform shim
# ---------------------------------------------------------------------------

# winreg only exists on Windows. The shim lets the unit tests run on
# Linux CI by raising a typed error rather than ImportError at import
# time, which keeps the test discovery phase clean.
if sys.platform == "win32":
    import winreg  # type: ignore[import-not-found]
else:
    class _WinregUnavailable:  # noqa: N801 - pseudo-module name
        """Stand-in raised at call time on non-Windows platforms."""

        # Constants referenced by callers; values match the real winreg
        # so the function bodies do not branch on platform.
        HKEY_CURRENT_USER = 0x80000001
        KEY_SET_VALUE = 0x0002
        KEY_READ = 0x20019
        REG_SZ = 1

        def _unsupported(self, *_args: object, **_kwargs: object) -> None:
            # Raised lazily so simply importing the module on Linux is
            # safe; only callers that actually try to touch the registry
            # see the failure.
            raise OSError("winreg is only available on Windows")

        OpenKey = CreateKey = SetValueEx = QueryValueEx = DeleteValue = CloseKey = _unsupported

    # The type: ignore is necessary because mypy sees winreg as a
    # module on Windows and an instance on other platforms.
    winreg = _WinregUnavailable()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_run_value(run_key: str, value_name: str) -> Optional[str]:
    """Return the string stored at HKCU\\``run_key``\\``value_name``.

    Returns None when the value is absent or the key cannot be opened.
    Never raises so the tray menu can safely show its current state on
    a freshly installed system that has never written the key.
    """
    # KEY_READ is sufficient for QueryValueEx; using a narrower right
    # than KEY_ALL_ACCESS avoids a UAC prompt on systems with stricter
    # policies and matches the principle of least privilege.
    try:
        handle = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_READ
        )
    except FileNotFoundError:
        # The Run subkey itself is missing. Treat the value as absent.
        return None
    except OSError as exc:
        _logger.warning("Could not open Run key '%s' for read: %s", run_key, exc)
        return None

    try:
        value, _kind = winreg.QueryValueEx(handle, value_name)
    except FileNotFoundError:
        return None
    except OSError as exc:
        _logger.warning(
            "Could not read value '%s' under '%s': %s", value_name, run_key, exc
        )
        return None
    finally:
        # Always close the handle even on the success path to release
        # the underlying Win32 HKEY allocation immediately.
        winreg.CloseKey(handle)

    # Coerce to str so consumers do not need to special-case the
    # bytes-like representation winreg sometimes returns.
    return str(value)


def write_run_value(run_key: str, value_name: str, command: str) -> bool:
    """Persist ``command`` under HKCU\\``run_key``\\``value_name``.

    Creates the subkey if it does not already exist; this is required
    because the unit tests target a sandbox subkey that does not exist
    until the first call. Returns True on success, False on any OS
    error so callers can revert their UI state without raising.
    """
    # CreateKey opens or creates atomically; on Windows it is the
    # documented way to ensure the subkey exists before writing.
    try:
        handle = winreg.CreateKey(winreg.HKEY_CURRENT_USER, run_key)
    except OSError as exc:
        _logger.error("Could not create/open Run key '%s': %s", run_key, exc)
        return False

    try:
        winreg.SetValueEx(handle, value_name, 0, winreg.REG_SZ, command)
        _logger.info(
            "Wrote autostart command for '%s' (length=%d)", value_name, len(command)
        )
        return True
    except OSError as exc:
        _logger.error("Could not write value '%s': %s", value_name, exc)
        return False
    finally:
        winreg.CloseKey(handle)


def delete_run_value(run_key: str, value_name: str) -> bool:
    """Remove ``value_name`` from HKCU\\``run_key``.

    Treats "value already absent" as success because the caller's goal
    (autostart disabled) is satisfied either way. Returns False only
    when an unexpected OS error blocks removal.
    """
    try:
        handle = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE
        )
    except FileNotFoundError:
        # No Run subkey; therefore no value to delete. Desired end state.
        return True
    except OSError as exc:
        _logger.error("Could not open Run key '%s' for delete: %s", run_key, exc)
        return False

    try:
        winreg.DeleteValue(handle, value_name)
        _logger.info("Removed autostart value '%s'", value_name)
        return True
    except FileNotFoundError:
        # Value was already gone. The user's intent is satisfied.
        return True
    except OSError as exc:
        _logger.error("Could not delete value '%s': %s", value_name, exc)
        return False
    finally:
        winreg.CloseKey(handle)


def is_autostart_enabled(run_key: str, value_name: str) -> bool:
    """Convenience wrapper: True iff a value exists under the Run key."""
    # Implemented in terms of read_run_value so we have a single place
    # that knows how to talk to winreg; keeps error handling consistent.
    return read_run_value(run_key, value_name) is not None


def build_launch_command(launcher: Path, target_script: Path) -> str:
    """Return the quoted command string for the Run value.

    The Run key receives a single string interpreted by Windows as a
    command line. Both the interpreter and the script must be quoted
    independently so paths containing spaces (very common on Windows)
    survive the shell parser.
    """
    # str() converts Path to its native Windows form (backslashes) and
    # the explicit double quotes survive any later os.system or
    # CreateProcess invocation.
    return f'"{launcher}" "{target_script}"'
