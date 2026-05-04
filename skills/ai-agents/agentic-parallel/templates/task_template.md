<!--
filename: task_template.md
developer: Marcus Daley
date: 2026-04-29
purpose: Fill-in scaffold for a single multi-agent run under the AgenticOS Command Center. Copy this template into a session-specific file (such as tasks/agentic-parallel/sessions/2026-04-29-<mission>.md) and replace every [FILL IN] before launching any agent.
-->

# Multi-Agent Task Template

Skill reference: `skills/ai-agents/agentic-parallel/SKILL.md`. Every agent below MUST read that skill in full at session start.

State paths and ports are symbolic; treat them as references to `AgenticOS/config.py` constants:
- `config.AGENTS_JSON` (currently `AgenticOS/state/agents.json`)
- `config.APPROVAL_QUEUE_JSON` (currently `AgenticOS/state/approval_queue.json`)
- `config.OUTPUTS_DIR` (currently `AgenticOS/state/outputs/`)
- `config.WEBSOCKET_PORT` (currently 7842)

If those constants change, this template still holds. Do not bake the literal port or paths into agent prompts; reference them by name and let the agent read `config.py` to resolve.

---

## 1. Header

```
TASK NAME:    [FILL IN - e.g., "VetAssist PTSD Service Connection Package"]
DOMAIN:       [FILL IN - va-advisory | game-dev | software-eng | 3d-content | general]
CREATED:      [FILL IN - YYYY-MM-DD]
OWNER:        Marcus Daley
SESSION GOAL: [FILL IN - one paragraph describing the artifact this run produces]
```

---

## 2. Agent Roster

| agent_id | role | total_stages | output_ref (terminal stage) |
|---|---|---|---|
| AGENT-01 | [FILL IN - short role label] | [FILL IN] | state/outputs/agent-01-stage-[FILL IN].md |
| AGENT-02 | [FILL IN] | [FILL IN] | state/outputs/agent-02-stage-[FILL IN].md |
| AGENT-03 | [FILL IN] | [FILL IN] | state/outputs/agent-03-stage-[FILL IN].md |
| ... | ... | ... | ... |

Number of agents: 1-6. Do not exceed 6 in one supervised session; the operator cannot meaningfully gate more than that in parallel.

---

## 3. Stage Definitions

Copy this block once per agent. Fill in every row.

### Agent [FILL IN: AGENT-NN] - [FILL IN: role label]

```
agent_id:     AGENT-NN
domain:       [FILL IN]
task:         [FILL IN - one-sentence overall mission for this agent]
spawned_by:   [FILL IN - null for top-level, parent agent_id otherwise]
total_stages: [FILL IN - integer]
```

| Stage | stage_label (present-tense verb phrase) | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | [FILL IN] | [FILL IN - e.g., "20 min"] | [Yes / No] |
| 2 | [FILL IN] | [FILL IN] | [Yes / No] |
| 3 | [FILL IN] | [FILL IN] | [Yes / No] |
| ... | ... | ... | ... |

Initial prompt to paste into this agent's Claude Code session:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-NN.
Your domain is [domain].
Your task is: [task]
Your total_stages is [total_stages].
Your spawned_by is [spawned_by - null or parent agent_id].

Your stages are:
  Stage 1: [stage_label]
  Stage 2: [stage_label]
  ...

Approval gates after stages: [list stage numbers that have gate_after = Yes]

Use AgenticOS.state_store and AgenticOS.config for every state write. Do not
hardcode paths or ports.

Begin by completing the Session Start Checklist in the skill, then write your
initial state entry through state_store.upsert_agent, then begin Stage 1.
```

---

## 4. Approval Policy

For each agent, declare which gates require a human click vs. which auto-proceed.

| agent_id | Gate after stage | Policy | Operator evaluation criteria |
|---|---|---|---|
| AGENT-01 | [N] | [Human approval / Auto-proceed] | [FILL IN - one sentence on what to look for before clicking PROCEED] |
| AGENT-01 | [M] | [Human approval / Auto-proceed] | [FILL IN] |
| AGENT-02 | [N] | [Human approval / Auto-proceed] | [FILL IN] |
| ... | ... | ... | ... |

Default policy: every gate marked `gate_after_stage = Yes` in Section 3 is human-approval. Auto-proceed is permitted only for low-risk transitions (gate exists for visibility, not for go/no-go). When in doubt, leave it as human approval.

---

## 5. Reviewer Policy

Reviewer agents are spawned by the dashboard via `AgenticOS/reviewer_spawner.py`, model `config.REVIEWER_MODEL` (currently Claude Haiku 4.5), timeout `config.REVIEWER_TIMEOUT_SECONDS` (currently 120 seconds).

| agent_id | Stage requiring reviewer | Verdict format expected | Why review here |
|---|---|---|---|
| AGENT-01 | [N] | PASS / REVISE / REJECT + 1-3 actionable notes | [FILL IN - e.g., "Citation accuracy on CFR sections"] |
| AGENT-02 | [M] | PASS / REVISE / REJECT + notes | [FILL IN] |
| ... | ... | ... | ... |

Verdict file path: `config.OUTPUTS_DIR / config.REVIEWER_OUTPUT_TEMPLATE.format(agent_id=...)` (currently `agent-{agent_id}-review.md` under `state/outputs/`).

Verdict format the worker agent will read (matches `models.ReviewerOutcome`):

```markdown
PASS | REVISE | REJECT

Note 1: [reviewer specific finding]
Note 2: [reviewer specific finding]
Note 3: [reviewer specific finding]
```

Recommend a reviewer when: citations need spot-checking, drafted text needs bias check, generated code needs correctness check, or anything where the operator wants a second opinion before clicking PROCEED.

---

## 6. Output Paths

Every stage output file MUST follow the Section 6 structure of the skill (Header, Work Output, Stage Summary, Confidence Note).

| Artifact | Path |
|---|---|
| AGENT-01 stage outputs | `state/outputs/agent-01-stage-{1..total_stages}.md` |
| AGENT-02 stage outputs | `state/outputs/agent-02-stage-{1..total_stages}.md` |
| AGENT-NN stage outputs | `state/outputs/agent-NN-stage-{1..total_stages}.md` |
| Reviewer verdicts | `state/outputs/agent-NN-review.md` (overwritten on each review pass for the same agent) |
| Final assembly (optional, owned by the merger agent) | [FILL IN - e.g., `state/outputs/final-claim-package.md`] |

---

## 7. Success Criteria

The session is successful when ALL of the following hold:

- [ ] Every agent reaches `status=complete` in `config.AGENTS_JSON`.
- [ ] Every terminal stage output file exists and follows the Section 6 (skill) structure.
- [ ] Every reviewer verdict (if any) shows PASS, OR a REVISE/REJECT was resolved through a redo and the redo PASSed.
- [ ] [FILL IN - mission-specific success criterion 1]
- [ ] [FILL IN - mission-specific success criterion 2]
- [ ] Operator has reviewed every gate and there are no orphaned `waiting_approval` rows.

---

## 8. Rollback Plan

If any agent fails (`status=error`):

1. Read `error_msg` from the agent's row in `config.AGENTS_JSON`.
2. Decide: fixable in place, or needs continuation agent?
3. If fixable in place:
   - Resolve the root cause (path, permission, tool error).
   - Have the agent retry the failing stage. Overwrite `state/outputs/agent-NN-stage-N.md`.
   - Have the agent upsert `status=active`, clear `error_msg`, refresh `updated_at`.
4. If a continuation is needed (typical for `ContextExhausted`):
   - Spawn a fresh Claude Code session.
   - Seed it with the prior agent's last successful output file (the `output_ref` from stage `N-1`).
   - Have the continuation agent read SKILL.md, then upsert the SAME `agent_id` (it inherits the row), with `stage=N`, `status=active`, `error_msg=None`, refreshed `updated_at`.
   - Continuation agent resumes from stage `N` as if the prior agent had not crashed.
5. If the failure is structural (state files corrupt, server down):
   - Stop all agents.
   - Restore `config.AGENTS_JSON` from the last good backup (or reset to `[]` and re-seed).
   - Restart the dashboard. Restart agents. Resume from the last completed stage of each.

---

## 9. Pre-Flight Checklist

Run before launching the first agent:

- [ ] AgenticOS Command Center dashboard is running (gold submarine in system tray).
- [ ] `curl http://{config.SERVER_HOST}:{config.REST_PORT}/healthz` returns 200.
- [ ] `config.AGENTS_JSON` and `config.APPROVAL_QUEUE_JSON` both exist (the server seeds them on boot).
- [ ] `config.OUTPUTS_DIR` exists and is writable.
- [ ] Section 1-7 of this template are fully filled in.
- [ ] `agents.json` is seeded with one placeholder row per agent (Section 10 below).
- [ ] Each agent's initial prompt (Section 3) has been copied to a clipboard or buffer ready to paste.

---

## 10. agents.json Seed

Write this to `config.AGENTS_JSON` BEFORE launching the first agent. Replace `[FILL IN]` placeholders with concrete values from Sections 1-3. The seed pre-populates the dashboard so all cards appear before agents start writing live state.

```json
[
  {
    "agent_id": "AGENT-01",
    "domain": "[FILL IN]",
    "task": "[FILL IN]",
    "stage_label": "Not started",
    "stage": 1,
    "total_stages": [FILL IN],
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "[FILL IN - ISO-8601 UTC timestamp]"
  }
]
```

Append one block per agent. Every block must satisfy the `models.AgentState` validator (notably: `stage >= 1`, `stage <= total_stages`, `progress_pct` in `[0, 100]`).

---

## 11. Post-Session Checklist

After every agent shows `status=complete` and the operator has reviewed every terminal output:

- [ ] Read every `state/outputs/agent-NN-stage-{total_stages}.md` and confirm against Section 7 success criteria.
- [ ] Archive `state/outputs/` to `AgenticOS/sessions/{YYYY-MM-DD}-{mission-name}/`.
- [ ] Save this filled-in template alongside the archived outputs.
- [ ] Reset `config.AGENTS_JSON` to `[]`.
- [ ] Reset `config.APPROVAL_QUEUE_JSON` to `[]`.
- [ ] Note any tooling friction or skill-protocol gaps in `docs/superpowers/postmortems/{date}-{mission}.md`.
