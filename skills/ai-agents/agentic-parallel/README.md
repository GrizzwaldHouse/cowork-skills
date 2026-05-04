# Agentic Parallel Skill

Behavioral protocol for Claude Code sub-agents that participate in a multi-agent parallel session supervised by the AgenticOS Command Center.

## What this is

`SKILL.md` in this folder is the protocol every sub-agent reads at the start of a multi-agent session. It defines the AgentState shape written to `C:\ClaudeSkills\AgenticOS\state\agents.json`, the cadence of state writes, the approval gate polling loop, the reviewer verdict handler, and the completion contract.

The skill is not user-invocable. Operators do not run it directly. They invoke it through a multi-agent session that is defined by `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md`.

## Folder layout

```
skills/ai-agents/agentic-parallel/
  SKILL.md       Canonical skill protocol (this folder)
  README.md      This file
  templates/     Per-session task template (TO BUILD, see tasks.md for now)
  examples/      Worked examples per domain (TO BUILD)
```

A second SKILL.md lives at `skills/agentic-parallel/SKILL.md`. That copy is the simpler Plan 5 verbatim version, written from `docs/superpowers/plans/2026-04-29-plan-5-skill-templates.md` on 2026-04-30. The canonical, evolved skill is the one in this folder. If the two diverge, the canonical here is the source of truth. Treat the Plan 5 copy as a historical reference only.

## When this applies

Use this skill when:
- A human operator has opened the AgenticOS Command Center before the session
- Your task template references this skill by path
- Your task assigns you an `agent_id` (format `AGENT-01`)
- Your task lists a fixed set of stages with explicit approval gates

If those conditions are not met, the skill does not apply. Do not write to `agents.json` for ad-hoc Claude Code sessions.

## How it fits with the rest of AgenticOS

| Surface | Role |
|---|---|
| `AgenticOS/agentic_server.py` | FastAPI state bus that watches `agents.json` and broadcasts diffs |
| `AgenticOS/dashboard/agentic_dashboard.py` | WPF tray launcher that hosts the React dashboard |
| `AgenticOS/frontend/` | React + Vite UI that renders one card per agent |
| `AgenticOS/models.py` | Canonical Pydantic shapes for AgentState and ApprovalQueueEntry |
| `AgenticOS/state_store.py` | Only sanctioned writer for agents.json and approval_queue.json |
| `skills/ai-agents/agentic-parallel/SKILL.md` | This skill, the contract every sub-agent obeys |
| `tasks/agentic-parallel/tasks.md` | Top-level operator checklist |

The dashboard is read-only on `agents.json` (only sub-agents write). The dashboard writes to `approval_queue.json` (sub-agents read and remove their entries).

## Operator quickstart

1. Launch AgenticOS Command Center: `pwsh C:\ClaudeSkills\launch_agentic_os.ps1`
2. Confirm the gold submarine icon is in the system tray
3. Open `C:\ClaudeSkills\tasks\agentic-parallel\tasks.md`, copy it to a session-specific filename, fill in mission and agents
4. Write the initial `agents.json` seed
5. For each agent, paste the per-agent prompt from the task template into a new Claude Code session
6. Watch the dashboard. Click PROCEED, RESEARCH MORE, or REVIEW BY AGENT when cards reach an approval gate

## Sub-agent quickstart

If you are a Claude sub-agent reading this README to orient yourself:

1. Read `SKILL.md` end-to-end before any other action
2. Confirm your `agent_id`, `domain`, `total_stages`, `spawned_by` from the prompt you were given
3. Run the Section 13 Session Start Checklist
4. Write your initial `agents.json` entry per Section 5 (upsert procedure)
5. Begin Stage 1
6. After every stage, write the output file before updating `agents.json`
7. Pause at every approval gate per Section 8

## Outstanding work in this folder

- `templates/task_template.md`. Per-session fill-in template. Use `tasks/agentic-parallel/tasks.md` as the source for now; fold into a templates file once the session contract has run end to end at least once.
- `examples/example_va_advisory_run.md`, `examples/example_game_dev_run.md`, `examples/example_software_eng_run.md`. Three worked sessions, one per primary domain. Plan 5 contains a fully filled-in VA advisory example that can seed the first file.

## See also

- `C:\ClaudeSkills\AgenticOS\README.md` for the FastAPI server contract
- `C:\ClaudeSkills\docs\superpowers\plans\2026-04-29-plan-5-skill-templates.md` for the plan that produced this skill
- `C:\ClaudeSkills\AgenticOS\models.py` for the canonical Pydantic shape
