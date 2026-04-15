# test_stability_monitor.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Comprehensive unit tests for StabilityMonitor with mocked psutil and QProcess

"""
Unit tests for StabilityMonitor.

Tests cover initialization, health snapshot capture, anomaly detection,
verdict calculation, and graceful fallback when psutil is unavailable.
Uses mocks to avoid actually running 13-minute stability tests.
"""

from __future__ import annotations

import sys
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

# Ensure ClaudeSkills paths are available for imports
sys.path.insert(0, "C:/ClaudeSkills")
sys.path.insert(0, "C:/ClaudeSkills/scripts")

# Initialize PyQt6 application for QObject tests
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QProcess

_app = QApplication.instance() or QApplication(sys.argv)

# Import module under test
from testing.stability_monitor import (
    StabilityMonitor,
    HealthSnapshot,
    StabilityReport,
    DEFAULT_DURATION_MINUTES,
    HEALTH_CHECK_INTERVAL_MS,
    MEMORY_GROWTH_THRESHOLD,
    HANG_TIMEOUT_MS,
    HAS_PSUTIL,
)


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

class TestStabilityMonitor(unittest.TestCase):
    """Test cases for StabilityMonitor class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.monitor = StabilityMonitor()

    def tearDown(self) -> None:
        """Clean up after tests."""
        if self.monitor.is_monitoring:
            self.monitor.stop_monitoring()

    # -----------------------------------------------------------------------
    # Test 1: Initial state
    # -----------------------------------------------------------------------

    def test_initial_state(self) -> None:
        """Test that monitor starts in correct initial state."""
        self.assertFalse(self.monitor.is_monitoring, "Should not be monitoring initially")
        self.assertEqual(self.monitor.elapsed_seconds, 0.0, "Elapsed time should be zero")
        self.assertEqual(len(self.monitor.get_snapshots()), 0, "Should have no snapshots")

    # -----------------------------------------------------------------------
    # Test 2: Start with PID
    # -----------------------------------------------------------------------

    @patch("testing.stability_monitor.psutil")
    @patch("testing.stability_monitor.HAS_PSUTIL", True)
    def test_start_with_pid(self, mock_psutil: Mock) -> None:
        """Test starting monitoring with a PID."""
        # Mock psutil.Process
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024, vms=200 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process

        # Start monitoring with fake PID
        test_pid = 12345
        self.monitor.start_monitoring(test_pid)

        # Verify state
        self.assertTrue(self.monitor.is_monitoring, "Should be monitoring")
        self.assertGreater(self.monitor.elapsed_seconds, 0.0, "Should have elapsed time")
        self.assertGreater(len(self.monitor.get_snapshots()), 0, "Should have initial snapshot")

        # Verify psutil.Process called with correct PID
        mock_psutil.Process.assert_called_with(test_pid)

    # -----------------------------------------------------------------------
    # Test 3: HealthSnapshot structure
    # -----------------------------------------------------------------------

    def test_health_snapshot_structure(self) -> None:
        """Test that HealthSnapshot has all required fields."""
        snapshot = HealthSnapshot(
            timestamp="2026-04-05T12:00:00",
            memory_rss_mb=100.5,
            memory_vms_mb=200.3,
            cpu_percent=12.4,
            is_alive=True
        )

        self.assertEqual(snapshot.timestamp, "2026-04-05T12:00:00")
        self.assertAlmostEqual(snapshot.memory_rss_mb, 100.5, places=1)
        self.assertAlmostEqual(snapshot.memory_vms_mb, 200.3, places=1)
        self.assertAlmostEqual(snapshot.cpu_percent, 12.4, places=1)
        self.assertTrue(snapshot.is_alive)

    # -----------------------------------------------------------------------
    # Test 4: Stable verdict
    # -----------------------------------------------------------------------

    @patch("testing.stability_monitor.psutil")
    @patch("testing.stability_monitor.HAS_PSUTIL", True)
    def test_stable_verdict(self, mock_psutil: Mock) -> None:
        """Test STABLE verdict when no anomalies detected."""
        # Mock process with low, stable memory
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024, vms=200 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process

        # Start and immediately stop (no time for anomalies)
        self.monitor.start_monitoring(12345)
        report = self.monitor.stop_monitoring()

        # Verify stable verdict
        self.assertEqual(report.verdict, "STABLE", "Should be STABLE with no anomalies")
        self.assertEqual(report.crash_count, 0, "Should have no crashes")
        self.assertEqual(report.hang_count, 0, "Should have no hangs")
        self.assertLess(report.memory_growth_pct, MEMORY_GROWTH_THRESHOLD, "Memory growth below threshold")

    # -----------------------------------------------------------------------
    # Test 5: Unstable crash verdict
    # -----------------------------------------------------------------------

    @patch("testing.stability_monitor.psutil")
    @patch("testing.stability_monitor.HAS_PSUTIL", True)
    def test_unstable_crash_verdict(self, mock_psutil: Mock) -> None:
        """Test UNSTABLE verdict when crash detected."""
        # Mock process that dies
        mock_process = Mock()
        mock_process.is_running.return_value = False  # Process not running
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024, vms=200 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 0.0
        mock_psutil.Process.return_value = mock_process

        # Manually inject crash
        self.monitor.start_monitoring(12345)
        self.monitor._crash_count = 1
        self.monitor._anomaly_count = 1
        report = self.monitor.stop_monitoring()

        # Verify unstable verdict
        self.assertEqual(report.verdict, "UNSTABLE", "Should be UNSTABLE with crash")
        self.assertEqual(report.crash_count, 1, "Should have 1 crash")
        self.assertIn("crash", report.details.lower(), "Details should mention crash")

    # -----------------------------------------------------------------------
    # Test 6: Unstable memory verdict
    # -----------------------------------------------------------------------

    @patch("testing.stability_monitor.psutil")
    @patch("testing.stability_monitor.HAS_PSUTIL", True)
    def test_unstable_memory_verdict(self, mock_psutil: Mock) -> None:
        """Test UNSTABLE verdict when memory growth exceeds threshold."""
        # Mock process with high memory growth
        mock_process = Mock()
        mock_process.is_running.return_value = True

        # Initial: 100 MB, Peak: 200 MB (100% growth > 50% threshold)
        initial_mem = 100 * 1024 * 1024
        peak_mem = 200 * 1024 * 1024

        mock_process.memory_info.return_value = Mock(rss=initial_mem, vms=200 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process

        # Start monitoring
        self.monitor.start_monitoring(12345)

        # Simulate memory growth
        mock_process.memory_info.return_value = Mock(rss=peak_mem, vms=300 * 1024 * 1024)
        self.monitor._peak_memory_mb = peak_mem / (1024 * 1024)

        report = self.monitor.stop_monitoring()

        # Verify unstable verdict
        self.assertEqual(report.verdict, "UNSTABLE", "Should be UNSTABLE with high memory growth")
        self.assertGreater(report.memory_growth_pct, MEMORY_GROWTH_THRESHOLD, "Memory growth should exceed threshold")
        self.assertIn("memory", report.details.lower(), "Details should mention memory")

    # -----------------------------------------------------------------------
    # Test 7: Unstable hang verdict
    # -----------------------------------------------------------------------

    @patch("testing.stability_monitor.psutil")
    @patch("testing.stability_monitor.HAS_PSUTIL", True)
    def test_unstable_hang_verdict(self, mock_psutil: Mock) -> None:
        """Test UNSTABLE verdict when hang detected."""
        # Mock process
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024, vms=200 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process

        # Manually inject hang
        self.monitor.start_monitoring(12345)
        self.monitor._hang_count = 1
        self.monitor._anomaly_count = 1
        report = self.monitor.stop_monitoring()

        # Verify unstable verdict
        self.assertEqual(report.verdict, "UNSTABLE", "Should be UNSTABLE with hang")
        self.assertEqual(report.hang_count, 1, "Should have 1 hang")
        self.assertIn("hang", report.details.lower(), "Details should mention hang")

    # -----------------------------------------------------------------------
    # Test 8: StabilityReport structure
    # -----------------------------------------------------------------------

    def test_report_structure(self) -> None:
        """Test that StabilityReport has all required fields."""
        snapshots = (
            HealthSnapshot("2026-04-05T12:00:00", 100.0, 200.0, 5.0, True),
            HealthSnapshot("2026-04-05T12:01:00", 110.0, 210.0, 6.0, True),
        )

        report = StabilityReport(
            duration_seconds=780.0,
            memory_initial_mb=100.0,
            memory_peak_mb=110.0,
            memory_final_mb=110.0,
            memory_growth_pct=0.10,
            crash_count=0,
            hang_count=0,
            anomaly_count=0,
            health_snapshots=snapshots,
            verdict="STABLE",
            details="No anomalies detected"
        )

        self.assertEqual(report.duration_seconds, 780.0)
        self.assertEqual(report.memory_initial_mb, 100.0)
        self.assertEqual(report.memory_peak_mb, 110.0)
        self.assertEqual(report.memory_final_mb, 110.0)
        self.assertAlmostEqual(report.memory_growth_pct, 0.10, places=2)
        self.assertEqual(report.crash_count, 0)
        self.assertEqual(report.hang_count, 0)
        self.assertEqual(report.anomaly_count, 0)
        self.assertEqual(len(report.health_snapshots), 2)
        self.assertEqual(report.verdict, "STABLE")
        self.assertIn("No anomalies", report.details)

    # -----------------------------------------------------------------------
    # Test 9: Stop produces report
    # -----------------------------------------------------------------------

    @patch("testing.stability_monitor.psutil")
    @patch("testing.stability_monitor.HAS_PSUTIL", True)
    def test_stop_produces_report(self, mock_psutil: Mock) -> None:
        """Test that stop_monitoring returns complete StabilityReport."""
        # Mock process
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024, vms=200 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process

        # Start and stop
        self.monitor.start_monitoring(12345)
        report = self.monitor.stop_monitoring()

        # Verify report completeness
        self.assertIsInstance(report, StabilityReport)
        self.assertGreater(report.duration_seconds, 0.0)
        self.assertGreaterEqual(report.memory_initial_mb, 0.0)
        self.assertGreaterEqual(report.memory_peak_mb, 0.0)
        self.assertGreaterEqual(report.memory_final_mb, 0.0)
        self.assertIn(report.verdict, ["STABLE", "UNSTABLE"])
        self.assertIsInstance(report.details, str)
        self.assertGreater(len(report.details), 0)

    # -----------------------------------------------------------------------
    # Test 10: Duration config
    # -----------------------------------------------------------------------

    def test_duration_config(self) -> None:
        """Test that custom duration from config is respected."""
        custom_duration = 5
        custom_config = {"duration_minutes": custom_duration}

        monitor = StabilityMonitor(config=custom_config)

        # Verify internal state (access private attribute for testing)
        self.assertEqual(monitor._duration_minutes, custom_duration, "Should use custom duration")

    # -----------------------------------------------------------------------
    # Test 11: psutil fallback
    # -----------------------------------------------------------------------

    @patch("testing.stability_monitor.HAS_PSUTIL", False)
    def test_psutil_fallback(self) -> None:
        """Test graceful degradation when psutil not available."""
        # Create monitor with psutil disabled
        monitor = StabilityMonitor()

        # Mock QProcess
        mock_qprocess = Mock(spec=QProcess)
        mock_qprocess.state.return_value = QProcess.ProcessState.Running
        mock_qprocess.processId.return_value = 12345

        # Should not raise exception even without psutil
        try:
            monitor.start_monitoring(mock_qprocess)
            self.assertTrue(monitor.is_monitoring, "Should be monitoring even without psutil")

            # Get snapshot - should have zero memory data but valid structure
            snapshots = monitor.get_snapshots()
            self.assertGreater(len(snapshots), 0, "Should have snapshots")

            snapshot = snapshots[0]
            self.assertEqual(snapshot.memory_rss_mb, 0.0, "Memory should be 0 without psutil")
            self.assertEqual(snapshot.memory_vms_mb, 0.0, "Memory should be 0 without psutil")
            self.assertIsInstance(snapshot.is_alive, bool, "is_alive should still be valid")

            report = monitor.stop_monitoring()
            self.assertIsInstance(report, StabilityReport, "Should produce valid report")

        except Exception as e:
            self.fail(f"Should not raise exception without psutil: {e}")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
