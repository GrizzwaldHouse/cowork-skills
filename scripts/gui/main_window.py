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

import json
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

from gui.paths import ASSETS_DIR, BASE_DIR, CONFIG_PATH
from gui.widgets.owl_widget import OwlWidget

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TRAY_ICON_PATH = ASSETS_DIR / "owl_tray.svg"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("main_window")

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
_NAVY = "#1B2838"
_GOLD = "#C9A94E"
_PARCHMENT = "#F5E6C8"
_TEAL = "#1A3C40"
_DARK_PANEL = "#0D1117"
_MID_PANEL = "#162230"
_HEADER_BG = "#142030"

_EVENT_MAX_ROWS = 1000

# ---------------------------------------------------------------------------
# QSS Stylesheet
# ---------------------------------------------------------------------------
_STYLESHEET = f"""
QMainWindow {{
    background-color: {_NAVY};
}}
QWidget#centralWidget {{
    background-color: {_NAVY};
}}
QSplitter::handle {{
    background-color: {_TEAL};
    width: 3px;
}}
QTreeView {{
    background-color: {_DARK_PANEL};
    color: {_PARCHMENT};
    border: 1px solid {_TEAL};
    font-family: 'Segoe UI';
    font-size: 12px;
    selection-background-color: {_TEAL};
    selection-color: {_GOLD};
}}
QTreeView::item:hover {{
    background-color: {_MID_PANEL};
}}
QHeaderView::section {{
    background-color: {_HEADER_BG};
    color: {_GOLD};
    border: 1px solid {_TEAL};
    padding: 4px 8px;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: bold;
}}
QTableWidget {{
    background-color: {_DARK_PANEL};
    color: {_PARCHMENT};
    border: 1px solid {_TEAL};
    gridline-color: {_TEAL};
    font-family: 'Consolas', 'Cascadia Code', monospace;
    font-size: 11px;
    selection-background-color: {_TEAL};
    selection-color: {_GOLD};
}}
QTableWidget::item {{
    padding: 2px 6px;
}}
QPushButton {{
    background-color: {_TEAL};
    color: {_PARCHMENT};
    border: 1px solid {_GOLD};
    border-radius: 4px;
    padding: 6px 16px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {_GOLD};
    color: {_NAVY};
}}
QPushButton:pressed {{
    background-color: #A8892F;
    color: {_NAVY};
}}
QPushButton#stopBtn {{
    border-color: #E74C3C;
}}
QPushButton#stopBtn:hover {{
    background-color: #E74C3C;
    color: white;
}}
QLineEdit {{
    background-color: {_MID_PANEL};
    color: {_PARCHMENT};
    border: 1px solid {_TEAL};
    border-radius: 3px;
    padding: 4px 8px;
    font-family: 'Segoe UI';
    font-size: 11px;
}}
QLineEdit:focus {{
    border-color: {_GOLD};
}}
QComboBox {{
    background-color: {_MID_PANEL};
    color: {_PARCHMENT};
    border: 1px solid {_TEAL};
    border-radius: 3px;
    padding: 4px 8px;
    font-family: 'Segoe UI';
    font-size: 11px;
}}
QComboBox:hover {{
    border-color: {_GOLD};
}}
QComboBox QAbstractItemView {{
    background-color: {_DARK_PANEL};
    color: {_PARCHMENT};
    selection-background-color: {_TEAL};
    selection-color: {_GOLD};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QStatusBar {{
    background-color: {_HEADER_BG};
    color: {_PARCHMENT};
    font-family: 'Segoe UI';
    font-size: 11px;
    border-top: 1px solid {_TEAL};
}}
QLabel {{
    color: {_PARCHMENT};
    font-family: 'Segoe UI';
}}
QMenu {{
    background-color: {_DARK_PANEL};
    color: {_PARCHMENT};
    border: 1px solid {_TEAL};
}}
QMenu::item:selected {{
    background-color: {_TEAL};
    color: {_GOLD};
}}
QScrollBar:vertical {{
    background: {_DARK_PANEL};
    width: 10px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {_TEAL};
    min-height: 30px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {_GOLD};
}}
QScrollBar:horizontal {{
    background: {_DARK_PANEL};
    height: 10px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {_TEAL};
    min-width: 30px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {_GOLD};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0px;
    width: 0px;
}}
QToolTip {{
    background-color: {_HEADER_BG};
    color: {_PARCHMENT};
    border: 1px solid {_GOLD};
    padding: 4px;
    font-family: 'Segoe UI';
}}
"""

# ---------------------------------------------------------------------------
# Row colours for security levels
# ---------------------------------------------------------------------------
_ROW_COLORS: dict[str, QColor] = {
    "INFO": QColor(_DARK_PANEL),
    "WARNING": QColor("#332D00"),
    "CRITICAL": QColor("#3D1010"),
}

_LEVEL_TEXT_COLORS: dict[str, QColor] = {
    "INFO": QColor(_PARCHMENT),
    "WARNING": QColor("#FFD54F"),
    "CRITICAL": QColor("#FF6B6B"),
}

# ---------------------------------------------------------------------------
# Event type icons (text-based for simplicity)
# ---------------------------------------------------------------------------
_EVENT_TYPE_LABELS: dict[str, str] = {
    "created": "[NEW]",
    "modified": "[MOD]",
    "deleted": "[DEL]",
    "moved": "[MOV]",
}


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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._is_watching = False
        self._event_count = 0
        self._alert_count = 0
        self._start_time: datetime | None = None
        self._minimize_to_tray_asked = False
        self._minimize_to_tray = True

        self._settings = QSettings("ClaudeSkills", "OwlWatcher")

        self.setWindowTitle("OwlWatcher - File Security Monitor")
        self.setMinimumSize(900, 600)

        self.setStyleSheet(_STYLESHEET)

        self._build_ui()
        self._connect_signals()
        self._restore_state()

        # Uptime timer (updates status bar every second)
        self._uptime_timer = QTimer(self)
        self._uptime_timer.setInterval(1000)
        self._uptime_timer.timeout.connect(self._update_status_bar)

    # =====================================================================
    # UI construction
    # =====================================================================

    def _build_ui(self) -> None:
        """Construct all child widgets and lay them out."""
        central = QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Header bar ---
        root_layout.addWidget(self._build_header())

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

    # -- Header -----------------------------------------------------------

    def _build_header(self) -> QWidget:
        """Build the header bar with owl, title, and control buttons."""
        header = QWidget()
        header.setStyleSheet(f"background-color: {_HEADER_BG};")
        header.setFixedHeight(80)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 4, 12, 4)

        # Owl widget (small version in header)
        self._owl = OwlWidget(owl_size=56)
        layout.addWidget(self._owl)

        # Title
        title = QLabel("OwlWatcher")
        title.setStyleSheet(
            f"color: {_GOLD}; font-size: 22px; font-weight: bold; "
            f"font-family: 'Segoe UI';"
        )
        layout.addWidget(title)

        subtitle = QLabel("File Security Monitor")
        subtitle.setStyleSheet(
            f"color: {_PARCHMENT}; font-size: 12px; font-family: 'Segoe UI';"
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

        return header

    # -- Folder tree ------------------------------------------------------

    def _build_folder_tree(self) -> QWidget:
        """Build the folder tree panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 2, 4)
        layout.setSpacing(4)

        panel_label = QLabel("Watched Folders")
        panel_label.setStyleSheet(
            f"color: {_GOLD}; font-size: 12px; font-weight: bold; padding: 4px;"
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
            f"color: {_GOLD}; font-size: 12px; font-weight: bold; padding: 4px;"
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

        # Event table
        self._event_table = QTableWidget(0, 5)
        self._event_table.setHorizontalHeaderLabels(
            ["Time", "Type", "Path", "Details", "Level"],
        )
        self._event_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows,
        )
        self._event_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers,
        )
        self._event_table.verticalHeader().setVisible(False)

        header = self._event_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

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
        self._owl.set_state("alert")
        self._owl.say("Watching your files...", 3000)
        self._uptime_timer.start()

    def _on_watch_stopped(self) -> None:
        """Update UI when the watcher stops."""
        self._is_watching = False
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_watch_label.setText("Stopped")
        self._owl.set_state("idle")
        self._owl.say("Watcher stopped.", 3000)
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

    def _on_security_alert(self, alert: dict[str, Any]) -> None:
        """Handle a security alert from the security engine.

        Parameters
        ----------
        alert:
            Dictionary with keys from :class:`SecurityAlert.to_dict`.
        """
        self._alert_count += 1
        self._status_alerts_label.setText(f"{self._alert_count} alerts")
        self._status_alerts_label.setStyleSheet("color: #FF6B6B;")

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

        # Update owl state based on severity
        if level == "CRITICAL":
            self._owl.set_state("alarm")
            self._owl.say(message, 8000)
            # Notify via tray when window is hidden
            if not self.isVisible() and self._tray_icon.isVisible():
                self._tray_icon.showMessage(
                    "OwlWatcher Security Alert",
                    message,
                    QSystemTrayIcon.MessageIcon.Critical,
                    5000,
                )
        else:
            self._owl.set_state("alert")
            self._owl.say(message, 5000)

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

        Caps the table at ``_EVENT_MAX_ROWS`` rows by removing the oldest.
        """
        table = self._event_table
        row_count = table.rowCount()

        # Cap at max rows
        if row_count >= _EVENT_MAX_ROWS:
            table.removeRow(0)
            row_count -= 1

        row = row_count
        table.insertRow(row)

        # Parse fields
        timestamp = event.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                time_str = str(timestamp)
        else:
            time_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

        event_type = event.get("event_type", "")
        type_label = _EVENT_TYPE_LABELS.get(event_type, f"[{event_type.upper()}]")
        file_path = event.get("path", "")
        details = event.get("details", "")
        level = event.get("level", "INFO")

        # Create items
        items = [
            QTableWidgetItem(time_str),
            QTableWidgetItem(type_label),
            QTableWidgetItem(file_path),
            QTableWidgetItem(str(details)),
            QTableWidgetItem(level),
        ]

        # Apply row colouring
        bg = _ROW_COLORS.get(level, _ROW_COLORS["INFO"])
        fg = _LEVEL_TEXT_COLORS.get(level, _LEVEL_TEXT_COLORS["INFO"])

        for col, item in enumerate(items):
            item.setBackground(bg)
            item.setForeground(fg)
            table.setItem(row, col, item)

        # Store raw event data for filtering
        items[0].setData(Qt.ItemDataRole.UserRole, event)

        # Auto-scroll to bottom
        table.scrollToBottom()

    def _apply_filters(self) -> None:
        """Show/hide event log rows based on current filter settings."""
        search_text = self._search_input.text().lower()
        level_filter = self._level_filter.currentText()
        type_filter = self._type_filter.currentText()

        for row in range(self._event_table.rowCount()):
            time_item = self._event_table.item(row, 0)
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
        """Update the uptime display in the status bar."""
        if self._start_time is None:
            return
        elapsed = datetime.now(timezone.utc) - self._start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self._status_uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")

    # =====================================================================
    # Config helpers
    # =====================================================================

    def _load_watched_paths(self) -> list[str]:
        """Load the list of watched directories from watch_config.json."""
        if not CONFIG_PATH.exists():
            return [str(BASE_DIR)]
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as fh:
                config = json.load(fh)
            return config.get("watched_paths", [str(BASE_DIR)])
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read config: %s", exc)
            return [str(BASE_DIR)]

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
