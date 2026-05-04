# AgenticOS Command Center -- WPF Launcher

Developer: Marcus Daley
Date: 2026-04-29
Purpose: Operator-facing guide to the Windows-native launcher that
hosts the AgenticOS Command Center inside a borderless WPF window
with a system-tray icon and a managed FastAPI backend.

## What it does

`agentic_dashboard.py` is the single entry point a user double-clicks
(or pins to the Start menu) to bring the AgenticOS Command Center up.
On launch it:

1. Acquires a named Win32 mutex so a second double-click does not
   start a duplicate process.
2. Loads pythonnet, registers the WPF assemblies, and parses
   `agentic_dashboard.xaml` from disk.
3. Spawns `python -m AgenticOS.agentic_server` as a managed child
   under `process_supervisor.ProcessSupervisor`. Stdout and stderr
   are captured to `AgenticOS/logs/server.log` so a crash leaves a
   forensics trail.
4. Polls the `/healthz` endpoint until it returns 200, then
   navigates the embedded WebView2 control to
   `http://127.0.0.1:7842/app`. If the React build is missing the
   FastAPI splash served at `/` is used instead.
5. Pins a gold submarine glyph in the system tray with a right-click
   menu (Show / Hide / View Logs / Start with Windows / Quit) and a
   single-click Show toggle.
6. Persists the user's window rectangle to
   `AgenticOS/state/window_prefs.json` on every hide/quit.

## Prerequisites

- Windows 11 (Windows 10 may work but is not the supported target).
- Python 3.11 or newer with `pythonnet` and `pywin32` installed:
  `pip install -r AgenticOS/dashboard/requirements.txt`
- Microsoft WebView2 Runtime: download from
  <https://developer.microsoft.com/en-us/microsoft-edge/webview2/>.
  The launcher detects a missing runtime and shows a dialog with the
  same link instead of crashing.

## Running it

From an elevated or standard PowerShell prompt at the repo root:

```powershell
pwsh C:/ClaudeSkills/launch_agentic_os.ps1
```

The PowerShell launcher resolves the active interpreter, sets
`PYTHONPATH` so the `AgenticOS` package is importable, and invokes
`python -m AgenticOS.dashboard.agentic_dashboard` with logging.

You can also run the dashboard directly:

```bash
python -m AgenticOS.dashboard.agentic_dashboard
```

## Enabling autostart

Right-click the tray icon and tick `Start with Windows`. The launcher
writes the following registry value:

- Hive: `HKEY_CURRENT_USER`
- Key:  `Software\Microsoft\Windows\CurrentVersion\Run`
- Name: `AgenticOS`
- Data: `"<pythonw.exe>" "<repo>\AgenticOS\dashboard\agentic_dashboard.py"`

Untick the menu item to remove the value. Failures (rare; usually
caused by group policy) revert the menu state automatically.

## Where logs live

| Stream | Path |
| --- | --- |
| Dashboard launcher | `AgenticOS/logs/dashboard.log` |
| FastAPI server (stdout + stderr) | `AgenticOS/logs/server.log` |
| Window geometry | `AgenticOS/state/window_prefs.json` |

The `View Logs` tray entry opens `server.log` in Notepad on Windows.

## Troubleshooting

- The dashboard window is empty / shows the install link: WebView2
  Runtime is missing. Install it and relaunch.
- The supervisor log shows repeated restarts: open `server.log` to
  read the FastAPI traceback. Common causes are a port conflict on
  7842 (another dashboard already running, or an OWL Watcher port
  clash) or a Python import error inside `AgenticOS.agentic_server`.
- The tray icon does not appear: verify `tray-icon.ico` is a real
  multi-resolution ICO (the placeholder shipped in source control is
  intentionally a text file). The dashboard works without an icon
  but the tray slot will look blank.

## Related code

| File | Role |
| --- | --- |
| `agentic_dashboard.py` | Main launcher / WPF host |
| `agentic_dashboard.xaml` | Borderless chrome and palette |
| `process_supervisor.py` | uvicorn child lifecycle and restart policy |
| `tray_icon.py` | NotifyIcon and ContextMenuStrip wiring |
| `webview_host.py` | WebView2 detection, instantiation, fallback |
| `registry_helper.py` | HKCU Run-key read/write/delete |
| `config.py` | Every dashboard constant |
