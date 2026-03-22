# owl_3d_widget.py
# Developer: Marcus Daley
# Date: 2026-02-21
# Purpose: 3D sprite-based owl mascot widget with pre-rendered state images and smooth transitions

"""
3D Owl mascot widget using pre-rendered sprite images.

Displays pre-rendered 3D owl sprites for each state with smooth crossfade
transitions between states. Maintains the same API as OwlWidget for drop-in
replacement compatibility.

Usage::

    owl = Owl3DWidget()
    owl.set_state("idle")            # calm owl
    owl.set_state("alert")           # wide-eyed owl
    owl.say("Watching your files.")  # show speech bubble for 5 seconds

Sprite Requirements
-------------------
Place PNG sprites in `gui/assets/owl_3d/`:
- owl_3d_sleeping.png
- owl_3d_waking.png
- owl_3d_idle.png
- owl_3d_scanning.png
- owl_3d_curious.png
- owl_3d_alert.png
- owl_3d_alarm.png
- owl_3d_proud.png

Each sprite should be 512x512 PNG with transparency.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import (
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from gui.constants import (
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
    STATE_LABELS,
    STATE_LABEL_COLOR,
)
from gui.paths import ASSETS_DIR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("owl_3d_widget")

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
_BUBBLE_BG = QColor(BUBBLE_BG)
_BUBBLE_TEXT_COLOR = QColor(BUBBLE_TEXT)
_BUBBLE_BORDER = QColor(BUBBLE_BORDER)
_BUBBLE_SHADOW = QColor(0, 0, 0, BUBBLE_SHADOW_ALPHA)

# 3D sprite directory
_SPRITE_DIR = ASSETS_DIR / "owl_3d"

# State to sprite filename mapping
_STATE_SPRITES = {
    "sleeping": "owl_3d_sleeping.png",
    "waking": "owl_3d_waking.png",
    "idle": "owl_3d_idle.png",
    "scanning": "owl_3d_scanning.png",
    "curious": "owl_3d_curious.png",
    "alert": "owl_3d_alert.png",
    "alarm": "owl_3d_alarm.png",
    "proud": "owl_3d_proud.png",
}


# ---------------------------------------------------------------------------
# Speech bubble (reused from owl_widget.py)
# ---------------------------------------------------------------------------
class SpeechBubble(QWidget):
    """Rounded-rect speech bubble with a pointer triangle."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setVisible(False)

        self._opacity: float = 0.0
        self._message: str = ""

        self._font = QFont(FONT_FAMILY, BUBBLE_FONT_SIZE)
        self._font.setWeight(QFont.Weight.Medium)

    def _get_bubble_opacity(self) -> float:
        return self._opacity

    def _set_bubble_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    bubble_opacity = pyqtProperty(float, _get_bubble_opacity, _set_bubble_opacity)

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, text: str) -> None:
        self._message = text
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        if not self._message or self._opacity <= 0.0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        painter.setFont(self._font)

        w = self.width()
        h = self.height()

        bubble_h = h - BUBBLE_POINTER_SIZE
        bubble_rect_x = 2.0
        bubble_rect_y = 2.0
        bubble_rect_w = w - 4.0
        bubble_rect_h = bubble_h - 4.0

        # Shadow
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

        # Pointer triangle
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
        from PyQt6.QtCore import QRectF
        text_rect = QRectF(
            bubble_rect_x + BUBBLE_PADDING,
            bubble_rect_y + BUBBLE_PADDING,
            bubble_rect_w - 2 * BUBBLE_PADDING,
            bubble_rect_h - 2 * BUBBLE_PADDING,
        )
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap),
            self._message,
        )

        painter.end()


# ---------------------------------------------------------------------------
# Main 3D owl widget
# ---------------------------------------------------------------------------
class Owl3DWidget(QWidget):
    """3D sprite-based owl mascot widget with crossfade transitions.

    Drop-in replacement for OwlWidget that uses pre-rendered 3D sprites
    instead of SVG files.

    Parameters
    ----------
    owl_size:
        Width and height of the owl display area in pixels.
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
        self._current_pixmap: QPixmap | None = None

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Speech bubble
        self._bubble = SpeechBubble(self)
        self._bubble.setFixedSize(owl_size + 60, 60)

        # 3D sprite display (QLabel with pixmap)
        self._sprite = QLabel(self)
        self._sprite.setFixedSize(QSize(owl_size, owl_size))
        self._sprite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sprite.setScaledContents(False)  # We'll scale pixmap manually

        # Crossfade overlay for smooth transitions
        self._overlay = QLabel(self)
        self._overlay.setFixedSize(QSize(owl_size, owl_size))
        self._overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay.setScaledContents(False)
        self._overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._overlay_opacity = 0.0

        # State label
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            f"color: {STATE_LABEL_COLOR}; font-size: 10px; font-family: '{FONT_FAMILY}';"
        )

        layout.addWidget(self._bubble, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._sprite, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Position overlay on top of sprite
        self._overlay.setParent(self._sprite)
        self._overlay.move(0, 0)
        self._overlay.hide()

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

        # --- Crossfade animation ---
        self._crossfade_anim = QPropertyAnimation(self, b"overlay_opacity")
        self._crossfade_anim.setDuration(300)  # 300ms crossfade
        self._crossfade_anim.setStartValue(1.0)
        self._crossfade_anim.setEndValue(0.0)
        self._crossfade_anim.finished.connect(self._on_crossfade_done)

        # --- Initial state ---
        self.set_state("idle")

    # -- Qt property for crossfade animation ---------------------------------

    def _get_overlay_opacity(self) -> float:
        return self._overlay_opacity

    def _set_overlay_opacity(self, value: float) -> None:
        self._overlay_opacity = value
        # Apply opacity via style sheet
        alpha = int(value * 255)
        self._overlay.setStyleSheet(f"background: transparent;")
        self._overlay.setWindowOpacity(value)
        self._overlay.update()

    overlay_opacity = pyqtProperty(float, _get_overlay_opacity, _set_overlay_opacity)

    # -- Public API -----------------------------------------------------------

    def set_state(self, state: str) -> None:
        """Switch the owl to a visual state.

        Parameters
        ----------
        state:
            One of the 8 owl states (sleeping, waking, idle, scanning,
            curious, alert, alarm, proud).
        """
        if state not in _STATE_SPRITES:
            logger.warning("Unknown owl state: %r (using idle)", state)
            state = "idle"

        # Load new sprite
        sprite_path = _SPRITE_DIR / _STATE_SPRITES[state]

        if not sprite_path.exists():
            # Fallback: try to load a placeholder or log error
            logger.error("3D sprite not found: %s", sprite_path)
            logger.info(
                "To use 3D owl sprites, generate PNG images using the prompts "
                "in CLAUDE.md and place them in %s", _SPRITE_DIR
            )
            # For now, just show the state label
            self._current_state = state
            self._label.setText(STATE_LABELS.get(state, ""))
            return

        new_pixmap = QPixmap(str(sprite_path))

        if new_pixmap.isNull():
            logger.error("Failed to load sprite: %s", sprite_path)
            return

        # Scale pixmap to owl_size maintaining aspect ratio
        scaled_pixmap = new_pixmap.scaled(
            self._owl_size,
            self._owl_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Crossfade transition
        if self._current_pixmap is not None:
            # Set current sprite as overlay
            self._overlay.setPixmap(self._current_pixmap)
            self._overlay.show()
            self._overlay_opacity = 1.0

            # Set new sprite as base
            self._sprite.setPixmap(scaled_pixmap)

            # Animate overlay fade out (reveals new sprite underneath)
            self._crossfade_anim.start()
        else:
            # First load, no transition
            self._sprite.setPixmap(scaled_pixmap)

        self._current_pixmap = scaled_pixmap
        self._current_state = state
        self._label.setText(STATE_LABELS.get(state, ""))

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
        """
        self._hide_timer.stop()
        self._fade_in_anim.stop()
        self._fade_out_anim.stop()

        self._bubble.message = message
        self._bubble.setVisible(True)

        self._fade_in_anim.start()
        self._hide_timer.start(duration_ms)

    def dismiss(self) -> None:
        """Immediately start fading out the speech bubble."""
        self._hide_timer.stop()
        self._fade_in_anim.stop()
        self._start_fade_out()

    # -- Private --------------------------------------------------------------

    def _start_fade_out(self) -> None:
        """Begin the fade-out animation."""
        self._fade_out_anim.setStartValue(self._bubble._opacity)
        self._fade_out_anim.start()

    def _on_fade_out_done(self) -> None:
        """Hide the bubble widget after fade-out completes."""
        self._bubble.setVisible(False)
        self._bubble._opacity = 0.0

    def _on_crossfade_done(self) -> None:
        """Hide overlay after crossfade completes."""
        self._overlay.hide()
        self._overlay_opacity = 0.0
