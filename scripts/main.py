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
    elif args.rollback:
        sys.exit(cmd_rollback(args.rollback))


if __name__ == "__main__":
    main()
