# Phase: Execution
<!-- Marcus Daley — 2026-05-01 — TDD execution contract per phase -->

## Purpose
Implement each phase from phases.json using Test-Driven Development.

## Input
`phases.json` — read the next phase with status `not_started`.

## Method: Superpower-Style TDD
For each phase in order:

1. **Write the failing test** — test the acceptance criterion directly, not the implementation
2. **Run the test — verify it fails for the right reason** (missing function, wrong output — not a syntax error)
3. **Write the minimal implementation** that makes the test pass
4. **Run the test — verify it passes**
5. **Refactor if needed** — clean up without changing behavior; re-run tests
6. **Commit** with message: `feat(<phase-id>): <what was implemented>`
7. **Update state** — call `mark_phase_complete()` in state_manager.py
8. **Push event** — call `push_event(EventType.PHASE_COMPLETE, ...)` in agenticos_push.py

## Voting Gate (before starting execution)
This phase triggers a **high-stakes voting gate** if phases.json was just generated.
Read `references/voting-protocol.md` and execute the hybrid vote before writing any code.

## Completion Criteria
All phases in phases.json have `status: complete` in workflow_state.json.
