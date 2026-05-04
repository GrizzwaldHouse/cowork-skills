// agentic-os-architecture.md / Developer: Marcus Daley / Date: 2026-04-30
// Description: Technical reference for the Agentic OS Electron dashboard architecture.

# Agentic OS — Architecture Reference

## 1. Overview

Agentic OS is a local Electron desktop dashboard for monitoring and interacting with AI agent pipelines. It is built for a single operator who needs real-time visibility into multi-agent orchestration runs: which agents are running, what phase the pipeline is in, what tool calls are waiting for approval, and how far along overall progress is. The problem it solves is the opacity of headless agent processes — without a live dashboard, pipeline state exists only in terminal output. Agentic OS surfaces that state into a structured UI with a Spline 3D background that reflects live pipeline activity, a phase strip showing pipeline stage progression, per-agent status cards, a tool-approval overlay for human-in-the-loop decisions, and an activity log.

---

## 2. Process Architecture

Electron runs three isolated processes for every application window. Agentic OS uses all three with strict boundaries between them.

### Main Process (`main.js`)

The main process is the privileged Node.js process that owns the OS integration layer. In Agentic OS it performs three responsibilities:

- **BrowserWindow creation** — `createWindow()` instantiates a 1100×780 frameless, transparent window with `contextIsolation: true`, `nodeIntegration: false`, and `sandbox: false`. The `preload.js` path is passed via `webPreferences.preload`.
- **IPC handler registration** — `registerIpcHandlers()` calls `require('./src/ipc-handlers')` and passes `ipcMain` to it. This is done before `createWindow()` so all channels exist before the renderer makes its first `invoke` call. If `ipc-handlers.js` is absent (MODULE_NOT_FOUND), a warning is logged and the app continues with a degraded IPC surface rather than crashing.
- **Session directory management** — the main process indirectly owns the `data/sessions.json` flat file via `session-manager.js`, which is required synchronously by `ipc-handlers.js` at module load time.

The main process also handles platform-specific quit behaviour: on non-macOS platforms the app quits when all windows are closed; on macOS it stays alive until Cmd+Q.

### Preload Script (`preload.js`)

The preload script runs inside the renderer process but has access to Node.js and Electron APIs. Its sole job is to construct a narrow, typed IPC surface and expose it to renderer page scripts via `contextBridge.exposeInMainWorld`. The raw `ipcRenderer` object is never placed on `window` — only the five named methods below are exposed as `window.dashboard`:

| Method | Underlying channel | Description |
|---|---|---|
| `readState()` | `state:read` (invoke) | Fetches the full current state from the main process as a JSON string. Called once on startup by `ipc.js` to seed `AgentState`. |
| `onStateUpdated(callback)` | `state:updated` (on) | Registers a callback for state push events from the main process. Removes all prior listeners before registering to prevent accumulation across reloads. |
| `approveAction(agentId, action)` | `action:approve` (invoke) | Submits a user approval for a pending agent action. Clears `pendingAction` in main-process state. |
| `decideTool(decision)` | `tool:decide` (invoke) | Submits a tool-use decision (approve or reject) for a pending tool call. |
| `advancePhase()` | `phase:advance` (invoke) | Manually increments the pipeline phase index on the main process. |

### Renderer Process (`renderer/`)

The renderer process is a Chromium page that cannot access Node.js directly. It loads five JS modules via plain `<script>` tags in `index.html` and communicates with the main process exclusively through `window.dashboard`. The five modules and their responsibilities are:

- **`scripts/state.js`** — owns `window.AgentState`, the single source of truth for all renderer state. All mutations go through `setState()`. Subscribers are notified synchronously after every mutation.
- **`scripts/render.js`** — owns all DOM writes. Subscribes to `AgentState`, calls `renderAll()` on every state change, and registers all event delegation listeners once at init time.
- **`scripts/ipc.js`** — bridges main-process state into `AgentState`. Pulls initial state via `readState()` on startup, then registers the `onStateUpdated` push subscription.
- **`scripts/spline.js`** — subscribes to `AgentState` and pushes four derived variables (`phase`, `phaseProgress`, `agentCount`, `hasAlert`) into the `<spline-viewer>` custom element after every state change.
- **`scripts/actions.js`** — owns `window.AgentActions`. Handles user interactions (approve, reject, advance phase) by calling `window.dashboard` IPC methods and applying optimistic local state updates via `AgentState`.

---

## 3. IPC Channel Reference

All channels except `state:updated` are invokable (renderer calls `ipcRenderer.invoke`, main process uses `ipcMain.handle`). `state:updated` is a push channel (main process sends, renderer listens).

| Channel | Direction | Purpose |
|---|---|---|
| `state:read` | renderer → main | Returns the full `_state` as a JSON string. Called once on startup to seed renderer state. |
| `state:write` | renderer → main | Shallow-merges a partial object into `_state` and broadcasts the updated state to all windows. |
| `action:approve` | renderer → main | Clears `pendingAction` on the named agent in `_state.agents` and broadcasts. |
| `tool:decide` | renderer → main | Records a tool-use decision (approve or reject). Logs the decision; returns `'acknowledged'`. |
| `phase:advance` | renderer → main | Increments `_state.phase` by 1, clamped to `phases.length - 1`. Returns the new phase index. |
| `session:start` | renderer → main | Creates a new session record with `outcome: 'in-progress'` and persists it via `session-manager`. Returns the new session id. |
| `session:end` | renderer → main | Stamps `endTime`, `tasksCompleted`, and `outcome` on an existing session. Attempts skill artifact generation. Returns `'ok'` or `'not-found'`. |
| `state:updated` | main → renderer | Push event broadcast by `_broadcastState()` after every `_state` mutation. Payload is the full `_state` object. |

---

## 4. State Shape

`AgentState` maintains a single canonical `_state` object in `state.js`. Mutations are only permitted through `setState()`, `addLogEntry()`, `updateAgent()`, `setPhaseProgress()`, and `recalcOverallProgress()`. `getState()` always returns a deep copy via JSON round-trip.

| Key | Type | Description |
|---|---|---|
| `phase` | `number` | Zero-based index of the currently active pipeline phase. Authoritative copy lives in `_state` on the main process; renderer mirrors it via IPC push. |
| `phases` | `Array<{ name: string, status: 'pending'\|'active'\|'completed', progress: number }>` | Ordered list of pipeline phase descriptors. `progress` is 0–100 per phase. `status` reflects whether the phase is waiting, executing, or finished. |
| `agents` | `Array<{ id: string, name: string, status: 'idle'\|'running'\|'blocked'\|'done'\|'error', task: string, progress: number, pendingAction: string\|null }>` | All agents participating in the current run. `pendingAction` is non-null when the agent is waiting for user approval. `progress` is 0–100 task-level completion. |
| `log` | `Array<{ ts: string, type: 'user'\|'agent'\|'warn'\|'err', message: string }>` | Bounded activity log capped at 200 entries (oldest dropped via `shift()` when exceeded). `ts` is an ISO 8601 timestamp. |
| `toolApproval` | `{ agentId: string, action: string, description: string } \| null` | Populated when an agent requests permission for a tool call requiring user confirmation. Drives the tool-approval overlay in the renderer. `null` when no approval is pending. |
| `overallProgress` | `number` | 0–100 mean of all `phases[i].progress` values. Recomputed by `recalcOverallProgress()`. Drives the SVG progress ring widget. |

---

## 5. Renderer Module Map

| Module | `window.*` export | Single responsibility |
|---|---|---|
| `scripts/state.js` | `window.AgentState` | Canonical renderer state store — owns `_state`, mutation methods, and subscriber notification |
| `scripts/render.js` | `window.renderAll`, `window.renderAgents`, `window.renderPhaseStrip`, `window.renderOverall`, `window.renderLog`, `window.renderToolApproval`, `window.escHtml`, `window.initRenderer` | All DOM writes — maps state slices to innerHTML and manages event delegation |
| `scripts/ipc.js` | `window.initIpc` | IPC bridge — pulls initial state from main process and maintains push subscription via `window.dashboard` |
| `scripts/spline.js` | `window.syncSplineState`, `window.initSpline` | Spline 3D sync — derives four scene variables from state and calls `viewer.setVariables()` fire-and-forget |
| `scripts/actions.js` | `window.AgentActions` | User action handlers — sends IPC calls to main process and applies optimistic local state updates |

---

## 6. Data Flow: State Update Cycle

The following sequence describes how a state change on the main process propagates through to the Spline 3D scene. The same cycle applies whether the change originates from a renderer IPC call (e.g. `action:approve`) or from a future main-process service writing to `_state` directly.

1. An external caller (renderer via `window.dashboard`, or a main-process service) triggers a `_state` mutation in `ipc-handlers.js`. For example, `state:write` receives a partial object and calls `Object.assign(_state, partial)`.

2. `ipc-handlers.js` calls `_broadcastState()`, which iterates `BrowserWindow.getAllWindows()` and calls `win.webContents.send('state:updated', _state)` on every non-destroyed window. The payload is the full `_state` object, not a delta.

3. In the renderer, `preload.js` has registered an `ipcRenderer.on('state:updated', ...)` listener (set up via `window.dashboard.onStateUpdated` in `ipc.js`). The listener fires and calls `window.AgentState.setState(state)` with the pushed payload.

4. `AgentState.setState()` calls `Object.assign(_state, partial)` to merge the update, then calls `_notifySubscribers()`. `_notifySubscribers()` iterates `_subscribers`, calls each registered callback with `getState()` (a deep copy), and swallows individual subscriber errors so one broken subscriber cannot silence others.

5. `render.js` subscribed to `AgentState` during `initRenderer()` with `AgentState.subscribe(onStateChange)`. Its `onStateChange` callback calls `renderAll(state)`, which dispatches the state snapshot to `renderAgents()`, `renderPhaseStrip()`, `renderOverall()`, `renderLog()`, and `renderToolApproval()`. Each function replaces its target element's `innerHTML` with freshly generated markup. Event delegation listeners on persistent parent elements survive innerHTML replacement.

6. `spline.js` also subscribed to `AgentState` during `initSpline()`. Its subscriber callback calls `syncSplineState(state)`, which calls `deriveSplineVars(state)` to compute `{ phase, phaseProgress, agentCount, hasAlert }` and then calls `viewer.setVariables(vars)` on the `<spline-viewer id="spline-bg">` element. This call is fire-and-forget — neither the returned Promise nor any error is propagated. If the viewer element is absent or not yet upgraded, `syncSplineState()` exits silently at a debug-level log.

---

## 7. Session Persistence

`session-manager.js` provides an in-memory session cache backed by a JSON flat file at `<app-root>/data/sessions.json`. It is required synchronously by `ipc-handlers.js` at module load time.

**Storage location:** `data/sessions.json` relative to the `agentic-os` app root. The `data/` directory is created with `fs.mkdirSync({ recursive: true })` at module load if it does not exist.

**File format:** A JSON array of session record objects, pretty-printed with 2-space indentation. One record per session. Example record shape:

```js
// Session record stored in data/sessions.json
{
  "id": "1746000000000",         // Date.now().toString() at creation
  "startTime": "2026-04-30T...", // ISO 8601
  "endTime": "2026-04-30T...",   // ISO 8601, or null if still in-progress
  "agentName": "implementer",    // primary agent for this session
  "tasksCompleted": 4,
  "tasksPlanned": 5,
  "skillsUsed": ["beta-team"],
  "outcome": "success"           // 'in-progress' | 'success' | 'partial' | 'failed'
}
```

**`startSession` (via `session:start` IPC channel):** Called when an orchestration run begins. Builds a record with `outcome: 'in-progress'` and a unique id (`Date.now().toString()`), calls `sessionManager.addSession(record)`, which pushes it to `_sessions` and calls `_persist()` synchronously. Returns the session id.

**`endSession` (via `session:end` IPC channel):** Called when a run completes. Calls `sessionManager.updateSession(id, { endTime, tasksCompleted, outcome })`, which finds the record by id, shallow-merges the partial update with `Object.assign`, and calls `_persist()`. If the id is not found, returns `'not-found'`. After a successful update, attempts to call `skill-artifact.generateArtifacts()` — this is loaded lazily and swallowed on MODULE_NOT_FOUND so a missing artifact module never blocks session closure.

**`getSession(id)`:** Returns the live session record from `_sessions` by id, or `null` if not found. Callers needing an immutable snapshot must JSON-clone the result.

`_persist()` uses `fs.writeFileSync` (synchronous) so the file is flushed before the IPC handler returns. Write errors are caught and logged but never thrown — sessions remain in memory for the process lifetime if the file write fails.

---

## 8. Security Model

### `contextIsolation: true` / `nodeIntegration: false`

`contextIsolation: true` means the renderer page's JavaScript world is isolated from the preload script's world. Renderer scripts cannot access Node.js globals (`require`, `process`, `Buffer`) or reach back through the `contextBridge` API to the preload scope. Even if a malicious script were injected into the renderer (e.g. via a compromised Spline asset), it could not call `ipcRenderer` directly or read the file system. `nodeIntegration: false` reinforces this by removing the Node.js module system from the renderer's global scope entirely. The only IPC surface available to renderer scripts is the five methods on `window.dashboard`, which were explicitly defined and copied into the isolated context by `contextBridge.exposeInMainWorld`.

### CSP meta tag in `index.html`

The Content Security Policy is delivered as a `<meta http-equiv="Content-Security-Policy">` tag in `renderer/index.html`. It permits the following origins and nothing else:

| Directive | Permitted origins | Reason |
|---|---|---|
| `default-src` | `'self'` | Blocks all unlisted origins by default |
| `script-src` | `'self'` `https://unpkg.com` | Allows local scripts and the Spline viewer web component from unpkg CDN |
| `connect-src` | `'self'` `https://prod.spline.design` `https://unpkg.com` | Allows Spline scene file and asset fetches from Spline's CDN |
| `style-src` | `'self'` `'unsafe-inline'` | Local stylesheets plus inline `style=` attributes used on `<spline-viewer>` and `<div id="app">` |
| `img-src` | `'self'` `data:` `blob:` | Local images, data URIs, and blob URLs (used by Spline for texture assets) |
| `font-src` | `'self'` | Local fonts only |
| `worker-src` | `blob:` | Spline runtime spawns a Web Worker via a blob URL to parse the scene off the main thread |

No inline scripts are permitted by `script-src` — only `'self'` and `https://unpkg.com`. All five renderer JS modules are loaded as external file references, not inline.

### `sandbox: false` exception

`sandbox: false` is set in the `webPreferences` of the main BrowserWindow. This is required because the preload script (`preload.js`) calls `require('electron')` to access `contextBridge` and `ipcRenderer`. Electron's preload sandbox mode (introduced to align with Chromium's sandboxed renderer architecture) would strip `require` from the preload context. With `sandbox: false`, the preload retains Node.js access while the renderer page remains isolated via `contextIsolation: true`. The renderer itself has no `require` access because `nodeIntegration: false` is still enforced — `sandbox: false` only elevates the preload script, not the page.

---

## 9. Key Design Decisions

- **Plain `<script>` tags instead of a bundler.** The renderer is an Electron local HTML page loaded from the file system via `win.loadFile()`. There is no HTTP server, no module resolution chain, and no need for tree-shaking or code splitting in a single-window local tool. Using plain `<script>` tags eliminates the build step entirely, keeps the source files directly readable in DevTools, and reduces tooling dependencies. The load order defined in `index.html` (component factories first, then `state.js` → `render.js` → `ipc.js` → `spline.js` → `actions.js`) replaces the role that an import graph would play in an ES module setup.

- **Single-source-of-truth state + subscriber pattern.** All renderer state lives in `_state` inside `state.js` and is mutated only through the exported methods on `window.AgentState`. Every module that needs to react to state changes registers a subscriber via `AgentState.subscribe()` — render.js and spline.js both do this at init time. This is the Observer pattern: `AgentState` is the subject, the subscriber callbacks are the observers. It eliminates polling (`setInterval`, `refetchInterval`) and direct coupling between modules. A change in `ipc.js` calling `setState()` automatically propagates to the DOM (render.js) and the 3D scene (spline.js) without those modules needing to know about each other.

- **`_initialized` guard in `render.js`.** `initRenderer()` sets `_initialized = true` on first call and returns immediately on any subsequent call. This guard is necessary because Electron can navigate or reload the renderer process during development (DevTools reload, hot-module substitution workarounds, or future test harness injection). Without the guard, a second call to `initRenderer()` would add a second `AgentState` subscriber, causing every state mutation to trigger two `renderAll()` calls, and would re-bind the `addEventListener` delegation listeners, causing every approve or reject click to fire twice. The guard ensures the renderer's event wiring and subscriber registration each happen exactly once per page lifetime.

- **`typeof window.X === 'undefined'` guards on window globals.** Every renderer module that reads another module's `window.*` export guards the access with a `typeof` check before using it. For example, `render.js` checks `typeof window.agentCard !== 'function'` before calling it, and `actions.js` checks `typeof window.dashboard !== 'undefined'` before calling `approveAction`. These guards serve two purposes: they make the modules safe to evaluate independently (e.g. in a test harness that does not load all five scripts), and they defend against re-evaluation. If `actions.js` is evaluated more than once (Electron reload, test injection), the `typeof window.AgentActions === 'undefined'` guard at the bottom of the file prevents `window.AgentActions` from being replaced with a fresh object, preserving any references other modules may have already captured.
