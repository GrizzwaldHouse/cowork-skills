---
name: agentic-parallel
description: Agent state-writing protocol for the AgenticOS Command Center. Any Claude sub-agent running in a multi-agent parallel session reads this skill to participate in dashboard tracking, approval gates, and reviewer spawning.
user-invocable: false
---

# Agentic Parallel, Agent State Protocol

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

## 2. State Files, Locations and Format

All state lives in: `C:\ClaudeSkills\AgenticOS\state\`

| File | Purpose | Who writes |
|---|---|---|
| `state/agents.json` | Live agent state, one entry per agent, JSON array | Each agent writes its own entry |
| `state/approval_queue.json` | Pending approval decisions from the dashboard | FastAPI writes; agent reads and removes its entry |
| `state/outputs/agent-{id}-stage-{n}.md` | Stage output files | Each agent writes its stage output |
| `state/outputs/agent-{id}-review.md` | Reviewer verdict file | Reviewer agent writes; main agent reads |

`{id}` in file names is the lowercase agent_id with the hyphen preserved.
Examples: `agent-01-stage-2.md`, `agent-02-review.md`

---

## 3. State Writing Contract, the AgentState Shape

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

## 4. When to Write State, Required Write Points

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

## 5. File Write Procedure, Upsert Protocol

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
- Cap at 99, never write 100 unless you are in an error state from context exhaustion

Write `context_pct_used` at every state write, not only at stage transitions.

If context usage exceeds 80%: set `status: "waiting_approval"` and `awaiting: "proceed"`
at the next natural stage boundary. Do not continue to the next stage without explicit
approval when context is above 80%. Write `stage_label` as "Context at 80%, awaiting
approval to continue" so the operator sees the reason.

---

## 8. Approval Gate Protocol

Approval gates are checkpoints where you pause and wait for the human operator to decide
whether to proceed. Gates are defined in your task template. You may also reach an
unplanned gate at 80% context (see Section 7).

### 8.1 Entering a gate

When you reach an approval gate:

1. Write your completed output for the current stage to `state/outputs/agent-{id}-stage-{n}.md`
2. Write state with: `status: "waiting_approval"`, `awaiting: "proceed"`, updated `output_ref`
3. Stop all work. Do not advance to the next stage.
4. Begin polling `state/approval_queue.json` per Section 8.2

### 8.2 Polling for a decision

Poll `state/approval_queue.json` every 2 seconds.

On each poll:
1. Read `state/approval_queue.json`
2. Parse as JSON array
3. Search for an entry where `agent_id` equals your agent_id
4. If not found: wait 2 seconds and poll again
5. If found: read the `decision` field and proceed to Section 8.3

The dashboard operator chooses one of three decisions: `proceed`, `research`, or `review`.

### 8.3 Handling a `proceed` decision

1. Read the entry from `approval_queue.json`
2. Remove your entry from the array (leave all other entries intact)
3. Write the updated array back to `state/approval_queue.json`
4. Increment stage, update stage_label to the next stage
5. Write state with: `status: "active"`, `awaiting: null`
6. Continue work on the next stage

### 8.4 Handling a `research` decision

1. Read the entry from `approval_queue.json`
2. Remove your entry from the array
3. Write the updated array back to `state/approval_queue.json`
4. Write state with: `status: "waiting_review"`, `awaiting: "research"`
5. Stop work. The dashboard will spawn a research sub-agent automatically.
6. Poll `state/approval_queue.json` again, the research sub-agent result will appear
   as a new `proceed` decision for your agent_id once the research is complete
7. When the `proceed` decision arrives, handle it per Section 8.3

### 8.5 Handling a `review` decision

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
# Agent {AGENT-ID}, Stage {N}: {Stage Label}
**Agent:** {agent_id}
**Domain:** {domain}
**Stage:** {stage} of {total_stages}
**Completed at:** {ISO-8601 timestamp}

---

## Work Output

{The complete output for this stage, findings, analysis, drafted text, code,
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
2. Find the verdict line, it starts with `PASS`, `REVISE`, or `REJECT`
3. Read the notes beneath the verdict line
4. Set `reviewer_verdict` in your state to the verdict line plus the first note
   (truncated to 200 characters total)
5. Do not discard the full verdict file contents, reference the full file in your
   next stage's work if the verdict is REVISE or REJECT
6. If verdict is `PASS`: when the operator clicks PROCEED, continue to the next stage
7. If verdict is `REVISE`: when the operator clicks PROCEED, re-do the current stage
   incorporating the reviewer's specific notes before advancing
8. If verdict is `REJECT`: when the operator clicks PROCEED, treat the current stage
   as failed, write a new stage output that re-approaches the problem from a different
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
5. Leave `awaiting: null`, errors require human diagnosis, not a queue entry

Error message format: `"[Error type]: [What happened] at stage [N]"`
Example: `"FileWriteError: Could not write agents.json, path not accessible at stage 3"`

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
3. Do not remove your entry from agents.json, the dashboard retains complete agents
   for the operator's review until they manually dismiss the card

The session is complete. Do not poll approval_queue after writing complete status.
