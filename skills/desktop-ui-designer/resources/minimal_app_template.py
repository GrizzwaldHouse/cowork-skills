# minimal_app_template.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Minimal PyQt6 application template following coding standards

"""
Minimal PyQt6 application template.

This template demonstrates:
- Proper initialization with all defaults in __init__
- Access control with private attributes
- Signal/slot communication
- Type hints
- QSettings persistence
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, QSettings
from typing import Optional
import sys


class MainWindow(QMainWindow):
    """Main application window with minimal functionality."""

    # Configuration constants
    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 600
    MIN_WIDTH = 600
    MIN_HEIGHT = 400
    WINDOW_TITLE = "Minimal App"
    SETTINGS_ORG = "YourOrganization"
    SETTINGS_APP = "MinimalApp"

    def __init__(self):
        super().__init__()

        # Initialize state
        self._click_count = 0
        self._settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        # Configure window
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Restore saved geometry
        self._restore_window_state()

        # Setup UI
        self._setup_ui()

    @property
    def click_count(self) -> int:
        """Read-only access to click count."""
        return self._click_count

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Label
        self._label = QLabel("Click the button below")
        layout.addWidget(self._label)

        # Button
        button = QPushButton("Click Me")
        button.clicked.connect(self._on_button_clicked)
        layout.addWidget(button)

        layout.addStretch()

    def _on_button_clicked(self) -> None:
        """Handle button click event."""
        self._click_count += 1
        self._label.setText(f"Button clicked {self._click_count} times")

    def _restore_window_state(self) -> None:
        """Restore window geometry from saved settings."""
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:
        """Save window state before closing."""
        self._settings.setValue("geometry", self.saveGeometry())
        event.accept()


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)

    # Enable high DPI scaling
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
