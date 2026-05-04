# agentic_dashboard.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Python entry point for the AgenticOS Command Center launcher.
#          Hosts a borderless WPF window via pythonnet, embeds a
#          WebView2 control pointed at the supervised FastAPI server,
#          wires a system-tray icon for show / hide / logs / autostart
#          / quit, persists window geometry across sessions, and uses
#          a named Windows mutex to guarantee a single instance per
#          logged-on user.

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Optional

# Dashboard package imports. They live behind the AgenticOS namespace
# so the launcher can be run via -m and so the production layout
# matches the test layout exactly.
from AgenticOS.dashboard import config as dashboard_config
from AgenticOS.dashboard.process_supervisor import ProcessSupervisor
from AgenticOS.dashboard.registry_helper import (
    build_launch_command,
    delete_run_value,
    is_autostart_enabled,
    write_run_value,
)
from AgenticOS.dashboard.tray_icon import TrayCallbacks, TrayIcon
from AgenticOS.dashboard.webview_host import (
    WebView2NotInstalledError,
    WebViewHost,
    render_fallback_html,
)


# ---------------------------------------------------------------------------
# Logging
#
# Root logger is configured here, before any pythonnet import, so a
# crash inside CLR loading still writes a record to the dashboard log.
# Both file and stderr are wired up so a developer running from a
# console sees output immediately.
# ---------------------------------------------------------------------------

def _configure_logging() -> logging.Logger:
    """Set up dashboard logging and return the dashboard logger.

    Parameters:
        None.

    Returns:
        logging.Logger: The namespaced logger used by the WPF launcher.

    Notes:
        The function is idempotent: re-calling it does not duplicate
        handlers, which matters when the launcher is imported by pytest.
    """
    dashboard_config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if not getattr(root, "_agentic_dashboard_configured", False):
        root.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        # File handler: persistent record for post-mortem debugging.
        file_handler = logging.FileHandler(
            dashboard_config.DASHBOARD_LOG_PATH, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        # Stream handler: visible in the launching shell during dev.
        stream_handler = logging.StreamHandler(stream=sys.stderr)
        stream_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        root.addHandler(stream_handler)
        # Sentinel attribute prevents duplicate handlers on re-import.
        setattr(root, "_agentic_dashboard_configured", True)
    return logging.getLogger("AgenticOS.dashboard.agentic_dashboard")


_logger = _configure_logging()


# ---------------------------------------------------------------------------
# pythonnet / WPF availability probes
# ---------------------------------------------------------------------------

def _ensure_wpf_loaded() -> None:
    """Register every WPF assembly the launcher relies on.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        ImportError: If pythonnet's ``clr`` module is unavailable.
        Exception: If neither CLR name lookup nor explicit framework paths
            can load the required WPF/WinForms assemblies.

    Notes:
        Called once at startup; subsequent imports of System.Windows etc.
        rely on the side effects of clr.AddReference here. Some Python
        distributions cannot resolve .NET Framework WPF assemblies by
        display name, so this function falls back to explicit framework
        paths that are present on Windows 10/11 with .NET Framework 4.x.
    """
    import clr  # type: ignore[import-not-found]

    framework_paths = _resolve_wpf_framework_paths()
    for assembly_name in (
        "PresentationFramework",
        "PresentationCore",
        "WindowsBase",
        "System.Windows.Forms",
        "System.Drawing",
        "System",
    ):
        try:
            clr.AddReference(assembly_name)
        except Exception:
            explicit_path = framework_paths.get(assembly_name)
            if explicit_path is None:
                raise
            clr.AddReference(str(explicit_path))


def _resolve_wpf_framework_paths() -> dict[str, Path]:
    """Return explicit .NET Framework assembly paths for WPF startup.

    Parameters:
        None.

    Returns:
        dict[str, Path]: Mapping from assembly display name to an absolute
        DLL path. Missing files are omitted so callers can still raise the
        original CLR lookup error.

    Notes:
        pythonnet can load WPF by simple assembly name on some machines,
        but Python.org/uv standalone environments may not inherit the same
        probing paths. Returning explicit paths gives the launcher a stable
        second chance without requiring users to edit the Global Assembly
        Cache or machine-wide CLR settings.
    """
    framework_root = (
        Path(os.environ.get("WINDIR", "C:/Windows"))
        / "Microsoft.NET"
        / ("Framework64" if sys.maxsize > 2**32 else "Framework")
        / "v4.0.30319"
    )
    candidates = {
        "PresentationFramework": framework_root / "WPF" / "PresentationFramework.dll",
        "PresentationCore": framework_root / "WPF" / "PresentationCore.dll",
        "WindowsBase": framework_root / "WPF" / "WindowsBase.dll",
        "System.Windows.Forms": framework_root / "System.Windows.Forms.dll",
        "System.Drawing": framework_root / "System.Drawing.dll",
        "System": framework_root / "System.dll",
    }
    return {name: path for name, path in candidates.items() if path.exists()}


# ---------------------------------------------------------------------------
# Single-instance guard
# ---------------------------------------------------------------------------

class SingleInstanceGuard:
    """Acquire a named Win32 mutex; release on dispose.

    Implements the QSharedMemory equivalent the user asked for using
    the kernel32 named-mutex primitive. Holding a reference to the
    handle for the lifetime of the dashboard prevents a second copy of
    the launcher from succeeding.
    """

    def __init__(self, mutex_name: str) -> None:
        """Create the guard for one named mutex.

        Parameters:
            mutex_name: Win32 mutex name. Use a ``Local\\`` prefix when
                the instance should be scoped to the current user session.

        Returns:
            None.

        Notes:
            Construction does not acquire the mutex. Call ``acquire`` so
            tests can instantiate the guard without touching Win32 state.
        """
        self._mutex_name = mutex_name
        self._mutex_handle: Optional[Any] = None
        self._already_running = False

    def acquire(self) -> bool:
        """Acquire the mutex if no other launcher instance owns it.

        Parameters:
            None.

        Returns:
            bool: True when this process may continue launching; False
            when another AgenticOS Command Center instance is already
            running in the current Windows logon session.

        Notes:
            On non-Windows platforms this degrades to True so tests and
            future cross-platform wrappers can import the module.
        """
        # On non-Windows test machines we degrade to a no-op so the
        # rest of the dashboard remains importable for unit tests.
        if sys.platform != "win32":
            self._already_running = False
            return True

        # Importing kernel32 lazily keeps the cross-platform tests
        # importable; the real type system check happens here.
        import ctypes
        from ctypes import wintypes

        ERROR_ALREADY_EXISTS = 183

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]

        # bInitialOwner=False so the mutex is created in the signaled
        # state; we only use the named-existence check, never the
        # signalled/unsignalled distinction.
        self._mutex_handle = kernel32.CreateMutexW(None, False, self._mutex_name)
        last_error = kernel32.GetLastError()

        if last_error == ERROR_ALREADY_EXISTS:
            self._already_running = True
            return False
        return True

    def release(self) -> None:
        """Close the mutex handle so a later launch can succeed.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            Safe to call more than once. The function is intentionally
            silent on non-Windows platforms.
        """
        if self._mutex_handle is None or sys.platform != "win32":
            return
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.CloseHandle(self._mutex_handle)
        self._mutex_handle = None


# ---------------------------------------------------------------------------
# Window preferences
# ---------------------------------------------------------------------------

def _load_window_prefs() -> dict[str, int]:
    """Return the saved window geometry, falling back to defaults.

    Parameters:
        None.

    Returns:
        dict[str, int]: Window rectangle with ``x``, ``y``, ``width``, and
        ``height`` keys.

    Notes:
        Defensive: any IO or schema error returns the defaults rather than
        raising, because a corrupt prefs file should never block launch.
    """
    defaults = {
        "x": dashboard_config.WINDOW_DEFAULT_X,
        "y": dashboard_config.WINDOW_DEFAULT_Y,
        "width": dashboard_config.WINDOW_DEFAULT_WIDTH,
        "height": dashboard_config.WINDOW_DEFAULT_HEIGHT,
    }
    path = dashboard_config.WINDOW_PREFS_PATH
    if not path.exists():
        return defaults
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {
            "x": int(raw["x"]),
            "y": int(raw["y"]),
            "width": int(raw["width"]),
            "height": int(raw["height"]),
        }
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        _logger.warning("Could not load window prefs at %s: %s", path, exc)
        return defaults


def _save_window_prefs(prefs: dict[str, int]) -> None:
    """Persist the window geometry to disk with atomic temp-then-rename.

    Parameters:
        prefs: Window rectangle containing integer ``x``, ``y``, ``width``,
            and ``height`` values.

    Returns:
        None.

    Notes:
        Crash safety matters here: if the user is force-quitting the
        dashboard the rename guarantees prefs are either fully written or
        untouched, never half-written.
    """
    path = dashboard_config.WINDOW_PREFS_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Suffix ".tmp.<pid>" so concurrent writers from two processes
        # cannot stomp each other's temp files.
        tmp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
        tmp_path.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
        # os.replace is atomic on Windows when both paths live on the
        # same filesystem (always the case here).
        os.replace(tmp_path, path)
    except OSError as exc:
        _logger.warning("Could not save window prefs to %s: %s", path, exc)


# ---------------------------------------------------------------------------
# Dashboard application
# ---------------------------------------------------------------------------

class DashboardApp:
    """Owns the WPF Application, tray icon, and supervised server."""

    def __init__(self) -> None:
        """Initialise the supervisor and lazy WPF state.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            No WPF objects are created here. They must be built on the STA
            thread in ``_wpf_main`` after pythonnet has loaded WPF.
        """
        # Create the supervisor. Command line uses python -m so the
        # AgenticOS package is resolved exactly the same way as inside
        # the test suite, regardless of the launcher's working dir.
        self._supervisor = ProcessSupervisor(
            command=[
                str(dashboard_config.resolve_python_executable()),
                "-m",
                "AgenticOS.agentic_server",
            ],
            log_path=dashboard_config.SERVER_LOG_PATH,
            health_url=dashboard_config.build_health_check_url(),
            startup_timeout_s=dashboard_config.SERVER_STARTUP_TIMEOUT_S,
            poll_interval_s=dashboard_config.SERVER_POLL_INTERVAL_S,
            max_restart_attempts=dashboard_config.MAX_RESTART_ATTEMPTS,
            restart_backoff_initial_s=dashboard_config.RESTART_BACKOFF_INITIAL_S,
            restart_backoff_cap_s=dashboard_config.RESTART_BACKOFF_CAP_S,
            graceful_shutdown_timeout_s=dashboard_config.GRACEFUL_SHUTDOWN_TIMEOUT_S,
            cwd=dashboard_config.AGENTIC_DIR.parent,
        )

        # Built lazily on the STA thread.
        self._wpf_app: Optional[Any] = None
        self._window: Optional[Any] = None
        self._webview_host: Optional[WebViewHost] = None
        self._tray: Optional[TrayIcon] = None

        # Cached saved geometry so it survives the WPF round-trip.
        self._prefs = _load_window_prefs()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> int:
        """Boot the server, launch the WPF UI, and return an exit code.

        Parameters:
            None.

        Returns:
            int: ``0`` for a normal shutdown, ``1`` when the FastAPI server
            cannot become healthy.

        Notes:
            The supervised server is always stopped in ``finally`` so a WPF
            crash does not leave port 7842 occupied by an orphan process.
        """
        # Register a state listener BEFORE the supervisor starts so we
        # never miss the initial "running" transition.
        self._supervisor.add_state_listener(self._on_supervisor_state)

        if not self._supervisor.start():
            _logger.error("Server failed to start; aborting dashboard launch")
            self._show_blocking_error(
                "AgenticOS server failed to start.\n\n"
                f"Inspect the log file for details:\n{dashboard_config.SERVER_LOG_PATH}"
            )
            return 1

        try:
            self._run_wpf_on_sta()
            return 0
        finally:
            # Always stop the supervisor on the way out; the WPF event
            # pump may have terminated for any reason (user quit,
            # exception, etc.) and orphaning the FastAPI server would
            # block a future relaunch on the same port.
            self._supervisor.stop()

    # ------------------------------------------------------------------
    # WPF main thread plumbing
    # ------------------------------------------------------------------

    def _run_wpf_on_sta(self) -> None:
        """Run the WPF Application on a dedicated STA thread.

        Parameters:
            None.

        Returns:
            None.

        Raises:
            BaseException: Re-raises any exception from the WPF worker
            thread so startup failures are visible to the parent process.

        Notes:
            WPF requires Single-Threaded Apartment threading. The code tries
            to mark the thread STA through pythonnet before the message pump
            starts; if pythonnet cannot expose that wrapper we log and let
            WPF report the real failure.
        """
        # Holder lets the worker propagate exceptions back here so a
        # failure on the STA thread is not silently swallowed.
        error_holder: list[Optional[BaseException]] = [None]

        def _worker() -> None:
            try:
                self._wpf_main()
            except BaseException as exc:  # noqa: BLE001
                error_holder[0] = exc

        from System.Threading import (  # type: ignore[import-not-found]
            ApartmentState,
            Thread,
            ThreadStart,
        )

        # WPF requires a real .NET STA thread. A Python threading.Thread
        # does not reliably expose SetApartmentState, so create the CLR
        # Thread directly and wrap the Python worker in a ThreadStart
        # delegate. This is the difference between "WPF assemblies load"
        # and "WPF can actually create controls."
        thread = Thread(ThreadStart(_worker))
        thread.Name = "AgenticOSWpfStaThread"
        thread.SetApartmentState(ApartmentState.STA)
        thread.Start()
        thread.Join()

        if error_holder[0] is not None:
            raise error_holder[0]

    def _wpf_main(self) -> None:
        """Build and run the WPF Application on the current STA thread.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            This method blocks until ``Application.Shutdown`` is invoked
            from the tray Quit action or another WPF shutdown path.
        """
        # Imports happen inside the function because pythonnet cannot
        # resolve System.Windows until clr.AddReference completes.
        from System.Windows import Application  # type: ignore[import-not-found]
        from System.Windows.Markup import XamlReader  # type: ignore[import-not-found]

        # Application instance owns the message pump and the lifetime
        # rules; ShutdownMode keeps the app alive when every window
        # closes so the tray icon can still drive Show Window.
        self._wpf_app = Application()
        self._wpf_app.ShutdownMode = self._wpf_app.ShutdownMode.OnExplicitShutdown
        self._wpf_app.Exit += lambda _s, _e: _logger.info("WPF Application.Exit fired")

        # Build window from XAML on disk so a designer can iterate on
        # the chrome without restarting the Python interpreter.
        xaml_text = dashboard_config.DASHBOARD_XAML_PATH.read_text(encoding="utf-8")
        self._window = XamlReader.Parse(xaml_text)
        self._apply_window_prefs()
        self._wire_window_events()
        self._mount_webview_or_fallback()
        self._build_tray_icon()

        # Show the window initially so first-run users see something.
        self._window.Show()

        # Run() blocks until Application.Shutdown is invoked.
        self._wpf_app.Run()

    # ------------------------------------------------------------------
    # Window setup helpers
    # ------------------------------------------------------------------

    def _apply_window_prefs(self) -> None:
        """Restore size and position from disk-backed preferences.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            Requires ``self._window`` to be populated by ``_wpf_main``.
        """
        assert self._window is not None
        self._window.Left = self._prefs["x"]
        self._window.Top = self._prefs["y"]
        self._window.Width = self._prefs["width"]
        self._window.Height = self._prefs["height"]
        self._window.MinWidth = dashboard_config.WINDOW_MIN_WIDTH
        self._window.MinHeight = dashboard_config.WINDOW_MIN_HEIGHT

    def _wire_window_events(self) -> None:
        """Attach click handlers to chrome buttons and the title bar.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            The close button hides to tray instead of shutting down the
            process, matching normal tray-app behavior.
        """
        assert self._window is not None
        from System.Windows import WindowState  # type: ignore[import-not-found]

        title_bar = self._window.FindName("TitleBar")
        if title_bar is not None:
            # MouseLeftButtonDown drives DragMove which is the documented
            # WPF idiom for moving a borderless window.
            title_bar.MouseLeftButtonDown += lambda _s, _e: self._window.DragMove()

        minimize_btn = self._window.FindName("MinimizeButton")
        if minimize_btn is not None:
            minimize_btn.Click += lambda _s, _e: self._set_window_state(
                WindowState.Minimized
            )

        maximize_btn = self._window.FindName("MaximizeButton")
        if maximize_btn is not None:
            # Toggle between Normal and Maximized so the same button
            # acts as Restore when the window is already maximised.
            maximize_btn.Click += lambda _s, _e: self._toggle_maximize(WindowState)

        close_btn = self._window.FindName("CloseButton")
        if close_btn is not None:
            # Close button on a tray app should hide, not exit.
            close_btn.Click += lambda _s, _e: self._hide_window()

        # Closing event lets us persist geometry even when the user
        # presses Alt+F4 or quits via the system menu.
        self._window.Closing += self._on_window_closing

    def _toggle_maximize(self, WindowState: Any) -> None:
        """Flip the window between maximised and normal states.

        Parameters:
            WindowState: The .NET ``System.Windows.WindowState`` enum.

        Returns:
            None.
        """
        assert self._window is not None
        if self._window.WindowState == WindowState.Maximized:
            self._window.WindowState = WindowState.Normal
        else:
            self._window.WindowState = WindowState.Maximized

    def _set_window_state(self, state: Any) -> None:
        """Assign a WPF window state.

        Parameters:
            state: A ``System.Windows.WindowState`` enum value.

        Returns:
            None.

        Notes:
            Centralising this mutation gives future logging or telemetry a
            single insertion point.
        """
        assert self._window is not None
        self._window.WindowState = state

    def _mount_webview_or_fallback(self) -> None:
        """Insert the WebView2 control or show a clear fallback message.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            The FastAPI backend may be healthy even when WebView2 is absent;
            in that case the launcher remains alive and tells the user how
            to install the runtime.
        """
        assert self._window is not None
        host_grid = self._window.FindName("WebView2Host")
        loading_label = self._window.FindName("LoadingLabel")

        self._webview_host = WebViewHost(
            dashboard_url=dashboard_config.build_dashboard_url(),
            fallback_html=render_fallback_html(),
        )

        try:
            control = self._webview_host.create_control()
            self._webview_host.navigate_to_dashboard()
            if loading_label is not None:
                # Hide the placeholder once the real control is mounted.
                from System.Windows import Visibility  # type: ignore[import-not-found]

                loading_label.Visibility = Visibility.Collapsed
            if host_grid is not None:
                host_grid.Children.Add(control)
        except WebView2NotInstalledError:
            _logger.warning("WebView2 runtime missing; rendering fallback message")
            self._show_runtime_missing_dialog()
            if loading_label is not None:
                loading_label.Text = (
                    "WebView2 Runtime not installed. Open the dashboard "
                    "log for the install link."
                )
        except Exception as exc:  # noqa: BLE001
            _logger.error("Could not mount WebView2: %s", exc)
            if loading_label is not None:
                loading_label.Text = f"Failed to load dashboard: {exc}"

    def _show_runtime_missing_dialog(self) -> None:
        """Show a WPF dialog explaining the missing WebView2 runtime.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            This is only called after WPF itself has loaded, so WPF imports
            inside the method are safe.
        """
        # Imports inside the method so the unit tests can import this
        # module without pythonnet.
        from System.Windows import (  # type: ignore[import-not-found]
            MessageBox,
            MessageBoxButton,
            MessageBoxImage,
        )

        MessageBox.Show(
            "Microsoft WebView2 Runtime was not detected.\n\n"
            "The dashboard will continue to run, but the React UI cannot "
            "render until the runtime is installed.\n\n"
            f"Download from:\n{dashboard_config.WEBVIEW2_DOWNLOAD_URL}",
            dashboard_config.APP_DISPLAY_NAME,
            MessageBoxButton.OK,
            MessageBoxImage.Warning,
        )

    # ------------------------------------------------------------------
    # Tray icon
    # ------------------------------------------------------------------

    def _build_tray_icon(self) -> None:
        """Construct and show the tray icon.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            The tray icon owns the show/hide/autostart/quit callbacks that
            keep the launcher usable after the main window is hidden.
        """
        callbacks = TrayCallbacks(
            on_show_window=self._show_window,
            on_hide_window=self._hide_window,
            on_view_logs=self._open_log_in_editor,
            on_toggle_autostart=self._set_autostart,
            on_quit=self._quit,
            autostart_initially_enabled=is_autostart_enabled(
                dashboard_config.REGISTRY_RUN_KEY,
                dashboard_config.REGISTRY_VALUE_NAME,
            ),
        )

        self._tray = TrayIcon(
            icon_path=dashboard_config.TRAY_ICON_PATH,
            tooltip=dashboard_config.APP_DISPLAY_NAME,
            callbacks=callbacks,
        )
        self._tray.show()

    # ------------------------------------------------------------------
    # Tray callback handlers
    # ------------------------------------------------------------------

    def _show_window(self) -> None:
        """Bring the WPF window to the foreground.

        Parameters:
            None.

        Returns:
            None.
        """
        if self._window is None:
            return
        from System.Windows import WindowState  # type: ignore[import-not-found]

        # Restore from minimised so the user does not see a flash of
        # an empty restore-from-tray that then needs another click.
        if self._window.WindowState == WindowState.Minimized:
            self._window.WindowState = WindowState.Normal
        self._window.Show()
        self._window.Activate()

    def _hide_window(self) -> None:
        """Hide the window without quitting the app.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            Geometry is saved first so the next show restores exactly where
            the user left it.
        """
        if self._window is None:
            return
        # Save geometry on every hide so the next show is exact.
        self._save_current_geometry()
        self._window.Hide()

    def _open_log_in_editor(self) -> None:
        """Open the FastAPI server log in the platform editor.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            Uses Notepad on Windows and ``xdg-open`` elsewhere. Errors are
            logged because this runs from a tray callback.
        """
        log_path = dashboard_config.SERVER_LOG_PATH
        if not log_path.exists():
            _logger.info("View Logs requested but %s does not exist yet", log_path)
            return
        try:
            if sys.platform == "win32":
                # subprocess.Popen("notepad", path) is the lightest way
                # to surface the log without bringing in a heavy editor.
                subprocess.Popen(["notepad.exe", str(log_path)])
            else:
                subprocess.Popen(["xdg-open", str(log_path)])
        except OSError as exc:
            _logger.error("Could not launch external viewer for %s: %s", log_path, exc)

    def _set_autostart(self, enabled: bool) -> None:
        """Toggle the HKCU Run-key value that drives login autostart.

        Parameters:
            enabled: True to enable launch on login, False to remove it.

        Returns:
            None.

        Notes:
            Registry failures roll back the tray checkmark so UI state stays
            honest.
        """
        if enabled:
            command = build_launch_command(
                dashboard_config.resolve_pythonw_executable(),
                dashboard_config.AGENTIC_DIR / "dashboard" / "agentic_dashboard.py",
            )
            success = write_run_value(
                dashboard_config.REGISTRY_RUN_KEY,
                dashboard_config.REGISTRY_VALUE_NAME,
                command,
            )
        else:
            success = delete_run_value(
                dashboard_config.REGISTRY_RUN_KEY,
                dashboard_config.REGISTRY_VALUE_NAME,
            )

        if not success and self._tray is not None:
            # Roll the visual back so the menu reflects reality.
            self._tray.set_autostart_checkmark(not enabled)

    def _quit(self) -> None:
        """Persist geometry, dispose tray, and shut WPF down.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            The actual server shutdown happens in ``run`` after the WPF
            message pump exits.
        """
        self._save_current_geometry()
        if self._tray is not None:
            self._tray.dispose()
        if self._wpf_app is not None:
            # Dispatcher.Invoke ensures Shutdown runs on the STA thread
            # even if a tray click fired Quit on the WinForms thread.
            try:
                self._wpf_app.Dispatcher.Invoke(self._wpf_app.Shutdown)
            except Exception as exc:  # noqa: BLE001
                _logger.warning("Shutdown dispatch failed: %s", exc)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _save_current_geometry(self) -> None:
        """Snapshot the current window position and size to disk.

        Parameters:
            None.

        Returns:
            None.

        Notes:
            Any WPF interop exception is logged and ignored so shutdown can
            continue.
        """
        if self._window is None:
            return
        try:
            prefs = {
                "x": int(self._window.Left),
                "y": int(self._window.Top),
                "width": int(self._window.Width),
                "height": int(self._window.Height),
            }
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Could not snapshot window geometry: %s", exc)
            return
        _save_window_prefs(prefs)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_window_closing(self, _sender: Any, args: Any) -> None:
        """Hide instead of exit so the tray app stays alive.

        Parameters:
            _sender: WPF sender object. Unused.
            args: WPF closing event args; ``Cancel`` is set to True.

        Returns:
            None.
        """
        # Cancel = True means the close event is suppressed entirely.
        args.Cancel = True
        self._hide_window()

    def _on_supervisor_state(self, state: str) -> None:
        """React to ProcessSupervisor state transitions.

        Parameters:
            state: Supervisor state string such as ``running``,
                ``unhealthy``, ``crashed``, ``failed``, or ``stopped``.

        Returns:
            None.

        Notes:
            Currently used to update the status dot in the title bar so
            the user has a live indicator of the server's health.
        """
        if self._window is None:
            return
        # Marshal the brush change to the UI thread; supervisor
        # listeners may run on the watcher thread.
        try:
            self._wpf_app.Dispatcher.BeginInvoke(  # type: ignore[union-attr]
                lambda: self._set_status_dot(state)
            )
        except Exception as exc:  # noqa: BLE001
            _logger.debug("Status dot update skipped: %s", exc)

    def _set_status_dot(self, state: str) -> None:
        """Mutate the ServerStatusDot fill brush based on supervisor state.

        Parameters:
            state: Supervisor state string.

        Returns:
            None.
        """
        from System.Windows.Media import (  # type: ignore[import-not-found]
            BrushConverter,
        )

        dot = self._window.FindName("ServerStatusDot") if self._window else None
        if dot is None:
            return
        # Map states to colours sourced from the palette.
        colour_map = {
            "running": "#C9A94E",
            "unhealthy": "#8B7435",
            "crashed": "#8B1A1A",
            "failed": "#8B1A1A",
            "stopped": "#8899AA",
        }
        hex_value = colour_map.get(state, "#8899AA")
        dot.Fill = BrushConverter().ConvertFromString(hex_value)
        dot.ToolTip = f"Server status: {state}"

    # ------------------------------------------------------------------
    # Error helpers
    # ------------------------------------------------------------------

    def _show_blocking_error(self, message: str) -> None:
        """Display a blocking error dialog without the rest of the UI.

        Parameters:
            message: Human-readable failure text to display.

        Returns:
            None.

        Notes:
            Used when launch fails before the WPF Application is built.
            Falls back to stderr on machines where pythonnet is missing.
        """
        try:
            _ensure_wpf_loaded()
            from System.Windows import (  # type: ignore[import-not-found]
                MessageBox,
                MessageBoxButton,
                MessageBoxImage,
            )

            MessageBox.Show(
                message,
                dashboard_config.APP_DISPLAY_NAME,
                MessageBoxButton.OK,
                MessageBoxImage.Error,
            )
        except Exception:
            # Last-resort path so the user sees something on stderr.
            print(message, file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Boot the dashboard and return a process exit code.

    Parameters:
        None.

    Returns:
        int: ``0`` for normal startup/shutdown, ``2`` when WPF/pythonnet
        cannot load, or the value returned by ``DashboardApp.run``.

    Notes:
        This function owns the single-instance guard so every exit path
        releases the mutex.
    """
    guard = SingleInstanceGuard(dashboard_config.SINGLE_INSTANCE_MUTEX_NAME)
    if not guard.acquire():
        _logger.info(
            "Another AgenticOS Command Center instance is already running; exiting"
        )
        # Returning 0 (not an error) because this is a normal user
        # outcome: they double-clicked the launcher twice.
        return 0

    try:
        _ensure_wpf_loaded()
    except Exception as exc:  # noqa: BLE001
        _logger.error("WPF assemblies could not be loaded: %s", exc)
        print(
            "ERROR: pythonnet / WPF could not be loaded. Install pythonnet:\n"
            "    pip install pythonnet\n"
            "Then rerun this script on Windows.",
            file=sys.stderr,
        )
        guard.release()
        return 2

    try:
        return DashboardApp().run()
    finally:
        guard.release()


if __name__ == "__main__":
    sys.exit(main())
