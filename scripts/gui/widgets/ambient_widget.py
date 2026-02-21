# ambient_widget.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Animated night-sky background with drifting stars and moon phase to create immersive nocturnal theme

"""
Ambient night-sky background widget for the OwlWatcher header.

Renders a vertical gradient from deep navy to dark navy, scattered
gold star dots that drift slowly, and a real-phase moon glyph in the
top-right corner.

Usage::

    from gui.widgets.ambient_widget import AmbientBackgroundWidget

    bg = AmbientBackgroundWidget()
    # Place other widgets on top via layout
"""

from __future__ import annotations

import math
import random
from datetime import date

from PyQt6.QtCore import QPointF, QRectF, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import QWidget

from gui.constants import AMBIENT_FRAME_MS, GOLD, NAVY

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_NUM_STARS = 40
_STAR_DRIFT_PX_PER_SEC = 0.5  # pixels per second of horizontal drift
_STAR_MIN_SIZE = 1.0
_STAR_MAX_SIZE = 2.5
_GRADIENT_TOP = "#060D15"
_GRADIENT_BOTTOM = NAVY
_MOON_SIZE = 16
_STAR_COLOR = QColor(GOLD)


# ---------------------------------------------------------------------------
# Moon phase calculation
# ---------------------------------------------------------------------------
def _moon_phase(d: date | None = None) -> float:
    """Return the moon phase as a float 0.0 -- 1.0 (0 = new, 0.5 = full).

    Uses a simple synodic period approximation.
    """
    if d is None:
        d = date.today()
    # Known new moon: 2000-01-06
    known_new = date(2000, 1, 6)
    synodic = 29.53058770576
    days = (d - known_new).days
    return (days % synodic) / synodic


def _moon_char(phase: float) -> str:
    """Return a Unicode moon glyph for the given phase (0.0 -- 1.0)."""
    # 8 phases mapped to Unicode symbols
    glyphs = [
        "\U0001F311",  # new moon
        "\U0001F312",  # waxing crescent
        "\U0001F313",  # first quarter
        "\U0001F314",  # waxing gibbous
        "\U0001F315",  # full moon
        "\U0001F316",  # waning gibbous
        "\U0001F317",  # last quarter
        "\U0001F318",  # waning crescent
    ]
    idx = int(phase * 8) % 8
    return glyphs[idx]


# ---------------------------------------------------------------------------
# Star data
# ---------------------------------------------------------------------------
class _Star:
    """A single drifting star dot."""

    __slots__ = ("x", "y", "size", "opacity", "drift_speed")

    def __init__(self, width: float, height: float) -> None:
        self.x = random.uniform(0, width) if width > 0 else random.uniform(0, 400)
        self.y = random.uniform(0, height) if height > 0 else random.uniform(0, 100)
        self.size = random.uniform(_STAR_MIN_SIZE, _STAR_MAX_SIZE)
        self.opacity = random.uniform(0.3, 1.0)
        # Each star drifts at a slightly different speed
        self.drift_speed = _STAR_DRIFT_PX_PER_SEC * random.uniform(0.5, 1.5)


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------
class AmbientBackgroundWidget(QWidget):
    """Night-sky gradient background with drifting gold stars and moon phase.

    The moon glyph in the top-right is clickable and emits theme_toggle_requested
    when clicked.

    Signals
    -------
    theme_toggle_requested:
        Emitted when the user clicks the moon button.

    Parameters
    ----------
    parent:
        Optional parent widget.
    """

    theme_toggle_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._stars: list[_Star] = []
        self._moon_char = _moon_char(_moon_phase())
        self._moon_font = QFont("Segoe UI Emoji", _MOON_SIZE)
        self._moon_rect = QRectF()  # Stores moon clickable area

        # Animation timer for star drift
        self._dt = AMBIENT_FRAME_MS / 1000.0
        self._timer = QTimer(self)
        self._timer.setInterval(AMBIENT_FRAME_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        # Enable mouse tracking for hover cursor
        self.setMouseTracking(True)

    def _ensure_stars(self) -> None:
        """Create stars if not yet initialized or if widget was resized."""
        if len(self._stars) < _NUM_STARS:
            w = max(self.width(), 1)
            h = max(self.height(), 1)
            self._stars = [_Star(w, h) for _ in range(_NUM_STARS)]

    def resizeEvent(self, event: object) -> None:  # noqa: N802
        """Regenerate stars on resize to fill the new area."""
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        self._stars = [_Star(w, h) for _ in range(_NUM_STARS)]

    def _tick(self) -> None:
        """Advance star positions."""
        w = self.width()
        for star in self._stars:
            star.x += star.drift_speed * self._dt
            if star.x > w + 5:
                star.x = -5
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        self._ensure_stars()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # --- Gradient background ---
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(_GRADIENT_TOP))
        grad.setColorAt(1.0, QColor(_GRADIENT_BOTTOM))
        painter.fillRect(self.rect(), QBrush(grad))

        # --- Stars ---
        painter.setPen(Qt.PenStyle.NoPen)
        for star in self._stars:
            color = QColor(_STAR_COLOR)
            color.setAlphaF(star.opacity)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(star.x, star.y), star.size, star.size)

        # --- Moon phase glyph (top-right) ---
        painter.setFont(self._moon_font)
        painter.setPen(QPen(QColor(255, 255, 255, 180)))
        self._moon_rect = QRectF(w - _MOON_SIZE - 12, 4, _MOON_SIZE + 8, _MOON_SIZE + 8)
        painter.drawText(
            self._moon_rect, int(Qt.AlignmentFlag.AlignCenter), self._moon_char,
        )

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Detect clicks on the moon to toggle theme."""
        if self._moon_rect.contains(event.pos()):
            self.theme_toggle_requested.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event: object) -> None:
        """Show pointer cursor when hovering over moon."""
        if hasattr(event, 'pos') and self._moon_rect.contains(event.pos()):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Update cursor when moving over moon."""
        if self._moon_rect.contains(event.pos()):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)
