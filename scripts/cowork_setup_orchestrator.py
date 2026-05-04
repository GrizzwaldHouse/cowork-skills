# cowork_setup_orchestrator.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Drive Cowork-mode setup with the OwlWatcher GUI as the visible
#          progress display. Reuses the OwlWatcher MainWindow for theming
#          and event-log presentation, and pushes phase events through its
#          existing Qt signals so the bridge stays event-driven (no polling).
#          Headless mode runs the same pipeline without any Qt dependency
#          so the orchestrator works on machines that do not have PyQt6.

"""
Cowork Setup Orchestrator.

Two execution modes:

* GUI mode (default): launches the OwlWatcher MainWindow and runs the
  install pipeline on a QThread worker. Each phase emits Qt signals that
  populate the existing OwlWatcher event log in real time. Requires PyQt6
  and the OwlWatcher gui package.

* Headless mode (--headless or auto-fallback when PyQt6 is missing):
  runs the same pipeline as a plain Python sequence and streams phase
  events to stdout and a log file. No Qt dependency.

Run::

    python C:/ClaudeSkills/scripts/cowork_setup_orchestrator.py
    python C:/ClaudeSkills/scripts/cowork_setup_orchestrator.py --dry-run
    python C:/ClaudeSkills/scripts/cowork_setup_orchestrator.py --headless
"""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

# Ensure scripts/ is on sys.path so 'gui.*' resolves the same way as app.py.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Configuration variables (no hardcoded literals scattered through the file)
# ---------------------------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[1]
SETUP_PS1: Path = REPO_ROOT / "setup.ps1"
SETUP_SH: Path = REPO_ROOT / "setup.sh"
PUBLISH_GUARD_PS1: Path = REPO_ROOT / "scripts" / "publish_guard.ps1"
PUBLISH_GUARD_SH: Path = REPO_ROOT / "scripts" / "publish_guard.sh"
TAXONOMY_FILE: Path = REPO_ROOT / "skills" / "_taxonomy.yaml"
LOG_DIR: Path = REPO_ROOT / "logs"
SETUP_LOG: Path = LOG_DIR / "cowork_setup.log"

WINDOW_TITLE: str = "Cowork Setup - OwlWatcher Progress GUI"
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 800

SEV_INFO: str = "INFO"
SEV_WARNING: str = "WARNING"
SEV_CRITICAL: str = "CRITICAL"

EXPECTED_MARKER_SKILLS: tuple[str, ...] = (
    "brainstorm-artifact",
    "universal-coding-standards",
)

logger = logging.getLogger("cowork_setup")


# ---------------------------------------------------------------------------
# Lazy GUI import (so headless mode works without PyQt6)
# ---------------------------------------------------------------------------
class _GuiBundle:
    """Holds references to PyQt6 and OwlWatcher symbols once imported."""

    def __init__(self) -> None:
        self.available: bool = False
        self.error: Exception | None = None
        self.QObject: Any = None
        self.QThread: Any = None
        self.pyqtSignal: Any = None
        self.QIcon: Any = None
        self.QApplication: Any = None
        self.MainWindow: Any = None
        self.OwlState: Any = None
        self.OwlStateMachine: Any = None
        self.ASSETS_DIR: Path | None = None


def _import_gui() -> _GuiBundle:
    bundle = _GuiBundle()
    try:
        from PyQt6.QtCore import QObject, QThread, pyqtSignal
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        from gui.owl_state_machine import OwlState, OwlStateMachine
        from gui.paths import ASSETS_DIR
    except Exception as exc:                                   # any import failure
        bundle.error = exc
        return bundle
    bundle.available = True
    bundle.QObject = QObject
    bundle.QThread = QThread
    bundle.pyqtSignal = pyqtSignal
    bundle.QIcon = QIcon
    bundle.QApplication = QApplication
    bundle.MainWindow = MainWindow
    bundle.OwlState = OwlState
    bundle.OwlStateMachine = OwlStateMachine
    bundle.ASSETS_DIR = ASSETS_DIR
    return bundle


# ---------------------------------------------------------------------------
# Phase model (Qt-free, used by both modes)
# ---------------------------------------------------------------------------
class PhaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SetupPhase:
    """One ordered step in the Cowork setup pipeline."""

    name: str
    description: str
    command: Sequence[str] = field(default_factory=tuple)
    blocking: bool = True
    cwd: Path | None = None
    status: PhaseStatus = PhaseStatus.PENDING
    output_lines: list[str] = field(default_factory=list)


def _command_exists(name: str) -> bool:
    extensions: tuple[str, ...] = (".exe", ".cmd", ".bat") if os.name == "nt" else ("",)
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        for ext in extensions:
            candidate = Path(path_dir) / f"{name}{ext}"
            if candidate.is_file():
                return True
    return False


def _powershell_invocation(script: Path, *args: str) -> Sequence[str]:
    pwsh_exe = "pwsh" if _command_exists("pwsh") else "powershell"
    return (pwsh_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args)


def build_default_phases() -> list[SetupPhase]:
    """Compose the default Cowork install pipeline."""
    return [
        SetupPhase(
            name="Verify repository",
            description="Confirm we are running inside the repo and the taxonomy file is present.",
        ),
        SetupPhase(
            name="Run publish guard (install mode)",
            description="Soft-scan the repo for redlines before installing skills locally.",
            command=_powershell_invocation(PUBLISH_GUARD_PS1, "-Mode", "install"),
            blocking=False,
            cwd=REPO_ROOT,
        ),
        SetupPhase(
            name="Walk skills tree",
            description="Discover every SKILL.md under skills/ recursively.",
        ),
        SetupPhase(
            name="Install skills to ~/.claude/skills",
            description="Flatten the categorized source tree into the Cowork skills target.",
            command=_powershell_invocation(SETUP_PS1),
            cwd=REPO_ROOT,
        ),
        SetupPhase(
            name="Verify install",
            description="Confirm marker skills landed in the target.",
        ),
    ]


# ---------------------------------------------------------------------------
# In-process phase handlers (Qt-free)
# ---------------------------------------------------------------------------
def _handle_verify_repository(phase: SetupPhase) -> bool:
    if not REPO_ROOT.is_dir():
        phase.output_lines.append(f"Repo root missing: {REPO_ROOT}")
        return False
    if not TAXONOMY_FILE.is_file():
        phase.output_lines.append(f"Taxonomy file missing: {TAXONOMY_FILE}")
        return False
    phase.output_lines.append(f"Repo root: {REPO_ROOT}")
    phase.output_lines.append(f"Taxonomy:  {TAXONOMY_FILE}")
    return True


def _handle_walk_skills(phase: SetupPhase) -> bool:
    skills_root = REPO_ROOT / "skills"
    manifests = list(skills_root.rglob("SKILL.md"))
    manifests = [m for m in manifests if m.parent != skills_root]
    phase.output_lines.append(f"Found {len(manifests)} SKILL.md manifests")
    if not manifests:
        return False
    categories = sorted({m.relative_to(skills_root).parts[0] for m in manifests})
    phase.output_lines.append("Categories: " + ", ".join(categories))
    return True


def _handle_verify_install(phase: SetupPhase) -> bool:
    target = Path.home() / ".claude" / "skills"
    if not target.is_dir():
        phase.output_lines.append(f"Target not found: {target}")
        return False
    missing = [s for s in EXPECTED_MARKER_SKILLS if not (target / s / "SKILL.md").is_file()]
    if missing:
        phase.output_lines.append(f"Missing marker skills: {missing}")
        return False
    phase.output_lines.append(f"Verified marker skills present in {target}")
    return True


IN_PROCESS_HANDLERS: dict[str, Callable[[SetupPhase], bool]] = {
    "Verify repository": _handle_verify_repository,
    "Walk skills tree": _handle_walk_skills,
    "Verify install": _handle_verify_install,
}


# ---------------------------------------------------------------------------
# Pipeline runner (Qt-free, observer-pattern via callbacks)
# ---------------------------------------------------------------------------
class PhaseObserver:
    """Callback surface that GUI and headless modes both implement."""

    def on_phase_started(self, phase: SetupPhase) -> None: ...
    def on_phase_progress(self, phase: SetupPhase, line: str) -> None: ...
    def on_phase_finished(self, phase: SetupPhase) -> None: ...
    def on_pipeline_finished(self, succeeded: int, failed: int, total: int) -> None: ...


def _run_subprocess(phase: SetupPhase, observer: PhaseObserver, dry_run: bool) -> bool:
    if dry_run:
        line = f"DRY RUN: would execute {' '.join(shlex.quote(c) for c in phase.command)}"
        phase.output_lines.append(line)
        observer.on_phase_progress(phase, line)
        return True

    cwd = str(phase.cwd) if phase.cwd else None
    process = subprocess.Popen(                               # noqa: S603
        list(phase.command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.rstrip("\r\n")
        phase.output_lines.append(line)
        observer.on_phase_progress(phase, line)
    process.stdout.close()
    return process.wait() == 0


def run_pipeline(
    phases: list[SetupPhase],
    observer: PhaseObserver,
    dry_run: bool,
) -> tuple[int, int]:
    """Execute the full pipeline. Returns (succeeded, failed)."""
    succeeded = 0
    failed = 0
    for index, phase in enumerate(phases):
        phase.status = PhaseStatus.RUNNING
        observer.on_phase_started(phase)

        try:
            if phase.command:
                ok = _run_subprocess(phase, observer, dry_run)
            else:
                handler = IN_PROCESS_HANDLERS.get(phase.name)
                if handler is None:
                    phase.output_lines.append(
                        f"No in-process handler registered for phase '{phase.name}'."
                    )
                    ok = False
                else:
                    ok = handler(phase)
                    for line in phase.output_lines:
                        observer.on_phase_progress(phase, line)
        except Exception as exc:
            logger.exception("Phase '%s' raised", phase.name)
            phase.output_lines.append(f"EXCEPTION: {exc}")
            ok = False

        phase.status = PhaseStatus.SUCCEEDED if ok else PhaseStatus.FAILED
        observer.on_phase_finished(phase)

        if ok:
            succeeded += 1
        else:
            failed += 1
            if phase.blocking:
                for downstream in phases[index + 1:]:
                    downstream.status = PhaseStatus.SKIPPED
                    observer.on_phase_finished(downstream)
                break

    observer.on_pipeline_finished(succeeded, failed, len(phases))
    return succeeded, failed


# ---------------------------------------------------------------------------
# Headless observer
# ---------------------------------------------------------------------------
class ConsoleObserver(PhaseObserver):
    def on_phase_started(self, phase: SetupPhase) -> None:
        logger.info("START   | %s | %s", phase.name, phase.description)

    def on_phase_progress(self, phase: SetupPhase, line: str) -> None:
        logger.info("        | %s | %s", phase.name, line)

    def on_phase_finished(self, phase: SetupPhase) -> None:
        verb = {
            PhaseStatus.SUCCEEDED: "DONE   ",
            PhaseStatus.FAILED:    "FAIL   ",
            PhaseStatus.SKIPPED:   "SKIP   ",
        }.get(phase.status, "       ")
        logger.info("%s| %s", verb, phase.name)

    def on_pipeline_finished(self, succeeded: int, failed: int, total: int) -> None:
        logger.info("Pipeline complete: %d/%d succeeded, %d failed", succeeded, total, failed)


# ---------------------------------------------------------------------------
# GUI mode (built only when PyQt6 is importable)
# ---------------------------------------------------------------------------
def _run_gui(phases: list[SetupPhase], dry_run: bool, gui: _GuiBundle) -> int:
    """Build the Qt application, MainWindow, and worker. Returns exec exit code."""

    QObject = gui.QObject
    QThread = gui.QThread
    pyqtSignal = gui.pyqtSignal

    class GuiObserver(QObject):                                # type: ignore[misc, valid-type]
        phase_started = pyqtSignal(dict)
        phase_progress = pyqtSignal(dict)
        phase_finished = pyqtSignal(dict)
        pipeline_finished = pyqtSignal(dict)

        def emit_started(self, phase: SetupPhase) -> None:
            self.phase_started.emit(_payload(phase))

        def emit_progress(self, phase: SetupPhase, line: str) -> None:
            self.phase_progress.emit({
                "phase": phase.name,
                "line": line,
                "timestamp": _now(),
            })

        def emit_finished(self, phase: SetupPhase) -> None:
            self.phase_finished.emit(_payload(phase))

        def emit_pipeline(self, succeeded: int, failed: int, total: int) -> None:
            self.pipeline_finished.emit({
                "succeeded": succeeded,
                "failed": failed,
                "total": total,
                "timestamp": _now(),
            })

    class BridgeObserver(PhaseObserver):
        def __init__(self, signals: Any) -> None:
            self._signals = signals

        def on_phase_started(self, phase: SetupPhase) -> None:
            self._signals.emit_started(phase)

        def on_phase_progress(self, phase: SetupPhase, line: str) -> None:
            self._signals.emit_progress(phase, line)

        def on_phase_finished(self, phase: SetupPhase) -> None:
            self._signals.emit_finished(phase)

        def on_pipeline_finished(self, succeeded: int, failed: int, total: int) -> None:
            self._signals.emit_pipeline(succeeded, failed, total)

    class Worker(QThread):                                     # type: ignore[misc, valid-type]
        def __init__(self, signals: Any) -> None:
            super().__init__()
            self._signals = signals

        def run(self) -> None:                                 # noqa: D401
            run_pipeline(phases, BridgeObserver(self._signals), dry_run)

    app = gui.QApplication.instance() or gui.QApplication(sys.argv)
    window = gui.MainWindow()
    window.setWindowTitle(WINDOW_TITLE)
    window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
    if gui.ASSETS_DIR is not None:
        icon_path = gui.ASSETS_DIR / "owl_tray.svg"
        if icon_path.is_file():
            window.setWindowIcon(gui.QIcon(str(icon_path)))

    owl_state = gui.OwlStateMachine() if gui.OwlStateMachine is not None else None
    signals = GuiObserver()

    def on_started(payload: dict) -> None:
        window.security_alert_received.emit({
            "level": SEV_INFO,
            "message": f"START - {payload['phase']}: {payload['description']}",
            "file_path": "(setup)",
            "timestamp": payload["timestamp"],
        })
        if owl_state is not None and gui.OwlState is not None:
            owl_state.transition_to(gui.OwlState.WATCHING)

    def on_progress(payload: dict) -> None:
        window.file_event_received.emit({
            "path": payload["phase"],
            "event_type": "progress",
            "level": SEV_INFO,
            "message": payload["line"],
            "timestamp": payload["timestamp"],
        })

    def on_finished(payload: dict) -> None:
        status = payload["status"]
        if status == PhaseStatus.SUCCEEDED.value:
            level, verb = SEV_INFO, "DONE"
        elif status == PhaseStatus.SKIPPED.value:
            level, verb = SEV_WARNING, "SKIPPED"
        else:
            level, verb = SEV_CRITICAL, "FAIL"
        window.security_alert_received.emit({
            "level": level,
            "message": f"{verb} - {payload['phase']}",
            "file_path": "(setup)",
            "timestamp": payload["timestamp"],
        })

    def on_pipeline(payload: dict) -> None:
        all_green = payload["failed"] == 0
        if owl_state is not None and gui.OwlState is not None:
            owl_state.transition_to(
                gui.OwlState.SLEEPING if all_green else gui.OwlState.ALERT
            )
        level = SEV_INFO if all_green else SEV_CRITICAL
        window.security_alert_received.emit({
            "level": level,
            "message": (
                f"Pipeline complete: {payload['succeeded']}/{payload['total']} succeeded, "
                f"{payload['failed']} failed."
            ),
            "file_path": "(setup)",
            "timestamp": payload["timestamp"],
        })
        app.quit()

    signals.phase_started.connect(on_started)
    signals.phase_progress.connect(on_progress)
    signals.phase_finished.connect(on_finished)
    signals.pipeline_finished.connect(on_pipeline)

    worker = Worker(signals)
    window.show()
    worker.start()
    rc = app.exec()
    worker.wait(timeout=10000)
    return rc


def _payload(phase: SetupPhase) -> dict:
    return {
        "phase": phase.name,
        "description": phase.description,
        "status": phase.status.value,
        "blocking": phase.blocking,
        "lines": list(phase.output_lines),
        "timestamp": _now(),
    }


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cowork_setup_orchestrator",
        description="Run Cowork setup with the OwlWatcher GUI as the progress display.",
    )
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Skip subprocess execution; emit signals as if commands ran cleanly.")
    parser.add_argument("--headless", action="store_true", default=False,
                        help="Run the pipeline in the console without showing the OwlWatcher window.")
    return parser.parse_args(argv)


def _configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(SETUP_LOG, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_logging()
    logger.info(
        "Cowork setup orchestrator starting (dry_run=%s, headless=%s)",
        args.dry_run, args.headless,
    )

    phases = build_default_phases()

    if args.headless:
        succeeded, failed = run_pipeline(phases, ConsoleObserver(), args.dry_run)
        return 0 if failed == 0 else 1

    gui = _import_gui()
    if not gui.available:
        logger.warning("PyQt6 / OwlWatcher GUI unavailable (%s). Falling back to headless mode.", gui.error)
        succeeded, failed = run_pipeline(phases, ConsoleObserver(), args.dry_run)
        return 0 if failed == 0 else 1

    return _run_gui(phases, args.dry_run, gui)


if __name__ == "__main__":
    sys.exit(main())
