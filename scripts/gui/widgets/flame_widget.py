# flame_widget.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Indicate watcher uptime duration through growing visual intensity to reinforce system health awareness

"""
Uptime flame widget that grows brighter over 24 hours.

A 24x32px flame shape whose opacity ramps from 0.2 (just started)
to 1.0 (24h uptime).

Usage::

    flame = FlameWidget()
    flame.set_uptime_hours(12.5)
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from gui.constants import DARK_PANEL, FONT_FAMILY, GOLD

_W = 24
_H = 32
_MAX_HOURS = 24.0


class FlameWidget(QWidget):
    """Uptime flame indicator that brightens over 24 hours."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(_W, _H))
        self.setToolTip("Uptime intensity")

        self._hours: float = 0.0
        self._font = QFont(FONT_FAMILY, 7)

    def set_uptime_hours(self, hours: float) -> None:
        """Set the current uptime in hours."""
        self._hours = max(0.0, hours)
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(DARK_PANEL))

        # Opacity ramps from 0.2 to 1.0 over 24h
        t = min(self._hours / _MAX_HOURS, 1.0)
        opacity = 0.2 + 0.8 * t

        painter.setOpacity(opacity)

        # Draw flame shape
        cx = _W / 2.0
        path = QPainterPath()
        path.moveTo(QPointF(cx, 2))  # tip
        path.cubicTo(
            QPointF(cx + 8, 10),
            QPointF(cx + 10, 20),
            QPointF(cx, _H - 4),
        )
        path.cubicTo(
            QPointF(cx - 10, 20),
            QPointF(cx - 8, 10),
            QPointF(cx, 2),
        )

        # Gold -> orange gradient effect via two fills
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#E8820C"))
        painter.drawPath(path)

        # Inner flame (smaller, brighter gold)
        inner = QPainterPath()
        inner.moveTo(QPointF(cx, 8))
        inner.cubicTo(
            QPointF(cx + 4, 14),
            QPointF(cx + 5, 20),
            QPointF(cx, _H - 8),
        )
        inner.cubicTo(
            QPointF(cx - 5, 20),
            QPointF(cx - 4, 14),
            QPointF(cx, 8),
        )
        painter.setBrush(QColor(GOLD))
        painter.drawPath(inner)

        painter.end()
