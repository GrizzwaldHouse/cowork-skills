<!--
filename: example_va_advisory_run.md
developer: Marcus Daley
date: 2026-04-29
purpose: Worked example of a 3-agent VA advisory run under the AgenticOS Command Center. Demonstrates regulatory research, document drafting, and compliance review with one REVIEW BY AGENT invocation. Read this end-to-end to understand a complete supervised parallel session before you build your own.
-->

# Worked Example: VA Advisory - PTSD Service Connection Package

This is a fully filled-in `task_template.md` ready to drop into a Claude Code session. Three agents run in parallel under operator supervision, with two scheduled approval gates per agent and one REVIEW BY AGENT invocation at the compliance stage.

Skill reference: `skills/ai-agents/agentic-parallel/SKILL.md`. State paths and ports come from `AgenticOS/config.py`.

---

## 1. Header

```
TASK NAME:    VetAssist PTSD Service Connection Package
DOMAIN:       va-advisory
CREATED:      2026-04-29
OWNER:        Marcus Daley
SESSION GOAL: Produce a complete educational package for a veteran's PTSD
              service-connection claim: regulatory research on 38 C.F.R.
              Part 3 nexus criteria, a draft buddy letter from a fellow
              service member, and a compliance review confirming both
              documents satisfy VA OGC 2004 educational-tool standards
              and California SB 694 free-model requirements.
```

---

## 2. Agent Roster

| agent_id | role | total_stages | output_ref (terminal stage) |
|---|---|---|---|
| AGENT-01 | CFR-analyzer (regulatory research) | 4 | state/outputs/agent-01-stage-4.md |
| AGENT-02 | VA-form-extractor / buddy-letter drafter | 3 | state/outputs/agent-02-stage-3.md |
| AGENT-03 | advisory-letter-writer / compliance reviewer | 3 | state/outputs/agent-03-stage-3.md |

---

## 3. Stage Definitions

### Agent AGENT-01 - CFR-analyzer

```
agent_id:     AGENT-01
domain:       va-advisory
task:         Research 38 C.F.R. Part 3 service-connection criteria for PTSD,
              capturing nexus requirements, buddy-statement evidentiary value,
              and rating-schedule criteria under 38 C.F.R. Section 4.130.
spawned_by:   null
total_stages: 4
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Locating applicable CFR sections for PTSD service connection | 25 min | No |
| 2 | Analyzing nexus requirements and evidentiary standards | 35 min | Yes |
| 3 | Researching rating schedule criteria under Section 4.130 | 30 min | No |
| 4 | Compiling regulatory summary with citations | 20 min | Yes |

Initial prompt for AGENT-01:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-01.
Your domain is va-advisory.
Your task is: Research 38 C.F.R. Part 3 service-connection criteria for PTSD,
capturing nexus requirements, buddy-statement evidentiary value, and rating-
schedule criteria under 38 C.F.R. Section 4.130.
Your total_stages is 4.
Your spawned_by is null.

Your stages are:
  Stage 1: Locating applicable CFR sections for PTSD service connection
  Stage 2: Analyzing nexus requirements and evidentiary standards
  Stage 3: Researching rating schedule criteria under Section 4.130
  Stage 4: Compiling regulatory summary with citations

Approval gates after stages: 2, 4

Use AgenticOS.state_store and AgenticOS.config for every state write.
Begin with the Session Start Checklist, then upsert your initial state, then begin Stage 1.
```

---

### Agent AGENT-02 - VA-form-extractor / buddy-letter drafter

```
agent_id:     AGENT-02
domain:       va-advisory
task:         Draft a buddy letter for a veteran's PTSD service-connection
              claim, written from the perspective of a fellow service member
              who witnessed the in-service stressor and its immediate
              behavioral aftermath. Limit content to first-person observable
              fact: no diagnoses, no legal conclusions, no outcome guarantees.
spawned_by:   null
total_stages: 3
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Drafting opening and witness credential section | 15 min | No |
| 2 | Drafting stressor description and observed behavioral changes | 40 min | Yes |
| 3 | Drafting closing statement and formatting final letter | 20 min | Yes |

Initial prompt for AGENT-02:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-02.
Your domain is va-advisory.
Your task is: Draft a buddy letter for a veteran's PTSD service-connection claim,
written first-person from a fellow service member who witnessed the stressor
event and its immediate behavioral aftermath. No diagnoses, no legal conclusions,
no outcome guarantees.
Your total_stages is 3.
Your spawned_by is null.

Your stages are:
  Stage 1: Drafting opening and witness credential section
  Stage 2: Drafting stressor description and observed behavioral changes
  Stage 3: Drafting closing statement and formatting final letter

Approval gates after stages: 2, 3

You may read AGENT-01's stage 4 output once it exists, but you do not need
to wait for it. Begin Stage 1 independently.

Use AgenticOS.state_store and AgenticOS.config for every state write.
Begin with the Session Start Checklist, then upsert your initial state, then begin Stage 1.
```

---

### Agent AGENT-03 - advisory-letter-writer / compliance reviewer

```
agent_id:     AGENT-03
domain:       va-advisory
task:         Review the regulatory research and the buddy letter draft for
              compliance with VA OGC 2004 Opinion (educational-tool standard),
              California SB 694 free-model requirements, and the VetAssist
              platform legal position. Flag any language that constitutes
              legal advice, outcome guarantees, or unauthorized practice of law.
spawned_by:   null
total_stages: 3
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Reviewing regulatory research for compliance issues | 25 min | No |
| 2 | Reviewing buddy letter draft for compliance issues | 25 min | No |
| 3 | Writing compliance summary report with PASS / FLAG / FIX items | 30 min | Yes |

Initial prompt for AGENT-03:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-03.
Your domain is va-advisory.
Your task is: Review the regulatory research and the buddy letter draft for
compliance with VA OGC 2004 Opinion, California SB 694, and the VetAssist
platform legal position. Flag any language that constitutes legal advice,
outcome guarantees, or unauthorized practice of law.
Your total_stages is 3.
Your spawned_by is null.

Your stages are:
  Stage 1: Reviewing regulatory research for compliance issues
  Stage 2: Reviewing buddy letter draft for compliance issues
  Stage 3: Writing compliance summary report with PASS / FLAG / FIX items

Approval gates after stages: 3

Wait for both upstream output files to exist before beginning Stage 1:
  - state/outputs/agent-01-stage-4.md (AGENT-01 terminal output)
  - state/outputs/agent-02-stage-3.md (AGENT-02 terminal output)

Upsert your initial state with stage_label "Waiting for AGENT-01 and AGENT-02 outputs"
and status active immediately, then poll for both files every 30 seconds before
beginning Stage 1.
```

---

## 4. Approval Policy

| agent_id | Gate after stage | Policy | Operator evaluation criteria |
|---|---|---|---|
| AGENT-01 | 2 | Human approval | Spot-check 38 C.F.R. Section 3.304(f) citation against VA.gov. Click PROCEED if accurate, RESEARCH MORE if citation looks off. |
| AGENT-01 | 4 | Human approval | Read full regulatory summary. Verify all citations include section numbers and are not fabricated. Click REVIEW BY AGENT if anything looks suspicious. |
| AGENT-02 | 2 | Human approval | Verify stressor description is observable fact only (no medical conclusions, no speculation). Click RESEARCH MORE if it overstates. |
| AGENT-02 | 3 | Human approval | Verify letter is dated, signed-block present, no legal conclusions, no outcome guarantee language. |
| AGENT-03 | 3 | Human approval (mandatory) | Read compliance summary. Any FLAG item requires resolution before any document is used. |

---

## 5. Reviewer Policy

| agent_id | Stage requiring reviewer | Verdict format expected | Why review here |
|---|---|---|---|
| AGENT-01 | 4 (conditional, on operator click) | PASS / REVISE / REJECT + 1-3 notes on citation accuracy | Regulatory citations must be verifiable; an independent Haiku pass catches fabrications the worker model is biased to defend. |
| AGENT-03 | 3 (conditional) | PASS / REVISE / REJECT + 1-3 notes on legal-advice language | Compliance verdict on a compliance review is the highest-stakes gate in the run. |

The first scheduled invocation in this example is at AGENT-01 stage 4: the operator clicks REVIEW BY AGENT after reading the regulatory summary. The dashboard spawns a Haiku reviewer via `AgenticOS/reviewer_spawner.py` (`config.REVIEWER_MODEL`), passes `state/outputs/agent-01-stage-4.md` as `reviewer_context`, waits up to `config.REVIEWER_TIMEOUT_SECONDS`, and writes the verdict to `state/outputs/agent-01-review.md`. AGENT-01 reads the verdict, populates `reviewer_verdict` in its `AgentState`, transitions back to `waiting_approval`, and waits for the operator's final PROCEED.

Sample verdict file produced by the Haiku reviewer:

```markdown
PASS

Note 1: Section 3.304(f) is cited correctly with the verbatim "in-service stressor"
        language; cross-checked against the official CFR text.
Note 2: Section 4.130 rating-schedule criteria are summarized accurately at the
        30/50/70/100 percent levels; one minor wording softening recommended at the
        100% criterion ("total occupational and social impairment") for fidelity.
Note 3: No fabricated citations detected.
```

AGENT-01 reads this, sets `reviewer_verdict` to "PASS - Section 3.304(f) cited correctly with the verbatim 'in-service stressor' language; cross-checked against the official CFR text." (truncated to 200 chars), then transitions to `status=waiting_approval`, `awaiting=proceed` for the operator's final click.

---

## 6. Output Paths

| Artifact | Path |
|---|---|
| AGENT-01 stage outputs | state/outputs/agent-01-stage-{1..4}.md |
| AGENT-02 stage outputs | state/outputs/agent-02-stage-{1..3}.md |
| AGENT-03 stage outputs | state/outputs/agent-03-stage-{1..3}.md |
| Reviewer verdicts | state/outputs/agent-01-review.md (and agent-03-review.md if invoked) |
| Final assembled package | AgenticOS/sessions/2026-04-29-ptsd-service-connection/package.md (assembled by operator post-session) |

---

## 7. Success Criteria

- [ ] All three agents reach `status=complete`.
- [ ] AGENT-01 stage 4 output cites every CFR section with a section number and quoted regulatory text.
- [ ] AGENT-02 stage 3 letter contains no legal conclusion, no outcome guarantee, and no medical diagnosis.
- [ ] AGENT-03 stage 3 compliance summary marks all items PASS, OR every FLAG item has been resolved by an operator decision (re-run the relevant agent with REVISE notes).
- [ ] If REVIEW BY AGENT was invoked at AGENT-01 stage 4, the verdict is PASS or the redo is PASS.
- [ ] No `waiting_approval` rows remain in `config.AGENTS_JSON` at session end.

---

## 8. Rollback Plan

- AGENT-01 fails (e.g., a CFR lookup tool is offline): pause AGENT-02 if it is mid-stage 3 (it would need AGENT-01's output to inform the closing). Resume AGENT-01 with a continuation agent seeded from `state/outputs/agent-01-stage-{N-1}.md` once the tool is back.
- AGENT-02 fails after stage 2: the stressor description draft is the highest-value artifact; preserve `state/outputs/agent-02-stage-2.md` as-is and continue from stage 3.
- AGENT-03 fails: no downstream agent depends on it, but its compliance summary is mission-critical. Re-spawn it with the same `agent_id` once the upstream files are stable.
- Compliance summary returns FLAG: do NOT release the package. Re-run the flagged agent (AGENT-01 or AGENT-02) with REVISE notes from the compliance summary as the new prompt. Re-trigger AGENT-03 stage 1-3 against the redone outputs.

---

## 9. agents.json Seed

```json
[
  {
    "agent_id": "AGENT-01",
    "domain": "va-advisory",
    "task": "Research 38 C.F.R. Part 3 service-connection criteria for PTSD, capturing nexus requirements, buddy-statement evidentiary value, and rating-schedule criteria under 38 C.F.R. Section 4.130.",
    "stage_label": "Not started",
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
    "updated_at": "2026-04-29T10:00:00Z"
  },
  {
    "agent_id": "AGENT-02",
    "domain": "va-advisory",
    "task": "Draft a buddy letter for a veteran's PTSD service-connection claim, first-person from a fellow service member who witnessed the in-service stressor.",
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
    "updated_at": "2026-04-29T10:00:00Z"
  },
  {
    "agent_id": "AGENT-03",
    "domain": "va-advisory",
    "task": "Review regulatory research and buddy letter for compliance with VA OGC 2004 Opinion, California SB 694, and VetAssist platform legal position.",
    "stage_label": "Waiting for AGENT-01 and AGENT-02 outputs",
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
    "updated_at": "2026-04-29T10:00:00Z"
  }
]
```
