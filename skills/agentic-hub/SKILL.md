---
name: agentic-hub
description: Connects any Claude Code project to the AgenticOS Universal Hub — enables multi-project monitoring, iPhone approval, Ollama handoff, and skill auto-loading.
version: 1.0.0
author: Marcus Daley
---

# AgenticOS Universal Hub Skill

## Purpose

Auto-connects a new Claude Code project to the AgenticOS Universal Hub running at C:/ClaudeSkills/AgenticOS. Once connected, Marcus can:

- See all active agents for this project in the React HUD
- Approve/review agents from his iPhone via Claude Desktop MCP
- Have Ollama automatically continue work when the Claude Code context resets
- Get skill packages auto-loaded into this project

## Quick Setup (3 steps)

### 1. Register this project

```bash
curl -X POST http://localhost:7842/projects/register \
  -H "Content-Type: application/json" \
  -d '{"path": "'$(pwd)'"}'
```

Or just create/edit CLAUDE.md — the project_watcher daemon registers it automatically within 5 seconds.

### 2. Set your phase hint

After each work session, record what Marcus needs to do next:

```bash
curl -X POST http://localhost:7842/projects/<PROJECT_ID>/phase \
  -H "Content-Type: application/json" \
  -d '{"hint": "Review the auth system changes in src/api/ then run tests"}'
```

### 3. Create a handoff snapshot before context limit

When Claude Code is approaching its context limit, call:

```bash
curl -X POST http://localhost:7842/handoff/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "MyProject",
    "project_path": "C:/Users/daley/Projects/MyProject",
    "plan_summary": "...",
    "completed_tasks": ["task 1", "task 2"],
    "pending_tasks": ["task 3", "task 4"],
    "context_notes": "...",
    "files_modified": ["src/api/auth.py"],
    "next_action": "Implement the token refresh endpoint"
  }'
```

Ollama will pick up the manifest and continue automatically.

## iPhone Access

1. Install Tailscale on PC + iPhone (free)
2. AgenticOS binds on 0.0.0.0:7842 — Tailscale handles the tunnel
3. In Claude Desktop: add mcp_config.json (from AgenticOS/mcp_config.json)
4. Ask Claude: "What do I need to do on [project]?" → get_phase() returns the answer

## Skill Auto-Loading

Add skill references to your CLAUDE.md like:
```
skills/universal-coding-standards/
skills/architecture-patterns/
```

The skill_loader will copy them into .claude/skills/ automatically.

## Ollama Handoff Loop

```
Claude Code writes manifest → Ollama continues work → Claude Code reviews
```

Start the runner manually:
```bash
python -m AgenticOS.handoff_runner
```

Or set OLLAMA_HANDOFF_MODEL in .env to configure which model runs.

## REST API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| /projects | GET | List all projects |
| /projects/active | GET | List active projects |
| /projects/register | POST | Register a project |
| /projects/{id}/phase | GET | What to do now |
| /projects/{id}/phase | POST | Set phase hint |
| /handoff | GET | Handoff manifest status |
| /handoff/snapshot | POST | Write handoff manifest |
| /agents | GET | All running agents |
| /approve/{id} | POST | Approve agent |
| /research/{id} | POST | Request more research |
| /review/{id} | POST | Trigger reviewer |
