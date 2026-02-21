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
    sync_utils.py                     #   Shared utilities (hashing, atomic writes, locking)
    github_sync.py                    #   GitHub integration
    config_manager.py                 #   Centralized config loading
    log_config.py                     #   Centralized logging setup
    watcher_core.py                   #   Shared filtering logic (transient files, ignored patterns)
    ui_launcher.py                    #   WPF UI launcher
    ui_console_fallback.py            #   Console fallback UI
    requirements.txt                  #   Python dependencies
    gui/                              #   Desktop GUI modules (PyQt6)
      app.py                          #     Main GUI application orchestrator
      main_window.py                  #     Primary dashboard window
      owl_state_machine.py            #     8-state owl mascot FSM
      security_engine.py              #     Threat detection and integrity checking
      watcher_thread.py               #     Background file watcher thread
      tray_icon.py                    #     System tray icon with badges
      sound_manager.py                #     Sound effect playback
      speech_messages.py              #     Randomized owl messages
      generate_sounds.py              #     Procedural WAV generation
      constants.py                    #     All magic numbers, colors, thresholds
      paths.py                        #     Path constants (BASE_DIR, ASSETS_DIR)
      widgets/                        #     Dashboard widgets
        owl_widget.py                 #       Animated owl mascot
        stats_strip.py                #       Composite stats bar
        sparkline_widget.py           #       Event frequency chart
        donut_widget.py               #       File type breakdown
        gauge_widget.py               #       Threat score arc
        flame_widget.py               #       Uptime intensity
        ambient_widget.py             #       Night-sky background
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

## Architecture

### Core Principles (CLAUDE.md Standards)

All code follows strict architectural standards:
- **Configuration-Driven**: No hardcoded values. All constants in `scripts/gui/constants.py` and config loaded via `config_manager.py`
- **Signal-Based Communication**: Qt signals for all inter-component messaging (no polling loops)
- **Graceful Degradation**: Sound system works without QtMultimedia, security engine is optional
- **Atomic Operations**: All file writes use temp-then-rename for crash safety
- **Advisory Locking**: Prevents concurrent write corruption

### Centralized Modules

Refactored from duplicate implementations to single sources of truth:

- **`config_manager.py`**: Loads `watch_config.json` with defaults. Used by observer, watcher_thread, and main.
- **`log_config.py`**: Configures logging format once. Idempotent (safe to call multiple times).
- **`watcher_core.py`**: Shared filtering logic (`is_transient()`, `matches_ignored()`, `should_process()`). Eliminates duplication between observer and watcher_thread.
- **`gui/constants.py`**: All magic numbers, colors, thresholds. Extracted from 20+ files during refactoring.
- **`gui/paths.py`**: Path constants (BASE_DIR, ASSETS_DIR) for all GUI modules.

### OwlWatcher GUI (PyQt6)

The desktop GUI is a themed file security monitor with an animated owl mascot:

- **8-State FSM**: `SLEEPING → WAKING → SCANNING → CURIOUS/ALERT/ALARM/PROUD` with auto-return transitions
- **Real-Time Monitoring**: Background QThread runs watchdog observer, emits Qt signals for events
- **Threat Detection**: SHA-256 integrity baselines, burst detection, suspicious extension checks
- **Dashboard Widgets**: Sparkline charts, donut breakdowns, arc gauges, flame uptime, ambient night-sky
- **Sound Effects**: Procedurally generated WAV files (startup_hoot, alert_chirp, alarm_hoot, allclear_settle)
- **Speech Bubbles**: Randomized owl messages for each state, with 5% humor variants

## Requirements

- Python 3.10+
- Git 2.x+ (for GitHub sync)
- PyQt6 6.x+ (for OwlWatcher GUI)
- .NET Runtime 6.0+ (optional, for legacy WPF UI)

## Documentation

See [Installation_Workflow_Guide/guide.md](Installation_Workflow_Guide/guide.md) for detailed setup, configuration, and troubleshooting instructions.

See [Skill_Creator/README.md](Skill_Creator/README.md) for how to create new skills.
