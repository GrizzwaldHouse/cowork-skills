# main.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: CLI orchestrator coordinating watcher, sync, UI, and GitHub operations from single entry point

"""
Main entry point for the Claude Skills system.

Orchestrates the observer, broadcaster, UI launcher, and GitHub sync modules.
Provides a unified CLI for all operations.

Usage::

    python main.py --watch          # Start file watcher in background
    python main.py --sync           # Run one-time sync cycle
    python main.py --github         # Push to GitHub (dry-run by default)
    python main.py --github --confirm  # Actually push to GitHub
    python main.py --preview        # Show pending changes without applying
    python main.py --rollback <ts>  # Restore files from a timestamped backup
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
SCRIPTS_DIR = BASE_DIR / "scripts"
BACKUP_DIR = BASE_DIR / "backups"

# Ensure scripts directory is on the Python path so modules can import each other.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from log_config import configure_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()
logger = logging.getLogger("claude-skills")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_watch() -> int:
    """Start the file observer in the foreground."""
    from observer import start_observer, load_config

    logger.info("Starting file observer...")
    config = load_config()

    # Auto-add secondary watch path if it exists.
    secondary = Path("D:/Portfolio/Projects")
    if secondary.exists():
        watched = config.setdefault("watched_paths", [])
        if str(secondary) not in watched:
            watched.append(str(secondary))
            logger.info("Auto-added secondary watch path: %s", secondary)

    start_observer(config)
    return 0


def cmd_sync(preview: bool = False) -> int:
    """Run a one-time sync cycle."""
    from broadcaster import full_sync

    logger.info("Running %s sync...", "preview" if preview else "full")
    success = full_sync(preview=preview)
    return 0 if success else 1


def cmd_preview() -> int:
    """Show pending changes without applying them."""
    from broadcaster import generate_diff_summary

    print(generate_diff_summary())
    return 0


def cmd_github(confirm: bool = False, skip_pull: bool = False, tag: str | None = None) -> int:
    """Run GitHub sync (dry-run by default)."""
    from github_sync import sync

    logger.info("Running GitHub sync (%s)...", "LIVE" if confirm else "dry-run")
    success = sync(
        dry_run=not confirm,
        tag=tag,
        skip_pull=skip_pull,
    )
    return 0 if success else 1


def cmd_rollback(timestamp: str) -> int:
    """Restore files from a timestamped backup."""
    backup_path = BACKUP_DIR / timestamp

    if not backup_path.exists():
        logger.error("Backup not found: %s", backup_path)
        print(f"\nNo backup found at: {backup_path}")

        # List available backups.
        if BACKUP_DIR.exists():
            backups = sorted(
                [d.name for d in BACKUP_DIR.iterdir() if d.is_dir()],
                reverse=True,
            )
            if backups:
                print("\nAvailable backups:")
                for b in backups[:20]:
                    print(f"  {b}")
            else:
                print("\nNo backups available.")
        return 1

    # List files that would be restored.
    files_to_restore: list[tuple[Path, Path]] = []
    for backup_file in backup_path.rglob("*"):
        if backup_file.is_file():
            rel = backup_file.relative_to(backup_path)
            target = BASE_DIR / rel
            files_to_restore.append((backup_file, target))

    if not files_to_restore:
        print(f"Backup at {timestamp} contains no files.")
        return 1

    print(f"\nRollback from backup: {timestamp}")
    print(f"Files to restore: {len(files_to_restore)}")
    print()

    for backup_file, target in files_to_restore:
        rel = backup_file.relative_to(backup_path).as_posix()
        exists = "overwrite" if target.exists() else "create"
        print(f"  [{exists}] {rel}")

    print()
    try:
        answer = input("Proceed with rollback? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    if answer not in ("y", "yes"):
        print("Rollback cancelled.")
        return 0

    # Perform rollback.
    restored = 0
    for backup_file, target in files_to_restore:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(backup_file), str(target))
        restored += 1
        rel = backup_file.relative_to(backup_path).as_posix()
        logger.info("Restored: %s", rel)

    print(f"\nRestored {restored} file(s) from backup {timestamp}.")
    return 0


def cmd_eval(skill_name: str) -> int:
    """Run eval assertions against a skill and show results."""
    from skill_eval_runner import EvalRunner, print_eval_summary

    logger.info("Running eval for skill: %s", skill_name)

    try:
        runner = EvalRunner(skill_name)
        report = runner.run()
        print_eval_summary(report)
        return 0 if report["summary"]["pass_rate"] >= 1.0 else 1
    except FileNotFoundError as exc:
        print(f"\nError: {exc}")
        return 1
    except Exception as exc:
        logger.exception("Eval failed for '%s'", skill_name)
        print(f"\nEval failed: {exc}")
        return 1


def cmd_self_improve(
    skill_name: str,
    max_iterations: int,
    target_score: float,
    resume: bool = False,
    self_heal: bool = False,
) -> int:
    """Start the autonomous self-improvement loop for a skill."""
    logger.info(
        "Starting self-improvement for '%s' (max=%d, target=%.2f, resume=%s, heal=%s)",
        skill_name,
        max_iterations,
        target_score,
        resume,
        self_heal,
    )

    try:
        # Detect interrupted loop if --resume was specified
        continuation = None
        if resume:
            from diff_continuation import DiffContinuationEngine

            engine = DiffContinuationEngine(skill_name)
            continuation = engine.detect_interrupted_loop()
            if continuation:
                print(f"Resuming from iteration {continuation.resume_iteration} "
                      f"(score: {continuation.last_score:.2%}, "
                      f"state: {continuation.skill_state})")
            else:
                print("No interrupted loop detected. Starting fresh.")

        # Use self-healing wrapper if --self-heal was specified
        if self_heal:
            from self_healing_loop import SelfHealingLoop

            loop = SelfHealingLoop(
                skill_name=skill_name,
                max_iterations=max_iterations,
                target_score=target_score,
            )
            summary = loop.run(continuation=continuation)
        else:
            from skill_improver import SkillImprover

            improver = SkillImprover(
                skill_name=skill_name,
                max_iterations=max_iterations,
                target_score=target_score,
            )
            summary = improver.run_loop(continuation=continuation)

        return 0 if summary.get("target_reached", False) else 1
    except FileNotFoundError as exc:
        print(f"\nError: {exc}")
        return 1
    except Exception as exc:
        logger.exception("Self-improvement failed for '%s'", skill_name)
        print(f"\nSelf-improvement failed: {exc}")
        return 1


def cmd_intelligence() -> int:
    """Start the GUI with intelligence pipeline enabled."""
    from gui.app import OwlWatcherApp, _parse_args, _check_single_instance
    from PyQt6.QtWidgets import QApplication
    import sys as _sys

    _app_temp = QApplication.instance() or QApplication(_sys.argv)
    shared_mem = _check_single_instance()
    if shared_mem is None:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(None, "OwlWatcher", "Another instance is already running.")
        return 1

    # Create args with intelligence flag
    args = _parse_args(["--visible"])
    args.intelligence = True

    owl_app = OwlWatcherApp(args)
    owl_app._shared_mem = shared_mem
    return owl_app.run()


def cmd_agents() -> int:
    """Start the multi-agent system in headless mode."""
    from agent_runtime import AgentRuntime

    logger.info("Starting multi-agent system...")

    runtime = AgentRuntime()
    runtime.bootstrap()
    started = runtime.start()

    print(runtime.get_status_summary())
    print(f"\nAgents running: {', '.join(started)}")
    print("Press Ctrl+C to stop.\n")

    try:
        import time
        while runtime.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down agents...")
        runtime.stop()
        print("All agents stopped.")

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse arguments and dispatch to the appropriate command."""
    parser = argparse.ArgumentParser(
        prog="claude-skills",
        description="Claude Skills System - Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --watch                 # Start file watcher\n"
            "  python main.py --sync                  # Full sync cycle\n"
            "  python main.py --preview               # Show pending changes\n"
            "  python main.py --github                # GitHub dry-run\n"
            "  python main.py --github --confirm      # GitHub push\n"
            "  python main.py --rollback 20260217T120000Z  # Restore backup\n"
            "  python main.py --eval canva-designer   # Run eval assertions\n"
            "  python main.py --self-improve canva-designer  # Self-improve loop\n"
            "  python main.py --self-improve canva-designer --max-iterations 10\n"
        ),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--watch",
        action="store_true",
        help="Start the file observer (runs in foreground)",
    )
    group.add_argument(
        "--sync",
        action="store_true",
        help="Run a one-time sync cycle",
    )
    group.add_argument(
        "--preview",
        action="store_true",
        help="Show pending changes without applying them",
    )
    group.add_argument(
        "--github",
        action="store_true",
        help="Run GitHub sync (dry-run by default, use --confirm to push)",
    )
    group.add_argument(
        "--rollback",
        metavar="TIMESTAMP",
        help="Restore files from a backup (e.g. 20260217T120000Z)",
    )
    group.add_argument(
        "--eval",
        metavar="SKILL_NAME",
        help="Run eval assertions against a skill and show results",
    )
    group.add_argument(
        "--self-improve",
        metavar="SKILL_NAME",
        help="Start autonomous self-improvement loop for a skill",
    )
    group.add_argument(
        "--intelligence",
        action="store_true",
        help="Start OwlWatcher with intelligence pipeline enabled",
    )
    group.add_argument(
        "--agents",
        action="store_true",
        help="Start the multi-agent system (headless, no GUI)",
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm destructive operations (used with --github or --sync)",
    )
    parser.add_argument(
        "--skip-pull",
        action="store_true",
        help="Skip git pull (used with --github)",
    )
    parser.add_argument(
        "--tag",
        metavar="TAG",
        help="Create a git tag after push (used with --github --confirm)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Max improvement iterations (used with --self-improve, default: 50)",
    )
    parser.add_argument(
        "--target-score",
        type=float,
        default=1.0,
        help="Target pass rate to stop at (used with --self-improve, default: 1.0)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume interrupted self-improvement loop (used with --self-improve)",
    )
    parser.add_argument(
        "--self-heal",
        action="store_true",
        help="Enable self-healing retry wrapper (used with --self-improve)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(
        "Claude Skills System starting at %s",
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    if args.watch:
        sys.exit(cmd_watch())
    elif args.sync:
        sys.exit(cmd_sync(preview=not args.confirm))
    elif args.preview:
        sys.exit(cmd_preview())
    elif args.github:
        sys.exit(cmd_github(
            confirm=args.confirm,
            skip_pull=args.skip_pull,
            tag=args.tag,
        ))
    elif args.eval:
        sys.exit(cmd_eval(args.eval))
    elif args.self_improve:
        sys.exit(cmd_self_improve(
            skill_name=args.self_improve,
            max_iterations=args.max_iterations,
            target_score=args.target_score,
            resume=args.resume,
            self_heal=args.self_heal,
        ))
    elif args.rollback:
        sys.exit(cmd_rollback(args.rollback))
    elif args.intelligence:
        sys.exit(cmd_intelligence())
    elif args.agents:
        sys.exit(cmd_agents())


if __name__ == "__main__":
    main()
