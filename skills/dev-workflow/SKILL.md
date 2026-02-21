---
name: dev-workflow
description: Development workflow standards covering brainstorm-first methodology, session management, build/tooling rules, testing, version control, logging, debugging, and portfolio priorities.
user-invocable: false
---

# Development Workflow

> Session management, build practices, testing standards, version control rules, debugging methodology, and portfolio priorities for all of Marcus Daley's projects.

## Description

Defines how development sessions are structured, how features are approached (brainstorm-first), build and tooling rules, testing philosophy, version control conventions, logging standards, systematic debugging methodology, and what to prioritize for portfolio impact. Includes the Problem Tracker and Lessons Learned templates.

## Prerequisites

- None -- these workflows apply universally

## Usage

Follow these workflows for every development session. The brainstorm-first methodology applies to every feature request.

### Prompt Pattern

```
I want to add [feature] to [project].
Follow the brainstorm-first methodology:
1. Research built-in solutions
2. Generate multiple approaches (BUILT-IN, ADAPT, HYBRID, CUSTOM)
3. Discuss trade-offs
4. Design architecture
5. Implement
```

## Brainstorm-First Methodology

Any feature request begins with research, not code.

1. **Research** if the language/framework already has a built-in solution
2. **Generate** multiple implementation approaches tagged as:
   - **BUILT-IN**: Use existing framework/library solution
   - **ADAPT**: Modify existing code in the project
   - **HYBRID**: Combine built-in with custom code
   - **CUSTOM**: Build from scratch
3. **Discuss trade-offs**: development time vs learning value vs portfolio impact vs maintainability
4. **Design architecture**: responsibilities, data flow, interfaces, extensibility
5. **Implement** with complete, working code and human-style comments

## Session Workflow

### Start of Session

1. Context recall: Review what was accomplished last session
2. Goal setting: Define specific feature, bug fix, or learning target
3. Scope definition: What's in-scope for this session, what's future work
4. Pull latest, install deps if needed, clean build, verify baseline works

### During Implementation

1. Research before coding (brainstorm approaches, check for built-in solutions)
2. Explain architectural decisions as they're made
3. Check against coding standards before each commit
4. Build/compile and test frequently, not just at the end
5. Work in micro-chunks suitable for 15-minute interrupted sessions

### End of Session

1. Summarize progress: What got done, what's next
2. Log any issues in Problem Tracker format
3. Update dev notes with new gotchas or lessons learned
4. Provide memory keywords for session recall
5. Commit working state to version control with descriptive message

## Build & Tooling Rules

### General Principles

- **NEVER modify shared/global build configurations for project-specific needs.** Project-specific settings belong in project-specific config files.
  - UE5: Never modify Target.cs with AdditionalCompilerArguments. Use Build.cs PrivateDefinitions.
  - Node.js: Never modify global npm/yarn config. Use .npmrc in project root.
  - Python: Never install globally. Use virtual environments.

- **Lock dependency versions for reproducible builds.**
  - Node.js: Commit package-lock.json or yarn.lock
  - Python: Use requirements.txt with pinned versions or poetry.lock
  - Rust: Commit Cargo.lock
  - C#: Use packages.lock.json

- **Suppress warnings at the narrowest possible scope.** Annotate WHY.
  - UE5: Suppress in Build.cs only, never Target.cs
  - ESLint: `// eslint-disable-next-line` for specific lines
  - Python: `# noqa: E501` for specific lines

### Build Workflow

1. Pull latest changes from version control
2. Install/update dependencies if lockfile changed
3. Run a clean build to verify baseline
4. Make changes in small increments
5. Build and test after each meaningful change
6. Run full test suite before committing
7. Commit with descriptive message explaining what and why

### Environment-Specific

**UE5:**
- Always close Unreal Editor before building in Visual Studio (Live Coding conflicts)
- Set MaxParallelActions in BuildConfiguration.xml based on system RAM
- When using FSlateBrush/FSlateColor, add SlateCore to module dependencies

**Web Dev:**
- Use HMR during development but always do a full production build before deploying
- Never commit .env files with secrets. Use .env.example as template
- Never commit node_modules. Always use lockfiles

**Python:**
- Always use virtual environments. Never pip install globally
- Use mypy or pyright for type checking

## Testing Standards

### Philosophy

Tests are documentation that verifies behavior. Write tests that describe WHAT the system does, not HOW it's implemented.

### Rules

| Rule | Details |
|------|---------|
| Test behavior, not implementation | Good: "submitting order reduces inventory." Bad: "submitOrder calls inventoryService.reduce with specific parameters" |
| One test, one thing | Naming: `should_[expected behavior]_when_[condition]` |
| Arrange-Act-Assert | Set up preconditions, execute the action, verify the result |
| Mock external deps only | Mock database, API, file system. Don't mock private methods of the class under test |

## Version Control

### Rules

- **Comprehensive .gitignore** appropriate to project type
  - UE5: Binaries, Intermediate, Saved, DerivedDataCache, .vs
  - Node: node_modules, dist, .env, .next, coverage
  - Python: __pycache__, .venv, *.pyc, .env, dist

- **Git LFS** for large binary assets (game assets, images, ML models)

- **Commit working state** at end of every session. Descriptive message explaining WHAT and WHY, not just "fixed stuff"

- **Never commit secrets, credentials, or API keys.** Use .gitignore, git-secrets, pre-commit hooks. Rotate any key that was ever committed.

## Logging & Debugging

### Structured Logging

| Level | Use For |
|-------|---------|
| ERROR | Something failed that shouldn't have. Requires attention |
| WARNING | Unexpected state that the system recovered from |
| INFO | Significant business events (user login, order placed, deployment) |
| DEBUG | Detailed diagnostic information for development |

### Logging Rules

- Include contextual identifiers (Request ID, User ID, entity name, Transaction ID)
- Log at system boundaries and state transitions, not every function call
- NEVER log sensitive data (passwords, tokens, PII, credit cards)

### Debugging Workflow

1. Gather symptoms (crash, incorrect behavior, error message, unexpected output)
2. Hypothesize 3-5 possible causes based on symptoms
3. Add targeted logging or use debugger to narrow down location
4. Inspect state at failure point (variables, call stack, data)
5. Identify root cause, not just the symptom
6. Document in Problem Tracker format

### Problem Tracker Format

```
Symptom:    [What you observed]
Root Cause: [Why it happened]
Solution:   [How you fixed it]
Prevention: [How to avoid this in the future]
```

### Lessons Learned Template

```
ID:         LS-###
Title:      [Short descriptive title]
Date:       YYYY-MM-DD
Category:   Build System | UI | Networking | Data | Performance | etc.
Severity:   Critical | High | Medium | Low
Symptom:    [What you observed]
Root Cause: [Why it happened]
Solution:   [How you fixed it]
Prevention: [How to avoid this in the future]
Reusable:   Does this lesson apply across projects? (yes/no)
```

## Web Development Specific

### Frontend

- Components should be small, focused, composable (~200 line max guideline)
- Separate data fetching from rendering (container/presenter, hooks, server components)
- Use semantic HTML for accessibility (`<button>` not `<div onClick>`, `<nav>` not `<div class='nav'>`)
- CSS follows component structure (CSS Modules, Tailwind, CSS-in-JS scoped to components)
- Handle loading, error, and empty states for every async operation

### Backend

- Validate all external input (Zod for TS, Pydantic for Python, FluentValidation for C#)
- Use middleware for cross-cutting concerns (auth, logging, rate limiting, CORS)
- Database queries through data access layer, never directly in route handlers
- Return consistent API response shapes: `{ data, error, metadata }`

### API Design

- Descriptive endpoints reflecting the resource: `GET /users/:id/orders` (not `GET /getUserOrders`)
- Appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 500)
- Version APIs from the start: `/api/v1/resource`

## Portfolio Priorities

### What to Showcase in Any Project

- Event-driven architecture over polling
- Proper encapsulation and access control
- Initialization discipline (all defaults in one place)
- Interface-driven loose coupling
- Comprehensive but targeted logging
- Dependency minimization and clean module boundaries
- Data/config driven design over hardcoded values
- Composition-based architecture for reusability
- Clean code comments explaining WHY, not WHAT
- Consistent error handling patterns
- Meaningful test coverage of behavior

### Success Metrics

- Marcus understands architecture well enough to modify independently
- Code is portfolio-quality that could be shown to hiring managers or clients
- Demonstrates mastery of platform's built-in systems before custom alternatives
- Thoroughly documented for future developers (including future Marcus)
- Systems are reusable following the 95/5 Rule

## Examples

### Example 1: Feature Request Workflow

**Input:**
```
I want to add user notifications to my web app.
```

**Output:**
1. Research: Does the framework have built-in notification support? Check for existing notification libraries.
2. Approaches:
   - BUILT-IN: Browser Notification API + service worker
   - ADAPT: Extend existing event bus with notification channel
   - HYBRID: Browser API for push, custom event system for in-app
   - CUSTOM: Full notification service with queue, persistence, multi-channel
3. Trade-offs: Browser API is simplest but limited to push. Custom gives full control but more work.
4. Architecture: NotificationService interface, channels injected via DI, event-driven delivery.
5. Implement with full code.

### Example 2: Bug Investigation

**Input:**
```
Users report the dashboard sometimes shows stale data.
```

**Output:**
1. Symptoms: Stale data on dashboard, intermittent
2. Hypotheses: (a) Cache not invalidating, (b) WebSocket disconnecting silently, (c) Race condition in data fetch, (d) Browser tab backgrounding pauses updates, (e) Event listener not cleaned up on remount
3. Investigation: Add logging at data fetch boundary, check WebSocket connection state, review useEffect cleanup
4. Root cause identified, fix applied, documented in Problem Tracker format

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| methodology | brainstorm-first | Always research before coding |
| session_chunks | 15-minute | Work in micro-chunks for interrupted sessions |
| commit_frequency | per-feature | Commit at every meaningful milestone |

## File Structure

```
dev-workflow/
  SKILL.md                     # This skill definition
  README.md                    # Quick-start guide
  resources/
    problem-tracker-template.md  # Reusable tracking template
    lessons-learned-log.md       # Running lessons learned
```

## Notes

- The brainstorm-first methodology is non-negotiable. Every feature starts with research.
- Session workflow is designed for Marcus's reality as a stay-at-home dad: micro-chunks, clear stopping points, easy context recall.
- Portfolio priorities should influence every architectural decision. This isn't just code -- it's a demonstration of professional engineering skills.
