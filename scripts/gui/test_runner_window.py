# test_runner_window.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Visual test runner window for executing pytest tests with real-time status updates

"""
PyQt6 visual test runner for the ClaudeSkills project.

Provides a themed QMainWindow that discovers pytest tests, runs them via QProcess,
and displays live results in a table with colored status indicators. Supports
selective test execution via checkboxes and displays raw pytest output in a console.

Usage::

    from gui.test_runner_window import TestRunnerWindow

    window = TestRunnerWindow()
    window.show()
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QProcess, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.constants import (
    DARK_PANEL,
    FONT_FAMILY,
    GOLD,
    HEADER_BG,
    INTEL_APPROVED_COLOR,
    INTEL_PENDING_COLOR,
    INTEL_REFACTORING_COLOR,
    INTEL_REJECTED_COLOR,
    MID_PANEL,
    MONO_FONT,
    NAVY,
    PARCHMENT,
    TEXT_WARNING,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
PYTHON_EXE = r"C:\Users\daley\AppData\Local\Programs\Python\Launcher\py.exe"
TESTS_DIR = Path("C:/ClaudeSkills/tests")
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700

# Status icons (Unicode symbols)
ICON_RUNNING = "\u23F3"  # Hourglass
ICON_PASSED = "\u2713"  # Check mark
ICON_FAILED = "\u2717"  # X mark
ICON_ERROR = "\u26A0"  # Warning sign
ICON_SKIPPED = "\u23ED"  # Skip forward

# Status colors (from constants)
COLOR_RUNNING = INTEL_PENDING_COLOR  # Dark orange
COLOR_PASSED = INTEL_APPROVED_COLOR  # Lime green
COLOR_FAILED = INTEL_REJECTED_COLOR  # Crimson
COLOR_ERROR = TEXT_WARNING  # Gold
COLOR_SKIPPED = INTEL_REFACTORING_COLOR  # Purple

# Pytest result regex patterns
PATTERN_TEST_RESULT = re.compile(
    r"^([\w/\\:.-]+)::([\w:]+)\s+(PASSED|FAILED|ERROR|SKIPPED)\s*(?:\[(\d+)%\])?\s*(?:in\s+([\d.]+)s)?",
)
PATTERN_DURATION = re.compile(r"in\s+([\d.]+)s")
PATTERN_SUMMARY = re.compile(
    r"=+\s*(\d+)\s+(?:passed|failed|errors?|skipped)\s*(?:,\s*(\d+)\s+(?:passed|failed|errors?|skipped)\s*)*.*in\s+([\d.]+)s",
)


# ---------------------------------------------------------------------------
# Test runner window
# ---------------------------------------------------------------------------
class TestRunnerWindow(QMainWindow):
    """Visual test runner window for pytest tests.

    Signals
    -------
    test_started(str):
        Emitted when a test begins execution.
    test_completed(str, str):
        Emitted when a test completes with result (test_name, status).
    all_tests_completed():
        Emitted when the entire test run finishes.
    """

    test_started = pyqtSignal(str)
    test_completed = pyqtSignal(str, str)
    all_tests_completed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._is_running = False
        self._test_results: dict[str, dict[str, Any]] = {}
        self._start_time: datetime | None = None
        self._total_tests = 0
        self._completed_tests = 0

        self.setWindowTitle("Pipeline Test Runner")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # QProcess for running pytest
        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)

        # Timer for uptime display
        self._uptime_timer = QTimer(self)
        self._uptime_timer.setInterval(100)
        self._uptime_timer.timeout.connect(self._update_uptime)

        self._build_ui()
        self._discover_tests()

    # =====================================================================
    # UI construction
    # =====================================================================

    def _build_ui(self) -> None:
        """Construct all child widgets and lay them out."""
        central = QWidget(self)
        central.setStyleSheet(f"background-color: {NAVY};")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header bar
        root_layout.addWidget(self._build_header())

        # Main splitter (test tree | results + console)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_test_tree_panel())
        splitter.addWidget(self._build_results_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root_layout.addWidget(splitter, stretch=1)

        # Footer summary bar
        root_layout.addWidget(self._build_summary_bar())

    def _build_header(self) -> QWidget:
        """Build the header bar with title and action buttons."""
        header = QWidget()
        header.setStyleSheet(f"background-color: {HEADER_BG};")
        header.setFixedHeight(80)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        # Title and subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("Pipeline Test Runner")
        title.setStyleSheet(
            f"color: {GOLD}; font-size: 20px; font-weight: bold; "
            f"font-family: '{FONT_FAMILY}';"
        )
        title_layout.addWidget(title)

        self._subtitle = QLabel("0 tests discovered")
        self._subtitle.setStyleSheet(
            f"color: {PARCHMENT}; font-size: 12px; font-family: '{FONT_FAMILY}';"
        )
        title_layout.addWidget(self._subtitle)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Run All button
        self._run_all_btn = QPushButton("Run All")
        self._run_all_btn.setFixedSize(120, 40)
        self._run_all_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {GOLD};
                color: {NAVY};
                border: none;
                border-radius: 4px;
                font-family: '{FONT_FAMILY}';
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PARCHMENT};
            }}
            QPushButton:disabled {{
                background-color: {MID_PANEL};
                color: {PARCHMENT};
            }}
            """
        )
        self._run_all_btn.clicked.connect(self._on_run_all)
        layout.addWidget(self._run_all_btn)

        # Run Selected button
        self._run_selected_btn = QPushButton("Run Selected")
        self._run_selected_btn.setFixedSize(120, 40)
        self._run_selected_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {MID_PANEL};
                color: {PARCHMENT};
                border: 1px solid {GOLD};
                border-radius: 4px;
                font-family: '{FONT_FAMILY}';
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {GOLD};
                color: {NAVY};
            }}
            QPushButton:disabled {{
                background-color: {MID_PANEL};
                color: {PARCHMENT};
                border-color: {MID_PANEL};
            }}
            """
        )
        self._run_selected_btn.clicked.connect(self._on_run_selected)
        layout.addWidget(self._run_selected_btn)

        return header

    def _build_test_tree_panel(self) -> QWidget:
        """Build the test discovery tree panel."""
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {NAVY};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(8)

        # Panel label
        label = QLabel("Test Discovery")
        label.setStyleSheet(
            f"color: {GOLD}; font-size: 14px; font-weight: bold; "
            f"font-family: '{FONT_FAMILY}';"
        )
        layout.addWidget(label)

        # Test tree
        self._test_tree = QTreeWidget()
        self._test_tree.setHeaderLabels(["Test Name"])
        self._test_tree.setStyleSheet(
            f"""
            QTreeWidget {{
                background-color: {DARK_PANEL};
                color: {PARCHMENT};
                border: 1px solid {GOLD};
                font-family: '{FONT_FAMILY}';
                font-size: 12px;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {MID_PANEL};
            }}
            QTreeWidget::item:selected {{
                background-color: {GOLD};
                color: {NAVY};
            }}
            """
        )
        layout.addWidget(self._test_tree, stretch=1)

        return panel

    def _build_results_panel(self) -> QWidget:
        """Build the results table and console output panel."""
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {NAVY};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 8, 8, 8)
        layout.setSpacing(8)

        # Results label
        label = QLabel("Live Results")
        label.setStyleSheet(
            f"color: {GOLD}; font-size: 14px; font-weight: bold; "
            f"font-family: '{FONT_FAMILY}';"
        )
        layout.addWidget(label)

        # Results table (4 columns: Icon, Test Name, Duration, Result)
        self._results_table = QTableWidget(0, 4)
        self._results_table.setHorizontalHeaderLabels(
            ["Status", "Test Name", "Duration", "Result"]
        )
        self._results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._results_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._results_table.verticalHeader().setVisible(False)
        self._results_table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {DARK_PANEL};
                color: {PARCHMENT};
                border: 1px solid {GOLD};
                gridline-color: {MID_PANEL};
                font-family: {MONO_FONT};
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: {HEADER_BG};
                color: {GOLD};
                border: 1px solid {GOLD};
                padding: 6px;
                font-family: '{FONT_FAMILY}';
                font-size: 11px;
                font-weight: bold;
            }}
            """
        )

        header = self._results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._results_table, stretch=2)

        # Console output label
        console_label = QLabel("Console Output")
        console_label.setStyleSheet(
            f"color: {GOLD}; font-size: 14px; font-weight: bold; "
            f"font-family: '{FONT_FAMILY}';"
        )
        layout.addWidget(console_label)

        # Console output
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {DARK_PANEL};
                color: {PARCHMENT};
                border: 1px solid {GOLD};
                font-family: {MONO_FONT};
                font-size: 10px;
            }}
            """
        )
        mono_font = QFont("Consolas", 10)
        self._console.setFont(mono_font)
        layout.addWidget(self._console, stretch=1)

        return panel

    def _build_summary_bar(self) -> QWidget:
        """Build the footer summary bar with counts and progress."""
        footer = QWidget()
        footer.setStyleSheet(f"background-color: {HEADER_BG};")
        footer.setFixedHeight(60)

        layout = QVBoxLayout(footer)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(4)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {DARK_PANEL};
                border: 1px solid {GOLD};
                border-radius: 4px;
                text-align: center;
                color: {PARCHMENT};
                font-family: '{FONT_FAMILY}';
                font-size: 11px;
            }}
            QProgressBar::chunk {{
                background-color: {GOLD};
                border-radius: 3px;
            }}
            """
        )
        layout.addWidget(self._progress_bar)

        # Summary label
        self._summary_label = QLabel("Ready")
        self._summary_label.setStyleSheet(
            f"color: {PARCHMENT}; font-size: 12px; font-family: '{FONT_FAMILY}';"
        )
        layout.addWidget(self._summary_label)

        return footer

    # =====================================================================
    # Test discovery
    # =====================================================================

    def _discover_tests(self) -> None:
        """Discover all pytest tests using --collect-only."""
        if not TESTS_DIR.exists():
            self._append_console(f"[ERROR] Tests directory not found: {TESTS_DIR}")
            return

        self._append_console(f"Discovering tests in {TESTS_DIR}...")

        try:
            result = subprocess.run(
                [PYTHON_EXE, "-m", "pytest", "--collect-only", "-q"],
                cwd=str(TESTS_DIR.parent),
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse collection output
            lines = result.stdout.split("\n")
            test_files: dict[str, list[str]] = {}

            for line in lines:
                # Match patterns like: tests/test_foo.py::TestClass::test_method
                match = re.match(r"^(tests/[\w_]+\.py)::([\w:]+)", line.strip())
                if match:
                    file_path = match.group(1)
                    test_name = match.group(2)

                    if file_path not in test_files:
                        test_files[file_path] = []
                    test_files[file_path].append(test_name)

            # Populate tree
            self._test_tree.clear()
            total_tests = 0

            for file_path in sorted(test_files.keys()):
                file_item = QTreeWidgetItem(self._test_tree, [Path(file_path).name])
                file_item.setFlags(
                    file_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
                )
                file_item.setCheckState(0, Qt.CheckState.Checked)
                file_item.setData(0, Qt.ItemDataRole.UserRole, file_path)

                for test_name in test_files[file_path]:
                    test_item = QTreeWidgetItem(file_item, [test_name])
                    test_item.setFlags(
                        test_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    test_item.setCheckState(0, Qt.CheckState.Checked)
                    test_item.setData(0, Qt.ItemDataRole.UserRole, f"{file_path}::{test_name}")
                    total_tests += 1

            self._test_tree.expandAll()
            self._total_tests = total_tests
            self._subtitle.setText(f"{total_tests} tests discovered")
            self._append_console(f"Discovered {total_tests} tests across {len(test_files)} files.")

        except subprocess.TimeoutExpired:
            self._append_console("[ERROR] Test discovery timed out.")
        except Exception as exc:
            self._append_console(f"[ERROR] Test discovery failed: {exc}")

    # =====================================================================
    # Test execution
    # =====================================================================

    def _on_run_all(self) -> None:
        """Run all tests."""
        if self._is_running:
            return

        self._run_tests([])

    def _on_run_selected(self) -> None:
        """Run only checked tests."""
        if self._is_running:
            return

        selected_tests = self._get_selected_tests()
        if not selected_tests:
            self._append_console("[WARNING] No tests selected.")
            return

        self._run_tests(selected_tests)

    def _get_selected_tests(self) -> list[str]:
        """Collect all checked test items from the tree."""
        selected: list[str] = []

        for i in range(self._test_tree.topLevelItemCount()):
            file_item = self._test_tree.topLevelItem(i)
            if file_item is None:
                continue

            for j in range(file_item.childCount()):
                test_item = file_item.child(j)
                if test_item is None:
                    continue

                if test_item.checkState(0) == Qt.CheckState.Checked:
                    test_path = test_item.data(0, Qt.ItemDataRole.UserRole)
                    if test_path:
                        selected.append(test_path)

        return selected

    def _run_tests(self, test_paths: list[str]) -> None:
        """Execute pytest with the given test paths.

        Parameters
        ----------
        test_paths:
            List of test paths (e.g., "tests/test_foo.py::test_bar").
            Empty list runs all tests.
        """
        self._is_running = True
        self._start_time = datetime.now(timezone.utc)
        self._completed_tests = 0
        self._test_results.clear()
        self._results_table.setRowCount(0)
        self._console.clear()

        self._run_all_btn.setEnabled(False)
        self._run_selected_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._summary_label.setText("Running tests...")

        self._uptime_timer.start()

        # Build pytest command
        args = ["-m", "pytest", "-v", "--tb=short", "--no-header"]
        if test_paths:
            args.extend(test_paths)
        else:
            args.append(str(TESTS_DIR))

        self._append_console(f"Executing: {PYTHON_EXE} {' '.join(args)}\n")

        self._process.start(PYTHON_EXE, args)

    def _on_stdout(self) -> None:
        """Handle stdout from pytest process."""
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self._append_console(data)
        self._parse_output(data)

    def _on_stderr(self) -> None:
        """Handle stderr from pytest process."""
        data = self._process.readAllStandardError().data().decode("utf-8", errors="replace")
        self._append_console(data)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Handle pytest process completion."""
        self._is_running = False
        self._uptime_timer.stop()

        self._run_all_btn.setEnabled(True)
        self._run_selected_btn.setEnabled(True)

        # Calculate final stats
        passed = sum(1 for r in self._test_results.values() if r.get("status") == "PASSED")
        failed = sum(1 for r in self._test_results.values() if r.get("status") == "FAILED")
        errors = sum(1 for r in self._test_results.values() if r.get("status") == "ERROR")
        skipped = sum(1 for r in self._test_results.values() if r.get("status") == "SKIPPED")
        total = len(self._test_results)

        if total == 0:
            total = self._total_tests

        # Update progress
        if total > 0:
            self._progress_bar.setValue(100)

        # Update summary
        duration = 0.0
        if self._start_time is not None:
            duration = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        summary = f"Passed: {passed} | Failed: {failed} | Errors: {errors} | Skipped: {skipped} | Duration: {duration:.2f}s"

        if failed == 0 and errors == 0:
            verdict = "ALL PASSED"
            verdict_color = COLOR_PASSED
        else:
            verdict = "FAILURES"
            verdict_color = COLOR_FAILED

        self._summary_label.setText(f"{summary} | {verdict}")
        self._summary_label.setStyleSheet(
            f"color: {verdict_color}; font-size: 12px; font-weight: bold; font-family: '{FONT_FAMILY}';"
        )

        self.all_tests_completed.emit()
        self._append_console(f"\n[COMPLETED] Exit code: {exit_code}")

    # =====================================================================
    # Output parsing
    # =====================================================================

    def _parse_output(self, output: str) -> None:
        """Parse pytest verbose output and update results table."""
        lines = output.split("\n")

        for line in lines:
            # Match test result lines (e.g., "tests/test_foo.py::test_bar PASSED")
            match = PATTERN_TEST_RESULT.search(line)
            if match:
                test_path = f"{match.group(1)}::{match.group(2)}"
                status = match.group(3)
                duration_str = match.group(5)

                duration = 0.0
                if duration_str:
                    try:
                        duration = float(duration_str)
                    except ValueError:
                        pass

                self._update_test_result(test_path, status, duration)

    def _update_test_result(self, test_path: str, status: str, duration: float) -> None:
        """Update or add a test result row in the table.

        Parameters
        ----------
        test_path:
            Full test path (e.g., "tests/test_foo.py::TestClass::test_method").
        status:
            Test status (PASSED, FAILED, ERROR, SKIPPED, RUNNING).
        duration:
            Test duration in seconds.
        """
        if test_path not in self._test_results:
            self._test_results[test_path] = {}
            row = self._results_table.rowCount()
            self._results_table.insertRow(row)
            self._test_results[test_path]["row"] = row
        else:
            row = self._test_results[test_path]["row"]

        self._test_results[test_path]["status"] = status
        self._test_results[test_path]["duration"] = duration

        # Determine icon and color
        if status == "PASSED":
            icon = ICON_PASSED
            color = COLOR_PASSED
        elif status == "FAILED":
            icon = ICON_FAILED
            color = COLOR_FAILED
        elif status == "ERROR":
            icon = ICON_ERROR
            color = COLOR_ERROR
        elif status == "SKIPPED":
            icon = ICON_SKIPPED
            color = COLOR_SKIPPED
        else:
            icon = ICON_RUNNING
            color = COLOR_RUNNING

        # Update table cells
        icon_item = QTableWidgetItem(icon)
        icon_item.setForeground(QColor(color))
        icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._results_table.setItem(row, 0, icon_item)

        name_item = QTableWidgetItem(test_path)
        name_item.setForeground(QColor(PARCHMENT))
        self._results_table.setItem(row, 1, name_item)

        duration_item = QTableWidgetItem(f"{duration:.3f}s" if duration > 0 else "")
        duration_item.setForeground(QColor(PARCHMENT))
        duration_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._results_table.setItem(row, 2, duration_item)

        result_item = QTableWidgetItem(status)
        result_item.setForeground(QColor(color))
        result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._results_table.setItem(row, 3, result_item)

        # Auto-scroll to latest result
        self._results_table.scrollToBottom()

        # Update progress
        self._completed_tests = len([r for r in self._test_results.values() if r.get("status") != "RUNNING"])
        if self._total_tests > 0:
            progress = int((self._completed_tests / self._total_tests) * 100)
            self._progress_bar.setValue(progress)

        # Emit signals
        self.test_completed.emit(test_path, status)

    # =====================================================================
    # Console output
    # =====================================================================

    def _append_console(self, text: str) -> None:
        """Append text to the console output (strips ANSI codes)."""
        # Strip ANSI color codes
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        clean_text = ansi_escape.sub("", text)

        self._console.append(clean_text)
        self._console.verticalScrollBar().setValue(
            self._console.verticalScrollBar().maximum()
        )

    # =====================================================================
    # Uptime updates
    # =====================================================================

    def _update_uptime(self) -> None:
        """Update the progress bar text with elapsed time."""
        if self._start_time is None:
            return

        elapsed = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        self._progress_bar.setFormat(f"%p% ({elapsed:.1f}s)")


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = TestRunnerWindow()
    window.show()
    sys.exit(app.exec())
