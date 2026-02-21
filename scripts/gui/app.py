"""
Main entry point for the OwlWatcher GUI application.

Creates and wires together the QApplication, MainWindow, OwlTrayIcon,
WatcherThread, and SecurityEngine.  Handles command-line arguments,
single-instance enforcement, and graceful shutdown.

Launch::

    python C:/ClaudeSkills/scripts/gui/app.py
    python C:/ClaudeSkills/scripts/gui/app.py --visible
    python C:/ClaudeSkills/scripts/gui/app.py --no-tray
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QSharedMemory
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow
from gui.paths import ASSETS_DIR, BASE_DIR
from gui.security_engine import SecurityEngine
from gui.tray_icon import OwlTrayIcon
from gui.watcher_thread import WatcherThread

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TRAY_ICON_SVG = ASSETS_DIR / "owl_tray.svg"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("owl_app")

# ---------------------------------------------------------------------------
# Single-instance guard
# ---------------------------------------------------------------------------
_SHARED_MEMORY_KEY = "OwlWatcher_SingleInstance_Guard"


def _check_single_instance() -> QSharedMemory | None:
    """Attempt to create shared memory for single-instance enforcement.

    Returns the QSharedMemory object on success (caller must keep a
    reference alive), or None if another instance is already running.
    """
    shared = QSharedMemory(_SHARED_MEMORY_KEY)
    if shared.attach():
        # Another instance already attached -- we are the second copy.
        shared.detach()
        return None
    # Create the segment (1 byte is enough as a lock flag).
    if shared.create(1):
        return shared
    # Creation failed for another reason -- allow launch anyway.
    logger.warning("Shared memory create failed: %s", shared.errorString())
    return shared


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="OwlWatcher",
        description="OwlWatcher - File Security Monitor",
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        default=False,
        help="Show the main window on startup (default: start minimised to tray)",
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        default=False,
        help="Disable the system tray icon (window always visible)",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Application wiring
# ---------------------------------------------------------------------------

class OwlWatcherApp:
    """Orchestrates all application components.

    Parameters
    ----------
    args:
        Parsed command-line arguments.
    """

    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self._shared_mem: QSharedMemory | None = None

        # -- Qt application ---------------------------------------------------
        self._app = QApplication.instance() or QApplication(sys.argv)
        self._app.setApplicationName("OwlWatcher")
        self._app.setOrganizationName("ClaudeSkills")

        if TRAY_ICON_SVG.exists():
            self._app.setWindowIcon(QIcon(str(TRAY_ICON_SVG)))

        # -- Security engine (shared instance) --------------------------------
        self._security_engine = SecurityEngine()

        # -- Main window ------------------------------------------------------
        self._window = MainWindow()

        # -- System tray icon -------------------------------------------------
        self._tray: OwlTrayIcon | None = None
        if not args.no_tray:
            self._tray = OwlTrayIcon(self._window)

        # -- Watcher thread ---------------------------------------------------
        self._watcher = WatcherThread()

        # -- Wire signals -----------------------------------------------------
        self._connect_watcher(self._watcher)
        self._connect_tray()

    # -- signal wiring --------------------------------------------------------

    def _connect_watcher(self, watcher: WatcherThread) -> None:
        """Connect a WatcherThread's signals to the window and tray."""
        window = self._window
        tray = self._tray

        # Watcher -> Window
        watcher.file_event.connect(window.file_event_received.emit)
        watcher.security_alert.connect(window.security_alert_received.emit)
        watcher.started_watching.connect(window.watch_started.emit)
        watcher.stopped_watching.connect(window.watch_stopped.emit)
        watcher.error_occurred.connect(self._on_watcher_error)

        if tray is not None:
            watcher.started_watching.connect(lambda: tray.set_watching(True))
            watcher.stopped_watching.connect(lambda: tray.set_watching(False))
            watcher.started_watching.connect(lambda: tray.set_state("alert"))
            watcher.stopped_watching.connect(lambda: tray.set_state("idle"))
            watcher.file_event.connect(lambda _evt: tray.increment_event_count())
            watcher.security_alert.connect(self._on_security_alert_tray)

    def _connect_tray(self) -> None:
        """Connect tray menu actions and window buttons to app actions."""
        window = self._window
        tray = self._tray

        # Window start/stop buttons emit watch_started / watch_stopped.
        # We intercept them to actually start/stop the thread.
        # Note: MainWindow internally connects its own buttons to these
        # signals, so we connect to the signals themselves.
        window.watch_started.connect(self._start_watcher)
        window.watch_stopped.connect(self._stop_watcher)

        if tray is not None:
            tray.start_action.triggered.connect(self._start_watcher)
            tray.stop_action.triggered.connect(self._stop_watcher)
            tray.export_action.triggered.connect(self._export_audit)
            tray.quit_action.triggered.connect(self._quit)

    # -- action handlers ------------------------------------------------------

    def _start_watcher(self) -> None:
        """Start the file watcher thread if not already running."""
        if self._watcher.isRunning():
            return
        # QThread instances cannot be restarted after they finish,
        # so create a fresh instance each time.
        self._watcher = WatcherThread()
        self._connect_watcher(self._watcher)
        self._watcher.start()
        logger.info("Watcher started.")

    def _stop_watcher(self) -> None:
        """Stop the running watcher thread."""
        if not self._watcher.isRunning():
            return
        self._watcher.requestInterruption()
        self._watcher.wait(10_000)
        logger.info("Watcher stopped.")

    def _export_audit(self) -> None:
        """Export a security audit report."""
        try:
            output = BASE_DIR / "security" / "audit_report.md"
            self._security_engine.export_report(output)
            self._window._owl.say(f"Report saved to {output.name}", 4000)
            if self._tray is not None:
                self._tray.notify(
                    "Audit Export",
                    f"Report saved to {output.name}",
                    "info",
                )
            logger.info("Audit report exported to %s", output)
        except Exception as exc:
            logger.error("Failed to export audit: %s", exc)
            self._window._owl.say("Export failed. Check logs.", 4000)

    def _on_watcher_error(self, message: str) -> None:
        """Handle watcher thread errors."""
        logger.error("Watcher error: %s", message)
        self._window._owl.set_state("alarm")
        self._window._owl.say(f"Error: {message}", 6000)

    def _on_security_alert_tray(self, alert: dict[str, Any]) -> None:
        """Show a tray balloon notification for security alerts."""
        if self._tray is None:
            return
        level = alert.get("level", "INFO")
        message = alert.get("message", "Security alert")
        icon_map = {
            "INFO": "info",
            "WARNING": "warning",
            "CRITICAL": "critical",
        }
        icon_type = icon_map.get(level, "info")
        self._tray.notify(f"OwlWatcher [{level}]", message, icon_type)

        if level == "CRITICAL":
            self._tray.set_state("alarm")

    def _quit(self) -> None:
        """Gracefully shut down the application."""
        logger.info("Quit requested -- shutting down.")
        self._stop_watcher()
        self._window.force_close()
        if self._tray is not None:
            self._tray.hide()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    # -- launch ---------------------------------------------------------------

    def run(self) -> int:
        """Launch the application and enter the Qt event loop.

        Returns the process exit code.
        """
        # Show tray icon
        if self._tray is not None:
            self._tray.show()

        # Show or hide the main window
        if self._args.visible or self._args.no_tray:
            self._window.show()

        # Auto-start the watcher
        self._watcher.start()

        # Ensure clean shutdown on app exit
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._on_about_to_quit)

        return app.exec()

    def _on_about_to_quit(self) -> None:
        """Clean up when the application is about to exit."""
        self._stop_watcher()
        if self._tray is not None:
            self._tray.hide()
        logger.info("Application exiting.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for the OwlWatcher GUI."""
    args = _parse_args()

    # Single-instance check (QApplication must exist for QSharedMemory).
    _app_temp = QApplication.instance() or QApplication(sys.argv)
    shared_mem = _check_single_instance()
    if shared_mem is None:
        QMessageBox.warning(
            None,
            "OwlWatcher",
            "Another instance of OwlWatcher is already running.",
        )
        sys.exit(1)

    owl_app = OwlWatcherApp(args)
    # Keep shared memory reference alive for the duration of the process.
    owl_app._shared_mem = shared_mem
    exit_code = owl_app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
