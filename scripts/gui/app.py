# app.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Bootstrap the GUI application and wire all components together via Qt signals

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

# Ensure scripts directory is on sys.path for gui.X imports.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from PyQt6.QtCore import QSettings, QSharedMemory, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from gui.constants import QSETTINGS_APP, QSETTINGS_ORG
from gui.main_window import MainWindow
from gui.owl_state_machine import OwlState, OwlStateMachine
from gui.paths import ASSETS_DIR, BASE_DIR
from gui.security_engine import SecurityEngine
from gui.sound_manager import SoundManager
from gui.speech_messages import get_alert_message, get_message
from gui.tray_icon import OwlTrayIcon
from gui.watcher_thread import WatcherThread
from log_config import configure_logging

from session_observer import SessionObserver
from quad_skill_engine import QuadSkillEngine
from validation_engine import ValidationEngine
from ai_safety_guard import AISafetyGuard
from admin_protocol import AdminControlProtocol
from open_model_manager import OpenModelManager
from agent_runtime import AgentRuntime
from agent_events import (
    AgentStatusChangedEvent,
    SkillRefactorRequestedEvent,
    SkillImprovedEvent,
    SkillRefactorFailedEvent,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TRAY_ICON_SVG = ASSETS_DIR / "owl_tray.svg"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()
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

        # -- Intelligence pipeline (safety guard first) -----------------------
        self._intelligence_enabled = getattr(args, 'intelligence', False)

        # -- Main window ------------------------------------------------------
        self._window = MainWindow()

        # -- Sound manager ----------------------------------------------------
        self._sounds = SoundManager()

        # -- Owl state machine ------------------------------------------------
        self._state_machine = OwlStateMachine()
        self._state_machine.state_changed.connect(self._window._owl.set_state)
        self._state_machine.state_changed.connect(self._on_state_changed)

        # -- System tray icon -------------------------------------------------
        self._tray: OwlTrayIcon | None = None
        if not args.no_tray:
            self._tray = OwlTrayIcon(self._window)
            self._state_machine.state_changed.connect(self._tray.set_state)

        # -- Watcher thread ---------------------------------------------------
        self._watcher = WatcherThread()

        # -- Wire signals -----------------------------------------------------
        self._connect_watcher(self._watcher)
        self._connect_tray()

        # Sound toggle from UI
        self._window.sound_toggled.connect(self._on_sound_toggled)

        # -- Intelligence pipeline (deferred init) ----------------------------
        if self._intelligence_enabled:
            self._init_intelligence_pipeline()

    # -- intelligence pipeline ------------------------------------------------

    def _init_intelligence_pipeline(self) -> None:
        """Initialize the AI self-improvement pipeline modules."""
        import json
        intel_config_path = BASE_DIR / "config" / "intelligence_config.json"
        admin_config_path = BASE_DIR / "config" / "admin_config.json"

        try:
            with intel_config_path.open("r", encoding="utf-8") as f:
                intel_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            intel_config = {}
            logger.warning("Intelligence config not found, using defaults")

        try:
            with admin_config_path.open("r", encoding="utf-8") as f:
                admin_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            admin_config = {}

        # Safety guard FIRST (non-negotiable)
        self._safety_guard = AISafetyGuard()

        # Observation layer
        self._session_observer = SessionObserver(intel_config)

        # Intelligence layer
        self._quad_skill_engine = QuadSkillEngine(intel_config)
        self._validation_engine = ValidationEngine(intel_config)

        # Governance layer
        self._admin_protocol = AdminControlProtocol(admin_config)

        # Integration layer
        self._open_model_manager = OpenModelManager(self._safety_guard)

        # Multi-agent runtime
        self._agent_runtime = AgentRuntime()
        self._agent_runtime.bootstrap()

        # Subscribe to EventBus for agent events -> Qt bridge
        bus = self._agent_runtime.event_bus
        bus.subscribe(AgentStatusChangedEvent, self._on_agent_event)
        bus.subscribe(SkillRefactorRequestedEvent, self._on_agent_event)
        bus.subscribe(SkillImprovedEvent, self._on_agent_event)
        bus.subscribe(SkillRefactorFailedEvent, self._on_agent_event)

        # Wire intelligence signals
        self._connect_intelligence()

        logger.info("Intelligence pipeline initialized.")

    def _connect_intelligence(self) -> None:
        """Wire intelligence pipeline signals."""
        window = self._window

        # File events -> SessionObserver
        # (Hook into the watcher's file_event to feed session observer)
        self._watcher.file_event.connect(self._on_file_event_intelligence)

        # Intelligence panel signals (if panel exists)
        intel_panel = getattr(window, '_intelligence_panel', None)
        if intel_panel is not None:
            intel_panel.skill_approve_requested.connect(self._on_skill_approve)
            intel_panel.skill_reject_requested.connect(self._on_skill_reject)
            intel_panel.rollback_requested.connect(self._on_skill_rollback)

    def _on_file_event_intelligence(self, event: dict) -> None:
        """Route file events through the intelligence pipeline."""
        if not self._intelligence_enabled:
            return

        event_type = event.get("event_type", "")
        file_path = event.get("path", "")

        # Session observation
        session_event = self._session_observer.observe_event(event_type, file_path)
        if session_event is None:
            return

        se_dict = session_event.to_dict()

        # Update state machine
        self._state_machine.command_session_detected()

        # Update UI
        intel_panel = getattr(self._window, '_intelligence_panel', None)
        if intel_panel is not None:
            intel_panel.on_session_event(se_dict)

        # Extract skills on session end
        if session_event.signal.value == "session_end":
            skills = self._quad_skill_engine.extract_from_session(se_dict)
            for skill in skills:
                skill_dict = skill.to_dict()
                self._state_machine.command_skills_extracted()

                if intel_panel is not None:
                    intel_panel.on_skill_extracted(skill_dict)

                # Validate
                report = self._validation_engine.validate(skill_dict)
                report_dict = report.to_dict()

                if intel_panel is not None:
                    intel_panel.on_skill_validated(report_dict)

                # Safety check
                safety_alert = self._safety_guard.check_content(
                    skill_dict.get("execution_logic", "")
                )
                if safety_alert is not None:
                    alert_dict = {
                        "violation": safety_alert.violation.value,
                        "severity": safety_alert.severity,
                        "message": safety_alert.message,
                    }
                    if intel_panel is not None:
                        intel_panel.on_safety_violation(alert_dict)
                    self._state_machine.command_validation_failed()
                    continue

                # Submit for review
                self._admin_protocol.submit_for_review(skill_dict, report_dict)

                # Auto-install approved skills
                if report.result.value == "approved":
                    success = self._open_model_manager.install_skill(skill_dict, report_dict)
                    if success:
                        self._state_machine.command_skills_approved()
                        self._open_model_manager.sync_to_github()
                        self._state_machine.command_sync_complete()

    def _on_skill_approve(self, skill_id: str) -> None:
        """Handle manual skill approval from the UI."""
        if not self._intelligence_enabled:
            return
        success = self._admin_protocol.approve(skill_id, "marcus")
        if success:
            # Load the approved skill and install it
            approved_path = Path("C:/ClaudeSkills/data/approved") / f"{skill_id}.json"
            if approved_path.exists():
                import json
                with approved_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                skill_dict = data.get("skill", {})
                validation_dict = data.get("validation", {})
                self._open_model_manager.install_skill(skill_dict, validation_dict)
                self._state_machine.command_skills_approved()

    def _on_skill_reject(self, skill_id: str) -> None:
        """Handle manual skill rejection from the UI."""
        if not self._intelligence_enabled:
            return
        self._admin_protocol.reject(skill_id, "marcus", "Rejected via UI")

    def _on_skill_rollback(self, skill_id: str) -> None:
        """Handle skill rollback from the UI."""
        if not self._intelligence_enabled:
            return
        self._open_model_manager.rollback(skill_id)

    def _check_idle_sessions(self) -> None:
        """Periodic check for idle sessions that trigger extraction."""
        if not self._intelligence_enabled:
            return
        idle_events = self._session_observer.check_idle_sessions()
        for session_event in idle_events:
            se_dict = session_event.to_dict()
            skills = self._quad_skill_engine.extract_from_session(se_dict)
            for skill in skills:
                skill_dict = skill.to_dict()
                report = self._validation_engine.validate(skill_dict)
                report_dict = report.to_dict()
                self._admin_protocol.submit_for_review(skill_dict, report_dict)
                if report.result.value == "approved":
                    self._open_model_manager.install_skill(skill_dict, report_dict)

    def _on_agent_event(self, event: Any) -> None:
        """Bridge EventBus agent events to Qt UI updates."""
        intel_panel = getattr(self._window, '_intelligence_panel', None)
        if intel_panel is None:
            return

        event_type = type(event).__name__

        if event_type == "AgentStatusChangedEvent":
            # Refresh all agent badges from the registry
            infos = self._agent_runtime.get_status()
            agent_dicts = [
                {"name": info.name, "status": info.status.value}
                for info in infos
            ]
            intel_panel.update_agent_status(agent_dicts)

            # Drive owl state machine for refactoring transitions
            new_status = getattr(event, "new_status", "")
            agent_name = getattr(event, "agent_name", "")
            if agent_name == "refactor":
                if new_status == "running":
                    self._state_machine.command_refactor_started()

        elif event_type == "SkillImprovedEvent":
            skill_name = getattr(event, "skill_name", "")
            new_score = getattr(event, "new_score", 0.0)
            iterations = getattr(event, "iterations_used", 0)
            intel_panel.update_refactor_progress(skill_name, new_score, iterations)
            self._state_machine.command_refactor_complete()

        elif event_type == "SkillRefactorFailedEvent":
            skill_name = getattr(event, "skill_name", "")
            reason = getattr(event, "reason", "")
            intel_panel.update_improvement_trend({
                "skill_name": skill_name,
                "scores": [getattr(event, "last_score", 0.0)],
                "iterations": getattr(event, "attempts", 0),
            })
            self._state_machine.command_refactor_failed()

        elif event_type == "SkillRefactorRequestedEvent":
            skill_name = getattr(event, "skill_name", "")
            score = getattr(event, "current_score", 0.0)
            intel_panel.update_refactor_progress(skill_name, score, 0)

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

        # Watcher -> State machine
        watcher.started_watching.connect(
            self._state_machine.command_start_watching
        )
        watcher.stopped_watching.connect(
            self._state_machine.command_stop_watching
        )
        watcher.file_event.connect(
            lambda _evt: self._state_machine.command_file_event()
        )
        watcher.security_alert.connect(self._on_security_alert_state)

        if tray is not None:
            watcher.started_watching.connect(lambda: tray.set_watching(True))
            watcher.stopped_watching.connect(lambda: tray.set_watching(False))
            watcher.file_event.connect(
                lambda evt: tray.increment_event_count(evt.get("path", ""))
            )
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
        if self._intelligence_enabled:
            self._watcher.file_event.connect(self._on_file_event_intelligence)
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
        self._state_machine.command_security_alert("CRITICAL")
        self._window._owl.say(f"Error: {message}", 6000)

    # State -> sound name mapping
    _STATE_SOUNDS: dict[str, str] = {
        "waking": "startup",
        "alert": "alert",
        "alarm": "alarm",
        "proud": "allclear",
    }

    def _on_state_changed(self, state: str) -> None:
        """Show an ambient speech bubble and play sounds on state change."""
        # Play state-specific sound
        sound_name = self._STATE_SOUNDS.get(state)
        if sound_name:
            self._sounds.play(sound_name)

        # Skip speech for rapid transitions (waking auto-goes to scanning)
        if state in ("waking",):
            return
        msg = get_message(state)
        if msg:
            self._window._owl.say(msg)

    def _on_sound_toggled(self, enabled: bool) -> None:
        """Handle the sound toggle checkbox in the UI."""
        self._sounds.enabled = enabled

    def _on_security_alert_state(self, alert: dict[str, Any]) -> None:
        """Route security alerts through the state machine and show message."""
        level = alert.get("level", "INFO")
        detail = alert.get("message", "")
        self._state_machine.command_security_alert(level)
        msg = get_alert_message(level, detail)
        if msg:
            self._window._owl.say(msg, 8000 if level == "CRITICAL" else 5000)

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
        self._tray.add_unacked_alert(level)

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

        settings = QSettings(QSETTINGS_ORG, QSETTINGS_APP)
        first_run = not settings.value("firstRunComplete_v2", False, type=bool)

        if first_run:
            # First run: show window, start owl sleeping, don't auto-start watcher
            self._window.show()
            self._state_machine.command_go_to_sleep()
            self._window._owl.say(
                "Welcome to OwlWatcher! Click Start to begin watching your files.",
                8000,
            )
            settings.setValue("firstRunComplete_v2", True)
            logger.info("First-run experience shown.")
        else:
            # Normal launch
            if self._args.visible or self._args.no_tray:
                self._window.show()
            # Auto-start the watcher
            self._watcher.start()

        if self._intelligence_enabled:
            self._idle_check_timer = QTimer()
            self._idle_check_timer.setInterval(60000)  # Check every 60s
            self._idle_check_timer.timeout.connect(self._check_idle_sessions)
            self._idle_check_timer.start()

            # Start agent runtime alongside intelligence pipeline
            if hasattr(self, '_agent_runtime'):
                self._agent_runtime.start()
                logger.info("Agent runtime started alongside intelligence pipeline.")

        # Ensure clean shutdown on app exit
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._on_about_to_quit)

        return app.exec()

    def _on_about_to_quit(self) -> None:
        """Clean up when the application is about to exit."""
        self._stop_watcher()
        if hasattr(self, '_agent_runtime'):
            self._agent_runtime.stop()
            logger.info("Agent runtime stopped.")
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
