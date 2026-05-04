---
name: session-recovery
description: Recover from interrupted AI agent coding sessions by detecting the exact interruption point, reconstructing intent from pre-written step comments, completing unfinished implementations, and validating through build + supervisor review. Use this skill whenever a user mentions session recovery, interrupted work, picking up where an agent left off, completing unfinished code, finding where a session dropped, resuming development, or anything related to detecting and finishing incomplete AI-assisted coding sessions. Also trigger when users mention Claude Code agent sessions that were cut off, lost progress, or need continuation. This skill works across all languages and frameworks — C++, C#, Python, TypeScript, Rust, Java, Go, Unreal Engine, Unity, .NET, React, Node.js. Trigger aggressively — if a user says anything about resuming, continuing, recovering, or picking up work, use this skill.
---

# Session Recovery Skill

Recover from interrupted AI coding sessions with surgical precision. This skill
turns the chaos of a dropped session into a structured recovery pipeline that
finds the exact interruption point, understands what was being built, finishes
it, validates it compiles clean, and submits it for supervisor review.

## Core Philosophy: Comment-Driven Development (CDD)

The entire recovery system depends on a simple discipline:

> **Before writing ANY code in a function, write step-by-step comments
> describing what the function will do and WHY.**

These comments serve as a contract between the current agent and any future
agent (or human) who picks up the work. When a session drops mid-implementation,
the next agent reads those comments and knows EXACTLY what remains.

## Recovery Pipeline (7 Phases)

When triggered, execute these phases in order. Do NOT skip phases.

### Phase 1: Detect Interruption Point

**Goal:** Find exactly where the last agent session was cut off.

**Detection Strategy (execute all, cross-reference results):**

1. **Git archaeology** — Run the detection script:
   ```bash
   python /path/to/skill/scripts/detect_interruption.py --project-root .
   ```
   If the script is unavailable, manually execute:
   - `git log --oneline -20` to see recent commits
   - `git diff --stat` for uncommitted changes
   - `git diff --name-only HEAD` for modified files
   - `git stash list` for stashed work

2. **Incomplete code scan** — Search for unfinished indicators:
   - `TODO`, `FIXME`, `HACK`, `XXX`, `INCOMPLETE`, `WIP` markers
   - Empty function bodies (declared but not implemented)
   - Functions with step-comments but no code beneath them
   - Commented-out code blocks (indicates mid-refactor)
   - `NotImplementedException` or `pass` or `unimplemented!()` placeholders

3. **Timestamp analysis** — Find most recently modified files:
   - Sort all source files by modification time
   - The cluster of most-recently-modified files = the working set
   - Cross-reference with git diff to confirm

4. **Build state check** — Attempt a build to find what's broken:
   - Language-specific build commands (see references/build_commands.md)
   - Compiler errors point directly to incomplete code
   - Warnings reveal partially-implemented features

5. **Log correlation** (if logs exist) — Check application logs:
   - Last successful operation logged = the feature that was working
   - First error after that = where things broke

**Output:** Produce a `recovery_anchor` with this structure:
```
RECOVERY ANCHOR
===============
File:     [exact file path]
Function: [function/method name]
Line:     [approximate line number]
State:    [EMPTY_BODY | PARTIAL_IMPL | COMMENTS_ONLY | BUILD_ERROR]
Context:  [what was being built and why]
Modified: [timestamp of last modification]
Git:      [last commit hash and message]
```

### Phase 2: Reconstruct Intent

**Goal:** Understand what the interrupted code was SUPPOSED to do.

1. **Read step-comments** in the incomplete function(s)
   - CDD comments describe each step the function should perform
   - These are the implementation contract — respect them

2. **Analyze naming conventions** — Function names, parameter names, and
   return types all encode intent. `CalculateSpawnGrid(radius, density)` 
   tells you exactly what it should produce.

3. **Cross-reference interfaces** — If the function implements an interface
   or overrides a base class method, read THAT contract first.

4. **Check calling code** — Find everywhere this function is called.
   The call sites tell you what the callers expect.

5. **Read adjacent completed functions** — Siblings in the same class
   reveal the architectural patterns in use.

6. **Validate against architecture constraints:**
   - Event-driven only (no polling)
   - Dependency injection (no hard-coded instantiation)
   - Separation of concerns (single responsibility)
   - Config-driven (no magic numbers/strings)
   - Repository pattern for data access
   - Proper access control (no unrestricted mutable state)

**Output:** Produce an `intent_specification`:
```
INTENT SPECIFICATION
====================
Function:    [name]
Purpose:     [what it does and why it exists]
Inputs:      [parameters with expected types and constraints]
Outputs:     [return type and possible states]
Side Effects:[events broadcast, state modified, external calls]
Constraints: [architecture rules that apply]
Dependencies:[what it needs injected or available]
Steps:       [numbered list matching CDD comments]
```

### Phase 3: Plan Completion

**Goal:** Break the remaining work into independently implementable steps.

1. Identify which CDD step-comments already have implementation beneath them
2. Identify which step-comments are still empty (need implementation)
3. For each empty step, verify the design follows:
   - Dependency injection over direct instantiation
   - Event broadcasting over return-value chains where appropriate
   - Configuration values from config, not hardcoded
   - Proper error handling with typed errors
4. Write any MISSING step-comments before writing code
5. Estimate complexity per step (simple / moderate / complex)

**Output:** `implementation_plan` — ordered list of steps with status

### Phase 4: Implement with Guided Comments

**Goal:** Write the actual code, guided by step-comments.

**RULES (non-negotiable):**
- Every function starts with step-by-step comments BEFORE any code
- Comments explain WHY, not WHAT
- No public mutable state (use proper access control)
- Fail fast on invalid input (validate at boundaries)
- Use typed errors (no bare exceptions, no silent failures)
- Clean up subscriptions/listeners in destructors/cleanup methods

**Process:**
1. For each incomplete function identified in Phase 3:
   a. Verify step-comments are complete and accurate
   b. Implement logic beneath each comment block
   c. After implementing, re-read the comment and verify alignment
   d. If the code diverges from the comment, update the COMMENT (the
      comment is the spec — if the spec was wrong, fix the spec)
2. After all functions are complete, review the full file for:
   - Consistent naming conventions
   - Proper includes/imports (minimal in headers/declarations)
   - File header comment (Developer, Date, Purpose)

### Phase 5: Validation and Build

**Goal:** Zero errors, zero warnings, stable runtime.

1. **Clean build** — Perform a full rebuild (not incremental):
   - C++/UE5: Close editor, build from Visual Studio
   - C#/.NET: `dotnet build --no-incremental` or VS Clean+Build
   - Python: `python -m py_compile *.py` + mypy/pyright
   - TypeScript: `tsc --noEmit` + `npm run build`
   - Rust: `cargo build` + `cargo clippy`

2. **Resolve ALL compilation errors** — Zero tolerance

3. **Resolve ALL warnings** — Warnings are future bugs. Fix them.
   If a warning is genuinely benign, suppress at narrowest scope with
   a comment explaining WHY it's safe to ignore.

4. **Runtime verification** — Run the application and verify:
   - Launches without crashes
   - Core features function correctly
   - No error-level log entries during normal operation
   - Stable for minimum 5 minutes of operation

**Output:** `build_validation_report`:
```
BUILD VALIDATION
================
Build Tool:    [Visual Studio / dotnet / cargo / etc.]
Errors:        [count — must be 0]
Warnings:      [count — must be 0]
Runtime:       [STABLE / UNSTABLE]
Duration:      [how long it ran without issues]
Log Errors:    [any error-level log entries]
```

### Phase 6: Behavioral Verification

**Goal:** Confirm the implemented code actually does what Phase 2 said it should.

1. Walk through each intent_specification and verify:
   - Inputs are validated at boundaries
   - Outputs match expected types and states
   - Side effects occur as specified
   - Event-driven flow is maintained (no polling snuck in)
   - Dependency injection is used (no `new ConcreteClass()` in logic)
   - No global mutable state introduced

2. Test edge cases mentally or with actual tests:
   - Null/empty inputs
   - Maximum/boundary values
   - Error paths (what happens when dependencies fail?)

3. Verify subscription cleanup:
   - Every `Subscribe` has a matching `Unsubscribe`
   - Every `addEventListener` has a `removeEventListener`
   - Every `useEffect` returns a cleanup function

### Phase 7: Supervisor Review

**Goal:** Submit completed work for quality audit.

Package these reports and present to the supervisor agent:
1. `recovery_anchor_report` — where the interruption was found
2. `intent_specification` — what the code was supposed to do
3. `implementation_plan` — how the completion was structured
4. `build_validation_report` — proof it compiles clean
5. `behavior_verification_report` — proof it works correctly

The supervisor agent evaluates against:
- Architecture constraint compliance
- Comment-code alignment (do comments match implementation?)
- Access control correctness (no unrestricted mutable state)
- Event-driven purity (no polling introduced)
- Build cleanliness (0 errors, 0 warnings)

If rejected, iterate: read the supervisor's feedback, fix the issues,
re-validate (Phase 5-6), and resubmit.

## Quick Reference: CDD Comment Format

```
// PURPOSE: Why this function exists in the architecture
// STEP 1: Validate input parameters against constraints
//         (fail fast with typed error if invalid)
// STEP 2: Query the injected repository for required data
//         (handle not-found case explicitly)
// STEP 3: Transform data using the configured strategy
//         (strategy is injected, not hardcoded)
// STEP 4: Broadcast result via delegate/event
//         (consumers subscribe independently)
// STEP 5: Log completion with contextual identifiers
```

## Scripts

- `scripts/detect_interruption.py` — Automated interruption point detection
- `scripts/generate_recovery_report.py` — Formats recovery reports
- `scripts/validate_build.py` — Cross-platform build validation wrapper

## References

- `references/comment_driven_development.md` — Full CDD methodology guide
- `references/supervisor_review_protocol.md` — How supervisor agents evaluate work
- `references/build_commands.md` — Build commands per language/framework

## Failure Conditions (auto-reject if any are true)

- Incomplete function without matching implementation
- Mismatch between step-comments and actual logic
- Build errors or warnings present
- Runtime crash within 5 minutes
- Architecture constraint violation (polling, mutable public state, etc.)
- Missing file header comments
- Hardcoded configuration values
