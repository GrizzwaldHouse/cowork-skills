# test_process_supervisor.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Unit tests for ProcessSupervisor that drive the lifecycle
#          using a benign Python one-liner as the "server". No
#          uvicorn, no FastAPI, no network: each test crafts a child
#          process whose exit conditions exercise the supervisor's
#          start/stop/restart paths.

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

from AgenticOS.dashboard.process_supervisor import ProcessSupervisor


# Use the active interpreter so the tests work inside any virtualenv.
PYTHON = sys.executable or "python"


def _sleep_command(duration: float) -> list[str]:
    """Build a portable child command that sleeps for ``duration`` seconds.

    Implemented as a fresh ``-c`` invocation so the supervisor really
    is launching an external process (and not just calling time.sleep
    in the same interpreter).
    """
    return [PYTHON, "-c", f"import time; time.sleep({duration})"]


def _exit_command(code: int) -> list[str]:
    """Build a child that exits immediately with ``code``.

    Used to drive the supervisor's "process died unexpectedly" path
    without waiting on a sleep.
    """
    return [PYTHON, "-c", f"import sys; sys.exit({code})"]


# ---------------------------------------------------------------------------
# Lifecycle: start a long-lived child, observe is_running, stop it cleanly.
# ---------------------------------------------------------------------------

def test_start_and_stop_long_lived_child(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "server.log"
    supervisor = ProcessSupervisor(
        # Sleep long enough that the test never races the supervisor.
        command=_sleep_command(30),
        log_path=log_path,
        # No health URL: the test is purely about the process handle.
        health_url=None,
        startup_timeout_s=2,
        poll_interval_s=0.1,
        max_restart_attempts=0,
        graceful_shutdown_timeout_s=2.0,
    )

    # start() returns True even without a health URL because the
    # contract is "process spawned successfully".
    assert supervisor.start() is True
    assert supervisor.is_running() is True

    # The log file is created the moment Popen opens it for writing.
    assert log_path.exists(), "log file should be created on spawn"

    supervisor.stop()
    assert supervisor.is_running() is False


# ---------------------------------------------------------------------------
# Health probe failure path: child runs but URL never responds.
# ---------------------------------------------------------------------------

def test_start_returns_false_when_health_url_unreachable(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "server.log"
    # Bind to a port nobody is listening on so the urllib probe always
    # gets a connection-refused. The actual child happily sleeps.
    supervisor = ProcessSupervisor(
        command=_sleep_command(10),
        log_path=log_path,
        health_url="http://127.0.0.1:1/healthz",
        # Keep timeout tight so the test runs quickly.
        startup_timeout_s=2,
        poll_interval_s=0.1,
        max_restart_attempts=0,
        graceful_shutdown_timeout_s=2.0,
    )

    try:
        # health URL never returns 200, so start() must report failure.
        assert supervisor.start() is False
    finally:
        # Clean up the still-running sleeper so the test process exits.
        supervisor.stop()


# ---------------------------------------------------------------------------
# Restart-on-crash: max_restart_attempts=0 means a single crash is final.
# ---------------------------------------------------------------------------

def test_supervisor_does_not_restart_when_disabled(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "server.log"
    supervisor = ProcessSupervisor(
        command=_exit_command(1),
        log_path=log_path,
        health_url=None,
        startup_timeout_s=1,
        poll_interval_s=0.1,
        max_restart_attempts=0,
        restart_backoff_initial_s=0.05,
        restart_backoff_cap_s=0.1,
        graceful_shutdown_timeout_s=1.0,
    )

    # The child exits as soon as it spawns; start() returns True
    # because spawning succeeded even though the process is short.
    assert supervisor.start() is True

    # Give the watcher thread a moment to observe the exit and decide
    # whether to restart. With max_restart_attempts=0 it must give up.
    time.sleep(1.0)

    assert supervisor.is_running() is False
    # Calling stop() after a self-terminating child must be a no-op.
    supervisor.stop()


# ---------------------------------------------------------------------------
# State listener fan-out: every transition must reach registered listeners.
# ---------------------------------------------------------------------------

def test_state_listener_receives_running_and_stopped(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "server.log"
    supervisor = ProcessSupervisor(
        command=_sleep_command(5),
        log_path=log_path,
        health_url=None,
        startup_timeout_s=2,
        poll_interval_s=0.1,
        max_restart_attempts=0,
        graceful_shutdown_timeout_s=2.0,
    )

    received: list[str] = []
    # Registering before start ensures we see the "running" notification.
    supervisor.add_state_listener(received.append)

    assert supervisor.start() is True
    supervisor.stop()

    # Order is start-driven (running) then stop-driven (stopped). The
    # test does not assert on uniqueness because a real implementation
    # may also emit transient states; we just need both terminal ones.
    assert "running" in received
    assert "stopped" in received
