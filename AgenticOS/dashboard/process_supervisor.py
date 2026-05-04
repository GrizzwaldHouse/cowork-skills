# process_supervisor.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Manage the lifecycle of the supervised uvicorn child process
#          that runs AgenticOS.agentic_server. Captures stdout/stderr
#          to a log file, polls a health URL for readiness, restarts
#          the process on unexpected exit with exponential backoff up
#          to a configurable cap, and shuts the child down cleanly
#          (SIGINT-equivalent first, SIGTERM after a grace period) so
#          a Ctrl+C from the dashboard never leaves an orphan server.

from __future__ import annotations

import logging
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, IO, List, Optional


_logger = logging.getLogger("AgenticOS.dashboard.process_supervisor")


class ProcessSupervisor:
    """Owns one long-running child process and keeps it alive.

    Designed for a single producer (the dashboard main thread) and a
    single background watcher thread that detects unexpected exits.
    Public methods are guarded by a re-entrant lock so a tray-menu
    quit firing simultaneously with a watcher-driven restart cannot
    corrupt internal state.
    """

    def __init__(
        self,
        command: List[str],
        log_path: Path,
        *,
        health_url: Optional[str] = None,
        startup_timeout_s: int = 20,
        poll_interval_s: float = 0.5,
        max_restart_attempts: int = 5,
        restart_backoff_initial_s: float = 1.0,
        restart_backoff_cap_s: float = 30.0,
        graceful_shutdown_timeout_s: float = 5.0,
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
    ) -> None:
        # Captured arguments. Keep them private (single underscore) so
        # callers cannot mutate supervisor state behind our back.
        self._command = list(command)
        self._log_path = log_path
        self._health_url = health_url
        self._startup_timeout_s = startup_timeout_s
        self._poll_interval_s = poll_interval_s
        self._max_restart_attempts = max_restart_attempts
        self._restart_backoff_initial_s = restart_backoff_initial_s
        self._restart_backoff_cap_s = restart_backoff_cap_s
        self._graceful_shutdown_timeout_s = graceful_shutdown_timeout_s
        self._cwd = cwd
        # Defensive copy of env so the caller can keep mutating their
        # own dict without surprising us.
        self._env = dict(env) if env is not None else None

        # Mutable state guarded by _lock.
        self._lock = threading.RLock()
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._log_file: Optional[IO[bytes]] = None
        self._watcher_thread: Optional[threading.Thread] = None
        # Set to True when stop() is called so the watcher knows the
        # next exit is intentional and must not trigger a restart.
        self._intentional_stop = threading.Event()
        # Tracks how many automatic restarts we have performed so the
        # backoff cap is honoured across the whole supervisor lifetime.
        self._restart_attempt = 0
        # Listeners notified on every state transition; used by the
        # dashboard to flip the "server status" indicator dot.
        self._state_listeners: List[Callable[[str], None]] = []

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Spawn the child process and (if configured) wait for ready.

        Returns True only when the process is alive AND, when a health
        URL is configured, the URL has returned 200 within the startup
        timeout. Returns False on any failure so the dashboard can show
        the "server failed to start" dialog instead of a blank window.
        """
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                # Already running; another start would orphan the child.
                _logger.warning(
                    "start() called but child is already alive (pid=%s)",
                    self._process.pid,
                )
                return True

            # Reset restart bookkeeping so a fresh start does not
            # inherit attempts from a previous failed run.
            self._intentional_stop.clear()
            self._restart_attempt = 0

            spawned = self._spawn_locked()
            if not spawned:
                return False

            # Hand off to the watcher thread which will catch crashes
            # and trigger restart attempts in the background.
            self._launch_watcher_locked()

        # Health probing happens outside the lock so the watcher thread
        # is free to react to a crash mid-probe without deadlocking.
        if self._health_url is None:
            self._notify_state("running")
            return True

        ready = self._wait_for_health()
        self._notify_state("running" if ready else "unhealthy")
        return ready

    def stop(self) -> None:
        """Gracefully terminate the child and stop the watcher.

        Safe to call multiple times: subsequent calls are a no-op.
        """
        with self._lock:
            # Mark intent so the watcher does not fight us with a restart.
            self._intentional_stop.set()
            process = self._process

        if process is None:
            return

        # First, ask politely. On Windows, terminate() sends CTRL_BREAK
        # to the process group, which uvicorn translates into a clean
        # FastAPI shutdown via the lifespan handler.
        try:
            self._send_graceful_signal(process)
            process.wait(timeout=self._graceful_shutdown_timeout_s)
        except subprocess.TimeoutExpired:
            # Polite shutdown ran out of time. Escalate.
            _logger.warning(
                "Child pid=%s did not exit within %.1fs; sending kill",
                process.pid,
                self._graceful_shutdown_timeout_s,
            )
            process.kill()
            try:
                process.wait(timeout=self._graceful_shutdown_timeout_s)
            except subprocess.TimeoutExpired:
                _logger.error(
                    "Child pid=%s ignored kill; abandoning handle", process.pid
                )

        with self._lock:
            self._process = None
            if self._log_file is not None:
                # Closing the log file flushes any buffered output and
                # releases the write handle so the user can View Logs
                # immediately after quitting.
                try:
                    self._log_file.close()
                finally:
                    self._log_file = None

        self._notify_state("stopped")

    def is_running(self) -> bool:
        """Return True iff the child process is currently alive."""
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def add_state_listener(self, listener: Callable[[str], None]) -> None:
        """Register a callback for state transitions ("running" / "stopped" / ...).

        Listeners run on whatever thread triggered the transition; they
        must therefore marshal to the UI thread themselves if needed.
        """
        # Append under the lock so a listener firing during start()
        # cannot observe the list mid-mutation.
        with self._lock:
            self._state_listeners.append(listener)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _spawn_locked(self) -> bool:
        """Open the log file and Popen the child. Caller must hold the lock."""
        # Make sure the log directory exists; the very first run sees
        # an empty AgenticOS/logs/ folder.
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            # Append-mode binary: Popen writes raw bytes from the child
            # stdout/stderr streams without re-encoding.
            self._log_file = self._log_path.open("ab", buffering=0)
        except OSError as exc:
            _logger.error("Could not open server log %s: %s", self._log_path, exc)
            return False

        # creationflags lets Windows give the child its own process
        # group, which is what makes graceful CTRL_BREAK shutdowns work.
        creationflags = 0
        if sys.platform == "win32":
            # CREATE_NEW_PROCESS_GROUP = 0x00000200; defining the literal
            # locally keeps the constant out of cross-platform code paths.
            creationflags = 0x00000200

        try:
            self._process = subprocess.Popen(
                self._command,
                stdout=self._log_file,
                stderr=self._log_file,
                stdin=subprocess.DEVNULL,
                cwd=str(self._cwd) if self._cwd is not None else None,
                env=self._env,
                creationflags=creationflags,
            )
        except (OSError, FileNotFoundError) as exc:
            _logger.error("Failed to launch child: %s", exc)
            self._log_file.close()
            self._log_file = None
            return False

        _logger.info(
            "Spawned child pid=%s, cmd=%s", self._process.pid, " ".join(self._command)
        )
        return True

    def _launch_watcher_locked(self) -> None:
        """Start the daemon watcher thread. Caller must hold the lock."""
        # Daemon=True so the dashboard process can exit even if the
        # watcher thread is still asleep between backoff retries.
        self._watcher_thread = threading.Thread(
            target=self._watch_loop,
            name="AgenticOSProcessWatcher",
            daemon=True,
        )
        self._watcher_thread.start()

    def _watch_loop(self) -> None:
        """Background loop that detects unexpected exits and restarts.

        Runs until the supervisor is intentionally stopped or until
        the maximum restart attempts have been exhausted.
        """
        while True:
            # Snapshot the process under the lock so we observe a single
            # consistent value across the wait() and the branching below.
            with self._lock:
                process = self._process
                # If stop() ran or _spawn_locked failed, exit the loop.
                if process is None or self._intentional_stop.is_set():
                    return

            # Block outside the lock so other public methods can run
            # while the child is alive.
            return_code = process.wait()

            # Check intent first: if the dashboard is shutting down we
            # never want to fight it with a restart.
            if self._intentional_stop.is_set():
                return

            with self._lock:
                self._restart_attempt += 1
                attempt = self._restart_attempt
                exhausted = attempt > self._max_restart_attempts

            self._notify_state("crashed")

            _logger.warning(
                "Child exited unexpectedly (rc=%s, attempt=%d/%d)",
                return_code,
                attempt,
                self._max_restart_attempts,
            )

            if exhausted:
                # Too many crashes; bail out so a human can investigate.
                _logger.error(
                    "Restart attempts exhausted; supervisor giving up. "
                    "See %s for failure context.",
                    self._log_path,
                )
                self._notify_state("failed")
                return

            # Exponential backoff capped at the configured ceiling so a
            # broken child never busy-loops the supervisor.
            delay = min(
                self._restart_backoff_initial_s * (2 ** (attempt - 1)),
                self._restart_backoff_cap_s,
            )
            _logger.info("Backing off %.1fs before restart attempt %d", delay, attempt)
            # wait() on the Event so an in-flight stop() can short-circuit
            # the sleep instead of forcing the user to wait it out.
            if self._intentional_stop.wait(timeout=delay):
                return

            with self._lock:
                if self._intentional_stop.is_set():
                    return
                if not self._spawn_locked():
                    # If the respawn itself failed, give up; another
                    # iteration would just spin.
                    self._notify_state("failed")
                    return

            self._notify_state("running")

    def _wait_for_health(self) -> bool:
        """Poll the health URL until it returns 200 or the timeout elapses."""
        # Defensive: callers should only invoke this when health_url is
        # set, but the assertion documents the precondition for readers.
        assert self._health_url is not None
        deadline = time.monotonic() + self._startup_timeout_s

        while time.monotonic() < deadline:
            # If the process died during startup there is no point in
            # continuing to poll.
            with self._lock:
                process = self._process
            if process is None or process.poll() is not None:
                _logger.error("Server exited before health check could pass")
                return False

            try:
                # Short per-request timeout so we revisit the deadline check
                # frequently and do not block on a hung socket.
                with urllib.request.urlopen(self._health_url, timeout=2) as response:
                    if response.status == 200:
                        return True
            except (urllib.error.URLError, OSError):
                # Server not yet listening; wait and retry.
                pass

            time.sleep(self._poll_interval_s)

        _logger.error(
            "Health check at %s did not return 200 within %ds",
            self._health_url,
            self._startup_timeout_s,
        )
        return False

    def _send_graceful_signal(self, process: subprocess.Popen[bytes]) -> None:
        """Ask the child to shut down without forcing it.

        On POSIX this is SIGINT (mirrors the Ctrl+C UX uvicorn expects);
        on Windows it is CTRL_BREAK_EVENT, which only works because we
        spawned the child in its own process group.
        """
        if sys.platform == "win32":
            # CTRL_BREAK_EVENT is delivered to every process in the group;
            # uvicorn's signal handler treats it as a normal shutdown.
            process.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        else:
            process.send_signal(signal.SIGINT)

    def _notify_state(self, state: str) -> None:
        """Fan out a state transition to every registered listener."""
        # Snapshot under the lock so listeners added concurrently do not
        # cause a "dictionary changed size during iteration" style bug.
        with self._lock:
            listeners = list(self._state_listeners)
        for listener in listeners:
            try:
                listener(state)
            except Exception as exc:
                # Listeners must never break the supervisor; log and continue.
                _logger.warning("State listener raised: %s", exc)
