# stability_monitor.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Qt-based stability monitor for long-running process health checks with memory/CPU tracking

"""
Stability monitor for tracking process health over extended periods.

Monitors memory usage, CPU utilization, responsiveness, and crash detection
for the OwlWatcher application or any specified process. Emits periodic health
snapshots and generates a final stability report with STABLE/UNSTABLE verdict.

Usage:
    monitor = StabilityMonitor(config={"duration_minutes": 13})
    monitor.health_check.connect(lambda data: print(f"Health: {data}"))
    monitor.anomaly_detected.connect(lambda desc: print(f"ANOMALY: {desc}"))
    monitor.monitor_complete.connect(lambda report: print(report.verdict))
    monitor.start_monitoring()  # Launches OwlWatcher and monitors it
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

DEFAULT_DURATION_MINUTES: int = 13
HEALTH_CHECK_INTERVAL_MS: int = 10_000  # 10 seconds
MEMORY_GROWTH_THRESHOLD: float = 0.50  # 50% growth = anomaly
HANG_TIMEOUT_MS: int = 30_000  # 30 seconds no response = hang

# Try importing psutil for memory tracking
# WHY: We bind `psutil` to None on ImportError instead of leaving the name
# undefined so that test code can patch `testing.stability_monitor.psutil`
# regardless of whether the package is installed in the current environment.
try:
    import psutil  # type: ignore[import-not-found]
    HAS_PSUTIL: bool = True
except ImportError:
    psutil = None  # type: ignore[assignment]
    HAS_PSUTIL: bool = False
    logger.warning("psutil not available - memory tracking disabled")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HealthSnapshot:
    """Immutable snapshot of process health metrics at a point in time."""

    timestamp: str
    memory_rss_mb: float
    memory_vms_mb: float
    cpu_percent: float
    is_alive: bool


@dataclass(frozen=True)
class StabilityReport:
    """Final stability assessment report with verdict and metrics."""

    duration_seconds: float
    memory_initial_mb: float
    memory_peak_mb: float
    memory_final_mb: float
    memory_growth_pct: float
    crash_count: int
    hang_count: int
    anomaly_count: int
    health_snapshots: tuple[HealthSnapshot, ...]
    verdict: str  # "STABLE" or "UNSTABLE"
    details: str


# ---------------------------------------------------------------------------
# StabilityMonitor
# ---------------------------------------------------------------------------

class StabilityMonitor(QObject):
    """
    Monitors process stability over a configured duration.

    Tracks memory usage, CPU utilization, crashes, hangs, and anomalies.
    Emits periodic health checks and generates a final stability report.

    Signals:
        health_check: Emitted every check interval with snapshot dict
        anomaly_detected: Emitted when anomaly found with description
        monitor_complete: Emitted with StabilityReport when monitoring ends
    """

    # Qt signals
    health_check = pyqtSignal(dict)
    anomaly_detected = pyqtSignal(str)
    monitor_complete = pyqtSignal(object)  # StabilityReport

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize stability monitor.

        Args:
            config: Optional configuration dict with keys:
                - duration_minutes: Monitor duration (default: 13)
                - check_interval_ms: Health check interval (default: 10000)
                - memory_threshold: Memory growth threshold (default: 0.50)
                - hang_timeout_ms: Hang detection timeout (default: 30000)
        """
        super().__init__()

        cfg = config or {}
        self._duration_minutes: int = cfg.get("duration_minutes", DEFAULT_DURATION_MINUTES)
        self._check_interval_ms: int = cfg.get("check_interval_ms", HEALTH_CHECK_INTERVAL_MS)
        self._memory_threshold: float = cfg.get("memory_threshold", MEMORY_GROWTH_THRESHOLD)
        self._hang_timeout_ms: int = cfg.get("hang_timeout_ms", HANG_TIMEOUT_MS)

        # Monitoring state
        self._is_monitoring: bool = False
        self._start_time: float = 0.0
        self._process: psutil.Process | None = None  # type: ignore
        self._qprocess: QProcess | None = None
        self._pid: int | None = None

        # Health tracking
        self._snapshots: list[HealthSnapshot] = []
        self._initial_memory_mb: float = 0.0
        self._peak_memory_mb: float = 0.0
        self._crash_count: int = 0
        self._hang_count: int = 0
        self._anomaly_count: int = 0
        self._last_response_time: float = 0.0

        # Timer for periodic health checks
        self._health_timer: QTimer = QTimer(self)
        self._health_timer.timeout.connect(self._check_health)

        logger.info(
            f"StabilityMonitor initialized: duration={self._duration_minutes}min, "
            f"interval={self._check_interval_ms}ms, threshold={self._memory_threshold:.0%}"
        )

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def start_monitoring(self, process_or_pid: int | QProcess | None = None) -> None:
        """
        Start monitoring a process.

        Args:
            process_or_pid:
                - int: Monitor existing process by PID
                - QProcess: Monitor existing QProcess instance
                - None: Launch OwlWatcher app and monitor it

        Raises:
            RuntimeError: If already monitoring or psutil unavailable for PID monitoring
        """
        if self._is_monitoring:
            raise RuntimeError("Already monitoring - stop current session first")

        logger.info(f"Starting stability monitoring for {self._duration_minutes} minutes")

        # Reset state
        self._snapshots.clear()
        self._crash_count = 0
        self._hang_count = 0
        self._anomaly_count = 0
        self._initial_memory_mb = 0.0
        self._peak_memory_mb = 0.0

        # Determine monitoring target
        if isinstance(process_or_pid, int):
            if not HAS_PSUTIL:
                raise RuntimeError("psutil required for PID monitoring but not installed")
            self._pid = process_or_pid
            self._process = psutil.Process(process_or_pid)
            self._qprocess = None
            logger.info(f"Monitoring existing process PID {self._pid}")

        elif isinstance(process_or_pid, QProcess):
            self._qprocess = process_or_pid
            self._pid = process_or_pid.processId() if process_or_pid.state() != QProcess.ProcessState.NotRunning else None
            if HAS_PSUTIL and self._pid:
                self._process = psutil.Process(self._pid)
            else:
                self._process = None
            logger.info(f"Monitoring QProcess (PID {self._pid})")

        else:  # None - launch OwlWatcher
            self._qprocess = QProcess(self)
            self._qprocess.finished.connect(self._on_process_finished)
            self._qprocess.errorOccurred.connect(self._on_process_error)

            # Launch OwlWatcher GUI
            # WHY: Use absolute path to ensure we're launching the correct application
            app_path = "C:/ClaudeSkills/scripts/gui/app.py"
            python_exe = "C:/Users/daley/AppData/Local/Programs/Python/Launcher/py.exe"
            self._qprocess.start(python_exe, [app_path])

            if not self._qprocess.waitForStarted(5000):
                raise RuntimeError("Failed to start OwlWatcher application")

            self._pid = self._qprocess.processId()
            if HAS_PSUTIL:
                self._process = psutil.Process(self._pid)
            else:
                self._process = None

            logger.info(f"Launched OwlWatcher (PID {self._pid})")

        # Record initial state
        self._is_monitoring = True
        self._start_time = time.time()
        self._last_response_time = self._start_time

        # Capture initial memory snapshot
        initial_snapshot = self._capture_snapshot()
        if initial_snapshot:
            self._initial_memory_mb = initial_snapshot.memory_rss_mb
            self._peak_memory_mb = initial_snapshot.memory_rss_mb
            self._snapshots.append(initial_snapshot)
            self.health_check.emit(self._snapshot_to_dict(initial_snapshot))

        # Start periodic health checks
        self._health_timer.start(self._check_interval_ms)
        logger.info("Monitoring started")

    def stop_monitoring(self) -> StabilityReport:
        """
        Stop monitoring and generate final stability report.

        Returns:
            StabilityReport with final verdict and metrics
        """
        if not self._is_monitoring:
            logger.warning("stop_monitoring called but not currently monitoring")
            return self._build_report()

        logger.info("Stopping monitoring")
        self._health_timer.stop()

        # WHY: Capture elapsed time BEFORE flipping _is_monitoring to False so
        # _build_report() can compute duration_seconds from the wall clock
        # rather than falling back to the snapshot timestamp string.
        self._final_duration_seconds: float = self.elapsed_seconds
        self._is_monitoring = False

        # Capture final snapshot
        final_snapshot = self._capture_snapshot()
        if final_snapshot:
            self._snapshots.append(final_snapshot)

        # Generate and emit report
        report = self._build_report()
        self.monitor_complete.emit(report)

        logger.info(f"Monitoring complete - Verdict: {report.verdict}")
        return report

    def get_snapshots(self) -> list[HealthSnapshot]:
        """Get all collected health snapshots."""
        return self._snapshots.copy()

    @property
    def is_monitoring(self) -> bool:
        """Check if currently monitoring."""
        return self._is_monitoring

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed monitoring time in seconds."""
        if not self._is_monitoring:
            return 0.0
        return time.time() - self._start_time

    # -----------------------------------------------------------------------
    # Private implementation
    # -----------------------------------------------------------------------

    def _check_health(self) -> None:
        """
        Periodic health check (QTimer slot).

        Captures memory/CPU snapshot, detects anomalies, and checks for
        hang conditions. Emits health_check signal with current metrics.
        """
        if not self._is_monitoring:
            return

        # Check if monitoring duration exceeded
        elapsed = self.elapsed_seconds
        duration_seconds = self._duration_minutes * 60
        if elapsed >= duration_seconds:
            logger.info(f"Duration exceeded ({elapsed:.1f}s >= {duration_seconds}s)")
            self.stop_monitoring()
            return

        # Capture health snapshot
        snapshot = self._capture_snapshot()
        if not snapshot:
            return

        self._snapshots.append(snapshot)

        # Update peak memory
        if snapshot.memory_rss_mb > self._peak_memory_mb:
            self._peak_memory_mb = snapshot.memory_rss_mb

        # Emit health check signal
        self.health_check.emit(self._snapshot_to_dict(snapshot))

        # Check for process death
        if not snapshot.is_alive:
            anomaly_msg = f"Process not responding at {elapsed:.1f}s"
            logger.warning(anomaly_msg)
            self._anomaly_count += 1
            self._crash_count += 1
            self.anomaly_detected.emit(anomaly_msg)
            self.stop_monitoring()
            return

        # Check for memory growth anomaly
        if self._initial_memory_mb > 0:
            growth_pct = (snapshot.memory_rss_mb - self._initial_memory_mb) / self._initial_memory_mb
            if growth_pct > self._memory_threshold:
                anomaly_msg = (
                    f"Memory growth {growth_pct:.1%} exceeds threshold {self._memory_threshold:.0%} "
                    f"({self._initial_memory_mb:.1f} MB -> {snapshot.memory_rss_mb:.1f} MB)"
                )
                logger.warning(anomaly_msg)
                self._anomaly_count += 1
                self.anomaly_detected.emit(anomaly_msg)

        # Check for hang (no response for HANG_TIMEOUT_MS)
        current_time = time.time()
        if snapshot.is_alive:
            self._last_response_time = current_time
        else:
            time_since_response_ms = (current_time - self._last_response_time) * 1000
            if time_since_response_ms > self._hang_timeout_ms:
                anomaly_msg = f"Process hang detected - no response for {time_since_response_ms:.0f}ms"
                logger.warning(anomaly_msg)
                self._hang_count += 1
                self._anomaly_count += 1
                self.anomaly_detected.emit(anomaly_msg)

    def _capture_snapshot(self) -> HealthSnapshot | None:
        """
        Capture current process health snapshot.

        Returns:
            HealthSnapshot with current metrics, or None if capture failed
        """
        timestamp = datetime.now().isoformat()

        # Try psutil first for detailed metrics
        if HAS_PSUTIL and self._process:
            try:
                if not self._process.is_running():
                    return HealthSnapshot(
                        timestamp=timestamp,
                        memory_rss_mb=0.0,
                        memory_vms_mb=0.0,
                        cpu_percent=0.0,
                        is_alive=False
                    )

                mem_info = self._process.memory_info()
                cpu_pct = self._process.cpu_percent(interval=0.1)

                return HealthSnapshot(
                    timestamp=timestamp,
                    memory_rss_mb=mem_info.rss / (1024 * 1024),  # bytes to MB
                    memory_vms_mb=mem_info.vms / (1024 * 1024),
                    cpu_percent=cpu_pct,
                    is_alive=True
                )

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f"Failed to capture psutil metrics: {e}")
                return HealthSnapshot(
                    timestamp=timestamp,
                    memory_rss_mb=0.0,
                    memory_vms_mb=0.0,
                    cpu_percent=0.0,
                    is_alive=False
                )

        # Fall back to QProcess state check (no memory data)
        elif self._qprocess:
            is_alive = self._qprocess.state() != QProcess.ProcessState.NotRunning
            return HealthSnapshot(
                timestamp=timestamp,
                memory_rss_mb=0.0,
                memory_vms_mb=0.0,
                cpu_percent=0.0,
                is_alive=is_alive
            )

        # No monitoring mechanism available
        return None

    def _build_report(self) -> StabilityReport:
        """
        Build final stability report from collected data.

        Returns:
            StabilityReport with verdict and detailed metrics
        """
        # WHY: Prefer the cached final duration captured by stop_monitoring()
        # so the report reflects the actual monitoring window. Fall back to the
        # live elapsed_seconds when called mid-session.
        if self._is_monitoring:
            duration = self.elapsed_seconds
        else:
            duration = getattr(self, "_final_duration_seconds", 0.0)

        final_memory_mb = self._snapshots[-1].memory_rss_mb if self._snapshots else 0.0

        # Calculate memory growth percentage
        memory_growth_pct = 0.0
        if self._initial_memory_mb > 0:
            memory_growth_pct = (self._peak_memory_mb - self._initial_memory_mb) / self._initial_memory_mb

        # Determine verdict
        verdict = "STABLE"
        details_parts = []

        if self._crash_count > 0:
            verdict = "UNSTABLE"
            details_parts.append(f"{self._crash_count} crash(es) detected")

        if self._hang_count > 0:
            verdict = "UNSTABLE"
            details_parts.append(f"{self._hang_count} hang(s) detected")

        if memory_growth_pct > self._memory_threshold:
            verdict = "UNSTABLE"
            details_parts.append(
                f"Memory growth {memory_growth_pct:.1%} exceeds {self._memory_threshold:.0%} threshold"
            )

        if verdict == "STABLE":
            details = f"No anomalies detected over {duration:.1f}s"
        else:
            details = "; ".join(details_parts)

        return StabilityReport(
            duration_seconds=duration,
            memory_initial_mb=self._initial_memory_mb,
            memory_peak_mb=self._peak_memory_mb,
            memory_final_mb=final_memory_mb,
            memory_growth_pct=memory_growth_pct,
            crash_count=self._crash_count,
            hang_count=self._hang_count,
            anomaly_count=self._anomaly_count,
            health_snapshots=tuple(self._snapshots),
            verdict=verdict,
            details=details
        )

    @staticmethod
    def _snapshot_to_dict(snapshot: HealthSnapshot) -> dict[str, Any]:
        """Convert HealthSnapshot to dict for signal emission."""
        return {
            "timestamp": snapshot.timestamp,
            "memory_rss_mb": snapshot.memory_rss_mb,
            "memory_vms_mb": snapshot.memory_vms_mb,
            "cpu_percent": snapshot.cpu_percent,
            "is_alive": snapshot.is_alive
        }

    # -----------------------------------------------------------------------
    # QProcess event handlers
    # -----------------------------------------------------------------------

    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Handle QProcess finished signal."""
        logger.info(f"Process finished: exit_code={exit_code}, status={exit_status}")
        if exit_status == QProcess.ExitStatus.CrashExit:
            self._crash_count += 1
            self._anomaly_count += 1
            anomaly_msg = f"Process crashed with exit code {exit_code}"
            logger.error(anomaly_msg)
            self.anomaly_detected.emit(anomaly_msg)

    def _on_process_error(self, error: QProcess.ProcessError) -> None:
        """Handle QProcess error signal."""
        error_msg = f"Process error: {error}"
        logger.error(error_msg)
        self._crash_count += 1
        self._anomaly_count += 1
        self.anomaly_detected.emit(error_msg)
