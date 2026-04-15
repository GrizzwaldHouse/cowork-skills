# OwlWatcher Intelligence Pipeline - Fresh Chat Prompt

Copy everything below the line into a new Claude Code chat.

---

## Project Context

I'm working on **OwlWatcher**, a PyQt6 file security monitor at `C:\ClaudeSkills`. It has been extended with a 6-layer AI Self-Improvement Pipeline that observes Claude Code sessions across multiple project directories, extracts reusable "Quad Skills," validates them through security + architecture + quality gates, installs approved skills to shape future Claude behavior (the "OpenModel"), provides admin governance with approval/rejection/rollback workflows, and auto-syncs to GitHub.

## Architecture: 6-Layer Signal Pipeline

```
Layer 1: OBSERVATION     → SessionObserver (scripts/session_observer.py)
Layer 2: EXTRACTION      → QuadSkillEngine (scripts/quad_skill_engine.py)
Layer 3: VALIDATION      → ValidationEngine (scripts/validation_engine.py)
Layer 4: SAFETY          → AISafetyGuard (scripts/ai_safety_guard.py)
Layer 5: GOVERNANCE      → AdminControlProtocol (scripts/admin_protocol.py)
Layer 6: INTEGRATION     → OpenModelManager (scripts/open_model_manager.py)
```

All modules use PyQt6 signal/slot event-driven architecture. No polling. Safety guard is instantiated before all other intelligence modules.

## Key Files

**Core Intelligence Modules** (`C:\ClaudeSkills\scripts\`):
- `ai_safety_guard.py` — Safety invariant enforcement (blocked patterns: eval, exec, os.system, subprocess, __import__). Core skill overwrite protection. Path confinement. Immutable audit trail.
- `session_observer.py` — Detects Claude sessions from file events (.claude/plans/, MEMORY.md, CLAUDE.md, git commits). Watches: D:\Agent-Alexander, D:\BrightForge, C:\Users\daley\Projects\Bob-AICompanion, C:\ClaudeSkills.
- `quad_skill_engine.py` — Extracts QuadSkill dataclasses from plans, diffs, and memory files. Jaccard dedup (0.85 threshold). Max 5 skills per session.
- `validation_engine.py` — Architecture scoring, security scoring, quality scoring. Auto-approve >= 0.7 confidence + 0.9 security. Reject <= 0.5 security.
- `admin_protocol.py` — Multi-reviewer governance (ADMIN/REVIEWER/OBSERVER roles). Approval queue, audit trail, rollback support.
- `open_model_manager.py` — Installs approved skills to ~/.claude/skills/ and C:\ClaudeSkills\skills/. Atomic writes. GitHub sync. Rollback.

**GUI** (`C:\ClaudeSkills\scripts\gui\`):
- `intelligence_panel.py` — New "Intelligence" tab: session monitor, skill queue, validation status, safety log.
- `widgets/skill_card_widget.py` — Card widget for skill display with approve/reject buttons.
- `widgets/session_timeline_widget.py` — Timeline showing session activity per watched project.
- `app.py` — Signal wiring hub (modified to wire intelligence pipeline).
- `main_window.py` — QTabWidget with "Monitor" + "Intelligence" tabs.
- `owl_state_machine.py` — 11 states including LEARNING, VALIDATING, SYNCING (added to existing 8).

**Config** (`C:\ClaudeSkills\config\`):
- `intelligence_config.json` — Session detection, extraction thresholds, safety rules, sync settings.
- `admin_config.json` — Reviewer profiles, approval rules, notification settings.
- `watch_config.json` — Watched paths (4 project dirs), ignored patterns.

**Tests** (`C:\ClaudeSkills\tests\`):
- 8 test files, 242 tests all passing. Covers safety guard, session observer, quad skill engine, validation engine, admin protocol, open model manager.

**Data** (`C:\ClaudeSkills\data\`):
- `quad_skills/`, `pending_review/`, `approved/`, `rejected/`, `sessions/` — Pipeline data directories.
- `training_log.json` — All OpenModel update history.

## State Machine

11 states: SLEEPING, WAKING, IDLE, SCANNING, CURIOUS, ALERT, ALARM, PROUD, LEARNING, VALIDATING, SYNCING. Auto-return timers prevent stuck states.

## Beta Team (QA Skills)

5 invocable Claude Code skills at `C:\ClaudeSkills\skills\beta-team-*/`:
- `/beta-team-code-debugger` — 5-phase code audit (discovery, static analysis, dependency, standards, bug hunt)
- `/beta-team-db-tester` — 6-phase DB audit (schema, queries, migrations, connections, integrity)
- `/beta-team-path-tester` — 6-phase path audit (routes, endpoints, traversal, navigation, auth boundaries)
- `/beta-team-ui-tester` — Playwright UI/UX audit (screenshots, accessibility, interactions, dark mode, performance)
- `/beta-team-button-pusher` — Playwright chaos testing (element census, button push, form chaos, toggle tornado, rapid fire)

## CLI

```bash
python scripts/main.py --watch            # File watcher
python scripts/main.py --intelligence     # GUI with AI pipeline
python scripts/main.py --sync --confirm   # Sync cycle
python scripts/main.py --github --confirm # Push to GitHub
python scripts/main.py --eval <SKILL>     # Eval assertions
python scripts/main.py --self-improve <SKILL>  # Skill improvement loop
```

## Tech Stack

- Python 3.10+, PyQt6, watchdog, pytest
- Windows 11, Git, GitHub (GrizzwaldHouse/cowork-skills)
- Playwright (for Beta Team UI/button skills)

## Coding Standards

- Event-driven (Observer pattern, never polling)
- Most restrictive access by default
- All defaults at construction, no magic numbers
- Atomic file writes (temp + rename)
- Dependency injection over hard-coded instantiation
- `//` or `#` line comments only, explain WHY not WHAT

## What's Next

The intelligence pipeline is fully implemented and all 242 tests pass. Possible next steps:
1. End-to-end integration testing with a live session
2. Rebuild the PyInstaller exe (`python build_owlwatcher.py`)
3. Windows startup auto-launch configuration
4. GitHub sync of all new files
5. Enhance QuadSkillEngine extraction with real Claude session artifacts
6. Build the skill-self-improver feedback loop (eval -> extract -> validate -> install -> re-eval)
