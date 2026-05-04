# skill-sync-hook.md
# Developer: Marcus Daley
# Date: 2026-05-04
# Purpose: Documents the OwlWatcher-triggered hook that auto-syncs new/updated
#          skills into ~/.claude/skills/ and pushes to GitHub.

# Skill Sync Hook — OwlWatcher Integration

## Overview

This hook fires whenever the OwlWatcher (the file-system observer in
`scripts/observer.py`) detects a `created` or `modified` event on a file
inside a recognized skill directory. It is the automation bridge between
"a skill appeared on disk" and "that skill is live in Claude Code and on GitHub."

## Hook Registration

Add the following entry to `.claude/settings.json` under `hooks`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python C:/ClaudeSkills/scripts/skill_sync_hook.py --event post-write --file \"${file}\""
          }
        ]
      }
    ],
    "UserPromptSubmit": [],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/ClaudeSkills/scripts/skill_sync_hook.py --event session-end"
          }
        ]
      }
    ]
  }
}
```

The `Stop` hook performs a final sweep at session end to catch any skills
written without triggering a Write/Edit event (e.g., shell copies, MCP tool
file writes).

## Hook Script: scripts/skill_sync_hook.py

The hook script (`scripts/skill_sync_hook.py`) does the following:

### --event post-write (per-file)

1. Receive `--file <path>` from the hook runner
2. Walk up the path to find the containing skill directory (must have `SKILL.md` or `README.md`)
3. If found and the file is in a `SKILL_ROOT_DIR`:
   a. Compute SHA-256 of the skill dir's tracked files
   b. Compare against `cloud/main_cloud.json`
   c. If new or changed:
      - Copy skill dir → `C:/Users/daley/.claude/skills/<skill-name>/`
      - Update `cloud/main_cloud.json` via `broadcaster.build_skill_entry()`
      - Append to `cloud/main_cloud.json` sync_log
      - Fire OwlWatcher `NotificationPolicy` → desktop balloon if threshold met
      - Schedule GitHub push (debounced — max one push per 60 s)

### --event session-end (sweep)

1. Call `broadcaster.discover_skills()` to enumerate all skill dirs
2. For each skill: compare hash against registry
3. Sync any that are new or changed (same steps as above)
4. Run `python scripts/github_sync.py --push` unconditionally if any changes found

## OwlWatcher as Signaler

The OwlWatcher does **not** call `skill_sync_hook.py` directly. Instead:

- `scripts/observer.py` (`SkillChangeHandler._handle_event`) detects the event
- It calls `broadcaster.broadcast_change(event_type, file_path)`
- `broadcast_change` updates the registry and fires the desktop notification
- The Claude Code hook (`PostToolUse: Write|Edit`) is the second signal path,
  catching tool-based writes that the observer may process after a debounce delay

Both paths are intentionally redundant — OwlWatcher guarantees no event is
missed; the Claude Code hook guarantees in-session writes are synced immediately.

## Notification Behavior

Notifications follow the `NotificationPolicy` in `scripts/gui/notification_policy.py`:

| Event | Level | Notified? |
|-------|-------|-----------|
| New skill detected | WARNING | Yes (first occurrence) |
| Skill updated | INFO | No (below min_level) |
| Sync error | CRITICAL | Yes (15 s cooldown) |
| GitHub push failed | CRITICAL | Yes |

Adjust thresholds in `config/watch_config.json` → `notification_policy`.

## Skill Directory Rules

A directory qualifies as a skill if it contains at least one of:
- `SKILL.md`
- `README.md`
- `prompt_template.md`
- `metadata.json`

(Defined in `scripts/broadcaster.py:TRACKED_FILENAMES`)

## Adding New Skill Source Paths

To monitor an additional directory (e.g., a cloud agent output folder):

1. Add the path to `config/watch_config.json` → `watched_paths`
2. Add the path to `scripts/broadcaster.py` → `SKILL_ROOT_DIRS`
3. Restart OwlWatcher: `python scripts/main.py --watch`

No hook changes required — the hook script derives sources from `SKILL_ROOT_DIRS`.

## Files Involved

| File | Role |
|------|------|
| `scripts/observer.py` | OwlWatcher — detects filesystem events |
| `scripts/broadcaster.py` | Registry update + notification dispatch |
| `scripts/skill_sync_hook.py` | Hook handler (to be created) |
| `scripts/github_sync.py` | GitHub push |
| `cloud/main_cloud.json` | Skill registry (hashes + timestamps) |
| `config/watch_config.json` | Watched paths + notification policy |
| `docs/hooks/skill-sync-hook.md` | This file |
| `skills/meta/skill-auto-sync/SKILL.md` | Skill manifest for manual invocation |
