# tray_icon.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Encapsulate every System.Windows.Forms.NotifyIcon detail so
#          the dashboard module can wire the tray menu in declarative
#          form. Loads the gold submarine glyph from disk, builds the
#          right-click menu (Show / Hide / View Logs / Start with
#          Windows / Quit), and exposes typed callback hooks so the
#          dashboard never reaches into the Win32 forms namespace
#          directly.

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


_logger = logging.getLogger("AgenticOS.dashboard.tray_icon")


# ---------------------------------------------------------------------------
# Callback record
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrayCallbacks:
    """Bag of UI callbacks the tray menu invokes.

    Using a frozen dataclass instead of a constructor with eight
    keyword arguments keeps construction call sites short and lets
    static analysis catch missing handlers at the call site rather
    than at runtime when the menu fires.
    """

    on_show_window: Callable[[], None]
    on_hide_window: Callable[[], None]
    on_view_logs: Callable[[], None]
    on_toggle_autostart: Callable[[bool], None]
    on_quit: Callable[[], None]
    autostart_initially_enabled: bool


# ---------------------------------------------------------------------------
# Tray icon controller
# ---------------------------------------------------------------------------

class TrayIcon:
    """Wraps a NotifyIcon and its ContextMenuStrip in a single object.

    Lifecycle:
        tray = TrayIcon(icon_path, tooltip, callbacks)
        tray.show()
        ...
        tray.dispose()      # called by DashboardApp on quit
    """

    def __init__(
        self,
        icon_path: Path,
        tooltip: str,
        callbacks: TrayCallbacks,
    ) -> None:
        # Store the construction inputs; they are referenced again only
        # by show() so we keep them on the instance for clarity.
        self._icon_path = icon_path
        self._tooltip = tooltip
        self._callbacks = callbacks

        # The .NET objects are constructed lazily in show() because
        # importing them at module load time would crash on systems
        # without pythonnet (e.g. the Linux CI used by the test suite).
        self._notify_icon: Optional[Any] = None
        self._menu_strip: Optional[Any] = None
        self._autostart_item: Optional[Any] = None

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Create the .NET NotifyIcon and make it visible in the tray."""
        # Local imports keep the module importable on non-Windows
        # platforms; the test suite only exercises classes that do not
        # call show().
        from System.Drawing import Icon  # type: ignore[import-not-found]
        from System.Windows.Forms import (  # type: ignore[import-not-found]
            ContextMenuStrip,
            NotifyIcon,
            ToolStripMenuItem,
            ToolStripSeparator,
        )

        self._notify_icon = NotifyIcon()
        self._notify_icon.Text = self._tooltip

        # Load the glyph if the asset exists. Running without an icon
        # is supported because the asset pipeline ships an SVG and
        # leaves the .ico build to the designer; a missing icon must
        # not block the dashboard from launching.
        if self._icon_path.exists():
            try:
                self._notify_icon.Icon = Icon(str(self._icon_path))
            except Exception as exc:  # noqa: BLE001
                # Log but keep going; an empty tray slot is still
                # interactive on Windows 11.
                _logger.warning("Could not load tray icon %s: %s", self._icon_path, exc)
        else:
            _logger.info(
                "Tray icon asset missing at %s; running without glyph", self._icon_path
            )

        # Single-click toggles visibility, matching every other tray
        # app on Windows. Wired before the menu so the assignment is
        # complete by the time the icon goes visible.
        self._notify_icon.MouseClick += self._on_mouse_click

        self._menu_strip = ContextMenuStrip()
        self._build_menu_locked(ToolStripMenuItem, ToolStripSeparator)
        self._notify_icon.ContextMenuStrip = self._menu_strip

        self._notify_icon.Visible = True
        _logger.info("Tray icon shown with tooltip %r", self._tooltip)

    def dispose(self) -> None:
        """Hide and dispose the NotifyIcon so Windows reclaims the slot."""
        if self._notify_icon is None:
            return
        try:
            self._notify_icon.Visible = False
            self._notify_icon.Dispose()
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Could not dispose tray icon cleanly: %s", exc)
        finally:
            self._notify_icon = None
            self._menu_strip = None
            self._autostart_item = None

    def set_autostart_checkmark(self, checked: bool) -> None:
        """Reflect the live registry state in the tray menu checkmark.

        Called by the dashboard after a registry write fails so the
        UI does not lie to the user. Safe to call before show().
        """
        if self._autostart_item is None:
            return
        # Setting Checked fires CheckedChanged; suppress the loop by
        # comparing to the current value before assigning.
        if bool(self._autostart_item.Checked) != checked:
            self._autostart_item.Checked = checked

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_menu_locked(self, ToolStripMenuItem: Any, ToolStripSeparator: Any) -> None:
        """Populate the ContextMenuStrip in spec order.

        Spec order (per Plan 2 / spec section 9):
            Show Window
            Hide Window
            ---
            View Logs
            ---
            Start with Windows  (checkbox)
            ---
            Quit
        """
        # Items are referenced by name in the closures so the dashboard
        # can reach in for the autostart checkmark via the public API.
        item_show = ToolStripMenuItem("Show Window")
        item_show.Click += lambda _s, _e: self._safe(self._callbacks.on_show_window)

        item_hide = ToolStripMenuItem("Hide Window")
        item_hide.Click += lambda _s, _e: self._safe(self._callbacks.on_hide_window)

        item_logs = ToolStripMenuItem("View Logs")
        item_logs.Click += lambda _s, _e: self._safe(self._callbacks.on_view_logs)

        # The autostart item is a checkbox: clicking it both toggles
        # the visual state and fires the CheckedChanged event.
        self._autostart_item = ToolStripMenuItem("Start with Windows")
        self._autostart_item.CheckOnClick = True
        self._autostart_item.Checked = self._callbacks.autostart_initially_enabled
        self._autostart_item.CheckedChanged += self._on_autostart_changed

        item_quit = ToolStripMenuItem("Quit")
        item_quit.Click += lambda _s, _e: self._safe(self._callbacks.on_quit)

        # Add items in spec order with separators between groups.
        items = self._menu_strip.Items
        items.Add(item_show)
        items.Add(item_hide)
        items.Add(ToolStripSeparator())
        items.Add(item_logs)
        items.Add(ToolStripSeparator())
        items.Add(self._autostart_item)
        items.Add(ToolStripSeparator())
        items.Add(item_quit)

    def _on_mouse_click(self, _sender: Any, args: Any) -> None:
        """Translate a left-click on the icon into a show/hide toggle.

        Right-click is handled by NotifyIcon natively (it pops the
        ContextMenuStrip), so we only special-case the left button.
        """
        # MouseButtons.Left = 1048576 in WinForms; comparing by the
        # enum is more readable than the magic number.
        try:
            from System.Windows.Forms import MouseButtons  # type: ignore[import-not-found]

            if args.Button != MouseButtons.Left:
                return
        except Exception:  # noqa: BLE001
            # If MouseButtons cannot be loaded for some reason, fall
            # through to the toggle: a stray right-click is preferable
            # to a tray icon that does nothing.
            pass

        # Toggle is implemented by the dashboard itself via the show /
        # hide callbacks; the tray does not track window state.
        self._safe(self._callbacks.on_show_window)

    def _on_autostart_changed(self, sender: Any, _args: Any) -> None:
        """Forward the checkbox change to the dashboard callback.

        Catching exceptions here is essential: a registry write that
        raises should never crash the WinForms message pump.
        """
        checked = bool(sender.Checked)
        try:
            self._callbacks.on_toggle_autostart(checked)
        except Exception as exc:  # noqa: BLE001
            _logger.error("on_toggle_autostart raised: %s", exc)
            # Roll the checkbox back so the UI matches reality.
            sender.Checked = not checked

    @staticmethod
    def _safe(callback: Callable[[], None]) -> None:
        """Run ``callback`` and swallow any exception with a log entry.

        Tray-menu clicks deserve the same defensive treatment as
        background threads: an unhandled exception there crashes the
        WinForms loop and the app silently disappears from the tray.
        """
        try:
            callback()
        except Exception as exc:  # noqa: BLE001
            _logger.error("Tray callback raised: %s", exc)
