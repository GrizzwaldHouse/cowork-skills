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
- `skills/` - Active skill packages (canva-designer, design-system, document-designer, universal-coding-standards, architecture-patterns, dev-workflow, enterprise-secure-ai-engineering, desktop-ui-designer, pyqt6-ui-debugger, python-code-reviewer, vault-analysis, verified-build-gate, ai-agents/agentic-parallel)
- `tasks/` - Reusable task checklists (agentic-parallel, ai-workflows, app-development)
- `AgenticOS/` - AgenticOS Command Center (FastAPI state bus, WPF tray launcher, React + Vite frontend with Spline 3D HUD)
- `docs/superpowers/plans/` - Locked plan files (state-bus, wpf-launcher, react-frontend, spline-integration, skill-templates, cowork-three-audience-setup)
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
- GitHub remote: `https://github.com/GrizzwaldHouse/cowork-skills.git` (branch: master)

## Canonical agent sources (binding)

Consult before improvising standards or workflows. Full table and sync cadence: [`docs/CANONICAL_SOURCES.md`](docs/CANONICAL_SOURCES.md).

- **Skills & templates (Git):** https://github.com/GrizzwaldHouse/cowork-skills.git — edit locally at `C:\ClaudeSkills`, sync with `git pull` and `setup.ps1` / `setup.sh`.
- **Workflow skills (Git):** https://github.com/obra/superpowers.git — align brainstorming/TDD/verification when not conflicting with Marcus Universal Coding Standards or `brainstorm-artifact`; on conflict, those win (see `docs/CANONICAL_SOURCES.md` precedence).
- **Claude Code session tooling:** https://github.com/IyadhKhalfallah/clauditor.git — protects quota/context window in Claude Code (install via npm package `@iyadhk/clauditor`, run `clauditor install`).
- **ML Hub:** https://huggingface.co/ — use Hugging Face MCP (`plugin-huggingface-skills-huggingface-skills`) for Hub-related tasks instead of guessing APIs.
- **Brainstorm skill:** `skills/brainstorm-artifact/` — scope-lock checklist; locked docs `docs/BRAINSTORM_[YYYY-MM-DD].md`; no implementation until Marcus confirms (see **Brainstorming Artifact Standard** below).

## Development Notes

- Do not modify `cloud/main_cloud.json` manually; it is managed by the sync engine
- `config/watch_config.json` controls watched paths and ignored patterns
- Logs go to `logs/` directory (gitignored)
- Backups go to `backups/` directory (gitignored)
- The `.env` file contains sensitive configuration and must never be committed

## Developer

- **Name**: Marcus Daley
- **Background**: Navy veteran (9 years leadership), Full Sail graduate (BS Online Game Development, Feb 6 2026), stay-at-home dad
- **Focus**: Portfolio-focused developer specializing in C++ and game development, applying AAA studio practices universally
- **Instructor Influence**: Nick Penney (Full Sail University) - AAA Studio Practices

## Coding Standards (Universal)

These rules apply to ALL code in this project and any project Marcus works on. See the `skills/universal-coding-standards/`, `skills/architecture-patterns/`, and `skills/dev-workflow/` skill packages for comprehensive details.

### Core Philosophy

- **The 95/5 Rule**: 95% of code should be reusable across projects without modification. Only 5% should be project-specific configuration.
- **Quality Over Speed**: Never suggest shortcuts or 'quick and dirty' solutions. This is portfolio work where architectural quality matters more than delivery speed. Refactoring is encouraged.
- **Brainstorm First**: Any feature request begins with research, not code. Research built-in solutions, generate multiple approaches, discuss trade-offs, design architecture, THEN implement.
- **Configuration-Driven Design**: NEVER hardcode values that could change. Use config files, environment variables, constructor parameters, or data stores.
- **Learning Through Understanding**: Explain WHY code is structured a particular way. Explain architectural reasoning behind every choice.
- **Maximum Sophistication**: NEVER suggest minimal, simple, or "good enough" designs. Always research and implement the most advanced, feature-rich, and sophisticated approach available. Push technical boundaries and explore cutting-edge solutions.

### Critical Rules (NEVER Violate)

- **Access Control**: Every property/method gets the most restrictive access level that allows it to function. NEVER expose unrestricted mutable public state.
- **Initialization**: ALL default values set at point of construction. NEVER use magic numbers or magic strings.
- **Communication**: Systems communicate through events/callbacks/delegates (Observer pattern), NEVER through polling.
- **Dependencies**: Minimize imports in declaration files. Use dependency injection over hard-coded instantiation. Prefer composition over inheritance.
- **Comments**: Explain WHY (design decisions), not WHAT (obvious syntax). Use `//` or `#` line comments. Block comments only for API documentation.
- **File Headers**: Every source file gets a header: filename, developer (Marcus Daley), date, purpose.

### Anti-Patterns (NEVER Do)

- Unrestricted mutable public state
- Default values scattered across the codebase
- Polling loops to detect state changes
- Hardcoded configuration values (magic numbers, strings, URLs)
- Block comments for code explanation (/* */ for flow, not API docs)
- Comments explaining WHAT code does (obvious from syntax)
- Modifying shared/global build config for project-specific needs
- Assuming time pressure or suggesting 'quick and dirty' solutions
- Global mutable state (singletons with mutable state, god objects)
- Catching and swallowing errors silently
- Committing secrets, .env files, or API keys

## Enterprise Secure AI Engineering

Active on all sessions. See `skills/enterprise-secure-ai-engineering/` for full guardrails. Aligned with OWASP Top 10, NIST SSDF, SLSA, SOC2.

### Security Guardrails (Always Enforced)

- **No hardcoded credentials or secrets** in source code -- use env vars and secret managers
- **Parameterized queries only** -- never dynamic SQL or string-interpolated queries
- **Server-side validation required** -- never rely on client-side validation alone
- **No custom crypto or auth** -- use established libraries (NextAuth, Clerk, bcrypt, etc.)
- **No sensitive data in logs** -- mask passwords, tokens, PII
- **Debug disabled in production** -- hide stack traces in error responses

### AI Code Governance

- AI-generated code over 350 lines requires a dedicated review pass
- Scan for hallucinated functions, placeholder comments, race conditions, and edge cases
- Use CodeRabbit or equivalent for automated PR audit

### Web Application Protections (Next.js / Node)

- ALL Next.js server actions are public endpoints -- apply auth + Zod validation + rate limiting
- Rate limiting required on all public endpoints (Arcjet or equivalent)
- Proxy middleware required for external API calls
- Recommended stack: Zustand (client state), TanStack Query (server state), Drizzle ORM (DB), Zod (validation)

## Agent Behavior

- Start with "What approach do you want to explore?" rather than immediately coding
- Research if the language/framework has a built-in solution FIRST
- Suggest 3-5 different approaches with trade-offs before implementing
- Design architecture before writing code
- Provide complete, working implementations with human-style comments
- Explain the WHY behind architectural decisions
- Never use time-pressure language ('quick and dirty', 'just get it working', 'for now')
- Encourage refactoring as a portfolio investment
- If Marcus wants something ambitious, explore how rather than discouraging
- When Marcus already knows something, don't over-explain it
- Provide complete, compilable/runnable code, not pseudo-code snippets
- When debugging, help systematically: clarify, find root cause, explain, suggest prevention
- Document significant bugs in Problem Tracker format (symptom, cause, solution, prevention)
- **NEVER suggest minimal or simplified designs** -- always research the most advanced, sophisticated, and feature-rich approach. Marcus wants cutting-edge, production-grade implementations with maximum capabilities

---

# DeepCommand Skills System

## Core Principles
- Event-driven only
- No polling
- Config-driven architecture
- No hardcoded values
- Production-ready outputs only
- Continuous validation

---

## Agent Roles

### Planner
- Defines milestones
- Breaks into parallel tasks
- Prioritizes playable demo progress

### Implementer
- Writes Unreal C++ systems
- Ensures Blueprint compatibility
- Uses Components + Subsystems

### Validator
- Compiles project
- Fixes errors and warnings
- Verifies runtime stability

### Refactorer
- Improves architecture
- Removes technical debt
- Enforces coding standards

### Supervisor (Ollama Agent)
- Validates Unreal API usage
- Detects deprecated functions
- Suggests modern alternatives
- Blocks invalid implementations

---

## Execution Flow

Planner → Implementer → Validator → Refactorer → Supervisor → Loop

---

## Task Types

- SYSTEM_TASK
- FIX_TASK
- DOC_TASK
- INTEGRATION_TASK

---

## Output Contract

Each task MUST include:
- What was done
- Why it was done
- Files changed
- Unreal Editor steps
- Validation result

---

## Unreal Rules

- C++ first, Blueprint exposed
- Use Actor Components for behavior
- Use Subsystems for global systems
- Interfaces for communication
- No tight coupling

---

## Parallel Execution Rules

- No overlapping file edits
- Scoped ownership per agent
- Merge only after validation

---

## Brainstorming Artifact Standard

When Marcus opens any new project, feature, milestone, or major architectural decision, the response begins with a structured **Brainstorm Artifact**, never with code.

This applies whether the trigger is explicit ("brainstorm this", "scope this", "what should this do") or implicit (a project name appears without prior scope, a new phase begins, or a decision between implementation paths is requested). When in doubt, default to producing the artifact.

### Required Format

The artifact is a markdown document titled `[PROJECT_NAME] BRAINSTORM RESPONSES` with a `Captured: [DATE]` line below the title. The body is organized into three to six thematic SECTIONS, each containing three to six grouped QUESTIONS, each question containing two to eight OPTION rows.

Every option is rendered as either `[ ] Label: Trade-off rationale` (open decision) or `[x] Label: Trade-off rationale` (decision already locked from the conversation or from prior sessions). The trade-off rationale is one sentence describing what the option gives and what it costs, so Marcus can scan a question in five seconds without expanding anything.

### Required Coverage

The artifact must cover the full scope of the project end-to-end, not just the immediate next session's work. The point of locking the picture is to prevent Claude or Claude Code from implementing only a slice and missing adjacent decisions that would force rework later. If the project has audience, tech stack, AI engine, MVP lock, compliance, funding, and launch dimensions, all of them appear as sections even if some have only one or two questions.

### Decision Pre-Checking

Options Marcus has already decided in the current chat or in prior sessions are pre-checked with `[x]` before the artifact is presented. The artifact is a record of decisions plus open questions, not just open questions. If a stack choice was locked three sessions ago in a related project, render it as locked here too with a note like "(carried from Bob)" so Marcus sees the link.

### Rules That Cannot Be Violated

Trade-off options must respect the Universal Coding Standards. Never offer "quick and dirty", "just hardcode for now", "skip the tests for MVP", or any time-pressure shortcut as a valid option. Options are quality-tier alternatives only. Speed-versus-correctness is a false dichotomy in Marcus's portfolio work.

Never begin coding, scaffolding files, or generating any other deliverable until Marcus has reviewed the artifact and given explicit confirmation. The brainstorm gate is non-negotiable. If Marcus says "skip it" or "just write the code" he can override, but the default is always artifact first.

Never bury the decisions inside prose paragraphs. The format is scannable checklists. Personality and theme can live in section headers and intro lines, but the decision rows themselves are clean checkbox format.

### Lock and Reference

After Marcus reviews and confirms, save the artifact to the project's `docs/` folder as `BRAINSTORM_[YYYY-MM-DD].md` and append a one-line reference to the project's `CLAUDE.md` or `SESSION_HANDOFF.md`:

```
- Brainstorm scope: docs/BRAINSTORM_2026-04-28.md (locked 2026-04-28)
```

This makes the locked scope discoverable in future sessions without re-litigating settled decisions.

### Reference Skill

The full implementation of this behavior lives in the `brainstorm-artifact` skill in `cowork-skills`. When that skill is loaded, follow it as the source of truth. When it is not loaded (because of context budget or a fresh environment), follow this section verbatim.
