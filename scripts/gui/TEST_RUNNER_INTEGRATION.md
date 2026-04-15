# Test Runner Window Integration Guide

## Overview

The `TestRunnerWindow` provides a visual interface for running pytest tests with real-time status updates. This document shows how to integrate it into the OwlWatcher main menu.

## Files Created

- `C:\ClaudeSkills\scripts\gui\test_runner_window.py` - Main test runner window implementation

## Features Implemented

### 1. Header Bar
- Title: "Pipeline Test Runner" in GOLD on HEADER_BG
- Dynamic subtitle showing discovered test count
- "Run All" button (GOLD background, NAVY text)
- "Run Selected" button (MID_PANEL background with GOLD border)

### 2. Test Discovery Panel (Left)
- QTreeWidget with file-level and test-level nodes
- Checkboxes for selective execution
- Auto-discovers tests from `C:/ClaudeSkills/tests/test_*.py`
- Uses `pytest --collect-only -q` for discovery
- Groups tests by file with expandable tree structure

### 3. Live Results Panel (Right)
- QTableWidget with 4 columns: Status Icon, Test Name, Duration, Result
- Status icons using Unicode symbols:
  - ⏳ (Hourglass) for RUNNING - Dark orange
  - ✓ (Check) for PASSED - Lime green
  - ✗ (X mark) for FAILED - Crimson
  - ⚠ (Warning) for ERROR - Gold
  - ⏭ (Skip) for SKIPPED - Purple
- Real-time row updates as tests complete
- Auto-scroll to latest result

### 4. Output Console (Bottom)
- QTextEdit with monospace font (Consolas)
- Dark background (DARK_PANEL)
- Parchment text
- Strips ANSI color codes from pytest output
- Auto-scrolls to bottom

### 5. Summary Bar (Footer)
- QProgressBar showing completion percentage
- Dynamic percentage and elapsed time display
- Summary counts: "Passed: X | Failed: X | Errors: X | Skipped: X"
- Final verdict badge: "ALL PASSED" (green) or "FAILURES" (red)

### 6. Test Execution Engine
- Uses QProcess for non-blocking pytest execution
- Command: `py.exe -m pytest -v --tb=short --no-header [paths]`
- Parses pytest verbose output using regex patterns
- Updates table rows in real-time via stdout signal
- Tracks duration per test
- Thread-safe (runs in Qt event loop, no manual threading)

### 7. Standalone Execution
- Window can be launched directly: `python scripts/gui/test_runner_window.py`
- Also importable for integration into main window

## Integration Steps

### Option 1: Add to Tools Menu

Edit `scripts/gui/main_window.py`:

```python
def _build_menu_bar(self) -> None:
    """Build the application menu bar."""
    menu_bar = self.menuBar()

    # File menu
    file_menu = menu_bar.addMenu("&File")
    # ... existing code ...

    # Tools menu (NEW)
    tools_menu = menu_bar.addMenu("&Tools")

    test_runner_action = QAction("&Test Runner...", self)
    test_runner_action.setShortcut("Ctrl+T")
    test_runner_action.triggered.connect(self._on_open_test_runner)
    tools_menu.addAction(test_runner_action)

    # Help menu
    help_menu = menu_bar.addMenu("&Help")
    # ... existing code ...

def _on_open_test_runner(self) -> None:
    """Open the Test Runner window."""
    from gui.test_runner_window import TestRunnerWindow

    self._test_runner = TestRunnerWindow()
    self._test_runner.show()
```

### Option 2: Add to Help Menu

```python
def _build_menu_bar(self) -> None:
    """Build the application menu bar."""
    menu_bar = self.menuBar()

    # ... existing menus ...

    # Help menu
    help_menu = menu_bar.addMenu("&Help")

    test_runner_action = QAction("Run &Tests...", self)
    test_runner_action.triggered.connect(self._on_open_test_runner)
    help_menu.addAction(test_runner_action)

    help_menu.addSeparator()

    about_action = QAction("&About OwlWatcher", self)
    about_action.triggered.connect(self._on_about)
    help_menu.addAction(about_action)
```

### Option 3: Standalone Launch

Launch directly from command line:

```bash
py.exe C:\ClaudeSkills\scripts\gui\test_runner_window.py
```

Or create a shortcut script `run_tests_gui.py`:

```python
# run_tests_gui.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from PyQt6.QtWidgets import QApplication
from gui.test_runner_window import TestRunnerWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestRunnerWindow()
    window.show()
    sys.exit(app.exec())
```

## Architecture Details

### Signal/Slot Design (NO Polling)
- All UI updates driven by Qt signals
- QProcess stdout/stderr connected to parsing slots
- Timer-based uptime updates (not test polling)
- Event-driven test result updates

### Constants
All magic numbers defined at module level:
- `PYTHON_EXE` - Python executable path
- `TESTS_DIR` - Tests directory path
- `MIN_WINDOW_WIDTH` / `MIN_WINDOW_HEIGHT` - Window size constraints
- `ICON_*` - Unicode status icons
- `COLOR_*` - Status colors from theme constants
- `PATTERN_*` - Regex patterns for output parsing

### Type Hints
All methods have complete type annotations following project standards.

### Thread Safety
- QProcess runs in main Qt event loop (no manual threading)
- All UI updates occur on main thread via signals
- No race conditions or thread synchronization needed

## Testing the Window

### Quick Test
```python
import sys
sys.path.insert(0, "C:/ClaudeSkills/scripts")

from PyQt6.QtWidgets import QApplication
from gui.test_runner_window import TestRunnerWindow

app = QApplication([])
window = TestRunnerWindow()
window.show()
sys.exit(app.exec())
```

### Verify Import
```bash
py.exe -c "import sys; sys.path.insert(0, 'C:/ClaudeSkills/scripts'); from gui.test_runner_window import TestRunnerWindow; print('Import OK')"
```

## Known Limitations

1. ANSI color stripping is basic (uses regex, not full ANSI parser)
2. Test duration parsing relies on pytest's `-v` format
3. Large test suites (1000+ tests) may cause UI lag during discovery
4. Window does not persist geometry/state to QSettings (can be added if needed)

## Future Enhancements

1. Test filtering by status (show only failures)
2. Re-run failed tests button
3. Export results to HTML/JSON
4. Integration with CI/CD status
5. Test history tracking across runs
6. Coverage visualization
7. Parallel test execution status

## Dependencies

- PyQt6 (already installed)
- pytest (project dependency)
- Python 3.10+ (project requirement)

All imports are from existing project modules, no new dependencies added.
