# theme.py
# Developer: Marcus Daley
# Date: 2026-02-21
# Purpose: Theme management for light/dark mode switching throughout the application

"""
Theme manager for OwlWatcher.

Provides two themes:
- DARK (default): Navy/gold night-sky theme
- LIGHT: Parchment/teal day theme

Usage::

    from gui.theme import ThemeManager, Theme
    
    manager = ThemeManager()
    manager.apply_theme(Theme.LIGHT)
"""

from __future__ import annotations

from enum import Enum

from PyQt6.QtWidgets import QApplication


class Theme(str, Enum):
    """Available theme modes."""
    DARK = "dark"
    LIGHT = "light"


# Dark theme colors (default night-sky)
DARK_COLORS = {
    "background": "#0D1B2A",      # Deep navy
    "panel": "#1B263B",           # Mid navy
    "header": "#415A77",          # Slate blue
    "text": "#E0E1DD",            # Parchment
    "accent": "#D4AF37",          # Gold
    "highlight": "#4A7C9D",       # Teal
    "border": "#D4AF37",          # Gold
}

# Light theme colors (day mode)
LIGHT_COLORS = {
    "background": "#F5F3E7",      # Light parchment
    "panel": "#E8E4D9",           # Warm cream
    "header": "#D4C5A9",          # Tan
    "text": "#2C3E50",            # Dark blue-gray
    "accent": "#C87533",          # Warm copper
    "highlight": "#5D8AA8",       # Steel blue
    "border": "#A0826D",          # Bronze
}


class ThemeManager:
    """Manages application-wide theme switching."""

    def __init__(self) -> None:
        self._current_theme = Theme.DARK

    @property
    def current_theme(self) -> Theme:
        """Get the current active theme."""
        return self._current_theme

    def toggle_theme(self) -> Theme:
        """Toggle between dark and light themes.
        
        Returns the new theme after toggling.
        """
        if self._current_theme == Theme.DARK:
            self._current_theme = Theme.LIGHT
        else:
            self._current_theme = Theme.DARK
        self.apply_theme(self._current_theme)
        return self._current_theme

    def apply_theme(self, theme: Theme) -> None:
        """Apply the specified theme to the application.
        
        Updates the global QApplication stylesheet with theme colors.
        """
        self._current_theme = theme
        colors = DARK_COLORS if theme == Theme.DARK else LIGHT_COLORS

        # Generate global stylesheet
        stylesheet = f"""
            QMainWindow, QDialog, QWidget {{
                background-color: {colors['background']};
                color: {colors['text']};
            }}
            QMenuBar {{
                background-color: {colors['header']};
                color: {colors['text']};
            }}
            QMenuBar::item:selected {{
                background-color: {colors['accent']};
                color: {colors['background']};
            }}
            QMenu {{
                background-color: {colors['panel']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
            QMenu::item:selected {{
                background-color: {colors['accent']};
                color: {colors['background']};
            }}
            QPushButton {{
                background-color: {colors['accent']};
                color: {colors['background']};
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors['highlight']};
            }}
            QLineEdit, QSpinBox, QComboBox {{
                background-color: {colors['panel']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 4px;
                border-radius: 3px;
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QStatusBar {{
                background-color: {colors['panel']};
                color: {colors['text']};
            }}
        """

        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)

    def get_colors(self) -> dict[str, str]:
        """Get the color palette for the current theme."""
        return DARK_COLORS if self._current_theme == Theme.DARK else LIGHT_COLORS
