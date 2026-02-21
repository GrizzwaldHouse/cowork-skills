# donut_widget.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: File type distribution visualization showing which extensions are most active

"""
Micro donut chart widget showing file-type breakdown.

A 40x40px donut chart that tracks file extension proportions from
observed events.

Usage::

    donut = DonutWidget()
    donut.record_file_type(".py")
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from gui.constants import DARK_PANEL, GOLD, PARCHMENT, TEAL

_SIZE = 40
_ARC_WIDTH = 6

# Palette for top file types
_COLORS = [
    QColor(GOLD),            # most common
    QColor("#4CAF50"),        # green
    QColor("#42A5F5"),        # blue
    QColor("#FF7043"),        # orange
    QColor(TEAL),             # teal
    QColor(PARCHMENT),        # parchment
]


class DonutWidget(QWidget):
    """Micro donut chart of file type distribution."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(_SIZE, _SIZE))
        self.setToolTip("File type breakdown")

        self._counts: dict[str, int] = {}
        self._total = 0

    def record_file_type(self, ext: str) -> None:
        """Record one occurrence of a file extension (e.g. '.py')."""
        ext = ext.lower() if ext else "(none)"
        self._counts[ext] = self._counts.get(ext, 0) + 1
        self._total += 1
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(DARK_PANEL))

        if self._total == 0:
            # Empty state: draw a dim ring
            pen = QPen(QColor(TEAL), _ARC_WIDTH)
            painter.setPen(pen)
            rect = QRectF(
                _ARC_WIDTH / 2, _ARC_WIDTH / 2,
                _SIZE - _ARC_WIDTH, _SIZE - _ARC_WIDTH,
            )
            painter.drawEllipse(rect)
            painter.end()
            return

        # Sort by count descending, take top 6
        sorted_exts = sorted(
            self._counts.items(), key=lambda x: x[1], reverse=True,
        )[:len(_COLORS)]

        rect = QRectF(
            _ARC_WIDTH / 2, _ARC_WIDTH / 2,
            _SIZE - _ARC_WIDTH, _SIZE - _ARC_WIDTH,
        )

        start_angle = 90 * 16  # Start from top (Qt uses 1/16th degree units)
        for i, (ext, count) in enumerate(sorted_exts):
            span = int((count / self._total) * 360 * 16)
            pen = QPen(_COLORS[i % len(_COLORS)], _ARC_WIDTH)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, start_angle, -span)
            start_angle -= span

        painter.end()
