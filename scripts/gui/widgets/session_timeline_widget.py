# session_timeline_widget.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Timeline widget showing session activity across watched projects

"""
Session timeline widget for the intelligence panel.

Displays horizontal bars per watched project, colored by session status,
with event-count badges and elapsed-time labels.

Usage::

    timeline = SessionTimelineWidget()
    timeline.update_sessions([
        {
            "project": "OwlWatcher",
            "status": "active",
            "event_count": 42,
            "idle_seconds": 0,
            "start_time": "2026-03-23T10:00:00",
        },
    ])
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from gui.constants import (
    DARK_PANEL,
    FONT_FAMILY,
    GOLD,
    INTEL_LEARNING_COLOR,
    MID_PANEL,
    PARCHMENT,
    TEAL,
)

_ROW_HEIGHT = 28
_BAR_HEIGHT = 14
_BAR_RADIUS = 4
_NAME_WIDTH = 100
_TIME_WIDTH = 50
_BADGE_MIN_WIDTH = 24

_ACTIVE_COLOR = INTEL_LEARNING_COLOR
_IDLE_COLOR = MID_PANEL

_LABEL_STYLE = (
    f"color: {PARCHMENT}; font-size: 10px; font-family: '{FONT_FAMILY}';"
)
_HEADER_STYLE = (
    f"color: {GOLD}; font-size: 12px; font-weight: bold; "
    f"font-family: '{FONT_FAMILY}';"
)


def _format_elapsed(seconds: int) -> str:
    """Format elapsed seconds as a human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}min"
    hours = minutes // 60
    remaining = minutes % 60
    if remaining:
        return f"{hours}h{remaining}m"
    return f"{hours}h"


class _TimelineBar(QWidget):
    """Horizontal bar representing session progress."""

    def __init__(
        self, fill_ratio: float, active: bool, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._fill = max(0.0, min(1.0, fill_ratio))
        self._active = active
        self.setFixedHeight(_BAR_HEIGHT)

    def set_state(self, fill_ratio: float, active: bool) -> None:
        """Update bar fill and color."""
        self._fill = max(0.0, min(1.0, fill_ratio))
        self._active = active
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(_IDLE_COLOR))
        painter.drawRoundedRect(0, 0, w, h, _BAR_RADIUS, _BAR_RADIUS)

        # Filled portion
        fill_w = max(int(w * self._fill), 0)
        if fill_w > 0:
            color = _ACTIVE_COLOR if self._active else _IDLE_COLOR
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(0, 0, fill_w, h, _BAR_RADIUS, _BAR_RADIUS)

        painter.end()


class _SessionRow(QWidget):
    """A single row in the session timeline."""

    clicked = pyqtSignal(str)

    def __init__(self, session: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project = session.get("project", "Unknown")
        self.setFixedHeight(_ROW_HEIGHT)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._build_ui(session)

    def _build_ui(self, session: dict) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        # Project name
        self._name_label = QLabel(self._project)
        self._name_label.setFixedWidth(_NAME_WIDTH)
        self._name_label.setStyleSheet(_LABEL_STYLE)
        self._name_label.setToolTip(self._project)
        layout.addWidget(self._name_label)

        # Timeline bar
        is_active = session.get("status", "idle").lower() == "active"
        idle_secs = session.get("idle_seconds", 0)
        # Fill represents activity: 1.0 when active (0 idle), decreasing
        # toward 0.1 after 30 minutes of idle.
        if is_active:
            fill = 1.0
        else:
            fill = max(0.1, 1.0 - (idle_secs / 1800.0))

        self._bar = _TimelineBar(fill, is_active)
        layout.addWidget(self._bar, stretch=1)

        # Event count badge
        count = session.get("event_count", 0)
        self._count_badge = QLabel(str(count))
        self._count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_badge.setMinimumWidth(_BADGE_MIN_WIDTH)
        self._count_badge.setStyleSheet(
            f"color: {GOLD}; background: {TEAL}; font-size: 9px; "
            f"font-weight: bold; font-family: '{FONT_FAMILY}'; "
            f"border-radius: 3px; padding: 1px 4px;"
        )
        layout.addWidget(self._count_badge)

        # Elapsed time
        elapsed = session.get("idle_seconds", 0)
        self._time_label = QLabel(_format_elapsed(elapsed))
        self._time_label.setFixedWidth(_TIME_WIDTH)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._time_label.setStyleSheet(
            f"color: #8899AA; font-size: 9px; font-family: '{FONT_FAMILY}';"
        )
        layout.addWidget(self._time_label)

    def update_session(self, session: dict) -> None:
        """Refresh the row with new session data."""
        is_active = session.get("status", "idle").lower() == "active"
        idle_secs = session.get("idle_seconds", 0)

        if is_active:
            fill = 1.0
        else:
            fill = max(0.1, 1.0 - (idle_secs / 1800.0))

        self._bar.set_state(fill, is_active)
        self._count_badge.setText(str(session.get("event_count", 0)))
        self._time_label.setText(_format_elapsed(idle_secs))

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._project)
        super().mousePressEvent(event)


class SessionTimelineWidget(QWidget):
    """Timeline widget showing session activity across watched projects."""

    session_clicked = pyqtSignal(str)  # Emits project name

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sessions: list[dict] = []
        self._rows: dict[str, _SessionRow] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the timeline layout."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)

        self._header = QLabel("Session Activity")
        self._header.setStyleSheet(_HEADER_STYLE)
        self._layout.addWidget(self._header)

        self._rows_widget = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(2)
        self._layout.addWidget(self._rows_widget)

        self._layout.addStretch()

    def update_sessions(self, sessions: list[dict]) -> None:
        """Update timeline with current session data.

        Each dict has: project, status, event_count, idle_seconds, start_time
        """
        self._sessions = sessions
        incoming_projects = {s.get("project", "") for s in sessions}

        # Remove rows for projects no longer in session list
        for name in list(self._rows.keys()):
            if name not in incoming_projects:
                row = self._rows.pop(name)
                self._rows_layout.removeWidget(row)
                row.deleteLater()

        # Update existing or create new rows
        for session in sessions:
            project = session.get("project", "Unknown")
            if project in self._rows:
                self._rows[project].update_session(session)
            else:
                row = self._build_row(session)
                self._rows[project] = row
                self._rows_layout.addWidget(row)

    def _build_row(self, session: dict) -> _SessionRow:
        """Build a single project timeline row."""
        row = _SessionRow(session)
        row.clicked.connect(self.session_clicked.emit)
        return row

    def clear(self) -> None:
        """Remove all session rows."""
        for row in self._rows.values():
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self._sessions.clear()

    @property
    def active_count(self) -> int:
        """Return the number of currently active sessions."""
        return sum(
            1 for s in self._sessions
            if s.get("status", "").lower() == "active"
        )

    @property
    def total_events(self) -> int:
        """Return total event count across all sessions."""
        return sum(s.get("event_count", 0) for s in self._sessions)
