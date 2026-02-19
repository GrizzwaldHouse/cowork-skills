# Claude Skills System - Installation & Workflow Guide

## Prerequisites

Before installing, ensure you have the following:

| Requirement         | Version    | Notes                                      |
|---------------------|------------|--------------------------------------------|
| Python              | 3.10+      | Required for all scripts                   |
| pip                 | Latest     | Python package manager                     |
| Git                 | 2.x+       | Required for GitHub sync                   |
| .NET Runtime        | 6.0+       | Optional, required for WPF UI (Windows)    |

### Optional Dependencies

- **pythonnet** - Enables the themed WPF graphical UI. Without it, a console-based fallback is used.
- **plyer** - Enables desktop notifications on sync events.

---

## Installation

### Step 1: Clone or Extract

If you received the ZIP package:

```powershell
Expand-Archive -Path claude-skills-system.zip -DestinationPath C:\ClaudeSkills
```

Or clone from GitHub:

```bash
git clone https://github.com/GrizzwaldHouse/cowork-skills.git C:/ClaudeSkills
```

### Step 2: Install Python Dependencies

```bash
cd C:/ClaudeSkills/scripts
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `watchdog` - File system monitoring
- `pythonnet` - WPF UI (optional, system falls back to console without it)
- `plyer` - Desktop notifications (optional)

### Step 3: Verify Installation

```bash
python C:/ClaudeSkills/scripts/main.py --preview
```

You should see a diff summary showing all registered skills.

---

## Configuration

### Watch Paths

Edit `C:/ClaudeSkills/config/watch_config.json` to configure which directories are monitored:

```json
{
  "watched_paths": ["C:/ClaudeSkills"],
  "ignored_patterns": ["__pycache__", ".git", "*.pyc", "backups", "logs", "dist"],
  "sync_interval": 5,
  "enabled_skills": []
}
```

| Field             | Description                                                  |
|-------------------|--------------------------------------------------------------|
| `watched_paths`   | Directories to monitor for file changes                      |
| `ignored_patterns`| File/folder names or glob patterns to skip                   |
| `sync_interval`   | Minimum seconds between processing events for the same file  |
| `enabled_skills`  | Limit sync to specific skill names (empty = all skills)      |

### Adding a Secondary Watch Path

The observer automatically detects `D:/Portfolio/Projects` if it exists. To add other paths, edit `watch_config.json`.

---

## Usage

### Start the File Watcher

Monitors your skill directories and triggers sync on file changes:

```bash
python C:/ClaudeSkills/scripts/main.py --watch
```

Press `Ctrl+C` to stop.

### Run a One-Time Sync

Update the cloud registry from current files on disk:

```bash
python C:/ClaudeSkills/scripts/main.py --sync
```

Add `--confirm` to apply changes (without it, runs in preview mode):

```bash
python C:/ClaudeSkills/scripts/main.py --sync --confirm
```

### Preview Pending Changes

See what would change without applying anything:

```bash
python C:/ClaudeSkills/scripts/main.py --preview
```

### Push to GitHub

Dry-run (default) -- shows what would be committed:

```bash
python C:/ClaudeSkills/scripts/main.py --github
```

Actually commit and push:

```bash
python C:/ClaudeSkills/scripts/main.py --github --confirm
```

Push with a version tag:

```bash
python C:/ClaudeSkills/scripts/main.py --github --confirm --tag v1.0.0
```

First push to a new empty repository:

```bash
python C:/ClaudeSkills/scripts/main.py --github --confirm --skip-pull
```

### Restore from Backup

List available backups and restore a specific timestamp:

```bash
python C:/ClaudeSkills/scripts/main.py --rollback 20260217T120000Z
```

If you are unsure of the timestamp, run the command with an invalid value to see available backups.

---

## GitHub Integration Setup

### Step 1: Create a Repository

Create a new repository on GitHub (e.g., `cowork-skills`).

### Step 2: Configure the Remote

The default remote URL is `https://github.com/GrizzwaldHouse/cowork-skills.git`. To use a different repository, pass `--remote` to the GitHub sync script directly:

```bash
python C:/ClaudeSkills/scripts/github_sync.py --remote https://github.com/youruser/yourrepo.git --confirm
```

### Step 3: Authentication

For HTTPS, Git will prompt for credentials. For repeated use, configure a credential helper:

```bash
git config --global credential.helper manager
```

For SSH, ensure your SSH key is added to your GitHub account.

---

## Creating New Skills

1. Copy the template from `Skill_Creator/SKILL.md` into a new folder under `Example_Skills/`.
2. Fill in all sections: Name, Description, Prerequisites, Usage, Examples, Configuration.
3. Add a `README.md` with an overview and quick-start guide.
4. Create a `resources/` subfolder for supporting files.
5. Run `--sync --confirm` to register the new skill in the cloud registry.

See `Skill_Creator/README.md` for detailed instructions.

---

## Troubleshooting

### "No module named 'watchdog'"

Install dependencies:

```bash
pip install -r C:/ClaudeSkills/scripts/requirements.txt
```

### WPF UI does not appear

This requires pythonnet and a .NET runtime on Windows. Install with:

```bash
pip install pythonnet
```

If the .NET runtime is missing, install it from [dotnet.microsoft.com](https://dotnet.microsoft.com/download).

The system automatically falls back to a console UI if WPF is not available.

### "Config file not found" warning

Create the config file at `C:/ClaudeSkills/config/watch_config.json` using the template shown in the Configuration section above.

### Git push fails

- Verify the remote URL: `git remote -v` (run from `C:/ClaudeSkills`)
- Ensure you have write access to the repository
- If the remote branch does not exist yet, use `--skip-pull`

### Sync log grows too large

The broadcaster automatically caps `sync_log` entries at 500. The file-level sync log at `C:/ClaudeSkills/logs/sync_log.json` can be cleared manually if needed.

---

## Architecture Overview

```
main.py          -- CLI entry point, dispatches commands
observer.py      -- File watcher (watchdog), detects changes
broadcaster.py   -- Sync engine, updates cloud registry, propagates changes
sync_utils.py    -- Shared utilities (hashing, locking, atomic writes, backups)
github_sync.py   -- Git operations (pull, commit, push, conflict resolution)
ui_launcher.py   -- WPF dialog launcher (or console fallback)
ui_console_fallback.py -- Console-based progress UI
```
