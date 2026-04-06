# AgentForge Phase Registry

All 8 development phases with detection heuristics, objectives, and completion criteria.

---

## Phase 1: Foundation

| Field | Value |
|-------|-------|
| **Status** | COMPLETE |
| **Commit Pattern** | `Phase 1` or `Foundation` |
| **Detection** | `src/core/interfaces/Agent.ts` exists with `Agent`, `AgentInput`, `AgentOutput` interfaces |
| **Objective** | Core interfaces, entity types, project scaffolding |
| **Key Files** | `src/core/interfaces/Agent.ts`, `src/core/entities/Task.ts`, `src/lib/constants.ts`, `src/lib/format.ts`, `src/lib/cn.ts` |
| **Completion Criteria** | Agent interface defined, Task entity defined, path aliases working, TypeScript compiles |
| **Dependencies** | None |

### What Was Built
- `Agent` interface: `{ id, name, execute(input: AgentInput): Promise<AgentOutput> }`
- `AgentInput`: `{ taskId, context }`
- `AgentOutput`: `{ success, data?, logs[] }`
- `Task` entity with lifecycle states
- Utility functions (cn, format, constants)
- Next.js 15 + React 19 + Tailwind CSS 4 scaffold

---

## Phase 2: Event System

| Field | Value |
|-------|-------|
| **Status** | COMPLETE |
| **Commit Pattern** | `Phase 2` or `Event System` |
| **Detection** | `src/core/events/agent-event-bus.ts` exists with `AgentEventBus` class |
| **Objective** | Typed event bus for inter-agent communication |
| **Key Files** | `src/core/events/agent-event-bus.ts`, `src/core/events/types.ts`, `src/core/events/__tests__/agent-event-bus.test.ts` |
| **Completion Criteria** | EventBus emits/subscribes typed events, tests pass, SSE endpoint exists |
| **Dependencies** | Phase 1 |

### What Was Built
- `AgentEventBus` — singleton typed event bus
- Event types: `agent:start`, `agent:complete`, `agent:error`, `task:update`
- SSE endpoint at `/api/agent/events`
- React hook `useAgentEvents` for real-time UI updates
- Full test coverage for event bus

---

## Phase 3: Observable Execution

| Field | Value |
|-------|-------|
| **Status** | COMPLETE |
| **Commit Pattern** | `Phase 3` or `Observable execution` |
| **Detection** | `src/core/observability/trace.ts` exists, `src/backend/execution/ExecutionBackend.ts` exists |
| **Objective** | Execution backends (simulated + Ollama) with tracing and observability |
| **Key Files** | `src/backend/execution/ExecutionBackend.ts`, `src/backend/execution/SimulatedBackend.ts`, `src/backend/execution/OllamaBackend.ts`, `src/core/observability/trace.ts`, `src/core/observability/logger.ts`, `src/core/observability/event-middleware.ts`, `src/backend/services/ObservableOrchestrator.ts` |
| **Completion Criteria** | SimulatedBackend passes tests, OllamaBackend scaffolded, tracing infrastructure works, ObservableOrchestrator integrates events + execution |
| **Dependencies** | Phase 2 |

### What Was Built
- `ExecutionBackend` abstract class with `execute()` contract
- `SimulatedBackend` — deterministic test backend with configurable delays/failures
- `OllamaBackend` — skeleton for local LLM integration
- Tracing: `Span`, `Trace` classes for execution profiling
- `Logger` — structured logging with levels
- `EventMiddleware` — bridges execution events to the event bus
- `ObservableOrchestrator` — orchestrator that emits events during execution
- Full test suites for all components

---

## Phase 4: Dashboard UI

| Field | Value |
|-------|-------|
| **Status** | NOT STARTED |
| **Commit Pattern** | `Phase 4` or `Dashboard` |
| **Detection** | `src/app/dashboard/page.tsx` exists with agent status cards |
| **Objective** | Real-time dashboard showing agent status, task progress, and event stream |
| **Key Files** | `src/app/dashboard/page.tsx`, `src/app/dashboard/layout.tsx`, `src/components/agent-card.tsx`, `src/components/task-list.tsx`, `src/components/event-stream.tsx` |
| **Completion Criteria** | Dashboard renders agent cards, task list updates via SSE, event stream shows real-time events, responsive layout, TypeScript compiles, `npm run build` succeeds |
| **Dependencies** | Phase 3 |

### Specification
- **Agent Cards**: One card per agent showing name, status (idle/running/error), last execution time
- **Task List**: Shows tasks with status badges (PENDING/IN_PROGRESS/REVIEW/DONE/BLOCKED)
- **Event Stream**: Scrolling log of real-time events from SSE endpoint
- **Layout**: Sidebar navigation + main content area
- **Styling**: Tailwind CSS 4 + Radix UI components + Framer Motion transitions
- **Data Source**: `useAgentEvents` hook for SSE, API routes for initial data
- **Components to create**:
  - `AgentCard` — Radix Card with status indicator, agent name, metrics
  - `TaskListPanel` — filterable list of tasks with status badges
  - `EventStream` — auto-scrolling event log with type-based coloring
  - `DashboardHeader` — title, connection status indicator, refresh button

---

## Phase 5: Real Agent Implementations

| Field | Value |
|-------|-------|
| **Status** | NOT STARTED |
| **Commit Pattern** | `Phase 5` or `Real agents` |
| **Detection** | `src/agents/planner/PlannerAgent.ts` contains prompt construction and LLM call logic (not just a stub) |
| **Objective** | Replace agent stubs with real implementations that call LLMs via ExecutionBackend |
| **Key Files** | `src/agents/planner/PlannerAgent.ts`, `src/agents/builder/BuilderAgent.ts`, `src/agents/reviewer/ReviewerAgent.ts`, `src/agents/tester/TesterAgent.ts`, `src/agents/learning/LearningAgent.ts`, `src/agents/context/ContextManagerAgent.ts`, `src/agents/registry.ts` |
| **Completion Criteria** | Each agent constructs proper prompts, calls ExecutionBackend, parses responses, emits events, handles errors. Tests verify prompt construction and response parsing. |
| **Dependencies** | Phase 3 |

### Specification
- Each agent implements the `Agent` interface from Phase 1
- Agents construct task-specific prompts with system instructions
- `PlannerAgent` — takes a task description, produces step-by-step implementation plan
- `BuilderAgent` — takes a plan, produces code implementations
- `ReviewerAgent` — takes code, produces review with issues/suggestions
- `TesterAgent` — takes code, produces test cases
- `LearningAgent` — observes all outputs, extracts patterns, updates LEARNING.md
- `ContextManagerAgent` — manages context window, prunes old data
- All agents emit events via `AgentEventBus` during execution
- Agent registry maps agent IDs to instances

---

## Phase 6: Ollama Integration

| Field | Value |
|-------|-------|
| **Status** | NOT STARTED |
| **Commit Pattern** | `Phase 6` or `Ollama` |
| **Detection** | `src/backend/execution/OllamaBackend.ts` contains `fetch('http://127.0.0.1:11434/api/generate')` or equivalent |
| **Objective** | Connect OllamaBackend to local Ollama instance for real LLM inference |
| **Key Files** | `src/backend/execution/OllamaBackend.ts`, `src/backend/services/ModelService.ts`, `src/lib/constants.ts` |
| **Completion Criteria** | OllamaBackend sends prompts to Ollama API, streams responses, handles timeouts/errors, ModelService detects available models. Integration test passes with mock server. |
| **Dependencies** | Phase 3 |

### Specification
- Ollama API endpoint: `http://127.0.0.1:11434`
- Endpoints: `/api/generate` (completion), `/api/chat` (chat), `/api/tags` (model list)
- Support streaming responses with progress events
- Model selection: use `ModelService.detectModels()` → pick best for task type
- Default model priority: `llama3.3:70b` → `glm-4.7-flash` → `llama3:8b`
- Timeout: 60s for generation, 5s for health check
- Error handling: connection refused → clear error message, model not found → list available
- Mock server for tests (do not require running Ollama for test suite)

---

## Phase 7: Pipeline Orchestration

| Field | Value |
|-------|-------|
| **Status** | NOT STARTED |
| **Commit Pattern** | `Phase 7` or `Orchestrator` |
| **Detection** | `src/backend/services/AgentOrchestrator.ts` contains sequential pipeline logic (Plan → Build → Review → Test) |
| **Objective** | Wire agents into the full execution pipeline with proper sequencing and error handling |
| **Key Files** | `src/backend/services/AgentOrchestrator.ts`, `src/backend/services/ObservableOrchestrator.ts`, `src/app/api/agent/run/route.ts` |
| **Completion Criteria** | Pipeline executes Plan → Build → Review → Test sequence, passes output between stages, handles failures at each stage, API route triggers pipeline runs. Tests verify full pipeline with SimulatedBackend. |
| **Dependencies** | Phase 5 |

### Specification
- Pipeline stages: `PLAN → BUILD → REVIEW → TEST → DONE`
- Each stage receives output from previous stage as input context
- If REVIEW finds critical issues → loop back to BUILD (max 2 retries)
- If TEST fails → loop back to BUILD with failure context (max 2 retries)
- Pipeline emits events at each stage transition
- API route `/api/agent/run` accepts task description, returns pipeline result
- Observable: all stages emit traces via observability infrastructure
- Configurable: allow skipping stages or running subset

---

## Phase 8: Polish and Documentation

| Field | Value |
|-------|-------|
| **Status** | NOT STARTED |
| **Commit Pattern** | `Phase 8` or `Polish` |
| **Detection** | `README.md` contains usage documentation, `src/app/page.tsx` has landing content |
| **Objective** | Production readiness — error boundaries, loading states, documentation, CI |
| **Key Files** | `README.md`, `src/app/page.tsx`, `src/app/layout.tsx`, `src/app/error.tsx`, `src/app/loading.tsx`, `.github/workflows/ci.yml` |
| **Completion Criteria** | Landing page links to dashboard, error boundaries catch React errors, loading states on all async components, README has setup/usage/architecture docs, CI runs build + test. |
| **Dependencies** | Phase 4, Phase 7 |

### Specification
- Landing page (`/`) with project overview and link to dashboard
- Error boundary component wrapping dashboard
- Loading skeletons for agent cards and task list
- README sections: Overview, Setup, Usage, Architecture, Development
- CI workflow: checkout → install → build → test → lint
- Verify all pages render without errors
- Verify no TypeScript errors (`npx tsc --noEmit`)
- Verify no ESLint errors (`npx next lint`)
