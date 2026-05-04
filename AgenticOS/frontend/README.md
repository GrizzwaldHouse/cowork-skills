# AgenticOS Command Center // Frontend (Plan 3 scaffold)

React + Vite + TypeScript frontend for the AgenticOS Command Center. Renders a
gold-on-navy submarine instrument panel of live Claude Code sub-agents driven
by a FastAPI WebSocket state bus.

This directory is the Plan 3 scaffold. The Sonar HUD is intentionally a CSS
placeholder; Plan 4 wires up the Spline 3D scene without changing any other
file.

## Layout

```
frontend/
  package.json                # vite, react 18, typescript, vitest, RTL
  vite.config.ts              # ws/api proxy to FastAPI on 127.0.0.1:7842
  tsconfig.json               # strict + exactOptionalPropertyTypes
  tsconfig.node.json
  index.html
  src/
    main.tsx                  # React entry, imports global styles in order
    App.tsx                   # owns useAgentState + useApproval, renders grid
    config.ts                 # all URLs, ports, message types, thresholds
    types/
      agent.ts                # mirrors AgenticOS/models.py shapes
      messages.ts             # SnapshotMessage | DiffMessage union + guards
    hooks/
      useAgentState.ts        # WebSocket lifecycle, snapshot + diff merge
      useApproval.ts          # POST decisions, idempotency key, per-agent state
    components/
      AgentCard/              # instrument panel card composition
      StatusPill/             # status indicator pill
      ProgressBar/            # animated stage progress bar
      ContextMeter/           # context-window gauge with thresholds
      ApprovalButtons/        # PROCEED // RESEARCH MORE // REVIEW BY AGENT
      ReviewerPanel/          # collapsible reviewer verdict panel
      SonarHUD/               # placeholder; Plan 4 wires Spline here
    styles/
      tokens.css              # palette, spacing, radii, shadows, motion
      reset.css               # modern CSS reset
      typography.css          # Inter body, JetBrains Mono readouts
    utils/
      diffMerge.ts            # pure snapshot/diff -> AgentMap functions
      formatters.ts           # pure string + threshold helpers
  tests/
    setup.ts                  # vitest jest-dom matcher setup
    AgentCard.test.tsx
    ApprovalButtons.test.tsx
    useAgentState.test.ts
    diffMerge.test.ts
```

## Source-of-truth contracts

This frontend mirrors values from two backend modules. When those change, the
matching mirror here MUST change in the same commit.

| Backend module | Frontend mirror |
|----------------|-----------------|
| `AgenticOS/config.py` `WEBSOCKET_PORT` / `REST_PORT` | `src/config.ts` `FASTAPI_PORT` and `vite.config.ts` `FASTAPI_PORT` |
| `AgenticOS/config.py` `SERVER_HOST` | `src/config.ts` `FASTAPI_HOST` |
| `AgenticOS/config.py` `CORS_ORIGINS` | Vite dev port `5173` (already in CORS list) |
| `AgenticOS/models.py` `AgentStatus` | `src/types/agent.ts` `AgentStatus` |
| `AgenticOS/models.py` `AgentDomain` | `src/types/agent.ts` `AgentDomain` |
| `AgenticOS/models.py` `ApprovalKind` | `src/types/agent.ts` `ApprovalKind` |
| `AgenticOS/models.py` `AgentState` | `src/types/agent.ts` `AgentState` |
| `AgenticOS/models.py` `ApprovalDecision` | `src/types/agent.ts` `ApprovalPayload` |

## Development workflow

Run from `C:\ClaudeSkills\AgenticOS\frontend`.

```bash
# One-time: install dependencies (must be run before any other command).
npm install

# Type check. Strict mode + exactOptionalPropertyTypes; zero errors required.
npm run typecheck

# Run the full Vitest suite once. CI-style; exits non-zero on failure.
npm test

# Watch mode for iterative test runs.
npm run test:watch

# Dev server. Vite proxies /api and /ws to FastAPI on 127.0.0.1:7842.
npm run dev
```

The dev server binds `http://localhost:5173`. With FastAPI not running you
will see the header indicator stay on `CONNECTING` and the empty grid; the
hook keeps trying to connect with exponential backoff.

## Pointing the dev server at a non-default backend

The proxy targets in `vite.config.ts` are derived from a single `FASTAPI_PORT`
constant at the top of that file. If you run FastAPI on a different port,
update both that constant and `FASTAPI_PORT` in `src/config.ts` so both the
dev proxy and the production same-origin path stay in sync.

## Production build

```bash
# Compiles TypeScript and bundles into dist/. FastAPI serves dist/ at /app.
npm run build

# Sanity check the bundle locally on http://localhost:4173.
npm run preview
```

`AgenticOS/config.py` defines `FRONTEND_DIST_DIR = AGENTIC_DIR / "frontend"
/ "dist"` and `FRONTEND_MOUNT_PATH = "/app"`; both are read by the FastAPI
server when it mounts the static files.

## Testing notes

* Tests live under `tests/` and import from `@/...` aliases.
* `tests/setup.ts` registers `@testing-library/jest-dom/vitest` matchers
  (`toBeInTheDocument`, `toBeDisabled`, etc.) globally.
* `useAgentState.test.ts` stubs the global `WebSocket` and uses fake timers
  so reconnect backoff tests are deterministic.
* `diffMerge.test.ts` covers the pure utility functions and includes a
  same-reference assertion for the no-op diff short circuit.

## Plan 4 integration contract

Only `src/components/SonarHUD/SonarHUD.tsx` changes in Plan 4. The component
already lazy-imports `@splinetool/react-spline`; Plan 4 replaces the
placeholder body with `<Suspense><SplineLazy scene={...} /></Suspense>` and
binds the existing `progressPct`, `status`, and `agentId` props to the
Spline scene variables. No other file in this directory needs to change.
