---
name: agentforge-autopilot
description: Automate AgentForge development workflow — resume sessions, detect completed phases, run verification, and build the next phase. Use when the user says "autopilot", "resume agentforge", "continue building", "auto-build agentforge", "next phase", "spawn session", or invokes /agentforge-autopilot. Supports three modes: spawn (new terminal), resume (detect state + continue), auto-build (full pipeline).
---

# AgentForge Autopilot

Automate the AgentForge multi-agent system development cycle. Detect current phase, verify build health, and execute the next phase — all from a single command.

## Mode Detection

Parse the first argument to select mode:

| Input | Mode | Description |
|-------|------|-------------|
| `spawn` | Spawn | Open a new terminal with Claude CLI |
| `resume` | Resume | Detect state, verify, continue work |
| `auto-build` | Auto-Build | Full RESEARCH → PLAN → IMPLEMENT → TEST → COMMIT pipeline |
| *(no argument)* | Resume | Default mode |

---

## Mode 1: Spawn

Open a new Command Prompt window with Claude CLI pointed at the project.

```bash
start cmd /k "cd /d C:\Users\daley\Projects\SeniorDevBuddy\agentforge_autonomous && claude"
```

PowerShell fallback:
```powershell
Start-Process cmd -ArgumentList '/k', 'cd /d C:\Users\daley\Projects\SeniorDevBuddy\agentforge_autonomous && claude'
```

After spawning, report the command used and exit.

---

## Mode 2: Resume (Default)

### Step 1: Gather State (run in parallel)

Execute these four commands simultaneously:

```bash
# 1. Recent commits (phase detection)
git -C "C:/Users/daley/Projects/SeniorDevBuddy" log --oneline -20

# 2. Test results
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx vitest run --reporter=verbose 2>&1 | tail -30

# 3. Uncommitted changes
git -C "C:/Users/daley/Projects/SeniorDevBuddy" diff --stat

# 4. Working tree status
git -C "C:/Users/daley/Projects/SeniorDevBuddy" status --short
```

### Step 2: Detect Current Phase

Scan commit messages for `Phase N complete:` or `P{N}` patterns. Cross-reference with file existence:

| Phase | Commit Pattern | Key File Exists |
|-------|---------------|-----------------|
| P1 | `Phase 1` or `Foundation` | `src/core/interfaces/Agent.ts` |
| P2 | `Phase 2` or `Event System` | `src/core/events/agent-event-bus.ts` |
| P3 | `Phase 3` or `Observable execution` | `src/core/observability/trace.ts` |
| P4 | `Phase 4` or `Dashboard` | `src/app/dashboard/page.tsx` |
| P5 | `Phase 5` or `Real agents` | `src/agents/planner/PlannerAgent.ts` with real logic |
| P6 | `Phase 6` or `Ollama` | `src/backend/execution/OllamaBackend.ts` with real logic |
| P7 | `Phase 7` or `Orchestrator` | `src/backend/services/AgentOrchestrator.ts` with pipeline |
| P8 | `Phase 8` or `Polish` | `README.md` with usage docs |

Set `CURRENT_PHASE` to the highest completed phase. Set `NEXT_PHASE` to `CURRENT_PHASE + 1`.

### Step 3: Handle Uncommitted Work

If `git status` shows changes:
- If changes relate to `NEXT_PHASE` → continue working on them
- If changes are complete work → commit with format `Phase {N} complete: {description}`
- If changes are partial → preserve and continue

### Step 4: Run Verification

Run the verification checklist from [references/verification-checklist.md](references/verification-checklist.md). All checks must pass before advancing.

### Step 5: Load Next Phase

Read the phase spec from [references/phase-registry.md](references/phase-registry.md) for `NEXT_PHASE`.

### Step 6: Execute

Implement the phase following the spec. After completion, run verification again and commit.

---

## Mode 3: Auto-Build

Full pipeline with guardrails. One phase per invocation unless `--continuous` flag is set.

### Stage 1: RESEARCH
- Read phase spec from [references/phase-registry.md](references/phase-registry.md)
- Identify dependencies and key files
- Check existing code for patterns to follow

### Stage 2: PLAN
- Break the phase into implementation steps
- Identify files to create or modify
- Estimate scope (should be < 10 files per phase)

### Stage 3: IMPLEMENT
- Create/modify files following project conventions
- After every file change, run:
  ```bash
  cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx tsc --noEmit 2>&1 | head -20
  ```
- If TypeScript errors appear, fix immediately before proceeding

### Stage 4: TEST
- Run full test suite:
  ```bash
  cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx vitest run
  ```
- If tests fail, retry fix up to 3 times. After 3 failures, stop and report.

### Stage 5: COMMIT
- Run verification checklist
- Stage changed files with `git add` (specific files, not `-A`)
- Commit with message format:
  ```
  Phase {N} complete: {one-line description}
  ```

### Continuous Mode

With `--continuous`, repeat stages 1-5 for subsequent phases. Stop if:
- Verification fails after 3 retries
- All 8 phases are complete
- A phase has unmet dependencies

---

## Project Constants

| Constant | Value |
|----------|-------|
| Project Root | `C:\Users\daley\Projects\SeniorDevBuddy` |
| App Root | `C:\Users\daley\Projects\SeniorDevBuddy\agentforge_autonomous` |
| Source | `agentforge_autonomous/src/` |
| Tests | `**/__tests__/*.test.ts` |
| Build | `npx tsc --noEmit` |
| Test | `npx vitest run` |
| Lint | `npx next lint` |
| Dev Server | `npm run dev` |
| Path Alias | `@/*` → `./src/*` |
| Framework | Next.js 15 + React 19 + TypeScript + Tailwind CSS 4 |
| UI | Radix UI + Framer Motion |

## Commit Message Format

| Pattern | Usage |
|---------|-------|
| `Phase {N} complete: {description}` | Phase completion |
| `checkpoint: {description}` | Work-in-progress save |
| `fix: {description}` | Bug fix within a phase |
| `test: {description}` | Test additions |

## Guardrails

1. Never commit to `main` directly — use feature branches for multi-phase work
2. Run `npx tsc --noEmit` after every file change
3. Run `npx vitest run` before every commit
4. Never delete existing test files
5. Never modify `src/core/interfaces/Agent.ts` without updating all implementations
6. ES Modules only — no `require()` or `module.exports`
7. Use `@/` path alias for all imports
8. Maximum 3 retry attempts on any failure before stopping
9. Log all errors and decisions to console for traceability
