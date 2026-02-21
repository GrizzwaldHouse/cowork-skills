# settings_dialog.py
# Developer: Marcus Daley
# Date: 2026-02-21
# Purpose: User configuration dialog for watched paths, ignored patterns, sync intervals, and preferences

"""
Settings dialog for OwlWatcher.

Allows users to configure:
- Watched folder paths (add/remove)
- Ignored file patterns
- Sync interval (seconds)
- Sound effects toggle
- (Future) Theme toggle

Usage::

    dialog = SettingsDialog(parent_window)
    if dialog.exec():
        # User clicked Save
        new_config = dialog.get_config()
"""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from config_manager import load_config
from gui.constants import FONT_FAMILY, GOLD, MID_PANEL, NAVY, PARCHMENT


class SettingsDialog(QDialog):
    """User configuration dialog for OwlWatcher preferences."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("OwlWatcher Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Load current config
        self._config = load_config()

        # Build UI
        self._build_ui()
        self._load_values()

        # Styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {MID_PANEL};
                color: {PARCHMENT};
                font-family: '{FONT_FAMILY}';
            }}
            QGroupBox {{
                font-weight: bold;
                color: {GOLD};
                border: 1px solid {GOLD};
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
            QListWidget {{
                background-color: {NAVY};
                color: {PARCHMENT};
                border: 1px solid {GOLD};
            }}
            QPushButton {{
                background-color: {GOLD};
                color: {NAVY};
                border: none;
                padding: 4px 12px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: #D4AF37;
            }}
        """)

    def _build_ui(self) -> None:
        """Build the settings UI."""
        layout = QVBoxLayout(self)

        # --- Watched Paths ---
        paths_group = QGroupBox("Watched Folders")
        paths_layout = QVBoxLayout()

        self._paths_list = QListWidget()
        paths_layout.addWidget(self._paths_list)

        paths_buttons = QHBoxLayout()
        self._add_path_btn = QPushButton("Add Folder...")
        self._add_path_btn.clicked.connect(self._on_add_path)
        self._remove_path_btn = QPushButton("Remove Selected")
        self._remove_path_btn.clicked.connect(self._on_remove_path)
        paths_buttons.addWidget(self._add_path_btn)
        paths_buttons.addWidget(self._remove_path_btn)
        paths_buttons.addStretch()
        paths_layout.addLayout(paths_buttons)

        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        # --- Ignored Patterns ---
        ignored_group = QGroupBox("Ignored Patterns (comma-separated)")
        ignored_layout = QVBoxLayout()

        self._ignored_edit = QLineEdit()
        self._ignored_edit.setPlaceholderText("e.g. *.log, *.tmp, node_modules/**")
        ignored_layout.addWidget(self._ignored_edit)

        ignored_group.setLayout(ignored_layout)
        layout.addWidget(ignored_group)

        # --- Preferences ---
        prefs_group = QGroupBox("Preferences")
        prefs_layout = QFormLayout()

        self._sync_interval_spin = QSpinBox()
        self._sync_interval_spin.setMinimum(1)
        self._sync_interval_spin.setMaximum(60)
        self._sync_interval_spin.setSuffix(" seconds")
        prefs_layout.addRow("Sync Interval:", self._sync_interval_spin)

        self._sounds_checkbox = QCheckBox("Enable sound effects")
        prefs_layout.addRow("Sounds:", self._sounds_checkbox)

        prefs_group.setLayout(prefs_layout)
        layout.addWidget(prefs_group)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values(self) -> None:
        """Load current config values into UI."""
        # Watched paths
        watched = self._config.get("watched_paths", [])
        for path in watched:
            self._paths_list.addItem(path)

        # Ignored patterns
        ignored = self._config.get("ignored_patterns", [])
        self._ignored_edit.setText(", ".join(ignored))

        # Sync interval
        interval = self._config.get("sync_interval", 5)
        self._sync_interval_spin.setValue(int(interval))

        # Sounds (default True)
        sounds = self._config.get("sounds_enabled", True)
        self._sounds_checkbox.setChecked(sounds)

    def _on_add_path(self) -> None:
        """Add a new watched folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder to Watch", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._paths_list.addItem(folder)

    def _on_remove_path(self) -> None:
        """Remove selected folder from watch list."""
        current_row = self._paths_list.currentRow()
        if current_row >= 0:
            self._paths_list.takeItem(current_row)

    def get_config(self) -> dict:
        """Return updated config dict with user changes."""
        # Collect watched paths
        paths = []
        for i in range(self._paths_list.count()):
            paths.append(self._paths_list.item(i).text())

        # Parse ignored patterns
        ignored_text = self._ignored_edit.text().strip()
        ignored = [p.strip() for p in ignored_text.split(",") if p.strip()]

        return {
            "watched_paths": paths,
            "ignored_patterns": ignored,
            "sync_interval": self._sync_interval_spin.value(),
            "sounds_enabled": self._sounds_checkbox.isChecked(),
        }
