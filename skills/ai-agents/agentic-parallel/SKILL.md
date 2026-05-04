---
name: agentic-parallel
description: Cross-domain protocol for supervised parallel multi-agent runs against the AgenticOS Command Center. Use whenever Marcus says "spawn parallel agents", "multi-agent task", "review agent output", "approval gate", "monitor sub-agents", "supervised pipeline", "gate the next stage", "run several agents", "watch the agents", or kicks off a session with named AGENT-01, AGENT-02 roster. Defines the AgentState contract, the approval gate handshake, the reviewer-agent pattern, and the parallel etiquette every sub-agent must follow to appear in the Command Center dashboard with no extra wiring.
user-invocable: true
---

<!--
filename: SKILL.md
developer: Marcus Daley
date: 2026-04-29
purpose: Authoritative behavioral protocol for any Claude sub-agent participating in a supervised parallel run under the AgenticOS Command Center. Read in full at session start before any work, any state write, or any tool use. Following this skill is what makes an agent visible, gateable, and reviewable from the dashboard with zero additional configuration.
-->

# Agentic Parallel

> The cross-domain handshake every sub-agent in a supervised parallel run executes. Wires an agent into the AgenticOS Command Center for live tracking, human-in-the-loop approval gates, and independent reviewer spawns, without any project-specific glue code.

This skill is the contract. The dashboard, the FastAPI state bus, and the file watcher already exist (see `AgenticOS/agentic_server.py`, `AgenticOS/state_store.py`, `AgenticOS/file_watcher.py`). Your job as a participating sub-agent is to write the right shape to the right file at the right moment. Get those three things right and you appear on the operator's screen with progress, status, and approval buttons attached. Get any one of them wrong and the dashboard goes silent for your card.

## When To Use This Skill

Trigger automatically when:

- A task spawns more than one Claude Code sub-agent on a shared mission and a human operator is supervising
- The mission has named agents (AGENT-01, AGENT-02, ...) with declared stages and approval gates
- A task references `tasks/agentic-parallel/tasks.md` or pastes its filled-in content
- The user says "spawn parallel agents", "run a multi-agent task", "review the agent output", "approve before proceeding", "spawn a reviewer", or "monitor the agents"
- The AgenticOS Command Center dashboard is open (gold submarine icon in the system tray) before agents launch
- A sub-agent is being seeded with `agent_id`, `domain`, `total_stages`, and `spawned_by` fields in its initial prompt

Do NOT use when:

- A single agent is doing a single task in a single terminal (no parallel work, no human gate)
- The task is trivial (a one-liner fix, a quick lookup) where ceremony costs more than visibility
- There is no human-in-the-loop expectation (fully unattended automated pipeline)
- The user explicitly says "skip the dashboard" or "don't write state"
- An ad-hoc Claude Code session is doing exploratory work and the operator has not opened the Command Center

## Authority Files (Source Of Truth)

This skill cites three files as the only authoritative source for state shape, paths, ports, and timeouts. If any example below disagrees with these files, the files win:

- `AgenticOS/config.py`: every port (`WEBSOCKET_PORT`, `REST_PORT`), path (`AGENTS_JSON`, `APPROVAL_QUEUE_JSON`, `OUTPUTS_DIR`), timeout (`LOCK_ACQUIRE_TIMEOUT_SECONDS`, `REVIEWER_TIMEOUT_SECONDS`), reviewer model (`REVIEWER_MODEL`), and filename template (`REVIEWER_OUTPUT_TEMPLATE`).
- `AgenticOS/models.py`: the Pydantic v2 `AgentState`, `ApprovalDecision`, `ApprovalQueueEntry`, `ReviewerVerdict` models plus `AgentStatus`, `AgentDomain`, `ApprovalKind`, `ReviewerOutcome` enums. Field names, types, and constraints are defined there. Do not paraphrase them, mirror them.
- `AgenticOS/state_store.py`: the only sanctioned writer for `agents.json` and `approval_queue.json`. Performs temp-then-rename, advisory file locking (msvcrt on Windows, fcntl on POSIX), and concurrent-safe upserts. Sub-agents that bypass `state_store` and write JSON directly will eventually corrupt shared state.

Refer to constants symbolically wherever you can. When you must show a literal in an example, immediately attribute it (for example, "`config.WEBSOCKET_PORT` (currently 7842)") so a future port change does not silently break this skill's examples.

## 1. The AgentState Contract

The full field list, copied verbatim from `AgenticOS/models.py:AgentState`:

| Field | Type | Constraint |
|---|---|---|
| `agent_id` | `str` | `min_length=1`. Stable identifier such as `AGENT-01`. |
| `domain` | `AgentDomain` | One of `va-advisory`, `game-dev`, `software-eng`, `3d-content`, `general`. |
| `task` | `str` | `min_length=1`. One-line description of the agent's overall mission. |
| `stage_label` | `str` | `min_length=1`. Present-tense human label for the current stage. |
| `stage` | `int` | `ge=1`. Current stage number, 1-indexed. |
| `total_stages` | `int` | `ge=1`. Total stages this agent expects to execute. |
| `progress_pct` | `int` | `ge=0, le=100`. Overall progress percentage. |
| `status` | `AgentStatus` | One of `active`, `waiting_approval`, `waiting_review`, `complete`, `error`. |
| `context_pct_used` | `int` | `ge=0, le=100`. Percentage of context window consumed so far. |
| `output_ref` | `Optional[str]` | Path (relative to `AgenticOS/`) to the latest output file, or `None`. |
| `awaiting` | `Optional[ApprovalKind]` | One of `proceed`, `research`, `review`, or `None`. |
| `error_msg` | `Optional[str]` | Populated only when `status == error`. |
| `spawned_by` | `Optional[str]` | Parent `agent_id` if this agent was spawned (research or reviewer). |
| `reviewer_verdict` | `Optional[str]` | Trimmed verdict text once a reviewer completes. |
| `updated_at` | `datetime` | ISO 8601 UTC timestamp of the last update. |

Cross-field rule from `models.py`: `stage` MUST NOT exceed `total_stages`. The Pydantic `model_validator` rejects writes that violate this. If you accidentally set `stage = total_stages + 1` you will see a 422 from the server and a dashboard read failure.

The `model_config` declares `extra="forbid"`. Any extra field you invent is dropped at validation time. Stick to the contract.

## 2. State Writing Protocol

The shared write path is `config.AGENTS_JSON`, which currently resolves to `AgenticOS/state/agents.json`. The file is a JSON array. Multiple agents share it. You upsert your own entry (matched by `agent_id`) and never touch other entries.

### 2.1 When To Write

Write at every one of these moments. Missing any of them means stale data on the operator's screen:

| Trigger | What is updated |
|---|---|
| Session start (after Session Start Checklist passes) | Full entry, `stage=1`, `status=active`, `awaiting=null` |
| Stage transition | New `stage`, `stage_label`, `progress_pct`, `output_ref`, `updated_at` |
| Reaching an approval gate | `status=waiting_approval`, `awaiting=proceed`, refreshed `output_ref` |
| Receiving a gate decision | `status` and `awaiting` set per Section 4 below |
| Reviewer verdict consumed | `reviewer_verdict` populated, status transitions per Section 5 |
| Completion | `status=complete`, `stage=total_stages`, `progress_pct=100`, `awaiting=null` |
| Any unrecoverable error | `status=error`, `error_msg="<one-sentence cause>"` |

### 2.2 How To Write (Atomicity Is Mandatory)

The write must be atomic. The file watcher in `AgenticOS/file_watcher.py` reacts on every modification, and a half-written JSON array crashes the broadcaster. The only sanctioned writer is `AgenticOS/state_store.py`, which performs:

1. Acquire the advisory lock with timeout `config.LOCK_ACQUIRE_TIMEOUT_SECONDS` (currently 5.0 seconds), retrying every `config.LOCK_RETRY_INTERVAL_SECONDS` (currently 0.05 seconds).
2. Read the existing array from `config.AGENTS_JSON`.
3. Upsert your entry: replace if `agent_id` matches, append if it does not.
4. Write to a temp file with suffix `config.ATOMIC_WRITE_TEMP_SUFFIX + ".<pid>"`.
5. Rename the temp file over the target (POSIX-atomic on the same volume).
6. Release the lock.

Pseudocode (the sub-agent's perspective, mirroring `state_store`):

```python
# Use AgenticOS.state_store, not raw json.dump. The store owns atomicity.
from AgenticOS import config, state_store
from AgenticOS.models import AgentState, AgentStatus, AgentDomain
from datetime import datetime, timezone

# Compose the new state for this agent. Field names match models.AgentState exactly.
new_state = AgentState(
    agent_id="AGENT-01",
    domain=AgentDomain.VA_ADVISORY,
    task="Research 38 C.F.R. Part 3 service-connection criteria for PTSD",
    stage_label="Analyzing nexus requirements and evidentiary standards",
    stage=2,
    total_stages=4,
    progress_pct=50,
    status=AgentStatus.ACTIVE,
    context_pct_used=27,
    output_ref="state/outputs/agent-01-stage-2.md",
    awaiting=None,
    error_msg=None,
    spawned_by=None,
    reviewer_verdict=None,
    updated_at=datetime.now(timezone.utc),
)

# Upsert through the sanctioned writer; this is the only safe path.
state_store.upsert_agent(new_state)
```

Do NOT bypass `state_store`. Do NOT write partial JSON. Do NOT touch other agents' entries.

### 2.3 Bootstrap (Cold Start)

On first write at session start, if `config.AGENTS_JSON` does not exist or is empty, `state_store` creates it as `[<your entry>]`. The server's startup hook also seeds both state files with `[]` on first boot, so cold-start collisions are rare. If you see a `FileNotFoundError`, the server has not started: stop and surface that to the operator.

## 3. Approval Gate Protocol

Approval gates are the human-in-the-loop checkpoints declared in your task template. Every gate has the same shape: you stop, you write `waiting_approval`, you poll, you read your decision, you clear your entry, you proceed.

### 3.1 Entering A Gate

1. Write the stage's complete output to `state/outputs/agent-{id}-stage-{n}.md` per Section 6 (Output File Protocol).
2. Update your `AgentState` with `status=waiting_approval`, `awaiting=ApprovalKind.PROCEED`, `output_ref` pointing at the file from step 1.
3. Stop work. Do not advance `stage`. Do not start the next stage's work.
4. Begin polling per Section 3.2.

Note: you always set `awaiting=proceed` at a gate. The other two `ApprovalKind` values (`research` and `review`) describe what the operator decided, not what you are waiting for.

### 3.2 Polling The Approval Queue

The queue is `config.APPROVAL_QUEUE_JSON` (currently `AgenticOS/state/approval_queue.json`). Schema is `list[ApprovalQueueEntry]` from `models.py`:

```json
[
  {
    "agent_id": "AGENT-01",
    "decision": "proceed | research | review",
    "reviewer_context": "AgenticOS/state/outputs/agent-01-stage-2.md",
    "decided_at": "2026-04-29T14:35:00Z"
  }
]
```

Polling rule: read the file every 2 seconds. The file watcher cannot wake you from a polling sleep, so you ARE polling, but you are polling the queue (a small file with a small array), not `agents.json`. Each poll:

1. Read `config.APPROVAL_QUEUE_JSON`. If missing, treat as `[]`.
2. Find the entry where `agent_id` equals your `agent_id`.
3. If absent, sleep 2 seconds and poll again.
4. If present, read the `decision` field, then proceed to Section 3.3, 3.4, or 3.5.

Cap polling at a sane upper bound (say 60 minutes per gate). After that, write `status=error` with `error_msg="ApprovalTimeout: No decision after 60 minutes at stage <N>"`. The operator may have walked away.

### 3.3 Decision: PROCEED

Populated fields on the queue entry: `agent_id`, `decision="proceed"`, `decided_at`. (`reviewer_context` is `None` for proceed.)

1. Read your entry from `config.APPROVAL_QUEUE_JSON`.
2. Remove ONLY your entry from the array. Leave every other agent's entries intact.
3. Write the trimmed array back through `state_store` (it owns the lock).
4. Increment `stage`, update `stage_label`, recompute `progress_pct = round((stage / total_stages) * 100)`.
5. Update your `AgentState` with `status=active`, `awaiting=None`, refreshed `output_ref`.
6. Begin the new stage's work.

### 3.4 Decision: RESEARCH

Populated fields: `agent_id`, `decision="research"`, `decided_at`. The dashboard will spawn a research sub-agent on its own; you do not invoke it.

1. Remove your entry from the queue (same procedure as 3.3 step 2-3).
2. Update your `AgentState` with `status=waiting_review`, `awaiting=ApprovalKind.RESEARCH`. (Yes, `waiting_review` is the umbrella status for "waiting on another agent". The `awaiting` field disambiguates.)
3. Stop work. Do not advance `stage`.
4. Resume polling `config.APPROVAL_QUEUE_JSON`. The research sub-agent's output will arrive via a fresh `proceed` decision targeted at your `agent_id` once the operator clicks PROCEED again.
5. When that fresh `proceed` arrives, handle it per Section 3.3.

### 3.5 Decision: REVIEW

Populated fields: `agent_id`, `decision="review"`, `reviewer_context` (path to the file the reviewer will assess, falling back to your `output_ref` if the operator omitted it), `decided_at`.

1. Remove your entry from the queue.
2. Update your `AgentState` with `status=waiting_review`, `awaiting=ApprovalKind.REVIEW`, `reviewer_verdict=None`.
3. Stop work. The dashboard will spawn a reviewer subprocess via `AgenticOS/reviewer_spawner.py` using `config.REVIEWER_MODEL` (Claude Haiku 4.5) and `config.REVIEWER_TIMEOUT_SECONDS`.
4. Poll `config.OUTPUTS_DIR / config.REVIEWER_OUTPUT_TEMPLATE.format(agent_id=your_agent_id)` every 2 seconds.
5. When the verdict file exists: read it in full, then proceed to Section 5 (Reviewer Verdict Protocol).

## 4. The `ApprovalKind` Field Map

Copied from `models.py:ApprovalKind`. Each value populates `awaiting` differently and triggers different reads:

| ApprovalKind value | Set in `awaiting` when | Means |
|---|---|---|
| `proceed` | At every gate, while waiting for any decision | "I am stopped at a gate. Reading approval queue." |
| `research` | After operator clicks RESEARCH MORE | "Operator wants more context. A research sub-agent will run, then I will resume on the next proceed decision." |
| `review` | After operator clicks REVIEW BY AGENT | "Operator wants a verdict. A reviewer subprocess will write a verdict file, then I read it before the operator's final proceed." |

`awaiting` is `None` only when `status` is `active`, `complete`, or `error`. Any `waiting_*` status MUST have a non-null `awaiting`.

## 5. Reviewer Agent Pattern

When to recommend it: any time the operator is uncertain whether the stage's output is correct, complete, or unbiased. The dashboard surfaces it as REVIEW BY AGENT. The model is `config.REVIEWER_MODEL` (Haiku 4.5), chosen for speed, cost, and being a different model instance than the worker (which reduces same-model confirmation bias).

Context to include (provided by the operator via `reviewer_context`, or defaulted to your `output_ref`): the full markdown stage output (Section 6 format). The reviewer reads from `config.REVIEWER_PROMPT_TEMPLATE` filled with that file's contents. You do not assemble the prompt; the spawner does.

How the verdict is delivered: a markdown file at `config.OUTPUTS_DIR / config.REVIEWER_OUTPUT_TEMPLATE.format(agent_id=your_id)`. The reviewer writes it; you read it.

When you read the verdict:

1. Locate the line that begins with `PASS`, `REVISE`, or `REJECT`. This is the value of `models.ReviewerOutcome` and is always the first non-blank line of the verdict body.
2. Extract the verdict line plus the first reviewer note that follows it. Trim to 200 characters total.
3. Update your `AgentState`:
   - `reviewer_verdict = "<that 200-char extract>"`
   - `status = waiting_approval`
   - `awaiting = ApprovalKind.PROCEED`
4. The dashboard expands the card to show the verdict and re-enables PROCEED. Resume polling per Section 3.2.

When the operator's next `proceed` arrives:

| Outcome | Action on next stage |
|---|---|
| `PASS` | Advance normally per Section 3.3. |
| `REVISE` | Re-do the current stage incorporating the reviewer's notes verbatim. Overwrite the existing `state/outputs/agent-{id}-stage-{n}.md` (same path, same stage number). Do NOT increment `stage`. Re-enter the gate when finished. |
| `REJECT` | Treat the current stage as failed. Re-approach the problem from a different angle as the reviewer's notes specify. Overwrite the same output file. Do NOT increment `stage`. Re-enter the gate. |

For REVISE and REJECT, the re-done output replaces the prior file. Stage number does not advance until the operator approves the redo.

## 6. Output File Protocol

Path pattern: `state/outputs/agent-{id-lower}-stage-{n}.md` where `{id-lower}` is the lowercase `agent_id` with the hyphen preserved (`agent-01`, `agent-02`). Output goes under `config.OUTPUTS_DIR`.

Mandatory structure:

```markdown
# Agent {AGENT-ID} - Stage {N}: {Stage Label}
**Agent:** {agent_id}
**Domain:** {domain}
**Stage:** {stage} of {total_stages}
**Completed at:** {ISO-8601 UTC timestamp}

---

## Work Output

{Full stage output. Findings, analysis, drafted text, code, decisions made,
references consulted. Do not summarise. Write everything the next stage and
the reviewer will need.}

---

## Stage Summary

{One paragraph (3-5 sentences) on what was accomplished, what was found,
and what the next stage is going to do.}

---

## Confidence Note

{One sentence: High / Medium / Low confidence, plus the primary reason.}
```

The reviewer agent depends on every section being present. If you skip the Confidence Note the reviewer will return REVISE on procedural grounds.

## 7. Domain Tagging

Set `domain` once at session start from your task template. Never change it mid-session. Each value carries a colour, a card glyph, and a filter pill in the dashboard.

| `domain` value | Use when... |
|---|---|
| `va-advisory` | VA benefits research, buddy letters, CFR citations, VR&E plans, claims strategy. Marcus's VetAssist platform work falls here. Example: "AGENT-02 drafts a buddy letter for a veteran's PTSD claim while AGENT-01 analyzes 38 C.F.R. Part 3, and AGENT-03 runs a SB 694 / OGC 2004 compliance check across both outputs." |
| `game-dev` | Unreal Engine 5 systems, gameplay loops, gameplay AI, level design, shader work, build verification. The Quidditch AI and IslandEscape projects live here. Example: "AGENT-01 designs the broom-physics flight loop, AGENT-02 implements the C++ component skeleton, AGENT-03 runs `Build.bat` and validates editor PIE on a clean checkout." |
| `software-eng` | Full-stack apps, REST/GraphQL APIs, databases, MCP integrations, Next.js / Python / Rust services that are not games. DevProductivityTracker, Bob, SentinelMail, AgentForge orchestration code. Example: "AGENT-01 builds the React form and Zustand store, AGENT-02 wires the FastAPI endpoint with Drizzle and Zod, AGENT-03 writes the Playwright e2e suite that exercises both sides." |
| `3d-content` | 3D modeling, rigging, texturing, Substance / Blender pipelines, UE5 asset import. Use this when the agent's output is a binary asset or a procedural recipe rather than code. Example: "AGENT-01 sculpts the broom mesh in Blender, AGENT-02 generates Substance materials, AGENT-03 imports both into UE5 and validates LODs and collision." |
| `general` | Documentation, research, planning, brainstorming, anything that does not fit a specific discipline above. Example: "AGENT-01 drafts the spec, AGENT-02 produces the diagram, AGENT-03 reviews both for consistency." |

The dashboard treats `domain` as informational, not behavioral. Two agents in the same run can carry different domains (and often should: a `software-eng` builder + a `qa-testing`-flavoured reviewer would both register as `software-eng` because the reviewer's discipline is the discipline being checked).

## 8. Parallel Agent Etiquette

Pulled directly from Marcus's CLAUDE.md DeepCommand parallel rules ("No overlapping file edits. Scoped ownership per agent. Merge only after validation."). The skill operationalizes them:

1. **Scoped ownership.** Each agent owns its `agent_id` row in `agents.json` and its `state/outputs/agent-{id}-stage-*.md` files. No agent reads or writes another agent's row except via the Section 2.2 upsert procedure (which only touches its own row).
2. **No overlapping edits to source files.** When agents share a workspace (a UE5 project, a Next.js repo), assign each agent a non-overlapping set of files in the task template. Two agents editing the same `.uasset` or the same component module is a merge conflict waiting to happen.
3. **Merge only after validation.** No agent merges another agent's output into a shared artifact (the final claim package, the integrated build) before that other agent reaches `status=complete` AND the operator approves its terminal gate. The merger agent (typically the last agent in the chain) polls for the predecessor's terminal stage output file and waits.
4. **One reviewer per gate, fresh context.** A reviewer agent never reuses a prior reviewer's context window. Each REVIEW BY AGENT spawns a fresh subprocess via `reviewer_spawner.py`. Do not cache reviewer state between gates.
5. **Never self-review.** An agent cannot review its own output. The reviewer is always a different model instance (Haiku, by `config.REVIEWER_MODEL`) spawned by the server, not the agent. If you are tempted to inline a self-check, write that as an extra stage and route it through a real REVIEW BY AGENT click.
6. **Surface dependencies up front.** If AGENT-03 needs AGENT-01's stage 4 output to begin its own stage 1, declare that in the task template's stage breakdown and have AGENT-03 write its initial state with `stage_label="Waiting for AGENT-01 stage 4 output"` and poll for the file. Do not silently block.

## 9. Context Window Tracking

Estimate `context_pct_used` at every state write (not only at stage transitions). Method:

- Assume a 200,000-token context window.
- Estimate tokens consumed: count approximate words in instructions, prior outputs, and tool results, then multiply by 1.33.
- `context_pct_used = round((estimated_tokens / 200000) * 100)`. Cap at 99 unless you are in a context-exhaustion error.

Behavior at thresholds:

- **80% threshold.** At the next natural stage boundary, set `status=waiting_approval`, `awaiting=ApprovalKind.PROCEED`, and `stage_label="Context at 80% - awaiting approval to continue"`. Do not advance without a fresh `proceed`.
- **Hard exhaustion.** Set `status=error`, `error_msg="ContextExhausted: Context limit reached at stage <N>. Resume from state/outputs/agent-{id}-stage-{N-1}.md"`. The operator will spawn a continuation agent seeded with that file.

## 10. Error Handling

On any error preventing forward progress:

1. Write `status=error`, `error_msg="<Type>: <one-sentence cause> at stage <N>"`. Examples: `"FileWriteError: agents.json path not accessible at stage 3"`, `"ToolError: WebSearch returned 503 at stage 2"`.
2. Do NOT increment `stage`.
3. Do NOT continue work.
4. Do NOT poll the approval queue. Errors require human diagnosis, not a queued decision.
5. Leave `awaiting=None`.

The operator will read your error_msg, fix the root cause, and either resume your session manually or spawn a continuation agent.

## 11. Session Start Checklist

Run this BEFORE any state write or any stage 1 work:

- [ ] Confirmed `agent_id` from the task template (format `AGENT-NN`).
- [ ] Confirmed `domain` from the task template (one of the five values in `AgentDomain`).
- [ ] Confirmed `total_stages` count from the task template.
- [ ] Confirmed `spawned_by` (null for top-level agents, parent `agent_id` for sub-agents).
- [ ] `config.STATE_DIR` exists and is writable (the server creates it on boot).
- [ ] `config.OUTPUTS_DIR` exists.
- [ ] `config.AGENTS_JSON` exists (the server seeds it as `[]` on boot if missing).
- [ ] `config.APPROVAL_QUEUE_JSON` exists (same; seeded as `[]`).
- [ ] FastAPI server is responding at `http://{config.SERVER_HOST}:{config.REST_PORT}/healthz` (the dashboard's startup hook should have ensured this; if not, stop and surface to the operator).

When the checklist passes, write your initial state entry through `state_store.upsert_agent` with `stage=1`, `status=active`, `awaiting=None`. Then begin stage 1.

## 12. Completion Protocol

When all stages finish successfully:

1. Write the final stage output file at `state/outputs/agent-{id}-stage-{total_stages}.md`.
2. Upsert your `AgentState` with `status=complete`, `stage=total_stages`, `progress_pct=100`, `awaiting=None`, `error_msg=None`, `output_ref="state/outputs/agent-{id}-stage-{total_stages}.md"`.
3. Stop polling. Do not delete your row from `agents.json`. The dashboard retains complete cards until the operator explicitly clears them via the post-session checklist in `tasks.md`.

## Cross-References

- `skills/_core/universal-coding-standards/SKILL.md`: every example here adheres to the no-magic-values, file-header, restrictive-access rules. Read it for the underlying conventions any of your work files must respect.
- `skills/_core/dev-workflow/SKILL.md`: brainstorm-first, research-before-code. A multi-agent run begins with a brainstorm artifact and a filled task template, not with `claude` commands.
- `skills/brainstorm-artifact/SKILL.md`: produce a brainstorm artifact for the mission BEFORE filling out `tasks/agentic-parallel/tasks.md`. The artifact tells you how many agents you need; the task template translates that into the gate map.
- `skills/meta/skill-creator/SKILL.md`: when a multi-agent run produces a new reusable workflow, hand off to skill-creator to package it as its own SKILL.md alongside this one.
- `skills/ai-agents/multi-agent-pipeline/SKILL.md`: the in-process Python framework for typed agent communication. Agentic-parallel is the cross-process / human-supervised cousin: file-based, dashboard-driven, gated. Use multi-agent-pipeline for unattended pipelines, agentic-parallel for supervised ones.
- `skills/ai-agents/session-recovery/SKILL.md`: when an agent hits ContextExhausted, that skill defines how the continuation agent reads the prior output file and resumes the row in `agents.json`.

## Anti-Patterns (NEVER Do)

- **Silent state writes.** Writing your stage output but not upserting `agents.json` means the dashboard never sees the transition. Every output file write MUST be paired with a state upsert.
- **Polling `agents.json` for cross-agent coordination.** The file watcher exists. If you need to react to another agent's status, ask the task template author to add an explicit dependency stage (with a stage label like "Waiting for AGENT-02 stage 3 output"). Do not poll `agents.json` from inside an agent.
- **Hardcoded ports or paths.** Reference `config.WEBSOCKET_PORT`, `config.AGENTS_JSON`, `config.OUTPUTS_DIR` symbolically. Literals in your code or your stage outputs become wrong the moment the port or path moves.
- **Self-review.** An agent never reviews its own output. Every reviewer pass goes through REVIEW BY AGENT (Haiku, fresh context). If you find yourself adding a "self-check stage", you are reinventing self-review and producing biased verdicts. Add a real reviewer gate instead.
- **Bypassing `state_store`.** Direct `json.dump` to `agents.json` skips the advisory lock and the temp-then-rename. Two agents racing through `json.dump` will corrupt the file. Use `state_store.upsert_agent` exclusively.
- **Inventing extra fields.** `AgentState` has `extra="forbid"`. New fields are dropped at validation; the dashboard never sees them. If you need new state, the change is a `models.py` migration, not an ad-hoc field.
- **Touching another agent's row.** Read-only access for cross-agent coordination is fine in narrow cases (a merger agent reading a predecessor's `output_ref`). Writing another agent's row is never fine.
- **Skipping the Session Start Checklist.** Writing state before the checklist passes leaves stale `[]` arrays and missing output directories. The checklist is two minutes; the recovery from a corrupted seed is an hour.
- **Letting `awaiting` go stale.** `awaiting` is the primary signal the dashboard uses to enable buttons. A `waiting_approval` row with `awaiting=null` produces a card with no buttons. Always set `awaiting` together with `status`.
