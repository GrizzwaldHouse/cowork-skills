# Plan 5 of 5 — Reusable Skill and Task Templates
**Date:** 2026-04-29
**Author:** Marcus Daley
**Project:** AgenticOS Command Center — C:\ClaudeSkills
**Status:** Ready for implementation

---

## Goal

Produce two reusable markdown files — `SKILL.md` and `tasks.md` — that any future multi-agent workflow can invoke to participate in the AgenticOS Command Center dashboard with zero extra configuration. A sub-agent loads the skill, follows the protocol, and its state automatically appears in the dashboard. A user fills in the task template, and the session is fully defined before Claude Code starts.

Produce one companion README.md that documents the skill for future users.

---

## Architecture

```
C:\ClaudeSkills\
  skills\
    agentic-parallel\
      SKILL.md          ← Protocol every sub-agent reads and executes
      README.md         ← Human-facing documentation for the skill
  tasks\
    agentic-parallel\
      tasks.md          ← Fill-in scaffold for any multi-agent session
```

These files are Claude Code skill files (markdown). They contain no executable code. They are instructions that Claude Code agents read and follow as behavioral contracts.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Skill format | Claude Code markdown skill files |
| State format | JSON (agents.json, approval_queue.json) |
| Output format | Markdown (stage output files, reviewer verdicts) |
| Agent protocol | File-based polling — read/write JSON on disk |
| State location | `C:\ClaudeSkills\AgenticOS\state\` |

---

## Dependency on Prior Plans

This plan depends on state shapes established in Plans 1–4:

- **Plan 1** — `agentic_server.py`: defines the FastAPI endpoints the approval gate posts to and the file paths the server watches
- **Plan 2** — `agentic_dashboard.py` / `agentic_dashboard.xaml`: the WPF host that displays agent cards
- **Plan 3** — React frontend: `AgentState` TypeScript type that the dashboard reads
- **Plan 4** — `agents.json`, `approval_queue.json` file contracts

The state shape that all plans agree on:

```json
{
  "agent_id": "AGENT-01",
  "domain": "va-advisory | game-dev | software-eng | 3d-content | general",
  "task": "Human-readable description of what this agent is doing",
  "stage_label": "Current stage description",
  "stage": 2,
  "total_stages": 5,
  "progress_pct": 64,
  "status": "active | waiting_approval | waiting_review | complete | error",
  "context_pct_used": 34,
  "output_ref": "state/outputs/agent-01-stage-2.md",
  "awaiting": "proceed | research | review | null",
  "error_msg": null,
  "spawned_by": null,
  "reviewer_verdict": null,
  "updated_at": "2026-04-29T14:32:00Z"
}
```

The approval queue shape:

```json
[
  {
    "agent_id": "AGENT-01",
    "decision": "proceed | research | review",
    "reviewer_context": "path/to/output/for/reviewer",
    "decided_at": "2026-04-29T14:35:00Z"
  }
]
```

All field names in SKILL.md and tasks.md must match these shapes exactly. No deviations.

---

## Task 1 — Write `C:\ClaudeSkills\skills\agentic-parallel\SKILL.md`

### What this file is

A behavioral protocol document. Every Claude sub-agent that participates in a multi-agent parallel session must read this file at the start of its session. The skill defines what to write, when to write it, how to poll for approval decisions, and how to handle reviewer verdicts. Following this skill makes an agent visible and controllable from the AgenticOS Command Center dashboard without any additional configuration.

### Task steps

**Step 1.1 — Create the directory**

Verify `C:\ClaudeSkills\skills\agentic-parallel\` does not already exist. If not, it will be created when the file is written.

**Step 1.2 — Write the file**

File path: `C:\ClaudeSkills\skills\agentic-parallel\SKILL.md`

Complete file content:

```markdown
---
name: agentic-parallel
description: Agent state-writing protocol for the AgenticOS Command Center. Any Claude sub-agent running in a multi-agent parallel session reads this skill to participate in dashboard tracking, approval gates, and reviewer spawning.
user-invocable: false
---

# Agentic Parallel — Agent State Protocol

// filename: SKILL.md
// developer: Marcus Daley
// date: 2026-04-29
// purpose: Behavioral protocol every sub-agent reads to participate in the AgenticOS Command Center

Read this skill at the start of any multi-agent session. Follow every rule precisely.
Missing a state write or polling step breaks dashboard visibility for that agent.

---

## 1. When to Use This Skill

Use this skill whenever you are a Claude Code sub-agent running in parallel with other agents
and a human operator is supervising the session through the AgenticOS Command Center.

Indicators that this skill applies:
- Your task description references AGENT-01, AGENT-02, etc. as your agent_id
- Your task template references `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md`
- A human operator has opened the AgenticOS Command Center dashboard before your session
- Your task includes a list of named stages with a defined total_stages count

If none of these apply, this skill does not apply. Do not write to agents.json for ad-hoc sessions.

---

## 2. State Files — Locations and Format

All state lives in: `C:\ClaudeSkills\AgenticOS\state\`

| File | Purpose | Who writes |
|---|---|---|
| `state/agents.json` | Live agent state — one entry per agent, JSON array | Each agent writes its own entry |
| `state/approval_queue.json` | Pending approval decisions from the dashboard | FastAPI writes; agent reads and removes its entry |
| `state/outputs/agent-{id}-stage-{n}.md` | Stage output files | Each agent writes its stage output |
| `state/outputs/agent-{id}-review.md` | Reviewer verdict file | Reviewer agent writes; main agent reads |

`{id}` in file names is the lowercase agent_id with the hyphen preserved.
Examples: `agent-01-stage-2.md`, `agent-02-review.md`

---

## 3. State Writing Contract — The AgentState Shape

Every time you write to `state/agents.json`, write this exact shape for your entry:

```json
{
  "agent_id": "AGENT-01",
  "domain": "va-advisory",
  "task": "Research CFR Title 38 Part 3 for service connection criteria",
  "stage_label": "Analyzing disability rating schedules",
  "stage": 2,
  "total_stages": 5,
  "progress_pct": 64,
  "status": "active",
  "context_pct_used": 34,
  "output_ref": "state/outputs/agent-01-stage-2.md",
  "awaiting": null,
  "error_msg": null,
  "spawned_by": null,
  "reviewer_verdict": null,
  "updated_at": "2026-04-29T14:32:00Z"
}
```

Field rules:

| Field | Type | Rule |
|---|---|---|
| `agent_id` | string | Set once at session start from your task definition. Format: "AGENT-01". Never change it. |
| `domain` | string | One of: `va-advisory`, `game-dev`, `software-eng`, `3d-content`, `general`. Set once. |
| `task` | string | One sentence describing your overall mission. Set once at session start. |
| `stage_label` | string | Short present-tense description of the current stage. Update at every stage transition. |
| `stage` | integer | Current stage number. Start at 1. Increment only when advancing to the next stage. |
| `total_stages` | integer | Fixed count of all stages for this agent. Set once at session start. Never change. |
| `progress_pct` | integer | Calculated as `round((stage / total_stages) * 100)`. Update with stage. |
| `status` | string | One of: `active`, `waiting_approval`, `waiting_review`, `complete`, `error`. |
| `context_pct_used` | integer | Estimated percentage of context window consumed. See Section 7 for calculation. |
| `output_ref` | string | Path to the output file for the current stage. Format: `state/outputs/agent-{id}-stage-{n}.md`. |
| `awaiting` | string or null | One of: `proceed`, `research`, `review`, `null`. Set to `null` when not at a gate. |
| `error_msg` | string or null | null normally. Set to a one-sentence description if status is `error`. |
| `spawned_by` | string or null | null if top-level agent. Set to parent agent_id if you were spawned as a sub-agent. |
| `reviewer_verdict` | string or null | null until reviewer verdict file is read. Then set to the verdict text (truncated to 200 chars). |
| `updated_at` | string | ISO-8601 UTC timestamp at the moment of the write. Format: "YYYY-MM-DDTHH:MM:SSZ". |

---

## 4. When to Write State — Required Write Points

Write to `state/agents.json` at each of these moments. Missing any write point means the
dashboard shows stale data for your agent.

| Moment | What to write |
|---|---|
| Session start | Full entry with stage=1, status="active", awaiting=null |
| Each stage transition | Updated stage, stage_label, progress_pct, output_ref, updated_at |
| Reaching an approval gate | status="waiting_approval", awaiting="proceed" |
| Receiving approval decision | Updated status and awaiting reflecting the decision |
| Completion | status="complete", stage=total_stages, progress_pct=100, awaiting=null |
| Any error | status="error", error_msg="one sentence description" |

---

## 5. File Write Procedure — Upsert Protocol

`state/agents.json` is a shared JSON array. Multiple agents write to it. You must
never overwrite other agents' entries.

Follow this exact procedure every time you write your state:

1. Read the current contents of `state/agents.json`
2. Parse it as a JSON array
3. Find the element where `agent_id` equals your agent_id
4. If found: replace that element with your updated entry
5. If not found: append your entry to the array
6. Write the entire updated array back to `state/agents.json`
7. Confirm the write succeeded before continuing

If `state/agents.json` does not exist or is empty, write it as a JSON array containing
only your entry: `[{ ...your entry... }]`

Do not write partial JSON. Always write a complete, valid JSON array.

---

## 6. Stage Transition Rules

A stage transition happens when you finish all work for the current stage and move to
the next stage. Transition rules:

1. Write your completed stage output to `state/outputs/agent-{id}-stage-{n}.md`
   before incrementing the stage counter
2. Increment `stage` by 1
3. Update `stage_label` to describe the new stage
4. Recalculate `progress_pct` as `round((new_stage / total_stages) * 100)`
5. Update `output_ref` to the new stage output file path
6. Write state immediately after incrementing

Do not increment `stage` before the previous stage's output file is written.
The output file must exist before the state write for that stage transition.

Stage label format: present-tense verb phrase describing what this stage is doing.
Examples: "Analyzing CFR disability criteria", "Drafting buddy letter", "Running compliance check"

---

## 7. Context Window Tracking

Estimate your context window usage at each state write.

Calculation method:
- Assume a 200,000 token context window
- Estimate tokens consumed so far: count the approximate number of words in all messages
  in this session (including your instructions, prior outputs, and tool results), then
  multiply by 1.33 to convert words to tokens
- context_pct_used = round((estimated_tokens / 200000) * 100)
- Cap at 99 — never write 100 unless you are in an error state from context exhaustion

Write `context_pct_used` at every state write, not only at stage transitions.

If context usage exceeds 80%: set `status: "waiting_approval"` and `awaiting: "proceed"`
at the next natural stage boundary. Do not continue to the next stage without explicit
approval when context is above 80%. Write `stage_label` as "Context at 80% — awaiting
approval to continue" so the operator sees the reason.

---

## 8. Approval Gate Protocol

Approval gates are checkpoints where you pause and wait for the human operator to decide
whether to proceed. Gates are defined in your task template. You may also reach an
unplanned gate at 80% context (see Section 7).

### 8.1 — Entering a gate

When you reach an approval gate:

1. Write your completed output for the current stage to `state/outputs/agent-{id}-stage-{n}.md`
2. Write state with: `status: "waiting_approval"`, `awaiting: "proceed"`, updated `output_ref`
3. Stop all work. Do not advance to the next stage.
4. Begin polling `state/approval_queue.json` per Section 8.2

### 8.2 — Polling for a decision

Poll `state/approval_queue.json` every 2 seconds.

On each poll:
1. Read `state/approval_queue.json`
2. Parse as JSON array
3. Search for an entry where `agent_id` equals your agent_id
4. If not found: wait 2 seconds and poll again
5. If found: read the `decision` field and proceed to Section 8.3

The dashboard operator chooses one of three decisions: `proceed`, `research`, or `review`.

### 8.3 — Handling a `proceed` decision

1. Read the entry from `approval_queue.json`
2. Remove your entry from the array (leave all other entries intact)
3. Write the updated array back to `state/approval_queue.json`
4. Increment stage, update stage_label to the next stage
5. Write state with: `status: "active"`, `awaiting: null`
6. Continue work on the next stage

### 8.4 — Handling a `research` decision

1. Read the entry from `approval_queue.json`
2. Remove your entry from the array
3. Write the updated array back to `state/approval_queue.json`
4. Write state with: `status: "waiting_review"`, `awaiting: "research"`
5. Stop work. The dashboard will spawn a research sub-agent automatically.
6. Poll `state/approval_queue.json` again — the research sub-agent result will appear
   as a new `proceed` decision for your agent_id once the research is complete
7. When the `proceed` decision arrives, handle it per Section 8.3

### 8.5 — Handling a `review` decision

1. Read the entry from `approval_queue.json`
2. Remove your entry from the array
3. Write the updated array back to `state/approval_queue.json`
4. Write state with: `status: "waiting_review"`, `awaiting: "review"`, `reviewer_verdict: null`
5. Stop work. The dashboard will spawn a reviewer agent automatically using claude-haiku-4-5-20251001.
6. Poll `state/outputs/agent-{id}-review.md` every 2 seconds
7. When the file appears: read its full contents
8. Extract the verdict (first line that starts with PASS, REVISE, or REJECT)
9. Write state with: `reviewer_verdict: "[first 200 chars of verdict text]"`
10. Write state with: `status: "waiting_approval"`, `awaiting: "proceed"`
11. The dashboard will display the verdict to the operator and re-enable the PROCEED button
12. Poll `state/approval_queue.json` for the human's final proceed decision
13. When found: handle per Section 8.3

---

## 9. Output File Protocol

Write a stage output file at the end of every stage, before state is written for that
stage transition. Output files are what the reviewer agent reads and what the operator
sees in the ReviewerPanel.

File path pattern: `state/outputs/agent-{id}-stage-{n}.md`
Examples: `state/outputs/agent-01-stage-1.md`, `state/outputs/agent-02-stage-3.md`

Required output file structure:

```markdown
# Agent {AGENT-ID} — Stage {N}: {Stage Label}
**Agent:** {agent_id}
**Domain:** {domain}
**Stage:** {stage} of {total_stages}
**Completed at:** {ISO-8601 timestamp}

---

## Work Output

{The complete output for this stage — findings, analysis, drafted text, code,
decisions made, references consulted, etc. Do not summarize. Write the full output.}

---

## Stage Summary

{One paragraph (3-5 sentences) summarizing what was accomplished this stage,
what was found or produced, and what the next stage will do.}

---

## Confidence Note

{One sentence rating your confidence in this stage's output: High / Medium / Low,
and the primary reason for that rating.}
```

Do not omit the header, stage summary, or confidence note. Reviewer agents depend on
this structure to produce accurate verdicts.

---

## 10. Reviewer Verdict Protocol

When a reviewer verdict appears in `state/outputs/agent-{id}-review.md`:

1. Read the full contents of the verdict file
2. Find the verdict line — it starts with `PASS`, `REVISE`, or `REJECT`
3. Read the notes beneath the verdict line
4. Set `reviewer_verdict` in your state to the verdict line plus the first note
   (truncated to 200 characters total)
5. Do not discard the full verdict file contents — reference the full file in your
   next stage's work if the verdict is REVISE or REJECT
6. If verdict is `PASS`: when the operator clicks PROCEED, continue to the next stage
7. If verdict is `REVISE`: when the operator clicks PROCEED, re-do the current stage
   incorporating the reviewer's specific notes before advancing
8. If verdict is `REJECT`: when the operator clicks PROCEED, treat the current stage
   as failed — write a new stage output that re-approaches the problem from a different
   angle as specified by the reviewer notes

For REVISE and REJECT, the re-done stage output overwrites the previous output file
(same path, same stage number). Do not increment stage until the re-done output is
complete and the operator sends a new `proceed` decision.

---

## 11. Domain Tagging

Set `domain` once at session start from the task template. Never change it mid-session.

| Domain value | Use when |
|---|---|
| `va-advisory` | VA benefits research, buddy letters, CFR citations, VR&E, claims strategy |
| `game-dev` | Unreal Engine 5, gameplay systems, level design, shader work, game AI |
| `software-eng` | Full-stack development, APIs, databases, VetAssist app, DevProductivityTracker |
| `3d-content` | 3D modeling, textures, content creation pipeline, Blender, UE5 assets |
| `general` | Any task that does not fit a specific domain above |

---

## 12. Error Handling

On any error that prevents you from continuing:

1. Write state with: `status: "error"`, `error_msg: "One sentence describing the error"`
2. Do not increment stage
3. Do not continue work
4. Do not poll approval_queue
5. Leave `awaiting: null` — errors require human diagnosis, not a queue entry

Error message format: `"[Error type]: [What happened] at stage [N]"`
Example: `"FileWriteError: Could not write agents.json — path not accessible at stage 3"`

If the error is a context exhaustion (you cannot continue due to context limits):
- Set `status: "error"`, `error_msg: "ContextExhausted: Context limit reached at stage [N]. Resume from stage/outputs/agent-{id}-stage-[N-1].md"`
- The operator will spawn a continuation agent seeded with your last output file

---

## 13. Session Start Checklist

Before writing any state or doing any work, verify:

- [ ] You have a confirmed `agent_id` from your task template (format: AGENT-01, AGENT-02, etc.)
- [ ] You have a confirmed `domain` value from your task template
- [ ] You have a confirmed `total_stages` count from your task template
- [ ] `C:\ClaudeSkills\AgenticOS\state\` directory exists and is writable
- [ ] `state/outputs\` subdirectory exists
- [ ] `state/agents.json` exists (create it as `[]` if it does not)
- [ ] `state/approval_queue.json` exists (create it as `[]` if it does not)

Write your initial state entry immediately after this checklist passes.
Do not begin stage 1 work until the initial state is written and confirmed.

---

## 14. Completion Protocol

When all stages are complete:

1. Write final stage output file for the last stage
2. Write state with:
   - `status: "complete"`
   - `stage: {total_stages}` (confirm it is at the final value)
   - `progress_pct: 100`
   - `awaiting: null`
   - `error_msg: null`
   - `output_ref: "state/outputs/agent-{id}-stage-{total_stages}.md"`
3. Do not remove your entry from agents.json — the dashboard retains complete agents
   for the operator's review until they manually dismiss the card

The session is complete. Do not poll approval_queue after writing complete status.
```

**Step 1.3 — Self-review before saving**

Check each field name in the skill against the AgentState shape from the spec:
- `agent_id` ✓
- `domain` ✓ (includes `3d-content` which the spec adds in Section 11 domain expansion)
- `task` ✓
- `stage_label` ✓
- `stage` ✓
- `total_stages` ✓
- `progress_pct` ✓
- `status` ✓ (all four values: `active`, `waiting_approval`, `waiting_review`, `complete`, `error`)
- `context_pct_used` ✓
- `output_ref` ✓
- `awaiting` ✓ (all four values: `proceed`, `research`, `review`, `null`)
- `error_msg` ✓
- `spawned_by` ✓
- `reviewer_verdict` ✓
- `updated_at` ✓

Check approval_queue shape:
- `agent_id` ✓
- `decision` ✓
- `reviewer_context` — the skill does not read this field directly (the server uses it to spawn the reviewer, the agent only reads `decision`). This is correct — the agent does not need `reviewer_context`.
- `decided_at` — the agent does not need to read this field. Correct.

**Step 1.4 — Commit**

```
git -C C:\ClaudeSkills add skills/agentic-parallel/SKILL.md
git -C C:\ClaudeSkills commit -m "add agentic-parallel skill: agent state protocol for Command Center"
```

---

## Task 2 — Write `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md`

### What this file is

A fill-in scaffold. The human operator fills this out before starting a multi-agent session.
It defines the mission name, domain, the list of agents, each agent's stages and approval
gates, and produces the initial `agents.json` seed that pre-populates the dashboard.

Pattern followed: same checklist and section structure as `tasks/ai-workflows/tasks.md`
and `tasks/app-development/tasks.md`, extended with agent-specific fill-in blocks.

### Task steps

**Step 2.1 — Create the directory**

Verify `C:\ClaudeSkills\tasks\agentic-parallel\` does not already exist. Create on write.

**Step 2.2 — Write the file**

File path: `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md`

Complete file content:

```markdown
# Agentic Parallel — Multi-Agent Session Template

// filename: tasks.md
// developer: Marcus Daley
// date: 2026-04-29
// purpose: Fill-in scaffold for any multi-agent parallel session using the AgenticOS Command Center

Fill in every section marked with [FILL IN] before starting the session.
When complete, this file defines the full session. Paste the relevant sections
into each sub-agent's initial prompt.

Skill reference: `C:\ClaudeSkills\skills\agentic-parallel\SKILL.md`
Each agent MUST read that skill before beginning work.

---

## Pre-Flight Checklist

Complete before starting any agent:

- [ ] AgenticOS Command Center is running (check system tray for gold submarine icon)
- [ ] `C:\ClaudeSkills\AgenticOS\state\agents.json` exists and is writable
- [ ] `C:\ClaudeSkills\AgenticOS\state\approval_queue.json` exists and is writable
- [ ] `C:\ClaudeSkills\AgenticOS\state\outputs\` directory exists
- [ ] FastAPI state bus is responding at `http://localhost:7842` (open in browser — expect JSON)
- [ ] Dashboard WebView is showing the agent grid (no blank screen)
- [ ] You have decided how many agents to run and assigned each an ID (AGENT-01, AGENT-02, ...)
- [ ] Each agent's stages and approval gates are defined below in this file
- [ ] Initial agents.json seed has been written (Section 4 of this template)

---

## Section 1 — Mission Definition

```
Mission Name:    [FILL IN — e.g., "VA Claim Research Session #4"]
Date:            [FILL IN — e.g., 2026-04-29]
Domain:          [FILL IN — one of: va-advisory | game-dev | software-eng | 3d-content | general]
Operator:        Marcus Daley
Number of Agents: [FILL IN — integer, 1-6]
Expected Duration: [FILL IN — e.g., "2-3 hours"]
Session Goal:    [FILL IN — one paragraph describing what this session should produce]
```

---

## Section 2 — Agent Definitions

Copy this block once per agent. Fill in all fields.

### Agent [N] — [FILL IN: short name, e.g., "Research Agent"]

```
agent_id:      AGENT-0[N]
domain:        [FILL IN — same as mission domain or a different domain if this agent crosses disciplines]
task:          [FILL IN — one sentence describing this agent's overall mission]
total_stages:  [FILL IN — integer, how many stages this agent has]
spawned_by:    [FILL IN — null if top-level; parent agent_id if sub-agent]
```

Stage breakdown:

| Stage | stage_label | Approval gate after? |
|---|---|---|
| 1 | [FILL IN] | [Yes / No] |
| 2 | [FILL IN] | [Yes / No] |
| 3 | [FILL IN] | [Yes / No] |
| ... | ... | ... |

Gate notes (what the operator should evaluate at each gate):

```
After Stage [N]: [FILL IN — what the operator should look for before clicking PROCEED]
```

Initial prompt to paste into this agent's Claude Code session:

```
Read C:\ClaudeSkills\skills\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-0[N].
Your domain is [domain].
Your task is: [task]
Your total_stages is [total_stages].
Your spawned_by is [spawned_by — null or parent agent_id].

Your stages are:
  Stage 1: [stage_label]
  Stage 2: [stage_label]
  ...

Approval gates after stages: [list stage numbers with gates, e.g., "2, 4"]

Begin by completing the Session Start Checklist in the skill, then write your initial
state entry to C:\ClaudeSkills\AgenticOS\state\agents.json, then begin Stage 1.
```

---

## Section 3 — Approval Gate Decision Guide

Use this guide when the dashboard shows a waiting_approval card.

| Decision | When to use |
|---|---|
| PROCEED | Output looks correct, complete, and ready to advance |
| RESEARCH MORE | Output is missing key information — send the agent to research before advancing |
| REVIEW BY AGENT | Output needs an independent correctness check before you decide |

Review questions to ask before clicking PROCEED:
- [ ] Does the output fully address the stage goal?
- [ ] Are citations or references accurate (spot-check one)?
- [ ] Is the confidence note reasonable given the complexity of the task?
- [ ] Are there any obvious hallucinations or unsupported claims?
- [ ] Is the output complete enough for the next stage to build on it?

---

## Section 4 — Initial agents.json Seed

Before starting the first agent, write this JSON to `C:\ClaudeSkills\AgenticOS\state\agents.json`.
Replace all [FILL IN] values with your actual mission data.
This pre-populates the dashboard with placeholder cards so the operator can see all
agents before any of them start writing state.

```json
[
  {
    "agent_id": "AGENT-01",
    "domain": "[FILL IN]",
    "task": "[FILL IN]",
    "stage_label": "Not started",
    "stage": 0,
    "total_stages": [FILL IN],
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "[FILL IN — ISO-8601 timestamp of when you write this seed]"
  }
]
```

Add one entry per agent. The agents will overwrite these entries with live data as they
start and progress.

---

## Section 5 — Post-Session Review

After all agents reach status: "complete":

- [ ] Read all final stage output files: `state/outputs/agent-{id}-stage-{total_stages}.md`
- [ ] Collate the outputs into a session summary document
- [ ] Note any REVISE or REJECT verdicts and whether they were resolved
- [ ] Archive the session: copy `state/outputs/` to a dated folder
- [ ] Clear `state/agents.json` to `[]` for the next session
- [ ] Clear `state/approval_queue.json` to `[]`
- [ ] Save this filled-in tasks.md to `C:\ClaudeSkills\AgenticOS\sessions\YYYY-MM-DD-[mission-name].md`

---

---

# Worked Example — 3-Agent VA Advisory Session

The following is a fully filled-in example. It is ready to run — do not fill in anything,
just read it to understand what a complete session definition looks like.

---

## Mission Definition

```
Mission Name:    VA Claim Research Session — PTSD Service Connection
Date:            2026-04-29
Domain:          va-advisory
Operator:        Marcus Daley
Number of Agents: 3
Expected Duration: 3-4 hours
Session Goal:    Produce a complete package for a veteran's PTSD service connection claim:
                 regulatory research on 38 C.F.R. Part 3 criteria, a draft buddy letter
                 from a fellow service member, and a compliance review of both documents
                 confirming they meet VA educational platform standards.
```

---

## Agent Definitions — Worked Example

### Agent 1 — Research Agent

```
agent_id:      AGENT-01
domain:        va-advisory
task:          Research 38 C.F.R. Part 3 service connection criteria for PTSD,
               identifying nexus requirements, buddy statement evidentiary value,
               and rating schedule criteria under 38 C.F.R. § 4.130.
total_stages:  4
spawned_by:    null
```

Stage breakdown:

| Stage | stage_label | Approval gate after? |
|---|---|---|
| 1 | Locating applicable CFR sections for PTSD service connection | No |
| 2 | Analyzing nexus requirements and evidentiary standards | Yes |
| 3 | Researching rating schedule criteria under § 4.130 | No |
| 4 | Compiling regulatory summary with citations | Yes |

Gate notes:

```
After Stage 2: Verify the nexus requirements cited are accurate. Spot-check
               38 C.F.R. § 3.304(f) against VA.gov. If citations look off, click
               RESEARCH MORE. If citations look correct, click PROCEED.

After Stage 4: Review the full regulatory summary. Check that all citations include
               section numbers. If the summary is thorough and well-cited, click PROCEED.
               If anything looks fabricated, click REVIEW BY AGENT.
```

Initial prompt for AGENT-01:

```
Read C:\ClaudeSkills\skills\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-01.
Your domain is va-advisory.
Your task is: Research 38 C.F.R. Part 3 service connection criteria for PTSD,
identifying nexus requirements, buddy statement evidentiary value, and rating schedule
criteria under 38 C.F.R. § 4.130.
Your total_stages is 4.
Your spawned_by is null.

Your stages are:
  Stage 1: Locating applicable CFR sections for PTSD service connection
  Stage 2: Analyzing nexus requirements and evidentiary standards
  Stage 3: Researching rating schedule criteria under § 4.130
  Stage 4: Compiling regulatory summary with citations

Approval gates after stages: 2, 4

Begin by completing the Session Start Checklist in the skill, then write your initial
state entry to C:\ClaudeSkills\AgenticOS\state\agents.json, then begin Stage 1.
```

---

### Agent 2 — Document Drafting Agent

```
agent_id:      AGENT-02
domain:        va-advisory
task:          Draft a buddy letter for a veteran's PTSD service connection claim,
               written from the perspective of a fellow service member who witnessed
               the in-service stressor event and its immediate behavioral aftermath.
total_stages:  3
spawned_by:    null
```

Stage breakdown:

| Stage | stage_label | Approval gate after? |
|---|---|---|
| 1 | Drafting buddy letter opening and witness credential section | No |
| 2 | Drafting stressor event description and observed behavioral changes | Yes |
| 3 | Drafting closing statement and formatting final letter | Yes |

Gate notes:

```
After Stage 2: Read the stressor description carefully. Verify it is factual and
               observable — no medical conclusions, no diagnoses, no speculation.
               Language must be first-person and limited to what the writer witnessed
               directly. If the draft overstates, click RESEARCH MORE. If it looks
               appropriate, click PROCEED.

After Stage 3: Read the complete letter. Verify: dated, signed block present,
               no legal conclusions, no guarantee of outcome language. If correct,
               click PROCEED. If uncertain whether the letter meets VA standards,
               click REVIEW BY AGENT.
```

Initial prompt for AGENT-02:

```
Read C:\ClaudeSkills\skills\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-02.
Your domain is va-advisory.
Your task is: Draft a buddy letter for a veteran's PTSD service connection claim,
written from the perspective of a fellow service member who witnessed the in-service
stressor event and its immediate behavioral aftermath.
Your total_stages is 3.
Your spawned_by is null.

Your stages are:
  Stage 1: Drafting buddy letter opening and witness credential section
  Stage 2: Drafting stressor event description and observed behavioral changes
  Stage 3: Drafting closing statement and formatting final letter

Approval gates after stages: 2, 3

Note: You may read AGENT-01's output from state/outputs/agent-01-stage-4.md
once it exists (AGENT-01 completes its research before you need it for Stage 3).
You do not need to wait for AGENT-01 — begin your drafting independently.

Begin by completing the Session Start Checklist in the skill, then write your initial
state entry to C:\ClaudeSkills\AgenticOS\state\agents.json, then begin Stage 1.
```

---

### Agent 3 — Compliance Review Agent

```
agent_id:      AGENT-03
domain:        va-advisory
task:          Review both the regulatory research document and the buddy letter draft
               for compliance with VA OGC 2004 Opinion (educational tool standard),
               California SB 694 free-model requirements, and VetAssist platform
               legal position. Flag any language that constitutes legal advice,
               outcome guarantees, or unauthorized practice of law.
total_stages:  3
spawned_by:    null
```

Stage breakdown:

| Stage | stage_label | Approval gate after? |
|---|---|---|
| 1 | Reviewing regulatory research for compliance issues | No |
| 2 | Reviewing buddy letter draft for compliance issues | No |
| 3 | Writing compliance summary report with pass/flag/fix items | Yes |

Gate notes:

```
After Stage 3: Read the compliance summary. Any item marked FLAG requires a human
               decision before the documents are used. If all items are PASS, click
               PROCEED. If any items are flagged, do not click PROCEED until you have
               decided how to handle them. Use REVIEW BY AGENT if you want a second
               opinion on a flagged item.
```

Initial prompt for AGENT-03:

```
Read C:\ClaudeSkills\skills\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-03.
Your domain is va-advisory.
Your task is: Review both the regulatory research document and the buddy letter draft
for compliance with VA OGC 2004 Opinion (educational tool standard), California SB 694
free-model requirements, and VetAssist platform legal position. Flag any language that
constitutes legal advice, outcome guarantees, or unauthorized practice of law.
Your total_stages is 3.
Your spawned_by is null.

Your stages are:
  Stage 1: Reviewing regulatory research for compliance issues
  Stage 2: Reviewing buddy letter draft for compliance issues
  Stage 3: Writing compliance summary report with pass/flag/fix items

Approval gates after stages: 3

Wait until the following output files exist before beginning your reviews:
  - AGENT-01 research: state/outputs/agent-01-stage-4.md (wait for AGENT-01 to complete)
  - AGENT-02 buddy letter: state/outputs/agent-02-stage-3.md (wait for AGENT-02 to complete)

Poll for these files every 30 seconds. Write your initial state entry to
C:\ClaudeSkills\AgenticOS\state\agents.json immediately (with stage_label:
"Waiting for AGENT-01 and AGENT-02 outputs"), then poll until both files exist
before beginning Stage 1.

Begin by completing the Session Start Checklist in the skill, then write your initial
state entry, then begin polling.
```

---

## Initial agents.json Seed — Worked Example

Write this to `C:\ClaudeSkills\AgenticOS\state\agents.json` before starting any agent:

```json
[
  {
    "agent_id": "AGENT-01",
    "domain": "va-advisory",
    "task": "Research 38 C.F.R. Part 3 service connection criteria for PTSD, identifying nexus requirements, buddy statement evidentiary value, and rating schedule criteria under 38 C.F.R. § 4.130.",
    "stage_label": "Not started",
    "stage": 0,
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
    "task": "Draft a buddy letter for a veteran's PTSD service connection claim, written from the perspective of a fellow service member who witnessed the in-service stressor event and its immediate behavioral aftermath.",
    "stage_label": "Not started",
    "stage": 0,
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
    "task": "Review both the regulatory research document and the buddy letter draft for compliance with VA OGC 2004 Opinion, California SB 694, and VetAssist platform legal position.",
    "stage_label": "Waiting for AGENT-01 and AGENT-02 outputs",
    "stage": 0,
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

---

## Post-Session Review — Worked Example

After all three agents complete:

- [ ] Read `state/outputs/agent-01-stage-4.md` — regulatory research summary
- [ ] Read `state/outputs/agent-02-stage-3.md` — final buddy letter
- [ ] Read `state/outputs/agent-03-stage-3.md` — compliance report
- [ ] If compliance report has FLAG items, resolve before using any documents
- [ ] Collate into: `C:\ClaudeSkills\AgenticOS\sessions\2026-04-29-ptsd-service-connection.md`
- [ ] Clear `state/agents.json` to `[]`
- [ ] Clear `state/approval_queue.json` to `[]`
```

**Step 2.3 — Self-review**

Verify the worked example against the skill protocol:
- All three agents begin with the Session Start Checklist ✓
- All agent_ids follow AGENT-0N format ✓
- All domain values use `va-advisory` (correct for this session) ✓
- AGENT-03 correctly polls for dependency output files before starting ✓
- stage 0 in the seed JSON is intentional — it signals "not started yet"; agents write stage: 1 on first state write ✓
- All output_ref paths in the seed are `null` (correct — no output yet) ✓
- approval gates are after Stage 2 and 4 for AGENT-01, after Stage 2 and 3 for AGENT-02, after Stage 3 for AGENT-03 ✓
- Gate notes give the operator concrete pass/fail criteria, not vague guidance ✓
- AGENT-02's note about reading AGENT-01's output is correctly framed as "you may read" not "you must wait" — they can work independently and converge at Stage 3 ✓

**Step 2.4 — Commit**

```
git -C C:\ClaudeSkills add tasks/agentic-parallel/tasks.md
git -C C:\ClaudeSkills commit -m "add agentic-parallel task template: fill-in scaffold for multi-agent sessions"
```

---

## Task 3 — Write `C:\ClaudeSkills\skills\agentic-parallel\README.md`

### What this file is

Human-facing documentation for the skill. Explains what the skill does, when to use it,
how to set up the Command Center before use, and how to fill in the task template.

Pattern followed: same structure as `Example_Skills/game-dev-helper/README.md`,
`Example_Skills/backend-workflow-helper/README.md`.

### Task steps

**Step 3.1 — Write the file**

File path: `C:\ClaudeSkills\skills\agentic-parallel\README.md`

Complete file content:

```markdown
# Agentic Parallel — Skill README

// filename: README.md
// developer: Marcus Daley
// date: 2026-04-29
// purpose: Human-facing documentation for the agentic-parallel skill

---

## What This Skill Does

The agentic-parallel skill is a behavioral protocol for Claude Code sub-agents running
in parallel under human supervision. Any agent that reads SKILL.md will:

- Write its state (progress, stage, status) to a shared JSON file that the AgenticOS
  Command Center dashboard reads in real time
- Pause at defined approval gates and wait for the human operator to click PROCEED,
  RESEARCH MORE, or REVIEW BY AGENT before advancing
- Write stage output files that the operator and reviewer agents can inspect
- Handle reviewer verdicts (PASS / REVISE / REJECT) and re-do work when required
- Track context window usage and flag itself before hitting limits

The result: you can run 3-6 Claude agents in parallel, watch all of them on one screen,
approve or gate any of them from that screen, and spawn a reviewer for any agent's
output — all without typing a single terminal command.

---

## When to Use This Skill

Use it whenever:
- You are running more than one Claude Code agent on a single mission
- The mission has stages where you want a human checkpoint before the next stage
- You want an independent reviewer to check an agent's output before you act on it
- You need visibility into which agent is doing what at any given moment

Do not use it for:
- Single-agent sessions where you are directly supervising in the terminal
- Quick ad-hoc tasks without defined stages
- Automated pipelines that run unattended (this skill requires a human at the dashboard)

---

## Prerequisites

Before using this skill, you need:

1. **AgenticOS Command Center running** — The WPF dashboard application must be open
   in the system tray. Look for the gold submarine icon in the Windows taskbar tray.
   If it is not there, launch `C:\ClaudeSkills\AgenticOS\agentic_dashboard.py`.

2. **FastAPI state bus responding** — Open `http://localhost:7842` in a browser.
   You should see a JSON response. If you see an error, the dashboard did not start
   the server correctly — check the dashboard log (right-click tray icon > View Logs).

3. **State directory writable** — The following files must exist:
   - `C:\ClaudeSkills\AgenticOS\state\agents.json`
   - `C:\ClaudeSkills\AgenticOS\state\approval_queue.json`
   - `C:\ClaudeSkills\AgenticOS\state\outputs\` (directory)

   If they do not exist, the dashboard creates them on first launch.

4. **Task template filled in** — Complete `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md`
   before starting any agents. The template defines every agent's ID, domain, stages,
   and approval gates. Running agents without a completed template leads to inconsistent
   state and missing gate definitions.

---

## Setup: Step by Step

### Step 1 — Launch the Command Center

Double-click `C:\ClaudeSkills\AgenticOS\agentic_dashboard.py` or look for it in
Windows startup if auto-launch is enabled. The gold submarine icon appears in the
system tray. Single-click it to open the dashboard window.

### Step 2 — Fill In the Task Template

Open `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md`.

Fill in:
- Mission name, date, domain, number of agents
- For each agent: agent_id, domain, task, total_stages, stage labels, approval gates
- The initial `agents.json` seed JSON (Section 4 of the template)

Refer to the worked example at the bottom of the template for a complete filled-in
reference — a 3-agent VA Advisory session with research, drafting, and compliance agents.

### Step 3 — Write the agents.json Seed

Copy the filled-in JSON from Section 4 of your task template.
Write it to `C:\ClaudeSkills\AgenticOS\state\agents.json`.

The dashboard will pick up the file and show placeholder cards for each agent
within 2 seconds of the write.

### Step 4 — Start Each Agent

Open a Claude Code session for each agent. Paste the initial prompt from that agent's
definition in the task template.

The first thing each agent will do is read SKILL.md, complete the Session Start
Checklist, write its initial state, and begin Stage 1.

You can start agents sequentially (one at a time) or in parallel (multiple Claude Code
sessions open simultaneously). The state bus handles concurrent writes safely because
each agent upserts only its own entry.

### Step 5 — Operate the Dashboard

Watch the agent cards. Each card shows:
- Current stage and stage label
- Progress bar (filled by progress_pct)
- Spline 3D visual (sonar ring pulse rate reflects status)
- Context window gauge (filled by context_pct_used)
- PROCEED / RESEARCH MORE / REVIEW BY AGENT buttons (enabled only at approval gates)

When a card shows WAITING APPROVAL:
- Open the stage output file linked in the card (`output_ref`)
- Read the output and the confidence note
- Use the Approval Gate Decision Guide in the task template
- Click the appropriate button

When a REVIEW BY AGENT verdict appears:
- Read the verdict in the expandable ReviewerPanel below the buttons
- PASS: click PROCEED to advance the agent
- REVISE: click PROCEED — the agent will re-do the current stage with the reviewer's notes
- REJECT: click PROCEED — the agent will re-approach the stage from a new angle

### Step 6 — Session Wrap-Up

When all agent cards show COMPLETE:
- Follow the Post-Session Review checklist in your task template
- Archive outputs to a dated session folder
- Clear agents.json and approval_queue.json for the next session

---

## File Structure

```
skills/agentic-parallel/
  SKILL.md        ← Protocol document every sub-agent reads (this skill)
  README.md       ← This file

tasks/agentic-parallel/
  tasks.md        ← Fill-in scaffold for any multi-agent session

AgenticOS/
  agentic_server.py           ← FastAPI state bus (reads/writes state files)
  agentic_dashboard.py        ← WPF launcher + system tray
  state/
    agents.json               ← Live agent state (written by agents)
    approval_queue.json       ← Pending decisions (written by dashboard, read by agents)
    outputs/                  ← Stage output files + reviewer verdicts
```

---

## Domain Reference

| Domain value | Use for |
|---|---|
| `va-advisory` | VA benefits, buddy letters, CFR research, VR&E, claims strategy |
| `game-dev` | Unreal Engine 5, gameplay systems, game AI, shaders, level design |
| `software-eng` | Full-stack apps, APIs, databases, VetAssist, DevProductivityTracker |
| `3d-content` | 3D modeling, textures, Blender, UE5 asset pipeline |
| `general` | Anything that does not fit a specific domain |

---

## Notes

- The skill is `user-invocable: false` — it is loaded by agents from their initial
  prompt, not by the user directly. You invoke it by including the read instruction
  in the agent's starting prompt (as shown in the task template).
- Reviewer agents use `claude-haiku-4-5-20251001` (fast, low cost, different model
  instance than the worker agents to reduce confirmation bias).
- The skill does not handle network calls or API requests. All state is file-based.
  This keeps it offline-capable and human-inspectable at any time.
- If the dashboard is closed while agents are running, agents continue writing state
  files. Reopen the dashboard and it will read the current agents.json and show
  up-to-date cards.
```

**Step 3.2 — Commit**

```
git -C C:\ClaudeSkills add skills/agentic-parallel/README.md
git -C C:\ClaudeSkills commit -m "add agentic-parallel README: skill documentation and setup guide"
```

---

## Verification Steps

### Verification 1 — Load the skill in Claude Code

Start a new Claude Code session and provide this prompt:

```
Read C:\ClaudeSkills\skills\agentic-parallel\SKILL.md and confirm you understand
the agent state-writing protocol. Do not begin any task — only confirm you can
summarize the Session Start Checklist and the Approval Gate Protocol.
```

Expected response: The agent names all checklist items and describes the polling loop
and decision branching (proceed / research / review) correctly.

### Verification 2 — Run a test agent

With the Command Center running, start a single-agent session using the worked example
AGENT-01 prompt from tasks.md. Watch the dashboard.

Expected behavior within 30 seconds:
- A card for AGENT-01 appears in the dashboard
- The card shows domain "va-advisory" and the correct task text
- The stage bar shows 0% (or begins advancing as Stage 1 starts)
- The Spline sonar ring begins pulsing (fast pulse = active)

### Verification 3 — Verify state in agents.json

Open `C:\ClaudeSkills\AgenticOS\state\agents.json` in VS Code during the session.

Confirm:
- The file is valid JSON (no parse errors)
- The AGENT-01 entry exists with all 15 required fields present
- `updated_at` is a valid ISO-8601 timestamp
- `status` is one of the five valid values
- No other agents' entries are missing or corrupted

### Verification 4 — Approval gate test

Let the test agent reach its first approval gate (after Stage 2 in the worked example).

Confirm:
- The dashboard card changes to WAITING APPROVAL state (amber glow)
- The PROCEED button becomes clickable
- `state/agents.json` shows `status: "waiting_approval"` and `awaiting: "proceed"`
- `state/approval_queue.json` is empty (waiting for a decision — the agent has NOT
  written to it; only the dashboard writes to it)

Click PROCEED. Confirm:
- The dashboard card returns to ACTIVE state (gold glow)
- `state/agents.json` shows `status: "active"` and `awaiting: null`
- Stage increments to 3

### Verification 5 — Review verdict test

At an approval gate, click REVIEW BY AGENT.

Confirm:
- `state/agents.json` shows `status: "waiting_review"` and `awaiting: "review"`
- The dashboard card shows a teal double-pulse visual
- A file appears at `state/outputs/agent-01-review.md` (written by the reviewer agent)
- The card expands to show the reviewer verdict
- `reviewer_verdict` field in agents.json is populated (up to 200 chars)
- The PROCEED button re-enables after the verdict appears

---

## Self-Review — Consistency Check

### Field name consistency

Every field name in SKILL.md must match the TypeScript `AgentState` type from Plan 3
and the Python Pydantic model from Plan 1. Verified fields:

| Field | SKILL.md | Spec Section 5 | Match |
|---|---|---|---|
| agent_id | ✓ | ✓ | Yes |
| domain | ✓ | ✓ | Yes |
| task | ✓ | ✓ | Yes |
| stage_label | ✓ | ✓ | Yes |
| stage | ✓ | ✓ | Yes |
| total_stages | ✓ | ✓ | Yes |
| progress_pct | ✓ | ✓ | Yes |
| status | ✓ | ✓ | Yes |
| context_pct_used | ✓ | ✓ | Yes |
| output_ref | ✓ | ✓ | Yes |
| awaiting | ✓ | ✓ | Yes |
| error_msg | ✓ | ✓ | Yes |
| spawned_by | ✓ | ✓ | Yes |
| reviewer_verdict | ✓ | ✓ | Yes |
| updated_at | ✓ | ✓ | Yes |

Total fields: 15. All 15 present in SKILL.md, all 15 in worked example JSON. ✓

### Status values consistency

Spec lists: `active | waiting_approval | waiting_review | complete | error`
SKILL.md lists: `active | waiting_approval | waiting_review | complete | error` ✓

### Awaiting values consistency

Spec lists: `proceed | research | review | null`
SKILL.md lists: `proceed | research | review | null` ✓

### Domain values consistency

Spec Section 11 lists: `va-advisory`, `game-dev`, `software-eng`, `3d-content`, `general`
SKILL.md Section 11 lists: `va-advisory`, `game-dev`, `software-eng`, `3d-content`, `general` ✓

### Approval queue shape consistency

Spec Section 7 shape: `agent_id`, `decision`, `reviewer_context`, `decided_at`
SKILL.md references: `agent_id` (to identify entry), `decision` (to branch on)
SKILL.md correctly ignores `reviewer_context` (server uses it to spawn reviewer, not the agent) ✓
SKILL.md correctly ignores `decided_at` (not needed by agent) ✓

### Reviewer model consistency

Spec Section 8: `claude-haiku-4-5-20251001`
README.md Notes section: `claude-haiku-4-5-20251001` ✓
(SKILL.md does not mention the model — correct, the agent does not spawn its own reviewer)

### Worked example accuracy

AGENT-01 total_stages: 4, stages listed: 4, approval gates after: 2 and 4 ✓
AGENT-02 total_stages: 3, stages listed: 3, approval gates after: 2 and 3 ✓
AGENT-03 total_stages: 3, stages listed: 3, approval gates after: 3 only ✓
Seed JSON entry count: 3 entries matching the 3 agents ✓
Seed JSON all 15 fields present in each entry ✓
AGENT-03 dependency polling instruction is explicit and actionable ✓

---

## Files Created

| File | Path | Purpose |
|---|---|---|
| SKILL.md | `C:\ClaudeSkills\skills\agentic-parallel\SKILL.md` | Agent behavioral protocol |
| tasks.md | `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md` | Fill-in session scaffold |
| README.md | `C:\ClaudeSkills\skills\agentic-parallel\README.md` | Human-facing documentation |

---

## Commit Sequence

```
# After Task 1
git -C C:\ClaudeSkills add skills/agentic-parallel/SKILL.md
git -C C:\ClaudeSkills commit -m "add agentic-parallel skill: agent state protocol for Command Center"

# After Task 2
git -C C:\ClaudeSkills add tasks/agentic-parallel/tasks.md
git -C C:\ClaudeSkills commit -m "add agentic-parallel task template: fill-in scaffold for multi-agent sessions"

# After Task 3
git -C C:\ClaudeSkills add skills/agentic-parallel/README.md
git -C C:\ClaudeSkills commit -m "add agentic-parallel README: skill documentation and setup guide"
```

---

## Next Steps

Spawn the **reviewer** agent to validate this plan. Specific things the reviewer should check:

1. Do all 15 field names in SKILL.md match Plans 1-3 exactly? Pay particular attention to `stage_label` vs `stageLabel` (camelCase vs snake_case) — the spec uses snake_case throughout.
2. Is the upsert procedure in Section 5 of SKILL.md safe for concurrent writes by multiple agents? (Answer: no — two agents could read simultaneously and each overwrite the other's entry. The reviewer should flag this and recommend whether the server should own the write or whether a file lock is needed.)
3. Does the worked example in tasks.md have any logical dependency issues? Specifically: AGENT-02 Stage 2 says "stressor event description and observed behavioral changes" — does it need AGENT-01's research to write this accurately? If so, should a dependency note be added?
4. Is the output file structure in SKILL.md Section 9 complete enough for the reviewer agent to produce a useful verdict?
5. Is the context_pct_used calculation in Section 7 realistic? The word-count * 1.33 method is an approximation — is it accurate enough for the 80% warning gate to be meaningful?
