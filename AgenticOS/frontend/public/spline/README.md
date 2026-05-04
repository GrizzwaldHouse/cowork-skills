# sonar-hud.splinecode — Scene Variable Spec

Developer: Marcus Daley
Date: 2026-04-29
Project: AgenticOS Command Center

## Purpose

This document is the contract between the React frontend and the Spline
scene file. It enumerates every variable, animation state, and object name
that the React app reads or writes at runtime. The variable names are
case-sensitive; a typo here is silent in production because Spline silently
ignores unknown variable names.

The React side reads these names from `src/utils/splineSync.ts`. If the
mapping changes, both files change in the same commit.

## Aesthetic Direction

The HUD is a fusion of two visual languages:

- **Submarine instrument panel.** Brushed metal trim, deep navy backdrop,
  faint ambient teal glow, gold-needle gauges, and ring sweeps that pulse
  like sonar contacts on a tactical display.
- **Harry Potter brass divination instruments.** Hairline gold filigree,
  parchment-cream legends, slow ambient motion that suggests enchanted
  movement rather than mechanical animation.

The goal is "tactical command center crossed with magical observatory":
cold readability, warm trim, deliberate pacing.

### Palette (mirror of `src/styles/tokens.css`)

| Token              | Hex       | Use                                       |
|--------------------|-----------|-------------------------------------------|
| Deep navy          | `#1B2838` | Background fill                           |
| Status bar shade   | `#0F1A24` | Secondary panel surfaces                  |
| Inset well shade   | `#0A121A` | Dark wells (inactive instruments)         |
| Gold accent        | `#C9A94E` | Active rings, primary trim, needles       |
| Brass border       | `#8B7435` | Panel borders, secondary text             |
| Gold hairline      | `#5A4B22` | Decorative filigree, disabled chrome      |
| Dark teal          | `#1A3C40` | Ambient glow, waiting_review accent base  |
| Teal foreground    | `#4DB6AC` | Active waiting_review ring                |
| Parchment          | `#F5E6C8` | Primary text                              |
| Amber              | `#F39C12` | waiting_approval ring                     |
| Success green      | `#27AE60` | complete ring                             |
| Error red          | `#C0392B` | error ring                                |

### Background

- Fill: `#1B2838` (deep navy)
- Ambient glow: `#1A3C40` (dark teal) with low opacity, top-left
- Optional decorative arc: gold hairline filigree along the perimeter

## Required Variables

Create each of these in the Spline Variables panel exactly as written.
Names are case-sensitive. The React app uses `setVariable` with these
exact strings; an unknown name is silently dropped by the runtime.

### Per-Agent Variables

The Spline scene must define **N slots**, where **N matches
`MAX_AGENT_SLOTS` in `src/config.ts`** (currently `32`). For each slot
`{n}` in the range `1..N`, define:

| Variable Name        | Type    | Default     | Range / Allowed Values                                                              | Drives                                                            |
|----------------------|---------|-------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `agent_{n}_progress` | Number  | `0`         | `0` – `100`                                                                          | Depth gauge needle rotation: `degrees = (progress / 100) * 270`   |
| `agent_{n}_state`    | String  | `'active'`  | `'active'`, `'waiting_approval'`, `'waiting_review'`, `'complete'`, `'error'`        | Sonar ring pulse behavior, panel glow color                       |
| `agent_{n}_active`   | Boolean | `false`     | `true` / `false`                                                                     | Backlight on the slot's instrument panel                          |

Note: writing scenes with all 32 panels visible at once is excessive for a
single screen. The recommended layout is a 4 x 8 grid of panels with the
inactive ones rendered very dim (driven by `agent_{n}_active = false`).
This way the same scene works whether 2 agents or 30 are running.

### Global Variables

| Variable Name         | Type   | Default | Range            | Drives                                          |
|-----------------------|--------|---------|------------------|-------------------------------------------------|
| `global_agent_count`  | Number | `0`     | `0` – `MAX`      | Number of active sonar contacts on the radar    |

### State -> Visual Mapping

The React app sets the `agent_{n}_state` string; the Spline state machine
reads it and triggers the matching animation set. Use these mappings:

| State Value          | Sonar Ring Behavior                          | Ring Color  | Depth Gauge                          | Panel Backlight |
|----------------------|----------------------------------------------|-------------|--------------------------------------|-----------------|
| `'active'`           | Fast pulse, 0.5 s cycle                      | `#C9A94E`   | Animating toward `progress` value    | Bright gold     |
| `'waiting_approval'` | Slow pulse, 2 s cycle                        | `#F39C12`   | Paused at current value              | Amber           |
| `'waiting_review'`   | Double-pulse: two quick, then a long pause   | `#4DB6AC`   | Paused at current value              | Teal            |
| `'complete'`         | Solid, no pulse                              | `#27AE60`   | Full sweep, locked at 270 deg        | Dim green       |
| `'error'`            | Rapid flash, 0.1 s cycle                     | `#C0392B`   | Frozen at last value                 | Red             |

### Required Scene Object Names

The React app does not currently emit Spline events, but the scene should
expose the following named objects so a future expansion can address them
individually. For each slot `{n}` in `1..N`:

- `SonarRing_{n}`   — the pulsing ring around the depth gauge
- `DepthGauge_{n}`  — the needle/dial for the progress percentage
- `Panel_{n}`       — the chrome frame around the slot, controls backlight

### Depth Gauge Needle Formula

Wire the needle rotation in the Spline state machine to the agent's
progress variable:

```
needle_rotation_degrees = (agent_{n}_progress / 100) * 270
```

Zero progress points the needle at the bottom-left; full progress points
it at the top-right (a 270 deg sweep).

## Placeholder File

A 0-byte `sonar-hud.splinecode` placeholder lives in this directory so
that the React build does not 404 noisily during development. The
designer should replace it with the real file exported from the Spline
editor. The app detects an invalid scene file via the `onError` callback
and falls back to the `SceneErrorState` card, so the rest of the UI keeps
working until the real scene file lands.

## Drop Procedure

1. In the Spline editor, export the scene as `.splinecode`.
2. Save the file as `sonar-hud.splinecode` in this directory, overwriting
   the placeholder.
3. Reload the app. No code changes are required; the file is fetched at
   runtime from `/spline/sonar-hud.splinecode`.

## Change Control

If a variable name changes, this document and `src/utils/splineSync.ts`
must change in the same commit. Mismatched names produce a silent failure
in production: variables write into a void and the scene appears frozen.
