# skill_card_widget.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Card widget for displaying extracted Quad Skills with status and actions

"""
Skill card widget for the intelligence panel.

Displays a single extracted Quad Skill with name, confidence bar,
status badge, source label, and approve/reject action buttons.

Usage::

    card = SkillCardWidget({
        "skill_id": "abc-123",
        "name": "Auto-format imports",
        "intent": "Reorder Python imports on save",
        "confidence": 0.82,
        "status": "pending",
        "source_project": "OwlWatcher",
    })
    card.approve_clicked.connect(on_approve)
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.constants import (
    DARK_PANEL,
    FONT_FAMILY,
    GOLD,
    INTEL_APPROVED_COLOR,
    INTEL_PENDING_COLOR,
    INTEL_REJECTED_COLOR,
    MID_PANEL,
    PARCHMENT,
    TEAL,
)

_CARD_HEIGHT = 120
_CONFIDENCE_BAR_HEIGHT = 6
_CONFIDENCE_HIGH = 0.7
_CONFIDENCE_MID = 0.4

_CONFIDENCE_HIGH_COLOR = "#32CD32"
_CONFIDENCE_MID_COLOR = "#FF8C00"
_CONFIDENCE_LOW_COLOR = "#DC143C"

_STATUS_COLORS: dict[str, str] = {
    "approved": INTEL_APPROVED_COLOR,
    "pending": INTEL_PENDING_COLOR,
    "rejected": INTEL_REJECTED_COLOR,
}

_BTN_STYLE_APPROVE = (
    f"QPushButton {{ background: {INTEL_APPROVED_COLOR}; color: #000; "
    f"border: none; border-radius: 3px; padding: 2px 10px; "
    f"font-size: 10px; font-family: '{FONT_FAMILY}'; }}"
    f"QPushButton:hover {{ background: #28a428; }}"
)

_BTN_STYLE_REJECT = (
    f"QPushButton {{ background: {INTEL_REJECTED_COLOR}; color: #fff; "
    f"border: none; border-radius: 3px; padding: 2px 10px; "
    f"font-size: 10px; font-family: '{FONT_FAMILY}'; }}"
    f"QPushButton:hover {{ background: #b01030; }}"
)


def _confidence_color(score: float) -> str:
    """Return hex color based on confidence threshold."""
    if score >= _CONFIDENCE_HIGH:
        return _CONFIDENCE_HIGH_COLOR
    if score >= _CONFIDENCE_MID:
        return _CONFIDENCE_MID_COLOR
    return _CONFIDENCE_LOW_COLOR


class _ConfidenceBar(QWidget):
    """Horizontal confidence score bar."""

    def __init__(self, score: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._score = max(0.0, min(1.0, score))
        self.setFixedHeight(_CONFIDENCE_BAR_HEIGHT)

    def set_score(self, score: float) -> None:
        """Update the confidence score."""
        self._score = max(0.0, min(1.0, score))
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(MID_PANEL))
        painter.drawRoundedRect(0, 0, w, h, 3, 3)

        # Filled portion
        fill_w = int(w * self._score)
        if fill_w > 0:
            painter.setBrush(QColor(_confidence_color(self._score)))
            painter.drawRoundedRect(0, 0, fill_w, h, 3, 3)

        painter.end()


class SkillCardWidget(QFrame):
    """Card widget displaying a single Quad Skill with actions.

    Emits ``approve_clicked(skill_id)`` and ``reject_clicked(skill_id)``
    when the user interacts with the action buttons.
    """

    approve_clicked = pyqtSignal(str)
    reject_clicked = pyqtSignal(str)
    card_clicked = pyqtSignal(str)

    def __init__(self, skill_data: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._skill_id: str = skill_data.get("skill_id", "")
        self._status: str = skill_data.get("status", "pending")
        self._build_ui(skill_data)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self, data: dict) -> None:
        """Build the card layout."""
        self.setFixedHeight(_CARD_HEIGHT)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(
            f"QFrame {{ background: {DARK_PANEL}; border: 1px solid {TEAL}; "
            f"border-radius: 6px; }}"
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(8)

        # Left column: name, intent, confidence bar, source
        left = QVBoxLayout()
        left.setSpacing(4)

        self._name_label = QLabel(data.get("name", "Unnamed Skill"))
        self._name_label.setStyleSheet(
            f"color: {GOLD}; font-size: 13px; font-weight: bold; "
            f"font-family: '{FONT_FAMILY}'; border: none;"
        )
        left.addWidget(self._name_label)

        self._intent_label = QLabel(data.get("intent", ""))
        self._intent_label.setStyleSheet(
            f"color: {PARCHMENT}; font-size: 10px; font-family: '{FONT_FAMILY}'; "
            f"border: none;"
        )
        self._intent_label.setWordWrap(True)
        left.addWidget(self._intent_label)

        # Confidence row: bar + score text
        conf_row = QHBoxLayout()
        conf_row.setSpacing(6)
        confidence = data.get("confidence", 0.0)
        self._confidence_bar = _ConfidenceBar(confidence)
        conf_row.addWidget(self._confidence_bar, stretch=1)

        self._conf_label = QLabel(f"{confidence:.0%}")
        self._conf_label.setStyleSheet(
            f"color: {_confidence_color(confidence)}; font-size: 10px; "
            f"font-family: '{FONT_FAMILY}'; border: none;"
        )
        self._conf_label.setFixedWidth(36)
        conf_row.addWidget(self._conf_label)
        left.addLayout(conf_row)

        # Source project
        source = data.get("source_project", "")
        self._source_label = QLabel(f"Source: {source}" if source else "")
        self._source_label.setStyleSheet(
            f"color: #8899AA; font-size: 9px; font-family: '{FONT_FAMILY}'; "
            f"border: none;"
        )
        left.addWidget(self._source_label)

        left.addStretch()
        root.addLayout(left, stretch=1)

        # Right column: status badge + action buttons
        right = QVBoxLayout()
        right.setSpacing(6)
        right.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._status_badge = QLabel(self._status.upper())
        self._update_badge_style()
        right.addWidget(self._status_badge, alignment=Qt.AlignmentFlag.AlignRight)

        # Validation score labels (hidden until set)
        self._arch_label = QLabel("")
        self._sec_label = QLabel("")
        self._qual_label = QLabel("")
        for lbl in (self._arch_label, self._sec_label, self._qual_label):
            lbl.setStyleSheet(
                f"color: #8899AA; font-size: 9px; font-family: '{FONT_FAMILY}'; "
                f"border: none;"
            )
            lbl.hide()
            right.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignRight)

        right.addStretch()

        # Action buttons (only for pending)
        self._btn_row = QWidget()
        btn_layout = QHBoxLayout(self._btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        self._approve_btn = QPushButton("Approve")
        self._approve_btn.setStyleSheet(_BTN_STYLE_APPROVE)
        self._approve_btn.setFixedHeight(22)
        self._approve_btn.clicked.connect(self._on_approve)
        btn_layout.addWidget(self._approve_btn)

        self._reject_btn = QPushButton("Reject")
        self._reject_btn.setStyleSheet(_BTN_STYLE_REJECT)
        self._reject_btn.setFixedHeight(22)
        self._reject_btn.clicked.connect(self._on_reject)
        btn_layout.addWidget(self._reject_btn)

        right.addWidget(self._btn_row)
        self._btn_row.setVisible(self._status == "pending")

        root.addLayout(right)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def update_status(self, status: str) -> None:
        """Update the status badge and toggle action button visibility."""
        self._status = status.lower()
        self._status_badge.setText(self._status.upper())
        self._update_badge_style()
        self._btn_row.setVisible(self._status == "pending")

    def set_validation_scores(
        self, arch: float, sec: float, qual: float
    ) -> None:
        """Show architecture, security, and quality validation scores."""
        self._arch_label.setText(f"Arch: {arch:.0%}")
        self._sec_label.setText(f"Sec:  {sec:.0%}")
        self._qual_label.setText(f"Qual: {qual:.0%}")
        self._arch_label.show()
        self._sec_label.show()
        self._qual_label.show()

    @property
    def skill_id(self) -> str:
        """Return the skill ID for this card."""
        return self._skill_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_badge_style(self) -> None:
        """Apply the correct color to the status badge."""
        color = _STATUS_COLORS.get(self._status, INTEL_PENDING_COLOR)
        self._status_badge.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: bold; "
            f"font-family: '{FONT_FAMILY}'; border: 1px solid {color}; "
            f"border-radius: 3px; padding: 1px 6px;"
        )

    def _on_approve(self) -> None:
        """Handle approve button click."""
        self.approve_clicked.emit(self._skill_id)

    def _on_reject(self) -> None:
        """Handle reject button click."""
        self.reject_clicked.emit(self._skill_id)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Emit card_clicked when the card body is clicked."""
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.card_clicked.emit(self._skill_id)
        super().mousePressEvent(event)
