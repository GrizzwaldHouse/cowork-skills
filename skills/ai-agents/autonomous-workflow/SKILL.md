---
name: autonomous-workflow
description: >
  Spec-driven, phase-based workflow orchestration that runs projects end-to-end
  with minimal human intervention. Use this skill whenever the user says "run this
  end to end", "autonomous workflow", "execute phases", "ralph loop", "orchestrate
  this", or shares a project spec and wants it implemented without hand-holding.
  Also triggers when spec.md, phases.json, or state/workflow_state.json exist in
  the working directory. Extends the ralph loop with phase isolation, hybrid
  multi-role voting, and one-way AgenticOS event broadcasting.
---
<!-- Marcus Daley — 2026-05-01 — Autonomous workflow engine entry point -->

# Autonomous Workflow Engine

## What This Skill Does

Runs a 4-phase workflow (brainstorm → planning → execution → verification) with:
- **Adaptive resume**: detects existing state/spec/phases and picks up where you left off
- **Phase isolation**: each phase runs in a clean context — no context bleed
- **Hybrid voting**: simulated for routine decisions, 4-agent parallel vote for high-stakes gates
- **AgenticOS integration**: broadcasts lifecycle events to the state bus (fire-and-forget)

## Invocation

```
/autonomous-workflow [--from=brainstorm|planning|execution|verification]
                     [--no-vote]
                     [--agenticos-url=<url>]
                     <task description or path to spec.md>
```

## Resume Priority (checked in this order)

1. `--from=<phase>` flag → jump directly to that phase (overrides everything)
2. `state/workflow_state.json` exists → resume from last incomplete phase
3. `phases.json` exists → skip brainstorm+planning, enter execution
4. `spec.md` exists → skip brainstorm, enter planning
5. Nothing found → start at brainstorm

## Phase Routing

When this skill triggers, read the phase reference file for the current phase:

| Phase | Reference File |
|-------|---------------|
| brainstorm | `references/phase-brainstorm.md` |
| planning | `references/phase-planning.md` |
| execution | `references/phase-execution.md` |
| verification | `references/phase-verification.md` |

Read only the reference file for the current phase — not all of them. Load the next one when the current phase completes.

## State Management

Use `scripts/state_manager.py` to:
- `detect_resume_point(state_dir, from_flag)` — determine entry phase
- `mark_phase_complete(phase, state_dir)` — update state after each phase
- `mark_phase_failed(phase, reason, state_dir)` — record failures for retry

State files live in `state/` (gitignored). Pass `state_dir` as `Path("state")` relative to the working directory.

## AgenticOS Events

After each phase transition, call `scripts/agenticos_push.py`:

```python
from scripts.agenticos_push import push_event, EventType
push_event(EventType.PHASE_COMPLETE, workflow_id=state.workflow_id, extra={"phase": "brainstorm"})
```

This is fire-and-forget. Never await it or check the return value in the critical path.

## Voting Gates

Before entering the execution phase (planning → execution transition), check `references/voting-protocol.md` and run the appropriate vote level. Skip voting if `--no-vote` flag is set.

## First-Time Bootstrap

If the target project directory has no scaffold (no `workflows/`, `tasks/`, `skills/` subdirs), run:

```python
from scripts.bootstrap import scaffold_project
from pathlib import Path
scaffold_project(target_dir=Path("."), templates_dir=Path("templates"))
```

This copies templates into the project once. Subsequent runs skip this step.

## Loop Behavior (Ralph Extension)

This skill continues iterating until all phases in `workflow_state.json` have `status: complete`. After each phase:

1. Call `mark_phase_complete()` or `mark_phase_failed()`
2. Push the event to AgenticOS
3. Check if verification phase is complete — if yes, the workflow is done
4. Otherwise load the next phase reference file and continue

On failure: log the reason, update state, and surface the failure to the user with the specific phase and reason. Do not silently swallow phase failures.
