# CLAUDE.md - Claude Skills System

## Project Overview

A modular system for creating, managing, and syncing Claude AI skill templates. Includes a file watcher, bidirectional sync engine, GitHub integration, and a themed WPF desktop UI with console fallback.

## Tech Stack

- **Language**: Python 3.10+
- **UI**: WPF (XAML) with console fallback (ANSI colors)
- **Sync**: Git-based with hash change detection
- **Platform**: Windows 11 (primary), cross-platform CLI

## Key Directories

- `scripts/` - Python CLI and sync engine (main.py is the entry point)
- `Example_Skills/` - Pre-built skill definitions (6 categories)
- `Skill_Creator/` - Meta-template for creating new skills
- `cloud/` - Sync registry (main_cloud.json stores metadata/hashes/timestamps)
- `config/` - Configuration (watch_config.json)
- `UI_Templates/` - WPF XAML templates
- `skills/` - Active skill packages (canva-designer, design-system, document-designer)
- `Prompts/` - Prompt templates
- `security/` - Security audit logs

## Architecture

- `scripts/main.py` - CLI entry point, orchestrates all modules
- `scripts/observer.py` - File watcher (watchdog)
- `scripts/broadcaster.py` - Bidirectional sync engine
- `scripts/sync_utils.py` - Shared utilities
- `scripts/github_sync.py` - GitHub integration (remote: GrizzwaldHouse/cowork-skills)
- `scripts/ui_launcher.py` - WPF UI launcher
- `scripts/ui_console_fallback.py` - Console fallback UI

## Commands

```bash
python scripts/main.py --preview           # Show pending changes
python scripts/main.py --watch             # Start file watcher
python scripts/main.py --sync --confirm    # Run sync cycle
python scripts/main.py --github --confirm  # Push to GitHub
python scripts/main.py --rollback <ts>     # Restore from backup
```

## Conventions

- All file writes use atomic temp-then-rename for crash safety
- Advisory file locks prevent concurrent write corruption
- Timestamped backups are created before overwrites
- Skill files prefer local copy during conflict resolution
- Base directory is hardcoded as `C:/ClaudeSkills`
- GitHub remote: `https://github.com/GrizzwaldHouse/cowork-skills.git` (branch: main)

## Development Notes

- Do not modify `cloud/main_cloud.json` manually; it is managed by the sync engine
- `config/watch_config.json` controls watched paths and ignored patterns
- Logs go to `logs/` directory (gitignored)
- Backups go to `backups/` directory (gitignored)
- The `.env` file contains sensitive configuration and must never be committed
