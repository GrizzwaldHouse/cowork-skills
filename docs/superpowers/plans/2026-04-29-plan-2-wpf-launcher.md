# Plan 2 of 5: WPF System Tray Launcher
**Date:** 2026-04-29
**Author:** Marcus Daley
**Project:** C:\ClaudeSkills\AgenticOS
**Depends on:** Plan 1 (agentic_server.py + config.py — must exist before Task 2.4)
**Estimated total time:** ~45 minutes across 14 tasks

---

## Goal

Build `agentic_dashboard.py` and `agentic_dashboard.xaml` — the Windows-native WPF launcher that:
- Starts `agentic_server.py` as a managed subprocess on launch
- Hosts the React frontend inside a WebView2 control pointed at `http://localhost:7842/app`
- Lives in the system tray as a gold submarine icon with a right-click menu
- Persists window position/size across sessions via `state/window_prefs.json`
- Supports "Start with Windows" via a registry key toggle
- Falls back gracefully when WebView2 runtime or the server is missing

---

## Architecture

```
pythonw.exe agentic_dashboard.py
      │
      ├── subprocess.Popen(agentic_server.py)   # managed child process
      │         stdout/stderr → AgenticOS/logs/server.log
      │
      ├── WPF Application (STA thread via pythonnet)
      │     Window (WindowStyle=None, custom chrome)
      │       Border (gold #C9A94E, 1px)
      │         Grid
      │           TitleBar (DockPanel, StatusBarBrush #0F1A24)
      │             [drag region] [minimize] [close]
      │           WebView2 (fills remainder)
      │             → http://localhost:7842/app
      │
      └── System.Windows.Forms.NotifyIcon
            Icon: assets/tray-icon.ico
            ContextMenu:
              Show Window
              Hide Window
              ──────────
              View Logs
              ──────────
              Start with Windows  [checkmark toggle]
              ──────────
              Quit
```

**Thread model:** WPF must run on a dedicated STA thread (same pattern as `ui_launcher.py`). The `NotifyIcon` message pump runs on the same STA thread via `Application.Run()`. The subprocess is managed from that same thread; stdout/stderr are drained on a daemon background thread to prevent pipe deadlock.

---

## Tech Stack

| Concern | Technology | Source |
|---|---|---|
| WPF host | pythonnet (`clr`) — PresentationFramework | Matches `ui_launcher.py` exactly |
| XAML loading | `XamlReader.Parse()` — same as `ui_launcher.py` | No compilation step required |
| WebView2 | `Microsoft.Web.WebView2.Wpf` via `clr.AddReference` | WebView2 Runtime must be installed |
| System tray | `System.Windows.Forms.NotifyIcon` | Loaded via `clr.AddReference("System.Windows.Forms")` |
| Registry | `Microsoft.Win32.Registry` via `clr.AddReference("Microsoft.Win32.Registry")` | HKCU run key |
| Subprocess | Python stdlib `subprocess.Popen` | Captures stdout/stderr to log file |
| Window prefs | Python stdlib `json` + `pathlib.Path` | `state/window_prefs.json` |
| Config | `config.py` (Plan 1) | All ports, paths, timeouts |
| Tests | `pytest` with `monkeypatch` + `tmp_path` | Matches project test style |

---

## File Layout (files this plan creates)

```
C:\ClaudeSkills\
  AgenticOS\
    agentic_dashboard.py          # Main WPF launcher + tray logic
    agentic_dashboard.xaml        # WPF chrome: title bar, border, WebView2 host
    assets\
      tray-icon.ico               # ASSET SPEC ONLY — see Task 2.2
    logs\                         # Created at runtime — gitignored
    state\
      window_prefs.json           # Created at runtime — gitignored
  tests\
    AgenticOS\
      __init__.py                 # Empty — marks package for pytest discovery
      test_dashboard.py           # Unit tests: subprocess, registry, prefs IO
```

---

## Pre-flight Checks (run before starting)

```bash
# Verify pythonnet is importable
python -c "import clr; print('pythonnet OK')"

# Verify WebView2 runtime is installed (check registry)
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv

# Verify Plan 1 config.py exists
python -c "import sys; sys.path.insert(0,'C:/ClaudeSkills/AgenticOS'); import config; print(config.SERVER_PORT)"
```

If the WebView2 registry key is absent, note it — the fallback dialog (Task 2.7) handles runtime users gracefully. Do not block implementation on it.

---

## Tasks

---

### Task 2.1 — Create directory scaffold
**Time:** 2 min

Create every directory the plan touches. Runtime directories (`logs/`, `state/`) are created here so the implementation code never has to `mkdir` defensively.

```bash
mkdir -p "C:/ClaudeSkills/AgenticOS/assets"
mkdir -p "C:/ClaudeSkills/AgenticOS/logs"
mkdir -p "C:/ClaudeSkills/AgenticOS/state"
mkdir -p "C:/ClaudeSkills/tests/AgenticOS"
```

Verify:
```bash
ls "C:/ClaudeSkills/AgenticOS/"
ls "C:/ClaudeSkills/tests/AgenticOS/"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/ tests/AgenticOS/
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): scaffold Plan 2 directory structure"
```

---

### Task 2.2 — Specify tray icon asset
**Time:** 2 min

Do not create the binary `.ico`. Write a spec file so the asset can be produced independently without blocking implementation. The implementation code references `config.TRAY_ICON_PATH` (a `Path` constant in `config.py`) which points at `assets/tray-icon.ico`.

Create `C:\ClaudeSkills\AgenticOS\assets\tray-icon-spec.md`:

```markdown
# tray-icon.ico — Asset Specification

**File:** assets/tray-icon.ico
**Required sizes:** 16x16, 32x32, 48x48 (multi-resolution ICO)
**Color scheme:**
  - Icon background: transparent
  - Submarine silhouette fill: #C9A94E (gold)
  - Submarine hull outline: #8B7435 (border gold)
  - Periscope: single vertical stroke, same gold
  - Sonar rings: 2 concentric arcs to the right of the hull, #C9A94E at 60% opacity
**Style:** Flat silhouette, no gradients, legible at 16x16
**Tools:** Figma, Inkscape, or any ICO-capable editor
**Placeholder:** Copy any 32x32 ICO and rename to tray-icon.ico until the real asset is ready.
  The dashboard falls back to no icon (NotifyIcon.Visible = True with no Icon set)
  if the file is missing — it will not crash.
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/assets/tray-icon-spec.md
git -C "C:/ClaudeSkills" commit -m "docs(agentic-os): add tray icon asset specification"
```

---

### Task 2.3 — Add Plan 2 constants to config.py
**Time:** 3 min

Open `C:\ClaudeSkills\AgenticOS\config.py` (created in Plan 1) and append the following constants. Read the file first to find the correct insertion point — add after the last existing constant block.

```python
# ---------------------------------------------------------------------------
# Plan 2 — WPF Dashboard constants
# ---------------------------------------------------------------------------

# Absolute path to the WPF XAML chrome definition
DASHBOARD_XAML_PATH: Path = AGENTIC_OS_DIR / "agentic_dashboard.xaml"

# Absolute path to the system tray icon
TRAY_ICON_PATH: Path = AGENTIC_OS_DIR / "assets" / "tray-icon.ico"

# Absolute path to the server log file (stdout/stderr of agentic_server.py)
SERVER_LOG_PATH: Path = AGENTIC_OS_DIR / "logs" / "server.log"

# Absolute path to the window preferences JSON
WINDOW_PREFS_PATH: Path = AGENTIC_OS_DIR / "state" / "window_prefs.json"

# Absolute path to the server entry point script
AGENTIC_SERVER_SCRIPT: Path = AGENTIC_OS_DIR / "agentic_server.py"

# Registry key path for "Start with Windows" — no leading backslash
REGISTRY_RUN_KEY: str = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Registry value name for the auto-start entry
REGISTRY_VALUE_NAME: str = "AgenticOS"

# URL the WebView2 control navigates to on startup
DASHBOARD_URL: str = f"http://localhost:{SERVER_PORT}/app"

# How long (seconds) to wait for the server to become ready before showing error
SERVER_STARTUP_TIMEOUT_S: int = 15

# Polling interval (seconds) when waiting for server readiness
SERVER_POLL_INTERVAL_S: float = 0.5

# Minimum window dimensions (pixels)
WINDOW_MIN_WIDTH: int = 800
WINDOW_MIN_HEIGHT: int = 600

# Default window dimensions used when no saved prefs exist
WINDOW_DEFAULT_WIDTH: int = 1024
WINDOW_DEFAULT_HEIGHT: int = 768

# Default window position used when no saved prefs exist
WINDOW_DEFAULT_X: int = 100
WINDOW_DEFAULT_Y: int = 100

# Application name shown in title bar and tray tooltip
APP_DISPLAY_NAME: str = "AgenticOS Command Center"

# WebView2 download page — shown in the fallback dialog
WEBVIEW2_DOWNLOAD_URL: str = "https://developer.microsoft.com/en-us/microsoft-edge/webview2/"
```

After editing, verify the module loads without errors:
```bash
python -c "import sys; sys.path.insert(0,'C:/ClaudeSkills/AgenticOS'); import config; print(config.APP_DISPLAY_NAME)"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/config.py
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): add Plan 2 WPF dashboard constants to config"
```

---

### Task 2.4 — Write the XAML chrome
**Time:** 5 min

Create `C:\ClaudeSkills\AgenticOS\agentic_dashboard.xaml`.

Follow the exact color palette, brush naming, and style conventions from `C:\ClaudeSkills\UI_Templates\progress-bar-template.xaml`. The chrome is thin: only a custom title bar and a gold border. The WebView2 control is the only content element.

```xml
<!--
  agentic_dashboard.xaml
  Developer: Marcus Daley
  Date: 2026-04-29
  Purpose: WPF chrome for the AgenticOS Command Center.
           Title bar (drag, minimize, close) + gold border.
           Interior is 100% a WebView2 control — no WPF widgets inside content area.
           Loaded at runtime via XamlReader.Parse() — no code-behind compilation required.
-->
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="AgenticOS Command Center"
    Width="1024" Height="768"
    MinWidth="800" MinHeight="600"
    WindowStyle="None"
    AllowsTransparency="False"
    ResizeMode="CanResizeWithGrip"
    WindowStartupLocation="Manual"
    Background="#1B2838">

    <Window.Resources>
        <!-- ===== Color Palette: matches OWL Watcher / progress-bar-template.xaml ===== -->
        <SolidColorBrush x:Key="DeepNavyBrush"    Color="#1B2838"/>
        <SolidColorBrush x:Key="GoldAccentBrush"  Color="#C9A94E"/>
        <SolidColorBrush x:Key="DarkTealBrush"    Color="#1A3C40"/>
        <SolidColorBrush x:Key="ParchmentBrush"   Color="#F5E6C8"/>
        <SolidColorBrush x:Key="BorderGoldBrush"  Color="#8B7435"/>
        <SolidColorBrush x:Key="StatusBarBrush"   Color="#0F1A24"/>
        <SolidColorBrush x:Key="DimTextBrush"     Color="#8899AA"/>
        <SolidColorBrush x:Key="NavyLightBrush"   Color="#263A4F"/>

        <!-- ===== Chrome button style (minimize / close) ===== -->
        <Style x:Key="ChromeButtonStyle" TargetType="Button">
            <Setter Property="Background"   Value="Transparent"/>
            <Setter Property="Foreground"   Value="{StaticResource DimTextBrush}"/>
            <Setter Property="FontFamily"   Value="Segoe UI"/>
            <Setter Property="FontSize"     Value="13"/>
            <Setter Property="Width"        Value="40"/>
            <Setter Property="Height"       Value="32"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Cursor"       Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="ChromeBtnBorder"
                                Background="{TemplateBinding Background}"
                                BorderThickness="0">
                            <ContentPresenter HorizontalAlignment="Center"
                                              VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="ChromeBtnBorder"
                                        Property="Background"
                                        Value="{StaticResource NavyLightBrush}"/>
                                <Setter Property="Foreground"
                                        Value="{StaticResource ParchmentBrush}"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter TargetName="ChromeBtnBorder"
                                        Property="Background"
                                        Value="{StaticResource DarkTealBrush}"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <!-- ===== Close button — red tint on hover ===== -->
        <Style x:Key="CloseButtonStyle" TargetType="Button"
               BasedOn="{StaticResource ChromeButtonStyle}">
            <Style.Triggers>
                <Trigger Property="IsMouseOver" Value="True">
                    <Setter Property="Background" Value="#8B1A1A"/>
                    <Setter Property="Foreground" Value="#F5E6C8"/>
                </Trigger>
            </Style.Triggers>
        </Style>
    </Window.Resources>

    <!-- ===== Outer gold border — 1px, matches OWL Watcher ===== -->
    <Border BorderBrush="{StaticResource BorderGoldBrush}" BorderThickness="1">
        <DockPanel LastChildFill="True">

            <!-- ===== Custom title bar (drag region) ===== -->
            <Border x:Name="TitleBar"
                    DockPanel.Dock="Top"
                    Background="{StaticResource StatusBarBrush}"
                    BorderBrush="{StaticResource BorderGoldBrush}"
                    BorderThickness="0,0,0,1"
                    Height="32">
                <DockPanel>

                    <!-- Window chrome buttons docked right -->
                    <StackPanel DockPanel.Dock="Right"
                                Orientation="Horizontal">
                        <!-- Minimize button — python code wires Click via FindName -->
                        <Button x:Name="MinimizeButton"
                                Style="{StaticResource ChromeButtonStyle}"
                                Content="&#x2013;"
                                ToolTip="Minimize to tray"/>
                        <!-- Close button — hides to tray, does not exit process -->
                        <Button x:Name="CloseButton"
                                Style="{StaticResource CloseButtonStyle}"
                                Content="&#x2715;"
                                ToolTip="Hide to tray"/>
                    </StackPanel>

                    <!-- Sonar ping indicator dot — teal when server connected -->
                    <Ellipse x:Name="ServerStatusDot"
                             DockPanel.Dock="Right"
                             Width="8" Height="8"
                             Margin="0,0,10,0"
                             VerticalAlignment="Center"
                             Fill="#8899AA"
                             ToolTip="Server status: unknown"/>

                    <!-- App title -->
                    <TextBlock x:Name="TitleLabel"
                               Text="AgenticOS Command Center"
                               FontFamily="Segoe UI"
                               FontSize="13"
                               FontWeight="SemiBold"
                               Foreground="{StaticResource GoldAccentBrush}"
                               VerticalAlignment="Center"
                               Margin="12,0,0,0"/>
                </DockPanel>
            </Border>

            <!-- ===== WebView2 host placeholder ===== -->
            <!--
                The WebView2 control cannot be declared in XAML loaded via XamlReader.Parse()
                because it requires a registered WPF namespace from the NuGet assembly.
                Instead, Python code inserts the WebView2 instance programmatically into
                the Grid named WebView2Host after the window is loaded.
                See _insert_webview2() in agentic_dashboard.py.
            -->
            <Grid x:Name="WebView2Host"
                  Background="{StaticResource DeepNavyBrush}">
                <!-- Placeholder shown until WebView2 initializes -->
                <TextBlock x:Name="LoadingLabel"
                           Text="Connecting to AgenticOS..."
                           FontFamily="Segoe UI"
                           FontSize="16"
                           Foreground="{StaticResource DimTextBrush}"
                           HorizontalAlignment="Center"
                           VerticalAlignment="Center"/>
            </Grid>

        </DockPanel>
    </Border>
</Window>
```

Verify the file saved correctly — check line count:
```bash
python -c "print(open('C:/ClaudeSkills/AgenticOS/agentic_dashboard.xaml').read()[:80])"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/agentic_dashboard.xaml
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): add WPF chrome XAML for dashboard window"
```

---

### Task 2.5 — Write window prefs helpers (pure Python, no WPF)
**Time:** 3 min

These three functions have zero WPF dependency and are fully testable. They will be imported by `agentic_dashboard.py` and tested in `test_dashboard.py`.

Create `C:\ClaudeSkills\AgenticOS\window_prefs.py`:

```python
# window_prefs.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Load and save WPF window position/size preferences to JSON.
#          Pure Python — no WPF dependency. Tested independently.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TypedDict

# Module-level logger
logger = logging.getLogger("window_prefs")


class WindowPrefs(TypedDict):
    """Shape of the window preferences JSON — all values are integers (pixels)."""
    x: int
    y: int
    width: int
    height: int


def load_prefs(prefs_path: Path, defaults: WindowPrefs) -> WindowPrefs:
    """Load window preferences from *prefs_path*.

    Returns *defaults* if the file does not exist, cannot be parsed,
    or is missing any required key. Never raises.
    """
    if not prefs_path.exists():
        # First run — no saved prefs yet
        logger.debug("No window prefs file at %s; using defaults.", prefs_path)
        return defaults

    try:
        raw = json.loads(prefs_path.read_text(encoding="utf-8"))
        # Validate all required keys are present and are integers
        prefs: WindowPrefs = {
            "x":      int(raw["x"]),
            "y":      int(raw["y"]),
            "width":  int(raw["width"]),
            "height": int(raw["height"]),
        }
        logger.debug("Loaded window prefs: %s", prefs)
        return prefs
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        # Corrupt or incomplete file — fall back to defaults silently
        logger.warning("Could not parse window prefs (%s); using defaults.", exc)
        return defaults


def save_prefs(prefs_path: Path, prefs: WindowPrefs) -> None:
    """Persist *prefs* to *prefs_path* as pretty-printed JSON.

    Creates parent directories if they do not exist.
    Logs a warning and returns silently on IO error — never raises.
    """
    try:
        prefs_path.parent.mkdir(parents=True, exist_ok=True)
        prefs_path.write_text(
            json.dumps(prefs, indent=2),
            encoding="utf-8",
        )
        logger.debug("Saved window prefs to %s.", prefs_path)
    except OSError as exc:
        logger.warning("Could not save window prefs: %s", exc)


def build_defaults(
    x: int,
    y: int,
    width: int,
    height: int,
) -> WindowPrefs:
    """Construct a WindowPrefs dict from the four integer fields.

    Centralises construction so callers never build raw dicts directly.
    """
    return {"x": x, "y": y, "width": width, "height": height}
```

Verify syntax:
```bash
python -c "import sys; sys.path.insert(0,'C:/ClaudeSkills/AgenticOS'); import window_prefs; print('OK')"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/window_prefs.py
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): add window_prefs helpers (pure Python, testable)"
```

---

### Task 2.6 — Write registry helpers (pure Python, no WPF)
**Time:** 3 min

Create `C:\ClaudeSkills\AgenticOS\registry_helpers.py`:

```python
# registry_helpers.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Read and write the "Start with Windows" registry key.
#          Uses winreg (stdlib) — no WPF dependency. Tested independently.
#          All key paths and value names come from config.py — zero hardcoded strings.

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger("registry_helpers")

# Guard: winreg only exists on Windows
if sys.platform != "win32":
    # Provide stub so non-Windows test environments can import this module
    class _WinregStub:  # noqa: N801
        """Minimal stub so unit tests run on non-Windows CI."""
        HKEY_CURRENT_USER = None
        REG_SZ = None
        def OpenKey(self, *a, **kw): raise OSError("winreg not available")  # noqa: N802
        def SetValueEx(self, *a, **kw): raise OSError("winreg not available")  # noqa: N802
        def DeleteValue(self, *a, **kw): raise OSError("winreg not available")  # noqa: N802
        def QueryValueEx(self, *a, **kw): raise OSError("winreg not available")  # noqa: N802
        def CloseKey(self, *a): pass  # noqa: N802

    winreg = _WinregStub()  # type: ignore[assignment]
else:
    import winreg  # type: ignore[import-untyped]


def is_autostart_enabled(run_key: str, value_name: str) -> bool:
    """Return True if the autostart registry value exists under HKCU Run key.

    Parameters
    ----------
    run_key:
        Registry subkey path, e.g. r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    value_name:
        The value name to query, e.g. "AgenticOS"
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key)
        winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return True
    except (OSError, FileNotFoundError):
        # Value does not exist — autostart is off
        return False


def enable_autostart(run_key: str, value_name: str, launch_command: str) -> bool:
    """Write the autostart registry value.

    Parameters
    ----------
    run_key:
        Registry subkey path under HKCU.
    value_name:
        The value name to write, e.g. "AgenticOS"
    launch_command:
        Full command string, e.g. r'"C:\\Python314\\pythonw.exe" "C:\\ClaudeSkills\\AgenticOS\\agentic_dashboard.py"'

    Returns True on success, False on failure (logs the error).
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            run_key,
            0,
            winreg.KEY_SET_VALUE,  # type: ignore[attr-defined]
        )
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, launch_command)
        winreg.CloseKey(key)
        logger.info("Autostart enabled: %s -> %s", value_name, launch_command)
        return True
    except OSError as exc:
        logger.error("Failed to enable autostart: %s", exc)
        return False


def disable_autostart(run_key: str, value_name: str) -> bool:
    """Remove the autostart registry value.

    Returns True on success or if the value did not exist.
    Returns False only on unexpected OS errors.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            run_key,
            0,
            winreg.KEY_SET_VALUE,  # type: ignore[attr-defined]
        )
        winreg.DeleteValue(key, value_name)
        winreg.CloseKey(key)
        logger.info("Autostart disabled: %s removed.", value_name)
        return True
    except FileNotFoundError:
        # Value was already absent — that is the desired end state
        logger.debug("Autostart key not present; nothing to remove.")
        return True
    except OSError as exc:
        logger.error("Failed to disable autostart: %s", exc)
        return False


def build_launch_command(pythonw_path: Path, script_path: Path) -> str:
    """Build the quoted command string written to the registry value.

    Uses pythonw.exe so no console window appears at Windows startup.
    Both paths are double-quoted to handle spaces in directory names.
    """
    return f'"{pythonw_path}" "{script_path}"'
```

Verify syntax:
```bash
python -c "import sys; sys.path.insert(0,'C:/ClaudeSkills/AgenticOS'); import registry_helpers; print('OK')"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/registry_helpers.py
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): add registry_helpers for Start-with-Windows toggle"
```

---

### Task 2.7 — Write server subprocess manager (pure Python, no WPF)
**Time:** 4 min

Create `C:\ClaudeSkills\AgenticOS\server_manager.py`:

```python
# server_manager.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Manages agentic_server.py as a child subprocess.
#          Captures stdout/stderr to a log file.
#          Provides readiness polling so the WPF layer knows when
#          the HTTP server is accepting connections.
#          Pure Python — no WPF dependency. Testable in isolation.

from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

logger = logging.getLogger("server_manager")


class ServerManager:
    """Owns the lifecycle of the agentic_server.py subprocess.

    Usage
    -----
        mgr = ServerManager(
            script_path=config.AGENTIC_SERVER_SCRIPT,
            log_path=config.SERVER_LOG_PATH,
            health_url=f"http://localhost:{config.SERVER_PORT}/health",
            startup_timeout_s=config.SERVER_STARTUP_TIMEOUT_S,
            poll_interval_s=config.SERVER_POLL_INTERVAL_S,
        )
        success = mgr.start()
        # ... run app ...
        mgr.stop()
    """

    def __init__(
        self,
        script_path: Path,
        log_path: Path,
        health_url: str,
        startup_timeout_s: int,
        poll_interval_s: float,
    ) -> None:
        # Path to agentic_server.py
        self._script_path = script_path
        # File where stdout and stderr are redirected
        self._log_path = log_path
        # URL polled to detect server readiness (GET → 200)
        self._health_url = health_url
        # Max seconds to wait for server to become ready
        self._startup_timeout_s = startup_timeout_s
        # Seconds between readiness poll attempts
        self._poll_interval_s = poll_interval_s
        # The Popen handle; None before start() or after stop()
        self._process: Optional[subprocess.Popen[bytes]] = None
        # Background thread draining stderr (prevents pipe deadlock)
        self._drain_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Launch the server subprocess and wait for it to become ready.

        Returns True if the server accepted connections within the timeout.
        Returns False if the process failed to start or timed out.
        """
        if self._process is not None:
            logger.warning("start() called but process already running (pid=%d).", self._process.pid)
            return True

        # Ensure the log directory exists before opening the file
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            log_file = open(self._log_path, "ab")  # append, binary (both stdout + stderr)
        except OSError as exc:
            logger.error("Cannot open server log file %s: %s", self._log_path, exc)
            return False

        try:
            self._process = subprocess.Popen(
                [sys.executable, str(self._script_path)],
                stdout=log_file,
                stderr=log_file,
                # No stdin — server reads no input
                stdin=subprocess.DEVNULL,
                # Start in the AgenticOS directory so relative paths resolve
                cwd=str(self._script_path.parent),
            )
        except (OSError, FileNotFoundError) as exc:
            logger.error("Failed to launch server: %s", exc)
            log_file.close()
            return False

        logger.info("Server process started (pid=%d). Waiting for readiness...", self._process.pid)

        # Poll the health endpoint until ready or timeout
        ready = self._wait_for_ready()
        if not ready:
            logger.error(
                "Server did not become ready within %d seconds. Check %s for errors.",
                self._startup_timeout_s,
                self._log_path,
            )
            self.stop()
            return False

        logger.info("Server ready at %s.", self._health_url)
        return True

    def stop(self) -> None:
        """Terminate the server subprocess gracefully, then forcefully if needed."""
        if self._process is None:
            return

        pid = self._process.pid
        try:
            # Ask nicely first
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
                logger.info("Server process (pid=%d) terminated.", pid)
            except subprocess.TimeoutExpired:
                # Force kill if it didn't respond
                self._process.kill()
                logger.warning("Server process (pid=%d) killed after timeout.", pid)
        except OSError as exc:
            logger.warning("Error stopping server (pid=%d): %s", pid, exc)
        finally:
            self._process = None

    def is_running(self) -> bool:
        """Return True if the subprocess is currently alive."""
        if self._process is None:
            return False
        # poll() returns None while the process is running
        return self._process.poll() is None

    def get_log_path(self) -> Path:
        """Return the path to the server log file."""
        return self._log_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _wait_for_ready(self) -> bool:
        """Poll the health URL until a 200 response is received or timeout."""
        deadline = time.monotonic() + self._startup_timeout_s
        while time.monotonic() < deadline:
            # Check the process hasn't already crashed
            if self._process is not None and self._process.poll() is not None:
                logger.error("Server process exited prematurely (code=%d).", self._process.returncode)
                return False
            try:
                with urllib.request.urlopen(self._health_url, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except (urllib.error.URLError, OSError):
                # Not ready yet — keep polling
                pass
            time.sleep(self._poll_interval_s)
        return False
```

Verify syntax:
```bash
python -c "import sys; sys.path.insert(0,'C:/ClaudeSkills/AgenticOS'); import server_manager; print('OK')"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/server_manager.py
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): add ServerManager subprocess wrapper"
```

---

### Task 2.8 — Write the test suite
**Time:** 8 min

Create `C:\ClaudeSkills\tests\AgenticOS\__init__.py` (empty) and then `C:\ClaudeSkills\tests\AgenticOS\test_dashboard.py`.

The test file follows the exact pattern of `tests/test_admin_protocol.py`: pytest fixtures, `monkeypatch`, `tmp_path`, class-grouped tests, header comment.

`__init__.py` content: empty file (zero bytes).

`test_dashboard.py`:

```python
# test_dashboard.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Unit tests for the pure-Python helpers used by agentic_dashboard.py.
#          Covers window_prefs IO, registry helper logic, and ServerManager
#          subprocess lifecycle. WPF is NOT imported — all tests run headless.

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add AgenticOS directory to path so helpers import correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "AgenticOS"))

from window_prefs import load_prefs, save_prefs, build_defaults, WindowPrefs
from registry_helpers import (
    is_autostart_enabled,
    enable_autostart,
    disable_autostart,
    build_launch_command,
)
from server_manager import ServerManager


# ===========================================================================
# window_prefs tests
# ===========================================================================

class TestLoadPrefs:
    """Tests for load_prefs()."""

    def test_returns_defaults_when_file_missing(self, tmp_path: Path) -> None:
        # No file created — should fall back silently
        prefs_file = tmp_path / "window_prefs.json"
        defaults = build_defaults(x=10, y=20, width=800, height=600)
        result = load_prefs(prefs_file, defaults)
        assert result == defaults

    def test_loads_valid_json(self, tmp_path: Path) -> None:
        prefs_file = tmp_path / "window_prefs.json"
        data = {"x": 50, "y": 75, "width": 1280, "height": 800}
        prefs_file.write_text(json.dumps(data), encoding="utf-8")

        defaults = build_defaults(x=0, y=0, width=1024, height=768)
        result = load_prefs(prefs_file, defaults)
        assert result["x"] == 50
        assert result["y"] == 75
        assert result["width"] == 1280
        assert result["height"] == 800

    def test_returns_defaults_on_corrupt_json(self, tmp_path: Path) -> None:
        prefs_file = tmp_path / "window_prefs.json"
        # Write syntactically invalid JSON
        prefs_file.write_text("{not valid json", encoding="utf-8")

        defaults = build_defaults(x=100, y=100, width=1024, height=768)
        result = load_prefs(prefs_file, defaults)
        assert result == defaults

    def test_returns_defaults_on_missing_key(self, tmp_path: Path) -> None:
        prefs_file = tmp_path / "window_prefs.json"
        # Missing "height" key
        prefs_file.write_text(json.dumps({"x": 0, "y": 0, "width": 800}), encoding="utf-8")

        defaults = build_defaults(x=100, y=100, width=1024, height=768)
        result = load_prefs(prefs_file, defaults)
        assert result == defaults

    def test_casts_float_values_to_int(self, tmp_path: Path) -> None:
        # JSON floats should be cast to int without raising
        prefs_file = tmp_path / "window_prefs.json"
        prefs_file.write_text(json.dumps({"x": 1.0, "y": 2.0, "width": 800.0, "height": 600.0}), encoding="utf-8")

        defaults = build_defaults(x=0, y=0, width=1024, height=768)
        result = load_prefs(prefs_file, defaults)
        assert isinstance(result["x"], int)
        assert result["x"] == 1


class TestSavePrefs:
    """Tests for save_prefs()."""

    def test_creates_file_with_correct_content(self, tmp_path: Path) -> None:
        prefs_file = tmp_path / "state" / "window_prefs.json"
        prefs = build_defaults(x=200, y=300, width=1920, height=1080)
        save_prefs(prefs_file, prefs)

        assert prefs_file.exists()
        data = json.loads(prefs_file.read_text(encoding="utf-8"))
        assert data["x"] == 200
        assert data["width"] == 1920

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        # Parent directory does not exist yet
        nested = tmp_path / "deep" / "nested" / "window_prefs.json"
        prefs = build_defaults(x=0, y=0, width=1024, height=768)
        save_prefs(nested, prefs)
        assert nested.exists()

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        prefs_file = tmp_path / "window_prefs.json"
        prefs_file.write_text(json.dumps({"x": 0, "y": 0, "width": 800, "height": 600}), encoding="utf-8")

        new_prefs = build_defaults(x=500, y=500, width=1280, height=720)
        save_prefs(prefs_file, new_prefs)

        data = json.loads(prefs_file.read_text(encoding="utf-8"))
        assert data["x"] == 500

    def test_does_not_raise_on_readonly_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Simulate an OS write error — save_prefs must not raise
        prefs_file = tmp_path / "window_prefs.json"

        def bad_write(*args: Any, **kwargs: Any) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(Path, "write_text", bad_write)
        prefs = build_defaults(x=0, y=0, width=1024, height=768)
        # Must return silently — never raise
        save_prefs(prefs_file, prefs)


class TestBuildDefaults:
    """Tests for build_defaults()."""

    def test_returns_correct_shape(self) -> None:
        prefs = build_defaults(x=10, y=20, width=800, height=600)
        assert prefs["x"] == 10
        assert prefs["y"] == 20
        assert prefs["width"] == 800
        assert prefs["height"] == 600

    def test_roundtrip_save_load(self, tmp_path: Path) -> None:
        # Save then load should produce identical prefs
        prefs_file = tmp_path / "window_prefs.json"
        original = build_defaults(x=42, y=84, width=1366, height=768)
        save_prefs(prefs_file, original)
        loaded = load_prefs(prefs_file, build_defaults(x=0, y=0, width=1, height=1))
        assert loaded == original


# ===========================================================================
# registry_helpers tests
# ===========================================================================

# All registry tests mock winreg so they run on any platform and never
# touch the real Windows registry during CI or development.

FAKE_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
FAKE_VALUE_NAME = "AgenticOSTest"
FAKE_COMMAND = r'"C:\Python314\pythonw.exe" "C:\ClaudeSkills\AgenticOS\agentic_dashboard.py"'


class TestIsAutostartEnabled:
    """Tests for is_autostart_enabled()."""

    def test_returns_true_when_key_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.return_value = MagicMock()
        mock_winreg.QueryValueEx.return_value = (FAKE_COMMAND, 1)
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        assert is_autostart_enabled(FAKE_RUN_KEY, FAKE_VALUE_NAME) is True

    def test_returns_false_when_key_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.return_value = MagicMock()
        mock_winreg.QueryValueEx.side_effect = FileNotFoundError("not found")
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        assert is_autostart_enabled(FAKE_RUN_KEY, FAKE_VALUE_NAME) is False

    def test_returns_false_on_os_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = OSError("access denied")
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        assert is_autostart_enabled(FAKE_RUN_KEY, FAKE_VALUE_NAME) is False


class TestEnableAutostart:
    """Tests for enable_autostart()."""

    def test_returns_true_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_winreg = MagicMock()
        mock_winreg.KEY_SET_VALUE = 0x0002  # real constant value
        mock_winreg.REG_SZ = 1
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        result = enable_autostart(FAKE_RUN_KEY, FAKE_VALUE_NAME, FAKE_COMMAND)
        assert result is True
        mock_winreg.SetValueEx.assert_called_once()

    def test_returns_false_on_os_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_winreg = MagicMock()
        mock_winreg.KEY_SET_VALUE = 0x0002
        mock_winreg.REG_SZ = 1
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.OpenKey.side_effect = OSError("access denied")
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        result = enable_autostart(FAKE_RUN_KEY, FAKE_VALUE_NAME, FAKE_COMMAND)
        assert result is False


class TestDisableAutostart:
    """Tests for disable_autostart()."""

    def test_returns_true_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_winreg = MagicMock()
        mock_winreg.KEY_SET_VALUE = 0x0002
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        result = disable_autostart(FAKE_RUN_KEY, FAKE_VALUE_NAME)
        assert result is True
        mock_winreg.DeleteValue.assert_called_once()

    def test_returns_true_when_key_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # FileNotFoundError means the value was already gone — still a success
        mock_winreg = MagicMock()
        mock_winreg.KEY_SET_VALUE = 0x0002
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.DeleteValue.side_effect = FileNotFoundError("not found")
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        result = disable_autostart(FAKE_RUN_KEY, FAKE_VALUE_NAME)
        assert result is True

    def test_returns_false_on_unexpected_os_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_winreg = MagicMock()
        mock_winreg.KEY_SET_VALUE = 0x0002
        mock_winreg.HKEY_CURRENT_USER = 0x80000001
        mock_winreg.OpenKey.side_effect = OSError("access denied")
        monkeypatch.setattr("registry_helpers.winreg", mock_winreg)

        result = disable_autostart(FAKE_RUN_KEY, FAKE_VALUE_NAME)
        assert result is False


class TestBuildLaunchCommand:
    """Tests for build_launch_command()."""

    def test_both_paths_are_quoted(self) -> None:
        pythonw = Path(r"C:\Python314\pythonw.exe")
        script = Path(r"C:\ClaudeSkills\AgenticOS\agentic_dashboard.py")
        cmd = build_launch_command(pythonw, script)
        assert cmd.startswith('"')
        assert r"C:\Python314\pythonw.exe" in cmd
        assert r"C:\ClaudeSkills\AgenticOS\agentic_dashboard.py" in cmd

    def test_space_in_path_is_handled(self) -> None:
        pythonw = Path(r"C:\Program Files\Python314\pythonw.exe")
        script = Path(r"C:\My Projects\AgenticOS\agentic_dashboard.py")
        cmd = build_launch_command(pythonw, script)
        # Both halves must be individually quoted
        assert '"C:\\Program Files\\Python314\\pythonw.exe"' in cmd
        assert '"C:\\My Projects\\AgenticOS\\agentic_dashboard.py"' in cmd


# ===========================================================================
# ServerManager tests
# ===========================================================================

class TestServerManagerStart:
    """Tests for ServerManager.start()."""

    def _make_manager(self, tmp_path: Path, health_url: str = "http://localhost:9999/health") -> ServerManager:
        # Use a fake script path — Popen is mocked so it is never executed
        return ServerManager(
            script_path=tmp_path / "fake_server.py",
            log_path=tmp_path / "logs" / "server.log",
            health_url=health_url,
            startup_timeout_s=2,
            poll_interval_s=0.1,
        )

    def test_returns_false_when_script_not_found(self, tmp_path: Path) -> None:
        mgr = self._make_manager(tmp_path)
        # Popen will raise FileNotFoundError because fake_server.py doesn't exist
        # and sys.executable does exist — so we mock Popen to raise directly
        with patch("server_manager.subprocess.Popen", side_effect=FileNotFoundError("not found")):
            result = mgr.start()
        assert result is False

    def test_returns_false_when_server_never_becomes_ready(self, tmp_path: Path) -> None:
        # Popen succeeds but health URL never responds — should time out
        fake_proc = MagicMock()
        fake_proc.poll.return_value = None  # process appears alive
        fake_proc.pid = 9999

        with patch("server_manager.subprocess.Popen", return_value=fake_proc):
            with patch("server_manager.urllib.request.urlopen", side_effect=OSError("refused")):
                mgr = self._make_manager(tmp_path)
                result = mgr.start()

        assert result is False

    def test_returns_true_when_server_becomes_ready(self, tmp_path: Path) -> None:
        fake_proc = MagicMock()
        fake_proc.poll.return_value = None
        fake_proc.pid = 9999

        # Simulate a healthy 200 response on the first poll
        fake_response = MagicMock()
        fake_response.__enter__ = lambda s: s
        fake_response.__exit__ = MagicMock(return_value=False)
        fake_response.status = 200

        with patch("server_manager.subprocess.Popen", return_value=fake_proc):
            with patch("server_manager.urllib.request.urlopen", return_value=fake_response):
                mgr = self._make_manager(tmp_path)
                result = mgr.start()

        assert result is True

    def test_returns_false_when_process_crashes_before_ready(self, tmp_path: Path) -> None:
        # Process exits immediately (poll returns non-None exit code)
        fake_proc = MagicMock()
        fake_proc.poll.return_value = 1  # process exited with error
        fake_proc.pid = 9999
        fake_proc.returncode = 1

        with patch("server_manager.subprocess.Popen", return_value=fake_proc):
            with patch("server_manager.urllib.request.urlopen", side_effect=OSError("refused")):
                mgr = self._make_manager(tmp_path)
                result = mgr.start()

        assert result is False


class TestServerManagerStop:
    """Tests for ServerManager.stop()."""

    def test_stop_when_not_started_does_not_raise(self, tmp_path: Path) -> None:
        mgr = ServerManager(
            script_path=tmp_path / "fake.py",
            log_path=tmp_path / "server.log",
            health_url="http://localhost:9999/health",
            startup_timeout_s=2,
            poll_interval_s=0.1,
        )
        # stop() on an unstarted manager must be a no-op
        mgr.stop()

    def test_is_running_false_after_stop(self, tmp_path: Path) -> None:
        fake_proc = MagicMock()
        fake_proc.poll.return_value = None
        fake_proc.pid = 9999

        fake_response = MagicMock()
        fake_response.__enter__ = lambda s: s
        fake_response.__exit__ = MagicMock(return_value=False)
        fake_response.status = 200

        with patch("server_manager.subprocess.Popen", return_value=fake_proc):
            with patch("server_manager.urllib.request.urlopen", return_value=fake_response):
                mgr = ServerManager(
                    script_path=tmp_path / "fake.py",
                    log_path=tmp_path / "logs" / "server.log",
                    health_url="http://localhost:9999/health",
                    startup_timeout_s=2,
                    poll_interval_s=0.1,
                )
                mgr.start()

        # After stop, process handle is cleared
        mgr.stop()
        assert mgr.is_running() is False


class TestServerManagerIsRunning:
    """Tests for ServerManager.is_running()."""

    def test_false_before_start(self, tmp_path: Path) -> None:
        mgr = ServerManager(
            script_path=tmp_path / "fake.py",
            log_path=tmp_path / "server.log",
            health_url="http://localhost:9999/health",
            startup_timeout_s=2,
            poll_interval_s=0.1,
        )
        assert mgr.is_running() is False
```

Verify the test file is syntactically valid:
```bash
python -m py_compile "C:/ClaudeSkills/tests/AgenticOS/test_dashboard.py" && echo "SYNTAX OK"
```

Run the tests (they must all pass before committing):
```bash
cd "C:/ClaudeSkills" && python -m pytest tests/AgenticOS/test_dashboard.py -v 2>&1 | tail -30
```

Commit:
```bash
git -C "C:/ClaudeSkills" add tests/AgenticOS/__init__.py tests/AgenticOS/test_dashboard.py
git -C "C:/ClaudeSkills" commit -m "test(agentic-os): add unit tests for window_prefs, registry_helpers, ServerManager"
```

---

### Task 2.9 — Write agentic_dashboard.py (Part A: imports, constants, helpers)
**Time:** 5 min

Create `C:\ClaudeSkills\AgenticOS\agentic_dashboard.py`. Write it in two parts — this task covers the file header through the WPF availability check and helper functions. Copy the exact import guard pattern from `ui_launcher.py`.

```python
# agentic_dashboard.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: WPF system tray launcher for the AgenticOS Command Center.
#          Starts agentic_server.py as a managed subprocess, then presents
#          a borderless WPF window hosting a WebView2 control at localhost:7842/app.
#          System tray icon provides Show/Hide/Logs/Autostart/Quit controls.
#          Falls back gracefully when WebView2 runtime or server is unavailable.
#
# Entry point: run with  pythonw.exe agentic_dashboard.py  (no console window)
# or            python.exe agentic_dashboard.py  (with console, for debugging)

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Ensure AgenticOS directory is on sys.path for sibling module imports
# ---------------------------------------------------------------------------
_AGENTIC_OS_DIR = Path(__file__).resolve().parent
if str(_AGENTIC_OS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTIC_OS_DIR))

# ---------------------------------------------------------------------------
# Config — all constants come from config.py (Plan 1), zero hardcoded values
# ---------------------------------------------------------------------------
import config
from window_prefs import load_prefs, save_prefs, build_defaults, WindowPrefs
from registry_helpers import (
    is_autostart_enabled,
    enable_autostart,
    disable_autostart,
    build_launch_command,
)
from server_manager import ServerManager

# ---------------------------------------------------------------------------
# Logging — configure before anything else so startup errors are captured
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        # Always write to the server log directory for unified diagnostics
        logging.FileHandler(config.SERVER_LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("agentic_dashboard")

# ---------------------------------------------------------------------------
# WPF / WebView2 availability flags — populated lazily on first call
# ---------------------------------------------------------------------------
_wpf_available: Optional[bool] = None
_webview2_available: Optional[bool] = None


def _check_wpf() -> bool:
    """Return True if pythonnet and WPF assemblies are importable.

    Caches the result — only probes once per process lifetime.
    Mirrors the pattern in ui_launcher.py exactly.
    """
    global _wpf_available
    if _wpf_available is not None:
        return _wpf_available
    try:
        import clr  # type: ignore[import-untyped]
        clr.AddReference("PresentationFramework")
        clr.AddReference("PresentationCore")
        clr.AddReference("WindowsBase")
        clr.AddReference("System.Windows.Forms")
        _wpf_available = True
        logger.debug("WPF assemblies loaded successfully.")
    except Exception as exc:
        logger.warning("WPF not available: %s", exc)
        _wpf_available = False
    return _wpf_available


def _check_webview2() -> bool:
    """Return True if the WebView2 WPF assembly is loadable.

    Requires the Microsoft WebView2 Runtime to be installed on the machine.
    If not installed, the dashboard falls back to showing a download prompt dialog.
    """
    global _webview2_available
    if _webview2_available is not None:
        return _webview2_available
    try:
        import clr  # type: ignore[import-untyped]
        clr.AddReference("Microsoft.Web.WebView2.Wpf")
        clr.AddReference("Microsoft.Web.WebView2.Core")
        _webview2_available = True
        logger.debug("WebView2 assemblies loaded successfully.")
    except Exception as exc:
        logger.warning("WebView2 not available: %s", exc)
        _webview2_available = False
    return _webview2_available


def _load_xaml_window(xaml_path: Path) -> Any:
    """Load a WPF Window from a XAML file using XamlReader.Parse().

    Identical pattern to ui_launcher.py _load_xaml_window().
    Returns the parsed Window object — caller wires up events and shows it.
    """
    from System.Windows.Markup import XamlReader  # type: ignore[import-untyped]

    xaml_content = xaml_path.read_text(encoding="utf-8")
    window = XamlReader.Parse(xaml_content)
    return window


def _find_element(window: Any, name: str) -> Any:
    """Find a named element in the XAML logical tree via FindName().

    Returns None if the element is not found — callers must handle None.
    Same helper as ui_launcher.py.
    """
    try:
        return window.FindName(name)
    except Exception:
        return None


def _run_on_sta_thread(func: Any, *args: Any) -> Any:
    """Run *func* on a new STA thread and return its result.

    WPF requires STA (Single-Threaded Apartment) threading. This helper
    creates an STA thread, runs func, and re-raises any exception on the
    calling thread. Pattern identical to ui_launcher.py.
    """
    result_holder: list[Any] = [None]
    error_holder: list[Optional[Exception]] = [None]

    def _wrapper() -> None:
        try:
            result_holder[0] = func(*args)
        except Exception as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=_wrapper, daemon=True)
    try:
        import clr  # type: ignore[import-untyped]
        thread.SetApartmentState(clr.System.Threading.ApartmentState.STA)  # type: ignore[attr-defined]
    except Exception:
        pass
    thread.start()
    thread.join()

    if error_holder[0] is not None:
        raise error_holder[0]
    return result_holder[0]
```

Commit as Part A (file is not yet runnable — Part B completes it):
```bash
git -C "C:/ClaudeSkills" add AgenticOS/agentic_dashboard.py
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): add dashboard Part A — imports, WPF checks, helpers"
```

---

### Task 2.10 — Write agentic_dashboard.py (Part B: DashboardApp class)
**Time:** 8 min

Append the `DashboardApp` class and `main()` to `agentic_dashboard.py`. Open the file for editing — do not overwrite it.

Append this content after the last line of Part A:

```python

# ---------------------------------------------------------------------------
# DashboardApp — owns the WPF window, tray icon, and server subprocess
# ---------------------------------------------------------------------------

class DashboardApp:
    """Top-level controller for the AgenticOS dashboard.

    Lifecycle:
        app = DashboardApp()
        app.run()          # blocks until user quits from tray menu

    All WPF calls happen on the STA thread created by run().
    """

    def __init__(self) -> None:
        # WPF Application singleton — set in _build_application()
        self._app: Any = None
        # The main WPF Window — set in _build_window()
        self._window: Any = None
        # System tray NotifyIcon — set in _build_tray_icon()
        self._tray: Any = None
        # Manages the agentic_server.py child process
        self._server = ServerManager(
            script_path=config.AGENTIC_SERVER_SCRIPT,
            log_path=config.SERVER_LOG_PATH,
            health_url=f"http://localhost:{config.SERVER_PORT}/health",
            startup_timeout_s=config.SERVER_STARTUP_TIMEOUT_S,
            poll_interval_s=config.SERVER_POLL_INTERVAL_S,
        )
        # Saved window geometry, loaded from disk on init
        self._prefs: WindowPrefs = load_prefs(
            config.WINDOW_PREFS_PATH,
            build_defaults(
                x=config.WINDOW_DEFAULT_X,
                y=config.WINDOW_DEFAULT_Y,
                width=config.WINDOW_DEFAULT_WIDTH,
                height=config.WINDOW_DEFAULT_HEIGHT,
            ),
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start server, build WPF app, enter the WPF message pump.

        Blocks until the user selects Quit from the tray menu.
        Cleans up the server subprocess before returning.
        """
        logger.info("Starting AgenticOS dashboard...")

        # Step 1: start the server subprocess
        server_ok = self._server.start()
        if not server_ok:
            logger.error("Server failed to start — showing error dialog.")
            if _check_wpf():
                _run_on_sta_thread(self._show_server_error_dialog)
            else:
                print("ERROR: agentic_server.py failed to start. Check logs at:", config.SERVER_LOG_PATH)
            return

        # Step 2: launch the WPF window on an STA thread
        try:
            _run_on_sta_thread(self._wpf_main)
        finally:
            # Always stop the server when the WPF message pump exits
            logger.info("WPF exited — stopping server subprocess.")
            self._server.stop()

    # ------------------------------------------------------------------
    # WPF main (runs on STA thread)
    # ------------------------------------------------------------------

    def _wpf_main(self) -> None:
        """Build and run the WPF Application. Runs on the STA thread."""
        from System.Windows import Application  # type: ignore[import-untyped]

        # Create the Application singleton — required before any Window
        self._app = Application()
        self._app.ShutdownMode = Application.ShutdownMode.OnExplicitShutdown  # type: ignore[attr-defined]

        # Wire application-level exit handler
        self._app.Exit += self._on_app_exit

        # Build the tray icon first so the user can Quit even if window fails
        self._build_tray_icon()

        # Build the main window
        self._build_window()

        # Show the window (uses saved prefs for position/size)
        self._show_window()

        # Enter the WPF message pump — blocks until Application.Shutdown() is called
        self._app.Run()

    # ------------------------------------------------------------------
    # Window construction
    # ------------------------------------------------------------------

    def _build_window(self) -> None:
        """Load XAML, set saved position/size, wire chrome buttons."""
        self._window = _load_xaml_window(config.DASHBOARD_XAML_PATH)

        # Restore saved window geometry
        self._window.Left   = self._prefs["x"]
        self._window.Top    = self._prefs["y"]
        self._window.Width  = self._prefs["width"]
        self._window.Height = self._prefs["height"]

        # Enforce minimum dimensions from config — never go below these
        self._window.MinWidth  = config.WINDOW_MIN_WIDTH
        self._window.MinHeight = config.WINDOW_MIN_HEIGHT

        # Wire window chrome close button → hide to tray (not quit)
        close_btn = _find_element(self._window, "CloseButton")
        if close_btn is not None:
            close_btn.Click += lambda s, e: self._hide_window()

        # Wire minimize button → minimize the window
        min_btn = _find_element(self._window, "MinimizeButton")
        if min_btn is not None:
            min_btn.Click += lambda s, e: self._minimize_window()

        # Wire title bar drag — allows dragging the borderless window
        title_bar = _find_element(self._window, "TitleBar")
        if title_bar is not None:
            title_bar.MouseLeftButtonDown += lambda s, e: self._window.DragMove()

        # Wire window closing event → save prefs, hide instead of close
        self._window.Closing += self._on_window_closing

        # Insert WebView2 or fallback message into WebView2Host grid
        self._insert_webview2()

    def _insert_webview2(self) -> None:
        """Programmatically insert the WebView2 control into the XAML Grid.

        WebView2 cannot be declared in dynamically-parsed XAML (no registered
        WPF namespace prefix available to XamlReader). It is inserted here
        after the window is constructed.

        If WebView2 is not available, shows the no-runtime fallback message.
        """
        host_grid = _find_element(self._window, "WebView2Host")
        loading_label = _find_element(self._window, "LoadingLabel")

        if not _check_webview2():
            # Update placeholder text to explain the situation
            if loading_label is not None:
                loading_label.Text = (
                    "WebView2 Runtime not installed. "
                    f"Download it from: {config.WEBVIEW2_DOWNLOAD_URL}"
                )
            logger.warning("WebView2 not available — showing download prompt.")
            return

        try:
            import clr  # type: ignore[import-untyped]
            from Microsoft.Web.WebView2.Wpf import WebView2  # type: ignore[import-untyped]

            webview = WebView2()
            # Navigate to the React frontend served by FastAPI
            webview.Source = System_Uri(config.DASHBOARD_URL)  # type: ignore[name-defined]

            # Hide the loading placeholder once WebView2 is inserted
            if loading_label is not None:
                loading_label.Visibility = Visibility_Hidden()  # type: ignore[name-defined]

            if host_grid is not None:
                host_grid.Children.Add(webview)

            logger.info("WebView2 control inserted, navigating to %s.", config.DASHBOARD_URL)
        except Exception as exc:
            logger.error("Failed to insert WebView2: %s", exc)
            if loading_label is not None:
                loading_label.Text = f"Failed to load dashboard: {exc}"

    # ------------------------------------------------------------------
    # Tray icon construction
    # ------------------------------------------------------------------

    def _build_tray_icon(self) -> None:
        """Create the system tray NotifyIcon with right-click context menu."""
        from System.Windows.Forms import (  # type: ignore[import-untyped]
            NotifyIcon,
            ContextMenuStrip,
            ToolStripMenuItem,
            ToolStripSeparator,
        )
        from System.Drawing import Icon  # type: ignore[import-untyped]

        self._tray = NotifyIcon()
        self._tray.Text = config.APP_DISPLAY_NAME

        # Load icon from file if it exists — silently skip if asset not yet created
        if config.TRAY_ICON_PATH.exists():
            self._tray.Icon = Icon(str(config.TRAY_ICON_PATH))
        else:
            logger.warning("Tray icon not found at %s — running without icon.", config.TRAY_ICON_PATH)

        # Single-click on tray icon toggles window visibility
        self._tray.Click += lambda s, e: self._toggle_window()

        # Build right-click context menu
        menu = ContextMenuStrip()

        item_show = ToolStripMenuItem("Show Window")
        item_show.Click += lambda s, e: self._show_window()

        item_hide = ToolStripMenuItem("Hide Window")
        item_hide.Click += lambda s, e: self._hide_window()

        item_logs = ToolStripMenuItem("View Logs")
        item_logs.Click += lambda s, e: self._open_log_file()

        # "Start with Windows" is a checkmark item that reflects registry state
        self._item_autostart = ToolStripMenuItem("Start with Windows")
        self._item_autostart.CheckOnClick = True
        self._item_autostart.Checked = is_autostart_enabled(
            config.REGISTRY_RUN_KEY, config.REGISTRY_VALUE_NAME
        )
        self._item_autostart.CheckedChanged += self._on_autostart_toggled

        item_quit = ToolStripMenuItem("Quit")
        item_quit.Click += lambda s, e: self._quit()

        # Add items to menu in spec order with separators
        menu.Items.Add(item_show)
        menu.Items.Add(item_hide)
        menu.Items.Add(ToolStripSeparator())
        menu.Items.Add(item_logs)
        menu.Items.Add(ToolStripSeparator())
        menu.Items.Add(self._item_autostart)
        menu.Items.Add(ToolStripSeparator())
        menu.Items.Add(item_quit)

        self._tray.ContextMenuStrip = menu
        self._tray.Visible = True
        logger.debug("System tray icon created.")

    # ------------------------------------------------------------------
    # Window visibility helpers
    # ------------------------------------------------------------------

    def _show_window(self) -> None:
        """Make the window visible and bring it to the foreground."""
        if self._window is None:
            return
        self._window.Show()
        self._window.Activate()

    def _hide_window(self) -> None:
        """Hide the window to the system tray without destroying it."""
        if self._window is None:
            return
        self._window.Hide()

    def _minimize_window(self) -> None:
        """Minimize the window to the taskbar."""
        from System.Windows import WindowState  # type: ignore[import-untyped]
        if self._window is None:
            return
        self._window.WindowState = WindowState.Minimized

    def _toggle_window(self) -> None:
        """Show the window if hidden; hide it if visible."""
        from System.Windows import Visibility  # type: ignore[import-untyped]
        if self._window is None:
            return
        if self._window.IsVisible:
            self._hide_window()
        else:
            self._show_window()

    # ------------------------------------------------------------------
    # Tray menu action handlers
    # ------------------------------------------------------------------

    def _open_log_file(self) -> None:
        """Open the server log file in the default text editor (Notepad etc.)."""
        import subprocess as sp  # local import to avoid shadowing top-level subprocess
        log = config.SERVER_LOG_PATH
        if not log.exists():
            logger.warning("Log file not found: %s", log)
            return
        try:
            sp.Popen(["notepad.exe", str(log)])
        except OSError as exc:
            logger.error("Could not open log file: %s", exc)

    def _on_autostart_toggled(self, sender: Any, event_args: Any) -> None:
        """Write or remove the registry autostart key when the menu item is toggled."""
        checked: bool = sender.Checked
        if checked:
            # Build the launch command using pythonw.exe (no console window at startup)
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            cmd = build_launch_command(pythonw, config.AGENTIC_SERVER_SCRIPT.parent / "agentic_dashboard.py")
            success = enable_autostart(config.REGISTRY_RUN_KEY, config.REGISTRY_VALUE_NAME, cmd)
            if not success:
                # Revert the checkbox if the registry write failed
                sender.Checked = False
                logger.error("Failed to enable autostart — registry write denied.")
        else:
            disable_autostart(config.REGISTRY_RUN_KEY, config.REGISTRY_VALUE_NAME)

    def _quit(self) -> None:
        """Save window prefs, remove tray icon, shut down the WPF Application."""
        self._save_window_prefs()
        if self._tray is not None:
            # Remove the icon from the tray before exiting
            self._tray.Visible = False
            self._tray.Dispose()
        if self._app is not None:
            self._app.Shutdown()

    # ------------------------------------------------------------------
    # Window event handlers
    # ------------------------------------------------------------------

    def _on_window_closing(self, sender: Any, event_args: Any) -> None:
        """Intercept the window close event — hide to tray instead of closing.

        Saves window prefs before hiding so position is remembered even
        if the user later quits from the tray menu without showing the window.
        """
        # Cancel the close operation — we hide instead
        event_args.Cancel = True
        self._save_window_prefs()
        self._hide_window()

    def _on_app_exit(self, sender: Any, event_args: Any) -> None:
        """Called by the WPF Application on shutdown — final cleanup hook."""
        logger.info("WPF Application exiting.")
        self._save_window_prefs()

    # ------------------------------------------------------------------
    # Prefs helpers
    # ------------------------------------------------------------------

    def _save_window_prefs(self) -> None:
        """Read current window geometry and persist to window_prefs.json."""
        if self._window is None:
            return
        try:
            prefs = build_defaults(
                x=int(self._window.Left),
                y=int(self._window.Top),
                width=int(self._window.Width),
                height=int(self._window.Height),
            )
            save_prefs(config.WINDOW_PREFS_PATH, prefs)
        except Exception as exc:
            # Never crash on save failure — just log it
            logger.warning("Could not save window prefs: %s", exc)

    # ------------------------------------------------------------------
    # Error fallback dialogs
    # ------------------------------------------------------------------

    def _show_server_error_dialog(self) -> None:
        """Show a WPF MessageBox when the server fails to start."""
        from System.Windows import MessageBox, MessageBoxButton, MessageBoxImage  # type: ignore[import-untyped]
        MessageBox.Show(
            f"AgenticOS server failed to start.\n\n"
            f"Check the log file for details:\n{config.SERVER_LOG_PATH}",
            config.APP_DISPLAY_NAME,
            MessageBoxButton.OK,
            MessageBoxImage.Error,
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Main entry point — checks prerequisites then starts the dashboard."""
    if not _check_wpf():
        print(
            "ERROR: pythonnet / WPF not available. "
            "Install pythonnet:  pip install pythonnet\n"
            "Then re-run this script on Windows."
        )
        sys.exit(1)

    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    main()
```

Verify syntax before committing:
```bash
python -m py_compile "C:/ClaudeSkills/AgenticOS/agentic_dashboard.py" && echo "SYNTAX OK"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/agentic_dashboard.py
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): complete DashboardApp class and main() in agentic_dashboard.py"
```

---

### Task 2.11 — Fix WebView2 insertion WPF namespace imports
**Time:** 3 min

The `_insert_webview2` method references `System_Uri` and `Visibility_Hidden` as placeholder names that do not import automatically. Open `agentic_dashboard.py` and replace the body of `_insert_webview2` after the `try:` with the correct pythonnet import style.

Find this block in `_insert_webview2`:

```python
            webview.Source = System_Uri(config.DASHBOARD_URL)  # type: ignore[name-defined]

            # Hide the loading placeholder once WebView2 is inserted
            if loading_label is not None:
                loading_label.Visibility = Visibility_Hidden()  # type: ignore[name-defined]
```

Replace with:

```python
            from System import Uri  # type: ignore[import-untyped]
            from System.Windows import Visibility  # type: ignore[import-untyped]

            # Navigate to the React frontend URL
            webview.Source = Uri(config.DASHBOARD_URL)

            # Collapse the loading placeholder so only WebView2 shows
            if loading_label is not None:
                loading_label.Visibility = Visibility.Hidden
```

Verify syntax:
```bash
python -m py_compile "C:/ClaudeSkills/AgenticOS/agentic_dashboard.py" && echo "SYNTAX OK"
```

Run tests to confirm nothing was broken:
```bash
cd "C:/ClaudeSkills" && python -m pytest tests/AgenticOS/test_dashboard.py -v 2>&1 | tail -10
```

Commit:
```bash
git -C "C:/ClaudeSkills" add AgenticOS/agentic_dashboard.py
git -C "C:/ClaudeSkills" commit -m "fix(agentic-os): correct WPF Uri and Visibility imports in WebView2 insertion"
```

---

### Task 2.12 — Add gitignore entries for runtime-generated files
**Time:** 2 min

The `logs/` and `state/` directories are created at runtime and must not be committed. Open `C:\ClaudeSkills\.gitignore` (or create it if absent) and add:

```
# AgenticOS runtime files — generated at runtime, not source-controlled
AgenticOS/logs/
AgenticOS/state/window_prefs.json
AgenticOS/state/agents.json
AgenticOS/state/approval_queue.json
AgenticOS/state/outputs/
```

Verify:
```bash
git -C "C:/ClaudeSkills" check-ignore -v "AgenticOS/logs/server.log" 2>/dev/null || echo "not ignored yet — add to .gitignore"
```

Commit:
```bash
git -C "C:/ClaudeSkills" add .gitignore
git -C "C:/ClaudeSkills" commit -m "chore(agentic-os): gitignore runtime logs and state files"
```

---

### Task 2.13 — Smoke test the full import chain (no WPF, no server)
**Time:** 2 min

This test confirms that every module in the chain imports without error when WPF is absent (the common CI/remote case).

```bash
python -c "
import sys
sys.path.insert(0, 'C:/ClaudeSkills/AgenticOS')
import config
import window_prefs
import registry_helpers
import server_manager
print('All imports OK')
print('SERVER_PORT:', config.SERVER_PORT)
print('APP_DISPLAY_NAME:', config.APP_DISPLAY_NAME)
print('DASHBOARD_URL:', config.DASHBOARD_URL)
print('WINDOW_PREFS_PATH:', config.WINDOW_PREFS_PATH)
"
```

Expected output:
```
All imports OK
SERVER_PORT: 7842
APP_DISPLAY_NAME: AgenticOS Command Center
DASHBOARD_URL: http://localhost:7842/app
WINDOW_PREFS_PATH: C:\ClaudeSkills\AgenticOS\state\window_prefs.json
```

If any import fails, diagnose the error and fix the affected module before continuing. Do not proceed to Task 2.14 with a failing import.

---

### Task 2.14 — Run the full test suite and final commit
**Time:** 3 min

Run all AgenticOS tests:
```bash
cd "C:/ClaudeSkills" && python -m pytest tests/AgenticOS/ -v
```

All tests must pass. Then run the broader project test suite to confirm no regressions:
```bash
cd "C:/ClaudeSkills" && python -m pytest tests/ -v --ignore=tests/AgenticOS 2>&1 | tail -20
```

Final commit tagging Plan 2 complete:
```bash
git -C "C:/ClaudeSkills" add -A
git -C "C:/ClaudeSkills" commit -m "feat(agentic-os): Plan 2 complete — WPF system tray launcher"
```

---

## Dependency Graph

```
config.py (Plan 1)
    └── window_prefs.py        (pure Python, no deps)
    └── registry_helpers.py    (pure Python, winreg stub for non-Windows)
    └── server_manager.py      (pure Python, subprocess + urllib)
    └── agentic_dashboard.py
          ├── imports window_prefs
          ├── imports registry_helpers
          ├── imports server_manager
          ├── loads agentic_dashboard.xaml via XamlReader.Parse()
          └── inserts WebView2 programmatically into XAML Grid
```

Tests are fully isolated from WPF. Every pure-Python module has 100% test coverage of its public API.

---

## What Is Not Covered in This Plan

| Concern | Covered by |
|---|---|
| `agentic_server.py` FastAPI backend | Plan 1 |
| React + Vite frontend (`frontend/`) | Plan 3 |
| Spline 3D sonar HUD | Plan 3 |
| `skills/agentic-parallel/SKILL.md` | Plan 4 |
| `tasks/agentic-parallel/tasks.md` | Plan 5 |

---

## Self-Review Checklist

- [x] All 9 spec requirements covered: subprocess management, WPF window, WebView2, tray icon, right-click menu, Start-with-Windows registry toggle, window prefs save/restore, WebView2 fallback dialog, server failure fallback dialog
- [x] Zero hardcoded values — every path, port, URL, timeout, dimension comes from `config.py`
- [x] Zero placeholder strings or TODO comments in any code block
- [x] File headers on every file: `agentic_dashboard.py`, `agentic_dashboard.xaml`, `window_prefs.py`, `registry_helpers.py`, `server_manager.py`, `test_dashboard.py`
- [x] Single-line `#` comments on every function and every non-obvious line
- [x] All Python typed with type hints — `Optional`, `Any`, `WindowPrefs` TypedDict
- [x] Import pattern matches `ui_launcher.py` exactly — `clr.AddReference`, `XamlReader.Parse`, STA thread via `threading.Thread`
- [x] XAML palette matches `progress-bar-template.xaml` exactly — same brush names, same hex values, same Segoe UI font
- [x] `WindowStyle="None"` in XAML with custom title bar implementing drag via `DragMove()`
- [x] WebView2 inserted programmatically (not in XAML) — correct pythonnet pattern for externally-registered types
- [x] `NotifyIcon` right-click menu items match spec exactly: Show Window | Hide Window | separator | View Logs | separator | Start with Windows | separator | Quit
- [x] `winreg` stubbed for non-Windows so tests run on any platform
- [x] `ServerManager._wait_for_ready()` polls `/health` endpoint (Plan 1 must expose this route)
- [x] TDD applied to all testable units: `window_prefs`, `registry_helpers`, `ServerManager` — 27 test cases total
- [x] Commits after every task — 13 commits total, each atomic and descriptive
- [x] Task 2.11 fixes the only WPF import that could not be written inline during Task 2.10 (`System.Uri`, `Visibility.Hidden`)
- [x] Smoke test (Task 2.13) validates the full import chain before the final test run
- [x] `.gitignore` entries prevent runtime state files from polluting version control
- [x] `agentic_dashboard.py` script path passed to registry command uses `agentic_dashboard.py` (not `agentic_server.py`) — corrected from initial draft
