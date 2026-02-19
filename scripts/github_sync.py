"""
GitHub Sync Script for ClaudeSkills

Manages git operations for syncing local skill files to a remote GitHub repository.
Supports dry-run preview (default), explicit push confirmation, conflict handling,
and structured logging.

Target repo: https://github.com/GrizzwaldHouse/cowork-skills.git
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path("C:/ClaudeSkills")
SCRIPTS_DIR = BASE_DIR / "scripts"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
SYNC_LOG_PATH = LOGS_DIR / "sync_log.json"
WATCH_CONFIG_PATH = CONFIG_DIR / "watch_config.json"

DEFAULT_REMOTE_URL = "https://github.com/GrizzwaldHouse/cowork-skills.git"
DEFAULT_BRANCH = "main"
_git_timeout = 60

# Patterns for files where *local* version wins during a merge conflict.
SKILL_FILE_PATTERNS = ("SKILL.md", "README.md", "PROMPT.md", "metadata.json")

# Patterns that should never be committed (mirrors watch_config ignored_patterns).
IGNORED_PATTERNS = {"__pycache__", ".git", "*.pyc", "backups", "logs", "dist"}


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _load_sync_log() -> list:
    """Load existing sync log entries from disk."""
    if SYNC_LOG_PATH.exists():
        try:
            with open(SYNC_LOG_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _save_sync_log(entries: list) -> None:
    """Persist sync log entries to disk."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SYNC_LOG_PATH, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, default=str)


def log_operation(operation: str, detail: str, success: bool, *, extra: dict | None = None) -> None:
    """Append a structured log entry for a git operation."""
    entries = _load_sync_log()
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "operation": operation,
        "detail": detail,
        "success": success,
    }
    if extra:
        entry["extra"] = extra
    entries.append(entry)
    _save_sync_log(entries)


# ---------------------------------------------------------------------------
# Git command runner
# ---------------------------------------------------------------------------

def run_git(*args: str, timeout: int | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a git command inside BASE_DIR.

    Returns the CompletedProcess result. Raises subprocess.CalledProcessError
    when *check* is True and the command exits with a non-zero status.
    """
    if timeout is None:
        timeout = _git_timeout
    cmd = ["git"] + list(args)
    detail = " ".join(cmd)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        log_operation("git", detail, success=True, extra={"stdout": result.stdout.strip()})
        return result
    except subprocess.TimeoutExpired as exc:
        log_operation("git", detail, success=False, extra={"error": f"Timed out after {timeout}s"})
        raise SystemExit(f"[ERROR] Git command timed out after {timeout}s: {detail}") from exc
    except subprocess.CalledProcessError as exc:
        log_operation("git", detail, success=False, extra={
            "returncode": exc.returncode,
            "stderr": (exc.stderr or "").strip(),
        })
        if check:
            raise
        return subprocess.CompletedProcess(cmd, exc.returncode, exc.stdout or "", exc.stderr or "")


# ---------------------------------------------------------------------------
# Repository initialisation
# ---------------------------------------------------------------------------

def ensure_repo(remote_url: str, branch: str) -> None:
    """Ensure BASE_DIR is a git repository with the correct remote."""
    git_dir = BASE_DIR / ".git"
    if not git_dir.exists():
        print(f"[INIT] Initialising git repository in {BASE_DIR}")
        run_git("init")
        run_git("remote", "add", "origin", remote_url)
        log_operation("init", f"Initialised repo with remote {remote_url}", success=True)
    else:
        # Verify remote URL matches; update if needed.
        result = run_git("remote", "get-url", "origin", check=False)
        current_url = result.stdout.strip()
        if result.returncode != 0:
            # Remote 'origin' missing -- add it.
            run_git("remote", "add", "origin", remote_url)
            print(f"[INIT] Added remote origin -> {remote_url}")
        elif current_url != remote_url:
            run_git("remote", "set-url", "origin", remote_url)
            print(f"[INIT] Updated remote origin -> {remote_url}")

    # Make sure we are on the target branch.
    current_branch_result = run_git("branch", "--show-current", check=False)
    current_branch = current_branch_result.stdout.strip()
    if not current_branch:
        # Likely a fresh repo with no commits yet -- create initial commit.
        print("[INIT] Creating initial commit on fresh repository")
        run_git("commit", "--allow-empty", "-m", "Initial commit")
        run_git("branch", "-M", branch)
    elif current_branch != branch:
        run_git("checkout", branch, check=False)


# ---------------------------------------------------------------------------
# Watch config filtering
# ---------------------------------------------------------------------------

def load_enabled_skills() -> list[str]:
    """Return list of enabled skill names from watch_config.json.

    An empty list means 'all skills'.
    """
    if not WATCH_CONFIG_PATH.exists():
        return []
    try:
        with open(WATCH_CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data.get("enabled_skills", [])
    except (json.JSONDecodeError, OSError):
        return []


def is_file_syncable(filepath: str, enabled_skills: list[str]) -> bool:
    """Determine whether a changed file should be staged for sync.

    Applies ignored-pattern filtering and optional enabled-skills filtering.
    """
    parts = Path(filepath).parts
    for part in parts:
        for pattern in IGNORED_PATTERNS:
            if pattern.startswith("*"):
                if part.endswith(pattern[1:]):
                    return False
            elif part == pattern:
                return False
    if enabled_skills:
        # A file is syncable only if it belongs to one of the enabled skill directories.
        for skill_name in enabled_skills:
            if skill_name in parts:
                return True
        return False
    return True


# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------

def resolve_conflicts() -> list[str]:
    """Attempt to auto-resolve merge conflicts.

    For skill-related files (SKILL.md, README.md, etc.) we prefer the local version.
    For everything else we prefer the remote version.

    Returns a list of files that were resolved.
    """
    result = run_git("diff", "--name-only", "--diff-filter=U", check=False)
    conflicted = [f for f in result.stdout.strip().splitlines() if f]
    if not conflicted:
        return []

    resolved: list[str] = []
    for filepath in conflicted:
        basename = Path(filepath).name
        if basename in SKILL_FILE_PATTERNS:
            # Prefer local (ours).
            run_git("checkout", "--ours", filepath)
            print(f"  [CONFLICT] {filepath} -> kept LOCAL version (skill file)")
        else:
            # Prefer remote (theirs).
            run_git("checkout", "--theirs", filepath)
            print(f"  [CONFLICT] {filepath} -> kept REMOTE version (shared config)")
        run_git("add", filepath)
        resolved.append(filepath)
        log_operation("conflict-resolve", filepath, success=True, extra={"strategy": "ours" if basename in SKILL_FILE_PATTERNS else "theirs"})
    return resolved


# ---------------------------------------------------------------------------
# Pull
# ---------------------------------------------------------------------------

def pull(branch: str) -> bool:
    """Pull latest changes from the remote. Returns True on success."""
    print(f"[PULL] Pulling from origin/{branch} ...")
    result = run_git("pull", "origin", branch, "--no-rebase", check=False)
    if result.returncode == 0:
        print("[PULL] Up to date.")
        return True

    # Check for merge conflicts.
    if "CONFLICT" in (result.stdout + result.stderr):
        print("[PULL] Merge conflicts detected -- attempting auto-resolve ...")
        resolved = resolve_conflicts()
        if resolved:
            run_git("commit", "-m", f"Auto-resolve {len(resolved)} conflict(s) (prefer local skill files)")
            print(f"[PULL] Resolved {len(resolved)} conflict(s).")
            return True
        print("[PULL] Could not auto-resolve all conflicts. Manual intervention needed.")
        return False

    # Other pull failure (e.g. network error, no upstream yet).
    stderr = result.stderr.strip()
    stderr_lower = stderr.lower()
    if "couldn't find remote ref" in stderr_lower or "no tracking information" in stderr_lower:
        print("[PULL] Remote branch does not exist yet -- will push to create it.")
        return True
    print(f"[PULL] Pull failed: {stderr}")
    return False


# ---------------------------------------------------------------------------
# Staging and commit message generation
# ---------------------------------------------------------------------------

def get_changed_files() -> dict[str, list[str]]:
    """Return dict mapping change type to list of file paths.

    Change types: 'new', 'modified', 'deleted'.
    """
    changes: dict[str, list[str]] = {"new": [], "modified": [], "deleted": []}

    # Untracked files.
    result = run_git("ls-files", "--others", "--exclude-standard")
    for f in result.stdout.strip().splitlines():
        if f:
            changes["new"].append(f)

    # Modified tracked files.
    result = run_git("diff", "--name-only")
    for f in result.stdout.strip().splitlines():
        if f:
            changes["modified"].append(f)

    # Deleted tracked files.
    result = run_git("diff", "--name-only", "--diff-filter=D")
    for f in result.stdout.strip().splitlines():
        if f:
            changes["deleted"].append(f)

    return changes


def generate_commit_message(staged_files: list[str]) -> str:
    """Build a human-readable commit message from the list of staged files."""
    if not staged_files:
        return "Sync update"

    # Group files by their top-level directory (skill name).
    groups: dict[str, list[str]] = {}
    for fp in staged_files:
        parts = Path(fp).parts
        key = parts[0] if len(parts) > 1 else "(root)"
        groups.setdefault(key, []).append(Path(fp).name)

    if len(groups) == 1:
        folder = next(iter(groups))
        files = groups[folder]
        file_list = ", ".join(sorted(set(files)))
        return f"Update {folder}: {file_list}"

    summaries = []
    for folder, files in sorted(groups.items()):
        file_list = ", ".join(sorted(set(files)))
        summaries.append(f"{folder} ({file_list})")
    return "Sync: " + "; ".join(summaries)


def stage_files(changes: dict[str, list[str]], enabled_skills: list[str]) -> list[str]:
    """Stage syncable changed files. Returns list of staged file paths."""
    staged: list[str] = []

    to_add = changes["new"] + changes["modified"]
    for filepath in to_add:
        if is_file_syncable(filepath, enabled_skills):
            run_git("add", filepath)
            staged.append(filepath)

    for filepath in changes["deleted"]:
        if is_file_syncable(filepath, enabled_skills):
            run_git("rm", "--cached", filepath, check=False)
            staged.append(filepath)

    return staged


# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------

def push(branch: str) -> bool:
    """Push to origin. Returns True on success.

    Never force-pushes.
    """
    print(f"[PUSH] Pushing to origin/{branch} ...")
    result = run_git("push", "origin", branch, check=False)
    if result.returncode == 0:
        print("[PUSH] Push successful.")
        log_operation("push", f"Pushed to origin/{branch}", success=True)
        return True
    stderr = result.stderr.strip()
    print(f"[PUSH] Push failed: {stderr}")
    log_operation("push", f"Push to origin/{branch} failed", success=False, extra={"stderr": stderr})
    return False


# ---------------------------------------------------------------------------
# Tagging
# ---------------------------------------------------------------------------

def create_tag(tag_name: str, message: str) -> bool:
    """Create an annotated tag and push it."""
    result = run_git("tag", "-a", tag_name, "-m", message, check=False)
    if result.returncode != 0:
        print(f"[TAG] Failed to create tag '{tag_name}': {result.stderr.strip()}")
        return False
    push_result = run_git("push", "origin", tag_name, check=False)
    if push_result.returncode != 0:
        print(f"[TAG] Failed to push tag '{tag_name}': {push_result.stderr.strip()}")
        return False
    print(f"[TAG] Created and pushed tag '{tag_name}'")
    log_operation("tag", f"Created tag {tag_name}", success=True)
    return True


# ---------------------------------------------------------------------------
# Preview / dry-run
# ---------------------------------------------------------------------------

def preview(changes: dict[str, list[str]], enabled_skills: list[str]) -> None:
    """Show what would be committed without making any changes."""
    print("\n=== DRY-RUN PREVIEW ===\n")

    any_syncable = False
    for change_type, files in changes.items():
        for filepath in files:
            syncable = is_file_syncable(filepath, enabled_skills)
            marker = "  " if syncable else "  [SKIP] "
            label = {"new": "NEW", "modified": "MOD", "deleted": "DEL"}.get(change_type, "???")
            print(f"{marker}[{label}] {filepath}")
            if syncable:
                any_syncable = True

    if not any_syncable:
        print("  (no syncable changes detected)")

    syncable_files = [
        f for ct, files in changes.items() for f in files
        if is_file_syncable(f, enabled_skills)
    ]
    if syncable_files:
        msg = generate_commit_message(syncable_files)
        print(f"\n  Commit message: \"{msg}\"")

    print("\n=== END PREVIEW (no changes made) ===\n")


# ---------------------------------------------------------------------------
# Main sync workflow
# ---------------------------------------------------------------------------

def sync(
    remote_url: str = DEFAULT_REMOTE_URL,
    branch: str = DEFAULT_BRANCH,
    dry_run: bool = True,
    tag: str | None = None,
    skip_pull: bool = False,
) -> bool:
    """Run the full sync workflow.

    Args:
        remote_url: Git remote URL (HTTPS or SSH).
        branch: Branch to sync with.
        dry_run: If True (default), only preview changes.
        tag: Optional tag name for a version tag after push.
        skip_pull: Skip the pull step (useful for first push to empty remote).

    Returns True if the sync completed successfully.
    """
    print(f"[SYNC] Remote : {remote_url}")
    print(f"[SYNC] Branch : {branch}")
    print(f"[SYNC] Mode   : {'DRY-RUN' if dry_run else 'LIVE'}\n")

    # 1. Ensure repo is initialised.
    ensure_repo(remote_url, branch)

    # 2. Load watch config filters.
    enabled_skills = load_enabled_skills()
    if enabled_skills:
        print(f"[SYNC] Enabled skills filter: {', '.join(enabled_skills)}")

    # 3. Pull latest (unless skipped).
    if not skip_pull:
        if not pull(branch):
            print("[SYNC] Aborting due to pull failure.")
            return False

    # 4. Detect changes.
    changes = get_changed_files()
    total_changes = sum(len(v) for v in changes.values())
    if total_changes == 0:
        print("[SYNC] No changes detected. Nothing to do.")
        log_operation("sync", "No changes detected", success=True)
        return True

    print(f"[SYNC] Detected {total_changes} changed file(s).")

    # 5. Dry-run -- show preview and exit.
    if dry_run:
        preview(changes, enabled_skills)
        log_operation("sync-preview", f"{total_changes} changes previewed", success=True)
        return True

    # 6. Stage files.
    staged = stage_files(changes, enabled_skills)
    if not staged:
        print("[SYNC] No syncable changes after filtering. Nothing to commit.")
        return True

    # 7. Commit.
    commit_msg = generate_commit_message(staged)
    print(f"[COMMIT] {commit_msg}")
    run_git("commit", "-m", commit_msg)
    log_operation("commit", commit_msg, success=True, extra={"files": staged})

    # 8. Push.
    if not push(branch):
        return False

    # 9. Optional tag.
    if tag:
        create_tag(tag, f"Sync tag: {commit_msg}")

    print("[SYNC] Complete.")
    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    global _git_timeout
    parser = argparse.ArgumentParser(
        description="Sync ClaudeSkills to GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python github_sync.py                  # dry-run preview (default)\n"
            "  python github_sync.py --confirm        # actually commit and push\n"
            "  python github_sync.py --confirm --tag v1.0  # push and tag\n"
            "  python github_sync.py --remote git@github.com:user/repo.git\n"
        ),
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually commit and push (without this flag, only a preview is shown)",
    )
    parser.add_argument(
        "--remote",
        default=DEFAULT_REMOTE_URL,
        help=f"Remote URL (default: {DEFAULT_REMOTE_URL})",
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Branch name (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Create an annotated tag after pushing",
    )
    parser.add_argument(
        "--skip-pull",
        action="store_true",
        help="Skip the pull step (useful for first push to an empty remote)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=_git_timeout,
        help=f"Timeout in seconds for git commands (default: {_git_timeout})",
    )

    args = parser.parse_args()

    # Apply timeout override globally.
    _git_timeout = args.timeout

    success = sync(
        remote_url=args.remote,
        branch=args.branch,
        dry_run=not args.confirm,
        tag=args.tag,
        skip_pull=args.skip_pull,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
