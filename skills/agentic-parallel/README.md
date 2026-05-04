<!-- README.md -->
<!-- Developer: Marcus Daley -->
<!-- Date: 2026-04-30 -->
<!-- Purpose: Human-facing guide for the agentic-parallel skill -->

# Agentic Parallel — Operator Guide

## What this system does

The agentic-parallel skill lets you run multiple Claude Code agents in parallel, each working on a defined set of stages, while you supervise them through a single dashboard. Each agent reads a behavioral protocol (SKILL.md), writes its progress to a shared state file, and pauses at approval gates — checkpoints where you decide whether to proceed, request more research, or have a second AI agent review the work before continuing. The AgenticOS Command Center server watches the state file and pushes live updates to the dashboard so you can see every agent's status, progress, and context usage in real time without touching a terminal.

---

## Prerequisites

- AgenticOS server running (see How to Launch below)
- Dashboard open in a browser
- One terminal or Claude Code tab available per agent you plan to run
- Ollama is optional — the skill does not require it, but if you have local models running they can serve as reviewer agents when the dashboard spawns a REVIEW BY AGENT sub-session

---

## Quick Start

1. Copy `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md` to a session-specific file:
   `tasks/agentic-parallel/sessions/YYYY-MM-DD-your-mission-name.md`

2. Fill in every `FILL_IN` field in your copied file:
   - Section 1: date, goal, estimated duration
   - Section 2: one agent block per agent (agent_id, domain, task, stages, gate positions)
   - Section 3: success criteria you will check at the end
   - Section 4: the agents.json seed block

3. Write the Section 4 JSON block to `C:\ClaudeSkills\AgenticOS\state\agents.json`.

4. Start the server:
   ```
   pwsh C:\ClaudeSkills\launch_agentic_os.ps1
   ```
   Confirm the gold submarine icon appears in the system tray.

5. Open the dashboard in a browser at the URL shown in the tray launcher.
   Within 2 seconds of writing agents.json you should see one card per agent.

6. For each agent, open a new Claude Code session and paste that agent's Section 5 prompt block — nothing before it. The agent reads SKILL.md, runs its startup checklist, writes initial state, and begins Stage 1. Cards go live within about 30 seconds.

---

## What the Dashboard Shows

Each agent gets one card. Cards update in real time as agents write state.

| Element | What it means |
|---|---|
| Status pill | Current agent state: active (working), waiting_approval (at a gate), waiting_review (reviewer spawned), complete, error |
| Progress bar | Percentage through total stages, calculated as stage / total_stages |
| Context meter | Estimated percentage of the agent's context window consumed. At 80% the agent will pause automatically at the next stage boundary. |
| Stage line | Current stage number, total stages, and a short label describing what the agent is doing right now |
| Approval gate buttons | PROCEED / RESEARCH MORE / REVIEW BY AGENT — enabled only when the card shows waiting_approval |
| Reviewer panel | Expandable section showing the reviewer verdict (PASS / REVISE / REJECT) and notes, appears after a REVIEW BY AGENT cycle completes |

---

## Approval Gate Decisions

When a card reaches a gate, the status pill changes to waiting_approval and the three buttons activate. Before clicking, open the output file shown on the card and read the Work Output, Stage Summary, and Confidence Note.

**PROCEED**
The work looks good. The agent advances to the next stage and resumes immediately.

**RESEARCH MORE**
The output is incomplete or you need more information before the agent continues. The dashboard spawns a research sub-agent automatically. Your agent pauses and waits. When research is done, a proceed decision is sent to your agent automatically and it resumes.

**REVIEW BY AGENT**
You want a second opinion before deciding. The dashboard spawns a Haiku reviewer agent that reads the stage output and returns a one-line verdict plus 1-3 actionable notes. The verdict appears in the reviewer panel on the card. Then you make the final call:
- Verdict is PASS: click PROCEED, agent continues to next stage
- Verdict is REVISE: click PROCEED, agent redoes the current stage incorporating the reviewer notes, then re-enters the gate
- Verdict is REJECT: click PROCEED, agent re-approaches the current stage from a different angle per reviewer guidance, then re-enters the gate

---

## Context Window Handoff

Each agent tracks its own context usage and writes the estimate to the dashboard on every state update. When an agent hits 80% context, it pauses at the next natural stage boundary and sets its stage label to "Context at 80%, awaiting approval to continue". This appears on the card as a waiting_approval status.

When you see this:
1. Click PROCEED to spawn a continuation agent (or open a new session manually, seeded with the last stage output file as context)
2. The continuation agent picks up from the last completed stage output at `C:\ClaudeSkills\AgenticOS\state\outputs\agent-{id}-stage-{n}.md`
3. Give the continuation agent the same agent_id so the dashboard card stays coherent

If an agent exhausts context before it can pause cleanly, its card shows status: error with a message pointing to the last completed output file.

---

## Troubleshooting

**Server not running / tray icon missing**

Run `pwsh C:\ClaudeSkills\launch_agentic_os.ps1` from any terminal. If it fails, check that Python is on PATH and that no other process is using the configured REST or WebSocket port (see `AgenticOS/config.py`).

**WebSocket disconnected (dashboard shows stale data or spinner)**

Refresh the browser. The dashboard reconnects automatically and replays the current state snapshot. If it keeps disconnecting, restart the server and refresh.

**Agent card not appearing after pasting the launch prompt**

The agent must complete SKILL.md Section 13 (Session Start Checklist) and write its initial state entry before the card appears. This takes 20-40 seconds. If no card appears after 60 seconds:
- Check that `C:\ClaudeSkills\AgenticOS\state\agents.json` was seeded before launch
- Check the agent's terminal for errors reading SKILL.md or writing state
- Confirm `C:\ClaudeSkills\AgenticOS\state\outputs\` exists (agents create stage files there)
- Restart the agent with the same agent_id — the upsert is idempotent, no data is lost

**Approval buttons stay grayed out**

The agent's awaiting field is null even though status is waiting_approval. Send the agent a one-line corrective prompt: "Your awaiting field is null but status is waiting_approval — upsert with awaiting set to proceed." The buttons will activate on the next state write.

---

## See Also

- `C:\ClaudeSkills\skills\agentic-parallel\SKILL.md` — the protocol every sub-agent reads
- `C:\ClaudeSkills\AgenticOS\README.md` — server endpoints and WebSocket frame format
- `C:\ClaudeSkills\AgenticOS\models.py` — canonical AgentState field definitions
- `tasks/agentic-parallel/sessions/` — your saved session files (created as you run missions)
