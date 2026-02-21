# main_window.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Primary UI dashboard integrating owl mascot, event log, and security monitoring

"""
Main dashboard window for the OwlWatcher file security monitor.

Provides a themed PyQt6 QMainWindow with an owl mascot header, folder tree,
live event log, and status bar.  Communicates with the file watcher and
security engine via Qt signals.

Usage::

    from gui.main_window import MainWindow

    window = MainWindow()
    window.show()
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PyQt6.QtCore import (
    QModelIndex,
    QSettings,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QCloseEvent, QColor, QFileSystemModel, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from config_manager import load_config, watched_paths
from gui.constants import (
    DARK_PANEL,
    EVENT_MAX_ROWS,
    EVENT_TYPE_LABELS,
    FILE_TYPE_GLYPHS,
    FONT_FAMILY,
    GOLD,
    HEADER_BG,
    HEADER_HEIGHT,
    LEFT_BORDER_CRITICAL,
    LEFT_BORDER_INFO,
    LEFT_BORDER_WARNING,
    LEFT_BORDER_WIDTH,
    MID_PANEL,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MONO_FONT,
    NAVY,
    OWL_HEADER_SIZE,
    PARCHMENT,
    QSETTINGS_APP,
    QSETTINGS_ORG,
    PRESSED_BTN_COLOR,
    ROW_BG_CRITICAL,
    ROW_BG_INFO,
    ROW_BG_WARNING,
    ROW_HIGHLIGHT_COLOR,
    ROW_HIGHLIGHT_MS,
    STOP_BTN_COLOR,
    TEAL,
    THREAT_CRITICAL_MULTIPLIER,
    THREAT_WARNING_MULTIPLIER,
    TEXT_CRITICAL,
    TEXT_INFO,
    TEXT_WARNING,
    TIME_CLUSTER_GAP_SECONDS,
    UPTIME_TICK_MS,
)
from gui.paths import ASSETS_DIR, BASE_DIR
from gui.theme import ThemeManager
from gui.widgets.ambient_widget import AmbientBackgroundWidget
from gui.widgets.owl_widget import OwlWidget
from gui.widgets.stats_strip import StatsStrip

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TRAY_ICON_PATH = ASSETS_DIR / "owl_tray.svg"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("main_window")

# ---------------------------------------------------------------------------
# QSS Stylesheet
# ---------------------------------------------------------------------------
_STYLESHEET = f"""
QMainWindow {{
    background-color: {NAVY};
}}
QWidget#centralWidget {{
    background-color: {NAVY};
}}
QSplitter::handle {{
    background-color: {TEAL};
    width: 3px;
}}
QTreeView {{
    background-color: {DARK_PANEL};
    color: {PARCHMENT};
    border: 1px solid {TEAL};
    font-family: '{FONT_FAMILY}';
    font-size: 12px;
    selection-background-color: {TEAL};
    selection-color: {GOLD};
}}
QTreeView::item:hover {{
    background-color: {MID_PANEL};
}}
QHeaderView::section {{
    background-color: {HEADER_BG};
    color: {GOLD};
    border: 1px solid {TEAL};
    padding: 4px 8px;
    font-family: '{FONT_FAMILY}';
    font-size: 11px;
    font-weight: bold;
}}
QTableWidget {{
    background-color: {DARK_PANEL};
    color: {PARCHMENT};
    border: 1px solid {TEAL};
    gridline-color: {TEAL};
    font-family: {MONO_FONT};
    font-size: 11px;
    selection-background-color: {TEAL};
    selection-color: {GOLD};
}}
QTableWidget::item {{
    padding: 2px 6px;
}}
QPushButton {{
    background-color: {TEAL};
    color: {PARCHMENT};
    border: 1px solid {GOLD};
    border-radius: 4px;
    padding: 6px 16px;
    font-family: '{FONT_FAMILY}';
    font-size: 12px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {GOLD};
    color: {NAVY};
}}
QPushButton:pressed {{
    background-color: {PRESSED_BTN_COLOR};
    color: {NAVY};
}}
QPushButton#stopBtn {{
    border-color: {STOP_BTN_COLOR};
}}
QPushButton#stopBtn:hover {{
    background-color: {STOP_BTN_COLOR};
    color: white;
}}
QLineEdit {{
    background-color: {MID_PANEL};
    color: {PARCHMENT};
    border: 1px solid {TEAL};
    border-radius: 3px;
    padding: 4px 8px;
    font-family: '{FONT_FAMILY}';
    font-size: 11px;
}}
QLineEdit:focus {{
    border-color: {GOLD};
}}
QComboBox {{
    background-color: {MID_PANEL};
    color: {PARCHMENT};
    border: 1px solid {TEAL};
    border-radius: 3px;
    padding: 4px 8px;
    font-family: '{FONT_FAMILY}';
    font-size: 11px;
}}
QComboBox:hover {{
    border-color: {GOLD};
}}
QComboBox QAbstractItemView {{
    background-color: {DARK_PANEL};
    color: {PARCHMENT};
    selection-background-color: {TEAL};
    selection-color: {GOLD};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QStatusBar {{
    background-color: {HEADER_BG};
    color: {PARCHMENT};
    font-family: '{FONT_FAMILY}';
    font-size: 11px;
    border-top: 1px solid {TEAL};
}}
QLabel {{
    color: {PARCHMENT};
    font-family: '{FONT_FAMILY}';
}}
QMenu {{
    background-color: {DARK_PANEL};
    color: {PARCHMENT};
    border: 1px solid {TEAL};
}}
QMenu::item:selected {{
    background-color: {TEAL};
    color: {GOLD};
}}
QScrollBar:vertical {{
    background: {DARK_PANEL};
    width: 10px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {TEAL};
    min-height: 30px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {GOLD};
}}
QScrollBar:horizontal {{
    background: {DARK_PANEL};
    height: 10px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {TEAL};
    min-width: 30px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {GOLD};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0px;
    width: 0px;
}}
QToolTip {{
    background-color: {HEADER_BG};
    color: {PARCHMENT};
    border: 1px solid {GOLD};
    padding: 4px;
    font-family: '{FONT_FAMILY}';
}}
"""

# ---------------------------------------------------------------------------
# Row colours for security levels (QColor from constants)
# ---------------------------------------------------------------------------
_ROW_COLORS: dict[str, QColor] = {
    "INFO": QColor(ROW_BG_INFO),
    "WARNING": QColor(ROW_BG_WARNING),
    "CRITICAL": QColor(ROW_BG_CRITICAL),
}

_LEVEL_TEXT_COLORS: dict[str, QColor] = {
    "INFO": QColor(TEXT_INFO),
    "WARNING": QColor(TEXT_WARNING),
    "CRITICAL": QColor(TEXT_CRITICAL),
}

_LEFT_BORDER_COLORS: dict[str, str] = {
    "INFO": LEFT_BORDER_INFO,
    "WARNING": LEFT_BORDER_WARNING,
    "CRITICAL": LEFT_BORDER_CRITICAL,
}

_HIGHLIGHT_BG = QColor(ROW_HIGHLIGHT_COLOR)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """OwlWatcher main dashboard window.

    Signals
    -------
    file_event_received(dict):
        Emitted when a file-system event is received from the watcher thread.
    security_alert_received(dict):
        Emitted when the security engine raises an alert.
    watch_started():
        Emitted when the file watcher begins monitoring.
    watch_stopped():
        Emitted when the file watcher stops monitoring.
    """

    file_event_received = pyqtSignal(dict)
    security_alert_received = pyqtSignal(dict)
    watch_started = pyqtSignal()
    watch_stopped = pyqtSignal()
    sound_toggled = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._is_watching = False
        self._event_count = 0
        self._alert_count = 0
        self._start_time: datetime | None = None
        self._last_event_dt: datetime | None = None
        self._minimize_to_tray_asked = False
        self._minimize_to_tray = True

        self._settings = QSettings(QSETTINGS_ORG, QSETTINGS_APP)
        self._theme_manager = ThemeManager()

        self.setWindowTitle("OwlWatcher - File Security Monitor")
        self.setWindowIcon(QIcon(str(ASSETS_DIR / "owl_tray.svg")))
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.setStyleSheet(_STYLESHEET)

        self._build_ui()
        self._connect_signals()
        self._restore_state()

        # Uptime timer (updates status bar every second)
        self._uptime_timer = QTimer(self)
        self._uptime_timer.setInterval(UPTIME_TICK_MS)
        self._uptime_timer.timeout.connect(self._update_status_bar)

    # =====================================================================
    # UI construction
    # =====================================================================

    def _build_ui(self) -> None:
        """Construct all child widgets and lay them out."""
        # Menu bar
        self._build_menu_bar()

        central = QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Header bar ---
        root_layout.addWidget(self._build_header())

        # --- Stats strip ---
        self._stats_strip = StatsStrip()
        root_layout.addWidget(self._stats_strip)

        # --- Main area (splitter) ---
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(self._build_folder_tree())
        self._splitter.addWidget(self._build_event_log_panel())
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 3)
        root_layout.addWidget(self._splitter, stretch=1)

        # --- Status bar ---
        self._build_status_bar()

        # --- System tray ---
        self._build_system_tray()

    # -- Menu Bar ---------------------------------------------------------

    def _build_menu_bar(self) -> None:
        """Build the application menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._on_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("&About OwlWatcher", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _on_settings(self) -> None:
        """Show the Settings dialog."""
        from gui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self)
        if dialog.exec():
            new_config = dialog.get_config()
            # Save config to watch_config.json
            from pathlib import Path
            import json
            config_path = Path("C:/ClaudeSkills/config/watch_config.json")
            with config_path.open("w", encoding="utf-8") as fh:
                json.dump(new_config, fh, indent=2)
            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved. Restart OwlWatcher for changes to take effect.",
            )

    def _on_about(self) -> None:
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About OwlWatcher",
            "<h3>OwlWatcher File Security Monitor</h3>"
            "<p>Version 1.0</p>"
            "<p>Developer: Marcus Daley</p>"
            "<p>A themed file security monitor with real-time threat detection.</p>",
        )

    # -- Header -----------------------------------------------------------

    def _build_header(self) -> QWidget:
        """Build the header bar with ambient night-sky background."""
        self._header = AmbientBackgroundWidget()
        self._header.setFixedHeight(HEADER_HEIGHT)
        self._header.theme_toggle_requested.connect(self._on_theme_toggle)

        layout = QHBoxLayout(self._header)
        layout.setContentsMargins(12, 4, 12, 4)

        # Owl widget (small version in header)
        self._owl = OwlWidget(owl_size=OWL_HEADER_SIZE)
        layout.addWidget(self._owl)

        # Title
        title = QLabel("OwlWatcher")
        title.setStyleSheet(
            f"color: {GOLD}; font-size: 22px; font-weight: bold; "
            f"font-family: '{FONT_FAMILY}';"
        )
        layout.addWidget(title)

        subtitle = QLabel("File Security Monitor")
        subtitle.setStyleSheet(
            f"color: {PARCHMENT}; font-size: 12px; font-family: '{FONT_FAMILY}';"
        )
        layout.addWidget(subtitle)

        layout.addStretch()

        # Start / Stop button
        self._start_btn = QPushButton("Start Watching")
        self._start_btn.setFixedWidth(140)
        layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("stopBtn")
        self._stop_btn.setFixedWidth(80)
        self._stop_btn.setEnabled(False)
        layout.addWidget(self._stop_btn)

        # Export button
        self._export_btn = QPushButton("Export Audit")
        self._export_btn.setFixedWidth(120)
        layout.addWidget(self._export_btn)

        # Sound toggle
        self._sound_check = QCheckBox("Sound")
        self._sound_check.setStyleSheet(
            f"color: {PARCHMENT}; font-size: 10px; font-family: '{FONT_FAMILY}';"
        )
        self._sound_check.setChecked(
            self._settings.value("soundEnabled", False, type=bool),
        )
        self._sound_check.toggled.connect(self.sound_toggled.emit)
        layout.addWidget(self._sound_check)

        return self._header

    def _on_theme_toggle(self) -> None:
        """Handle theme toggle request from moon button."""
        new_theme = self._theme_manager.toggle_theme()
        theme_name = "Light" if new_theme.value == "light" else "Dark"
        self.statusBar().showMessage(f"Switched to {theme_name} theme", 2000)

    # -- Folder tree ------------------------------------------------------

    def _build_folder_tree(self) -> QWidget:
        """Build the folder tree panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 2, 4)
        layout.setSpacing(4)

        panel_label = QLabel("Watched Folders")
        panel_label.setStyleSheet(
            f"color: {GOLD}; font-size: 12px; font-weight: bold; padding: 4px;"
        )
        layout.addWidget(panel_label)

        self._fs_model = QFileSystemModel()
        self._fs_model.setReadOnly(True)

        self._tree_view = QTreeView()
        self._tree_view.setModel(self._fs_model)
        self._tree_view.setAnimated(True)
        self._tree_view.setIndentation(16)
        self._tree_view.setSortingEnabled(True)
        self._tree_view.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu,
        )
        self._tree_view.customContextMenuRequested.connect(
            self._on_tree_context_menu,
        )

        # Hide Size, Type, Date Modified columns -- show only Name
        self._tree_view.setColumnHidden(1, True)
        self._tree_view.setColumnHidden(2, True)
        self._tree_view.setColumnHidden(3, True)

        # Load watched paths from config
        self._watched_paths = self._load_watched_paths()
        if self._watched_paths:
            first_path = self._watched_paths[0]
            root_index = self._fs_model.setRootPath(first_path)
            self._tree_view.setRootIndex(root_index)

        layout.addWidget(self._tree_view, stretch=1)
        return panel

    # -- Event log --------------------------------------------------------

    def _build_event_log_panel(self) -> QWidget:
        """Build the live event log panel with filter bar."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 4, 4, 4)
        layout.setSpacing(4)

        # Filter bar
        filter_bar = QHBoxLayout()

        filter_label = QLabel("Events")
        filter_label.setStyleSheet(
            f"color: {GOLD}; font-size: 12px; font-weight: bold; padding: 4px;"
        )
        filter_bar.addWidget(filter_label)

        filter_bar.addStretch()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search events...")
        self._search_input.setFixedWidth(200)
        filter_bar.addWidget(self._search_input)

        self._level_filter = QComboBox()
        self._level_filter.addItems(["All Levels", "INFO", "WARNING", "CRITICAL"])
        self._level_filter.setFixedWidth(110)
        filter_bar.addWidget(self._level_filter)

        self._type_filter = QComboBox()
        self._type_filter.addItems(
            ["All Types", "created", "modified", "deleted", "moved"],
        )
        self._type_filter.setFixedWidth(110)
        filter_bar.addWidget(self._type_filter)

        layout.addLayout(filter_bar)

        # Event table (6 columns: severity border, time, type, path, details, level)
        self._event_table = QTableWidget(0, 6)
        self._event_table.setHorizontalHeaderLabels(
            ["", "Time", "Type", "Path", "Details", "Level"],
        )
        self._event_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows,
        )
        self._event_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers,
        )
        self._event_table.verticalHeader().setVisible(False)

        header = self._event_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, LEFT_BORDER_WIDTH)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._event_table, stretch=1)
        return panel

    # -- Status bar -------------------------------------------------------

    def _build_status_bar(self) -> None:
        """Build the status bar with watch status, event count, and uptime."""
        status = QStatusBar()
        self.setStatusBar(status)

        self._status_watch_label = QLabel("Stopped")
        self._status_events_label = QLabel("0 events")
        self._status_alerts_label = QLabel("0 alerts")
        self._status_uptime_label = QLabel("")

        status.addWidget(self._status_watch_label, stretch=1)
        status.addPermanentWidget(self._status_events_label)
        status.addPermanentWidget(self._status_alerts_label)
        status.addPermanentWidget(self._status_uptime_label)

    # -- System tray ------------------------------------------------------

    def _build_system_tray(self) -> None:
        """Build the system tray icon and its context menu."""
        self._tray_icon = QSystemTrayIcon(self)

        if TRAY_ICON_PATH.exists():
            self._tray_icon.setIcon(QIcon(str(TRAY_ICON_PATH)))
        else:
            app = QApplication.instance()
            if app is not None:
                self._tray_icon.setIcon(app.windowIcon())

        self._tray_icon.setToolTip("OwlWatcher - File Security Monitor")
        self._tray_icon.activated.connect(self._on_tray_activated)

        tray_menu = QMenu()
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.show()

    # =====================================================================
    # Signal connections
    # =====================================================================

    def _connect_signals(self) -> None:
        """Wire up all signals and slots."""
        self._start_btn.clicked.connect(self._on_start_watching)
        self._stop_btn.clicked.connect(self._on_stop_watching)
        self._export_btn.clicked.connect(self._on_export_audit)

        self.file_event_received.connect(self._on_file_event)
        self.security_alert_received.connect(self._on_security_alert)
        self.watch_started.connect(self._on_watch_started)
        self.watch_stopped.connect(self._on_watch_stopped)

        self._search_input.textChanged.connect(self._apply_filters)
        self._level_filter.currentTextChanged.connect(self._apply_filters)
        self._type_filter.currentTextChanged.connect(self._apply_filters)

    # =====================================================================
    # Slot handlers
    # =====================================================================

    def _on_start_watching(self) -> None:
        """Handle Start Watching button click."""
        self.watch_started.emit()

    def _on_stop_watching(self) -> None:
        """Handle Stop button click."""
        self.watch_stopped.emit()

    def _on_watch_started(self) -> None:
        """Update UI when the watcher starts."""
        self._is_watching = True
        self._start_time = datetime.now(timezone.utc)
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_watch_label.setText(
            f"Watching {len(self._watched_paths)} dir(s)",
        )
        # Owl state is now managed by OwlStateMachine in app.py
        self._uptime_timer.start()

    def _on_watch_stopped(self) -> None:
        """Update UI when the watcher stops."""
        self._is_watching = False
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_watch_label.setText("Stopped")
        # Owl state is now managed by OwlStateMachine in app.py
        self._uptime_timer.stop()

    def _on_file_event(self, event: dict[str, Any]) -> None:
        """Handle a file-system event from the watcher thread.

        Parameters
        ----------
        event:
            Dictionary with keys: ``timestamp``, ``event_type``, ``path``,
            and optionally ``details``, ``level``.
        """
        self._event_count += 1
        self._add_event_row(event)
        self._status_events_label.setText(f"{self._event_count} events")

        # Feed stats strip
        file_path = event.get("path", "")
        ext = Path(file_path).suffix.lower() if file_path else ""
        self._stats_strip.record_event(ext)

    def _on_security_alert(self, alert: dict[str, Any]) -> None:
        """Handle a security alert from the security engine.

        Parameters
        ----------
        alert:
            Dictionary with keys from :class:`SecurityAlert.to_dict`.
        """
        self._alert_count += 1
        self._status_alerts_label.setText(f"{self._alert_count} alerts")
        self._status_alerts_label.setStyleSheet(f"color: {TEXT_CRITICAL};")

        level = alert.get("level", "WARNING")
        message = alert.get("message", "Unknown alert")

        # Convert alert to event-log row format
        event_row: dict[str, Any] = {
            "timestamp": alert.get("timestamp", ""),
            "event_type": "alert",
            "path": alert.get("file_path", ""),
            "details": message,
            "level": level,
        }
        self._add_event_row(event_row)

        # Feed threat score to stats strip (weighted by severity for visual urgency)
        threat_score = min(100, self._alert_count * THREAT_CRITICAL_MULTIPLIER if level == "CRITICAL" else self._alert_count * THREAT_WARNING_MULTIPLIER)
        self._stats_strip.set_threat_score(threat_score)

        # Owl state transitions are handled by OwlStateMachine in app.py.
        # Notify via tray when window is hidden.
        if level == "CRITICAL" and not self.isVisible() and self._tray_icon.isVisible():
            self._tray_icon.showMessage(
                "OwlWatcher Security Alert",
                message,
                QSystemTrayIcon.MessageIcon.Critical,
                5000,
            )

    def _on_export_audit(self) -> None:
        """Handle Export Audit button click."""
        try:
            from gui.security_engine import SecurityEngine

            engine = SecurityEngine()
            output = BASE_DIR / "security" / "audit_report.md"
            engine.export_report(output)
            self._owl.say(f"Report saved to {output.name}", 4000)
            logger.info("Audit report exported to %s", output)
        except Exception as exc:
            logger.error("Failed to export audit report: %s", exc)
            self._owl.say("Export failed. Check logs.", 4000)

    # =====================================================================
    # Event log management
    # =====================================================================

    def _add_event_row(self, event: dict[str, Any]) -> None:
        """Add one row to the event table.

        Includes: severity left-border, file type glyphs, time cluster
        separators, and brief highlight animation on insert.
        Caps the table at ``EVENT_MAX_ROWS`` rows by removing the oldest.
        """
        table = self._event_table
        row_count = table.rowCount()

        # Cap at max rows
        if row_count >= EVENT_MAX_ROWS:
            table.removeRow(0)
            row_count -= 1

        # Parse timestamp
        timestamp = event.get("timestamp", "")
        event_dt: datetime | None = None
        if timestamp:
            try:
                event_dt = datetime.fromisoformat(timestamp)
                time_str = event_dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                time_str = str(timestamp)
        else:
            event_dt = datetime.now(timezone.utc)
            time_str = event_dt.strftime("%H:%M:%S")

        # --- 3C: Time cluster separator ---
        if self._last_event_dt is not None and event_dt is not None:
            gap = (event_dt - self._last_event_dt).total_seconds()
            if gap > TIME_CLUSTER_GAP_SECONDS:
                self._insert_time_separator(table, gap)
        self._last_event_dt = event_dt

        # Parse fields
        event_type = event.get("event_type", "")
        file_path = event.get("path", "")
        details = event.get("details", "")
        level = event.get("level", "INFO")

        # --- 3D: File type glyph ---
        ext = Path(file_path).suffix.lower() if file_path else ""
        glyph = FILE_TYPE_GLYPHS.get(ext, "")
        type_label = EVENT_TYPE_LABELS.get(event_type, f"[{event_type.upper()}]")
        if glyph:
            type_label = f"{glyph} {type_label}"

        row = table.rowCount()
        table.insertRow(row)

        # --- 3B: Color-coded left border (column 0) ---
        border_item = QTableWidgetItem("")
        border_color = QColor(_LEFT_BORDER_COLORS.get(level, LEFT_BORDER_INFO))
        border_item.setBackground(border_color)
        table.setItem(row, 0, border_item)

        # Content columns (1-5)
        items = [
            QTableWidgetItem(time_str),
            QTableWidgetItem(type_label),
            QTableWidgetItem(file_path),
            QTableWidgetItem(str(details)),
            QTableWidgetItem(level),
        ]

        # Row text color per severity
        fg = _LEVEL_TEXT_COLORS.get(level, _LEVEL_TEXT_COLORS["INFO"])
        # Use dark background for all rows (border provides severity color)
        bg = QColor(DARK_PANEL)

        for col, item in enumerate(items, start=1):
            item.setBackground(bg)
            item.setForeground(fg)
            table.setItem(row, col, item)

        # Store raw event data for filtering
        items[0].setData(Qt.ItemDataRole.UserRole, event)

        # --- 3A: Animated row highlight ---
        self._highlight_row(table, row)

        # Auto-scroll to bottom
        table.scrollToBottom()

    def _insert_time_separator(self, table: QTableWidget, gap: float) -> None:
        """Insert a thin gold separator row indicating a time gap."""
        row = table.rowCount()
        table.insertRow(row)
        table.setRowHeight(row, 16)

        gap_text = f"-- {int(gap)}s gap --"
        sep_bg = QColor(GOLD)
        sep_fg = QColor(NAVY)

        for col in range(table.columnCount()):
            item = QTableWidgetItem(gap_text if col == 3 else "")
            item.setBackground(sep_bg)
            item.setForeground(sep_fg)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, col, item)

    def _highlight_row(self, table: QTableWidget, row: int) -> None:
        """Briefly highlight a new row then fade to normal background."""
        # Apply highlight color to content columns
        highlight = _HIGHLIGHT_BG
        for col in range(1, table.columnCount()):
            item = table.item(row, col)
            if item is not None:
                item.setBackground(highlight)

        # Schedule fade back to normal after ROW_HIGHLIGHT_MS
        def _fade_back() -> None:
            normal_bg = QColor(DARK_PANEL)
            for c in range(1, table.columnCount()):
                it = table.item(row, c)
                if it is not None:
                    it.setBackground(normal_bg)

        QTimer.singleShot(ROW_HIGHLIGHT_MS, _fade_back)

    def _apply_filters(self) -> None:
        """Show/hide event log rows based on current filter settings."""
        search_text = self._search_input.text().lower()
        level_filter = self._level_filter.currentText()
        type_filter = self._type_filter.currentText()

        for row in range(self._event_table.rowCount()):
            # Time item is in column 1 (column 0 is the severity border)
            time_item = self._event_table.item(row, 1)
            if time_item is None:
                continue

            event_data = time_item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(event_data, dict):
                self._event_table.setRowHidden(row, False)
                continue

            visible = True

            # Level filter
            if level_filter != "All Levels":
                if event_data.get("level", "INFO") != level_filter:
                    visible = False

            # Type filter
            if type_filter != "All Types":
                if event_data.get("event_type", "") != type_filter:
                    visible = False

            # Text search
            if search_text and visible:
                path = event_data.get("path", "").lower()
                details = str(event_data.get("details", "")).lower()
                if search_text not in path and search_text not in details:
                    visible = False

            self._event_table.setRowHidden(row, not visible)

    # =====================================================================
    # Context menu for folder tree
    # =====================================================================

    def _on_tree_context_menu(self, position: Any) -> None:
        """Show context menu for the folder tree."""
        index: QModelIndex = self._tree_view.indexAt(position)
        if not index.isValid():
            return

        file_path = self._fs_model.filePath(index)
        menu = QMenu(self)

        baseline_action = QAction("Baseline this folder", self)
        baseline_action.triggered.connect(
            lambda: self._baseline_folder(file_path),
        )
        menu.addAction(baseline_action)

        hash_action = QAction("View file hash", self)
        hash_action.triggered.connect(
            lambda: self._view_file_hash(file_path),
        )
        menu.addAction(hash_action)

        menu.exec(self._tree_view.viewport().mapToGlobal(position))

    def _baseline_folder(self, folder_path: str) -> None:
        """Baseline a folder using the security engine."""
        try:
            from gui.security_engine import SecurityEngine

            engine = SecurityEngine()
            count = engine.baseline_directory(folder_path)
            self._owl.say(f"Baselined {count} files.", 4000)
            logger.info("Baselined %d files in %s", count, folder_path)
        except Exception as exc:
            logger.error("Baseline failed: %s", exc)
            self._owl.say("Baseline failed.", 3000)

    def _view_file_hash(self, file_path: str) -> None:
        """Compute and display the SHA-256 hash of a file."""
        import hashlib

        path = Path(file_path)
        if not path.is_file():
            self._owl.say("Select a file, not a folder.", 3000)
            return

        try:
            h = hashlib.sha256()
            with path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    h.update(chunk)
            digest = h.hexdigest()
            QMessageBox.information(
                self,
                "File Hash",
                f"SHA-256 for:\n{path.name}\n\n{digest}",
            )
        except OSError as exc:
            logger.error("Cannot hash %s: %s", path, exc)
            self._owl.say("Cannot read file.", 3000)

    # =====================================================================
    # Status bar updates
    # =====================================================================

    def _update_status_bar(self) -> None:
        """Update the uptime display in the status bar and flame widget."""
        if self._start_time is None:
            return
        elapsed = datetime.now(timezone.utc) - self._start_time
        total_seconds = elapsed.total_seconds()
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        self._status_uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")

        # Feed uptime to flame widget
        self._stats_strip.set_uptime_hours(total_seconds / 3600.0)

    # =====================================================================
    # Config helpers
    # =====================================================================

    def _load_watched_paths(self) -> list[str]:
        """Load the list of watched directories from watch_config.json."""
        return watched_paths()

    # =====================================================================
    # Window state persistence
    # =====================================================================

    def _save_state(self) -> None:
        """Save window geometry and splitter state to QSettings."""
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        self._settings.setValue("splitterState", self._splitter.saveState())

    def _restore_state(self) -> None:
        """Restore window geometry and splitter state from QSettings."""
        geometry = self._settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        state = self._settings.value("windowState")
        if state is not None:
            self.restoreState(state)

        splitter_state = self._settings.value("splitterState")
        if splitter_state is not None:
            self._splitter.restoreState(splitter_state)

    # =====================================================================
    # System tray handlers
    # =====================================================================

    def _on_tray_activated(
        self, reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        """Handle tray icon activation (double-click to restore)."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        """Restore the window from the system tray."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_app(self) -> None:
        """Fully quit the application from the tray context menu."""
        self._save_state()
        self._tray_icon.hide()
        QApplication.quit()

    # =====================================================================
    # Close / minimize to tray
    # =====================================================================

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Intercept close to offer minimize-to-tray option."""
        self._save_state()

        if not self._minimize_to_tray_asked:
            reply = QMessageBox.question(
                self,
                "Minimize to Tray?",
                "OwlWatcher will continue running in the system tray.\n"
                "Use the tray icon to restore or quit.\n\n"
                "Minimize to tray?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            self._minimize_to_tray_asked = True
            self._minimize_to_tray = reply == QMessageBox.StandardButton.Yes
            self._settings.setValue("minimizeToTray", self._minimize_to_tray)

        if self._minimize_to_tray:
            event.ignore()
            self.hide()
            if self._tray_icon.isVisible():
                self._tray_icon.showMessage(
                    "OwlWatcher",
                    "Still running in the system tray.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
        else:
            self._tray_icon.hide()
            event.accept()

    def force_close(self) -> None:
        """Close the window without the minimize-to-tray prompt."""
        self._save_state()
        self._minimize_to_tray = False
        self._tray_icon.hide()
        self.close()


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
def _test() -> None:
    """Quick visual test of the main window."""
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # Simulate some events
    QTimer.singleShot(1000, lambda: window.watch_started.emit())

    sample_events = [
        {
            "timestamp": "2026-02-18T12:01:03+00:00",
            "event_type": "modified",
            "path": "C:/ClaudeSkills/Example_Skills/game-dev/SKILL.md",
            "details": "",
            "level": "INFO",
        },
        {
            "timestamp": "2026-02-18T12:01:05+00:00",
            "event_type": "created",
            "path": "C:/ClaudeSkills/scripts/test.py",
            "details": "",
            "level": "INFO",
        },
        {
            "timestamp": "2026-02-18T12:01:08+00:00",
            "event_type": "created",
            "path": "C:/ClaudeSkills/scripts/malware.exe",
            "details": "Suspicious file type detected: .exe",
            "level": "CRITICAL",
        },
        {
            "timestamp": "2026-02-18T12:01:10+00:00",
            "event_type": "modified",
            "path": "C:/ClaudeSkills/config/watch_config.json",
            "details": "Rapid burst of changes",
            "level": "WARNING",
        },
    ]

    for i, evt in enumerate(sample_events):
        QTimer.singleShot(
            1500 + i * 800,
            lambda e=evt: window.file_event_received.emit(e),
        )

    # Simulate a security alert
    QTimer.singleShot(
        5000,
        lambda: window.security_alert_received.emit({
            "level": "CRITICAL",
            "message": "Suspicious file type detected: .exe",
            "file_path": "C:/ClaudeSkills/scripts/malware.exe",
            "timestamp": "2026-02-18T12:01:08+00:00",
        }),
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    _test()
