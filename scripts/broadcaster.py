"""
Broadcaster and sync engine for the Claude Skills system.

Receives change events from the observer, updates main_cloud.json with
file metadata, and propagates changes bidirectionally between the cloud
registry and individual skill folders.  Supports rollback via timestamped
backups and desktop notifications via plyer.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sync_utils import (
    BASE_DIR,
    CLOUD_PATH,
    atomic_write,
    backup_file,
    file_mtime_iso,
    file_sha256,
    is_file_newer,
    load_cloud,
    relative_skill_path,
    resolve_from_base,
    save_cloud,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("broadcaster")

# ---------------------------------------------------------------------------
# Skill discovery
# ---------------------------------------------------------------------------

# Directories that contain individual skill folders.
SKILL_ROOT_DIRS: list[Path] = [
    BASE_DIR / "Example_Skills",
    BASE_DIR / "Skill_Creator",
    BASE_DIR / "Blog_Automation_Prompt",
]

# Files tracked per skill.
TRACKED_FILENAMES = ("SKILL.md", "README.md", "prompt_template.md", "metadata.json")


def discover_skills() -> dict[str, Path]:
    """Discover all skill directories and return a mapping of name -> path.

    Scans SKILL_ROOT_DIRS for folders containing at least one tracked file.
    """
    skills: dict[str, Path] = {}

    for root in SKILL_ROOT_DIRS:
        if not root.exists():
            continue

        # Check if the root itself is a skill folder (e.g. Skill_Creator/).
        if _is_skill_dir(root):
            skills[root.name] = root
            continue

        # Otherwise scan children.
        for child in sorted(root.iterdir()):
            if child.is_dir() and _is_skill_dir(child):
                skills[child.name] = child

    return skills


def _is_skill_dir(path: Path) -> bool:
    """Return True if *path* contains at least one tracked file."""
    for name in TRACKED_FILENAMES:
        if (path / name).exists():
            return True
    return False


# ---------------------------------------------------------------------------
# Cloud registry update
# ---------------------------------------------------------------------------

def build_skill_entry(skill_dir: Path) -> dict[str, Any]:
    """Build a cloud registry entry for a single skill directory."""
    files: dict[str, dict[str, str]] = {}
    latest_modified: str | None = None

    for name in TRACKED_FILENAMES:
        file_path = skill_dir / name
        if file_path.exists():
            h = file_sha256(file_path)
            mod = file_mtime_iso(file_path)
            files[name] = {"hash": h, "modified": mod}
            if latest_modified is None or mod > latest_modified:
                latest_modified = mod

    rel_path = relative_skill_path(skill_dir)

    return {
        "path": rel_path,
        "last_modified": latest_modified,
        "hash": _combined_hash(files),
        "files": files,
    }


def _combined_hash(files: dict[str, dict[str, str]]) -> str:
    """Produce a combined hash from individual file hashes."""
    import hashlib

    combined = hashlib.sha256()
    for name in sorted(files):
        combined.update(files[name]["hash"].encode())
    return combined.hexdigest()


def update_cloud_registry() -> dict[str, Any]:
    """Scan all skills and update main_cloud.json.

    Returns the updated cloud data.
    """
    cloud = load_cloud()
    skills = discover_skills()

    for skill_name, skill_dir in skills.items():
        entry = build_skill_entry(skill_dir)
        cloud["skills"][skill_name] = entry

    # Remove entries for skills that no longer exist on disk.
    stale = [name for name in cloud["skills"] if name not in skills]
    for name in stale:
        logger.info("Removing stale skill from registry: %s", name)
        del cloud["skills"][name]

    cloud["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_cloud(cloud)
    logger.info("Cloud registry updated with %d skill(s)", len(cloud["skills"]))
    return cloud


# ---------------------------------------------------------------------------
# Change propagation
# ---------------------------------------------------------------------------

def propagate_changes(preview: bool = False) -> list[dict[str, str]]:
    """Propagate changes bidirectionally between cloud and skill folders.

    Compares both timestamps AND sha256 hashes in the cloud registry against
    actual file state on disk. Never overwrites a newer file with an older
    version. Backs up old versions before any overwrite.

    Bidirectional logic:
    - If a file on disk is newer (by mtime) and different (by hash), the
      cloud registry is updated to match disk.
    - If the registry records a file that is missing on disk, it is flagged
      for manual recovery (the registry entry is preserved).
    - If a registered file's hash matches disk, no action is taken.

    Parameters
    ----------
    preview:
        If True, only log what would happen without making changes.

    Returns
    -------
    A list of action dicts describing what was (or would be) propagated.
    """
    cloud = load_cloud()
    actions: list[dict[str, str]] = []

    for skill_name, entry in cloud.get("skills", {}).items():
        skill_dir = resolve_from_base(entry["path"])

        if not skill_dir.exists():
            logger.warning("Skill directory missing: %s", skill_dir)
            continue

        for filename, file_meta in entry.get("files", {}).items():
            file_path = skill_dir / filename
            registered_hash = file_meta.get("hash", "")
            registered_modified = file_meta.get("modified", "")

            if not file_path.exists():
                # File recorded in cloud but missing on disk.
                action = {
                    "action": "missing_on_disk",
                    "skill": skill_name,
                    "file": filename,
                    "detail": f"{file_path} recorded in cloud but not found on disk",
                }
                actions.append(action)
                logger.warning(
                    "[%s] %s is in the registry but missing on disk",
                    skill_name, filename,
                )
                continue

            current_hash = file_sha256(file_path)

            if current_hash == registered_hash:
                # Hashes match -- file is in sync.
                continue

            # Hash mismatch -- determine which is newer by timestamp.
            current_mtime_iso = file_mtime_iso(file_path)

            # Disk is newer or registry has no timestamp: update registry.
            if not registered_modified or current_mtime_iso >= registered_modified:
                action = {
                    "action": "disk_newer",
                    "skill": skill_name,
                    "file": filename,
                    "detail": (
                        f"Hash mismatch: disk={current_hash[:12]}... "
                        f"registry={registered_hash[:12]}... "
                        f"(disk mtime: {current_mtime_iso})"
                    ),
                }
                actions.append(action)

                if not preview:
                    file_meta["hash"] = current_hash
                    file_meta["modified"] = current_mtime_iso
                    logger.info(
                        "[%s] Updated registry for %s (disk is newer)",
                        skill_name, filename,
                    )
            else:
                # Registry records a newer timestamp than disk -- disk file
                # may have been reverted or corrupted. Back up the disk copy
                # before flagging so no data is lost.
                action = {
                    "action": "registry_newer",
                    "skill": skill_name,
                    "file": filename,
                    "detail": (
                        f"Registry timestamp ({registered_modified}) is newer "
                        f"than disk ({current_mtime_iso}). Backed up disk copy."
                    ),
                }
                actions.append(action)

                if not preview:
                    backup_file(file_path)
                    logger.info(
                        "[%s] Registry is newer for %s; backed up disk copy",
                        skill_name, filename,
                    )

    if actions and not preview:
        cloud["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_cloud(cloud)

    return actions


# ---------------------------------------------------------------------------
# Sync log management
# ---------------------------------------------------------------------------

def append_cloud_sync_log(
    action: str,
    file: str,
    source: str,
    target: str,
) -> None:
    """Append an entry to the sync_log array in main_cloud.json."""
    cloud = load_cloud()
    cloud.setdefault("sync_log", []).append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "file": file,
        "source": source,
        "target": target,
    })
    # Keep sync_log from growing unbounded.
    if len(cloud["sync_log"]) > 500:
        cloud["sync_log"] = cloud["sync_log"][-500:]
    save_cloud(cloud)


# ---------------------------------------------------------------------------
# Broadcaster entry point (called by the observer)
# ---------------------------------------------------------------------------

def broadcast_change(event_type: str, file_path: str) -> None:
    """Handle a single file change event from the observer.

    This is the function imported by observer.py via::

        from broadcaster import broadcast_change

    Steps:
    1. Update the cloud registry for the affected skill.
    2. Log the change to the cloud sync_log.
    3. Send a desktop notification.
    """
    path = Path(file_path)

    if not path.exists() and event_type != "deleted":
        logger.debug("File no longer exists, skipping: %s", path)
        return

    # Identify which skill this file belongs to.
    skills = discover_skills()
    skill_name: str | None = None
    for name, skill_dir in skills.items():
        try:
            path.relative_to(skill_dir)
            skill_name = name
            break
        except ValueError:
            continue

    if skill_name is None:
        logger.debug("Changed file is not part of a tracked skill: %s", path)
        return

    # Backup the file before updating the registry if the hash has changed.
    # This ensures no data is lost when the registry entry is overwritten.
    cloud = load_cloud()
    skill_dir = skills[skill_name]
    existing_entry = cloud.get("skills", {}).get(skill_name, {})

    if event_type in ("created", "modified") and path.exists():
        existing_files = existing_entry.get("files", {})
        if path.name in existing_files:
            old_hash = existing_files[path.name].get("hash", "")
            current_hash = file_sha256(path)
            if old_hash and old_hash != current_hash:
                backup_file(path)
                logger.info("[%s] Backed up %s before registry update", skill_name, path.name)

    # Update the cloud registry for this skill.
    cloud["skills"][skill_name] = build_skill_entry(skill_dir)
    cloud["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_cloud(cloud)

    # Log to cloud sync_log.
    rel = relative_skill_path(path)
    append_cloud_sync_log(
        action=event_type,
        file=rel,
        source="disk",
        target="cloud",
    )

    logger.info("[%s] %s -> cloud registry updated (%s)", skill_name, rel, event_type)

    # Desktop notification.
    _send_notification(
        title=f"Skill Updated: {skill_name}",
        message=f"{event_type.capitalize()}: {path.name}",
    )


# ---------------------------------------------------------------------------
# Desktop notifications
# ---------------------------------------------------------------------------

def _send_notification(title: str, message: str) -> None:
    """Send a desktop notification via plyer. Fails silently."""
    try:
        from plyer import notification  # type: ignore[import-untyped]

        notification.notify(
            title=title,
            message=message,
            app_name="ClaudeSkills",
            timeout=5,
        )
    except ImportError:
        logger.debug("plyer not installed; skipping desktop notification")
    except Exception as exc:
        logger.debug("Desktop notification failed: %s", exc)


# ---------------------------------------------------------------------------
# Diff preview
# ---------------------------------------------------------------------------

def generate_diff_summary() -> str:
    """Generate a human-readable diff summary of pending changes.

    Compares the current state of skill files on disk against what is
    recorded in the cloud registry.
    """
    cloud = load_cloud()
    lines: list[str] = []
    lines.append("=== SYNC DIFF SUMMARY ===")
    lines.append("")

    skills_on_disk = discover_skills()
    any_diff = False

    # Check each registered skill.
    for skill_name, entry in cloud.get("skills", {}).items():
        skill_dir = resolve_from_base(entry["path"])
        if not skill_dir.exists():
            lines.append(f"  [REMOVED] {skill_name} (directory no longer exists)")
            any_diff = True
            continue

        for filename, file_meta in entry.get("files", {}).items():
            file_path = skill_dir / filename
            if not file_path.exists():
                lines.append(f"  [DELETED] {skill_name}/{filename}")
                any_diff = True
                continue

            current_hash = file_sha256(file_path)
            if current_hash != file_meta.get("hash", ""):
                lines.append(f"  [MODIFIED] {skill_name}/{filename}")
                any_diff = True

    # Check for new skills not yet in the registry.
    for skill_name, skill_dir in skills_on_disk.items():
        if skill_name not in cloud.get("skills", {}):
            lines.append(f"  [NEW SKILL] {skill_name}")
            any_diff = True

    if not any_diff:
        lines.append("  (no differences detected)")

    lines.append("")
    lines.append("=== END DIFF SUMMARY ===")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full sync workflow
# ---------------------------------------------------------------------------

def full_sync(preview: bool = False) -> bool:
    """Run a full sync cycle.

    1. Discover all skills on disk.
    2. Update the cloud registry.
    3. Propagate changes bidirectionally.
    4. Send a summary notification.

    Parameters
    ----------
    preview:
        If True, show what would happen without making changes.

    Returns True on success.
    """
    if preview:
        print(generate_diff_summary())
        return True

    logger.info("Starting full sync cycle...")

    # Step 1-2: Update registry from disk.
    cloud = update_cloud_registry()
    skill_count = len(cloud.get("skills", {}))

    # Step 3: Propagate changes.
    actions = propagate_changes(preview=False)

    # Step 4: Notification.
    if actions:
        _send_notification(
            title="ClaudeSkills Sync Complete",
            message=f"{len(actions)} change(s) across {skill_count} skill(s)",
        )
        for action in actions:
            logger.info(
                "  [%s] %s/%s: %s",
                action["action"], action["skill"], action["file"], action["detail"],
            )
    else:
        logger.info("Full sync complete: %d skill(s), no changes needed.", skill_count)

    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for the broadcaster/sync engine."""
    parser = argparse.ArgumentParser(
        description="ClaudeSkills broadcaster and sync engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python broadcaster.py                # full sync (live)\n"
            "  python broadcaster.py --preview      # show diff without changes\n"
            "  python broadcaster.py --update-only  # only update cloud registry\n"
        ),
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show a diff summary without making any changes",
    )
    parser.add_argument(
        "--update-only",
        action="store_true",
        help="Only update the cloud registry (no propagation or notification)",
    )

    args = parser.parse_args()

    if args.update_only:
        cloud = update_cloud_registry()
        print(json.dumps(cloud, indent=2, default=str))
        return

    success = full_sync(preview=args.preview)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
