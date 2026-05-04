# config.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Dashboard-scoped constants for the AgenticOS Command Center
#          WPF launcher. Re-exports the upstream AgenticOS.config values
#          the dashboard depends on (ports, server paths) and adds the
#          launcher-only values (window dimensions, registry locations,
#          tray asset paths). Every value lives here so no other module
#          in the dashboard package ever hardcodes a constant.

from __future__ import annotations

from pathlib import Path
from typing import Final

# Reach into the parent AgenticOS package for the values that already
# exist there so the dashboard does not duplicate truth. If the upstream
# value ever changes (e.g. server moves to a new port) the dashboard
# follows automatically.
from AgenticOS.config import (
    AGENTIC_DIR,
    REST_PORT,
    SERVER_HOST,
    STATE_DIR,
    WEBSOCKET_PORT,
)


# ---------------------------------------------------------------------------
# Package paths
# ---------------------------------------------------------------------------

# Filesystem root of the dashboard package. Resolved at import time so
# the value is correct regardless of the current working directory of
# the launching shell. Using __file__ keeps the dashboard relocatable.
DASHBOARD_DIR: Final[Path] = Path(__file__).resolve().parent

# Folder holding the XAML chrome, tray glyph, fonts, and any future
# brand artwork. Co-located with the package so a single git move
# relocates the whole launcher.
ASSETS_DIR: Final[Path] = DASHBOARD_DIR / "assets"

# Absolute path to the WPF chrome description that XamlReader.Parse
# loads at startup. Centralising the path avoids duplicating the
# filename in both the loader and the docs.
DASHBOARD_XAML_PATH: Final[Path] = DASHBOARD_DIR / "agentic_dashboard.xaml"

# Tray icon asset. The placeholder shipped in source control is a PNG;
# the icon loader expects a Windows .ico, so the assets README explains
# how a designer converts the placeholder. The launcher tolerates a
# missing file so a developer can run the dashboard before the asset
# pipeline is wired up.
TRAY_ICON_PATH: Final[Path] = ASSETS_DIR / "tray-icon.ico"


# ---------------------------------------------------------------------------
# Logging targets
# ---------------------------------------------------------------------------

# Folder containing every dashboard-emitted log file. Created on first
# write by ProcessSupervisor; gitignored at the repository level.
LOGS_DIR: Final[Path] = AGENTIC_DIR / "logs"

# Combined stdout/stderr capture from the supervised uvicorn server.
# Kept in a single file so the View Logs tray action can hand it
# directly to Notepad without picking between streams.
SERVER_LOG_PATH: Final[Path] = LOGS_DIR / "server.log"

# Dashboard-process log: separate from the server log so a startup
# crash in the launcher does not get tangled with a server crash.
DASHBOARD_LOG_PATH: Final[Path] = LOGS_DIR / "dashboard.log"


# ---------------------------------------------------------------------------
# Window preferences storage
# ---------------------------------------------------------------------------

# Folder that holds the JSON file persisting the user's last window
# rectangle. Sits inside the existing STATE_DIR so all runtime data
# lives in one place and is covered by the same .gitignore rule.
WINDOW_PREFS_PATH: Final[Path] = STATE_DIR / "window_prefs.json"


# ---------------------------------------------------------------------------
# Server lifecycle tuning
# ---------------------------------------------------------------------------

# Maximum number of times ProcessSupervisor will relaunch the uvicorn
# child after an unexpected exit. Capped to avoid a runaway crash loop
# eating CPU when a deeper problem (port conflict, code bug) needs
# human attention.
MAX_RESTART_ATTEMPTS: Final[int] = 5

# Seconds to wait before the first restart attempt. Subsequent attempts
# double this delay (exponential backoff) up to RESTART_BACKOFF_CAP_S.
RESTART_BACKOFF_INITIAL_S: Final[float] = 1.0

# Hard ceiling on the backoff so a stuck process never waits longer
# than 30 seconds between attempts; keeps recovery responsive.
RESTART_BACKOFF_CAP_S: Final[float] = 30.0

# Seconds the supervisor waits for the child to honour SIGINT/terminate
# before escalating to SIGTERM/kill. Kept short because the FastAPI app
# acknowledges shutdown promptly under normal conditions.
GRACEFUL_SHUTDOWN_TIMEOUT_S: Final[float] = 5.0

# Seconds to wait for the FastAPI /healthz route to return 200 after
# launch before declaring the server stuck. Mirrors the health check
# documented in the spec.
SERVER_STARTUP_TIMEOUT_S: Final[int] = 20

# Seconds between health probes during startup. Small enough that the
# UI feels responsive, large enough that we are not spamming the loop.
SERVER_POLL_INTERVAL_S: Final[float] = 0.5


# ---------------------------------------------------------------------------
# Window geometry
# ---------------------------------------------------------------------------

# Hard floor on user resize so the WebView2 host always has room for
# the React layout (which is designed at 800x600 minimum).
WINDOW_MIN_WIDTH: Final[int] = 800
WINDOW_MIN_HEIGHT: Final[int] = 600

# First-run default size: comfortable on a 1080p display while leaving
# room for the OWL Watcher window beside it.
WINDOW_DEFAULT_WIDTH: Final[int] = 1280
WINDOW_DEFAULT_HEIGHT: Final[int] = 800

# First-run default position: offset from origin so the window does not
# hide behind the Windows taskbar regardless of taskbar location.
WINDOW_DEFAULT_X: Final[int] = 120
WINDOW_DEFAULT_Y: Final[int] = 90


# ---------------------------------------------------------------------------
# Branding strings
# ---------------------------------------------------------------------------

# Human-readable product name. Reused in the title bar, tray tooltip,
# and any error dialog so the brand is consistent in one place only.
APP_DISPLAY_NAME: Final[str] = "AgenticOS Command Center"

# Named mutex used for the single-instance guard. The "Local\" prefix
# scopes the name to the user's logon session so two different users
# on the same machine each get their own dashboard.
SINGLE_INSTANCE_MUTEX_NAME: Final[str] = "Local\\AgenticOSCommandCenter.SingleInstance"


# ---------------------------------------------------------------------------
# Registry (Run key for "Start with Windows")
# ---------------------------------------------------------------------------

# Subkey under HKCU. No leading backslash; winreg.OpenKey expects a
# relative path. Constant lives here so the helper module never bakes
# the magic string in.
REGISTRY_RUN_KEY: Final[str] = (
    r"Software\Microsoft\Windows\CurrentVersion\Run"
)

# Value name written under the Run key. Matches the product name so an
# advanced user inspecting regedit immediately recognises the entry.
REGISTRY_VALUE_NAME: Final[str] = "AgenticOS"

# Test-mode value name used by the unit tests so they never collide
# with the user's real autostart entry. The helper exposes this so the
# test fixture does not duplicate the literal.
REGISTRY_TEST_VALUE_NAME: Final[str] = "AgenticOS-Test"


# ---------------------------------------------------------------------------
# WebView2
# ---------------------------------------------------------------------------

# Microsoft's runtime download page. Linked from the fallback dialog
# shown when the WebView2 assembly is not present on the host. Kept as
# a constant so a future redirect only needs one edit.
WEBVIEW2_DOWNLOAD_URL: Final[str] = (
    "https://developer.microsoft.com/en-us/microsoft-edge/webview2/"
)

# Set to True only in debug builds: enables F12 dev tools inside the
# WebView2 control. Toggled via the AGENTIC_DEBUG environment variable
# at module import time so production launches stay locked down.
import os as _os  # local alias: never re-exported
WEBVIEW2_DEVTOOLS_ENABLED: Final[bool] = (
    _os.environ.get("AGENTIC_DEBUG", "0").strip().lower() in {"1", "true", "yes"}
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def build_dashboard_url(host: str = SERVER_HOST, port: int = REST_PORT) -> str:
    """Return the URL the WebView2 control should navigate to.

    Defaults to the loopback host/port from AgenticOS.config so a single
    edit there relocates the dashboard. Exposed as a function rather
    than a constant so test code can build a URL pointing at a fake
    server on a different port without monkeypatching.
    """
    # Build with an explicit scheme so accidentally passing host="localhost:8080"
    # does not produce a malformed URL. The route /app is the SPA mount
    # point defined by FRONTEND_MOUNT_PATH in the upstream config; the
    # FastAPI splash at "/" is the natural fallback when the React build
    # is missing because StaticFiles is only mounted when dist/ exists.
    return f"http://{host}:{port}/app"


def resolve_python_executable() -> Path:
    """Return the Python interpreter the supervised server should run.

    Prefers the same interpreter that imported this module so the
    dashboard and the server share an environment (and therefore the
    same installed AgenticOS package). Falls back to the well-known
    Windows install location only if sys.executable is empty (which
    happens in some embedded launchers).
    """
    import sys

    # sys.executable is empty when Python is embedded; in that case the
    # most predictable fallback on Marcus's workstation is the system
    # python launcher.
    if sys.executable:
        return Path(sys.executable)
    return Path("py.exe")


def resolve_pythonw_executable() -> Path:
    """Return pythonw.exe alongside the active interpreter.

    The "Start with Windows" registry entry points at pythonw.exe so
    Windows does not flash a console window at logon. We derive the
    path from sys.executable to avoid hardcoding a Python version.
    """
    import sys

    interpreter = Path(sys.executable) if sys.executable else Path("python.exe")
    # with_name swaps the filename while preserving the directory, so
    # this works for both Python.org and embedded distributions.
    return interpreter.with_name("pythonw.exe")


def build_health_check_url(host: str = SERVER_HOST, port: int = REST_PORT) -> str:
    """Return the URL polled by ProcessSupervisor to detect readiness.

    The FastAPI app exposes /healthz (see agentic_server._register_routes).
    Centralising the path here means moving the route in one place
    updates the supervisor automatically.
    """
    return f"http://{host}:{port}/healthz"


# ---------------------------------------------------------------------------
# Re-exports
#
# Make the upstream values available as dashboard.config attributes so
# downstream modules import every constant from a single place.
# ---------------------------------------------------------------------------
__all__ = [
    "AGENTIC_DIR",
    "APP_DISPLAY_NAME",
    "ASSETS_DIR",
    "DASHBOARD_DIR",
    "DASHBOARD_LOG_PATH",
    "DASHBOARD_XAML_PATH",
    "GRACEFUL_SHUTDOWN_TIMEOUT_S",
    "LOGS_DIR",
    "MAX_RESTART_ATTEMPTS",
    "REGISTRY_RUN_KEY",
    "REGISTRY_TEST_VALUE_NAME",
    "REGISTRY_VALUE_NAME",
    "REST_PORT",
    "RESTART_BACKOFF_CAP_S",
    "RESTART_BACKOFF_INITIAL_S",
    "SERVER_HOST",
    "SERVER_LOG_PATH",
    "SERVER_POLL_INTERVAL_S",
    "SERVER_STARTUP_TIMEOUT_S",
    "SINGLE_INSTANCE_MUTEX_NAME",
    "STATE_DIR",
    "TRAY_ICON_PATH",
    "WEBSOCKET_PORT",
    "WEBVIEW2_DEVTOOLS_ENABLED",
    "WEBVIEW2_DOWNLOAD_URL",
    "WINDOW_DEFAULT_HEIGHT",
    "WINDOW_DEFAULT_WIDTH",
    "WINDOW_DEFAULT_X",
    "WINDOW_DEFAULT_Y",
    "WINDOW_MIN_HEIGHT",
    "WINDOW_MIN_WIDTH",
    "WINDOW_PREFS_PATH",
    "build_dashboard_url",
    "build_health_check_url",
    "resolve_python_executable",
    "resolve_pythonw_executable",
]
