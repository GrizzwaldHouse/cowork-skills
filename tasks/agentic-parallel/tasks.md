<!-- tasks.md -->
<!-- Developer: Marcus Daley -->
<!-- Date: 2026-04-30 -->
<!-- Purpose: Fill-in session scaffold for AgenticOS parallel agent sessions -->

# AgenticOS Parallel Session — Mission Brief

// How to use this template:
// 1. Copy this file to tasks/agentic-parallel/sessions/YYYY-MM-DD-mission-name.md
// 2. Fill in every field marked FILL_IN. Leave no FILL_IN placeholders in your saved copy.
// 3. Write the agents.json seed block (Section 4) to C:\ClaudeSkills\AgenticOS\state\agents.json
//    before launching any agent.
// 4. Open one Claude Code session per agent. Paste that agent's prompt block (Section 5)
//    at the start of the session — nothing before it.
// 5. Watch the dashboard. Click PROCEED / RESEARCH MORE / REVIEW BY AGENT when cards hit gates.
// 6. After all agents show complete, run the post-session checklist (Section 6).

---

## Domain Options Reference

va-advisory | game-dev | software-eng | 3d-content | general

---

## Section 1 — Session Metadata

| Field             | Value                      |
|-------------------|----------------------------|
| Date              | FILL_IN (YYYY-MM-DD)       |
| Operator          | FILL_IN (your name)        |
| Session goal      | FILL_IN (one paragraph — what this run will produce and why it matters) |
| Estimated duration| FILL_IN (e.g., 2 hours)    |
| Agent count       | FILL_IN (1–6)              |
| Domain(s)         | FILL_IN (from domain options above) |

---

## Section 2 — Agent Slots

Copy one block per agent. Remove unused blocks.

---

### AGENT-01

| Field         | Value                                                       |
|---------------|-------------------------------------------------------------|
| agent_id      | AGENT-01                                                    |
| domain        | FILL_IN                                                     |
| task          | FILL_IN (one sentence describing this agent's overall mission) |
| total_stages  | FILL_IN (integer)                                           |
| output_ref    | state/outputs/agent-01-stage-FILL_IN.md (terminal stage)   |

**Stage list:**

| Stage | Label                        | Gate? |
|-------|------------------------------|-------|
| 1     | FILL_IN (present-tense verb phrase) |       |
| 2     | FILL_IN                      |       |
| 3     | FILL_IN                      | [GATE] |
| 4     | FILL_IN                      |       |
| 5     | FILL_IN                      | [GATE] |

// [GATE] marks every stage where the agent must pause and wait for your decision.
// Remove or add rows to match your total_stages count.
// At minimum, put a [GATE] at the last stage so you review final output before complete.

**Gate decisions (fill in for each [GATE] stage):**

- Gate at stage FILL_IN: FILL_IN (what you will check; approval policy: human / auto-proceed)
- Gate at stage FILL_IN: FILL_IN

**Reviewer policy:** FILL_IN (which gates are likely candidates for REVIEW BY AGENT; or "none")

---

### AGENT-02

| Field         | Value                                                       |
|---------------|-------------------------------------------------------------|
| agent_id      | AGENT-02                                                    |
| domain        | FILL_IN                                                     |
| task          | FILL_IN                                                     |
| total_stages  | FILL_IN                                                     |
| output_ref    | state/outputs/agent-02-stage-FILL_IN.md                     |

**Stage list:**

| Stage | Label   | Gate? |
|-------|---------|-------|
| 1     | FILL_IN |       |
| 2     | FILL_IN | [GATE] |
| 3     | FILL_IN | [GATE] |

**Gate decisions:**

- Gate at stage FILL_IN: FILL_IN
- Gate at stage FILL_IN: FILL_IN

**Reviewer policy:** FILL_IN

---

### AGENT-03

| Field         | Value                                                       |
|---------------|-------------------------------------------------------------|
| agent_id      | AGENT-03                                                    |
| domain        | FILL_IN                                                     |
| task          | FILL_IN                                                     |
| total_stages  | FILL_IN                                                     |
| output_ref    | state/outputs/agent-03-stage-FILL_IN.md                     |

**Stage list:**

| Stage | Label   | Gate? |
|-------|---------|-------|
| 1     | FILL_IN |       |
| 2     | FILL_IN | [GATE] |
| 3     | FILL_IN | [GATE] |

**Gate decisions:**

- Gate at stage FILL_IN: FILL_IN
- Gate at stage FILL_IN: FILL_IN

**Reviewer policy:** FILL_IN

---

### AGENT-04

| Field         | Value                                                       |
|---------------|-------------------------------------------------------------|
| agent_id      | AGENT-04                                                    |
| domain        | FILL_IN                                                     |
| task          | FILL_IN                                                     |
| total_stages  | FILL_IN                                                     |
| output_ref    | state/outputs/agent-04-stage-FILL_IN.md                     |

**Stage list:**

| Stage | Label   | Gate? |
|-------|---------|-------|
| 1     | FILL_IN |       |
| 2     | FILL_IN | [GATE] |
| 3     | FILL_IN | [GATE] |

**Gate decisions:**

- Gate at stage FILL_IN: FILL_IN
- Gate at stage FILL_IN: FILL_IN

**Reviewer policy:** FILL_IN

---

## Section 3 — Success Criteria

Boolean checklist. Walk this after all agents show complete.

- [ ] FILL_IN
- [ ] FILL_IN
- [ ] FILL_IN
- [ ] All stage output files present in C:\ClaudeSkills\AgenticOS\state\outputs\
- [ ] No agent cards show status: error

---

## Section 4 — agents.json Seed

Write this block to C:\ClaudeSkills\AgenticOS\state\agents.json before launching any agent.
Replace every FILL_IN. The server reads this within 2 seconds and renders one card per entry.

```json
[
  {
    "agent_id": "AGENT-01",
    "domain": "FILL_IN",
    "task": "FILL_IN",
    "stage_label": "FILL_IN (label of stage 1)",
    "stage": 1,
    "total_stages": FILL_IN,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": "state/outputs/agent-01-stage-1.md",
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "FILL_IN (ISO-8601 UTC, e.g. 2026-04-30T10:00:00Z)"
  },
  {
    "agent_id": "AGENT-02",
    "domain": "FILL_IN",
    "task": "FILL_IN",
    "stage_label": "FILL_IN",
    "stage": 1,
    "total_stages": FILL_IN,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": "state/outputs/agent-02-stage-1.md",
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "FILL_IN"
  }
]
```

// Add or remove objects to match your agent count.
// All agents start with stage=1, progress_pct=0, status="active", awaiting=null.

---

## Section 5 — Per-Agent Launch Prompts

Paste the relevant block — and nothing else — at the top of each agent's Claude Code session.

---

**AGENT-01 launch prompt:**

```
You are AGENT-01 in a supervised multi-agent session.

agent_id: AGENT-01
domain: FILL_IN
task: FILL_IN
total_stages: FILL_IN
spawned_by: null

Your stages:
1. FILL_IN
2. FILL_IN
3. FILL_IN [GATE]
4. FILL_IN
5. FILL_IN [GATE]

State directory: C:\ClaudeSkills\AgenticOS\state\
Skill to read first: C:\ClaudeSkills\skills\agentic-parallel\SKILL.md

Read SKILL.md completely before taking any other action.
Run the Section 13 Session Start Checklist.
Write your initial agents.json entry.
Begin Stage 1.
```

---

**AGENT-02 launch prompt:**

```
You are AGENT-02 in a supervised multi-agent session.

agent_id: AGENT-02
domain: FILL_IN
task: FILL_IN
total_stages: FILL_IN
spawned_by: null

Your stages:
1. FILL_IN
2. FILL_IN [GATE]
3. FILL_IN [GATE]

State directory: C:\ClaudeSkills\AgenticOS\state\
Skill to read first: C:\ClaudeSkills\skills\agentic-parallel\SKILL.md

Read SKILL.md completely before taking any other action.
Run the Section 13 Session Start Checklist.
Write your initial agents.json entry.
Begin Stage 1.
```

---

**AGENT-03 launch prompt:**

```
You are AGENT-03 in a supervised multi-agent session.

agent_id: AGENT-03
domain: FILL_IN
task: FILL_IN
total_stages: FILL_IN
spawned_by: null

Your stages:
1. FILL_IN
2. FILL_IN [GATE]
3. FILL_IN [GATE]

State directory: C:\ClaudeSkills\AgenticOS\state\
Skill to read first: C:\ClaudeSkills\skills\agentic-parallel\SKILL.md

Read SKILL.md completely before taking any other action.
Run the Section 13 Session Start Checklist.
Write your initial agents.json entry.
Begin Stage 1.
```

---

**AGENT-04 launch prompt:**

```
You are AGENT-04 in a supervised multi-agent session.

agent_id: AGENT-04
domain: FILL_IN
task: FILL_IN
total_stages: FILL_IN
spawned_by: null

Your stages:
1. FILL_IN
2. FILL_IN [GATE]
3. FILL_IN [GATE]

State directory: C:\ClaudeSkills\AgenticOS\state\
Skill to read first: C:\ClaudeSkills\skills\agentic-parallel\SKILL.md

Read SKILL.md completely before taking any other action.
Run the Section 13 Session Start Checklist.
Write your initial agents.json entry.
Begin Stage 1.
```

---

## Section 6 — Post-Session Checklist

Run after all agent cards show status: complete.

- [ ] Walk Section 3 success criteria. Every box checked before archiving.
- [ ] Archive C:\ClaudeSkills\AgenticOS\state\outputs\ to AgenticOS/sessions/YYYY-MM-DD-mission/outputs/
- [ ] Copy this filled-in template to AgenticOS/sessions/YYYY-MM-DD-mission/task.md
- [ ] Reset C:\ClaudeSkills\AgenticOS\state\agents.json to []
- [ ] Reset C:\ClaudeSkills\AgenticOS\state\approval_queue.json to []
- [ ] Note any protocol friction in docs/superpowers/postmortems/YYYY-MM-DD-mission.md

---

## How to Launch

**Start the server:**
```
pwsh C:\ClaudeSkills\launch_agentic_os.ps1
```
Confirm the gold submarine icon appears in the Windows system tray.

**Open the dashboard:**
Open a browser to http://localhost:{REST_PORT}/app (port from AgenticOS/config.py).
You should see one card per agent within 2 seconds of writing agents.json.

**Start each agent:**
Open a new Claude Code terminal session per agent.
Paste that agent's Section 5 prompt block. Nothing before it.
The agent reads SKILL.md, runs its checklist, writes state, and begins Stage 1.
The dashboard card transitions from seed values to live values within ~30 seconds.

**At each gate:**
The card status pill turns to "waiting_approval". The PROCEED / RESEARCH MORE / REVIEW BY AGENT
buttons activate. Read the output file at the path shown on the card, then click your decision.
