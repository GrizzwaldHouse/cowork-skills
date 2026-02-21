# gauge_widget.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Threat level indicator using color gradient arc to communicate security urgency at a glance

"""
Circular gauge widget showing a threat score from 0 to 100.

A 48x48px arc that transitions from green (0) to gold (50) to red (100).

Usage::

    gauge = GaugeWidget()
    gauge.set_score(42)
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from gui.constants import DARK_PANEL, FONT_FAMILY

_SIZE = 48
_ARC_WIDTH = 5
_SWEEP_ANGLE = 240  # degrees of arc (not a full circle)


def _score_color(score: int) -> QColor:
    """Interpolate green -> gold -> red based on score 0-100."""
    if score <= 50:
        t = score / 50.0
        r = int(76 + t * (201 - 76))
        g = int(175 + t * (169 - 175))
        b = int(80 + t * (78 - 80))
    else:
        t = (score - 50) / 50.0
        r = int(201 + t * (255 - 201))
        g = int(169 - t * (169 - 107))
        b = int(78 - t * (78 - 107))
    return QColor(r, g, b)


class GaugeWidget(QWidget):
    """Circular arc gauge for threat score 0-100."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(_SIZE, _SIZE))
        self.setToolTip("Threat score")

        self._score: int = 0
        self._font = QFont(FONT_FAMILY, 9)
        self._font.setWeight(QFont.Weight.Bold)

    def set_score(self, score: int) -> None:
        """Set the threat score (clamped to 0-100)."""
        self._score = max(0, min(100, score))
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(DARK_PANEL))

        margin = _ARC_WIDTH / 2 + 2
        rect = QRectF(margin, margin, _SIZE - 2 * margin, _SIZE - 2 * margin)

        # Background arc (dim)
        start = (90 + _SWEEP_ANGLE / 2) * 16  # Qt uses 1/16 degree
        span = -_SWEEP_ANGLE * 16

        bg_pen = QPen(QColor(40, 40, 40), _ARC_WIDTH)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, int(start), int(span))

        # Filled arc based on score
        fill_span = int(-(_SWEEP_ANGLE * (self._score / 100.0)) * 16)
        fill_pen = QPen(_score_color(self._score), _ARC_WIDTH)
        fill_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(fill_pen)
        painter.drawArc(rect, int(start), fill_span)

        # Score text in center
        painter.setFont(self._font)
        painter.setPen(QPen(_score_color(self._score)))
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), str(self._score))

        painter.end()
