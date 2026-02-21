# sparkline_widget.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Real-time event frequency visualization using ring buffer to avoid unbounded memory growth

"""
Sparkline mini-chart widget showing event frequency over the last 60 minutes.

Renders a 100x32px gold line on a dark background, updated as new file
events are recorded.

Usage::

    spark = SparklineWidget()
    spark.record_event()  # call on each file event
"""

from __future__ import annotations

import time

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from gui.constants import DARK_PANEL, GOLD

_BUCKET_COUNT = 60  # one bucket per minute
_BUCKET_SECONDS = 60
_CHART_W = 100
_CHART_H = 32


class SparklineWidget(QWidget):
    """Mini sparkline chart of event frequency (last 60 minutes)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(_CHART_W, _CHART_H))
        self.setToolTip("Events per minute (last 60 min)")

        # Ring buffer: counts per 1-minute bucket
        self._buckets = [0] * _BUCKET_COUNT
        self._current_bucket = 0
        self._last_bucket_time = time.monotonic()

        # Tick every 60 seconds to rotate buckets
        self._timer = QTimer(self)
        self._timer.setInterval(_BUCKET_SECONDS * 1000)
        self._timer.timeout.connect(self._rotate_bucket)
        self._timer.start()

    def record_event(self) -> None:
        """Record one file event in the current bucket."""
        self._buckets[self._current_bucket] += 1
        self.update()

    def _rotate_bucket(self) -> None:
        """Advance to the next bucket, clearing its old value."""
        self._current_bucket = (self._current_bucket + 1) % _BUCKET_COUNT
        self._buckets[self._current_bucket] = 0
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(DARK_PANEL))

        # Gather data points in chronological order
        points: list[int] = []
        for i in range(_BUCKET_COUNT):
            idx = (self._current_bucket + 1 + i) % _BUCKET_COUNT
            points.append(self._buckets[idx])

        max_val = max(max(points), 1)
        w = self.width() - 4
        h = self.height() - 6

        # Build path
        path = QPainterPath()
        step_x = w / max(_BUCKET_COUNT - 1, 1)

        for i, val in enumerate(points):
            x = 2 + i * step_x
            y = 3 + h - (val / max_val) * h
            if i == 0:
                path.moveTo(QPointF(x, y))
            else:
                path.lineTo(QPointF(x, y))

        # Draw line
        pen = QPen(QColor(GOLD), 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)

        painter.end()
