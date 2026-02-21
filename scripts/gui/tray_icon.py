"""
System tray icon for the OwlWatcher application.

Provides a :class:`QSystemTrayIcon` with a context menu, balloon
notifications for security alerts, and state-dependent icon switching.

Usage::

    tray = OwlTrayIcon(window)
    tray.show()
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from gui.paths import ASSETS_DIR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("tray_icon")


def _load_icon_from_svg(svg_name: str, size: int = 32) -> QIcon:
    """Render an SVG asset to a QIcon at the given pixel size."""
    svg_path = ASSETS_DIR / svg_name
    if not svg_path.exists():
        logger.warning("SVG not found: %s", svg_path)
        return QIcon()

    renderer = QSvgRenderer(str(svg_path))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)

    from PyQt6.QtGui import QPainter
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


# ---------------------------------------------------------------------------
# Tray icon
# ---------------------------------------------------------------------------
class OwlTrayIcon(QSystemTrayIcon):
    """System tray icon with context menu and balloon notifications.

    Parameters
    ----------
    window:
        The main application window to show/hide.
    parent:
        Optional parent widget.
    """

    def __init__(
        self,
        window: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._window = window
        self._event_count = 0

        # Pre-load icons for each state
        self._icons: dict[str, QIcon] = {
            "idle": _load_icon_from_svg("owl_tray.svg", 32),
            "alert": _load_icon_from_svg("owl_alert.svg", 32),
            "alarm": _load_icon_from_svg("owl_alarm.svg", 32),
        }

        self.setIcon(self._icons["idle"])

        # Context menu (must be built before _update_tooltip)
        self._build_menu()
        self._update_tooltip()

        # Double-click to toggle window
        self.activated.connect(self._on_activated)

    # -- menu -------------------------------------------------------------

    def _build_menu(self) -> None:
        """Build the tray icon context menu."""
        menu = QMenu()

        self._show_action = QAction("Show Window", self)
        self._show_action.triggered.connect(self._toggle_window)
        menu.addAction(self._show_action)

        menu.addSeparator()

        self._start_action = QAction("Start Watcher", self)
        menu.addAction(self._start_action)

        self._stop_action = QAction("Stop Watcher", self)
        self._stop_action.setEnabled(False)
        menu.addAction(self._stop_action)

        menu.addSeparator()

        self._export_action = QAction("Export Audit Report", self)
        menu.addAction(self._export_action)

        menu.addSeparator()

        self._quit_action = QAction("Quit", self)
        menu.addAction(self._quit_action)

        self.setContextMenu(menu)

    # -- public API -------------------------------------------------------

    @property
    def start_action(self) -> QAction:
        """The 'Start Watcher' action for external signal wiring."""
        return self._start_action

    @property
    def stop_action(self) -> QAction:
        """The 'Stop Watcher' action for external signal wiring."""
        return self._stop_action

    @property
    def export_action(self) -> QAction:
        """The 'Export Audit Report' action for external signal wiring."""
        return self._export_action

    @property
    def quit_action(self) -> QAction:
        """The 'Quit' action for external signal wiring."""
        return self._quit_action

    def set_state(self, state: str) -> None:
        """Change the tray icon to reflect the watcher state.

        Parameters
        ----------
        state:
            One of ``"idle"``, ``"alert"``, or ``"alarm"``.
        """
        icon = self._icons.get(state, self._icons["idle"])
        self.setIcon(icon)

    def set_watching(self, is_watching: bool) -> None:
        """Update menu enabled states for watcher running status."""
        self._start_action.setEnabled(not is_watching)
        self._stop_action.setEnabled(is_watching)
        self._update_tooltip()

    def increment_event_count(self) -> None:
        """Bump the event counter and refresh the tooltip."""
        self._event_count += 1
        self._update_tooltip()

    def notify(self, title: str, message: str, icon_type: str = "info") -> None:
        """Show a balloon notification from the tray icon.

        Parameters
        ----------
        title:
            Notification title.
        message:
            Notification body text.
        icon_type:
            One of ``"info"``, ``"warning"``, or ``"critical"``.
        """
        type_map = {
            "info": QSystemTrayIcon.MessageIcon.Information,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "critical": QSystemTrayIcon.MessageIcon.Critical,
        }
        msg_icon = type_map.get(icon_type, QSystemTrayIcon.MessageIcon.Information)
        self.showMessage(title, message, msg_icon, 5000)

    # -- private ----------------------------------------------------------

    def _update_tooltip(self) -> None:
        watching = self._stop_action.isEnabled()
        status = "Watching" if watching else "Stopped"
        self.setToolTip(f"OwlWatcher - {status} | {self._event_count} events")

    def _toggle_window(self) -> None:
        """Show or hide the main window."""
        if self._window.isVisible():
            self._window.hide()
            self._show_action.setText("Show Window")
        else:
            self._window.showNormal()
            self._window.activateWindow()
            self._show_action.setText("Hide Window")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation (double-click)."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()
