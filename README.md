# Claude Skills System

A modular system for creating, managing, and syncing Claude AI skill templates. Includes a file watcher, bidirectional sync engine, GitHub integration, and a themed WPF desktop UI with console fallback.

## Quick Start

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Preview current state
python scripts/main.py --preview

# Start the file watcher
python scripts/main.py --watch

# Run a sync cycle
python scripts/main.py --sync --confirm

# Push to GitHub
python scripts/main.py --github --confirm
```

## Folder Structure

```
C:/ClaudeSkills/
  README.md                           # This file
  Skill_Creator/                      # Meta-template for creating new skills
    SKILL.md                          #   Canonical skill template
    README.md                         #   How to create new skills
  Example_Skills/                     # Pre-built skill definitions
    frontend-ui-helper/               #   Front-end UI generation
    backend-workflow-helper/           #   Back-end API and workflow help
    game-dev-helper/                  #   UE5, Unity, Godot assistance
    workflow-productivity/            #   Automation and scripting
    documentation-blog-generator/     #   Docs and blog content generation
    notion-figma-integration/         #   Notion/Figma bridge workflows
  Blog_Automation_Prompt/             # Blog generation prompt template
    prompt_template.md                #   Ready-to-use blog prompt
    README.md
  cloud/                              # Sync registry
    main_cloud.json                   #   Skill metadata, hashes, timestamps
  config/                             # Configuration
    watch_config.json                 #   Watch paths and filters
  scripts/                            # Python scripts
    main.py                           #   CLI entry point
    observer.py                       #   File watcher (watchdog)
    broadcaster.py                    #   Sync engine
    sync_utils.py                     #   Shared utilities
    github_sync.py                    #   GitHub integration
    ui_launcher.py                    #   WPF UI launcher
    ui_console_fallback.py            #   Console fallback UI
    requirements.txt                  #   Python dependencies
  UI_Templates/                       # WPF XAML templates
    frontend-ui-template.xaml         #   Main skill manager window
    progress-bar-template.xaml        #   Sync progress dialog
  Installation_Workflow_Guide/        # Documentation
    guide.md                          #   Full installation and usage guide
  backups/                            # Timestamped file backups
  logs/                               # Sync log files
  dist/                               # Distribution packages
```

## Key Features

- **File Watcher**: Monitors skill directories for changes using watchdog
- **Bidirectional Sync**: Updates cloud registry from disk and vice versa, with hash-based change detection
- **GitHub Integration**: Commit, push, pull with auto-conflict resolution (skill files prefer local)
- **Themed UI**: Submarine/Harry Potter themed WPF desktop UI with gold-on-navy color scheme
- **Console Fallback**: Full-featured console UI with ANSI colors when WPF is not available
- **Desktop Notifications**: Optional toast notifications via plyer on sync events
- **Backup & Rollback**: Timestamped backups before overwrites, with CLI restore command
- **Atomic Writes**: All file operations use temp-then-rename for crash safety
- **File Locking**: Advisory locks prevent concurrent write corruption

## Requirements

- Python 3.10+
- Git 2.x+ (for GitHub sync)
- .NET Runtime 6.0+ (optional, for WPF UI)

## Documentation

See [Installation_Workflow_Guide/guide.md](Installation_Workflow_Guide/guide.md) for detailed setup, configuration, and troubleshooting instructions.

See [Skill_Creator/README.md](Skill_Creator/README.md) for how to create new skills.
