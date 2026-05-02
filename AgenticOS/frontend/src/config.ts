// config.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Single source of truth for every URL, port, timeout, message
//          discriminator, and layout constant the React frontend uses.
//          Mirrors values from AgenticOS/config.py and AgenticOS/models.py;
//          if the Python side changes, the matching constant here must be
//          updated in the same commit. Nothing in src/ may hardcode any
//          value that conceivably differs between environments or releases.

// ---------------------------------------------------------------------------
// Server endpoints
//
// FastAPI binds a single port for both REST and WebSocket. The host is
// loopback-only (see SERVER_HOST in AgenticOS/config.py); the dev server
// proxies /api and /ws so client code never needs to know which mode it
// runs in.
// ---------------------------------------------------------------------------

// Mirror of AgenticOS.config.WEBSOCKET_PORT. Must stay in sync; the dev
// proxy in vite.config.ts also mirrors this number for the same reason.
export const FASTAPI_PORT = 7842 as const;

// Loopback host. Mirror of AgenticOS.config.SERVER_HOST. We bias toward
// 127.0.0.1 because some Windows configurations resolve "localhost" to ::1
// and FastAPI binds IPv4 by default.
export const FASTAPI_HOST = '127.0.0.1' as const;

// Full WebSocket URL for the live state bus. Hooks build their socket from
// this constant; never construct ws:// URLs at the call site.
export const WS_URL = `ws://${FASTAPI_HOST}:${FASTAPI_PORT}/ws` as const;

// REST base URL for approval decision POSTs. ENDPOINTS below appends path
// segments; we keep the base separate so a future reverse proxy could swap
// it for a relative origin.
export const REST_BASE = `http://${FASTAPI_HOST}:${FASTAPI_PORT}` as const;

// REST endpoint builders. Take the agent_id (always a string in the
// Pydantic schema) and return a fully-qualified URL. Centralizing these
// keeps fetch call sites free of string interpolation.
export const ENDPOINTS = {
  approve: (agentId: string): string => `${REST_BASE}/approve/${agentId}`,
  research: (agentId: string): string => `${REST_BASE}/research/${agentId}`,
  review: (agentId: string): string => `${REST_BASE}/review/${agentId}`,
  skillActions: (projectPath?: string): string => {
    const query = projectPath ? `?project_path=${encodeURIComponent(projectPath)}` : '';
    return `${REST_BASE}/skill-actions${query}`;
  },
  runSkillAction: (slug: string): string =>
    `${REST_BASE}/skill-actions/${encodeURIComponent(slug)}/run`,
  taskSnapshot: (): string => `${REST_BASE}/tasks/snapshot`,
  terminals: (): string => `${REST_BASE}/terminals`,
  terminalFocus: (hwnd: number): string => `${REST_BASE}/terminals/${hwnd}/focus`,
  terminalClose: (hwnd: number): string => `${REST_BASE}/terminals/${hwnd}/close`,
  terminalTerminate: (pid: number): string => `${REST_BASE}/terminals/${pid}/terminate`,
  workflowEvents: (since = 0, workflowId?: string): string => {
    const params = new URLSearchParams({ since: String(since) });
    if (workflowId !== undefined) params.set('workflow_id', workflowId);
    return `${REST_BASE}/workflow-events?${params.toString()}`;
  },
} as const;

// Operator terminal panel refresh cadence. This is a dashboard sampling
// interval only; filesystem coordination remains watchdog/event-driven.
export const TERMINAL_PANEL_REFRESH_MS = 6_000 as const;
export const TERMINAL_TERMINATE_CONFIRMATION = 'TERMINATE' as const;

// ---------------------------------------------------------------------------
// WebSocket message discriminators
//
// Plan 3 broadcasts a full snapshot on connect and a diff on each change.
// The discriminator field is "type" so we can model the wire shape as a
// TypeScript discriminated union without inventing a runtime tag scheme.
// ---------------------------------------------------------------------------

// Sent immediately after the WebSocket opens. Carries the entire current
// agents map so the client can render without waiting for the next change.
export const MESSAGE_TYPE_SNAPSHOT = 'snapshot' as const;

// Sent on every state mutation. Carries adds, updates, and removes only.
export const MESSAGE_TYPE_DIFF = 'diff' as const;

// ---------------------------------------------------------------------------
// WebSocket reconnect policy
//
// Why exponential backoff: the server may be restarting, the laptop may
// have just woken from sleep, or the user may have closed and reopened the
// app. A flat retry interval hammers the server during outages; an
// unbounded backoff makes the UI feel dead. Doubling capped at 30s is the
// industry default for this exact tradeoff.
// ---------------------------------------------------------------------------

// First reconnect delay after an unexpected close, in milliseconds.
export const WS_RECONNECT_BASE_MS = 1_000 as const;

// Upper bound on the reconnect delay. Doubling stops here.
export const WS_RECONNECT_MAX_MS = 30_000 as const;

// ---------------------------------------------------------------------------
// Approval POST policy
//
// Idempotency key prevents accidental double-posts when the user clicks a
// gate button twice or the network retries. The key is generated client
// side and sent in the X-Idempotency-Key header; the server is expected to
// dedupe on it.
// ---------------------------------------------------------------------------

// HTTP header name for the per-request idempotency key. Constant so the
// hook and the server stay in agreement on the spelling.
export const IDEMPOTENCY_HEADER = 'X-Idempotency-Key' as const;

// ---------------------------------------------------------------------------
// Capacity ceilings
//
// The grid is responsive but the FastAPI broadcaster has hard limits to
// keep memory bounded. MAX_AGENT_SLOTS is the upper bound of agents the UI
// will render; further entries are dropped with a console warning. This
// mirrors a similar cap on the server side that the spec calls for.
// ---------------------------------------------------------------------------

// Maximum agents rendered in the grid simultaneously. Plan 4 may raise it.
export const MAX_AGENT_SLOTS = 32 as const;

// ---------------------------------------------------------------------------
// Status and domain display mappings
//
// The Python AgentStatus / AgentDomain enums use snake_case and kebab-case
// values. The UI wants UPPERCASE labels and themed colors. We map both
// here in one place so a new enum value only needs an entry in this table.
// ---------------------------------------------------------------------------

// Human-readable status labels for the StatusPill. Keys mirror
// AgenticOS.models.AgentStatus values exactly.
export const STATUS_LABELS = {
  active: 'ACTIVE',
  waiting_approval: 'WAITING APPROVAL',
  waiting_review: 'WAITING REVIEW',
  complete: 'COMPLETE',
  error: 'ERROR',
} as const;

// Human-readable domain labels. Keys mirror AgenticOS.models.AgentDomain
// values exactly.
export const DOMAIN_LABELS = {
  'va-advisory': 'VA-ADVISORY',
  'game-dev': 'GAME-DEV',
  'software-eng': 'SOFTWARE-ENG',
  '3d-content': '3D-CONTENT',
  general: 'GENERAL',
} as const;

// ---------------------------------------------------------------------------
// Context meter thresholds
//
// Two named thresholds drive the meter color. Below WARN it is gold; from
// WARN to CRIT it is amber; at and above CRIT it is red. Centralizing the
// numbers makes the policy reviewable in one place.
// ---------------------------------------------------------------------------

// Above this percentage the context meter renders amber (warning).
export const CONTEXT_WARN_PCT = 70 as const;

// At or above this percentage the context meter renders red (critical).
export const CONTEXT_CRIT_PCT = 90 as const;

// ---------------------------------------------------------------------------
// Status colors — adopted from DeveloperProductivityTracker GetWellnessStatusColor()
//
// Each AgentStatus maps to the same color used by the tracker's activity
// state system: Active=gold, Away/waiting=amber, Review=teal, Complete=green,
// Error=red. Mirrors CSS token values in tokens.css exactly.
// ---------------------------------------------------------------------------

// CSS hex color per agent status. Components read this rather than
// hardcoding hex values, keeping the palette centralized in one table.
export const STATUS_COLORS = {
  active:           '#C9A94E', // gold — instrument panel active glow
  waiting_approval: '#F39C12', // amber — attention required, gate open
  waiting_review:   '#4DB6AC', // teal — external reviewer in progress
  complete:         '#27AE60', // green — mission accomplished
  error:            '#C0392B', // red — halt and investigate
} as const satisfies Record<string, string>;

// Sonar ring pulse durations per status (CSS animation-duration values).
// Maps to the Spline state machine pulse rates in public/spline/README.md.
export const STATUS_PULSE_MS = {
  active:           500,   // fast pulse — agent is working
  waiting_approval: 2000,  // slow pulse — waiting on human
  waiting_review:   750,   // double-pulse approximated as fast
  complete:         0,     // no pulse — solid ring
  error:            100,   // rapid flash — alert
} as const satisfies Record<string, number>;

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

// Minimum grid card width in pixels. The CSS grid in App.css uses this
// constant via a CSS custom property to stay in lockstep.
export const CARD_MIN_WIDTH_PX = 360 as const;

// ---------------------------------------------------------------------------
// Phase 2 expansion (2026-04-29) -- view modes, neural-brain layout,
// terminal stream, progress log endpoints. Centralized so no component
// hardcodes any of these literals.
// ---------------------------------------------------------------------------

// LocalStorage key used by ViewModeToggle to persist the user's choice
// across sessions. Versioned so a future schema change can migrate.
export const VIEW_MODE_STORAGE_KEY = 'agenticos:view-mode' as const;

// View mode literal union. The UI renders the AgentCard grid in 'grid'
// mode and the NeuralBrainView in 'brain' mode.
export const VIEW_MODES = ['grid', 'brain'] as const;
export type ViewMode = typeof VIEW_MODES[number];
export const DEFAULT_VIEW_MODE: ViewMode = 'grid';

// d3-force simulation tuning. Centralized so a designer can tweak the
// brain layout density without touching the component file.
export const FORCE_LINK_DISTANCE_PX = 90 as const;
export const FORCE_CHARGE_STRENGTH = -180 as const;
export const FORCE_CENTER_X_RATIO = 0.5 as const;
export const FORCE_CENTER_Y_RATIO = 0.5 as const;
export const FORCE_RADIUS_PX = 28 as const;

// Neural-brain canvas dimensions. The Spline scene renders in the
// background and the SVG overlay sizes itself to match.
export const BRAIN_CANVAS_WIDTH_PX = 1200 as const;
export const BRAIN_CANVAS_HEIGHT_PX = 700 as const;

// Status -> hex color mapping for the brain nodes. Mirrors STATUS_COLORS
// above but separated because the brain mode adds 'stuck' as a distinct
// pulsing-red treatment that the grid does not need.
export const BRAIN_NODE_COLORS = {
  active: '#C9A94E',
  waiting_approval: '#F39C12',
  waiting_review: '#4DB6AC',
  complete: '#27AE60',
  error: '#C0392B',
  stuck: '#E74C3C',
  looping: '#FF6B35',
} as const;

// Spline scene path for the neural-brain background. Same convention
// as SonarHUD: served from /spline/ in dev and prod.
export const BRAIN_SPLINE_SCENE_PATH = '/spline/neural-brain.splinecode' as const;

// Terminal stream cap. The TerminalStreamPanel keeps at most this many
// lines in memory and trims the head on overflow. 2000 mirrors the spec.
export const TERMINAL_STREAM_MAX_LINES = 2000 as const;

// SSE endpoint builder. Returns the full URL to the per-agent stream.
export const SSE_ENDPOINTS = {
  agentStream: (agentId: string): string =>
    `${REST_BASE}/agents/${encodeURIComponent(agentId)}/stream`,
} as const;

// Progress log REST endpoint builder. seq=0 returns the entire log.
export const PROGRESS_ENDPOINT = (since: number): string =>
  `${REST_BASE}/progress?since=${since}`;
