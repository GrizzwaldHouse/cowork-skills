---
name: desktop-ui-designer
description: Design and implement modern desktop applications using PyQt6/PySide6 with proper architecture, signals/slots, themes, animations, and system tray integration following Marcus's coding standards.
user-invocable: true
---

# Desktop UI Designer (PyQt6/PySide6)

> Comprehensive patterns and standards for designing and implementing cross-platform desktop applications using PyQt6 or PySide6. Covers main windows, dialogs, custom widgets, themes, animations, event-driven architecture, and system integration.

## Description

Provides production-ready implementation patterns for PyQt6/PySide6 desktop applications. Emphasizes event-driven communication through signals/slots (Observer pattern), proper separation of UI from business logic, restrictive access control, theme systems, and cross-platform compatibility. All patterns follow Marcus's universal coding standards for portfolio-quality desktop applications.

## Prerequisites

- Python 3.10+
- PyQt6 or PySide6 installed (`pip install PyQt6` or `pip install PySide6`)
- Understanding of Qt's signals/slots mechanism
- Familiarity with Qt layouts (QVBoxLayout, QHBoxLayout, QGridLayout)
- Basic understanding of the event loop and Qt object hierarchy

## Usage

Follow the brainstorm-first methodology for any desktop UI feature request.

1. **Describe the requirement**: Specify window type (main window, dialog, widget), interactions, theme needs, platform constraints
2. **Choose the appropriate pattern**: Main window, dialog, custom widget, animated component, system tray
3. **Implement with proper architecture**: MVC/MVVM separation, signals/slots for communication, restrictive access control
4. **Apply theme system**: Dark/light modes, custom palettes, consistent styling
5. **Test on target platforms**: Windows, Linux, macOS

### Prompt Pattern

```
I need a [main window / dialog / custom widget / system tray app] for [purpose].
Requirements:
- [Feature 1]
- [Feature 2]
- Theme: [dark / light / custom]
- Platform: [Windows / Linux / macOS / all]

Apply Desktop UI Designer skill with proper signals/slots, access control, and theme support.
```

## Core Principles

### Event-Driven Communication (CRITICAL)

**NEVER poll for state changes.** Use Qt's signals/slots for all inter-component communication.

```python
# Good: Signal-based communication
class DataModel(QObject):
    data_changed = pyqtSignal(dict)  # Signal declaration

    def __init__(self):
        super().__init__()
        self._data = {}

    def update_data(self, new_data: dict) -> None:
        self._data = new_data
        self.data_changed.emit(self._data)  # Emit signal

class DisplayWidget(QWidget):
    def __init__(self, model: DataModel):
        super().__init__()
        self._model = model
        # Connect signal to slot
        self._model.data_changed.connect(self._on_data_changed)

    def _on_data_changed(self, data: dict) -> None:
        # React to data change
        self._update_display(data)

# Bad: Polling
class DisplayWidget(QWidget):
    def __init__(self, model: DataModel):
        super().__init__()
        self._model = model
        # NEVER DO THIS
        self._timer = QTimer()
        self._timer.timeout.connect(self._check_for_changes)
        self._timer.start(100)  # Polling every 100ms
```

### Access Control (CRITICAL)

All properties and methods get the most restrictive access level possible.

```python
# Good: Restrictive access control
class CustomWidget(QWidget):
    # Public signal for external connections
    value_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0  # Private attribute (Python convention with underscore)
        self._setup_ui()  # Private initialization method

    # Public read-only property
    @property
    def value(self) -> int:
        """Read-only access to current value."""
        return self._value

    # Public method to set value (controlled mutation)
    def set_value(self, new_value: int) -> None:
        """Set value with validation and signal emission."""
        if new_value != self._value:
            self._value = new_value
            self.value_changed.emit(self._value)
            self._update_display()

    # Private UI setup
    def _setup_ui(self) -> None:
        """Initialize UI components."""
        # Implementation
        pass

    # Private update method
    def _update_display(self) -> None:
        """Update internal display based on current value."""
        # Implementation
        pass

# Bad: Unrestricted mutable state
class CustomWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0  # Public mutable attribute - NEVER DO THIS
```

### Initialization (CRITICAL)

All defaults set in `__init__`. No magic numbers or strings.

```python
# Good: All defaults in constructor
class ThemedWindow(QMainWindow):
    # Class-level constants for configuration
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 800
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    WINDOW_TITLE = "Application Name"

    # Theme constants
    DARK_THEME_BG = "#1E1E1E"
    DARK_THEME_FG = "#FFFFFF"
    LIGHT_THEME_BG = "#FFFFFF"
    LIGHT_THEME_FG = "#000000"

    def __init__(self):
        super().__init__()
        # Initialize all instance attributes at construction
        self._current_theme = "dark"
        self._is_maximized = False

        # Apply configuration
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        self._setup_ui()
        self._apply_theme(self._current_theme)

# Bad: Magic numbers and scattered defaults
class ThemedWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)  # Magic numbers
        self._setup_ui()

    def _apply_theme(self):
        # Magic strings scattered in methods
        if self.theme == "dark":
            self.setStyleSheet("background-color: #1E1E1E;")
```

## Architecture Patterns

### Main Window Pattern (MVC)

Separate presentation from business logic. Main window orchestrates but doesn't contain business rules.

```python
# MainWindow.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Main application window following MVC pattern with theme support

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QMenuBar)
from PyQt6.QtCore import pyqtSignal, Qt, QSettings
from PyQt6.QtGui import QAction, QIcon
from typing import Optional

class MainWindow(QMainWindow):
    """Main application window with theme support and proper MVC separation."""

    # Signals for communication
    theme_changed = pyqtSignal(str)  # Emits "dark" or "light"
    settings_requested = pyqtSignal()

    # Window configuration
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 800
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    SETTINGS_ORG = "YourOrganization"
    SETTINGS_APP = "YourApp"

    def __init__(self):
        super().__init__()
        # Initialize state
        self._current_theme = "dark"
        self._settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        # Restore saved state
        self._restore_window_state()

        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._apply_theme(self._current_theme)

    @property
    def current_theme(self) -> str:
        """Read-only access to current theme."""
        return self._current_theme

    def toggle_theme(self) -> None:
        """Toggle between dark and light theme."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self._apply_theme(new_theme)
        self.theme_changed.emit(new_theme)

    def _setup_ui(self) -> None:
        """Initialize main UI components."""
        # Central widget with layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)  # 8px grid system
        main_layout.setSpacing(16)

        # Add components (delegate to separate methods)
        self._setup_header(main_layout)
        self._setup_content_area(main_layout)
        self._setup_footer(main_layout)

    def _setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Setup header section with title and controls."""
        header_layout = QHBoxLayout()

        title_label = QLabel("Application Title")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        theme_button = QPushButton("Toggle Theme")
        theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(theme_button)

        parent_layout.addLayout(header_layout)

    def _setup_content_area(self, parent_layout: QVBoxLayout) -> None:
        """Setup main content area."""
        content_label = QLabel("Main Content Area")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(content_label, stretch=1)

    def _setup_footer(self, parent_layout: QVBoxLayout) -> None:
        """Setup footer section."""
        footer_label = QLabel("Status: Ready")
        footer_label.setObjectName("statusLabel")
        parent_layout.addWidget(footer_label)

    def _setup_menu_bar(self) -> None:
        """Setup application menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        toggle_theme_action = QAction("Toggle &Theme", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(toggle_theme_action)

    def _apply_theme(self, theme: str) -> None:
        """Apply theme stylesheet to the entire window."""
        self._current_theme = theme

        if theme == "dark":
            stylesheet = self._get_dark_theme_stylesheet()
        else:
            stylesheet = self._get_light_theme_stylesheet()

        self.setStyleSheet(stylesheet)
        self._settings.setValue("theme", theme)

    def _get_dark_theme_stylesheet(self) -> str:
        """Return dark theme stylesheet."""
        return """
            QMainWindow {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QLabel#statusLabel {
                color: #B0B0B0;
                font-size: 12px;
            }
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3E3E3E;
            }
            QPushButton:pressed {
                background-color: #4E4E4E;
            }
            QMenuBar {
                background-color: #2D2D2D;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #3E3E3E;
            }
            QMenu {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3E3E3E;
            }
            QMenu::item:selected {
                background-color: #3E3E3E;
            }
        """

    def _get_light_theme_stylesheet(self) -> str:
        """Return light theme stylesheet."""
        return """
            QMainWindow {
                background-color: #FFFFFF;
                color: #000000;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #000000;
            }
            QLabel#statusLabel {
                color: #666666;
                font-size: 12px;
            }
            QPushButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QMenuBar {
                background-color: #F0F0F0;
                color: #000000;
            }
            QMenuBar::item:selected {
                background-color: #E0E0E0;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
            }
            QMenu::item:selected {
                background-color: #E0E0E0;
            }
        """

    def _restore_window_state(self) -> None:
        """Restore window geometry and theme from saved settings."""
        # Restore geometry
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
            self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Restore theme
        saved_theme = self._settings.value("theme", "dark")
        self._current_theme = saved_theme

    def closeEvent(self, event) -> None:
        """Save window state before closing."""
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("theme", self._current_theme)
        event.accept()
```

### Custom Widget Pattern

Create reusable components with proper encapsulation.

```python
# CustomProgressWidget.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Custom animated progress widget with signals

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from typing import Optional

class CircularProgressWidget(QWidget):
    """Custom circular progress indicator with smooth animations."""

    # Signals
    value_changed = pyqtSignal(int)  # Emits current progress value
    animation_finished = pyqtSignal()

    # Widget configuration
    DEFAULT_SIZE = 200
    MIN_VALUE = 0
    MAX_VALUE = 100
    ANIMATION_DURATION_MS = 500

    # Visual configuration
    BACKGROUND_COLOR = QColor("#2D2D2D")
    PROGRESS_COLOR = QColor("#4CAF50")
    TEXT_COLOR = QColor("#FFFFFF")
    LINE_WIDTH = 12

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Initialize state
        self._value = 0
        self._animated_value = 0.0  # For smooth animation

        # Setup widget
        self.setMinimumSize(self.DEFAULT_SIZE, self.DEFAULT_SIZE)

        # Setup animation
        self._animation = QPropertyAnimation(self, b"animated_value")
        self._animation.setDuration(self.ANIMATION_DURATION_MS)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.finished.connect(self.animation_finished.emit)

    @property
    def value(self) -> int:
        """Read-only access to current progress value."""
        return self._value

    def set_value(self, new_value: int, animated: bool = True) -> None:
        """
        Set progress value with optional animation.

        Args:
            new_value: Progress value between MIN_VALUE and MAX_VALUE
            animated: Whether to animate the transition
        """
        # Clamp value to valid range
        clamped_value = max(self.MIN_VALUE, min(self.MAX_VALUE, new_value))

        if clamped_value != self._value:
            self._value = clamped_value

            if animated:
                self._animation.setStartValue(self._animated_value)
                self._animation.setEndValue(float(self._value))
                self._animation.start()
            else:
                self._animated_value = float(self._value)
                self.update()  # Trigger repaint

            self.value_changed.emit(self._value)

    # Qt Property for animation system
    @pyqtProperty(float)
    def animated_value(self) -> float:
        """Animated value property for QPropertyAnimation."""
        return self._animated_value

    @animated_value.setter
    def animated_value(self, value: float) -> None:
        """Setter for animated value, triggers repaint."""
        self._animated_value = value
        self.update()  # Trigger repaint on every animation step

    def paintEvent(self, event) -> None:
        """Custom paint event to draw circular progress."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate dimensions
        width = self.width()
        height = self.height()
        size = min(width, height)

        # Center the circle
        rect = QRectF(
            (width - size) / 2 + self.LINE_WIDTH / 2,
            (height - size) / 2 + self.LINE_WIDTH / 2,
            size - self.LINE_WIDTH,
            size - self.LINE_WIDTH
        )

        # Draw background circle
        painter.setPen(QPen(self.BACKGROUND_COLOR, self.LINE_WIDTH, Qt.PenStyle.SolidLine))
        painter.drawArc(rect, 0, 360 * 16)  # Qt uses 1/16th degree units

        # Draw progress arc
        span_angle = int((self._animated_value / self.MAX_VALUE) * 360 * 16)
        painter.setPen(QPen(self.PROGRESS_COLOR, self.LINE_WIDTH, Qt.PenStyle.SolidLine))
        painter.drawArc(rect, 90 * 16, -span_angle)  # Start at top, go clockwise

        # Draw percentage text
        painter.setPen(QPen(self.TEXT_COLOR))
        painter.setFont(painter.font())
        font = painter.font()
        font.setPixelSize(size // 6)
        font.setBold(True)
        painter.setFont(font)

        text = f"{int(self._animated_value)}%"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
```

### Dialog Pattern

Modal dialogs with proper result handling and validation.

```python
# SettingsDialog.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Settings dialog with validation and signal-based communication

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLineEdit, QSpinBox, QCheckBox, QPushButton,
                              QLabel, QDialogButtonBox)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import Dict, Any, Optional

class SettingsDialog(QDialog):
    """Application settings dialog with validation."""

    # Signal emitted when settings are applied
    settings_changed = pyqtSignal(dict)

    # Default values
    DEFAULT_TIMEOUT = 30
    MIN_TIMEOUT = 5
    MAX_TIMEOUT = 300

    def __init__(self, current_settings: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Store current settings
        self._current_settings = current_settings.copy()
        self._pending_settings = current_settings.copy()

        # Configure dialog
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(400)

        # Setup UI
        self._setup_ui()
        self._populate_from_settings()

    def _setup_ui(self) -> None:
        """Initialize dialog UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Form layout for settings
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Username field
        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("Enter username")
        self._username_edit.textChanged.connect(self._on_username_changed)
        form_layout.addRow("Username:", self._username_edit)

        # Timeout field
        self._timeout_spin = QSpinBox()
        self._timeout_spin.setMinimum(self.MIN_TIMEOUT)
        self._timeout_spin.setMaximum(self.MAX_TIMEOUT)
        self._timeout_spin.setSuffix(" seconds")
        self._timeout_spin.valueChanged.connect(self._on_timeout_changed)
        form_layout.addRow("Timeout:", self._timeout_spin)

        # Auto-save checkbox
        self._autosave_check = QCheckBox("Enable auto-save")
        self._autosave_check.stateChanged.connect(self._on_autosave_changed)
        form_layout.addRow("", self._autosave_check)

        layout.addLayout(form_layout)

        # Validation message label
        self._validation_label = QLabel()
        self._validation_label.setStyleSheet("color: #F44336;")  # Red for errors
        self._validation_label.setWordWrap(True)
        self._validation_label.hide()
        layout.addWidget(self._validation_label)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Store reference to OK button for validation
        self._ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)

    def _populate_from_settings(self) -> None:
        """Populate UI fields from current settings."""
        self._username_edit.setText(self._current_settings.get("username", ""))
        self._timeout_spin.setValue(self._current_settings.get("timeout", self.DEFAULT_TIMEOUT))
        self._autosave_check.setChecked(self._current_settings.get("autosave", False))

    def _on_username_changed(self, text: str) -> None:
        """Handle username field changes."""
        self._pending_settings["username"] = text
        self._validate()

    def _on_timeout_changed(self, value: int) -> None:
        """Handle timeout field changes."""
        self._pending_settings["timeout"] = value
        self._validate()

    def _on_autosave_changed(self, state: int) -> None:
        """Handle autosave checkbox changes."""
        self._pending_settings["autosave"] = bool(state)

    def _validate(self) -> bool:
        """
        Validate pending settings.

        Returns:
            True if settings are valid, False otherwise
        """
        # Validate username is not empty
        username = self._pending_settings.get("username", "").strip()
        if not username:
            self._show_validation_error("Username cannot be empty")
            return False

        # Validate username length
        if len(username) < 3:
            self._show_validation_error("Username must be at least 3 characters")
            return False

        # All validation passed
        self._hide_validation_error()
        return True

    def _show_validation_error(self, message: str) -> None:
        """Display validation error message and disable OK button."""
        self._validation_label.setText(message)
        self._validation_label.show()
        self._ok_button.setEnabled(False)

    def _hide_validation_error(self) -> None:
        """Hide validation error message and enable OK button."""
        self._validation_label.hide()
        self._ok_button.setEnabled(True)

    def _on_accept(self) -> None:
        """Handle OK button click with final validation."""
        if self._validate():
            self.settings_changed.emit(self._pending_settings)
            self.accept()
```

### System Tray Integration

Background application with tray icon and context menu.

```python
# SystemTrayApp.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: System tray application with context menu and notifications

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
import sys
from typing import Optional

class SystemTrayApp(QObject):
    """Application that runs in system tray with notifications."""

    # Signals
    show_main_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    # Notification configuration
    NOTIFICATION_DURATION_MS = 3000

    def __init__(self, app: QApplication, icon_path: str):
        super().__init__()

        self._app = app
        self._icon_path = icon_path

        # Check system tray availability
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("System tray is not available on this system")

        # Setup tray icon
        self._setup_tray_icon()

    def _setup_tray_icon(self) -> None:
        """Initialize system tray icon and context menu."""
        self._tray_icon = QSystemTrayIcon(QIcon(self._icon_path), self._app)

        # Create context menu
        menu = QMenu()

        # Show action
        show_action = QAction("Show Window", menu)
        show_action.triggered.connect(self.show_main_window_requested.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        # Set menu and show icon
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def show_notification(self, title: str, message: str,
                          icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """
        Display system tray notification.

        Args:
            title: Notification title
            message: Notification message
            icon: Notification icon type
        """
        self._tray_icon.showMessage(title, message, icon, self.NOTIFICATION_DURATION_MS)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation (click, double-click, etc.)."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window_requested.emit()

    def _on_quit(self) -> None:
        """Handle quit action from tray menu."""
        self.quit_requested.emit()
        self._tray_icon.hide()
        self._app.quit()
```

## Animation Patterns

### Property Animation

Smooth value transitions using QPropertyAnimation.

```python
# AnimatedButton.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Button with hover animation using QPropertyAnimation

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty, QSize
from PyQt6.QtGui import QColor
from typing import Optional

class AnimatedButton(QPushButton):
    """Button with smooth color animation on hover."""

    # Animation configuration
    ANIMATION_DURATION_MS = 200

    # Colors
    NORMAL_COLOR = QColor("#2D2D2D")
    HOVER_COLOR = QColor("#4CAF50")

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)

        # Initialize color state
        self._current_color = self.NORMAL_COLOR

        # Setup animation
        self._color_animation = QPropertyAnimation(self, b"button_color")
        self._color_animation.setDuration(self.ANIMATION_DURATION_MS)
        self._color_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Apply initial style
        self._update_stylesheet()

    @pyqtProperty(QColor)
    def button_color(self) -> QColor:
        """Animated color property."""
        return self._current_color

    @button_color.setter
    def button_color(self, color: QColor) -> None:
        """Set button color and update stylesheet."""
        self._current_color = color
        self._update_stylesheet()

    def _update_stylesheet(self) -> None:
        """Update button stylesheet with current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._current_color.name()};
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }}
        """)

    def enterEvent(self, event) -> None:
        """Animate to hover color when mouse enters."""
        self._color_animation.setStartValue(self._current_color)
        self._color_animation.setEndValue(self.HOVER_COLOR)
        self._color_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Animate to normal color when mouse leaves."""
        self._color_animation.setStartValue(self._current_color)
        self._color_animation.setEndValue(self.NORMAL_COLOR)
        self._color_animation.start()
        super().leaveEvent(event)
```

## Theme System

### Centralized Theme Manager

```python
# ThemeManager.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Centralized theme management with signal-based updates

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any

class ThemeManager(QObject):
    """Centralized theme management for the entire application."""

    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str, dict)  # (theme_name, theme_data)

    def __init__(self):
        super().__init__()

        self._current_theme = "dark"
        self._themes = {
            "dark": self._get_dark_theme(),
            "light": self._get_light_theme()
        }

    @property
    def current_theme_name(self) -> str:
        """Read-only access to current theme name."""
        return self._current_theme

    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme data."""
        return self._themes[self._current_theme].copy()

    def set_theme(self, theme_name: str) -> None:
        """
        Set active theme by name.

        Args:
            theme_name: Name of theme to activate ("dark" or "light")

        Raises:
            ValueError: If theme name is not recognized
        """
        if theme_name not in self._themes:
            raise ValueError(f"Unknown theme: {theme_name}")

        if theme_name != self._current_theme:
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name, self.get_current_theme())

    def register_theme(self, theme_name: str, theme_data: Dict[str, Any]) -> None:
        """Register a custom theme."""
        self._themes[theme_name] = theme_data

    def _get_dark_theme(self) -> Dict[str, Any]:
        """Return dark theme configuration."""
        return {
            "background": "#1E1E1E",
            "foreground": "#FFFFFF",
            "primary": "#4CAF50",
            "secondary": "#2196F3",
            "error": "#F44336",
            "warning": "#FF9800",
            "border": "#3E3E3E",
            "button_bg": "#2D2D2D",
            "button_hover": "#3E3E3E",
            "button_pressed": "#4E4E4E",
        }

    def _get_light_theme(self) -> Dict[str, Any]:
        """Return light theme configuration."""
        return {
            "background": "#FFFFFF",
            "foreground": "#000000",
            "primary": "#4CAF50",
            "secondary": "#2196F3",
            "error": "#F44336",
            "warning": "#FF9800",
            "border": "#CCCCCC",
            "button_bg": "#F0F0F0",
            "button_hover": "#E0E0E0",
            "button_pressed": "#D0D0D0",
        }
```

## Examples

### Example 1: Main Window with Theme Toggle

**Input:**
```
Create a main window with:
- Dark/light theme toggle button
- Menu bar with File and View menus
- Persistent window geometry
- Status bar showing current theme
```

**Output:**
Complete MainWindow implementation (shown in Architecture Patterns section above).

### Example 2: Custom Animated Progress Widget

**Input:**
```
Create a custom circular progress widget with:
- Smooth animation when value changes
- Percentage text in center
- Signal when progress completes
- Configurable colors
```

**Output:**
Complete CircularProgressWidget implementation (shown in Custom Widget Pattern section above).

### Example 3: Settings Dialog with Validation

**Input:**
```
Create a settings dialog with:
- Username field (required, min 3 characters)
- Timeout spinner (5-300 seconds)
- Auto-save checkbox
- Real-time validation
- Signal when settings change
```

**Output:**
Complete SettingsDialog implementation (shown in Dialog Pattern section above).

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| qt_library | PyQt6 | Qt binding to use (PyQt6 or PySide6) |
| default_theme | dark | Initial theme on first launch |
| animation_enabled | true | Enable UI animations |
| animation_duration | 200ms | Default animation duration |
| settings_persistence | QSettings | Use Qt's QSettings for state persistence |
| signal_slot_communication | required | All inter-component communication via signals/slots |

## File Structure

```
desktop-ui-designer/
  SKILL.md              # This skill definition
  README.md             # Quick-start guide
  resources/
    main_window_template.py      # Complete main window example
    custom_widget_template.py    # Custom widget template
    dialog_template.py           # Dialog template
    theme_manager.py             # Theme system
    animation_examples.py        # Animation patterns
```

## Best Practices

### Layout System

Use Qt's layout managers, never absolute positioning.

```python
# Good: Layout-based positioning
layout = QVBoxLayout()
layout.setContentsMargins(16, 16, 16, 16)  # 8px grid system
layout.setSpacing(16)
layout.addWidget(widget1)
layout.addWidget(widget2)

# Bad: Absolute positioning
widget.setGeometry(100, 100, 200, 50)  # Breaks on different screen sizes/DPI
```

### Resource Management

Clean up resources properly to prevent memory leaks.

```python
class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timeout)
        self._timer.start(1000)

    def cleanup(self) -> None:
        """Proper cleanup of resources."""
        if self._timer.isActive():
            self._timer.stop()
        self._timer.deleteLater()
```

### Signal Connection

Always connect signals properly and clean up when needed.

```python
# Good: Proper connection and cleanup
def __init__(self):
    self._model.data_changed.connect(self._on_data_changed)

def cleanup(self):
    self._model.data_changed.disconnect(self._on_data_changed)

# Bad: Lambda without cleanup (can cause memory leaks)
self._model.data_changed.connect(lambda: self.update())
```

### Type Hints

Use type hints for all method signatures.

```python
# Good: Complete type hints
def set_value(self, value: int, animated: bool = True) -> None:
    """Set value with optional animation."""
    pass

# Bad: No type information
def set_value(self, value, animated=True):
    pass
```

## Platform-Specific Considerations

### Windows
- System tray icon requires .ico format (use QIcon.fromTheme for fallback)
- High DPI scaling: `QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)` before QApplication creation
- Native window decorations: Use `Qt.WindowType.FramelessWindowHint` carefully

### Linux
- System tray support varies by desktop environment
- Use FreeDesktop standards for icon themes
- File dialogs respect GTK/KDE theming

### macOS
- Menu bar is global, not per-window
- Use `Qt.WindowType.Sheet` for modal dialogs following macOS HIG
- System tray called "menu bar extras"

## Testing

### Unit Testing Widgets

```python
# test_custom_widget.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Unit tests for custom widget with signal testing

import pytest
from PyQt6.QtCore import Qt, QSignalSpy
from custom_widget import CircularProgressWidget

@pytest.fixture
def widget(qtbot):
    """Create widget instance for testing."""
    w = CircularProgressWidget()
    qtbot.addWidget(w)
    return w

def test_initial_value(widget):
    """Test widget initializes with zero value."""
    assert widget.value == 0

def test_set_value_emits_signal(widget, qtbot):
    """Test that setting value emits value_changed signal."""
    # Create signal spy
    spy = QSignalSpy(widget.value_changed)

    # Set value
    widget.set_value(50, animated=False)

    # Verify signal emitted
    assert len(spy) == 1
    assert spy[0][0] == 50

def test_value_clamping(widget):
    """Test that values are clamped to valid range."""
    widget.set_value(150, animated=False)
    assert widget.value == 100  # MAX_VALUE

    widget.set_value(-10, animated=False)
    assert widget.value == 0  # MIN_VALUE
```

## Notes

- **Always use signals/slots** for inter-component communication. NEVER poll.
- **Access control is critical**: Use private attributes (`_attribute`) and expose through properties or controlled setters.
- **All defaults in `__init__`**: Never scatter magic numbers/strings throughout code.
- **QSettings for persistence**: Window geometry, theme, user preferences.
- **8px grid system**: All spacing and sizing should be multiples of 8px for visual consistency.
- **Test on target platforms**: Qt is cross-platform but behavior varies. Test Windows/Linux/macOS if targeting multiple platforms.
- **High DPI awareness**: Enable high DPI scaling for modern displays.
- **Cleanup resources**: Timer stops, signal disconnections, deleteLater() calls.
- **Stylesheet vs subclassing**: Use stylesheets for simple theming, subclass and override paintEvent for complex custom rendering.
- **Thread safety**: UI updates MUST happen on main thread. Use signals to communicate from worker threads.

## Integration with Other Skills

- **Universal Coding Standards**: Access control, initialization, communication patterns, comments
- **Dev Workflow**: Brainstorm-first methodology, testing standards, version control
- **Enterprise Secure AI Engineering**: Input validation, no hardcoded secrets, logging
- **Architecture Patterns**: MVC/MVVM, Observer (signals/slots), dependency injection

## Further Reading

- Qt Documentation: https://doc.qt.io/qt-6/
- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- PySide6 Documentation: https://doc.qt.io/qtforpython-6/
- Qt Designer: Visual UI design tool (generates .ui files loadable with `uic.loadUi()`)
