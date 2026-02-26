# Desktop UI Designer (PyQt6/PySide6)

Quick-start guide for designing and implementing modern desktop applications using PyQt6 or PySide6 following Marcus Daley's coding standards.

## Overview

This skill provides production-ready patterns for PyQt6/PySide6 desktop applications with emphasis on:

- **Event-driven architecture** using signals/slots (Observer pattern)
- **Proper encapsulation** with restrictive access control
- **Theme systems** supporting dark/light modes
- **Smooth animations** using QPropertyAnimation
- **System integration** with tray icons and notifications
- **MVC/MVVM separation** of UI from business logic

## Quick Start

### Installation

```bash
# PyQt6
pip install PyQt6

# OR PySide6
pip install PySide6
```

### Basic Main Window

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.resize(800, 600)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
```

## Key Patterns

### 1. Signals/Slots Communication

```python
# NEVER poll - use signals/slots
class DataModel(QObject):
    data_changed = pyqtSignal(dict)

    def update(self, data):
        self.data_changed.emit(data)

class View(QWidget):
    def __init__(self, model):
        super().__init__()
        model.data_changed.connect(self._on_data_changed)

    def _on_data_changed(self, data):
        # React to change
        pass
```

### 2. Access Control

```python
class Widget(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._value = 0  # Private attribute

    @property
    def value(self) -> int:
        """Read-only access."""
        return self._value

    def set_value(self, new_value: int) -> None:
        """Controlled mutation."""
        self._value = new_value
        self.value_changed.emit(self._value)
```

### 3. Theme Support

```python
# All colors/styles as constants
DARK_BACKGROUND = "#1E1E1E"
DARK_FOREGROUND = "#FFFFFF"

def apply_dark_theme(self):
    self.setStyleSheet(f"""
        QWidget {{
            background-color: {DARK_BACKGROUND};
            color: {DARK_FOREGROUND};
        }}
    """)
```

### 4. Smooth Animations

```python
animation = QPropertyAnimation(widget, b"geometry")
animation.setDuration(300)
animation.setEasingCurve(QEasingCurve.Type.OutCubic)
animation.setStartValue(start_rect)
animation.setEndValue(end_rect)
animation.start()
```

## Common Use Cases

### Main Application Window
See `SKILL.md` MainWindow pattern for complete example with:
- Menu bar
- Theme toggling
- Persistent geometry
- Proper layouts

### Custom Widget
See `SKILL.md` CircularProgressWidget for:
- Custom paintEvent
- Property animations
- Signal emissions
- Type hints

### Modal Dialog
See `SKILL.md` SettingsDialog for:
- Form validation
- Real-time feedback
- Result signals
- Button box handling

### System Tray App
See `SKILL.md` SystemTrayApp for:
- Tray icon
- Context menu
- Notifications
- Background operation

## Critical Rules

1. **NEVER poll** - always use signals/slots
2. **Private by default** - use `_attribute` and expose via properties
3. **All defaults in `__init__`** - no magic numbers/strings
4. **Use layouts** - never absolute positioning
5. **Clean up resources** - stop timers, disconnect signals, deleteLater()
6. **Type hints everywhere** - all method signatures
7. **QSettings for persistence** - window state, preferences
8. **8px grid system** - consistent spacing

## Testing

```bash
pip install pytest pytest-qt

# Run tests
pytest tests/
```

Example test:
```python
def test_widget_signal(qtbot):
    widget = MyWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.value_changed, timeout=1000):
        widget.set_value(50)
```

## Platform Notes

- **Windows**: Use .ico for tray icons, enable high DPI scaling
- **Linux**: System tray varies by desktop environment
- **macOS**: Global menu bar, use Qt.WindowType.Sheet for modals

## Resources

- Full patterns and examples: See `SKILL.md`
- Qt Documentation: https://doc.qt.io/qt-6/
- PyQt6 Docs: https://www.riverbankcomputing.com/static/Docs/PyQt6/

## Integration

Works with Marcus's other skills:
- **Universal Coding Standards** - Access control, initialization, communication
- **Dev Workflow** - Brainstorm-first methodology
- **Enterprise Secure AI Engineering** - Input validation, no secrets
- **Architecture Patterns** - MVC/MVVM, Observer, dependency injection
