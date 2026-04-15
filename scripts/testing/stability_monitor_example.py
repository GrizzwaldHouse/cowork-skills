# stability_monitor_example.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Example usage of StabilityMonitor for OwlWatcher stability testing

"""
Example usage of StabilityMonitor.

Shows how to monitor OwlWatcher for stability over a configured duration,
handle health check signals, detect anomalies, and interpret final reports.
"""

from __future__ import annotations

import sys
sys.path.insert(0, "C:/ClaudeSkills/scripts")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from testing.stability_monitor import StabilityMonitor


def main() -> None:
    """Run stability monitor example."""
    app = QApplication(sys.argv)

    # Create monitor with custom config (1 minute for demo)
    config = {
        "duration_minutes": 1,  # Short duration for demo
        "check_interval_ms": 5_000,  # Check every 5 seconds
        "memory_threshold": 0.50,  # 50% memory growth threshold
    }

    monitor = StabilityMonitor(config=config)

    # Connect to signals
    def on_health_check(data: dict) -> None:
        """Handle periodic health check."""
        print(f"[{data['timestamp']}] Health Check:")
        print(f"  Memory RSS: {data['memory_rss_mb']:.1f} MB")
        print(f"  Memory VMS: {data['memory_vms_mb']:.1f} MB")
        print(f"  CPU: {data['cpu_percent']:.1f}%")
        print(f"  Alive: {data['is_alive']}")

    def on_anomaly(description: str) -> None:
        """Handle anomaly detection."""
        print(f"\n⚠ ANOMALY DETECTED: {description}\n")

    def on_complete(report) -> None:
        """Handle monitoring completion."""
        print("\n" + "=" * 60)
        print("STABILITY REPORT")
        print("=" * 60)
        print(f"Verdict: {report.verdict}")
        print(f"Duration: {report.duration_seconds:.1f}s")
        print(f"Memory Initial: {report.memory_initial_mb:.1f} MB")
        print(f"Memory Peak: {report.memory_peak_mb:.1f} MB")
        print(f"Memory Final: {report.memory_final_mb:.1f} MB")
        print(f"Memory Growth: {report.memory_growth_pct:.1%}")
        print(f"Crashes: {report.crash_count}")
        print(f"Hangs: {report.hang_count}")
        print(f"Anomalies: {report.anomaly_count}")
        print(f"Snapshots: {len(report.health_snapshots)}")
        print(f"Details: {report.details}")
        print("=" * 60)

        # Exit app after report
        QTimer.singleShot(1000, app.quit)

    monitor.health_check.connect(on_health_check)
    monitor.anomaly_detected.connect(on_anomaly)
    monitor.monitor_complete.connect(on_complete)

    print("Starting OwlWatcher stability monitoring...")
    print(f"Duration: {config['duration_minutes']} minute(s)")
    print(f"Check interval: {config['check_interval_ms']} ms")
    print("-" * 60 + "\n")

    # Start monitoring (launches OwlWatcher)
    try:
        monitor.start_monitoring()
    except Exception as e:
        print(f"Failed to start monitoring: {e}")
        return

    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
