# AgenticOS Command Center — Design Spec
**Date:** 2026-04-29
**Author:** Marcus Daley
**Status:** Approved — ready for implementation planning
**Project:** C:\ClaudeSkills

---

## 1. Problem Statement

Claude Code sub-agents doing parallel work are invisible. There is no way to:
- See which stage each agent is in without reading terminal output
- Approve or gate an agent's next action without typing a prompt
- Spawn a reviewer agent for a specific agent's output without losing context
- Reuse this supervision pattern across domains (VA advisory, game dev, software engineering)

The AgenticOS Command Center solves all four problems with a persistent Windows GUI that any user — technical or not — can operate.

---

## 2. Scope

This spec covers **Option B**: a new standalone AgenticOS Command Center window that coexists with the existing OWL Watcher file security monitor. OWL Watcher is not modified. Both share the same gold-on-navy submarine/Harry Potter design language.

Out of scope for this version:
- Merging OWL Watcher and the Command Center into a single unified app (Option C — future)
- Remote/cloud agent support (all agents are local Claude Code sub-agents)
- Multi-user / networked dashboards

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────┐
│           AgenticOS Command Center (WPF)            │
│  ┌─────────────────────────────────────────────┐   │
│  │  WebView2 (React + Vite + Spline 3D)        │   │
│  │  Sonar HUD background · Agent Cards overlay │   │
│  └──────────────────┬──────────────────────────┘   │
│  System Tray Icon   │ WebSocket ws://localhost:7842 │
└─────────────────────┼───────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │   FastAPI State Bus     │
         │   agentic_server.py     │
         │   ws + REST endpoints   │
         └────┬──────────┬─────────┘
              │          │
   ┌──────────▼───┐  ┌───▼──────────────┐
   │ state/        │  │ state/            │
   │ agents.json   │  │ approval_queue    │
   │ (live state)  │  │ .json (pending)   │
   └──────────┬────┘  └──────────────────┘
              │
   ┌──────────▼──────────────────────────┐
   │     Claude Sub-Agents               │
   │  write state via skill protocol     │
   │  read approval_queue for gates      │
   └──────────┬──────────────────────────┘
              │
   ┌──────────▼──────────────────────────┐
   │     OWL Watcher (unchanged)         │
   │     file security monitor           │
   └─────────────────────────────────────┘
```

### Communication flow

1. Sub-agent writes its state to `state/agents.json` at every stage transition
2. FastAPI server (watchdog) detects the file change and broadcasts a WebSocket diff to all connected clients
3. React UI receives the diff and updates the relevant agent card
4. User clicks an approval button — React POSTs to FastAPI REST endpoint
5. FastAPI writes the decision to `state/approval_queue.json`
6. The waiting agent polls `approval_queue.json` and reads its gate decision
7. If "REVIEW BY AGENT" — FastAPI spawns a reviewer subprocess via Claude CLI with a fresh context window; reviewer writes its verdict to `state/outputs/agent-{id}-review.md`

---

## 4. Component Breakdown

### 4.1 `agentic_server.py` — FastAPI State Bus

- FastAPI application with WebSocket endpoint at `ws://localhost:7842/ws`
- REST endpoints: `POST /approve/{agent_id}`, `POST /research/{agent_id}`, `POST /review/{agent_id}`
- Watchdog file watcher on `state/agents.json` — broadcasts diffs on change
- Reviewer agent spawner: `subprocess` call to Claude CLI with isolated context
- CORS configured for localhost React dev server and production build
- Fully commented, typed with Pydantic models for all state shapes

### 4.2 `agentic_dashboard.py` — WPF System Tray Launcher

- Launches `agentic_server.py` as a managed subprocess on startup
- Creates a WPF Window hosting a WebView2 control pointed at `localhost:7842/app`
- System tray icon (gold submarine silhouette, `.ico`) — right-click menu: Show, Hide, Quit
- Auto-launches on Windows startup via registry key (optional, user-configurable)
- Falls back to console if WebView2 runtime not installed (with install prompt)
- Fully commented with startup sequence documented

### 4.3 `agentic_dashboard.xaml` — WPF Window Chrome

- Thin chrome only: title bar, window border, tray icon wiring
- Interior is 100% WebView2 — no WPF widgets inside content area
- Gold border (`#C9A94E`) on deep navy (`#1B2838`) — matches OWL Watcher palette exactly
- `WindowStyle="None"` with custom chrome for borderless modern look
- Resizable with minimum dimensions (800×600)

### 4.4 `frontend/` — React + Vite + Spline 3D

**Directory structure:**
```
frontend/
  src/
    components/
      AgentCard.tsx          # Instrument panel card per agent
      SonarHUD.tsx           # Spline scene wrapper + variable bindings
      ApprovalButtons.tsx    # PROCEED / RESEARCH MORE / REVIEW BY AGENT
      ContextMeter.tsx       # Context window % gauge
      ReviewerPanel.tsx      # Reviewer agent verdict display
    hooks/
      useAgentState.ts       # WebSocket connection + state management
      useApproval.ts         # POST approval decisions to FastAPI
    types/
      agent.ts               # AgentState, ApprovalDecision TypeScript types
    App.tsx
    main.tsx
  public/
    spline/
      sonar-hud.splinecode   # Self-hosted Spline scene (no CORS issues)
  index.html
  vite.config.ts
  package.json
```

**Spline scene variables (bound to agent state):**
| Variable name | Type | Maps to |
|---|---|---|
| `agent_{n}_progress` | number (0–100) | depth gauge needle angle |
| `agent_{n}_state` | string | sonar ring pulse rate |
| `agent_{n}_active` | boolean | instrument panel glow |
| `global_agent_count` | number | sonar screen active contacts |

**Agent states → Spline visual mapping:**
| State | Sonar ring | Depth gauge | Panel glow |
|---|---|---|---|
| `active` | Fast pulse | Filling | Bright gold |
| `waiting_approval` | Slow pulse | Paused | Amber |
| `waiting_review` | Double pulse | Paused | Teal |
| `complete` | Solid ring | Full | Dim green |
| `error` | Rapid flash | Frozen | Red |

### 4.5 `skills/agentic-parallel/SKILL.md` — Reusable Skill

The protocol skill that any multi-agent workflow invokes. Defines:
- Agent state-writing contract (what JSON to write and when)
- Stage transition rules (when to write, what fields are required)
- Approval gate protocol (how to poll and parse `approval_queue.json`)
- Reviewer spawn instructions (what context to pass, what format to write verdict in)
- Domain tagging (`va-advisory | game-dev | software-eng | general`)

### 4.6 `tasks/agentic-parallel/tasks.md` — Reusable Task Template

Fill-in scaffold for any multi-agent task:
- Define N agents, their domain, their stages
- Import the skill
- The Command Center auto-discovers them from `agents.json`

---

## 5. Agent State Contract

Every sub-agent writes this shape to `state/agents.json` (array, one entry per agent) at every stage transition:

```json
{
  "agent_id": "AGENT-01",
  "domain": "va-advisory | game-dev | software-eng | general",
  "task": "Human-readable description of what this agent is doing",
  "stage_label": "Analyzing CFR Title 38 Part 3",
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

---

## 6. Agent Instrument Panel Card UI

```
┌──────────────────────────────────────────────────────┐
│  AGENT-01  [VA-ADVISORY]              ● ACTIVE       │
│  ────────────────────────────────────────────────── │
│  Stage 2/5 · Analyzing CFR Title 38 Part 3           │
│                                                      │
│        [ Spline 3D: sonar ring + depth gauge ]       │
│                                                      │
│   ████████████░░░░░░░░░░░░░░  64%                   │
│                                                      │
│   ┌────────────┐ ┌─────────────┐ ┌───────────────┐  │
│   │  PROCEED   │ │ RESEARCH    │ │ REVIEW BY     │  │
│   │            │ │   MORE      │ │   AGENT       │  │
│   └────────────┘ └─────────────┘ └───────────────┘  │
│                                                      │
│   Context: 34% used  ·  Est. 2 min remaining         │
└──────────────────────────────────────────────────────┘
```

**Button behavior:**
- **PROCEED** — posts `{decision: "proceed"}` to `/approve/AGENT-01`; button row disables until next approval gate
- **RESEARCH MORE** — posts `{decision: "research"}`; spawns sub-research agent; card shows "Awaiting research sub-agent..." with its own mini progress indicator
- **REVIEW BY AGENT** — posts `{decision: "review"}`; spawns independent reviewer agent with fresh context; reviewer verdict appears in an expandable panel below the buttons before PROCEED becomes available again

---

## 7. Approval Gate Protocol

When an agent reaches a gate point, it:
1. Sets `status: "waiting_approval"` and `awaiting: "proceed"` in `agents.json`
2. Polls `state/approval_queue.json` every 2 seconds for its `agent_id`
3. On finding its decision, reads it, clears its entry from the queue, and continues

`approval_queue.json` shape:
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

---

## 8. Reviewer Agent Pattern

When "REVIEW BY AGENT" is selected:
1. FastAPI reads the agent's `output_ref` file
2. Spawns a new Claude CLI subprocess: `claude --model claude-haiku-4-5-20251001 --print "Review the following work output for correctness, completeness, and bias. Output a structured verdict: PASS | REVISE | REJECT with specific notes. Work output: [content]"`
3. Haiku is used for reviewer agents to keep context cost low and avoid bias from the same model instance
4. Reviewer writes verdict to `state/outputs/agent-{id}-review.md`
5. FastAPI detects the file and broadcasts reviewer verdict via WebSocket
6. Card expands to show verdict; PROCEED button re-enables only after user reads it

---

## 9. System Tray Behavior

- Gold submarine icon in Windows system tray at all times when running
- Single click: show/hide window
- Right-click menu: Show Window | Hide Window | View Logs | Quit
- Window remembers position and size between sessions (saved to `state/window_prefs.json`)
- No slash command needed — the app is always running in tray

---

## 10. Auto-Launch on Windows Startup

- Registry key: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run\AgenticOS`
- Value: path to `agentic_dashboard.py` via `pythonw.exe` (no console window)
- Toggled via right-click tray menu option: "Start with Windows"
- Default: ON after first install

---

## 11. Scalability: Domain Expansion

The system is domain-agnostic by design. Adding a new discipline requires:
1. Adding a new domain tag to the `domain` enum in `agent.ts` and `agentic_server.py`
2. Adding domain-specific color accent (optional) to the React theme config
3. No changes to the state bus, WPF layer, or Spline scene

Planned domains: `va-advisory`, `game-dev`, `software-eng`, `3d-content`, `general`

---

## 12. Technology Stack

| Layer | Technology | Reason |
|---|---|---|
| Windows host | WPF + pythonnet | Matches OWL Watcher; native Windows system tray |
| Browser runtime | Microsoft WebView2 | Modern Chromium, ships with Windows 11 |
| State bus | FastAPI + WebSocket | Async, typed, lightweight |
| File watching | watchdog | Same library as OWL Watcher |
| Frontend | React 18 + Vite | Fast dev cycle, TypeScript, component model |
| 3D visuals | Spline 3D (react-spline) | Self-hosted `.splinecode`, no CORS, offline-capable |
| Reviewer agents | Claude Haiku 4.5 | Fast, cheap, different model instance = unbiased review |
| State format | JSON files | Human-readable, git-trackable, no DB dependency |

---

## 13. File Layout in C:\ClaudeSkills

```
C:\ClaudeSkills\
  AgenticOS\
    agentic_dashboard.py        # WPF launcher + system tray
    agentic_dashboard.xaml      # WPF chrome (title bar, border)
    agentic_server.py           # FastAPI state bus + WebSocket
    state\
      agents.json               # Live agent state (written by agents)
      approval_queue.json       # Pending approval decisions
      window_prefs.json         # Window size/position memory
      outputs\                  # Agent output files + reviewer verdicts
    frontend\                   # React + Vite app
      src\
      public\spline\            # Self-hosted Spline scene
      dist\                     # Built frontend (served by FastAPI)
    assets\
      tray-icon.ico             # Gold submarine system tray icon
  skills\
    agentic-parallel\
      SKILL.md                  # Reusable multi-agent protocol skill
  tasks\
    agentic-parallel\
      tasks.md                  # Fill-in task template
  docs\
    superpowers\
      specs\
        2026-04-29-agentic-os-command-center-design.md  # This file
```

---

## 14. Coding Standards (Marcus Daley Universal Standards)

- File header on every file: filename, developer, date, purpose
- Single-line comments on every function and non-obvious line (`//` in JS/TS, `#` in Python)
- Zero hardcoded values — all ports, paths, timeouts in a central `config.py` / `config.ts`
- Zero magic numbers/strings — named constants only
- Most restrictive access by default
- Written to scale: no shortcuts, no MVP-only hacks, no untracked TODOs
- All Python typed with type hints; all TypeScript strict mode

---

## 15. Self-Review Checklist

- [x] No TBDs or incomplete sections
- [x] Architecture diagram matches component descriptions
- [x] State contract is fully specified (all fields, all statuses)
- [x] Approval gate protocol is unambiguous
- [x] Reviewer agent pattern is scoped (Haiku, not Sonnet, to control cost)
- [x] File layout matches every component described
- [x] Coding standards explicitly stated
- [x] OWL Watcher is fully isolated — zero modifications required
- [x] Spline variable names are concrete and match React component usage
- [x] Domain expansion path is clear and requires minimal changes
