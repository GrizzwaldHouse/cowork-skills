# Cowork Skills

Claude Code skills and task templates for professional design, document generation, coding standards, security engineering, desktop UI development, and game development.

## Quick Setup

Clone this repo on any machine, then run the setup script to install skills globally:

```bash
# Clone
git clone https://github.com/GrizzwaldHouse/cowork-skills.git
cd cowork-skills

# Install (Linux/macOS/Git Bash)
./setup.sh

# Install (Windows PowerShell)
.\setup.ps1
```

Skills install to `~/.claude/skills/` and are available in **all** Claude Code sessions on that machine.

To update: `git pull && ./setup.sh`

## Skills

### Background Skills (auto-loaded)

These skills load automatically when Claude detects a relevant task. No invocation needed.

#### design-system
Foundational design principles applied automatically to all visual and document tasks.
- Color theory (WCAG contrast, 60-30-10 rule, 6 ready-to-use palettes)
- Typography (font pairings, type scale, readability rules)
- Layout (8px grid, 12-column system, composition patterns)
- Accessibility standards

#### document-designer
Professional formatting for Excel, Word, PowerPoint, and PDF generation.
- Excel: sheet organization, data formatting, dashboard patterns
- Word: memo, report, proposal, meeting minutes templates
- PowerPoint: 6x6 rule, slide templates, content writing rules
- PDF: layout standards, document type templates

#### universal-coding-standards
Non-negotiable coding rules that apply to every project across all languages.
- Access control and encapsulation (most restrictive access by default)
- Initialization discipline (all defaults at construction, no magic numbers)
- Event-driven communication (Observer pattern, never polling)
- Dependency management and comment standards
- Language-specific guidance for C++, C#, Python, TypeScript, Rust, Java, Go, React

#### architecture-patterns
Design patterns, file organization, and UI architecture standards.
- Six core patterns: Observer, composition, interface-driven, data-driven, repository, separation of concerns
- UI architecture rules (MVC/MVVM separation)
- File organization conventions by project type
- Language-specific implementations for each pattern

#### dev-workflow
Development workflow standards and session management.
- Brainstorm-first methodology (research before code)
- Build/tooling rules and testing philosophy
- Version control conventions and logging standards
- Systematic debugging methodology
- Problem Tracker and Lessons Learned templates

#### enterprise-secure-ai-engineering
Enterprise-grade security guardrails aligned with OWASP, NIST SSDF, SLSA, and SOC2.
- Runtime safety and dependency hygiene
- Secure coding practices (parameterized queries, Zod validation, no custom crypto)
- Web application protections (rate limiting, server action hardening)
- AI-generated code governance (review thresholds, placeholder detection)

### User-Invocable Skills

These skills are triggered by typing the slash command in Claude Code.

#### canva-designer (`/canva-designer`)
Canva-specific prompt engineering for higher quality design generation.
- Query templates for every design type (logo, presentation, poster, social media)
- Platform dimensions reference (Instagram, LinkedIn, YouTube, print, etc.)
- Quality checklist for pre-commit review

#### desktop-ui-designer (`/desktop-ui-designer`)
Design and implement modern desktop applications using PyQt6/PySide6.
- Main windows, dialogs, custom widgets, themes, animations
- Event-driven architecture with signals/slots
- System tray integration and cross-platform compatibility
- Minimal app template and requirements included

#### pyqt6-ui-debugger (`/pyqt6-ui-debugger`)
Systematic debugging for PyQt6 user interface issues.
- Layout constraint analysis and size policy debugging
- Widget visibility, clipping, and z-order troubleshooting
- Signal/slot connection verification
- Debug helpers and common issues checklist included

#### python-code-reviewer (`/python-code-reviewer`)
Automated Python code review against universal coding standards.
- Severity-rated violation reports with line numbers
- Checks access control, initialization, type hints, error handling
- Identifies anti-patterns and security issues
- Example files for access control, initialization, communication, and error handling

## Task Templates

Pre-built task checklists for common workflows:

| Category | File | What's Included |
|----------|------|-----------------|
| App Development | `tasks/app-development/tasks.md` | Feature implementation, bug fixes, UI upgrades, API endpoints, deployment |
| AI Workflows | `tasks/ai-workflows/tasks.md` | Canva generation, document creation, prompt engineering, agent safety review |
| Game Development | `tasks/game-development/tasks.md` | Level design, Unreal Blueprints, AI agents, HUD/UI, multiplayer, optimization |

## How It Works

**Background skills** (`design-system`, `document-designer`, `universal-coding-standards`, `architecture-patterns`, `dev-workflow`, `enterprise-secure-ai-engineering`) load automatically whenever Claude detects a relevant task. You don't need to do anything.

**User-invocable skills** (`canva-designer`, `desktop-ui-designer`, `pyqt6-ui-debugger`, `python-code-reviewer`) are triggered by typing the slash command in Claude Code:
```
/canva-designer
/desktop-ui-designer
/pyqt6-ui-debugger
/python-code-reviewer
```

**Task templates** are reference checklists. Copy the relevant section into your project or reference them when planning work.

## Multi-Agent System

The `scripts/` directory contains a Python-based multi-agent runtime that coordinates specialized agents (extractor, validator, refactor, sync, pruner) over a shared typed event bus. Agents communicate via `EventBus.publish` with handler-level exception isolation so one bad handler can't stall the pipeline.

Security-sensitive components are covered by unit tests in `tests/`:

| Component | File | Tests | Purpose |
|---|---|---|---|
| EventBus | `scripts/agent_event_bus.py` | `tests/test_agent_event_bus.py` | Typed pub/sub with RLock + snapshot dispatch |
| SkillIsolator | `scripts/skill_isolator.py` | `tests/test_skill_isolator.py` (93 tests) | Per-agent skill manifest writer with strict path-traversal validation (CWE-22/41/66) |
| Extractor agent | `scripts/agents/extractor_agent.py` | `tests/test_extractor_agent.py` | Skill extraction pipeline |
| Validator agent | `scripts/agents/validator_agent.py` | `tests/test_validator_agent.py` | Skill validation against security rules |
| Sandbox manager | `scripts/testing/sandbox_manager.py` | `tests/test_sandbox_manager.py` | Process isolation for untrusted code |

Run the security-critical SkillIsolator tests directly:
```bash
py -3 tests/test_skill_isolator.py   # 93 assertions, path-traversal + TOCTOU hardening
```

Run the pytest-based tests:
```bash
py -3 -m pytest tests/test_agent_event_bus.py tests/test_sandbox_manager.py
```

## Structure

```
cowork-skills/
  skills/
    design-system/                      # Color, typography, layout, accessibility
    canva-designer/                     # Canva prompt engineering & quality review
    document-designer/                  # Excel, Word, PPT, PDF best practices
    universal-coding-standards/         # Access control, init, events, anti-patterns
    architecture-patterns/              # Observer, composition, data-driven, repo pattern
    dev-workflow/                       # Brainstorm-first, debugging, version control
    enterprise-secure-ai-engineering/   # OWASP, NIST, SLSA, SOC2 guardrails
    desktop-ui-designer/                # PyQt6/PySide6 desktop app patterns
    pyqt6-ui-debugger/                  # PyQt6 layout & widget debugging
    python-code-reviewer/               # Python standards compliance review
  scripts/
    agent_event_bus.py                  # Typed pub/sub for inter-agent communication
    agent_events.py                     # Event dataclasses
    agent_runtime.py                    # Agent orchestration
    skill_isolator.py                   # Per-agent skill manifests (path-traversal hardened)
    agents/                             # Extractor, validator, refactor, sync, pruner agents
  tests/                                # Unit and security tests (pytest + standalone scripts)
  tasks/
    app-development/      # Feature dev, bug fix, UI upgrade, API, deploy
    ai-workflows/         # Design gen, doc creation, prompt eng, safety
    game-development/     # Level design, Unreal, AI, HUD, multiplayer
  setup.sh                # Linux/macOS/Git Bash installer
  setup.ps1               # Windows PowerShell installer
```

## Multi-Machine Sync

1. Push changes from any machine: `git add -A && git commit -m "update skills" && git push`
2. Pull on other machine: `git pull && ./setup.sh`

That's it. Both machines stay in sync.

## License

MIT
