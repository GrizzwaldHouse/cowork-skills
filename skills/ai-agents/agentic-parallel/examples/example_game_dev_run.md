<!--
filename: example_game_dev_run.md
developer: Marcus Daley
date: 2026-04-29
purpose: Worked example of a 3-agent UE5 game-dev run under the AgenticOS Command Center. Demonstrates gameplay-loop design, C++ implementation, and build / PIE validation with one REVIEW BY AGENT invocation. Mirrors Marcus's UE5 stack and AAA-practice conventions.
-->

# Worked Example: Game Dev - UE5 Broom Boost Mechanic

A fully filled-in `task_template.md` for a single feature on a Quidditch-style flight game. Three agents collaborate on a new "boost" mechanic for the broom. AGENT-01 designs the gameplay loop, AGENT-02 implements the C++ Actor Component, AGENT-03 runs the build and PIE validation. One REVIEW BY AGENT pass at the C++ stage 3.

Skill reference: `skills/ai-agents/agentic-parallel/SKILL.md`. Constants come from `AgenticOS/config.py`.

---

## 1. Header

```
TASK NAME:    Quidditch Broom Boost Mechanic - Feature Slice
DOMAIN:       game-dev
CREATED:      2026-04-29
OWNER:        Marcus Daley
SESSION GOAL: Add a held-button boost ability to the player broom: design the
              gameplay loop and feel curves, implement an Actor Component in
              C++ with Blueprint exposure, and validate via a clean build
              followed by a 3-minute PIE smoke test. Produce a feature spec,
              the component source, and a validation report.
```

---

## 2. Agent Roster

| agent_id | role | total_stages | output_ref (terminal stage) |
|---|---|---|---|
| AGENT-01 | gameplay-loop-designer | 3 | state/outputs/agent-01-stage-3.md |
| AGENT-02 | c++-implementer | 4 | state/outputs/agent-02-stage-4.md |
| AGENT-03 | ue5-build-validator | 3 | state/outputs/agent-03-stage-3.md |

---

## 3. Stage Definitions

### Agent AGENT-01 - gameplay-loop-designer

```
agent_id:     AGENT-01
domain:       game-dev
task:         Design the broom boost mechanic: held-button activation, stamina
              cost curve, recovery curve, camera FOV punch, audio cue beats,
              and interaction with existing flight tilt and drift systems.
              Produce a feature spec the C++ implementer can build from.
spawned_by:   null
total_stages: 3
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Drafting boost activation rules and stamina budget | 25 min | No |
| 2 | Designing recovery and camera FOV curves with reference values | 30 min | Yes |
| 3 | Writing complete feature spec with Blueprint-side parameters | 25 min | Yes |

Initial prompt for AGENT-01:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-01.
Your domain is game-dev.
Your task is: Design the broom boost mechanic (held-button activation, stamina
cost / recovery curves, camera FOV punch, audio cue beats, interaction with
existing flight tilt / drift). Produce a feature spec the C++ implementer
can build from.
Your total_stages is 3.
Your spawned_by is null.

Your stages are:
  Stage 1: Drafting boost activation rules and stamina budget
  Stage 2: Designing recovery and camera FOV curves with reference values
  Stage 3: Writing complete feature spec with Blueprint-side parameters

Approval gates after stages: 2, 3

Reference Marcus's universal coding standards: configuration-driven design,
no magic numbers. Every numeric value in the spec must be expressed as a named
parameter the C++ implementer can expose to Blueprint via UPROPERTY.

Use AgenticOS.state_store and AgenticOS.config for every state write.
Begin with the Session Start Checklist, then upsert your initial state, then begin Stage 1.
```

---

### Agent AGENT-02 - c++-implementer

```
agent_id:     AGENT-02
domain:       game-dev
task:         Implement UBroomBoostComponent as a UActorComponent in C++,
              following Marcus's UE5 conventions: header / source split,
              UPROPERTY EditAnywhere for designer parameters, UFUNCTION
              BlueprintCallable, event-driven (no Tick-based polling).
              Hook it onto the existing PlayerBroomActor.
spawned_by:   null
total_stages: 4
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Drafting header file with UPROPERTY parameter surface | 25 min | No |
| 2 | Implementing activation, stamina drain, and recovery logic | 50 min | Yes |
| 3 | Implementing camera FOV punch via OnBoostStarted delegate | 30 min | Yes |
| 4 | Wiring component into PlayerBroomActor and adding default values | 20 min | Yes |

Initial prompt for AGENT-02:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-02.
Your domain is game-dev.
Your task is: Implement UBroomBoostComponent as a UActorComponent in C++ following
Marcus's UE5 conventions (header/source split, UPROPERTY EditAnywhere for designer
parameters, UFUNCTION BlueprintCallable, event-driven via delegates - no Tick polling).
Hook it onto PlayerBroomActor.
Your total_stages is 4.
Your spawned_by is null.

Your stages are:
  Stage 1: Drafting header file with UPROPERTY parameter surface
  Stage 2: Implementing activation, stamina drain, and recovery logic
  Stage 3: Implementing camera FOV punch via OnBoostStarted delegate
  Stage 4: Wiring component into PlayerBroomActor and adding default values

Approval gates after stages: 2, 3, 4

Wait for AGENT-01 stage 3 output (state/outputs/agent-01-stage-3.md) to exist
before starting Stage 1; the parameter surface must mirror the design spec.
Upsert initial state with stage_label "Waiting for AGENT-01 spec" immediately.

Critical rules from CLAUDE.md:
  - No polling. Use UFUNCTION delegates / multicast events.
  - All numeric defaults set at construction (no magic numbers in source).
  - File header on every new .h/.cpp file.

Use AgenticOS.state_store and AgenticOS.config for every state write.
```

---

### Agent AGENT-03 - ue5-build-validator

```
agent_id:     AGENT-03
domain:       game-dev
task:         Run a full clean rebuild of the UE5 project, then launch PIE
              for a 3-minute smoke test exercising boost activation, stamina
              depletion, recovery, and camera FOV punch. Produce a build /
              PIE validation report with pass/fail per checklist item.
spawned_by:   null
total_stages: 3
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Running clean rebuild via Build.bat | 15 min | No |
| 2 | Launching PIE and exercising the boost smoke test checklist | 20 min | No |
| 3 | Writing validation report with pass / fail per checklist item | 15 min | Yes |

Initial prompt for AGENT-03:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-03.
Your domain is game-dev.
Your task is: Run a full clean rebuild of the UE5 project, then launch PIE
for a 3-minute boost smoke test (activation, stamina depletion, recovery,
camera FOV punch). Produce a validation report with pass/fail per checklist item.
Your total_stages is 3.
Your spawned_by is null.

Your stages are:
  Stage 1: Running clean rebuild via Build.bat
  Stage 2: Launching PIE and exercising the boost smoke test checklist
  Stage 3: Writing validation report with pass / fail per checklist item

Approval gates after stages: 3

Wait for AGENT-02 stage 4 output (state/outputs/agent-02-stage-4.md) to exist
before starting Stage 1; you cannot validate code that has not been written.
Upsert initial state with stage_label "Waiting for AGENT-02 implementation"
immediately, then poll for the file every 30 seconds.

Use AgenticOS.state_store and AgenticOS.config for every state write.
```

---

## 4. Approval Policy

| agent_id | Gate after stage | Policy | Operator evaluation criteria |
|---|---|---|---|
| AGENT-01 | 2 | Human approval | Verify recovery curve is monotonic and the FOV punch peak fits the camera tween budget. RESEARCH MORE if curves feel arbitrary. |
| AGENT-01 | 3 | Human approval | Verify every numeric value in the spec has a named parameter (no magic numbers). PROCEED if clean. |
| AGENT-02 | 2 | Human approval | Verify activation logic is delegate-driven, not Tick-driven. Verify access modifiers are most-restrictive. |
| AGENT-02 | 3 | Human approval | Spot-check the FOV-punch delegate hookup; verify no direct camera mutation in component. REVIEW BY AGENT if unsure about the broadcast pattern. |
| AGENT-02 | 4 | Human approval | Verify default values are set at construction in the .cpp constructor, not in BeginPlay. |
| AGENT-03 | 3 | Human approval (mandatory) | All checklist items must read PASS. Any FAIL aborts the merge to main. |

---

## 5. Reviewer Policy

| agent_id | Stage requiring reviewer | Verdict format expected | Why review here |
|---|---|---|---|
| AGENT-02 | 3 (conditional, on operator click) | PASS / REVISE / REJECT + 1-3 notes on event-driven correctness | The FOV-punch path is the most likely place for a subtle Tick / polling regression; an independent Haiku pass catches "we will fix it later" patterns the worker model rationalizes. |

Scheduled invocation: at AGENT-02 stage 3 the operator clicks REVIEW BY AGENT. The dashboard spawns the Haiku reviewer (`config.REVIEWER_MODEL`), passes `state/outputs/agent-02-stage-3.md` as `reviewer_context`, and writes the verdict to `state/outputs/agent-02-review.md`.

Sample verdict produced by the Haiku reviewer:

```markdown
REVISE

Note 1: OnBoostStarted is declared as a DECLARE_DYNAMIC_MULTICAST_DELEGATE
        and broadcast correctly, but BroomBoostComponent.cpp lines 87-92 read
        GetWorld()->GetTimeSeconds() inside a Tick override that is not gated
        by bIsBoosting; this re-introduces polling. Convert to a one-shot
        FTimerHandle scheduled on activation.
Note 2: The camera FOV punch path is event-driven and clean.
Note 3: No magic numbers detected in the component source.
```

AGENT-02 reads the verdict, sets `reviewer_verdict = "REVISE - OnBoostStarted is declared as a DECLARE_DYNAMIC_MULTICAST_DELEGATE and broadcast correctly, but..."` (truncated to 200 chars), transitions to `status=waiting_approval`, `awaiting=proceed`, and waits. Operator clicks PROCEED. AGENT-02 redoes stage 3 incorporating the FTimerHandle change, overwrites `state/outputs/agent-02-stage-3.md`, re-enters the gate. Operator clicks PROCEED on the redo. AGENT-02 advances to stage 4.

---

## 6. Output Paths

| Artifact | Path |
|---|---|
| AGENT-01 stage outputs | state/outputs/agent-01-stage-{1..3}.md |
| AGENT-02 stage outputs | state/outputs/agent-02-stage-{1..4}.md |
| AGENT-03 stage outputs | state/outputs/agent-03-stage-{1..3}.md |
| Reviewer verdicts | state/outputs/agent-02-review.md |
| Component source (game-side artifacts produced by AGENT-02) | UE5 project under `Source/Quidditch/Components/BroomBoostComponent.{h,cpp}` |
| Validation report | state/outputs/agent-03-stage-3.md |

---

## 7. Success Criteria

- [ ] All three agents reach `status=complete`.
- [ ] AGENT-01 spec exposes every numeric value as a named parameter.
- [ ] AGENT-02 component has zero polling paths (no per-tick state checks).
- [ ] AGENT-02 component has file headers on `.h` and `.cpp` per Marcus's universal standards.
- [ ] AGENT-03 build produces zero compile errors and zero warnings.
- [ ] AGENT-03 PIE smoke test marks every checklist item PASS.
- [ ] If AGENT-02 stage 3 review returns REVISE, the redo verdict (or operator inspection) confirms the issue was resolved.

---

## 8. Rollback Plan

- AGENT-02 cannot compile after stage 2: revert `Source/Quidditch/Components/BroomBoostComponent.{h,cpp}` to the prior commit, re-spawn AGENT-02 with a continuation seeded from `state/outputs/agent-02-stage-1.md`.
- AGENT-03 build fails: capture the build log to `state/outputs/agent-03-stage-1.md`, mark the agent `status=error` with `error_msg="BuildError: Compile failed at stage 1, see output for log."`, and pass the log back to AGENT-02 for a fix pass.
- PIE crashes: collect the crash dump path in the validation report, mark AGENT-03 `status=error`, and route to a debugging session (not in scope for this run).
- Reviewer returns REJECT: do not redo in place. Spawn a fresh AGENT-02-bis with a new initial prompt that incorporates the reject reasoning, pointing to the prior output as a negative example. Continue the run with the new agent in the same row (same `agent_id`).

---

## 9. agents.json Seed

```json
[
  {
    "agent_id": "AGENT-01",
    "domain": "game-dev",
    "task": "Design the broom boost mechanic: held-button activation, stamina cost / recovery, camera FOV punch, audio cue beats, interaction with existing flight tilt / drift.",
    "stage_label": "Not started",
    "stage": 1,
    "total_stages": 3,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "2026-04-29T09:00:00Z"
  },
  {
    "agent_id": "AGENT-02",
    "domain": "game-dev",
    "task": "Implement UBroomBoostComponent as a UActorComponent in C++, header/source split, UPROPERTY for designer parameters, event-driven (no Tick polling). Hook to PlayerBroomActor.",
    "stage_label": "Waiting for AGENT-01 spec",
    "stage": 1,
    "total_stages": 4,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "2026-04-29T09:00:00Z"
  },
  {
    "agent_id": "AGENT-03",
    "domain": "game-dev",
    "task": "Run clean rebuild via Build.bat, launch PIE for a 3-minute boost smoke test, produce a validation report.",
    "stage_label": "Waiting for AGENT-02 implementation",
    "stage": 1,
    "total_stages": 3,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "2026-04-29T09:00:00Z"
  }
]
```
