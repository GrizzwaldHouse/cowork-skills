# intelligence_panel.py
# Developer: Marcus Daley
# Date: 2026-03-23
# Purpose: Intelligence dashboard tab for skill queue, validation status, and session monitoring

"""
Intelligence panel for the OwlWatcher UI.

Provides a tabbed dashboard with four quadrants: session monitor,
skill queue, validation status, and safety log.  All data arrives
via public slot methods wired to signals in ``app.py``.

Usage::

    panel = IntelligencePanel()
    panel.on_skill_extracted(skill_dict)
    panel.on_session_event(event_dict)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.constants import (
    DARK_PANEL,
    FONT_FAMILY,
    GOLD,
    INTEL_APPROVED_COLOR,
    INTEL_PENDING_COLOR,
    INTEL_REFACTORING_COLOR,
    INTEL_REJECTED_COLOR,
    MID_PANEL,
    MONO_FONT,
    NAVY,
    PARCHMENT,
    TEAL,
)
from gui.widgets.session_timeline_widget import SessionTimelineWidget
from gui.widgets.skill_card_widget import SkillCardWidget

_SECTION_HEADER_STYLE = (
    f"color: {GOLD}; font-size: 13px; font-weight: bold; "
    f"font-family: '{FONT_FAMILY}';"
)
_LABEL_STYLE = (
    f"color: {PARCHMENT}; font-size: 11px; font-family: '{FONT_FAMILY}';"
)
_STAT_VALUE_STYLE = (
    f"color: {GOLD}; font-size: 12px; font-weight: bold; "
    f"font-family: '{FONT_FAMILY}';"
)
_DIM_LABEL_STYLE = (
    f"color: #8899AA; font-size: 10px; font-family: '{FONT_FAMILY}';"
)
_BADGE_STYLE = (
    f"color: {GOLD}; background: {TEAL}; font-size: 10px; "
    f"font-weight: bold; font-family: '{FONT_FAMILY}'; "
    f"border-radius: 3px; padding: 1px 6px;"
)
_GUARD_ACTIVE_STYLE = (
    f"color: {INTEL_APPROVED_COLOR}; font-size: 11px; font-weight: bold; "
    f"font-family: '{FONT_FAMILY}';"
)
_ROLLBACK_BTN_STYLE = (
    f"QPushButton {{ background: {INTEL_REJECTED_COLOR}; color: #fff; "
    f"border: none; border-radius: 4px; padding: 4px 12px; "
    f"font-size: 10px; font-family: '{FONT_FAMILY}'; }}"
    f"QPushButton:hover {{ background: #b01030; }}"
)
_SAFETY_LOG_STYLE = (
    f"background: {DARK_PANEL}; color: {PARCHMENT}; border: 1px solid {TEAL}; "
    f"border-radius: 4px; font-size: 10px; font-family: {MONO_FONT};"
)

# Agent badge status colors
_AGENT_STATUS_COLORS: dict[str, str] = {
    "running": "#32CD32",     # Green
    "paused": "#FF8C00",      # Orange
    "stopped": "#8899AA",     # Gray
    "error": "#FF6B6B",       # Red
    "configured": "#20B2AA",  # Teal
    "uninitialized": "#8899AA",
}


def _make_section_frame() -> QFrame:
    """Create a styled section frame."""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{ background: {MID_PANEL}; border: 1px solid {TEAL}; "
        f"border-radius: 6px; }}"
    )
    return frame


def _make_scroll_area() -> QScrollArea:
    """Create a transparent scroll area for skill cards."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        f"QScrollArea {{ background: transparent; border: none; }}"
        f"QScrollBar:vertical {{ background: {DARK_PANEL}; width: 8px; "
        f"border-radius: 4px; }}"
        f"QScrollBar::handle:vertical {{ background: {TEAL}; "
        f"border-radius: 4px; min-height: 20px; }}"
        f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
    )
    return scroll


class IntelligencePanel(QWidget):
    """Intelligence dashboard panel for the OwlWatcher UI."""

    # Signals for communicating with app.py
    skill_approve_requested = pyqtSignal(str)   # skill_id
    skill_reject_requested = pyqtSignal(str)    # skill_id
    rollback_requested = pyqtSignal(str)        # skill_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pending_cards: dict[str, SkillCardWidget] = {}
        self._approved_cards: dict[str, SkillCardWidget] = {}
        self._last_approved_id: str = ""
        self._agent_badges: dict[str, QLabel] = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the intelligence panel layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # Agent status badges row (above all other content)
        root.addLayout(self._create_agent_badges())

        # Top section: Session Monitor (40%) + Skill Queue (60%)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self._build_session_monitor())
        top_splitter.addWidget(self._build_skill_queue())
        top_splitter.setStretchFactor(0, 2)
        top_splitter.setStretchFactor(1, 3)
        top_splitter.setHandleWidth(2)
        root.addWidget(top_splitter, stretch=3)

        # Bottom section: Validation Status + Safety Log
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(self._build_validation_status())
        bottom_splitter.addWidget(self._build_safety_log())
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)
        bottom_splitter.setHandleWidth(2)
        root.addWidget(bottom_splitter, stretch=1)

    def _create_agent_badges(self) -> QHBoxLayout:
        """Create a horizontal row of agent status badges."""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        agent_names = ["Extractor", "Validator", "Refactor", "Sync"]
        for name in agent_names:
            badge = QLabel(f"{name}: --")
            badge.setStyleSheet(
                f"color: #8899AA; background: {DARK_PANEL}; "
                f"font-size: 10px; font-weight: bold; "
                f"font-family: '{FONT_FAMILY}'; "
                f"border-radius: 3px; padding: 2px 8px; "
                f"border: 1px solid {TEAL};"
            )
            layout.addWidget(badge)
            self._agent_badges[name.lower()] = badge

        layout.addStretch()
        return layout

    def _build_session_monitor(self) -> QWidget:
        """Build the session monitor section (top-left)."""
        frame = _make_section_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("Active Sessions")
        header.setStyleSheet(_SECTION_HEADER_STYLE)
        layout.addWidget(header)

        self._session_timeline = SessionTimelineWidget()
        layout.addWidget(self._session_timeline, stretch=1)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self._total_events_label = QLabel("Events: 0")
        self._total_events_label.setStyleSheet(_LABEL_STYLE)
        stats_row.addWidget(self._total_events_label)

        self._total_commits_label = QLabel("Commits: 0")
        self._total_commits_label.setStyleSheet(_LABEL_STYLE)
        stats_row.addWidget(self._total_commits_label)

        self._active_idle_label = QLabel("Active: 0 / Idle: 0")
        self._active_idle_label.setStyleSheet(_DIM_LABEL_STYLE)
        stats_row.addWidget(self._active_idle_label)

        stats_row.addStretch()
        layout.addLayout(stats_row)

        return frame

    def _build_skill_queue(self) -> QWidget:
        """Build the skill queue section (top-right)."""
        frame = _make_section_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Pending header with count badge
        pending_row = QHBoxLayout()
        pending_header = QLabel("Pending Review")
        pending_header.setStyleSheet(_SECTION_HEADER_STYLE)
        pending_row.addWidget(pending_header)

        self._pending_count_badge = QLabel("0")
        self._pending_count_badge.setStyleSheet(_BADGE_STYLE)
        pending_row.addWidget(self._pending_count_badge)
        pending_row.addStretch()
        layout.addLayout(pending_row)

        # Pending scroll area
        self._pending_scroll = _make_scroll_area()
        self._pending_container = QWidget()
        self._pending_container.setStyleSheet("background: transparent;")
        self._pending_layout = QVBoxLayout(self._pending_container)
        self._pending_layout.setContentsMargins(0, 0, 0, 0)
        self._pending_layout.setSpacing(4)
        self._pending_layout.addStretch()
        self._pending_scroll.setWidget(self._pending_container)
        layout.addWidget(self._pending_scroll, stretch=1)

        # Recently installed header
        installed_row = QHBoxLayout()
        installed_header = QLabel("Recently Installed")
        installed_header.setStyleSheet(_SECTION_HEADER_STYLE)
        installed_row.addWidget(installed_header)

        self._approved_count_badge = QLabel("0")
        self._approved_count_badge.setStyleSheet(_BADGE_STYLE)
        installed_row.addWidget(self._approved_count_badge)
        installed_row.addStretch()
        layout.addLayout(installed_row)

        # Approved scroll area
        self._approved_scroll = _make_scroll_area()
        self._approved_container = QWidget()
        self._approved_container.setStyleSheet("background: transparent;")
        self._approved_layout = QVBoxLayout(self._approved_container)
        self._approved_layout.setContentsMargins(0, 0, 0, 0)
        self._approved_layout.setSpacing(4)
        self._approved_layout.addStretch()
        self._approved_scroll.setWidget(self._approved_container)
        layout.addWidget(self._approved_scroll, stretch=1)

        return frame

    def _build_validation_status(self) -> QWidget:
        """Build the validation status section (bottom-left)."""
        frame = _make_section_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("Validation Status")
        header.setStyleSheet(_SECTION_HEADER_STYLE)
        layout.addWidget(header)

        # Score rows
        self._arch_score_label = self._make_score_row(layout, "Architecture:", "---")
        self._sec_score_label = self._make_score_row(layout, "Security:", "---")
        self._qual_score_label = self._make_score_row(layout, "Quality:", "---")

        layout.addSpacing(6)

        # Count rows
        self._auto_approved_label = self._make_score_row(
            layout, "Auto-approved:", "0"
        )
        self._needs_review_label = self._make_score_row(
            layout, "Needs review:", "0"
        )
        self._rejected_count_label = self._make_score_row(
            layout, "Rejected:", "0"
        )

        layout.addStretch()
        return frame

    def _build_safety_log(self) -> QWidget:
        """Build the safety log section (bottom-right)."""
        frame = _make_section_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("Safety Log")
        header.setStyleSheet(_SECTION_HEADER_STYLE)
        layout.addWidget(header)

        # Safety log text area
        self._safety_log = QTextEdit()
        self._safety_log.setReadOnly(True)
        self._safety_log.setStyleSheet(_SAFETY_LOG_STYLE)
        self._safety_log.setPlaceholderText("No violations")
        layout.addWidget(self._safety_log, stretch=1)

        # Bottom status row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self._guard_status = QLabel("Guard: ACTIVE")
        self._guard_status.setStyleSheet(_GUARD_ACTIVE_STYLE)
        bottom_row.addWidget(self._guard_status)

        self._last_check_label = QLabel("Last check: --")
        self._last_check_label.setStyleSheet(_DIM_LABEL_STYLE)
        bottom_row.addWidget(self._last_check_label)

        bottom_row.addStretch()

        self._rollback_btn = QPushButton("Rollback last")
        self._rollback_btn.setStyleSheet(_ROLLBACK_BTN_STYLE)
        self._rollback_btn.clicked.connect(self._on_rollback)
        self._rollback_btn.setEnabled(False)
        bottom_row.addWidget(self._rollback_btn)

        layout.addLayout(bottom_row)
        return frame

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_score_row(
        parent_layout: QVBoxLayout, label_text: str, initial: str
    ) -> QLabel:
        """Create a label + value row and return the value label."""
        row = QHBoxLayout()
        row.setSpacing(8)
        label = QLabel(label_text)
        label.setStyleSheet(_LABEL_STYLE)
        row.addWidget(label)

        value = QLabel(initial)
        value.setStyleSheet(_STAT_VALUE_STYLE)
        row.addWidget(value)
        row.addStretch()

        parent_layout.addLayout(row)
        return value

    def _add_card_to_layout(
        self,
        card: SkillCardWidget,
        target_layout: QVBoxLayout,
    ) -> None:
        """Insert a skill card before the trailing stretch."""
        # Insert before the stretch at the end
        idx = max(target_layout.count() - 1, 0)
        target_layout.insertWidget(idx, card)

    def _wire_card(self, card: SkillCardWidget) -> None:
        """Connect card signals to panel signals."""
        card.approve_clicked.connect(self._on_card_approved)
        card.reject_clicked.connect(self._on_card_rejected)

    # ------------------------------------------------------------------
    # Slot methods (called by app.py signal wiring)
    # ------------------------------------------------------------------

    def on_session_event(self, event: dict) -> None:
        """Handle incoming session events.

        ``event`` may contain a ``sessions`` key with the full list,
        or individual fields for incremental updates.
        """
        sessions = event.get("sessions", [])
        if sessions:
            self._session_timeline.update_sessions(sessions)

        # Update stats
        total_events = event.get("total_events", self._session_timeline.total_events)
        total_commits = event.get("total_commits", 0)
        active = self._session_timeline.active_count
        idle = len(self._session_timeline._sessions) - active

        self._total_events_label.setText(f"Events: {total_events}")
        self._total_commits_label.setText(f"Commits: {total_commits}")
        self._active_idle_label.setText(f"Active: {active} / Idle: {idle}")

    def on_skill_extracted(self, skill: dict) -> None:
        """Handle newly extracted skills -- add to pending queue."""
        skill_id = skill.get("skill_id", "")
        if not skill_id or skill_id in self._pending_cards:
            return

        skill.setdefault("status", "pending")
        card = SkillCardWidget(skill)
        self._wire_card(card)
        self._pending_cards[skill_id] = card
        self._add_card_to_layout(card, self._pending_layout)
        self._pending_count_badge.setText(str(len(self._pending_cards)))

    def on_skill_validated(self, report: dict) -> None:
        """Handle validation results -- update status display."""
        skill_id = report.get("skill_id", "")
        scores = report.get("scores", {})

        # Update validation status averages
        arch = scores.get("architecture", 0.0)
        sec = scores.get("security", 0.0)
        qual = scores.get("quality", 0.0)

        self._arch_score_label.setText(f"{arch:.2f}")
        self._sec_score_label.setText(f"{sec:.2f}")
        self._qual_score_label.setText(f"{qual:.2f}")

        # Update card validation scores if it exists
        card = self._pending_cards.get(skill_id)
        if card is not None:
            card.set_validation_scores(arch, sec, qual)

        # Update last check time
        self._last_check_label.setText(
            f"Last check: {datetime.now(timezone.utc).strftime('%H:%M:%S')}"
        )

        # If auto-approved, move card from pending to approved
        if report.get("auto_approved", False):
            self._move_to_approved(skill_id)
            count = int(self._auto_approved_label.text() or "0")
            self._auto_approved_label.setText(str(count + 1))
        elif report.get("needs_review", False):
            count = int(self._needs_review_label.text() or "0")
            self._needs_review_label.setText(str(count + 1))

    def on_skill_rejected(self, data: dict) -> None:
        """Handle rejected skills."""
        skill_id = data.get("skill_id", "")
        card = self._pending_cards.get(skill_id)
        if card is not None:
            card.update_status("rejected")
            self._remove_pending_card(skill_id)

            count = int(self._rejected_count_label.text() or "0")
            self._rejected_count_label.setText(str(count + 1))

    def on_safety_violation(self, alert: dict) -> None:
        """Handle safety violations -- show in safety log."""
        timestamp = alert.get(
            "timestamp",
            datetime.now(timezone.utc).strftime("%H:%M:%S"),
        )
        severity = alert.get("severity", "WARN")
        message = alert.get("message", "Unknown violation")

        self._safety_log.append(f"[{timestamp}] {severity}: {message}")

        # Auto-scroll to bottom
        cursor = self._safety_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._safety_log.setTextCursor(cursor)

        # Update guard status if critical
        if severity == "CRITICAL":
            self._guard_status.setText("Guard: ALERT")
            self._guard_status.setStyleSheet(
                f"color: {INTEL_REJECTED_COLOR}; font-size: 11px; "
                f"font-weight: bold; font-family: '{FONT_FAMILY}';"
            )

    def refresh_queue(self, pending: list[dict], approved: list[dict]) -> None:
        """Refresh the skill queue display with complete lists."""
        # Clear existing cards
        self._clear_card_list(self._pending_cards, self._pending_layout)
        self._clear_card_list(self._approved_cards, self._approved_layout)

        # Rebuild pending
        for skill in pending:
            skill_id = skill.get("skill_id", "")
            if not skill_id:
                continue
            skill.setdefault("status", "pending")
            card = SkillCardWidget(skill)
            self._wire_card(card)
            self._pending_cards[skill_id] = card
            self._add_card_to_layout(card, self._pending_layout)

        # Rebuild approved (no action buttons shown due to status)
        for skill in approved:
            skill_id = skill.get("skill_id", "")
            if not skill_id:
                continue
            skill["status"] = "approved"
            card = SkillCardWidget(skill)
            self._approved_cards[skill_id] = card
            self._add_card_to_layout(card, self._approved_layout)
            if skill_id:
                self._last_approved_id = skill_id

        self._pending_count_badge.setText(str(len(self._pending_cards)))
        self._approved_count_badge.setText(str(len(self._approved_cards)))
        self._rollback_btn.setEnabled(bool(self._last_approved_id))

    def update_agent_status(self, agent_infos: list[dict]) -> None:
        """Update agent status badges from a list of agent info dicts.

        Each dict should have 'name' (str) and 'status' (str) keys.
        """
        for info in agent_infos:
            name = info.get("name", "").lower()
            status = info.get("status", "stopped").lower()
            badge = self._agent_badges.get(name)
            if badge is None:
                continue

            display_name = name.capitalize()
            display_status = status.upper()
            badge.setText(f"{display_name}: {display_status}")

            color = _AGENT_STATUS_COLORS.get(status, "#8899AA")
            badge.setStyleSheet(
                f"color: {color}; background: {DARK_PANEL}; "
                f"font-size: 10px; font-weight: bold; "
                f"font-family: '{FONT_FAMILY}'; "
                f"border-radius: 3px; padding: 2px 8px; "
                f"border: 1px solid {TEAL};"
            )

    def update_refactor_progress(self, skill_name: str, score: float, iteration: int) -> None:
        """Update the UI with refactoring progress for a skill."""
        self._safety_log.append(
            f"[REFACTOR] {skill_name}: score={score:.2%} iter={iteration}"
        )
        cursor = self._safety_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._safety_log.setTextCursor(cursor)

    def update_improvement_trend(self, trend: dict) -> None:
        """Update the UI with improvement trend data.

        ``trend`` may contain 'skill_name', 'scores' (list[float]),
        and 'iterations' (int).
        """
        skill_name = trend.get("skill_name", "unknown")
        scores = trend.get("scores", [])
        iterations = trend.get("iterations", 0)
        if scores:
            latest = scores[-1]
            self._safety_log.append(
                f"[TREND] {skill_name}: {iterations} iters, latest={latest:.2%}"
            )
            cursor = self._safety_log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self._safety_log.setTextCursor(cursor)

    # ------------------------------------------------------------------
    # Internal actions
    # ------------------------------------------------------------------

    def _on_card_approved(self, skill_id: str) -> None:
        """Handle approval from a card's approve button."""
        self._move_to_approved(skill_id)
        self.skill_approve_requested.emit(skill_id)

    def _on_card_rejected(self, skill_id: str) -> None:
        """Handle rejection from a card's reject button."""
        card = self._pending_cards.get(skill_id)
        if card is not None:
            card.update_status("rejected")
            self._remove_pending_card(skill_id)
        self.skill_reject_requested.emit(skill_id)

    def _on_rollback(self) -> None:
        """Handle rollback button click."""
        if self._last_approved_id:
            self.rollback_requested.emit(self._last_approved_id)

    def _move_to_approved(self, skill_id: str) -> None:
        """Move a card from pending to approved list."""
        card = self._pending_cards.pop(skill_id, None)
        if card is None:
            return

        # Remove from pending layout
        self._pending_layout.removeWidget(card)
        card.update_status("approved")

        # Add to approved layout
        self._approved_cards[skill_id] = card
        self._add_card_to_layout(card, self._approved_layout)
        self._last_approved_id = skill_id

        self._pending_count_badge.setText(str(len(self._pending_cards)))
        self._approved_count_badge.setText(str(len(self._approved_cards)))
        self._rollback_btn.setEnabled(True)

    def _remove_pending_card(self, skill_id: str) -> None:
        """Remove a card from the pending list and clean up."""
        card = self._pending_cards.pop(skill_id, None)
        if card is not None:
            self._pending_layout.removeWidget(card)
            card.deleteLater()
        self._pending_count_badge.setText(str(len(self._pending_cards)))

    def _clear_card_list(
        self,
        card_dict: dict[str, SkillCardWidget],
        target_layout: QVBoxLayout,
    ) -> None:
        """Remove all cards from a layout and clear the tracking dict."""
        for card in card_dict.values():
            target_layout.removeWidget(card)
            card.deleteLater()
        card_dict.clear()
