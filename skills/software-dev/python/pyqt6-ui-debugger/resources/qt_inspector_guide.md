# Qt Inspector Setup and Usage Guide

Advanced runtime debugging tools for PyQt6 applications.

## Overview

Qt Inspector tools allow you to:
- View the live widget hierarchy
- Inspect widget properties at runtime
- Monitor signal/slot connections
- Visualize layout calculations
- Profile paint events
- Debug stylesheet application

## Tools

### 1. GammaRay (Recommended)

**What it is**: Comprehensive Qt debugging tool from KDAB

**Features**:
- Live widget tree inspector
- Property editor with live updates
- Signal/slot connection viewer
- Paint analyzer
- Layout inspector
- Resource browser

**Installation**:

```bash
# Linux (Ubuntu/Debian)
sudo apt-get install gammaray

# Linux (Fedora)
sudo dnf install gammaray

# macOS
brew install gammaray

# Windows
# Download from: https://www.kdab.com/development-resources/qt-tools/gammaray/
# Or use chocolatey
choco install gammaray
```

**Usage**:

```bash
# Launch your app through GammaRay
gammaray python your_app.py

# Or attach to running process
gammaray --pid <process_id>

# Or inject into existing app
python -m gammaray.injector your_app.py
```

**Key Features**:
- Widget tree shows hierarchy, visibility, geometry
- Double-click widget to highlight in running app
- Edit properties live (useful for testing fixes)
- View all signal connections
- See stylesheet resolution chain

### 2. Qt Creator Debugger

**What it is**: Qt's official IDE with integrated debugging

**Features**:
- QML/Widget debugger
- Breakpoints in signal handlers
- Property inspection
- Call stack visualization

**Installation**:

```bash
# Download from https://www.qt.io/download-qt-installer

# Or via package manager
# Linux
sudo apt-get install qtcreator

# macOS
brew install --cask qt-creator
```

**Usage**:

1. Open Qt Creator
2. File → Open File or Project → Select your .py file
3. Run → Debug (F5)
4. Use Debug → Views → QML/Widget Debugger

**Key Features**:
- Set breakpoints in Python code
- Inspect Qt object properties in debugger
- View widget hierarchy while paused
- Step through paintEvent() calls

### 3. Built-in Qt Debug Output

**What it is**: Environment variables that enable Qt's internal logging

**Usage**:

```bash
# Enable all debug output
export QT_LOGGING_RULES="*.debug=true"
python your_app.py

# Enable specific categories
export QT_LOGGING_RULES="qt.qpa.*=true;qt.widgets.*=true"

# Show layout calculations
export QT_DEBUG_LAYOUTS=1

# Show paint rectangles (visual debugging)
export QT_DEBUG_BACKINGSTORE=1
```

**Windows**:
```cmd
set QT_LOGGING_RULES=*.debug=true
python your_app.py
```

**Key Features**:
- No additional tools needed
- See Qt's internal decision-making
- Useful for layout and paint issues

### 4. Python-Based Runtime Inspector

**What it is**: Custom Python script that inspects running app

**Implementation**:

```python
# File: runtime_inspector.py
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt

class RuntimeInspector(QDialog):
    """
    Live inspector for PyQt6 widget hierarchy.

    Usage:
        inspector = RuntimeInspector(main_window)
        inspector.show()
    """

    def __init__(self, root_widget: QWidget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyQt6 Runtime Inspector")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Widget", "Visible", "Size", "Pos", "Policy"])
        layout.addWidget(self.tree)

        self.root_widget = root_widget
        self.refresh()

        # Refresh every 2 seconds
        from PyQt6.QtCore import QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

    def refresh(self):
        """Rebuild widget tree"""
        self.tree.clear()
        self._add_widget(self.root_widget, self.tree)
        self.tree.expandAll()

    def _add_widget(self, widget: QWidget, parent_item):
        """Recursively add widget to tree"""
        # Create tree item
        item = QTreeWidgetItem(parent_item)
        item.setText(0, widget.__class__.__name__)
        item.setText(1, "✓" if widget.isVisible() else "✗")
        item.setText(2, f"{widget.size().width()}x{widget.size().height()}")
        item.setText(3, f"{widget.pos().x()},{widget.pos().y()}")

        policy = widget.sizePolicy()
        h_policy = self._policy_name(policy.horizontalPolicy())
        v_policy = self._policy_name(policy.verticalPolicy())
        item.setText(4, f"H:{h_policy}, V:{v_policy}")

        # Color-code based on visibility
        if not widget.isVisible():
            item.setForeground(0, Qt.GlobalColor.gray)

        # Recurse children
        for child in widget.children():
            if isinstance(child, QWidget):
                self._add_widget(child, item)

    @staticmethod
    def _policy_name(policy):
        """Convert policy enum to short name"""
        names = {
            0: "Fix", 1: "Min", 4: "Max", 5: "Pref",
            7: "Exp", 3: "MinExp", 13: "Ign"
        }
        return names.get(int(policy), "?")


# Usage in your app:
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.show()

    # Open inspector
    inspector = RuntimeInspector(window)
    inspector.show()

    sys.exit(app.exec())
```

**Key Features**:
- No external dependencies
- Customizable to your needs
- Auto-refresh for live updates
- Easy to extend with new columns

## Workflow: Debugging with Inspector

### Scenario: Widget Not Visible

1. **Launch app through GammaRay**:
   ```bash
   gammaray python your_app.py
   ```

2. **Open Widget Inspector** (GammaRay window):
   - Navigate to "Widget Inspector" tab
   - See full widget hierarchy

3. **Locate the problematic widget**:
   - Search by class name
   - Or navigate tree manually

4. **Check visibility chain**:
   - Look at "visible" column
   - Check all ancestors
   - If any parent is hidden, child won't show

5. **Check geometry**:
   - Look at "geometry" column
   - Size of 0x0 or 1x1 indicates sizing issue
   - Position outside parent bounds = not visible

6. **Fix and verify**:
   - Make code changes
   - Restart app (or use hot reload)
   - Verify in inspector

### Scenario: Layout Not Working

1. **Enable layout debugging**:
   ```bash
   export QT_DEBUG_LAYOUTS=1
   python your_app.py
   ```

2. **Watch console output**:
   - Qt logs layout decisions
   - Shows minimum/maximum sizes
   - Shows size hint calculations

3. **Open GammaRay Widget Inspector**:
   - Click on container widget
   - Go to "Properties" tab
   - Look at "layout" property

4. **Check margins and spacing**:
   - Look for "contentsMargins" property
   - Look for "spacing" property
   - Verify not set to 0 unintentionally

5. **Verify widget in layout**:
   - In widget tree, child should be nested under layout
   - If not, widget not added to layout

### Scenario: Stylesheet Not Applying

1. **Open GammaRay Style Inspector**:
   - Select widget in tree
   - Go to "Style Inspector" tab

2. **View computed styles**:
   - Shows final computed stylesheet
   - Shows which rules apply
   - Shows inheritance chain

3. **Check specificity**:
   - More specific selectors override general ones
   - IDs (`#myButton`) > classes (`.QPushButton`) > type (`QPushButton`)

4. **Test live changes**:
   - Edit stylesheet in GammaRay
   - See changes immediately
   - Copy working stylesheet back to code

## Best Practices

### During Development

1. **Run with debug output by default**:
   ```python
   import os
   if os.environ.get('DEBUG'):
       os.environ['QT_LOGGING_RULES'] = '*.debug=true'
   ```

2. **Add inspector keyboard shortcut**:
   ```python
   from PyQt6.QtGui import QShortcut, QKeySequence

   # Ctrl+I to open inspector
   shortcut = QShortcut(QKeySequence('Ctrl+I'), window)
   shortcut.activated.connect(lambda: RuntimeInspector(window).show())
   ```

3. **Log significant widget operations**:
   ```python
   def add_widget_with_logging(layout, widget):
       layout.addWidget(widget)
       print(f"Added {widget.__class__.__name__} to {layout.__class__.__name__}")
   ```

### For Bug Reports

1. **Capture hierarchy**:
   ```python
   from debug_helpers import dump_widget_tree
   dump_widget_tree(main_window, verbose=True)
   # Copy output to bug report
   ```

2. **Screenshot with GammaRay**:
   - Take screenshot of widget tree
   - Highlight problematic widget
   - Include in bug report

3. **Export properties**:
   - In GammaRay, select widget
   - File → Export Object → JSON
   - Attach to bug report

## Troubleshooting Inspector Tools

### GammaRay won't attach

**Symptom**: "Failed to inject into process"

**Solutions**:
- Ensure Qt versions match (GammaRay Qt == your app's PyQt6 Qt)
- Run as administrator/sudo if needed
- Use launcher mode instead of attach: `gammaray python app.py`

### Qt Creator doesn't show QML/Widget Debugger

**Symptom**: Debugger views menu is grayed out

**Solutions**:
- Ensure debugging mode is active (F5), not just run mode
- Install Qt Creator Debugger plugin if missing
- Use at least Qt Creator 4.12+

### Runtime Inspector crashes app

**Symptom**: Opening RuntimeInspector causes crash

**Solutions**:
- Don't inspect widget while it's being destroyed
- Add `try/except` around widget access in inspector
- Pause auto-refresh during heavy operations

## Resources

- **GammaRay Manual**: https://github.com/KDAB/GammaRay/wiki
- **Qt Creator Debugger**: https://doc.qt.io/qtcreator/creator-debugging-qml.html
- **Qt Debug Output**: https://doc.qt.io/qt-6/debug.html
- **Qt Logging Framework**: https://doc.qt.io/qt-6/qloggingcategory.html

---

**Created**: 2026-02-24
**Developer**: Marcus Daley
**Purpose**: Advanced Qt debugging for professional-grade development
