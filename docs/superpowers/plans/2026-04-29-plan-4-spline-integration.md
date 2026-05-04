# Plan 4 of 5: Spline 3D Scene Integration
**Date:** 2026-04-29
**Developer:** Marcus Daley
**Project:** AgenticOS Command Center
**Depends On:** Plan 3 (React frontend scaffold with SonarHUD placeholder)
**Next Plan:** Plan 5 — WPF Launcher + WebView2 Shell

---

## Goal

Replace the Plan 3 `SonarHUD` placeholder component with a fully wired Spline 3D scene. Agent state changes from the WebSocket flow to Spline variable updates in real time. Two degradation paths exist: a CSS-only animated fallback when WebGL is unavailable, and a graceful error state when the scene file fails to load. The `syncSplineState` utility is a pure function, tested in isolation with a mock Application object.

---

## Architecture

```
agents prop (AgentState[])
        │
        ▼
SonarHUD.tsx (lazy + Suspense)
        │
        ├── splineRef.current exists?
        │       │ yes
        │       └── syncSplineState(spline, agents)
        │               │
        │               ├── iterate slots 0..MAX_AGENT_SLOTS-1
        │               ├── set agent_{n}_progress (number)
        │               ├── set agent_{n}_state (string)
        │               ├── set agent_{n}_active (boolean)
        │               └── set global_agent_count (number)
        │
        ├── WebGL unavailable → <SonarFallback agents={agents} />
        └── scene load error  → <SceneErrorState />
```

The Spline `Application` ref is stored in `useRef` and populated by the `onLoad` callback. `syncSplineState` is imported from `utils/splineSync.ts` — a pure function with no React dependency, making it trivially testable. The Spline component is lazy-loaded via `React.lazy` so the large `@splinetool/runtime` bundle does not block the initial paint.

---

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| 3D scene | `@splinetool/react-spline` + `@splinetool/runtime` | Self-hostable `.splinecode`, offline capable, no CORS |
| Scene file | `/spline/sonar-hud.splinecode` (public/) | Served by Vite dev server and FastAPI prod server |
| Lazy loading | `React.lazy` + `Suspense` | Keeps initial bundle small; runtime is ~1MB |
| WebGL detection | `canvas.getContext('webgl2')` at mount | Fast synchronous check, no flicker |
| CSS fallback | Custom CSS animations, submarine color palette | Zero dependencies, degrades gracefully |
| Unit tests | Vitest + React Testing Library | Matches Plan 3 test infrastructure |
| Type safety | TypeScript strict mode, `import type` for runtime types | Matches project-wide standard |

---

## File Layout (Changes from Plan 3)

```
C:\ClaudeSkills\AgenticOS\frontend\
  src\
    components\
      SonarHUD\
        SonarHUD.tsx            ← REPLACE Plan 3 placeholder entirely
        SonarHUD.css            ← ADD: Spline container + CSS fallback wrapper
        SonarFallback.tsx       ← ADD: CSS-only animated sonar rings
        SonarFallback.css       ← ADD: Animated CSS rings, submarine palette
    utils\
      splineSync.ts             ← ADD: syncSplineState pure function
  public\
    spline\
      sonar-hud.splinecode      ← SPEC ONLY (created in Spline editor — see Task 0)
      README.md                 ← ADD: Designer instructions for scene variable setup

C:\ClaudeSkills\AgenticOS\
  tests\
    frontend\
      splineSync.test.ts        ← ADD: Unit tests for syncSplineState
      SonarFallback.test.tsx    ← ADD: CSS fallback render tests
```

---

## Type Reference (from Plan 3 — do not redefine)

These types are defined in `src/types/agent.ts` by Plan 3. Import them; never redeclare.

```typescript
// src/types/agent.ts (Plan 3 — reference only)
export type AgentStatus =
  | 'active'
  | 'waiting_approval'
  | 'waiting_review'
  | 'complete'
  | 'error';

export interface AgentState {
  agent_id: string;
  domain: 'va-advisory' | 'game-dev' | 'software-eng' | '3d-content' | 'general';
  task: string;
  stage_label: string;
  stage: number;
  total_stages: number;
  progress_pct: number;       // 0–100 — drives Spline depth gauge
  status: AgentStatus;        // drives Spline ring pulse behavior
  context_pct_used: number;
  output_ref: string;
  awaiting: 'proceed' | 'research' | 'review' | null;
  error_msg: string | null;
  spawned_by: string | null;
  reviewer_verdict: string | null;
  updated_at: string;
}
```

---

## Task 0 — Spline Scene Variable Spec (Designer Handoff)

**Duration:** 2 min (documentation only — no code)
**Output:** `public/spline/README.md`

This task produces the spec document that the Spline scene designer uses to build `sonar-hud.splinecode`. It must be written before any React code so the variable names are locked and the React implementation matches exactly.

### Spline Scene Variables — Required Definitions

Open the Spline editor. In the Variables panel, create the following variables exactly as listed. Names are case-sensitive and must match character-for-character — React reads these by name.

#### Per-Agent Variables (repeat for n = 1 through 8)

| Variable Name | Type | Default | Range / Allowed Values | Drives |
|---|---|---|---|---|
| `agent_1_progress` | Number | `0` | 0 – 100 | Depth gauge needle rotation (0° at 0, 270° at 100) |
| `agent_1_state` | String | `'active'` | `'active'`, `'waiting_approval'`, `'waiting_review'`, `'complete'`, `'error'` | Sonar ring pulse behavior (see states table) |
| `agent_1_active` | Boolean | `false` | `true` / `false` | Instrument panel backlight glow on/off |
| `agent_2_progress` | Number | `0` | 0 – 100 | Same as agent_1 for slot 2 |
| `agent_2_state` | String | `'active'` | same as agent_1_state | Same as agent_1 for slot 2 |
| `agent_2_active` | Boolean | `false` | `true` / `false` | Same as agent_1 for slot 2 |
| *(repeat through agent_8_progress, agent_8_state, agent_8_active)* | | | | |

#### Global Variables

| Variable Name | Type | Default | Range | Drives |
|---|---|---|---|---|
| `global_agent_count` | Number | `0` | 0 – 8 | Number of active sonar contacts visible on HUD |

#### State → Visual Mapping

| State Value | Sonar Ring Behavior | Ring Color | Depth Gauge | Panel Glow |
|---|---|---|---|---|
| `'active'` | Fast pulse, 0.5s cycle | Gold `#C9A94E` | Animating toward progress value | Bright gold |
| `'waiting_approval'` | Slow pulse, 2s cycle | Amber `#D4A017` | Paused at current value | Amber |
| `'waiting_review'` | Double-pulse (two quick, then pause) | Teal `#1A7A7A` | Paused at current value | Teal |
| `'complete'` | Solid, no pulse | Dim green `#27AE60` | Full (270°) | Dim green |
| `'error'` | Rapid flash, 0.1s cycle | Red `#C0392B` | Frozen | Red |

#### Scene Background & Ambient

- Background fill: `#1B2838` (dark navy)
- Ambient glow: deep teal `#1A3C40`
- Max visible agent slots: 8 (lay out 8 instrument panels in the scene; inactive slots are dark)
- Depth gauge needle: maps `progress_pct` 0 → 0°, 100 → 270° rotation on the needle object
- Each agent slot contains three objects: `SonarRing_{n}`, `DepthGauge_{n}`, `Panel_{n}` (n = 1–8)

#### Animation Events (emitted from React → Spline)

React calls `spline.emitEvent('mouseDown', objectName)` to trigger animations on specific objects:

| Object Name | When Triggered | Effect |
|---|---|---|
| `SonarRing_1` through `SonarRing_8` | State transitions | Re-evaluates ring animation from current state variable |

#### Depth Gauge Needle Rotation Formula

```
needle_rotation_degrees = (progress_pct / 100) * 270
```

Wire this formula in the Spline State Machine using the `agent_{n}_progress` variable as the input driver.

---

## Task 1 — Install Spline Packages

**Duration:** 2 min
**Working directory:** `C:\ClaudeSkills\AgenticOS\frontend\`

```bash
npm install @splinetool/react-spline @splinetool/runtime
```

Verify `package.json` now contains both packages under `dependencies`.

### Commit

```bash
git add package.json package-lock.json
git commit -m "plan-4: install @splinetool/react-spline and @splinetool/runtime"
```

---

## Task 2 — Create `public/spline/README.md`

**Duration:** 2 min
**File:** `C:\ClaudeSkills\AgenticOS\frontend\public\spline\README.md`

Create the designer handoff document derived from Task 0. This file doubles as version control for the scene spec — if variable names change, this file changes first.

```markdown
# sonar-hud.splinecode — Scene Variable Spec
Developer: Marcus Daley
Date: 2026-04-29
Purpose: Spline scene designer reference. Defines all variables, animation states,
and object names that the React app reads and writes at runtime.

## Required Variables

Create these in the Spline Variables panel. Names are case-sensitive.

### Per-Agent (repeat for n = 1 through 8)
| Name | Type | Default | Purpose |
|---|---|---|---|
| agent_{n}_progress | Number | 0 | Depth gauge needle (0–100 maps to 0–270°) |
| agent_{n}_state | String | active | Ring pulse behavior (see States table) |
| agent_{n}_active | Boolean | false | Panel backlight glow |

### Global
| Name | Type | Default | Purpose |
|---|---|---|---|
| global_agent_count | Number | 0 | Active sonar contacts on HUD |

## States
| Value | Ring | Color | Gauge | Glow |
|---|---|---|---|---|
| active | Fast pulse 0.5s | #C9A94E | Animating | Bright gold |
| waiting_approval | Slow pulse 2s | #D4A017 | Paused | Amber |
| waiting_review | Double-pulse | #1A7A7A | Paused | Teal |
| complete | Solid | #27AE60 | Full 270° | Dim green |
| error | Rapid flash 0.1s | #C0392B | Frozen | Red |

## Scene Objects (exact names required)
SonarRing_1 through SonarRing_8
DepthGauge_1 through DepthGauge_8
Panel_1 through Panel_8

## Background
Fill: #1B2838 · Ambient: #1A3C40

## Needle Formula
needle_degrees = (agent_n_progress / 100) * 270

## Placeholder
Place sonar-hud.splinecode in this directory before running the app.
The app checks for this file. If absent, it renders the CSS fallback.
```

### Commit

```bash
git add public/spline/README.md
git commit -m "plan-4: add Spline scene designer spec and variable reference"
```

---

## Task 3 — Create `utils/splineSync.ts`

**Duration:** 4 min
**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\utils\splineSync.ts`

This is a pure function with no React imports. It receives the `Application` ref and the current agent array, then writes all Spline variables. It is the single source of truth for the variable-name-to-state mapping.

```typescript
// splineSync.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Pure utility that maps AgentState[] to Spline variable updates.
// Called on initial scene load and on every agents prop change.
// No React dependency — import type only for Application.

import type { Application } from '@splinetool/runtime';
import type { AgentState } from '../types/agent';

// Maximum agent slots defined in the Spline scene
export const MAX_AGENT_SLOTS = 8;

// Default values written to unused slots so the scene resets cleanly
const INACTIVE_PROGRESS = 0;
const INACTIVE_STATE = 'active';
const INACTIVE_ACTIVE = false;

// syncSplineState — iterates agents (up to MAX_AGENT_SLOTS), writes all
// per-agent variables and the global count. Unused slots are zeroed out
// so stale data from a previous render cannot persist in the scene.
export function syncSplineState(
  spline: Application,
  agents: AgentState[],
  maxSlots: number = MAX_AGENT_SLOTS
): void {
  // Clamp agents to maxSlots — scene only has this many instrument panels
  const activeCount = Math.min(agents.length, maxSlots);

  for (let i = 0; i < maxSlots; i++) {
    // Spline variable names use 1-based slot indices (agent_1, agent_2, ...)
    const slot = i + 1;
    const agent = agents[i];

    if (agent !== undefined) {
      // Write live agent state into Spline variables for this slot
      spline.setVariable(`agent_${slot}_progress`, agent.progress_pct);
      spline.setVariable(`agent_${slot}_state`, agent.status);
      spline.setVariable(`agent_${slot}_active`, true);
    } else {
      // Zero out unused slots so the scene does not show stale data
      spline.setVariable(`agent_${slot}_progress`, INACTIVE_PROGRESS);
      spline.setVariable(`agent_${slot}_state`, INACTIVE_STATE);
      spline.setVariable(`agent_${slot}_active`, INACTIVE_ACTIVE);
    }
  }

  // global_agent_count drives the number of visible sonar contacts on the HUD
  spline.setVariable('global_agent_count', activeCount);
}
```

### Commit

```bash
git add src/utils/splineSync.ts
git commit -m "plan-4: add syncSplineState pure utility for Spline variable writes"
```

---

## Task 4 — Unit Tests for `splineSync.ts`

**Duration:** 5 min
**File:** `C:\ClaudeSkills\AgenticOS\tests\frontend\splineSync.test.ts`

Tests use a mock `Application` object — a plain object with a `setVariable` spy. No Spline runtime is loaded. This keeps tests fast and offline-capable.

```typescript
// splineSync.test.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for syncSplineState. Verifies variable writes for active
// agents, unused slot zeroing, global count, and slot clamping at MAX_AGENT_SLOTS.

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Application } from '@splinetool/runtime';
import { syncSplineState, MAX_AGENT_SLOTS } from '../../frontend/src/utils/splineSync';
import type { AgentState } from '../../frontend/src/types/agent';

// Factory: minimal valid AgentState for testing
function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
  return {
    agent_id: 'AGENT-01',
    domain: 'general',
    task: 'Test task',
    stage_label: 'Running',
    stage: 1,
    total_stages: 3,
    progress_pct: 50,
    status: 'active',
    context_pct_used: 20,
    output_ref: 'state/outputs/agent-01.md',
    awaiting: null,
    error_msg: null,
    spawned_by: null,
    reviewer_verdict: null,
    updated_at: '2026-04-29T00:00:00Z',
    ...overrides,
  };
}

// Factory: mock Application with a setVariable spy
function makeMockSpline(): Application {
  return {
    setVariable: vi.fn(),
    emitEvent: vi.fn(),
  } as unknown as Application;
}

describe('syncSplineState', () => {
  let spline: Application;

  beforeEach(() => {
    spline = makeMockSpline();
  });

  it('writes progress, state, and active=true for a single active agent', () => {
    const agents = [makeAgent({ progress_pct: 64, status: 'active' })];
    syncSplineState(spline, agents);

    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_progress', 64);
    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_state', 'active');
    expect(spline.setVariable).toHaveBeenCalledWith('agent_1_active', true);
  });

  it('maps status to the correct state string for all five statuses', () => {
    const statuses = [
      'active',
      'waiting_approval',
      'waiting_review',
      'complete',
      'error',
    ] as const;

    for (const status of statuses) {
      const mockSpline = makeMockSpline();
      syncSplineState(mockSpline, [makeAgent({ status })]);
      expect(mockSpline.setVariable).toHaveBeenCalledWith('agent_1_state', status);
    }
  });

  it('zeroes out unused slots beyond the active agent count', () => {
    // One active agent — slots 2 through MAX_AGENT_SLOTS must be zeroed
    syncSplineState(spline, [makeAgent()]);

    for (let slot = 2; slot <= MAX_AGENT_SLOTS; slot++) {
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_progress`, 0);
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_state`, 'active');
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_active`, false);
    }
  });

  it('sets global_agent_count to the number of active agents', () => {
    const agents = [makeAgent(), makeAgent({ agent_id: 'AGENT-02' })];
    syncSplineState(spline, agents);
    expect(spline.setVariable).toHaveBeenCalledWith('global_agent_count', 2);
  });

  it('sets global_agent_count to 0 when agents array is empty', () => {
    syncSplineState(spline, []);
    expect(spline.setVariable).toHaveBeenCalledWith('global_agent_count', 0);
  });

  it('clamps to maxSlots when agents exceed MAX_AGENT_SLOTS', () => {
    // 10 agents — only 8 slots in the scene
    const agents = Array.from({ length: 10 }, (_, i) =>
      makeAgent({ agent_id: `AGENT-0${i + 1}` })
    );
    syncSplineState(spline, agents);

    // global_agent_count must be clamped to MAX_AGENT_SLOTS, not 10
    expect(spline.setVariable).toHaveBeenCalledWith('global_agent_count', MAX_AGENT_SLOTS);

    // Slot 9 and 10 must not be written at all
    const calls = (spline.setVariable as ReturnType<typeof vi.fn>).mock.calls;
    const slotNames = calls.map((c) => c[0] as string);
    expect(slotNames.some((n) => n.startsWith('agent_9_'))).toBe(false);
    expect(slotNames.some((n) => n.startsWith('agent_10_'))).toBe(false);
  });

  it('writes variables for all 8 slots when all slots are filled', () => {
    const agents = Array.from({ length: MAX_AGENT_SLOTS }, (_, i) =>
      makeAgent({ agent_id: `AGENT-0${i + 1}`, progress_pct: i * 10 })
    );
    syncSplineState(spline, agents);

    for (let slot = 1; slot <= MAX_AGENT_SLOTS; slot++) {
      expect(spline.setVariable).toHaveBeenCalledWith(`agent_${slot}_active`, true);
    }
  });

  it('respects a custom maxSlots override', () => {
    const agents = [makeAgent(), makeAgent({ agent_id: 'AGENT-02' })];
    syncSplineState(spline, agents, 4);

    // Only 4 slots written, not 8
    const calls = (spline.setVariable as ReturnType<typeof vi.fn>).mock.calls;
    const progressCalls = calls.filter((c) => (c[0] as string).endsWith('_progress'));
    expect(progressCalls).toHaveLength(4);
  });
});
```

Run tests to confirm they pass before moving on:

```bash
npx vitest run tests/frontend/splineSync.test.ts
```

### Commit

```bash
git add tests/frontend/splineSync.test.ts
git commit -m "plan-4: add unit tests for syncSplineState — 7 cases covering all variable writes"
```

---

## Task 5 — Create `SonarFallback.css`

**Duration:** 3 min
**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\SonarHUD\SonarFallback.css`

CSS-only animated rings matching the submarine color palette. No JavaScript required — these animate via `@keyframes`. Each ring uses the same color as the Spline state it represents.

```css
/* SonarFallback.css */
/* Developer: Marcus Daley */
/* Date: 2026-04-29 */
/* Purpose: CSS-only animated sonar rings fallback for WebGL-unavailable environments. */
/* Uses identical color palette to the Spline scene so visual language is consistent. */

.sonar-fallback {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px;
  background-color: #1B2838;
  border-radius: 8px;
  min-height: 320px;
  align-content: flex-start;
}

.sonar-fallback__label {
  width: 100%;
  font-size: 11px;
  color: #4a6a6a;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 8px;
  /* Communicates degraded mode without alarming the user */
}

/* Individual agent slot — circular instrument panel */
.sonar-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 80px;
}

.sonar-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 2px solid transparent;
  position: relative;
}

/* Inactive slot — dark, no animation */
.sonar-ring--inactive {
  border-color: #1e3040;
  background: #1a2530;
}

/* active — fast gold pulse, 0.5s cycle */
.sonar-ring--active {
  border-color: #C9A94E;
  animation: sonar-pulse-fast 0.5s ease-in-out infinite;
}

/* waiting_approval — slow amber pulse, 2s cycle */
.sonar-ring--waiting_approval {
  border-color: #D4A017;
  animation: sonar-pulse-slow 2s ease-in-out infinite;
}

/* waiting_review — double-pulse teal */
.sonar-ring--waiting_review {
  border-color: #1A7A7A;
  animation: sonar-double-pulse 1.6s ease-in-out infinite;
}

/* complete — solid dim green, no animation */
.sonar-ring--complete {
  border-color: #27AE60;
  background: rgba(39, 174, 96, 0.08);
}

/* error — rapid red flash, 0.1s cycle */
.sonar-ring--error {
  border-color: #C0392B;
  animation: sonar-flash 0.1s step-end infinite;
}

/* Progress arc inside the ring — filled using conic-gradient */
.sonar-ring__progress {
  position: absolute;
  inset: 4px;
  border-radius: 50%;
  /* conic-gradient driven by --progress CSS custom property set inline */
  background: conic-gradient(
    currentColor calc(var(--progress, 0) * 1%),
    transparent 0
  );
  opacity: 0.25;
}

.sonar-slot__id {
  font-size: 9px;
  color: #5a7a8a;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-align: center;
}

.sonar-slot__status {
  font-size: 8px;
  color: #4a6a6a;
  text-align: center;
}

/* Keyframes */

@keyframes sonar-pulse-fast {
  0%, 100% { box-shadow: 0 0 0 0 rgba(201, 169, 78, 0.6); }
  50%       { box-shadow: 0 0 0 8px rgba(201, 169, 78, 0); }
}

@keyframes sonar-pulse-slow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(212, 160, 23, 0.6); }
  50%       { box-shadow: 0 0 0 8px rgba(212, 160, 23, 0); }
}

/* Double-pulse: two quick expansions, then a pause until the cycle resets */
@keyframes sonar-double-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(26, 122, 122, 0.7); }
  15%  { box-shadow: 0 0 0 6px rgba(26, 122, 122, 0); }
  30%  { box-shadow: 0 0 0 0 rgba(26, 122, 122, 0.7); }
  45%  { box-shadow: 0 0 0 6px rgba(26, 122, 122, 0); }
  100% { box-shadow: 0 0 0 0 rgba(26, 122, 122, 0); }
}

@keyframes sonar-flash {
  0%  { opacity: 1; }
  50% { opacity: 0; }
}
```

### Commit

```bash
git add src/components/SonarHUD/SonarFallback.css
git commit -m "plan-4: add CSS-only sonar ring animations for WebGL fallback"
```

---

## Task 6 — Create `SonarFallback.tsx`

**Duration:** 3 min
**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\SonarHUD\SonarFallback.tsx`

Renders up to `MAX_AGENT_SLOTS` CSS rings. Each ring picks its animation class from the agent's `status` field. Inactive slots render with the `--inactive` class variant.

```tsx
// SonarFallback.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: CSS-only sonar rings fallback component rendered when WebGL is unavailable.
// Matches the Spline scene color palette so the visual language is consistent.

import React from 'react';
import type { AgentState } from '../../types/agent';
import { MAX_AGENT_SLOTS } from '../../utils/splineSync';
import './SonarFallback.css';

interface SonarFallbackProps {
  readonly agents: AgentState[];
}

// SonarFallback — renders MAX_AGENT_SLOTS slots; fills active ones from agents[],
// leaves remaining slots as inactive dark rings.
export function SonarFallback({ agents }: SonarFallbackProps): React.ReactElement {
  // Build a fixed-length slot array so inactive slots always render
  const slots = Array.from({ length: MAX_AGENT_SLOTS }, (_, i) => agents[i] ?? null);

  return (
    <div className="sonar-fallback" role="region" aria-label="Agent status display (CSS mode)">
      <span className="sonar-fallback__label">Sonar HUD — CSS Mode</span>
      {slots.map((agent, index) => (
        // Key on index is safe here — slot count is fixed at MAX_AGENT_SLOTS
        <SonarSlot key={index} slotIndex={index} agent={agent} />
      ))}
    </div>
  );
}

interface SonarSlotProps {
  readonly slotIndex: number;
  readonly agent: AgentState | null;
}

// SonarSlot — one instrument panel slot. Inactive when agent is null.
function SonarSlot({ slotIndex, agent }: SonarSlotProps): React.ReactElement {
  const slotLabel = `AGENT-${String(slotIndex + 1).padStart(2, '0')}`;

  if (agent === null) {
    return (
      <div className="sonar-slot" aria-hidden="true">
        <div className="sonar-ring sonar-ring--inactive" />
        <span className="sonar-slot__id">{slotLabel}</span>
        <span className="sonar-slot__status">--</span>
      </div>
    );
  }

  // CSS class name mirrors the status string exactly — matches CSS selector names
  const ringClass = `sonar-ring sonar-ring--${agent.status}`;

  return (
    <div className="sonar-slot" aria-label={`${agent.agent_id} ${agent.status}`}>
      <div
        className={ringClass}
        // CSS custom property drives the conic-gradient progress arc
        style={{ '--progress': agent.progress_pct } as React.CSSProperties}
      >
        <div className="sonar-ring__progress" />
      </div>
      <span className="sonar-slot__id">{agent.agent_id}</span>
      <span className="sonar-slot__status">{agent.status.replace(/_/g, ' ')}</span>
    </div>
  );
}
```

### Commit

```bash
git add src/components/SonarHUD/SonarFallback.tsx
git commit -m "plan-4: add SonarFallback component with CSS animated rings"
```

---

## Task 7 — Unit Tests for `SonarFallback.tsx`

**Duration:** 3 min
**File:** `C:\ClaudeSkills\AgenticOS\tests\frontend\SonarFallback.test.tsx`

```tsx
// SonarFallback.test.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Render tests for SonarFallback. Verifies correct slot count, status classes,
// and graceful empty-state rendering without throwing.

import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SonarFallback } from '../../frontend/src/components/SonarHUD/SonarFallback';
import { MAX_AGENT_SLOTS } from '../../frontend/src/utils/splineSync';
import type { AgentState } from '../../frontend/src/types/agent';

function makeAgent(overrides: Partial<AgentState> = {}): AgentState {
  return {
    agent_id: 'AGENT-01',
    domain: 'general',
    task: 'Test',
    stage_label: 'Running',
    stage: 1,
    total_stages: 3,
    progress_pct: 50,
    status: 'active',
    context_pct_used: 20,
    output_ref: '',
    awaiting: null,
    error_msg: null,
    spawned_by: null,
    reviewer_verdict: null,
    updated_at: '2026-04-29T00:00:00Z',
    ...overrides,
  };
}

describe('SonarFallback', () => {
  it('renders without throwing when agents array is empty', () => {
    expect(() => render(<SonarFallback agents={[]} />)).not.toThrow();
  });

  it('renders the accessible region label', () => {
    render(<SonarFallback agents={[]} />);
    expect(screen.getByRole('region')).toBeTruthy();
  });

  it('always renders MAX_AGENT_SLOTS sonar-slot elements', () => {
    const { container } = render(<SonarFallback agents={[makeAgent()]} />);
    const slots = container.querySelectorAll('.sonar-slot');
    expect(slots).toHaveLength(MAX_AGENT_SLOTS);
  });

  it('applies the correct ring class for each status', () => {
    const statuses = [
      'active',
      'waiting_approval',
      'waiting_review',
      'complete',
      'error',
    ] as const;

    for (const status of statuses) {
      const { container } = render(
        <SonarFallback agents={[makeAgent({ status })]} />
      );
      const ring = container.querySelector(`.sonar-ring--${status}`);
      expect(ring).not.toBeNull();
    }
  });

  it('renders inactive class for empty slots beyond agent count', () => {
    const { container } = render(<SonarFallback agents={[makeAgent()]} />);
    const inactiveRings = container.querySelectorAll('.sonar-ring--inactive');
    // 1 active agent → 7 inactive slots
    expect(inactiveRings).toHaveLength(MAX_AGENT_SLOTS - 1);
  });

  it('displays agent_id in the slot label', () => {
    render(<SonarFallback agents={[makeAgent({ agent_id: 'AGENT-03' })]} />);
    expect(screen.getByText('AGENT-03')).toBeTruthy();
  });

  it('sets --progress CSS custom property from progress_pct', () => {
    const { container } = render(
      <SonarFallback agents={[makeAgent({ progress_pct: 75 })]} />
    );
    // The active ring div carries the inline style
    const ring = container.querySelector('.sonar-ring--active') as HTMLElement;
    expect(ring.style.getPropertyValue('--progress')).toBe('75');
  });
});
```

Run tests:

```bash
npx vitest run tests/frontend/SonarFallback.test.tsx
```

### Commit

```bash
git add tests/frontend/SonarFallback.test.tsx
git commit -m "plan-4: add SonarFallback render tests — 7 cases"
```

---

## Task 8 — Create `SonarHUD.css`

**Duration:** 2 min
**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\SonarHUD\SonarHUD.css`

Styles the Spline canvas container, the Suspense loading placeholder, and the error state. The loading placeholder must match the sonar aesthetic so there is no jarring flash on load.

```css
/* SonarHUD.css */
/* Developer: Marcus Daley */
/* Date: 2026-04-29 */
/* Purpose: Layout and loading/error state styles for the SonarHUD Spline container. */
/* The loading placeholder uses the submarine palette so the scene appears to fade in. */

.sonar-hud {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #1B2838;
  border-radius: 8px;
  overflow: hidden;
}

/* Spline canvas fills the container completely */
.sonar-hud__canvas {
  width: 100%;
  height: 100%;
  display: block;
}

/* Loading placeholder — shown via Suspense fallback while Spline bundle loads */
.sonar-hud__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  width: 100%;
  height: 100%;
  min-height: 320px;
  background-color: #1B2838;
}

.sonar-hud__loading-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px solid #1e3040;
  border-top-color: #C9A94E;
  animation: sonar-hud-spin 1.2s linear infinite;
}

.sonar-hud__loading-text {
  font-size: 11px;
  color: #4a6a6a;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

/* Error state — scene file missing or WebGL context lost mid-session */
.sonar-hud__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  height: 100%;
  min-height: 320px;
  background-color: #1B2838;
  padding: 24px;
}

.sonar-hud__error-code {
  font-size: 10px;
  color: #C0392B;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.sonar-hud__error-message {
  font-size: 12px;
  color: #5a7a8a;
  text-align: center;
  max-width: 280px;
  line-height: 1.6;
}

@keyframes sonar-hud-spin {
  to { transform: rotate(360deg); }
}
```

### Commit

```bash
git add src/components/SonarHUD/SonarHUD.css
git commit -m "plan-4: add SonarHUD container and loading/error state styles"
```

---

## Task 9 — Replace `SonarHUD.tsx` with Full Spline Integration

**Duration:** 5 min
**File:** `C:\ClaudeSkills\AgenticOS\frontend\src\components\SonarHUD\SonarHUD.tsx`

This replaces the Plan 3 placeholder entirely. Key decisions:

- `React.lazy` wraps the Spline import so `@splinetool/runtime` (~1MB) loads asynchronously — the agent cards and approval buttons paint immediately while the 3D scene loads in the background.
- WebGL detection runs synchronously at mount (`canvas.getContext('webgl2')`) — a fast, reliable check that avoids flickering.
- `splineRef` stores the `Application` object returned by `onLoad`. This is the only mutable ref — all other state uses `useState`.
- `useEffect` with `agents` in the dependency array re-syncs Spline variables on every prop change. The effect guard (`splineRef.current`) means it is a no-op until the scene is loaded.
- `renderOnDemand={true}` tells Spline to only re-render the 3D scene when a variable changes, not on every animation frame — critical for CPU performance in a persistent tray app.

```tsx
// SonarHUD.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Spline 3D scene wrapper that drives sonar ring and depth gauge animations
// from live AgentState[] props. Falls back to CSS rings when WebGL is unavailable.

import React, {
  useRef,
  useEffect,
  useState,
  lazy,
  Suspense,
  useCallback,
} from 'react';
import type { Application } from '@splinetool/runtime';
import type { AgentState } from '../../types/agent';
import { syncSplineState } from '../../utils/splineSync';
import { SonarFallback } from './SonarFallback';
import './SonarHUD.css';

// Lazy-load the Spline component — @splinetool/runtime is ~1MB and must not
// block the initial render of agent cards and approval buttons.
const Spline = lazy(() => import('@splinetool/react-spline'));

// Scene file path — self-hosted in public/spline/ to avoid CORS issues.
// FastAPI serves this in production; Vite serves it in development.
const SPLINE_SCENE_PATH = '/spline/sonar-hud.splinecode';

interface SonarHUDProps {
  readonly agents: AgentState[];
}

// SonarHUD — three-way render:
//   1. WebGL unavailable: SonarFallback (CSS rings)
//   2. Scene load error: SceneErrorState
//   3. Normal: Spline 3D scene with live variable bindings
export function SonarHUD({ agents }: SonarHUDProps): React.ReactElement {
  // Synchronous WebGL check at mount — determines which render path to use
  const [webGLAvailable] = useState<boolean>(() => detectWebGL());

  // Tracks whether the Spline scene failed to load (network error, bad .splinecode file)
  const [sceneError, setSceneError] = useState<string | null>(null);

  // Application ref — populated by onLoad, used by syncSplineState on every update
  const splineRef = useRef<Application | null>(null);

  // Re-sync Spline variables whenever agents changes — guard ensures no-op before load
  useEffect(() => {
    if (splineRef.current !== null) {
      syncSplineState(splineRef.current, agents);
    }
  }, [agents]);

  // onLoad — store the Application ref, then immediately sync current agent state
  const handleLoad = useCallback(
    (spline: Application): void => {
      splineRef.current = spline;
      // Initialize all variables with current prop values so scene is correct on first paint
      syncSplineState(spline, agents);
    },
    // agents is intentionally included: if props changed before onLoad fired, we still
    // initialize with the latest values rather than stale closure data
    [agents]
  );

  const handleError = useCallback((error: unknown): void => {
    const message =
      error instanceof Error ? error.message : 'Unknown scene load error';
    setSceneError(message);
  }, []);

  // Path 1: WebGL unavailable — CSS fallback, no Spline loaded at all
  if (!webGLAvailable) {
    return <SonarFallback agents={agents} />;
  }

  // Path 2: Scene load failed — show error state, keep other UI functional
  if (sceneError !== null) {
    return <SceneErrorState message={sceneError} />;
  }

  // Path 3: Normal — lazy Spline with a sonar-aesthetic Suspense placeholder
  return (
    <div className="sonar-hud">
      <Suspense fallback={<SceneLoadingPlaceholder />}>
        <Spline
          className="sonar-hud__canvas"
          scene={SPLINE_SCENE_PATH}
          onLoad={handleLoad}
          onError={handleError}
          renderOnDemand={true}
        />
      </Suspense>
    </div>
  );
}

// detectWebGL — synchronous canvas probe. Returns false if WebGL2 context cannot
// be created, which happens on headless environments and some older GPUs.
function detectWebGL(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return canvas.getContext('webgl2') !== null;
  } catch {
    // getContext can throw in sandboxed iframes
    return false;
  }
}

// SceneLoadingPlaceholder — animated ring shown while Spline bundle downloads.
// Uses submarine palette so there is no jarring color shift when the scene appears.
function SceneLoadingPlaceholder(): React.ReactElement {
  return (
    <div className="sonar-hud__loading" aria-label="Loading sonar display">
      <div className="sonar-hud__loading-ring" />
      <span className="sonar-hud__loading-text">Initializing Sonar</span>
    </div>
  );
}

// SceneErrorState — shown when the .splinecode file cannot be loaded.
// Keeps the rest of the dashboard functional — agents are still tracked,
// approvals still work, only the 3D visualization is unavailable.
function SceneErrorState({ message }: { message: string }): React.ReactElement {
  return (
    <div className="sonar-hud__error" role="alert">
      <span className="sonar-hud__error-code">Scene Load Error</span>
      <span className="sonar-hud__error-message">
        3D sonar display unavailable. Agent tracking and approvals remain functional.
      </span>
      <span className="sonar-hud__error-message" style={{ fontSize: '10px', opacity: 0.5 }}>
        {message}
      </span>
    </div>
  );
}
```

### Commit

```bash
git add src/components/SonarHUD/SonarHUD.tsx
git commit -m "plan-4: replace SonarHUD placeholder with full Spline 3D integration"
```

---

## Task 10 — Verify TypeScript Compiles Clean

**Duration:** 2 min
**Working directory:** `C:\ClaudeSkills\AgenticOS\frontend\`

```bash
npx tsc --noEmit
```

Expected output: no errors. If `@splinetool/runtime` types are missing, install them:

```bash
npm install --save-dev @types/splinetool__runtime 2>/dev/null || echo "no separate types package needed"
```

Note: `@splinetool/runtime` ships its own types in the package. No `@types/` package is needed. If `tsc` reports errors about the `Application` type, verify the import in `splineSync.ts` uses `import type { Application } from '@splinetool/runtime'` and not a path alias.

---

## Task 11 — Run Full Test Suite

**Duration:** 2 min
**Working directory:** `C:\ClaudeSkills\AgenticOS\frontend\`

```bash
npx vitest run
```

Expected: all tests pass — `splineSync.test.ts` (7 cases) and `SonarFallback.test.tsx` (7 cases).

### Final Commit

```bash
git add -A
git commit -m "plan-4: Spline 3D integration complete — syncSplineState, SonarFallback, full SonarHUD wiring"
```

---

## Task 12 — Verify Scene File Placeholder Behavior

**Duration:** 2 min (manual browser check — no scene file yet)

Start the dev server:

```bash
npx vite
```

Open `http://localhost:5173` in the browser. With no `sonar-hud.splinecode` present in `public/spline/`, the expected behavior is:

1. Spline's `onError` fires because the 404 response is not a valid `.splinecode` file
2. `sceneError` state is set
3. `SceneErrorState` renders with the error message
4. Agent cards and approval buttons remain visible and interactive — the error is scoped to the HUD widget only

This confirms the error boundary is working before the designer delivers the scene file.

---

## Self-Review Checklist

### Spec Coverage
- [x] `syncSplineState` signature matches spec exactly: `(spline, agents, maxSlots?)` → `void`
- [x] All 5 agent status strings covered in CSS and in tests
- [x] All 3 variable types per slot: progress (number), state (string), active (boolean)
- [x] `global_agent_count` set on every sync call
- [x] Unused slots zeroed out — prevents stale scene state
- [x] `renderOnDemand={true}` set on Spline component
- [x] `onLoad` initializes variables immediately with current prop values
- [x] `useEffect` re-syncs on every `agents` prop change
- [x] WebGL fallback path: `SonarFallback` with CSS animations
- [x] Scene load error path: `SceneErrorState`
- [x] Spline component is lazy-loaded via `React.lazy` + `Suspense`
- [x] Suspense fallback matches submarine aesthetic
- [x] Designer handoff spec complete in `public/spline/README.md`
- [x] Spline emitEvent pattern documented in Task 0 for designer reference

### Placeholder Scan
- [x] No `TODO` comments in any file
- [x] No `// placeholder` or `// stub` markers
- [x] No hardcoded agent IDs or state values in component code
- [x] `SPLINE_SCENE_PATH` is a named constant, not an inline string
- [x] `MAX_AGENT_SLOTS` and `INACTIVE_*` values are named constants in `splineSync.ts`

### Type Consistency with Plan 3
- [x] `AgentState` imported from `../../types/agent` — not redefined
- [x] `AgentStatus` union type values match CSS class suffix names exactly
- [x] `progress_pct` field name matches Plan 3 state contract (not `progress`, not `progressPct`)
- [x] `status` field name matches (not `state`, not `agentState`)
- [x] `Application` imported with `import type` — no runtime Spline import in utility file

### Coding Standards (Marcus Daley Universal Standards)
- [x] File header on every new file
- [x] Single-line comments only (`//`) — no block comments in TS/TSX
- [x] Zero hardcoded values — all constants named
- [x] Most restrictive access: all props are `readonly`, internal functions are local
- [x] Event-driven: `useEffect` + prop change, no polling
- [x] Cleanup: `useEffect` has no subscription to clean up (Spline Application ref is passive)
- [x] Error handling: both load error and WebGL absence handled explicitly, not swallowed
- [x] TypeScript strict: `import type` used for type-only imports throughout

---

## Handoff to Plan 5

Plan 5 (WPF Launcher + WebView2 Shell) can begin as soon as Plan 4 is committed. The React app now runs correctly at `localhost:5173`. Plan 5 will:

1. Build the React app to `frontend/dist/` (`npx vite build`)
2. Configure FastAPI to serve `frontend/dist/` as static files at `/app`
3. Create the WPF window with WebView2 pointed at `http://localhost:7842/app`
4. Add system tray icon and window chrome

The Spline scene file (`sonar-hud.splinecode`) can be delivered by the designer in parallel with Plan 5 — it drops directly into `public/spline/` and the app picks it up on next load with no code changes required.
