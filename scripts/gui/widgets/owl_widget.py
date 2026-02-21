"""
Owl mascot widget with animated speech bubbles.

Displays the owl SVG mascot and overlays speech bubble messages
with fade-in/fade-out animations. Used as the friendly status
indicator in the file watcher GUI.

Usage::

    owl = OwlWidget()
    owl.set_state("idle")            # calm owl
    owl.set_state("alert")           # wide-eyed owl
    owl.set_state("alarm")           # alarmed owl with red accents
    owl.say("Watching your files.")  # show speech bubble for 5 seconds
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

from PyQt6.QtCore import (
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
from gui.paths import ASSETS_DIR

_STATE_SVG_MAP: Final[dict[str, str]] = {
    "idle": "owl_idle.svg",
    "alert": "owl_alert.svg",
    "alarm": "owl_alarm.svg",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("owl_widget")

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
_BUBBLE_BG = QColor("#F5E6C8")
_BUBBLE_TEXT_COLOR = QColor("#1B2838")
_BUBBLE_BORDER = QColor("#C9A94E")
_BUBBLE_SHADOW = QColor(0, 0, 0, 40)
_BUBBLE_FONT_SIZE = 11
_BUBBLE_PADDING = 10
_BUBBLE_RADIUS = 10
_BUBBLE_POINTER_SIZE = 8


# ---------------------------------------------------------------------------
# Speech bubble overlay widget
# ---------------------------------------------------------------------------
class SpeechBubble(QWidget):
    """Rounded-rect speech bubble with a pointer triangle.

    Supports opacity animation for smooth fade-in and fade-out.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setVisible(False)

        self._opacity: float = 0.0
        self._message: str = ""

        self._font = QFont("Segoe UI", _BUBBLE_FONT_SIZE)
        self._font.setWeight(QFont.Weight.Medium)

    # -- Qt property for animation ----------------------------------------

    def _get_bubble_opacity(self) -> float:
        return self._opacity

    def _set_bubble_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    bubble_opacity = pyqtProperty(float, _get_bubble_opacity, _set_bubble_opacity)

    # -- Public API -------------------------------------------------------

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, text: str) -> None:
        self._message = text
        self.update()

    # -- Painting ---------------------------------------------------------

    def paintEvent(self, event: object) -> None:  # noqa: N802
        if not self._message or self._opacity <= 0.0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        painter.setFont(self._font)

        w = self.width()
        h = self.height()

        # Bubble body rect (leave room for pointer at bottom)
        bubble_h = h - _BUBBLE_POINTER_SIZE
        bubble_rect_x = 2.0
        bubble_rect_y = 2.0
        bubble_rect_w = w - 4.0
        bubble_rect_h = bubble_h - 4.0

        # Shadow (offset by 2px)
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(
            bubble_rect_x + 2,
            bubble_rect_y + 2,
            bubble_rect_w,
            bubble_rect_h,
            _BUBBLE_RADIUS,
            _BUBBLE_RADIUS,
        )
        painter.fillPath(shadow_path, _BUBBLE_SHADOW)

        # Bubble background
        bubble_path = QPainterPath()
        bubble_path.addRoundedRect(
            bubble_rect_x,
            bubble_rect_y,
            bubble_rect_w,
            bubble_rect_h,
            _BUBBLE_RADIUS,
            _BUBBLE_RADIUS,
        )
        painter.fillPath(bubble_path, _BUBBLE_BG)

        # Border
        pen = QPen(_BUBBLE_BORDER, 1.5)
        painter.setPen(pen)
        painter.drawPath(bubble_path)

        # Pointer triangle (centered at bottom of bubble)
        center_x = w / 2.0
        ptr_top = bubble_rect_y + bubble_rect_h
        pointer = QPainterPath()
        pointer.moveTo(center_x - _BUBBLE_POINTER_SIZE, ptr_top)
        pointer.lineTo(center_x, ptr_top + _BUBBLE_POINTER_SIZE)
        pointer.lineTo(center_x + _BUBBLE_POINTER_SIZE, ptr_top)
        pointer.closeSubpath()

        painter.fillPath(pointer, _BUBBLE_BG)
        painter.setPen(pen)
        painter.drawLine(
            int(center_x - _BUBBLE_POINTER_SIZE), int(ptr_top),
            int(center_x), int(ptr_top + _BUBBLE_POINTER_SIZE),
        )
        painter.drawLine(
            int(center_x), int(ptr_top + _BUBBLE_POINTER_SIZE),
            int(center_x + _BUBBLE_POINTER_SIZE), int(ptr_top),
        )

        # Text
        painter.setPen(QPen(_BUBBLE_TEXT_COLOR))
        text_rect_margin = _BUBBLE_PADDING
        from PyQt6.QtCore import QRectF
        text_rect = QRectF(
            bubble_rect_x + text_rect_margin,
            bubble_rect_y + text_rect_margin,
            bubble_rect_w - 2 * text_rect_margin,
            bubble_rect_h - 2 * text_rect_margin,
        )
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap),
            self._message,
        )

        painter.end()


# ---------------------------------------------------------------------------
# Main owl widget
# ---------------------------------------------------------------------------
class OwlWidget(QWidget):
    """Owl mascot widget with SVG display and speech bubble overlay.

    Parameters
    ----------
    owl_size:
        Width and height of the owl SVG display area in pixels.
    parent:
        Optional parent widget.
    """

    def __init__(
        self,
        owl_size: int = 128,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._owl_size = owl_size
        self._current_state = "idle"

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Speech bubble (positioned above the owl)
        self._bubble = SpeechBubble(self)
        self._bubble.setFixedSize(owl_size + 60, 60)

        # Owl SVG display
        self._svg = QSvgWidget(self)
        self._svg.setFixedSize(QSize(owl_size, owl_size))

        # State label under the owl
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "color: #8899AA; font-size: 10px; font-family: 'Segoe UI';"
        )

        layout.addWidget(self._bubble, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._svg, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Animations ---
        self._fade_in_anim = QPropertyAnimation(self._bubble, b"bubble_opacity")
        self._fade_in_anim.setDuration(300)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)

        self._fade_out_anim = QPropertyAnimation(self._bubble, b"bubble_opacity")
        self._fade_out_anim.setDuration(400)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0.0)
        self._fade_out_anim.finished.connect(self._on_fade_out_done)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)

        # --- Initial state ---
        self.set_state("idle")

    # -- Public API -------------------------------------------------------

    def set_state(self, state: str) -> None:
        """Switch the owl to a visual state.

        Parameters
        ----------
        state:
            One of ``"idle"``, ``"alert"``, or ``"alarm"``.
        """
        if state not in _STATE_SVG_MAP:
            logger.warning("Unknown owl state: %r (using idle)", state)
            state = "idle"

        self._current_state = state
        svg_path = ASSETS_DIR / _STATE_SVG_MAP[state]

        if svg_path.exists():
            self._svg.load(str(svg_path))
        else:
            logger.error("SVG not found: %s", svg_path)

        labels = {
            "idle": "All quiet",
            "alert": "Changes detected",
            "alarm": "Security alert",
        }
        self._label.setText(labels.get(state, ""))

    @property
    def current_state(self) -> str:
        """Return the current owl state name."""
        return self._current_state

    def say(self, message: str, duration_ms: int = 5000) -> None:
        """Show a speech bubble with the given message.

        Parameters
        ----------
        message:
            Text to display in the speech bubble.
        duration_ms:
            How long to show the bubble before it fades out.
            Defaults to 5000 ms.
        """
        # Stop any running animations/timers
        self._hide_timer.stop()
        self._fade_in_anim.stop()
        self._fade_out_anim.stop()

        self._bubble.message = message
        self._bubble.setVisible(True)

        # Fade in
        self._fade_in_anim.start()

        # Schedule fade out
        self._hide_timer.start(duration_ms)

    def dismiss(self) -> None:
        """Immediately start fading out the speech bubble."""
        self._hide_timer.stop()
        self._fade_in_anim.stop()
        self._start_fade_out()

    # -- Private ----------------------------------------------------------

    def _start_fade_out(self) -> None:
        """Begin the fade-out animation."""
        self._fade_out_anim.setStartValue(self._bubble._opacity)
        self._fade_out_anim.start()

    def _on_fade_out_done(self) -> None:
        """Hide the bubble widget after fade-out completes."""
        self._bubble.setVisible(False)
        self._bubble._opacity = 0.0


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
def _test() -> None:
    """Quick visual test of the owl widget."""
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Owl Widget Test")
    window.setStyleSheet("background-color: #0D1117;")

    layout = QVBoxLayout(window)
    owl = OwlWidget(owl_size=128)
    layout.addWidget(owl, alignment=Qt.AlignmentFlag.AlignCenter)

    owl.set_state("idle")
    owl.say("Hello! I am watching your files.", 3000)

    # Cycle through states for demo
    QTimer.singleShot(3500, lambda: owl.set_state("alert"))
    QTimer.singleShot(3500, lambda: owl.say("Changes detected!", 3000))
    QTimer.singleShot(7000, lambda: owl.set_state("alarm"))
    QTimer.singleShot(7000, lambda: owl.say("Security alert!", 3000))
    QTimer.singleShot(10500, lambda: owl.set_state("idle"))
    QTimer.singleShot(10500, lambda: owl.say("All clear now.", 3000))

    window.resize(300, 300)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    _test()
