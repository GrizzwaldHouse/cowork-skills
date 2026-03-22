# test_debug.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Debug script to test owl widget visibility and theme toggle functionality

"""
Debug script to isolate and test two critical bugs:
1. Owl widget not rendering (invisible)
2. Moon button theme toggle not working
"""

import sys
import logging
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt

# Import the components we're testing
from gui.widgets.owl_widget import OwlWidget
from gui.widgets.ambient_widget import AmbientBackgroundWidget
from gui.theme import ThemeManager
from gui.constants import OWL_HEADER_SIZE
from gui.paths import ASSETS_DIR

logger = logging.getLogger("debug_test")


class DebugWindow(QMainWindow):
    """Minimal test window to debug owl and theme issues."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Owl & Theme Debug Test")
        self.setGeometry(100, 100, 600, 400)

        # Theme manager
        self._theme_manager = ThemeManager()
        self._theme_manager.apply_theme(self._theme_manager.current_theme)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Info label
        info = QLabel("Testing Owl Widget Visibility and Theme Toggle")
        info.setStyleSheet("color: white; font-size: 14px; padding: 10px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # Ambient background with moon button
        logger.info("Creating AmbientBackgroundWidget...")
        self._ambient = AmbientBackgroundWidget()
        self._ambient.setFixedHeight(100)
        self._ambient.theme_toggle_requested.connect(self._on_theme_toggle)
        layout.addWidget(self._ambient)
        logger.info(f"AmbientBackgroundWidget created: {self._ambient}")

        # Owl widget
        logger.info(f"Creating OwlWidget with size={OWL_HEADER_SIZE}...")
        logger.info(f"ASSETS_DIR = {ASSETS_DIR}")
        logger.info(f"ASSETS_DIR exists: {ASSETS_DIR.exists()}")

        self._owl = OwlWidget(owl_size=OWL_HEADER_SIZE)
        layout.addWidget(self._owl, alignment=Qt.AlignmentFlag.AlignCenter)

        logger.info(f"OwlWidget created: {self._owl}")
        logger.info(f"OwlWidget visible: {self._owl.isVisible()}")
        logger.info(f"OwlWidget size: {self._owl.size()}")
        logger.info(f"OwlWidget geometry: {self._owl.geometry()}")

        # Status label
        self._status = QLabel(f"Theme: {self._theme_manager.current_theme.value}")
        self._status.setStyleSheet("color: yellow; font-size: 12px; padding: 10px;")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        layout.addStretch()

    def _on_theme_toggle(self):
        """Handle theme toggle from moon button."""
        logger.info("Theme toggle requested!")
        logger.info(f"Current theme before toggle: {self._theme_manager.current_theme}")

        new_theme = self._theme_manager.toggle_theme()

        logger.info(f"New theme after toggle: {new_theme}")
        self._status.setText(f"Theme: {new_theme.value}")


if __name__ == "__main__":
    logger.info("Starting debug test...")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Working directory: {Path.cwd()}")

    app = QApplication(sys.argv)
    window = DebugWindow()
    window.show()

    logger.info("Window shown, entering event loop...")
    sys.exit(app.exec())
