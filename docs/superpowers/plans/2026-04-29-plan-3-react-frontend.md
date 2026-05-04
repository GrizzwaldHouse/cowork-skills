# Plan 3 of 5 — React + Vite Frontend
**Project:** AgenticOS Command Center
**Author:** Marcus Daley
**Date:** 2026-04-29
**Status:** Ready for implementation

---

## Goal

Build the React + Vite frontend that renders the AgenticOS Command Center UI inside the FastAPI-served WebView2 window. The frontend connects to `ws://localhost:7842/ws` for live agent state, posts approval decisions to the FastAPI REST endpoints, and renders one instrument-panel card per agent in a submarine/tactical design language.

---

## Architecture

```
App.tsx  (WebSocket owner — single connection, passes agents[] down)
  └── AgentCard  (one per agent in agents[])
        ├── StatusBadge       (● ACTIVE / ● WAITING / ● COMPLETE)
        ├── SonarHUD          (Spline placeholder — wired in Plan 4)
        ├── ContextMeter      (context_pct_used gauge bar)
        ├── ApprovalButtons   (PROCEED / RESEARCH MORE / REVIEW BY AGENT)
        └── ReviewerPanel     (expandable — visible only when reviewer_verdict != null)

Hooks (pure logic, zero JSX):
  useAgentState  →  WebSocket, auto-reconnect, agents[] state
  useApproval    →  POST to /approve | /research | /review, per-agent loading/error
```

Data flows one direction: WebSocket → `useAgentState` → `App.tsx` → props → cards. Approval decisions flow back via `useApproval` HTTP POST — no shared mutable state between cards.

---

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| Build tool | Vite 5 | Fast HMR, native ESM, minimal config |
| Framework | React 18 | Hooks, concurrent features, RTL ecosystem |
| Language | TypeScript 5 (strict) | Required by coding standards |
| 3D layer | `@splinetool/react-spline` | Spline scene wired in Plan 4 — import included now |
| Tests | Vitest + React Testing Library | Vite-native, Jest-compatible API |
| CSS | Plain CSS Modules per component | No extra runtime; matches file-per-component pattern |
| Proxy | Vite `server.proxy` | Forwards `/api` and `/ws` to `localhost:7842` in dev |

---

## Non-Negotiable Standards

Every file must open with:
```ts
// filename.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: <one sentence>
```

- `//` comments on every non-obvious line and every function/component
- Zero hardcoded values — every URL, port, color, timeout lives in `src/config.ts`
- TypeScript strict mode — no `any`, no `!` non-null assertions without comment
- Named constants only — no magic numbers or strings inline
- Most restrictive access by design — no exported mutable module-level state

---

## Exact File Structure

```
C:\ClaudeSkills\AgenticOS\frontend\
  src\
    config.ts
    types\
      agent.ts
    hooks\
      useAgentState.ts
      useApproval.ts
    components\
      AgentCard\
        AgentCard.tsx
        AgentCard.css
      ApprovalButtons\
        ApprovalButtons.tsx
        ApprovalButtons.css
      ContextMeter\
        ContextMeter.tsx
        ContextMeter.css
      ReviewerPanel\
        ReviewerPanel.tsx
        ReviewerPanel.css
      StatusBadge\
        StatusBadge.tsx
        StatusBadge.css
      SonarHUD\
        SonarHUD.tsx
        SonarHUD.css
    App.tsx
    App.css
    main.tsx
  public\
    spline\               (empty — Spline scene added in Plan 4)
  index.html
  vite.config.ts
  tsconfig.json
  package.json

C:\ClaudeSkills\tests\AgenticOS\frontend\
  AgentCard.test.tsx
  useAgentState.test.ts
  useApproval.test.ts
```

---

## Commands

```bash
# From C:\ClaudeSkills\AgenticOS\frontend\

npm install              # install all dependencies
npm run dev              # Vite dev server at http://localhost:5173 (proxied to :7842)
npm run build            # production build → dist/ (FastAPI serves this)
npm run preview          # preview production build locally
npm test                 # vitest run (all tests, single pass)
npm run test:watch       # vitest watch mode during development
npm run typecheck        # tsc --noEmit (strict, no build output)
npm run lint             # eslint src/ --ext .ts,.tsx
```

---

## Step-by-Step Implementation

Each step is 2–5 minutes of focused work. Commit after every step.

---

### STEP 1 — Scaffold: `package.json`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\package.json`

```json
{
  "name": "agenticos-command-center-frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/ --ext .ts,.tsx"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@splinetool/react-spline": "^2.2.6",
    "@splinetool/runtime": "^0.9.490"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.4.5",
    "vite": "^5.2.12",
    "vitest": "^1.6.0",
    "@vitest/coverage-v8": "^1.6.0",
    "jsdom": "^24.1.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "@testing-library/jest-dom": "^6.4.6",
    "eslint": "^8.57.0",
    "@typescript-eslint/eslint-plugin": "^7.11.0",
    "@typescript-eslint/parser": "^7.11.0",
    "eslint-plugin-react-hooks": "^4.6.2",
    "eslint-plugin-react-refresh": "^0.4.7"
  }
}
```

**Commit:** `scaffold: add package.json for AgenticOS frontend`

---

### STEP 2 — TypeScript Config: `tsconfig.json`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src", "tests"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\tsconfig.node.json`

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

**Commit:** `scaffold: add tsconfig.json (strict mode, path aliases)`

---

### STEP 3 — Vite Config: `vite.config.ts`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\vite.config.ts`

```ts
// vite.config.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Vite build config — proxies /api and /ws to FastAPI at localhost:7842

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// FastAPI runs on this port — must match agentic_server.py SERVER_PORT
const FASTAPI_PORT = 7842;
const FASTAPI_BASE = `http://localhost:${FASTAPI_PORT}`;
const FASTAPI_WS   = `ws://localhost:${FASTAPI_PORT}`;

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      // @ maps to src/ — keeps imports clean across deep component trees
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    proxy: {
      // Proxy all REST calls (/approve, /research, /review) to FastAPI
      '/api': {
        target: FASTAPI_BASE,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
      // Proxy WebSocket connection to FastAPI ws endpoint
      '/ws': {
        target: FASTAPI_WS,
        ws: true,
        changeOrigin: true,
      },
    },
  },

  build: {
    // Output to dist/ — FastAPI serves this directory at /app
    outDir: 'dist',
    emptyOutDir: true,
  },

  test: {
    // Vitest config — jsdom simulates browser APIs for hook and component tests
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
    },
  },
});
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\test-setup.ts`

```ts
// test-setup.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Vitest global setup — imports jest-dom matchers for all tests

import '@testing-library/jest-dom';
```

**Commit:** `scaffold: add vite.config.ts with FastAPI proxy and vitest config`

---

### STEP 4 — Entry Point: `index.html` and `main.tsx`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AgenticOS Command Center</title>
    <!-- Favicon can be replaced with gold submarine .ico in Plan 4 -->
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
  </head>
  <body>
    <!-- Root mount point for React — styled by App.css -->
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\main.tsx`

```tsx
// main.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: React application entry point — mounts App into #root

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

// Locate the mount point — throw early if HTML is malformed rather than silent failure
const rootElement = document.getElementById('root');
if (rootElement === null) {
  throw new Error('Root element #root not found — check index.html');
}

ReactDOM.createRoot(rootElement).render(
  // StrictMode intentionally enabled — surfaces double-invoke issues during dev
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**Commit:** `scaffold: add index.html and main.tsx entry point`

---

### STEP 5 — Central Config: `src/config.ts`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\config.ts`

```ts
// config.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Single source of truth for all URLs, ports, timeouts, and theme values.
//          Nothing is hardcoded elsewhere in the frontend — all values import from here.

// ─── Server endpoints ────────────────────────────────────────────────────────

// WebSocket URL — FastAPI broadcasts agent state changes here
export const WS_URL = 'ws://localhost:7842/ws';

// REST base URL — approval decisions POST to sub-paths of this
export const API_BASE = 'http://localhost:7842';

// REST endpoint paths — combined with API_BASE + agent_id at call sites
export const ENDPOINTS = {
  approve:  (agentId: string) => `${API_BASE}/approve/${agentId}`,
  research: (agentId: string) => `${API_BASE}/research/${agentId}`,
  review:   (agentId: string) => `${API_BASE}/review/${agentId}`,
} as const;

// ─── WebSocket reconnect policy ──────────────────────────────────────────────

// Initial delay before first reconnect attempt (ms)
export const WS_RECONNECT_BASE_MS = 1_000;

// Reconnect delay doubles on each failed attempt — capped at this value (ms)
export const WS_RECONNECT_MAX_MS = 30_000;

// ─── Theme colors (submarine / tactical / instrument panel) ─────────────────
// These are exposed as JS constants AND written into App.css as CSS variables.
// Components use CSS variables; these constants exist for inline dynamic styles only.

export const THEME = {
  deepNavy:    '#1B2838', // page/card background
  goldAccent:  '#C9A94E', // primary accent — borders, active indicators
  darkTeal:    '#1A3C40', // secondary accent — waiting_review state
  parchment:   '#F5E6C8', // primary text
  borderGold:  '#8B7435', // card borders, dividers
  statusBarBg: '#0F1A24', // bottom status bar background
  errorRed:    '#C0392B', // error state — error_msg, rapid flash
  successGreen:'#27AE60', // complete state
} as const;

// ─── Status → display label mapping ─────────────────────────────────────────

export const STATUS_LABELS: Record<string, string> = {
  active:           'ACTIVE',
  waiting_approval: 'WAITING APPROVAL',
  waiting_review:   'WAITING REVIEW',
  complete:         'COMPLETE',
  error:            'ERROR',
} as const;

// ─── Status → theme color mapping ───────────────────────────────────────────

export const STATUS_COLORS: Record<string, string> = {
  active:           THEME.goldAccent,
  waiting_approval: '#F39C12', // amber — distinct from gold to signal pause
  waiting_review:   THEME.darkTeal,
  complete:         THEME.successGreen,
  error:            THEME.errorRed,
} as const;

// ─── Domain → display label mapping ─────────────────────────────────────────

export const DOMAIN_LABELS: Record<string, string> = {
  'va-advisory':  'VA-ADVISORY',
  'game-dev':     'GAME-DEV',
  'software-eng': 'SOFTWARE-ENG',
  'general':      'GENERAL',
} as const;

// ─── Context meter thresholds ────────────────────────────────────────────────

// Context usage above this percentage renders the meter in amber (warning)
export const CONTEXT_WARN_PCT  = 70;

// Context usage above this percentage renders the meter in red (critical)
export const CONTEXT_CRIT_PCT  = 90;

// ─── Layout ─────────────────────────────────────────────────────────────────

// Minimum card width in the agent grid (px)
export const CARD_MIN_WIDTH_PX = 340;
```

**Commit:** `config: add src/config.ts — all URLs, theme, constants`

---

### STEP 6 — Types: `src/types/agent.ts`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\types\agent.ts`

```ts
// agent.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: TypeScript types for agent state — must stay in sync with agentic_server.py Pydantic models.
//          These are the only types consumed by hooks and components. Never duplicate or shadow them.

// ─── Enumerations ────────────────────────────────────────────────────────────

// All possible lifecycle statuses a sub-agent can be in.
// Matches the `status` field written by agents to state/agents.json.
export type AgentStatus =
  | 'active'           // agent is running a stage
  | 'waiting_approval' // agent has paused and needs a human decision
  | 'waiting_review'   // agent is paused, a reviewer sub-agent is running
  | 'complete'         // agent finished all stages successfully
  | 'error';           // agent encountered an unrecoverable error

// Domain tag written by the spawning task — used for card color accents
// and future domain-specific config without modifying the bus.
export type AgentDomain =
  | 'va-advisory'
  | 'game-dev'
  | 'software-eng'
  | 'general';

// The three decisions a user can post to an approval gate.
// Null means no gate is currently open for this agent.
export type ApprovalDecision = 'proceed' | 'research' | 'review';

// ─── Core state shape ────────────────────────────────────────────────────────

// Full state object broadcast by the WebSocket for one agent.
// All fields are required; nullable fields use explicit `| null` — no optional `?`.
export interface AgentState {
  // Unique agent identifier — used as the key in all Maps and POST URL paths
  agent_id: string;

  // Domain tag — determines accent color and label in the card header
  domain: AgentDomain;

  // Human-readable description of what this agent is doing overall
  task: string;

  // Current stage name — shown below the progress bar
  stage_label: string;

  // Current stage number (1-indexed)
  stage: number;

  // Total number of stages this agent will run through
  total_stages: number;

  // Overall progress percentage (0–100) — drives the progress bar fill
  progress_pct: number;

  // Lifecycle status — drives StatusBadge color and button availability
  status: AgentStatus;

  // Percentage of Claude context window consumed (0–100) — drives ContextMeter
  context_pct_used: number;

  // Path to the agent's most recent output file — passed to reviewer on review decision
  output_ref: string | null;

  // Which decision the agent is currently waiting for (null if not at a gate)
  awaiting: ApprovalDecision | null;

  // Error message — only populated when status === 'error'
  error_msg: string | null;

  // agent_id of the parent agent that spawned this one (null for top-level agents)
  spawned_by: string | null;

  // Reviewer verdict text — only populated after a reviewer agent completes
  reviewer_verdict: string | null;

  // ISO 8601 timestamp of the last state write — used for staleness detection
  updated_at: string;
}

// ─── WebSocket message shape ─────────────────────────────────────────────────

// The FastAPI WebSocket broadcasts the full agents array on every change.
// Hooks parse this directly — no partial update protocol needed at this scale.
export type AgentsMessage = AgentState[];

// ─── Approval POST body ───────────────────────────────────────────────────────

// Body sent to /approve/{agent_id}, /research/{agent_id}, /review/{agent_id}
export interface ApprovalPayload {
  decision: ApprovalDecision;
}
```

**Commit:** `types: add src/types/agent.ts — full AgentState interface`

---

### STEP 7 — Hook: `src/hooks/useAgentState.ts`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\hooks\useAgentState.ts`

```ts
// useAgentState.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: WebSocket hook — connects to FastAPI state bus, manages reconnect backoff,
//          and exposes the current agents array to consumers.

import { useState, useEffect, useRef, useCallback } from 'react';
import type { AgentState, AgentsMessage } from '@/types/agent';
import {
  WS_URL,
  WS_RECONNECT_BASE_MS,
  WS_RECONNECT_MAX_MS,
} from '@/config';

// ─── Return type ─────────────────────────────────────────────────────────────

export interface UseAgentStateReturn {
  agents: AgentState[];       // current snapshot of all agent states
  connected: boolean;         // true when the WebSocket is open and healthy
  error: string | null;       // last connection error message, null if healthy
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useAgentState(): UseAgentStateReturn {
  const [agents, setAgents]       = useState<AgentState[]>([]);
  const [connected, setConnected] = useState<boolean>(false);
  const [error, setError]         = useState<string | null>(null);

  // Mutable ref stores the active WebSocket so the cleanup closure can close it
  const wsRef = useRef<WebSocket | null>(null);

  // Mutable ref stores current backoff delay — reset to base on successful open
  const backoffMsRef = useRef<number>(WS_RECONNECT_BASE_MS);

  // Mutable ref stores the pending reconnect timeout id so we can cancel it on unmount
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // connect is stable across renders — wrapped in useCallback to avoid effect re-runs
  const connect = useCallback(() => {
    // Close any existing socket before opening a new one
    if (wsRef.current !== null) {
      wsRef.current.close();
    }

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      // Successful connection — reset backoff and clear any error state
      setConnected(true);
      setError(null);
      backoffMsRef.current = WS_RECONNECT_BASE_MS;
    };

    ws.onmessage = (event: MessageEvent) => {
      // Parse the incoming JSON array — guard against malformed messages
      try {
        const data = JSON.parse(event.data as string) as AgentsMessage;
        setAgents(data);
      } catch {
        // Log parse errors but do not disconnect — the next message may be valid
        setError('Received malformed agent state message');
      }
    };

    ws.onerror = () => {
      // onerror fires before onclose — mark disconnected and surface to UI
      setConnected(false);
      setError(`WebSocket error on ${WS_URL}`);
    };

    ws.onclose = () => {
      setConnected(false);

      // Schedule exponential backoff reconnect — double delay, cap at max
      const delay = Math.min(backoffMsRef.current, WS_RECONNECT_MAX_MS);
      backoffMsRef.current = delay * 2;

      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, delay);
    };
  }, []); // no deps — WS_URL and backoff values are module-level constants

  useEffect(() => {
    // Open the initial connection on mount
    connect();

    // Cleanup: close socket and cancel any pending reconnect on unmount
    return () => {
      if (reconnectTimerRef.current !== null) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current !== null) {
        // Remove onclose before closing so cleanup doesn't trigger a reconnect
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { agents, connected, error };
}
```

**Commit:** `hooks: add useAgentState — WebSocket connection with exponential backoff`

---

### STEP 8 — Hook: `src/hooks/useApproval.ts`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\hooks\useApproval.ts`

```ts
// useApproval.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Approval POST hook — sends user decisions to FastAPI REST endpoints.
//          Tracks per-agent loading and error state independently.

import { useState, useCallback } from 'react';
import type { ApprovalDecision, ApprovalPayload } from '@/types/agent';
import { ENDPOINTS } from '@/config';

// ─── Return type ─────────────────────────────────────────────────────────────

export interface UseApprovalReturn {
  // True while a POST is in-flight for the given agent_id key
  loading: Record<string, boolean>;

  // Last error message for the given agent_id key, null if last call succeeded
  error: Record<string, string | null>;

  // Post a decision for a specific agent — resolves when the server acknowledges
  approve: (agentId: string, decision: ApprovalDecision) => Promise<void>;
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useApproval(): UseApprovalReturn {
  // Per-agent loading flags — keyed by agent_id so multiple cards don't block each other
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  // Per-agent error strings — keyed by agent_id; null means last call was successful
  const [error, setError]     = useState<Record<string, string | null>>({});

  // Selects the correct FastAPI endpoint path based on the decision type
  const resolveEndpoint = (agentId: string, decision: ApprovalDecision): string => {
    switch (decision) {
      case 'proceed':   return ENDPOINTS.approve(agentId);
      case 'research':  return ENDPOINTS.research(agentId);
      case 'review':    return ENDPOINTS.review(agentId);
      // Exhaustive switch — TypeScript will flag any missing case at compile time
    }
  };

  // approve is stable — useCallback prevents re-renders in child components that
  // receive it as a prop, since loading/error state changes would otherwise re-create it
  const approve = useCallback(
    async (agentId: string, decision: ApprovalDecision): Promise<void> => {
      // Mark this agent as loading and clear its prior error
      setLoading((prev) => ({ ...prev, [agentId]: true }));
      setError((prev)   => ({ ...prev, [agentId]: null }));

      const url = resolveEndpoint(agentId, decision);
      const body: ApprovalPayload = { decision };

      try {
        const response = await fetch(url, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(body),
        });

        if (!response.ok) {
          // Surface HTTP-level errors (404, 500) as readable strings
          throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
      } catch (err) {
        // Capture both network errors and HTTP errors
        const message = err instanceof Error ? err.message : 'Unknown error posting approval';
        setError((prev) => ({ ...prev, [agentId]: message }));
      } finally {
        // Always clear loading flag regardless of success or failure
        setLoading((prev) => ({ ...prev, [agentId]: false }));
      }
    },
    [] // no deps — ENDPOINTS are module-level constants
  );

  return { loading, error, approve };
}
```

**Commit:** `hooks: add useApproval — per-agent POST with loading and error state`

---

### STEP 9 — Component: `StatusBadge`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\StatusBadge\StatusBadge.tsx`

```tsx
// StatusBadge.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Renders the colored dot + status label in the top-right of each agent card.

import React from 'react';
import type { AgentStatus } from '@/types/agent';
import { STATUS_LABELS, STATUS_COLORS } from '@/config';
import styles from './StatusBadge.css?inline';

// CSS is imported via link in App.css to keep component files free of global side effects
import './StatusBadge.css';

interface StatusBadgeProps {
  readonly status: AgentStatus;
}

// StatusBadge renders a colored indicator dot followed by the status label.
// Color is driven entirely by STATUS_COLORS from config — never hardcoded here.
export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const color = STATUS_COLORS[status] ?? STATUS_COLORS['error'];
  const label = STATUS_LABELS[status] ?? status.toUpperCase();

  return (
    <span className="status-badge" aria-label={`Agent status: ${label}`}>
      {/* Colored dot — color injected via inline style from config constants */}
      <span
        className="status-badge__dot"
        style={{ color }}
        aria-hidden="true"
      >
        ●
      </span>
      {/* Status label — uses the human-readable mapping from config */}
      <span className="status-badge__label" style={{ color }}>
        {label}
      </span>
    </span>
  );
};
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\StatusBadge\StatusBadge.css`

```css
/* StatusBadge.css
   Developer: Marcus Daley
   Date: 2026-04-29
   Purpose: Styles for the colored status dot and label in the card header */

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-stack);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.status-badge__dot {
  /* Dot is decorative — sized by font-size so it scales with the label */
  font-size: 0.65rem;
  line-height: 1;
}

.status-badge__label {
  /* Label color is set inline from config constants — this rule is a fallback only */
  color: inherit;
}
```

**Commit:** `component: add StatusBadge — colored status dot and label`

---

### STEP 10 — Component: `ContextMeter`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\ContextMeter\ContextMeter.tsx`

```tsx
// ContextMeter.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Renders a horizontal gauge bar showing what percentage of the
//          Claude context window has been consumed by this agent.

import React from 'react';
import { THEME, CONTEXT_WARN_PCT, CONTEXT_CRIT_PCT } from '@/config';
import './ContextMeter.css';

interface ContextMeterProps {
  readonly pctUsed: number; // 0–100, from agent.context_pct_used
}

// Derive fill color from usage thresholds defined in config — never hardcoded here
function resolveMeterColor(pct: number): string {
  if (pct >= CONTEXT_CRIT_PCT) return THEME.errorRed;
  if (pct >= CONTEXT_WARN_PCT) return '#F39C12'; // amber — between normal and critical
  return THEME.goldAccent;
}

// ContextMeter renders a labeled gauge bar. The fill width is clamped to [0, 100]
// so malformed server data cannot overflow the visual container.
export const ContextMeter: React.FC<ContextMeterProps> = ({ pctUsed }) => {
  // Clamp to valid percentage range before rendering
  const clamped = Math.max(0, Math.min(100, pctUsed));
  const fillColor = resolveMeterColor(clamped);

  return (
    <div className="context-meter" aria-label={`Context window: ${clamped}% used`}>
      {/* Track is the full-width container; fill is the colored portion */}
      <div className="context-meter__track" role="progressbar" aria-valuenow={clamped} aria-valuemin={0} aria-valuemax={100}>
        <div
          className="context-meter__fill"
          style={{
            width: `${clamped}%`,
            backgroundColor: fillColor,
          }}
        />
      </div>
      {/* Percentage label to the right of the bar */}
      <span className="context-meter__label" style={{ color: fillColor }}>
        {clamped}%
      </span>
    </div>
  );
};
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\ContextMeter\ContextMeter.css`

```css
/* ContextMeter.css
   Developer: Marcus Daley
   Date: 2026-04-29
   Purpose: Horizontal gauge bar for context window consumption */

.context-meter {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.context-meter__track {
  flex: 1;
  height: 6px;
  background-color: var(--color-border-gold);
  border-radius: 3px;
  overflow: hidden; /* prevents fill from overflowing rounded corners */
}

.context-meter__fill {
  height: 100%;
  border-radius: 3px;
  /* Smooth animated fill as context_pct_used changes over WebSocket updates */
  transition: width 0.4s ease, background-color 0.4s ease;
}

.context-meter__label {
  font-family: var(--font-stack);
  font-size: 0.72rem;
  font-weight: 600;
  min-width: 36px; /* prevents layout shift as number changes from 9% to 100% */
  text-align: right;
  transition: color 0.4s ease;
}
```

**Commit:** `component: add ContextMeter — animated context window gauge bar`

---

### STEP 11 — Component: `ReviewerPanel`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\ReviewerPanel\ReviewerPanel.tsx`

```tsx
// ReviewerPanel.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Expandable panel that displays the reviewer agent's verdict.
//          Hidden until reviewer_verdict is non-null. Expands on mount when verdict arrives.

import React, { useState, useEffect } from 'react';
import './ReviewerPanel.css';

interface ReviewerPanelProps {
  // Verdict text written by the reviewer agent — null means review is not yet complete
  readonly verdict: string | null;
}

// ReviewerPanel is hidden when verdict is null. When a verdict arrives,
// the panel auto-expands once so the user notices it, then can collapse it.
export const ReviewerPanel: React.FC<ReviewerPanelProps> = ({ verdict }) => {
  // Tracks whether the panel is currently open (expanded)
  const [isOpen, setIsOpen] = useState<boolean>(false);

  // Auto-expand the panel the first time a verdict arrives
  useEffect(() => {
    if (verdict !== null) {
      setIsOpen(true);
    }
  }, [verdict]);

  // Render nothing when there is no verdict — the panel takes zero height
  if (verdict === null) {
    return null;
  }

  return (
    <div className="reviewer-panel">
      {/* Toggle button — always visible once verdict exists */}
      <button
        className="reviewer-panel__toggle"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-controls="reviewer-panel__body"
      >
        <span className="reviewer-panel__toggle-label">REVIEWER VERDICT</span>
        {/* Chevron rotates 180° when expanded */}
        <span
          className="reviewer-panel__chevron"
          aria-hidden="true"
          style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
        >
          ▼
        </span>
      </button>

      {/* Verdict body — shown only when isOpen */}
      {isOpen && (
        <div
          id="reviewer-panel__body"
          className="reviewer-panel__body"
          role="region"
          aria-label="Reviewer verdict content"
        >
          {/* Pre-wrap preserves the structured PASS | REVISE | REJECT formatting */}
          <pre className="reviewer-panel__text">{verdict}</pre>
        </div>
      )}
    </div>
  );
};
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\ReviewerPanel\ReviewerPanel.css`

```css
/* ReviewerPanel.css
   Developer: Marcus Daley
   Date: 2026-04-29
   Purpose: Expandable reviewer verdict panel below the approval buttons */

.reviewer-panel {
  width: 100%;
  border-top: 1px solid var(--color-border-gold);
  margin-top: 12px;
}

.reviewer-panel__toggle {
  /* Full-width toggle bar — matches card interior width */
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 0;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-gold-accent);
  font-family: var(--font-stack);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.reviewer-panel__toggle:hover {
  color: var(--color-parchment);
}

.reviewer-panel__chevron {
  display: inline-block;
  transition: transform 0.25s ease;
  font-size: 0.6rem;
}

.reviewer-panel__body {
  /* Slight indentation to visually separate from the toggle label */
  padding: 10px 0 6px 0;
}

.reviewer-panel__text {
  /* Pre-wrap preserves PASS / REVISE / REJECT structured output line breaks */
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-stack);
  font-size: 0.8rem;
  color: var(--color-parchment);
  margin: 0;
  line-height: 1.55;
}
```

**Commit:** `component: add ReviewerPanel — auto-expanding verdict display`

---

### STEP 12 — Component: `ApprovalButtons`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\ApprovalButtons\ApprovalButtons.tsx`

```tsx
// ApprovalButtons.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Renders the three approval action buttons. Buttons are enabled only when
//          the agent is at a gate (status === 'waiting_approval'). Each button is
//          disabled while its action is in-flight to prevent double-posting.

import React from 'react';
import type { AgentState, ApprovalDecision } from '@/types/agent';
import './ApprovalButtons.css';

interface ApprovalButtonsProps {
  readonly agent: AgentState;
  // Whether a POST is currently in-flight for this agent
  readonly isLoading: boolean;
  // Error from the last POST attempt, null if none
  readonly postError: string | null;
  // Callback that triggers the approval POST — provided by AgentCard from useApproval
  readonly onApprove: (decision: ApprovalDecision) => void;
}

// Buttons are enabled only when the agent is actively waiting for a user decision.
// Any other status (active, complete, error) leaves them disabled.
export const ApprovalButtons: React.FC<ApprovalButtonsProps> = ({
  agent,
  isLoading,
  postError,
  onApprove,
}) => {
  // Gate is open when the agent is waiting and no POST is currently in-flight
  const gateOpen = agent.status === 'waiting_approval' && !isLoading;

  return (
    <div className="approval-buttons">
      {/* ── PROCEED button ── */}
      <button
        className="approval-btn approval-btn--proceed"
        disabled={!gateOpen}
        onClick={() => onApprove('proceed')}
        aria-label="Approve agent to proceed to the next stage"
      >
        PROCEED
      </button>

      {/* ── RESEARCH MORE button ── */}
      <button
        className="approval-btn approval-btn--research"
        disabled={!gateOpen}
        onClick={() => onApprove('research')}
        aria-label="Spawn a research sub-agent before proceeding"
      >
        RESEARCH MORE
      </button>

      {/* ── REVIEW BY AGENT button ── */}
      <button
        className="approval-btn approval-btn--review"
        disabled={!gateOpen}
        onClick={() => onApprove('review')}
        aria-label="Spawn a reviewer agent to evaluate the current output"
      >
        REVIEW BY AGENT
      </button>

      {/* Loading indicator — shown inline only while POST is in-flight */}
      {isLoading && (
        <span className="approval-buttons__loading" aria-live="polite">
          Sending…
        </span>
      )}

      {/* Error message — shown below the buttons when last POST failed */}
      {postError !== null && (
        <p className="approval-buttons__error" role="alert">
          {postError}
        </p>
      )}
    </div>
  );
};
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\ApprovalButtons\ApprovalButtons.css`

```css
/* ApprovalButtons.css
   Developer: Marcus Daley
   Date: 2026-04-29
   Purpose: Three-button approval row in submarine tactical style */

.approval-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  width: 100%;
  margin-top: 12px;
}

.approval-btn {
  flex: 1;
  min-width: 90px;
  padding: 8px 10px;
  font-family: var(--font-stack);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: 1px solid var(--color-border-gold);
  background: transparent;
  color: var(--color-gold-accent);
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.approval-btn:hover:not(:disabled) {
  background: var(--color-gold-accent);
  color: var(--color-deep-navy);
}

/* Disabled state — visually dim when gate is not open */
.approval-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* REVIEW button uses teal accent to visually distinguish from the other two */
.approval-btn--review {
  border-color: var(--color-dark-teal);
  color: #4DB6AC; /* light teal readable against dark navy — complements dark-teal */
}

.approval-btn--review:hover:not(:disabled) {
  background: var(--color-dark-teal);
  color: var(--color-parchment);
}

.approval-buttons__loading {
  font-family: var(--font-stack);
  font-size: 0.7rem;
  color: var(--color-gold-accent);
  opacity: 0.75;
  margin-left: 4px;
}

.approval-buttons__error {
  width: 100%;
  margin: 6px 0 0 0;
  font-family: var(--font-stack);
  font-size: 0.72rem;
  color: var(--color-error-red);
}
```

**Commit:** `component: add ApprovalButtons — PROCEED / RESEARCH MORE / REVIEW BY AGENT`

---

### STEP 13 — Component: `SonarHUD`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\SonarHUD\SonarHUD.tsx`

```tsx
// SonarHUD.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Placeholder wrapper for the Spline 3D sonar scene.
//          Renders a styled placeholder rectangle now. Spline integration is wired in Plan 4.
//          The component API is final — Plan 4 only changes the implementation body.

import React from 'react';
import type { AgentStatus } from '@/types/agent';
import { STATUS_COLORS } from '@/config';
import './SonarHUD.css';

interface SonarHUDProps {
  // Agent progress (0–100) — will drive depth gauge needle in Plan 4
  readonly progressPct: number;
  // Agent status — will drive sonar ring pulse rate in Plan 4
  readonly status: AgentStatus;
  // Agent ID — used as the Spline variable namespace prefix in Plan 4
  readonly agentId: string;
}

// SonarHUD renders a placeholder that occupies the correct space in the card layout.
// The gold border and status color glow match what the Spline scene will produce.
// Plan 4 replaces the inner div with <Spline scene={SPLINE_SCENE_URL} onLoad={...} />
export const SonarHUD: React.FC<SonarHUDProps> = ({ progressPct, status, agentId }) => {
  // Use status color to tint the placeholder glow — matches future Spline panel glow
  const glowColor = STATUS_COLORS[status] ?? STATUS_COLORS['error'];

  return (
    <div
      className="sonar-hud"
      aria-label={`Sonar HUD for ${agentId} — progress ${progressPct}%`}
      style={{ boxShadow: `inset 0 0 24px ${glowColor}22` }}
    >
      {/* Placeholder label — removed in Plan 4 when Spline scene loads */}
      <span className="sonar-hud__placeholder-label">
        [ SONAR HUD — SPLINE WIRED IN PLAN 4 ]
      </span>

      {/* Static progress readout — Spline depth gauge replaces this in Plan 4 */}
      <span className="sonar-hud__progress" style={{ color: glowColor }}>
        {progressPct}%
      </span>
    </div>
  );
};
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\SonarHUD\SonarHUD.css`

```css
/* SonarHUD.css
   Developer: Marcus Daley
   Date: 2026-04-29
   Purpose: Placeholder and future Spline scene container styling */

.sonar-hud {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 140px;
  background: var(--color-status-bar-bg);
  border: 1px solid var(--color-border-gold);
  border-radius: 4px;
  margin: 12px 0;
  /* Box shadow is injected via inline style from STATUS_COLORS — see component */
  transition: box-shadow 0.4s ease;
}

.sonar-hud__placeholder-label {
  font-family: var(--font-stack);
  font-size: 0.65rem;
  color: var(--color-border-gold);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.6;
}

.sonar-hud__progress {
  font-family: var(--font-stack);
  font-size: 1.4rem;
  font-weight: 700;
  margin-top: 8px;
  transition: color 0.4s ease;
}
```

**Commit:** `component: add SonarHUD placeholder — final API, Spline wired in Plan 4`

---

### STEP 14 — Component: `AgentCard`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\AgentCard\AgentCard.tsx`

```tsx
// AgentCard.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Instrument panel card — renders the full state of one agent.
//          Composes StatusBadge, SonarHUD, ContextMeter, ApprovalButtons, ReviewerPanel.

import React from 'react';
import type { AgentState, ApprovalDecision } from '@/types/agent';
import { DOMAIN_LABELS, THEME } from '@/config';
import { StatusBadge } from '@/components/StatusBadge/StatusBadge';
import { SonarHUD } from '@/components/SonarHUD/SonarHUD';
import { ContextMeter } from '@/components/ContextMeter/ContextMeter';
import { ApprovalButtons } from '@/components/ApprovalButtons/ApprovalButtons';
import { ReviewerPanel } from '@/components/ReviewerPanel/ReviewerPanel';
import './AgentCard.css';

interface AgentCardProps {
  readonly agent: AgentState;
  // Whether a POST is in-flight for this specific agent
  readonly isLoading: boolean;
  // Last POST error for this agent, null if clean
  readonly postError: string | null;
  // Bubbles decision up to App.tsx which owns the useApproval hook
  readonly onApprove: (agentId: string, decision: ApprovalDecision) => void;
}

// AgentCard is a pure presentational component — it owns no state.
// All data flows in via props; decisions flow out via onApprove callback.
export const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  isLoading,
  postError,
  onApprove,
}) => {
  const domainLabel = DOMAIN_LABELS[agent.domain] ?? agent.domain.toUpperCase();

  // Wrap onApprove to inject the agent_id — ApprovalButtons doesn't know its own ID
  const handleApprove = (decision: ApprovalDecision) => {
    onApprove(agent.agent_id, decision);
  };

  return (
    <article
      className="agent-card"
      aria-label={`Agent card for ${agent.agent_id}`}
      data-status={agent.status} // allows CSS attribute selectors for status theming
    >
      {/* ── Header row: agent ID, domain tag, status badge ── */}
      <header className="agent-card__header">
        <div className="agent-card__identity">
          {/* Agent ID in gold uppercase — primary identifier */}
          <span className="agent-card__id">{agent.agent_id}</span>
          {/* Domain tag in brackets — secondary classification */}
          <span className="agent-card__domain">[{domainLabel}]</span>
        </div>
        {/* Status badge in top-right corner */}
        <StatusBadge status={agent.status} />
      </header>

      {/* ── Divider ── */}
      <hr className="agent-card__divider" />

      {/* ── Stage label — current step description ── */}
      <p className="agent-card__stage-label">
        <span className="agent-card__stage-count">
          Stage {agent.stage}/{agent.total_stages}
        </span>
        {' · '}
        {agent.stage_label}
      </p>

      {/* ── Task description — overall agent objective ── */}
      <p className="agent-card__task">{agent.task}</p>

      {/* ── Sonar HUD — Spline 3D placeholder (Plan 4 wires the real scene) ── */}
      <SonarHUD
        progressPct={agent.progress_pct}
        status={agent.status}
        agentId={agent.agent_id}
      />

      {/* ── Progress bar row ── */}
      <div className="agent-card__progress-row">
        {/* ASCII-style block fill matches the instrument panel design spec */}
        <div className="agent-card__progress-track" aria-hidden="true">
          <div
            className="agent-card__progress-fill"
            style={{ width: `${agent.progress_pct}%` }}
          />
        </div>
        <span className="agent-card__progress-pct">{agent.progress_pct}%</span>
      </div>

      {/* ── Approval buttons — enabled only at gate points ── */}
      <ApprovalButtons
        agent={agent}
        isLoading={isLoading}
        postError={postError}
        onApprove={handleApprove}
      />

      {/* ── Context meter — shows context window consumption ── */}
      <div className="agent-card__context-row">
        <span className="agent-card__context-label">Context:</span>
        <ContextMeter pctUsed={agent.context_pct_used} />
      </div>

      {/* ── Error message — only visible when status === 'error' ── */}
      {agent.error_msg !== null && (
        <p className="agent-card__error-msg" role="alert">
          {agent.error_msg}
        </p>
      )}

      {/* ── Reviewer panel — hidden until reviewer_verdict is populated ── */}
      <ReviewerPanel verdict={agent.reviewer_verdict} />
    </article>
  );
};
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\AgentCard\AgentCard.css`

```css
/* AgentCard.css
   Developer: Marcus Daley
   Date: 2026-04-29
   Purpose: Instrument panel card — submarine/tactical styling */

.agent-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 18px;
  background: var(--color-deep-navy);
  border: 1px solid var(--color-border-gold);
  border-radius: 6px;
  /* Subtle inner glow — deepens when status changes (transition on box-shadow) */
  box-shadow: 0 0 12px rgba(201, 169, 78, 0.08);
  transition: box-shadow 0.3s ease;
  min-width: 0; /* allows card to shrink inside CSS grid without overflow */
}

/* Brighten glow when agent is actively running */
.agent-card[data-status="active"] {
  box-shadow: 0 0 18px rgba(201, 169, 78, 0.18);
}

/* Amber glow when waiting for approval */
.agent-card[data-status="waiting_approval"] {
  box-shadow: 0 0 18px rgba(243, 156, 18, 0.18);
}

/* Teal glow when waiting for reviewer */
.agent-card[data-status="waiting_review"] {
  box-shadow: 0 0 18px rgba(26, 60, 64, 0.5);
}

/* Red glow on error */
.agent-card[data-status="error"] {
  box-shadow: 0 0 18px rgba(192, 57, 43, 0.3);
  border-color: var(--color-error-red);
}

/* ── Header ── */

.agent-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-card__identity {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.agent-card__id {
  font-family: var(--font-stack);
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-gold-accent);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.agent-card__domain {
  font-family: var(--font-stack);
  font-size: 0.7rem;
  color: var(--color-border-gold);
  letter-spacing: 0.08em;
}

/* ── Divider ── */

.agent-card__divider {
  border: none;
  border-top: 1px solid var(--color-border-gold);
  margin: 4px 0;
  opacity: 0.5;
}

/* ── Stage label ── */

.agent-card__stage-label {
  font-family: var(--font-stack);
  font-size: 0.78rem;
  color: var(--color-parchment);
  margin: 0;
  line-height: 1.4;
}

.agent-card__stage-count {
  color: var(--color-gold-accent);
  font-weight: 600;
}

/* ── Task description ── */

.agent-card__task {
  font-family: var(--font-stack);
  font-size: 0.72rem;
  color: var(--color-border-gold);
  margin: 0;
  line-height: 1.4;
}

/* ── Progress bar ── */

.agent-card__progress-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-card__progress-track {
  flex: 1;
  height: 8px;
  background: rgba(139, 116, 53, 0.25); /* faint gold — empty track */
  border-radius: 4px;
  overflow: hidden;
}

.agent-card__progress-fill {
  height: 100%;
  background: var(--color-gold-accent);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.agent-card__progress-pct {
  font-family: var(--font-stack);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-gold-accent);
  min-width: 36px;
  text-align: right;
}

/* ── Context row ── */

.agent-card__context-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-card__context-label {
  font-family: var(--font-stack);
  font-size: 0.7rem;
  color: var(--color-border-gold);
  white-space: nowrap;
}

/* ── Error message ── */

.agent-card__error-msg {
  font-family: var(--font-stack);
  font-size: 0.75rem;
  color: var(--color-error-red);
  margin: 0;
  padding: 6px 8px;
  background: rgba(192, 57, 43, 0.1);
  border-left: 3px solid var(--color-error-red);
}
```

**Commit:** `component: add AgentCard — full instrument panel card composition`

---

### STEP 15 — Root: `App.tsx` and `App.css`

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\App.tsx`

```tsx
// App.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Root component — owns the WebSocket connection and approval hook,
//          renders the agent grid, and displays the connection status bar.

import React from 'react';
import { useAgentState } from '@/hooks/useAgentState';
import { useApproval } from '@/hooks/useApproval';
import { AgentCard } from '@/components/AgentCard/AgentCard';
import type { ApprovalDecision } from '@/types/agent';
import './App.css';

// App is the single owner of both hooks — data flows down, events flow up.
// No context provider needed at this scale; props are direct.
const App: React.FC = () => {
  // Live agent state from WebSocket — re-renders on every broadcast
  const { agents, connected, error: wsError } = useAgentState();

  // POST approval decisions — exposes per-agent loading and error
  const { loading, error: postErrors, approve } = useApproval();

  // Stable callback forwarded to each AgentCard — avoids inline arrow in JSX
  const handleApprove = (agentId: string, decision: ApprovalDecision) => {
    void approve(agentId, decision);
  };

  return (
    <div className="app">
      {/* ── Header bar ── */}
      <header className="app__header">
        <h1 className="app__title">AGENTIC OS — COMMAND CENTER</h1>

        {/* WebSocket connection indicator — always visible in header */}
        <div className="app__connection-status" aria-live="polite">
          <span
            className="app__connection-dot"
            aria-hidden="true"
            data-connected={String(connected)}
          >
            ●
          </span>
          <span className="app__connection-label">
            {connected ? 'CONNECTED' : 'CONNECTING…'}
          </span>
        </div>
      </header>

      {/* ── WebSocket error banner — only shown when connection has an error ── */}
      {wsError !== null && (
        <div className="app__ws-error" role="alert">
          {wsError}
        </div>
      )}

      {/* ── Agent grid — responsive CSS grid, min card width from config ── */}
      <main className="app__grid" aria-label="Active agents">
        {agents.length === 0 ? (
          // Empty state — shown while waiting for the first WebSocket broadcast
          <p className="app__empty-state">
            No agents active. Agents appear here when a task is running.
          </p>
        ) : (
          agents.map((agent) => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              isLoading={loading[agent.agent_id] ?? false}
              postError={postErrors[agent.agent_id] ?? null}
              onApprove={handleApprove}
            />
          ))
        )}
      </main>

      {/* ── Status bar ── */}
      <footer className="app__status-bar">
        <span>AgenticOS Command Center</span>
        <span>{agents.length} agent{agents.length !== 1 ? 's' : ''} tracked</span>
      </footer>
    </div>
  );
};

export default App;
```

**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\App.css`

```css
/* App.css
   Developer: Marcus Daley
   Date: 2026-04-29
   Purpose: Global layout, CSS custom properties (theme tokens), and base resets.
            All component CSS files reference these variables — never hardcode theme colors. */

/* ── CSS custom properties — single source of truth for all theme values ── */
:root {
  /* Theme colors — match THEME constants in config.ts exactly */
  --color-deep-navy:    #1B2838;
  --color-gold-accent:  #C9A94E;
  --color-dark-teal:    #1A3C40;
  --color-parchment:    #F5E6C8;
  --color-border-gold:  #8B7435;
  --color-status-bar-bg: #0F1A24;
  --color-error-red:    #C0392B;
  --color-success-green: #27AE60;

  /* Font stack — Segoe UI system font with legible fallbacks */
  --font-stack: 'Segoe UI', 'Segoe UI Variable', system-ui, -apple-system, sans-serif;

  /* Card minimum width — from CARD_MIN_WIDTH_PX constant in config.ts */
  --card-min-width: 340px;
}

/* ── Base reset ── */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, #root {
  height: 100%;
  width: 100%;
}

body {
  background-color: var(--color-deep-navy);
  color: var(--color-parchment);
  font-family: var(--font-stack);
  /* Subpixel rendering for crisp text on the instrument panel */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── App shell layout ── */
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 100vh;
}

/* ── Header bar ── */
.app__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: var(--color-status-bar-bg);
  border-bottom: 1px solid var(--color-border-gold);
  flex-shrink: 0; /* header never shrinks when grid content grows */
}

.app__title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-gold-accent);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

/* ── Connection status indicator ── */
.app__connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.app__connection-dot {
  font-size: 0.6rem;
  /* Color driven by data attribute — green when connected, amber when not */
  color: var(--color-error-red);
}

.app__connection-dot[data-connected="true"] {
  color: var(--color-success-green);
}

.app__connection-label {
  color: var(--color-border-gold);
}

/* ── WebSocket error banner ── */
.app__ws-error {
  background: rgba(192, 57, 43, 0.15);
  border-bottom: 1px solid var(--color-error-red);
  color: var(--color-error-red);
  font-size: 0.75rem;
  padding: 6px 20px;
  flex-shrink: 0;
}

/* ── Agent grid ── */
.app__grid {
  flex: 1; /* takes remaining vertical space between header and status bar */
  display: grid;
  /* Responsive grid — cards wrap at var(--card-min-width) minimum */
  grid-template-columns: repeat(auto-fill, minmax(var(--card-min-width), 1fr));
  gap: 16px;
  padding: 16px 20px;
  align-content: start; /* cards stack from top, not vertically centered */
  overflow-y: auto;
}

/* ── Empty state ── */
.app__empty-state {
  grid-column: 1 / -1; /* span full grid width */
  text-align: center;
  color: var(--color-border-gold);
  font-size: 0.8rem;
  padding: 40px 0;
  opacity: 0.7;
}

/* ── Status bar ── */
.app__status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 20px;
  background: var(--color-status-bar-bg);
  border-top: 1px solid var(--color-border-gold);
  font-size: 0.68rem;
  color: var(--color-border-gold);
  letter-spacing: 0.06em;
  flex-shrink: 0;
}
```

**Commit:** `app: add App.tsx root component and App.css global theme tokens`

---

### STEP 16 — Tests: `AgentCard.test.tsx`

**File:** `C:\ClaudeSkills\tests\AgenticOS\frontend\AgentCard.test.tsx`

```tsx
// AgentCard.test.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for AgentCard — renders correctly for each agent status,
//          calls onApprove with correct args, shows/hides ReviewerPanel.

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentCard } from '../../../AgenticOS/frontend/src/components/AgentCard/AgentCard';
import type { AgentState } from '../../../AgenticOS/frontend/src/types/agent';

// ─── Fixture factory ─────────────────────────────────────────────────────────

// Builds a minimal valid AgentState — override individual fields per test
function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
  return {
    agent_id:         'AGENT-01',
    domain:           'va-advisory',
    task:             'Analyze CFR Title 38',
    stage_label:      'Parsing regulation text',
    stage:            2,
    total_stages:     5,
    progress_pct:     40,
    status:           'active',
    context_pct_used: 30,
    output_ref:       null,
    awaiting:         null,
    error_msg:        null,
    spawned_by:       null,
    reviewer_verdict: null,
    updated_at:       '2026-04-29T10:00:00Z',
    ...overrides,
  };
}

// ─── Render helper ────────────────────────────────────────────────────────────

function renderCard(agent: AgentState, isLoading = false, postError: string | null = null) {
  const onApprove = vi.fn();
  render(
    <AgentCard
      agent={agent}
      isLoading={isLoading}
      postError={postError}
      onApprove={onApprove}
    />
  );
  return { onApprove };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('AgentCard', () => {
  it('renders agent ID and domain label', () => {
    renderCard(makeAgent());
    // Agent ID must appear in the card header
    expect(screen.getByText('AGENT-01')).toBeInTheDocument();
    // Domain label must be bracketed
    expect(screen.getByText('[VA-ADVISORY]')).toBeInTheDocument();
  });

  it('renders stage label and task', () => {
    renderCard(makeAgent());
    expect(screen.getByText(/Parsing regulation text/)).toBeInTheDocument();
    expect(screen.getByText('Analyze CFR Title 38')).toBeInTheDocument();
  });

  it('renders ACTIVE status badge', () => {
    renderCard(makeAgent({ status: 'active' }));
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('renders WAITING APPROVAL status badge', () => {
    renderCard(makeAgent({ status: 'waiting_approval' }));
    expect(screen.getByText('WAITING APPROVAL')).toBeInTheDocument();
  });

  it('disables approval buttons when status is active', () => {
    renderCard(makeAgent({ status: 'active' }));
    // Buttons must be disabled — gate is not open for active agents
    expect(screen.getByRole('button', { name: /proceed/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /research more/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /review by agent/i })).toBeDisabled();
  });

  it('enables approval buttons when status is waiting_approval', () => {
    renderCard(makeAgent({ status: 'waiting_approval' }));
    expect(screen.getByRole('button', { name: /proceed/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /research more/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /review by agent/i })).not.toBeDisabled();
  });

  it('calls onApprove with correct agentId and decision on PROCEED click', () => {
    const agent = makeAgent({ status: 'waiting_approval' });
    const { onApprove } = renderCard(agent);
    fireEvent.click(screen.getByRole('button', { name: /proceed/i }));
    expect(onApprove).toHaveBeenCalledOnce();
    expect(onApprove).toHaveBeenCalledWith('AGENT-01', 'proceed');
  });

  it('calls onApprove with research decision on RESEARCH MORE click', () => {
    const agent = makeAgent({ status: 'waiting_approval' });
    const { onApprove } = renderCard(agent);
    fireEvent.click(screen.getByRole('button', { name: /research more/i }));
    expect(onApprove).toHaveBeenCalledWith('AGENT-01', 'research');
  });

  it('calls onApprove with review decision on REVIEW BY AGENT click', () => {
    const agent = makeAgent({ status: 'waiting_approval' });
    const { onApprove } = renderCard(agent);
    fireEvent.click(screen.getByRole('button', { name: /review by agent/i }));
    expect(onApprove).toHaveBeenCalledWith('AGENT-01', 'review');
  });

  it('disables buttons when isLoading is true even at approval gate', () => {
    renderCard(makeAgent({ status: 'waiting_approval' }), true);
    // Loading flag must override gate-open state to prevent double-post
    expect(screen.getByRole('button', { name: /proceed/i })).toBeDisabled();
  });

  it('renders postError message when provided', () => {
    renderCard(makeAgent(), false, 'Server responded with 500: Internal Server Error');
    expect(screen.getByText(/Server responded with 500/)).toBeInTheDocument();
  });

  it('renders error_msg when status is error', () => {
    renderCard(makeAgent({ status: 'error', error_msg: 'Stage 3 failed: timeout' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Stage 3 failed: timeout');
  });

  it('does not render ReviewerPanel when reviewer_verdict is null', () => {
    renderCard(makeAgent({ reviewer_verdict: null }));
    // Toggle button must not exist when there is no verdict
    expect(screen.queryByText(/reviewer verdict/i)).not.toBeInTheDocument();
  });

  it('renders ReviewerPanel and auto-expands when reviewer_verdict is set', () => {
    renderCard(makeAgent({ reviewer_verdict: 'PASS — output is complete and accurate.' }));
    // Panel toggle must be visible
    expect(screen.getByText(/reviewer verdict/i)).toBeInTheDocument();
    // Verdict text must be visible because panel auto-expands on mount
    expect(screen.getByText('PASS — output is complete and accurate.')).toBeInTheDocument();
  });
});
```

**Commit:** `tests: add AgentCard.test.tsx — 13 unit tests covering render, gate, approval, reviewer`

---

### STEP 17 — Tests: `useAgentState.test.ts`

**File:** `C:\ClaudeSkills\tests\AgenticOS\frontend\useAgentState.test.ts`

```ts
// useAgentState.test.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for useAgentState — WebSocket lifecycle, message parsing,
//          reconnect scheduling, and cleanup on unmount.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAgentState } from '../../../AgenticOS/frontend/src/hooks/useAgentState';
import type { AgentState } from '../../../AgenticOS/frontend/src/types/agent';

// ─── WebSocket mock ───────────────────────────────────────────────────────────

// We need a controllable WebSocket mock that lets tests trigger events manually.
// The real WebSocket is not available in jsdom — this mock replaces it globally.

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
  readyState: number = 0; // CONNECTING
  onopen:    ((e: Event) => void) | null = null;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onerror:   ((e: Event) => void) | null = null;
  onclose:   ((e: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  // Test helper: simulate a successful connection open
  triggerOpen() {
    this.readyState = 1; // OPEN
    this.onopen?.(new Event('open'));
  }

  // Test helper: simulate a received message
  triggerMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }

  // Test helper: simulate a connection close
  triggerClose() {
    this.readyState = 3; // CLOSED
    this.onclose?.(new CloseEvent('close'));
  }

  // Test helper: simulate an error
  triggerError() {
    this.onerror?.(new Event('error'));
  }

  close() {
    this.readyState = 3;
  }
}

// ─── Fixture ─────────────────────────────────────────────────────────────────

const AGENT_FIXTURE: AgentState = {
  agent_id:         'AGENT-01',
  domain:           'general',
  task:             'Test task',
  stage_label:      'Running',
  stage:            1,
  total_stages:     3,
  progress_pct:     33,
  status:           'active',
  context_pct_used: 10,
  output_ref:       null,
  awaiting:         null,
  error_msg:        null,
  spawned_by:       null,
  reviewer_verdict: null,
  updated_at:       '2026-04-29T10:00:00Z',
};

// ─── Setup / teardown ─────────────────────────────────────────────────────────

beforeEach(() => {
  MockWebSocket.instances = [];
  // Replace the global WebSocket with our mock before each test
  vi.stubGlobal('WebSocket', MockWebSocket);
  // Stub timers so reconnect delays don't stall tests
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('useAgentState', () => {
  it('starts with empty agents and connected false', () => {
    const { result } = renderHook(() => useAgentState());
    expect(result.current.agents).toEqual([]);
    expect(result.current.connected).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets connected to true on WebSocket open', () => {
    const { result } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
    });
    expect(result.current.connected).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('parses incoming JSON array and updates agents state', () => {
    const { result } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      MockWebSocket.instances[0].triggerMessage([AGENT_FIXTURE]);
    });
    expect(result.current.agents).toHaveLength(1);
    expect(result.current.agents[0].agent_id).toBe('AGENT-01');
  });

  it('sets error on malformed message without disconnecting', () => {
    // Malformed messages should surface an error but not close the socket
    const { result } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      // Manually trigger onmessage with invalid JSON — cannot use triggerMessage helper
      MockWebSocket.instances[0].onmessage?.(
        new MessageEvent('message', { data: 'not-valid-json{{{' })
      );
    });
    expect(result.current.error).toMatch(/malformed/i);
    // connected must still be true — bad message doesn't close the socket
    expect(result.current.connected).toBe(true);
  });

  it('sets connected false and schedules reconnect on close', () => {
    const { result } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      MockWebSocket.instances[0].triggerClose();
    });
    expect(result.current.connected).toBe(false);
    // Advance fake timers past the initial backoff (1000ms) — should trigger reconnect
    act(() => {
      vi.advanceTimersByTime(1500);
    });
    // A second WebSocket instance must have been created by the reconnect
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it('resets backoff on successful reconnect', () => {
    const { result } = renderHook(() => useAgentState());
    // First connection opens then closes — triggers backoff reconnect
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      MockWebSocket.instances[0].triggerClose();
    });
    // Advance to trigger reconnect
    act(() => { vi.advanceTimersByTime(1500); });
    // Second connection opens successfully — backoff should reset
    act(() => {
      MockWebSocket.instances[1].triggerOpen();
    });
    expect(result.current.connected).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('closes WebSocket and cancels reconnect timer on unmount', () => {
    const { unmount } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
    });
    unmount();
    // After unmount, closing should not schedule another reconnect
    act(() => { vi.advanceTimersByTime(5000); });
    // Only the original instance — no reconnect after unmount
    expect(MockWebSocket.instances).toHaveLength(1);
  });
});
```

**Commit:** `tests: add useAgentState.test.ts — WebSocket lifecycle and reconnect logic`

---

### STEP 18 — Tests: `useApproval.test.ts`

**File:** `C:\ClaudeSkills\tests\AgenticOS\frontend\useApproval.test.ts`

```ts
// useApproval.test.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for useApproval — correct endpoints per decision,
//          per-agent loading state, error capture, and successful clear.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useApproval } from '../../../AgenticOS/frontend/src/hooks/useApproval';
import { ENDPOINTS } from '../../../AgenticOS/frontend/src/config';

// ─── fetch mock ───────────────────────────────────────────────────────────────

// Replace global fetch with a vi.fn() so we can control responses per test
const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

// Helper: make fetch resolve with a 200 OK response
function fetchOk() {
  mockFetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: 'OK' });
}

// Helper: make fetch resolve with a non-OK response
function fetchError(status = 500, statusText = 'Internal Server Error') {
  mockFetch.mockResolvedValueOnce({ ok: false, status, statusText });
}

// Helper: make fetch reject (network failure)
function fetchNetworkFailure() {
  mockFetch.mockRejectedValueOnce(new Error('Network request failed'));
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('useApproval', () => {
  it('starts with empty loading and error records', () => {
    const { result } = renderHook(() => useApproval());
    expect(result.current.loading).toEqual({});
    expect(result.current.error).toEqual({});
  });

  it('POSTs to /approve endpoint for proceed decision', async () => {
    fetchOk();
    const { result } = renderHook(() => useApproval());
    await act(async () => {
      await result.current.approve('AGENT-01', 'proceed');
    });
    expect(mockFetch).toHaveBeenCalledWith(
      ENDPOINTS.approve('AGENT-01'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ decision: 'proceed' }),
      })
    );
  });

  it('POSTs to /research endpoint for research decision', async () => {
    fetchOk();
    const { result } = renderHook(() => useApproval());
    await act(async () => {
      await result.current.approve('AGENT-01', 'research');
    });
    expect(mockFetch).toHaveBeenCalledWith(
      ENDPOINTS.research('AGENT-01'),
      expect.anything()
    );
  });

  it('POSTs to /review endpoint for review decision', async () => {
    fetchOk();
    const { result } = renderHook(() => useApproval());
    await act(async () => {
      await result.current.approve('AGENT-01', 'review');
    });
    expect(mockFetch).toHaveBeenCalledWith(
      ENDPOINTS.review('AGENT-01'),
      expect.anything()
    );
  });

  it('sets loading true during POST and false after', async () => {
    // Use a deferred promise so we can observe the loading state during the call
    let resolveRequest!: (value: { ok: boolean; status: number; statusText: string }) => void;
    mockFetch.mockReturnValueOnce(
      new Promise((res) => { resolveRequest = res; })
    );

    const { result } = renderHook(() => useApproval());

    // Start the POST — do not await yet
    let approvePromise: Promise<void>;
    act(() => {
      approvePromise = result.current.approve('AGENT-01', 'proceed');
    });

    // Loading must be true while in-flight
    expect(result.current.loading['AGENT-01']).toBe(true);

    // Resolve the fetch and wait for state to settle
    await act(async () => {
      resolveRequest({ ok: true, status: 200, statusText: 'OK' });
      await approvePromise;
    });

    // Loading must be false after completion
    expect(result.current.loading['AGENT-01']).toBe(false);
  });

  it('captures HTTP error in per-agent error record', async () => {
    fetchError(404, 'Not Found');
    const { result } = renderHook(() => useApproval());
    await act(async () => {
      await result.current.approve('AGENT-02', 'proceed');
    });
    expect(result.current.error['AGENT-02']).toMatch(/404/);
  });

  it('captures network failure in per-agent error record', async () => {
    fetchNetworkFailure();
    const { result } = renderHook(() => useApproval());
    await act(async () => {
      await result.current.approve('AGENT-03', 'proceed');
    });
    expect(result.current.error['AGENT-03']).toMatch(/Network request failed/);
  });

  it('clears previous error on the next successful POST', async () => {
    // First call fails
    fetchError();
    const { result } = renderHook(() => useApproval());
    await act(async () => { await result.current.approve('AGENT-01', 'proceed'); });
    expect(result.current.error['AGENT-01']).not.toBeNull();

    // Second call succeeds — error for that agent must be cleared
    fetchOk();
    await act(async () => { await result.current.approve('AGENT-01', 'proceed'); });
    expect(result.current.error['AGENT-01']).toBeNull();
  });

  it('tracks loading state independently per agent', async () => {
    // Two agents, only AGENT-01 posts — AGENT-02 must not show loading
    fetchOk();
    const { result } = renderHook(() => useApproval());
    await act(async () => {
      await result.current.approve('AGENT-01', 'proceed');
    });
    // AGENT-02 was never called — its loading entry must be undefined (falsy)
    expect(result.current.loading['AGENT-02']).toBeUndefined();
  });
});
```

**Commit:** `tests: add useApproval.test.ts — endpoint routing, loading, error, isolation`

---

### STEP 19 — Create `public/spline/` directory placeholder

The `public/spline/` directory must exist before `npm run build` so Vite copies it to `dist/`. Create a `.gitkeep` file inside it.

**File:** `C:\ClaudeSkills\AgenticOS\frontend\public\spline\.gitkeep`

Content: empty file. The Spline `.splinecode` scene file is added in Plan 4.

**Commit:** `scaffold: add public/spline/.gitkeep placeholder for Plan 4 Spline scene`

---

### STEP 20 — Install, typecheck, and run tests

```bash
cd C:\ClaudeSkills\AgenticOS\frontend

# Install all dependencies declared in package.json
npm install

# TypeScript strict mode check — must pass with zero errors before any commit
npm run typecheck

# Run the full test suite — all 3 test files, all assertions must pass
npm test

# Start dev server to visually verify card layout in browser
npm run dev
```

Expected results:
- `npm run typecheck` exits with code 0
- `npm test` reports: `AgentCard.test.tsx` 13 passed, `useAgentState.test.ts` 6 passed, `useApproval.test.ts` 8 passed
- `npm run dev` opens at `http://localhost:5173` — app renders with connection indicator showing "CONNECTING…" until FastAPI (Plan 2) is running

**Commit:** `verified: frontend typecheck and all tests passing`

---

### STEP 21 — Production build verification

```bash
cd C:\ClaudeSkills\AgenticOS\frontend

# Build to dist/ — FastAPI will serve this at /app
npm run build

# Verify dist/ was created and contains index.html
ls dist/
```

Expected: `dist/index.html`, `dist/assets/` with hashed JS and CSS bundles, `dist/spline/` directory. FastAPI (Plan 2) must be configured to serve `dist/` as a StaticFiles mount at `/app`.

**Commit:** `build: production dist verified — ready for FastAPI StaticFiles mount`

---

## Commit Sequence Summary

| Step | Commit message |
|------|---------------|
| 1 | `scaffold: add package.json for AgenticOS frontend` |
| 2 | `scaffold: add tsconfig.json (strict mode, path aliases)` |
| 3 | `scaffold: add vite.config.ts with FastAPI proxy and vitest config` |
| 4 | `scaffold: add index.html and main.tsx entry point` |
| 5 | `config: add src/config.ts — all URLs, theme, constants` |
| 6 | `types: add src/types/agent.ts — full AgentState interface` |
| 7 | `hooks: add useAgentState — WebSocket connection with exponential backoff` |
| 8 | `hooks: add useApproval — per-agent POST with loading and error state` |
| 9 | `component: add StatusBadge — colored status dot and label` |
| 10 | `component: add ContextMeter — animated context window gauge bar` |
| 11 | `component: add ReviewerPanel — auto-expanding verdict display` |
| 12 | `component: add ApprovalButtons — PROCEED / RESEARCH MORE / REVIEW BY AGENT` |
| 13 | `component: add SonarHUD placeholder — final API, Spline wired in Plan 4` |
| 14 | `component: add AgentCard — full instrument panel card composition` |
| 15 | `app: add App.tsx root component and App.css global theme tokens` |
| 16 | `tests: add AgentCard.test.tsx — 13 unit tests covering render, gate, approval, reviewer` |
| 17 | `tests: add useAgentState.test.ts — WebSocket lifecycle and reconnect logic` |
| 18 | `tests: add useApproval.test.ts — endpoint routing, loading, error, isolation` |
| 19 | `scaffold: add public/spline/.gitkeep placeholder for Plan 4 Spline scene` |
| 20 | `verified: frontend typecheck and all tests passing` |
| 21 | `build: production dist verified — ready for FastAPI StaticFiles mount` |

---

## Integration Contract for Plan 2 (FastAPI)

The frontend expects these from `agentic_server.py`:

| Endpoint | Method | Body | Success response |
|----------|--------|------|-----------------|
| `ws://localhost:7842/ws` | WS | — | JSON array of `AgentState[]` on every state change |
| `/approve/{agent_id}` | POST | `{"decision": "proceed"}` | HTTP 200 |
| `/research/{agent_id}` | POST | `{"decision": "research"}` | HTTP 200 |
| `/review/{agent_id}` | POST | `{"decision": "review"}` | HTTP 200 |

FastAPI must serve `frontend/dist/` at `/app` via `StaticFiles`.

CORS must allow `http://localhost:5173` (Vite dev) and `http://localhost:7842` (production).

---

## Integration Contract for Plan 4 (Spline)

`SonarHUD.tsx` is the only file that changes in Plan 4. The component API is already final:

```tsx
<SonarHUD
  progressPct={agent.progress_pct}   // 0–100 → depth gauge needle
  status={agent.status}              // → sonar ring pulse rate
  agentId={agent.agent_id}           // → Spline variable namespace prefix
/>
```

Plan 4 replaces the placeholder `<div>` inside `SonarHUD.tsx` with a `<Spline>` component. No other files change.

---

## Self-Review

### Spec Coverage

| Spec requirement | Covered |
|---|---|
| `config.ts` with all URLs, ports, colors | Yes — Step 5 |
| `agent.ts` with `AgentState`, `ApprovalDecision`, `AgentStatus`, `AgentDomain` | Yes — Step 6 |
| `useAgentState` — connect, reconnect backoff, agents[], connected, error | Yes — Step 7 |
| `useApproval` — approve(), loading Record, error Record | Yes — Step 8 |
| `StatusBadge` — colored dot + label per status | Yes — Step 9 |
| `ContextMeter` — gauge bar with threshold colors | Yes — Step 10 |
| `ReviewerPanel` — hidden until verdict, auto-expand | Yes — Step 11 |
| `ApprovalButtons` — three buttons, gate logic, loading, error | Yes — Step 12 |
| `SonarHUD` — placeholder with final API | Yes — Step 13 |
| `AgentCard` — full card composition matching layout spec | Yes — Step 14 |
| `App.tsx` — grid, WebSocket owner, status bar | Yes — Step 15 |
| `App.css` — CSS variables for all theme tokens | Yes — Step 15 |
| Vitest + RTL tests for AgentCard | Yes — Step 16 (13 tests) |
| Vitest tests for useAgentState | Yes — Step 17 (6 tests) |
| Vitest tests for useApproval | Yes — Step 18 (8 tests) |
| `vite.config.ts` proxy for `/api` and `/ws` | Yes — Step 3 |
| TypeScript strict mode | Yes — Steps 2, 3 |
| File header on every file | Yes — all files |
| Single-line comments on all non-obvious lines | Yes — all files |
| Zero hardcoded values | Yes — all values in config.ts |
| Named constants only | Yes — THEME, STATUS_LABELS, ENDPOINTS, etc. |
| `public/spline/` directory created | Yes — Step 19 |
| `npm run dev`, `npm run build`, `npm test` commands | Yes — package.json Step 1 |

### Placeholder Scan

- `SonarHUD.tsx` — intentional placeholder per spec ("Spline wired in Plan 4"). Label text inside the component makes it obvious.
- No other placeholders, TODOs, or unfinished sections found.

### Type Consistency

- `AgentStatus` — used in `agent.ts`, `StatusBadge.tsx`, `ApprovalButtons.tsx`, `SonarHUD.tsx`, `AgentCard.tsx`, `config.ts` (STATUS_LABELS, STATUS_COLORS) — all consistent.
- `ApprovalDecision` — used in `agent.ts`, `useApproval.ts`, `ApprovalButtons.tsx`, `AgentCard.tsx` — all consistent.
- `AgentDomain` — used in `agent.ts`, `config.ts` (DOMAIN_LABELS), `AgentCard.tsx` — all consistent.
- `AgentState` — used in `useAgentState.ts`, `useApproval.ts`, `AgentCard.tsx`, all test fixtures — all consistent.
- `ApprovalPayload` — defined in `agent.ts`, consumed in `useApproval.ts` — consistent.

---

## Next Steps

Spawn the **reviewer** agent to validate this plan. The reviewer should check:

1. All 21 steps are achievable in 2–5 minutes each without ambiguity
2. The WebSocket mock in `useAgentState.test.ts` correctly simulates all lifecycle events
3. The `vite.config.ts` proxy configuration correctly handles both `/api` REST and `/ws` WebSocket in dev mode
4. `App.css` CSS custom properties exactly match the hex values in `config.ts` THEME constants
5. `SonarHUD.tsx` props are exactly what Plan 4 will need to bind Spline variables
6. The `AgentCard` layout matches the instrument panel spec from the design doc (Section 6)
7. No file in this plan imports from `agentic_server.py` or any Plan 2 artifact — frontend is fully self-contained
