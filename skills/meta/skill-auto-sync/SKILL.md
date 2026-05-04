# skill-auto-sync
# Developer: Marcus Daley
# Date: 2026-05-04
# Purpose: Auto-detect new or updated skills from any source (cloud agent, file drop, MCP,
#          or manual copy) and sync them into ~/.claude/skills/ and this repository.

---
name: skill-auto-sync
version: 1.0.0
description: >
  When invoked, scans all known skill source directories for new or modified skills,
  copies them into the global ~/.claude/skills/ folder, updates cloud/main_cloud.json,
  and commits + pushes the changes to GitHub. The OwlWatcher (scripts/observer.py +
  scripts/broadcaster.py) is the real-time signaler — it detects filesystem events and
  fires broadcast_change(), which this skill's hook handler receives to trigger sync.
category: meta
tags: [skills, sync, automation, owlwatcher, git]
triggers:
  - owlwatcher_skill_event   # fired by skill_sync_hook.py on OwlWatcher detection
  - manual                   # /skill-auto-sync in Claude Code
---

## What This Skill Does

`skill-auto-sync` closes the loop between skill *creation* (anywhere on this machine or
from a cloud/agent pipeline) and skill *availability* (in `~/.claude/skills/` and GitHub).

### Sources Monitored (by OwlWatcher)

| Source | Path Pattern | Event Type |
|--------|-------------|------------|
| Cloud agent drops | `C:/ClaudeSkills/skills/**` | created / modified |
| MCP tool writes | `C:/Users/daley/.claude/skills/**` | created / modified |
| Manual copies | `C:/ClaudeSkills/Example_Skills/**` | created / modified |
| AgenticOS pipelines | `C:/ClaudeSkills/AgenticOS/scripts/**` | created / modified |

### Sync Pipeline

```
OwlWatcher detects SKILL.md created/modified
        │
        ▼
skill_sync_hook.py  ← registered in .claude/settings.json PostToolUse hook
        │  validates: contains SKILL.md or README.md in a skill dir
        │  copies skill dir → ~/.claude/skills/<skill-name>/
        │  runs: python scripts/main.py --sync --confirm
        │  runs: python scripts/github_sync.py --push
        ▼
cloud/main_cloud.json updated (hash + timestamp)
GitHub pushed (GrizzwaldHouse/cowork-skills, branch: master)
Desktop notification via OwlWatcher NotificationPolicy
```

## When to Invoke Manually

Run `/skill-auto-sync` when:
- You've just created a skill via another agent or MCP tool and want immediate sync
- You suspect OwlWatcher missed an event (e.g., bulk file copy)
- After pulling from GitHub and needing to push local additions back

## Steps (Manual Invocation)

1. Scan all `SKILL_ROOT_DIRS` (see `scripts/broadcaster.py:SKILL_ROOT_DIRS`)
2. For each skill dir containing `SKILL.md` or `README.md`:
   - Compare SHA-256 hash against `cloud/main_cloud.json` entry
   - If new or changed: copy to `~/.claude/skills/<name>/`
3. Run `python scripts/main.py --sync --confirm` to update registry
4. Run `python scripts/github_sync.py --push` to push to GitHub
5. Report: N skills synced, M unchanged, any errors

## Configuration

Skill source paths are controlled by `config/watch_config.json` (`watched_paths`) and
`scripts/broadcaster.py` (`SKILL_ROOT_DIRS`). To add a new source, append to both.

## Dependencies

- `scripts/observer.py` — OwlWatcher filesystem events
- `scripts/broadcaster.py` — registry update + notification
- `scripts/skill_sync_hook.py` — hook handler (see hooks/skill-sync-hook.md)
- `scripts/github_sync.py` — GitHub push
- `cloud/main_cloud.json` — skill registry
