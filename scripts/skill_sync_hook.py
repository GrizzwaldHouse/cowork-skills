# skill_sync_hook.py
# Developer: Marcus Daley
# Date: 2026-05-04
# Purpose: Claude Code hook handler — syncs new/updated skills detected by OwlWatcher
#          into ~/.claude/skills/ and schedules a GitHub push.

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
GLOBAL_SKILLS_DIR = Path("C:/Users/daley/.claude/skills")
CLOUD_PATH = BASE_DIR / "cloud" / "main_cloud.json"
PUSH_STAMP_PATH = BASE_DIR / "logs" / ".last_github_push"
PUSH_DEBOUNCE_SECONDS = 60

SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [skill-sync-hook] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("skill_sync_hook")

# ---------------------------------------------------------------------------
# Skill root directories (mirrors broadcaster.py:SKILL_ROOT_DIRS)
# ---------------------------------------------------------------------------
SKILL_ROOT_DIRS: list[Path] = [
    BASE_DIR / "Example_Skills",
    BASE_DIR / "Skill_Creator",
    BASE_DIR / "Blog_Automation_Prompt",
    BASE_DIR / "skills",
]

TRACKED_FILENAMES = ("SKILL.md", "README.md", "prompt_template.md", "metadata.json")


# ---------------------------------------------------------------------------
# Skill directory detection
# ---------------------------------------------------------------------------

def _is_skill_dir(path: Path) -> bool:
    return any((path / name).exists() for name in TRACKED_FILENAMES)


def _find_skill_dir(file_path: Path) -> Path | None:
    """Walk up from file_path to find the nearest enclosing skill directory."""
    candidate = file_path if file_path.is_dir() else file_path.parent
    for root in SKILL_ROOT_DIRS:
        try:
            candidate.relative_to(root)
            # candidate is inside this root — find the immediate child of root
            rel = candidate.relative_to(root)
            skill_dir = root / rel.parts[0] if rel.parts else candidate
            if _is_skill_dir(skill_dir):
                return skill_dir
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def _load_cloud() -> dict:
    if not CLOUD_PATH.exists():
        return {"skills": {}, "sync_log": []}
    try:
        with CLOUD_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read cloud registry: %s", exc)
        return {"skills": {}, "sync_log": []}


def _skill_hash(skill_dir: Path) -> str:
    import hashlib
    combined = hashlib.sha256()
    for name in sorted(TRACKED_FILENAMES):
        fp = skill_dir / name
        if fp.exists():
            combined.update(fp.read_bytes())
    return combined.hexdigest()


def _is_changed(skill_name: str, skill_dir: Path, cloud: dict) -> bool:
    registered = cloud.get("skills", {}).get(skill_name, {})
    if not registered:
        return True
    return _skill_hash(skill_dir) != registered.get("hash", "")


# ---------------------------------------------------------------------------
# Sync a single skill
# ---------------------------------------------------------------------------

def _sync_skill(skill_name: str, skill_dir: Path) -> bool:
    """Copy skill dir to ~/.claude/skills/ and update broadcaster registry."""
    dest = GLOBAL_SKILLS_DIR / skill_name
    try:
        dest.mkdir(parents=True, exist_ok=True)
        for name in TRACKED_FILENAMES:
            src = skill_dir / name
            if src.exists():
                shutil.copy2(src, dest / name)
        # Copy any additional files (templates/, examples/, etc.)
        for item in skill_dir.iterdir():
            if item.name not in TRACKED_FILENAMES:
                target = dest / item.name
                if item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)
        logger.info("Synced skill '%s' → %s", skill_name, dest)
        return True
    except OSError as exc:
        logger.error("Failed to sync skill '%s': %s", skill_name, exc)
        return False


# ---------------------------------------------------------------------------
# GitHub push (debounced)
# ---------------------------------------------------------------------------

def _maybe_push_github() -> None:
    now = time.time()
    if PUSH_STAMP_PATH.exists():
        try:
            last = float(PUSH_STAMP_PATH.read_text(encoding="utf-8").strip())
            if now - last < PUSH_DEBOUNCE_SECONDS:
                logger.debug("GitHub push debounced (last push %.0fs ago)", now - last)
                return
        except ValueError:
            pass

    PUSH_STAMP_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUSH_STAMP_PATH.write_text(str(now), encoding="utf-8")

    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "github_sync.py"), "--push"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("GitHub push succeeded")
        else:
            logger.error("GitHub push failed: %s", result.stderr.strip())
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.error("GitHub push error: %s", exc)


# ---------------------------------------------------------------------------
# Update broadcaster registry
# ---------------------------------------------------------------------------

def _update_registry(skill_name: str, skill_dir: Path) -> None:
    try:
        from broadcaster import build_skill_entry, load_cloud, save_cloud
        cloud = load_cloud()
        cloud["skills"][skill_name] = build_skill_entry(skill_dir)
        from datetime import datetime, timezone
        cloud["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_cloud(cloud)
        logger.debug("Registry updated for '%s'", skill_name)
    except ImportError:
        logger.debug("broadcaster not importable; skipping registry update")
    except Exception as exc:
        logger.warning("Registry update failed for '%s': %s", skill_name, exc)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def handle_post_write(file_arg: str) -> None:
    file_path = Path(file_arg)
    skill_dir = _find_skill_dir(file_path)
    if skill_dir is None:
        logger.debug("Not a skill file, skipping: %s", file_path)
        return

    skill_name = skill_dir.name
    cloud = _load_cloud()
    if not _is_changed(skill_name, skill_dir, cloud):
        logger.debug("Skill '%s' unchanged, skipping", skill_name)
        return

    logger.info("Skill change detected: %s", skill_name)
    if _sync_skill(skill_name, skill_dir):
        _update_registry(skill_name, skill_dir)
        _maybe_push_github()


def handle_session_end() -> None:
    """Full sweep — catches any skills missed during the session."""
    cloud = _load_cloud()
    synced = 0

    for root in SKILL_ROOT_DIRS:
        if not root.exists():
            continue
        candidates = [root] if _is_skill_dir(root) else [
            c for c in sorted(root.iterdir()) if c.is_dir() and _is_skill_dir(c)
        ]
        for skill_dir in candidates:
            skill_name = skill_dir.name
            if _is_changed(skill_name, skill_dir, cloud):
                logger.info("Session-end sweep: syncing '%s'", skill_name)
                if _sync_skill(skill_name, skill_dir):
                    _update_registry(skill_name, skill_dir)
                    synced += 1

    if synced:
        logger.info("Session-end sweep: %d skill(s) synced", synced)
        _maybe_push_github()
    else:
        logger.info("Session-end sweep: all skills up to date")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="ClaudeSkills OwlWatcher sync hook")
    parser.add_argument(
        "--event",
        choices=["post-write", "session-end"],
        required=True,
        help="Hook event type",
    )
    parser.add_argument(
        "--file",
        default="",
        help="File path (required for post-write event)",
    )
    args = parser.parse_args()

    if args.event == "post-write":
        if not args.file:
            logger.error("--file is required for post-write event")
            sys.exit(1)
        handle_post_write(args.file)
    elif args.event == "session-end":
        handle_session_end()


if __name__ == "__main__":
    main()
