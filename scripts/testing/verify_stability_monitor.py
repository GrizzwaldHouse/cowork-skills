# verify_stability_monitor.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Verification script to check StabilityMonitor imports and basic functionality

"""
Quick verification script for StabilityMonitor.

Run this to verify the module loads correctly and basic structure is sound.
"""

from __future__ import annotations

import sys
sys.path.insert(0, "C:/ClaudeSkills/scripts")

try:
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

    print("✓ All imports successful")
    print(f"✓ DEFAULT_DURATION_MINUTES = {DEFAULT_DURATION_MINUTES}")
    print(f"✓ HEALTH_CHECK_INTERVAL_MS = {HEALTH_CHECK_INTERVAL_MS}")
    print(f"✓ MEMORY_GROWTH_THRESHOLD = {MEMORY_GROWTH_THRESHOLD}")
    print(f"✓ HANG_TIMEOUT_MS = {HANG_TIMEOUT_MS}")
    print(f"✓ HAS_PSUTIL = {HAS_PSUTIL}")

    # Test dataclass creation
    snapshot = HealthSnapshot(
        timestamp="2026-04-05T12:00:00",
        memory_rss_mb=100.0,
        memory_vms_mb=200.0,
        cpu_percent=5.0,
        is_alive=True
    )
    print(f"✓ HealthSnapshot created: {snapshot.memory_rss_mb} MB RSS")

    report = StabilityReport(
        duration_seconds=780.0,
        memory_initial_mb=100.0,
        memory_peak_mb=120.0,
        memory_final_mb=115.0,
        memory_growth_pct=0.20,
        crash_count=0,
        hang_count=0,
        anomaly_count=0,
        health_snapshots=(snapshot,),
        verdict="STABLE",
        details="Test report"
    )
    print(f"✓ StabilityReport created: {report.verdict}")

    # Test StabilityMonitor instantiation
    monitor = StabilityMonitor()
    print(f"✓ StabilityMonitor created: is_monitoring={monitor.is_monitoring}")

    print("\n✓ All verifications passed - module is ready to use")

except Exception as e:
    print(f"✗ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
