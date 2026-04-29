---
name: spline3d
description: >
  Integrate Spline 3D scenes into web, Electron, PyQt6, or React frontends.
  Covers scene spec authoring, variable-driven state sync, background embeds,
  icon/asset generation, WebGL fallback, and performance patterns.
  Evolves with each project — check the changelog at the bottom.
category: design
version: 2.0.0
last_updated: 2026-04-29
projects_applied: [OwlWatcher, BrightForge, AgenticOS]
tags: [spline, 3d, webgl, animation, react, electron, pyqt6, icon, background]
---

# Spline 3D Integration Skill

A project-agnostic guide for embedding Spline 3D scenes into any frontend.
Grows with every project — when you finish a project using this skill, add a changelog entry.

---

## When to Use

Use Spline when:
- You need interactive 3D elements that respond to app state (running/idle/error)
- A background scene gives the product identity without requiring 3D modeling expertise
- You want variable-driven animations (progress bars, state rings, ambient effects) with zero WebGL code
- The product has a strong visual concept (forge, sonar HUD, owl mascot) that deserves spatial expression

Don't use Spline when:
- The scene needs real-time physics or collision (use Three.js/Babylon instead)
- The target environment is a headless server, CI runner, or guaranteed low-end GPU
- Bundle size is critically constrained and the 1 MB runtime can't be lazy-loaded

---

## Core Workflow

### 1. Write the scene spec first

Before opening Spline editor or writing any code, author a `README.md` in `public/spline/`.
Lock variable names, object names, and state mappings before building.
**Variable names are a contract** — changing them after the scene is built breaks the integration.

Required sections in every scene spec:
- Canvas size + background fill (transparent or solid)
- Required objects table (exact names, case-sensitive)
- Required variables table (name, type, default, range, purpose)
- State → visual mapping table
- Animation specs per state
- Material specs for key objects
- Camera position and FOV
- File output path

See `D:\BrightForge\public\spline\README.md` for a complete example.

### 2. Build the scene in Spline editor

- Create variables in Spline's Variables panel matching the spec exactly
- Name objects exactly as specified — React/JS reads these by name
- Use State Machine nodes to wire variable changes to animations
- Export as `.splinecode` to `public/spline/`

### 3. Write the sync utility (pure function, no framework dependency)

```typescript
// splineSync.ts — pure function, testable with a mock Application
import type { Application } from '@splinetool/runtime';

export function syncState(spline: Application, state: AppState): void {
  spline.setVariable('is_active', state.running);
  spline.setVariable('alert_mode', state.hasError);
  spline.setVariable('progress', state.progress);
}
```

The sync function must:
- Import `Application` with `import type` (no runtime Spline import in utility files)
- Be a pure function with no React/Vue/Svelte dependency
- Zero out unused slots/variables so stale scene state cannot persist
- Be unit-tested with a mock `{ setVariable: vi.fn() }` Application object

### 4. Wire into the framework

**React:**
```tsx
const Spline = lazy(() => import('@splinetool/react-spline'));

// Store ref on load, sync on every state change
const splineRef = useRef<Application | null>(null);
useEffect(() => {
  if (splineRef.current) syncState(splineRef.current, appState);
}, [appState]);
```

**Vanilla JS / Electron:**
```js
import { Application } from '@splinetool/runtime';
const app = new Application(canvas);
await app.load('/spline/scene.splinecode');
// then call syncState(app, state) whenever state changes
```

**PyQt6:**
Use `QWebEngineView` with `QWebChannel` bridge. See `C:\ClaudeSkills\docs\SPLINE_3D_INTEGRATION_DESIGN.md`
for the full `Spline3DWidget` base class with bidirectional Python↔JS communication.

### 5. Always provide two fallbacks

**Fallback 1 — CSS animated (WebGL unavailable):**
Detect with `canvas.getContext('webgl2') !== null` at mount (synchronous, no flicker).
Render CSS `@keyframes` animations in the same color palette as the Spline scene.
Users on headless or integrated-GPU environments get a consistent visual language.

**Fallback 2 — Static gradient (Spline file missing / network error):**
Wrap `app.load()` in try/catch.
Apply a CSS `radial-gradient` that approximates the scene's ambient glow.
Never show a broken canvas or a white flash.

---

## Variable Patterns

### Boolean state variables
```
forge_active    Boolean  false   Job running
alert_mode      Boolean  false   Error state
scene_visible   Boolean  true    Hide/show scene
```

### Numeric driven variables
```
progress_pct    Number   0       0-100, drives needle/ring
ember_intensity Number   0.4     0-1, forge fire brightness
opacity         Number   0.18    0-1, overall canvas opacity
```

### Slot arrays (for multi-agent / multi-item scenes)
```
agent_1_progress  Number   0      Per-slot progress 0-100
agent_1_state     String   active Per-slot status string
agent_1_active    Boolean  false  Per-slot on/off
global_count      Number   0      Total active slots
```
Always zero out unused slots on every sync call — never assume Spline resets them.

---

## Background Embed Pattern

For translucent 3D backgrounds behind UI panels (BrightForge Terminal Forge, AgenticOS):

```css
.spline-bg-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.18;           /* tune per scene — 0.12–0.25 typical */
  pointer-events: none;    /* CRITICAL — never block UI clicks */
  z-index: 0;              /* behind all content */
}
```

Design rules for background scenes:
- Camera: static, slightly elevated, 10–15° down angle
- Composition: subject occupies one side (60%), other side empty (UI lives there)
- Opacity: 0.12–0.22 — visible but never competing with text legibility
- No camera animation — moving backgrounds are nauseating behind static UI
- Ambient light: warm tint matching the product accent color, intensity 0.3–0.5
- Background fill in Spline: **transparent** (alpha 0) — the app background shows through

---

## Icon Generation Pattern

For products with a strong visual mascot/mark, generate icons at multiple sizes:

1. **Design the master SVG first** — hand-craft at 1024×1024 using the product's color tokens
2. **Key sizes needed:** 1024, 512, 256, 128, 64, 32, 16
3. **Below 32×32:** simplify to silhouette only — detail is lost
4. **Rounded square radius:** `size * 0.214` (matches macOS/Windows icon conventions)
5. **Taskbar icons:** must work on both dark and light taskbars — test both
6. **Electron:** set in `BrowserWindow({ icon: path.join(__dirname, 'icons/icon.png') })`
7. **Convert SVG → ICO/ICNS:** use `electron-icon-builder` or `png2icons` npm packages

For AI-generated photorealistic icons — see `image-prompts.md` pattern.
Always generate at 1024×1024 minimum, then downscale with a sharpening pass.

---

## Performance Rules

| Rule | Reason |
|------|--------|
| Lazy-load Spline runtime via `React.lazy` or dynamic `import()` | Runtime is ~1MB — never block initial paint |
| Set `renderOnDemand={true}` on `<Spline>` component | Only re-render when variables change, not every frame |
| Max 3-4 concurrent Spline widgets per page | Each QWebEngineView = ~50-80MB Chromium overhead |
| Load scenes only when widget is visible (`IntersectionObserver`) | Idle scenes still consume GPU memory |
| Target particle counts: idle ≤ 10, active ≤ 50, alert ≤ 100 | More than this causes frame drops on integrated GPUs |
| Use Spline LOD system for complex meshes | Auto-reduces poly count at distance |

---

## Scene Variable Spec Template

Copy this into every new project's `public/spline/README.md`:

```markdown
# [scene-name].splinecode — Scene Spec
Developer: [name]
Date: [date]
Project: [project]

## Canvas
- Size: [width]×[height]
- Background: TRANSPARENT / [hex]
- Ambient: [hex], intensity [0-1]

## Objects
| Name | Type | Description |
|------|------|-------------|

## Variables
| Name | Type | Default | Range | Purpose |
|------|------|---------|-------|---------|

## State Mapping
| State | variable_a | variable_b | visual effect |
|-------|-----------|-----------|---------------|

## Animations
### [state name]
- [object]: [animation description], [duration]s [easing]

## Materials
### [object name]
- PBR: roughness [x], metalness [x]
- Color: [hex]
- Emissive: [hex] at [intensity] (if any)

## Camera
- Position: [x, y, z]
- FOV: [degrees]
- Animation: none / [description]

## File Output
Export as: [filename].splinecode
Place at: [path]
Served at: [url]
```

---

## Testing Checklist

Before shipping any Spline integration:

- [ ] WebGL2 unavailable → CSS fallback renders, no crash, no white flash
- [ ] `.splinecode` file 404 → error state renders, rest of UI still functional
- [ ] `syncState()` unit tests pass with mock Application object
- [ ] All variable names in sync function match spec exactly (case-sensitive)
- [ ] `pointer-events: none` on background canvas (click-through works)
- [ ] Opacity is readable — text contrast ratio ≥ 4.5:1 over the background scene
- [ ] Scene loads within 3s on a 10 Mbps connection (`.splinecode` file size ≤ 5MB)
- [ ] No console errors in production build
- [ ] Electron: icon appears in taskbar and title bar at correct sizes
- [ ] `renderOnDemand={true}` set (verify with browser DevTools — GPU usage should be near 0 when idle)

---

## File Conventions

```
project-root/
  public/
    spline/
      README.md              ← scene spec (this template)
      [scene-name].splinecode ← exported from Spline editor
    icons/
      brightforge-icon.svg   ← master SVG at 1024×1024
      preview.html           ← icon preview page at all sizes
      image-prompts.md       ← AI image generation prompts
  src/ (or public/js/)
    forge-bg.js              ← Spline background controller
    splineSync.ts            ← pure variable sync utility
  tests/
    splineSync.test.ts       ← mock Application unit tests
```

---

## Integrations by Framework

| Framework | Package | Notes |
|-----------|---------|-------|
| React | `@splinetool/react-spline` + `@splinetool/runtime` | Use `React.lazy`, `renderOnDemand` |
| Vanilla JS / Electron | `@splinetool/runtime` | Direct `Application` class |
| PyQt6 | `QWebEngineView` + `QWebChannel` | Full bridge in `SPLINE_3D_INTEGRATION_DESIGN.md` |
| Vue 3 | `@splinetool/runtime` in `onMounted` | Store ref in `ref<Application>()` |
| Svelte | `@splinetool/runtime` in `onMount` | `bind:this` on canvas element |

---

## Changelog

### v2.0.0 — 2026-04-29 (BrightForge)
- Added background embed pattern (translucent forge scene behind Terminal Forge UI)
- Added icon generation pattern (SVG master, AI prompts, size guide)
- Added CSS gradient fallback as second-level fallback (below CSS animations)
- Added `forge-bg.js` vanilla JS controller pattern (no React dependency)
- Expanded variable patterns with boolean/numeric/slot-array examples
- Added performance rules table
- Added testing checklist
- Added file conventions section
- Added scene variable spec template (copy-paste for new projects)
- Projects applied: OwlWatcher (PyQt6), AgenticOS (React/Vite), BrightForge (Electron/vanilla JS)

### v1.0.0 — 2026-02-24 (OwlWatcher)
- Initial skill created from OwlWatcher PyQt6 integration
- QWebEngineView + QWebChannel bridge pattern
- 3D mascot (owl), moon toggle, file visualization, stats widgets
- WebGL fallback detection
- Graceful degradation path
