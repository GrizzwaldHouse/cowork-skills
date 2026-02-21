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
- `skills/` - Active skill packages (canva-designer, design-system, document-designer, universal-coding-standards, architecture-patterns, dev-workflow, enterprise-secure-ai-engineering)
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
