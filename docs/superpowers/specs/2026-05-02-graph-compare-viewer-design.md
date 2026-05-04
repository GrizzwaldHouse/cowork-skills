# Graph Compare Viewer — Design Spec
# Developer: Marcus Daley
# Date: 2026-05-02
# Purpose: Locked architecture spec for Graphify Sub-project 1 (Graph Compare Viewer)

## Overview

A standalone split-pane HTML tool (`graph-compare.html`) that lets Marcus compare the original (pre-fix) and fixed knowledge graphs side-by-side, toggle the right pane between the original graph and the GRAPH_REPORT, annotate observations, and extract the pre-fix graph from git history via a Python helper script.

---

## Architecture

### Single-file rendering host
`graph-compare.html` is a self-contained HTML file that owns both graph renders directly. No iframes. Both the left pane (fixed graph) and right pane (original graph or report) live in the same DOM and share a single JS execution context. This eliminates cross-frame localStorage, Canvas, and pointer-event isolation problems.

### GraphRenderer abstraction
A `GraphRenderer` object wraps vis-network. Both panes instantiate it independently. The interface is locked:
- `init(container, graphData, options)` — creates the vis Network, applies node/edge transforms, starts rendering
- `destroy()` — tears down the Network instance and releases DOM
- `fit()` — calls `network.fit()`
- `on(event, cb)` — proxies `network.on(event, cb)`

vis-network is never called directly from layout or application code. Sub-project 4 replaces only the four method bodies with Sigma.js without touching the rest of the file.

### Data loading
`fetch()` at page load. No embedded globals.
- Left pane: `fetch('graph.json')`
- Right pane (graph mode): `fetch('graph-original.json')`
- Right pane (report mode): `fetch('GRAPH_REPORT.md')`

Both graph fetches run in parallel via `Promise.all`.

### Graph data schema (graph.json / graph-original.json)
NetworkX node_link format:
- `nodes[]` — `{ id, label, file_type, source_file, community, norm_label }`
- `links[]` — `{ source, target, relation, confidence, confidence_score, weight }`

GraphRenderer maps: `node.id → vis id`, `link.source → from`, `link.target → to`.

Color encoding: golden-angle HSL — `hsl((community * 137.508) % 360, 60%, 55%)` — produces maximally distinct colors for 163 communities without a lookup table.

Edge opacity: derived from `confidence_score` (0.25–1.0 range).

### Right-pane switcher
Button strip above the right pane: **Original Graph** | **Report**. Toggling between modes calls `rightRenderer.destroy()` / `rightRenderer.init()` for graph↔graph switches, or shows/hides the markdown panel div for graph↔report switches.

### Inline markdown parser
No CDN. No marked.js. A `parseMarkdown(text)` function under 150 lines handles:
- ATX headings (# ## ###)
- Fenced code blocks (``` ... ```)
- Tables (pipe-delimited)
- Bold (`**text**`)
- Inline code (backticks)

Sufficient for GRAPH_REPORT.md format. Output is sanitized HTML injected into a scrollable div.

### Annotation drawer
Fixed-position right-edge sidebar (tab handle visible at all times, drawer slides in/out). Persistence key: `'graphify-compare-annotations'` in localStorage. Features: add note (textarea + button), delete note (per-note button), Copy All Notes (produces plain text, one note per line, for pasting into Claude).

### Layout
CSS flexbox: `100vw × 100vh`, no scrollbars on body. Three columns: left pane (graph), draggable divider (8px), right pane (switcher strip + content area). Pointer-event drag on divider sets `flex-basis` on left pane in real time.

Dark theme tokens (matching graph.html):
- `--bg-deep: #0f0f1a`
- `--bg-panel: #1a1a2e`
- `--border: #2a2a4e`
- `--text: #e0e0e0`
- `--text-muted: #aaa`
- `--accent: #4E79A7`

---

## Output Files

| File | Status | Owner |
|------|--------|-------|
| `graphify-out/graph-compare.html` | Create | Agent 1–4 |
| `graphify-out/graph.json` | Exists | — |
| `graphify-out/graph-original.json` | Generate | Agent 5 |
| `graphify-out/GRAPH_REPORT.md` | Exists | — |
| `scripts/extract_original_graph.py` | Create | Agent 5 |

---

## Acceptance Criteria

1. All three panels accessible without page reload (left: fixed graph; right: toggles between original graph and GRAPH_REPORT)
2. Annotations persist in localStorage across browser sessions
3. Copy All Notes produces clean plain text for pasting into Claude
4. Standalone HTML — opens directly from filesystem (`file://` protocol), no server required
5. Works in Chrome and Brave
6. GraphRenderer abstraction in place — vis-network never called directly from layout code
7. No external dependencies except vis-network CDN (dev tool exception)
8. `graph-original.json` extracted correctly from git history by the Python script

---

## Constraints (locked)

- `no_external_dependencies` except vis-network CDN
- `no_hardcoded_values` — all config (CDN URL, localStorage key, git ref default) in a `CONFIG` object at the top of the file
- `event_driven_architecture` — divider drag, panel switching, and drawer open/close all use DOM event listeners, no polling
- `graph-compare.html` does NOT depend on `graph.html`
- `graph-original.json` is gitignored
