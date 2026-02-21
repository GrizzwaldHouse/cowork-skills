# owl_widget.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Animated mascot widget providing friendly visual feedback through state-driven SVG switching and speech bubbles

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

import math

from PyQt6.QtCore import (
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QTransform
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from gui.constants import (
    ANIMATION_FPS,
    BREATHING_CYCLE_MS,
    BREATHING_SCALE_RANGE,
    BUBBLE_BG,
    BUBBLE_BORDER,
    BUBBLE_DEFAULT_DURATION_MS,
    BUBBLE_FONT_SIZE,
    BUBBLE_PADDING,
    BUBBLE_POINTER_SIZE,
    BUBBLE_RADIUS,
    BUBBLE_SHADOW_ALPHA,
    BUBBLE_TEXT,
    FADE_IN_MS,
    FADE_OUT_MS,
    FONT_FAMILY,
    SCANNING_CYCLE_MS,
    SCANNING_ROTATION_DEG,
    STATE_LABELS,
    STATE_LABEL_COLOR,
    STATE_SVG_MAP,
)
from gui.paths import ASSETS_DIR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("owl_widget")

# ---------------------------------------------------------------------------
# Style constants (QColor instances built from constants)
# ---------------------------------------------------------------------------
_BUBBLE_BG = QColor(BUBBLE_BG)
_BUBBLE_TEXT_COLOR = QColor(BUBBLE_TEXT)
_BUBBLE_BORDER = QColor(BUBBLE_BORDER)
_BUBBLE_SHADOW = QColor(0, 0, 0, BUBBLE_SHADOW_ALPHA)


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

        self._font = QFont(FONT_FAMILY, BUBBLE_FONT_SIZE)
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
        bubble_h = h - BUBBLE_POINTER_SIZE
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
            BUBBLE_RADIUS,
            BUBBLE_RADIUS,
        )
        painter.fillPath(shadow_path, _BUBBLE_SHADOW)

        # Bubble background
        bubble_path = QPainterPath()
        bubble_path.addRoundedRect(
            bubble_rect_x,
            bubble_rect_y,
            bubble_rect_w,
            bubble_rect_h,
            BUBBLE_RADIUS,
            BUBBLE_RADIUS,
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
        pointer.moveTo(center_x - BUBBLE_POINTER_SIZE, ptr_top)
        pointer.lineTo(center_x, ptr_top + BUBBLE_POINTER_SIZE)
        pointer.lineTo(center_x + BUBBLE_POINTER_SIZE, ptr_top)
        pointer.closeSubpath()

        painter.fillPath(pointer, _BUBBLE_BG)
        painter.setPen(pen)
        painter.drawLine(
            int(center_x - BUBBLE_POINTER_SIZE), int(ptr_top),
            int(center_x), int(ptr_top + BUBBLE_POINTER_SIZE),
        )
        painter.drawLine(
            int(center_x), int(ptr_top + BUBBLE_POINTER_SIZE),
            int(center_x + BUBBLE_POINTER_SIZE), int(ptr_top),
        )

        # Text
        painter.setPen(QPen(_BUBBLE_TEXT_COLOR))
        text_rect_margin = BUBBLE_PADDING
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
            f"color: {STATE_LABEL_COLOR}; font-size: 10px; font-family: '{FONT_FAMILY}';"
        )

        layout.addWidget(self._bubble, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._svg, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Speech bubble animations ---
        self._fade_in_anim = QPropertyAnimation(self._bubble, b"bubble_opacity")
        self._fade_in_anim.setDuration(FADE_IN_MS)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)

        self._fade_out_anim = QPropertyAnimation(self._bubble, b"bubble_opacity")
        self._fade_out_anim.setDuration(FADE_OUT_MS)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0.0)
        self._fade_out_anim.finished.connect(self._on_fade_out_done)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)

        # --- State animations (breathing, scanning) ---
        self._anim_tick = 0
        frame_ms = 1000 // ANIMATION_FPS
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(frame_ms)
        self._anim_timer.timeout.connect(self._on_anim_tick)

        # --- Initial state ---
        self.set_state("idle")

    # -- Public API -------------------------------------------------------

    def set_state(self, state: str) -> None:
        """Switch the owl to a visual state.

        Parameters
        ----------
        state:
            One of the 8 owl states (sleeping, waking, idle, scanning,
            curious, alert, alarm, proud).
        """
        if state not in STATE_SVG_MAP:
            logger.warning("Unknown owl state: %r (using idle)", state)
            state = "idle"

        self._current_state = state
        svg_path = ASSETS_DIR / STATE_SVG_MAP[state]

        if svg_path.exists():
            self._svg.load(str(svg_path))
        else:
            logger.error("SVG not found: %s", svg_path)

        self._label.setText(STATE_LABELS.get(state, ""))

        # Reset SVG transform
        self._svg.setProperty("_rotation", 0.0)

        # Start/stop state-specific animations
        if state in ("sleeping", "scanning"):
            self._anim_tick = 0
            if not self._anim_timer.isActive():
                self._anim_timer.start()
        else:
            self._anim_timer.stop()
            # Reset any transform from previous animation
            self._svg.setFixedSize(QSize(self._owl_size, self._owl_size))

    @property
    def current_state(self) -> str:
        """Return the current owl state name."""
        return self._current_state

    def say(self, message: str, duration_ms: int = BUBBLE_DEFAULT_DURATION_MS) -> None:
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

    def _on_anim_tick(self) -> None:
        """Advance state-specific animation by one frame."""
        self._anim_tick += 1
        frame_ms = 1000 // ANIMATION_FPS

        if self._current_state == "sleeping":
            # Breathing: 2% scale pulse using sine wave over BREATHING_CYCLE_MS
            elapsed = (self._anim_tick * frame_ms) % BREATHING_CYCLE_MS
            phase = (elapsed / BREATHING_CYCLE_MS) * 2.0 * math.pi
            scale = 1.0 + BREATHING_SCALE_RANGE * math.sin(phase)
            new_size = int(self._owl_size * scale)
            self._svg.setFixedSize(QSize(new_size, new_size))

        elif self._current_state == "scanning":
            # Head turn: ±SCANNING_ROTATION_DEG oscillation over SCANNING_CYCLE_MS
            elapsed = (self._anim_tick * frame_ms) % SCANNING_CYCLE_MS
            phase = (elapsed / SCANNING_CYCLE_MS) * 2.0 * math.pi
            angle = SCANNING_ROTATION_DEG * math.sin(phase)
            transform = QTransform()
            center = self._owl_size / 2.0
            transform.translate(center, center)
            transform.rotate(angle)
            transform.translate(-center, -center)
            # QSvgWidget doesn't natively support transforms on its content,
            # so we apply it via a container paintEvent workaround:
            # store the angle and trigger a repaint from the parent if needed.
            self._svg.setProperty("_rotation", angle)
            self._svg.update()


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
def _test() -> None:
    """Quick visual test of the owl widget -- cycles through all 8 states."""
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Owl Widget Test")
    window.setStyleSheet("background-color: #0D1117;")

    layout = QVBoxLayout(window)
    owl = OwlWidget(owl_size=128)
    layout.addWidget(owl, alignment=Qt.AlignmentFlag.AlignCenter)

    # State demo sequence (state, speech bubble text, delay_ms)
    sequence = [
        (0, "sleeping", "Zzz... The owl is asleep."),
        (4000, "waking", "Good morning! Waking up..."),
        (6500, "idle", "Standing by, all quiet."),
        (10000, "scanning", "Scanning your files..."),
        (14000, "curious", "Hmm, what's this file?"),
        (18000, "alert", "Changes detected!"),
        (22000, "alarm", "Security alert!"),
        (26000, "proud", "All clear -- great job!"),
        (30000, "idle", "Back to idle. Demo complete."),
    ]

    for delay, state, msg in sequence:
        QTimer.singleShot(delay, lambda s=state: owl.set_state(s))
        QTimer.singleShot(delay, lambda m=msg: owl.say(m, 3500))

    window.resize(300, 350)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    _test()
