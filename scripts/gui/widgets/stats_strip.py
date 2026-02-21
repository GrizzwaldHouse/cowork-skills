# stats_strip.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Compact metrics dashboard composing multiple widgets for quick system health overview

"""
Horizontal stats strip containing sparkline, donut, gauge, and flame widgets.

A 48px-tall bar inserted between the header and the main content splitter,
providing at-a-glance dashboard metrics.

Usage::

    strip = StatsStrip()
    strip.record_event(".py")
    strip.set_threat_score(25)
    strip.set_uptime_hours(3.5)
"""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from gui.constants import DARK_PANEL, FONT_FAMILY, GOLD, PARCHMENT, TEAL
from gui.widgets.donut_widget import DonutWidget
from gui.widgets.flame_widget import FlameWidget
from gui.widgets.gauge_widget import GaugeWidget
from gui.widgets.sparkline_widget import SparklineWidget

_STRIP_HEIGHT = 48

_LABEL_STYLE = (
    f"color: {PARCHMENT}; font-size: 9px; font-family: '{FONT_FAMILY}';"
)


class StatsStrip(QWidget):
    """Horizontal dashboard strip with 4 mini-widgets.

    Contains: Sparkline (event rate), Donut (file types),
    Gauge (threat score), Flame (uptime intensity).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(_STRIP_HEIGHT)
        self.setStyleSheet(f"background-color: {DARK_PANEL};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(16)

        # --- Sparkline ---
        spark_group = QHBoxLayout()
        spark_group.setSpacing(4)
        spark_label = QLabel("Events/min")
        spark_label.setStyleSheet(_LABEL_STYLE)
        self.sparkline = SparklineWidget()
        spark_group.addWidget(spark_label)
        spark_group.addWidget(self.sparkline)
        layout.addLayout(spark_group)

        # --- Donut ---
        donut_group = QHBoxLayout()
        donut_group.setSpacing(4)
        donut_label = QLabel("File types")
        donut_label.setStyleSheet(_LABEL_STYLE)
        self.donut = DonutWidget()
        donut_group.addWidget(donut_label)
        donut_group.addWidget(self.donut)
        layout.addLayout(donut_group)

        layout.addStretch()

        # --- Gauge ---
        gauge_group = QHBoxLayout()
        gauge_group.setSpacing(4)
        gauge_label = QLabel("Threat")
        gauge_label.setStyleSheet(_LABEL_STYLE)
        self.gauge = GaugeWidget()
        gauge_group.addWidget(gauge_label)
        gauge_group.addWidget(self.gauge)
        layout.addLayout(gauge_group)

        # --- Flame ---
        flame_group = QHBoxLayout()
        flame_group.setSpacing(4)
        flame_label = QLabel("Uptime")
        flame_label.setStyleSheet(_LABEL_STYLE)
        self.flame = FlameWidget()
        flame_group.addWidget(flame_label)
        flame_group.addWidget(self.flame)
        layout.addLayout(flame_group)

    # -- Convenience methods for app.py wiring ---

    def record_event(self, ext: str) -> None:
        """Record one file event (updates sparkline + donut)."""
        self.sparkline.record_event()
        if ext:
            self.donut.record_file_type(ext)

    def set_threat_score(self, score: int) -> None:
        """Update the threat gauge."""
        self.gauge.set_score(score)

    def set_uptime_hours(self, hours: float) -> None:
        """Update the uptime flame."""
        self.flame.set_uptime_hours(hours)
