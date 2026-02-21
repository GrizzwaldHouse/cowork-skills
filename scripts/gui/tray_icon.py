# tray_icon.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: System tray integration with notification badges and context menu for background operation

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
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from gui.constants import TRAY_BADGE_PADDING, TRAY_BADGE_RADIUS
from gui.paths import ASSETS_DIR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("tray_icon")


def _load_pixmap_from_svg(svg_name: str, size: int = 32) -> QPixmap:
    """Render an SVG asset to a QPixmap at the given pixel size."""
    svg_path = ASSETS_DIR / svg_name
    if not svg_path.exists():
        logger.warning("SVG not found: %s", svg_path)
        return QPixmap(QSize(size, size))

    renderer = QSvgRenderer(str(svg_path))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap


def _overlay_badge(pixmap: QPixmap, count: int) -> QPixmap:
    """Draw a red badge with a white number in the top-right corner."""
    result = QPixmap(pixmap)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    size = pixmap.width()
    badge_r = max(6, size // 4)
    cx = size - badge_r - TRAY_BADGE_PADDING
    cy = badge_r + TRAY_BADGE_PADDING

    # Visual urgency indicator for unacknowledged alerts
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#E74C3C"))
    painter.drawEllipse(cx - badge_r, cy - badge_r, badge_r * 2, badge_r * 2)

    # White number
    font = QFont("Segoe UI", max(6, badge_r - 1))
    font.setWeight(QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QPen(QColor("white")))
    text = str(count) if count < 100 else "99+"
    from PyQt6.QtCore import QRectF
    painter.drawText(
        QRectF(cx - badge_r, cy - badge_r, badge_r * 2, badge_r * 2),
        int(Qt.AlignmentFlag.AlignCenter),
        text,
    )

    painter.end()
    return result


def _tint_red(pixmap: QPixmap) -> QPixmap:
    """Return a red-tinted copy of a pixmap for urgency pulse."""
    result = QPixmap(pixmap)
    painter = QPainter(result)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
    painter.fillRect(result.rect(), QColor(255, 50, 50, 120))
    painter.end()
    return result


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

    _URGENCY_DELAY_MS = 5 * 60 * 1000  # 5 minutes before urgency pulse
    _PULSE_INTERVAL_MS = 500            # alternate icon every 500ms

    def __init__(
        self,
        window: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._window = window
        self._event_count = 0
        self._unacked_alerts = 0
        self._last_event_path = ""
        self._last_event_time = ""
        self._current_state = "idle"

        # Pre-load pixmaps for each state (pixmaps allow badge overlay)
        self._pixmaps: dict[str, QPixmap] = {
            "idle": _load_pixmap_from_svg("owl_tray.svg", 32),
            "alert": _load_pixmap_from_svg("owl_alert.svg", 32),
            "alarm": _load_pixmap_from_svg("owl_alarm.svg", 32),
        }
        # Pre-build red-tinted versions for urgency pulse
        self._red_pixmaps: dict[str, QPixmap] = {
            k: _tint_red(v) for k, v in self._pixmaps.items()
        }

        self.setIcon(QIcon(self._pixmaps["idle"]))

        # Context menu (must be built before _update_tooltip)
        self._build_menu()
        self._update_tooltip()

        # Double-click to toggle window
        self.activated.connect(self._on_activated)

        # Urgency pulse timer (alternates icon when critical alerts unacked)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(self._PULSE_INTERVAL_MS)
        self._pulse_timer.timeout.connect(self._on_pulse_tick)
        self._pulse_is_red = False

        # Urgency delay timer (starts pulsing after 5 min of unacked criticals)
        self._urgency_timer = QTimer(self)
        self._urgency_timer.setSingleShot(True)
        self._urgency_timer.setInterval(self._URGENCY_DELAY_MS)
        self._urgency_timer.timeout.connect(self._start_urgency_pulse)

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
            One of the owl state names (uses idle/alert/alarm for icon).
        """
        # Map 8 states down to 3 icon variants
        if state in ("alarm",):
            icon_key = "alarm"
        elif state in ("alert", "scanning", "curious"):
            icon_key = "alert"
        else:
            icon_key = "idle"

        self._current_state = icon_key
        self._refresh_icon()

    def set_watching(self, is_watching: bool) -> None:
        """Update menu enabled states for watcher running status."""
        self._start_action.setEnabled(not is_watching)
        self._stop_action.setEnabled(is_watching)
        self._update_tooltip()

    def increment_event_count(self, path: str = "") -> None:
        """Bump the event counter and refresh the tooltip."""
        self._event_count += 1
        if path:
            self._last_event_path = Path(path).name
            self._last_event_time = datetime.now().strftime("%H:%M:%S")
        self._update_tooltip()

    def add_unacked_alert(self, level: str) -> None:
        """Register an unacknowledged alert for badge and urgency tracking."""
        self._unacked_alerts += 1
        self._refresh_icon()
        if level == "CRITICAL" and not self._urgency_timer.isActive() and not self._pulse_timer.isActive():
            self._urgency_timer.start()

    def acknowledge_alerts(self) -> None:
        """Clear unacknowledged alerts (called when window is shown)."""
        self._unacked_alerts = 0
        self._urgency_timer.stop()
        self._pulse_timer.stop()
        self._pulse_is_red = False
        self._refresh_icon()

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

    def _refresh_icon(self) -> None:
        """Rebuild the tray icon with optional badge overlay."""
        pixmap = self._pixmaps.get(self._current_state, self._pixmaps["idle"])
        if self._unacked_alerts > 0:
            pixmap = _overlay_badge(pixmap, self._unacked_alerts)
        self.setIcon(QIcon(pixmap))

    def _update_tooltip(self) -> None:
        watching = self._stop_action.isEnabled()
        status = "Watching" if watching else "Stopped"
        parts = [f"OwlWatcher - {status}", f"{self._event_count} events"]
        if self._unacked_alerts > 0:
            parts.append(f"{self._unacked_alerts} unacked alerts")
        if self._last_event_path:
            parts.append(f"Last: {self._last_event_path} @ {self._last_event_time}")
        self.setToolTip("\n".join(parts))

    def _start_urgency_pulse(self) -> None:
        """Begin alternating tray icon for unacknowledged critical alerts."""
        if self._unacked_alerts > 0:
            self._pulse_timer.start()

    def _on_pulse_tick(self) -> None:
        """Alternate between normal and red-tinted icon."""
        self._pulse_is_red = not self._pulse_is_red
        if self._pulse_is_red:
            pixmap = self._red_pixmaps.get(self._current_state, self._red_pixmaps["idle"])
        else:
            pixmap = self._pixmaps.get(self._current_state, self._pixmaps["idle"])
        if self._unacked_alerts > 0:
            pixmap = _overlay_badge(pixmap, self._unacked_alerts)
        self.setIcon(QIcon(pixmap))

    def _toggle_window(self) -> None:
        """Show or hide the main window."""
        if self._window.isVisible():
            self._window.hide()
            self._show_action.setText("Show Window")
        else:
            self._window.showNormal()
            self._window.activateWindow()
            self._show_action.setText("Hide Window")
            # Acknowledge alerts when user opens the window
            self.acknowledge_alerts()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation (double-click)."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()
