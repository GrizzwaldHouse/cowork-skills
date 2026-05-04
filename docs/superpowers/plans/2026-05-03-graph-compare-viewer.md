# Graph Compare Viewer Implementation Plan
# Developer: Marcus Daley
# Date: 2026-05-03
# Purpose: 6-agent implementation plan for Graphify Sub-project 1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `graphify-out/graph-compare.html` — a standalone split-pane tool that compares the fixed vs. original knowledge graphs side-by-side, with a right-pane switcher, inline markdown report view, annotation drawer, and a Python extraction script.

**Architecture:** Single rendering host (no iframes), GraphRenderer abstraction over vis-network, JSON-first data loading via `fetch()`, inline markdown parser (<150 lines, no CDN), and a sliding annotation drawer backed by localStorage.

**Tech Stack:** Vanilla HTML/CSS/JS (ES2020), vis-network v9 (CDN, dev tool exception), Python 3.10+ stdlib (subprocess + json), git CLI.

**Spec:** `docs/superpowers/specs/2026-05-02-graph-compare-viewer-design.md`

---

## File Map

| File | Action | Agent |
|------|--------|-------|
| `graphify-out/graph-compare.html` | Create | 1, 2, 3, 4 (sequential sections) |
| `scripts/extract_original_graph.py` | Create | 5 |
| `graphify-out/graph-original.json` | Generate (runtime) | 5 |
| `.gitignore` | Modify (add graph-original.json) | 5 |

---

## Task 1 — Scaffold & Shell

**Agent:** Agent 1 — Scaffold & Shell
**Owns:** `graphify-out/graph-compare.html` — HTML skeleton, CSS flex layout, dark theme, draggable divider
**Deliverable:** File renders two empty labeled panes separated by a working drag divider. No graph data yet.
**Dependency:** None

### Files:
- Create: `graphify-out/graph-compare.html`

---

- [ ] **Step 1.1 — Create the HTML skeleton**

Create `graphify-out/graph-compare.html` with this exact content:

```html
<!DOCTYPE html>
<!--
  graph-compare.html
  Developer: Marcus Daley
  Date: 2026-05-03
  Purpose: Split-pane knowledge graph compare viewer (fixed vs. original)
-->
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Graph Compare — Graphify</title>
  <style>
    /* ── Design tokens ── */
    :root {
      --bg-deep:   #0f0f1a;
      --bg-panel:  #1a1a2e;
      --border:    #2a2a4e;
      --text:      #e0e0e0;
      --text-muted:#aaa;
      --accent:    #4E79A7;
      --accent-warm:#d97706;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      width: 100vw; height: 100vh;
      overflow: hidden;
      background: var(--bg-deep);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* ── Top chrome ── */
    #top-bar {
      height: 36px;
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 14px;
      font-size: 13px;
      color: var(--text-muted);
      flex-shrink: 0;
    }
    #top-bar span { color: var(--accent); font-weight: 600; margin-right: 6px; }

    /* ── Main layout ── */
    #layout {
      display: flex;
      height: calc(100vh - 36px);
      overflow: hidden;
    }

    /* ── Panes ── */
    #left-pane {
      flex-basis: 50%;
      min-width: 200px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border-right: 1px solid var(--border);
    }

    #right-pane {
      flex: 1;
      min-width: 200px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .pane-header {
      height: 32px;
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 12px;
      font-size: 12px;
      color: var(--text-muted);
      flex-shrink: 0;
      gap: 8px;
    }
    .pane-header .pane-label {
      font-weight: 600;
      color: var(--accent);
    }

    .pane-body {
      flex: 1;
      overflow: hidden;
      position: relative;
    }

    /* ── Divider ── */
    #divider {
      width: 8px;
      background: var(--border);
      cursor: col-resize;
      flex-shrink: 0;
      transition: background 0.15s;
      position: relative;
      z-index: 10;
    }
    #divider:hover, #divider.dragging { background: var(--accent); }
    #divider::after {
      content: '⋮';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: var(--text-muted);
      font-size: 14px;
      pointer-events: none;
    }

    /* ── Right pane switcher strip ── */
    #switcher-strip {
      height: 32px;
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 10px;
      gap: 6px;
      flex-shrink: 0;
    }
    #switcher-strip button {
      background: var(--bg-deep);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 3px 10px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      transition: border-color 0.15s, color 0.15s;
    }
    #switcher-strip button:hover { border-color: var(--accent); color: var(--text); }
    #switcher-strip button.active { border-color: var(--accent); color: var(--accent); }

    /* ── Graph containers ── */
    .graph-container {
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0; left: 0;
    }

    /* ── Report panel ── */
    #report-panel {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      overflow-y: auto;
      padding: 20px 24px;
      display: none;
      font-size: 13px;
      line-height: 1.7;
      color: var(--text);
    }
    #report-panel.visible { display: block; }

    /* ── Markdown rendered styles ── */
    #report-panel h1 { font-size: 18px; color: var(--accent); margin-bottom: 12px; }
    #report-panel h2 { font-size: 15px; color: var(--text); margin: 18px 0 8px; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
    #report-panel h3 { font-size: 13px; color: var(--text-muted); margin: 14px 0 6px; }
    #report-panel p  { margin-bottom: 10px; }
    #report-panel code { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 3px; padding: 1px 5px; font-size: 12px; font-family: "Cascadia Code", "Fira Mono", monospace; }
    #report-panel pre { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px; padding: 12px; overflow-x: auto; margin-bottom: 12px; }
    #report-panel pre code { background: none; border: none; padding: 0; }
    #report-panel table { border-collapse: collapse; width: 100%; margin-bottom: 14px; font-size: 12px; }
    #report-panel th, #report-panel td { border: 1px solid var(--border); padding: 5px 10px; text-align: left; }
    #report-panel th { background: var(--bg-panel); color: var(--text-muted); }
    #report-panel strong { color: var(--text); font-weight: 600; }
    #report-panel ul, #report-panel ol { padding-left: 18px; margin-bottom: 10px; }
    #report-panel li { margin-bottom: 4px; }

    /* ── Loading overlay ── */
    .loading-overlay {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-deep);
      font-size: 13px;
      color: var(--text-muted);
      z-index: 5;
    }
    .loading-overlay.hidden { display: none; }

    /* ── Annotation drawer (placeholder — Agent 4 fills in) ── */
    #annotation-tab {
      position: fixed;
      right: 0; top: 50%;
      transform: translateY(-50%);
      writing-mode: vertical-rl;
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-right: none;
      border-radius: 6px 0 0 6px;
      padding: 10px 4px;
      font-size: 11px;
      color: var(--text-muted);
      cursor: pointer;
      z-index: 100;
      user-select: none;
    }
    #annotation-tab:hover { color: var(--accent); }
    #annotation-drawer {
      position: fixed;
      right: -320px;
      top: 36px;
      width: 320px;
      height: calc(100vh - 36px);
      background: var(--bg-panel);
      border-left: 1px solid var(--border);
      z-index: 99;
      transition: right 0.25s ease;
      display: flex;
      flex-direction: column;
    }
    #annotation-drawer.open { right: 0; }
  </style>
</head>
<body>

  <div id="top-bar">
    <span>Graphify</span> Graph Compare Viewer &nbsp;·&nbsp; Fixed ↔ Original
  </div>

  <div id="layout">

    <!-- Left pane: fixed graph -->
    <div id="left-pane">
      <div class="pane-header">
        <span class="pane-label">Fixed Graph</span>
        <span id="left-stats"></span>
      </div>
      <div class="pane-body" id="left-body">
        <div class="loading-overlay" id="left-loading">Loading graph.json…</div>
        <div class="graph-container" id="left-graph"></div>
      </div>
    </div>

    <!-- Divider -->
    <div id="divider"></div>

    <!-- Right pane: switcher + content -->
    <div id="right-pane">
      <div id="switcher-strip">
        <button id="btn-original" class="active">Original Graph</button>
        <button id="btn-report">Report</button>
      </div>
      <div class="pane-body" id="right-body">
        <div class="loading-overlay" id="right-loading">Loading graph-original.json…</div>
        <div class="graph-container" id="right-graph"></div>
        <div id="report-panel"></div>
      </div>
    </div>

  </div>

  <!-- Annotation drawer -->
  <div id="annotation-tab">Notes</div>
  <div id="annotation-drawer">
    <!-- Agent 4 fills this in -->
  </div>

  <script>
    // ── CONFIG (all tuneable values live here — never hardcoded below) ──
    const CONFIG = Object.freeze({
      CDN_VIS:         'https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js',
      DATA_FIXED:      'graph.json',
      DATA_ORIGINAL:   'graph-original.json',
      DATA_REPORT:     'GRAPH_REPORT.md',
      LS_ANNOTATIONS:  'graphify-compare-annotations',
      DIVIDER_MIN_PX:  200,
      PHYSICS_TIMEOUT: 8000,
    });

    // ── Divider drag ──
    (function initDivider() {
      const divider  = document.getElementById('divider');
      const layout   = document.getElementById('layout');
      const leftPane = document.getElementById('left-pane');
      let dragging = false;

      divider.addEventListener('mousedown', (e) => {
        dragging = true;
        divider.classList.add('dragging');
        e.preventDefault();
      });

      document.addEventListener('mousemove', (e) => {
        if (!dragging) return;
        const rect  = layout.getBoundingClientRect();
        const raw   = e.clientX - rect.left;
        const min   = CONFIG.DIVIDER_MIN_PX;
        const max   = rect.width - CONFIG.DIVIDER_MIN_PX - 8;
        const clamped = Math.max(min, Math.min(max, raw));
        leftPane.style.flexBasis = clamped + 'px';
      });

      document.addEventListener('mouseup', () => {
        if (!dragging) return;
        dragging = false;
        divider.classList.remove('dragging');
      });
    })();
  </script>
</body>
</html>
```

- [ ] **Step 1.2 — Verify the file opens in Chrome**

Open `graphify-out/graph-compare.html` in Chrome via `file://` protocol.

Expected: Two empty panes labeled "Fixed Graph" and "Original Graph", separated by an 8px drag divider. Dragging the divider resizes panes. Top bar reads "Graphify Graph Compare Viewer · Fixed ↔ Original". Background is `#0f0f1a`. No console errors.

- [ ] **Step 1.3 — Commit**

```bash
git add graphify-out/graph-compare.html
git commit -m "feat(graphify): scaffold graph-compare.html — shell, layout, divider drag"
```

---

## Task 2 — GraphRenderer Interface + vis-network

**Agent:** Agent 2 — GraphRenderer Interface + vis-network impl
**Owns:** GraphRenderer object, vis-network loading, fetch() calls, both pane renders
**Deliverable:** Both panes render graph data. Left = fixed (graph.json), Right = original (graph-original.json). No switcher logic yet.
**Dependency:** Task 1 complete

### Files:
- Modify: `graphify-out/graph-compare.html` — add `<script src CDN>` tag and GraphRenderer + boot script before `</body>`

---

- [ ] **Step 2.1 — Add vis-network CDN load + GraphRenderer to graph-compare.html**

In `graph-compare.html`, replace the closing `</body>` tag with the following block (everything before the existing `</body>`'s closing tag should be preserved):

Add this immediately after the existing `<script>` block (the divider script), before `</body>`:

```html
  <!-- vis-network loaded from CDN (dev tool — CDN acceptable here) -->
  <script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>

  <script>
    // ── GraphRenderer — abstraction over vis-network ──
    // Sub-project 4 replaces only the method bodies with Sigma.js.
    // Layout and application code NEVER reference vis directly.
    function GraphRenderer() {
      this._network  = null;
      this._nodes    = null;
      this._edges    = null;
    }

    // communityColor: golden-angle HSL — maximally distinct for N communities
    GraphRenderer._communityColor = function(communityId) {
      const hue = (communityId * 137.508) % 360;
      return { background: `hsl(${hue},60%,48%)`, border: `hsl(${hue},60%,35%)`, highlight: { background: `hsl(${hue},70%,62%)`, border: `hsl(${hue},60%,45%)` } };
    };

    // init: build vis DataSets, create Network, stabilize, then freeze physics
    GraphRenderer.prototype.init = function(container, graphData, options) {
      const defaultOptions = {
        physics: {
          enabled: true,
          solver: 'forceAtlas2Based',
          forceAtlas2Based: { gravitationalConstant: -26, centralGravity: 0.005, springLength: 230, springConstant: 0.18 },
          stabilization: { iterations: 150, updateInterval: 25 },
        },
        interaction: { hover: true, tooltipDelay: 200, navigationButtons: false, keyboard: false },
        nodes: { shape: 'dot', borderWidth: 1.5, font: { color: '#e0e0e0', size: 11 } },
        edges: { smooth: { type: 'continuous', roundness: 0.2 }, selectionWidth: 3, color: { inherit: false } },
      };
      const mergedOptions = Object.assign({}, defaultOptions, options || {});

      this._nodes = new vis.DataSet(
        (graphData.nodes || []).map(n => ({
          id:    n.id,
          label: n.label || n.id,
          title: `${n.label}\n${n.source_file || ''}`,
          color: GraphRenderer._communityColor(n.community || 0),
        }))
      );

      this._edges = new vis.DataSet(
        (graphData.links || []).map((l, i) => ({
          id:     i,
          from:   l.source,
          to:     l.target,
          title:  `${l.relation} (${l.confidence}, ${l.confidence_score})`,
          color:  { color: `rgba(120,120,180,${0.2 + l.confidence_score * 0.5})`, highlight: '#4E79A7' },
          width:  Math.max(0.5, l.weight * 2),
        }))
      );

      this._network = new vis.Network(container, { nodes: this._nodes, edges: this._edges }, mergedOptions);

      this._network.once('stabilizationIterationsDone', () => {
        this._network.setOptions({ physics: { enabled: false } });
      });
      setTimeout(() => {
        if (this._network) this._network.setOptions({ physics: { enabled: false } });
      }, CONFIG.PHYSICS_TIMEOUT);
    };

    // destroy: tear down network, release DOM
    GraphRenderer.prototype.destroy = function() {
      if (this._network) {
        this._network.destroy();
        this._network = null;
        this._nodes   = null;
        this._edges   = null;
      }
    };

    // fit: zoom to fit all nodes
    GraphRenderer.prototype.fit = function() {
      if (this._network) this._network.fit();
    };

    // on: proxy event binding to vis Network
    GraphRenderer.prototype.on = function(event, cb) {
      if (this._network) this._network.on(event, cb);
    };

    // ── Boot: fetch both graphs in parallel, render ──
    (function bootGraphs() {
      const leftRenderer  = new GraphRenderer();
      const rightRenderer = new GraphRenderer();
      window.__renderers  = { left: leftRenderer, right: rightRenderer };

      const leftLoading  = document.getElementById('left-loading');
      const rightLoading = document.getElementById('right-loading');
      const leftGraph    = document.getElementById('left-graph');
      const rightGraph   = document.getElementById('right-graph');
      const leftStats    = document.getElementById('left-stats');

      Promise.all([
        fetch(CONFIG.DATA_FIXED).then(r => { if (!r.ok) throw new Error(`Failed to load ${CONFIG.DATA_FIXED}: ${r.status}`); return r.json(); }),
        fetch(CONFIG.DATA_ORIGINAL).then(r => { if (!r.ok) throw new Error(`Failed to load ${CONFIG.DATA_ORIGINAL}: ${r.status}`); return r.json(); }),
      ]).then(([fixedData, originalData]) => {
        leftLoading.classList.add('hidden');
        rightLoading.classList.add('hidden');

        leftRenderer.init(leftGraph, fixedData);
        rightRenderer.init(rightGraph, originalData);

        leftStats.textContent = `${(fixedData.nodes||[]).length} nodes · ${(fixedData.links||[]).length} edges`;
      }).catch(err => {
        leftLoading.textContent  = err.message;
        rightLoading.textContent = err.message;
        console.error('[GraphRenderer] boot failed:', err);
      });
    })();
  </script>
```

- [ ] **Step 2.2 — Verify both panes render**

Open `graphify-out/graph-compare.html` in Chrome via `file://`.

**Note:** `file://` protocol blocks `fetch()` by default in Chrome. To test locally, serve the folder:
```bash
cd C:/ClaudeSkills/graphify-out
python -m http.server 7700
```
Then open `http://localhost:7700/graph-compare.html`.

Expected:
- Left pane shows the fixed graph (3227 nodes, colored by community)
- Right pane shows the original graph (if `graph-original.json` exists) or a load error message
- Physics stabilizes and freezes within 8 seconds
- No console errors referencing vis or GraphRenderer

If `graph-original.json` does not exist yet, the right pane shows "Failed to load graph-original.json: 404" — this is correct until Agent 5 runs.

- [ ] **Step 2.3 — Commit**

```bash
git add graphify-out/graph-compare.html
git commit -m "feat(graphify): add GraphRenderer abstraction + vis-network rendering for both panes"
```

---

## Task 3 — Right-Pane Switcher + Markdown Parser

**Agent:** Agent 3 — Right-Pane Switcher + Markdown Parser
**Owns:** Button strip logic, mode state, inline markdown parser, GRAPH_REPORT.md fetch
**Deliverable:** Right pane correctly switches between graph view and styled report view without page reload.
**Dependency:** Task 2 complete

### Files:
- Modify: `graphify-out/graph-compare.html` — add switcher logic and markdown parser after the bootGraphs IIFE, before `</body>`

---

- [ ] **Step 3.1 — Add switcher + markdown parser script to graph-compare.html**

Add the following `<script>` block after the existing `</script>` (after the bootGraphs block), before `</body>`:

```html
  <script>
    // ── Inline Markdown Parser ──
    // Handles: ATX headings, fenced code blocks, tables, bold, inline code, lists, paragraphs.
    // No CDN. No marked.js. Sufficient for GRAPH_REPORT.md format.
    function parseMarkdown(text) {
      const lines  = text.split('\n');
      const output = [];
      let i = 0;

      function escHtml(s) {
        return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      }

      function inlineFormat(s) {
        return escHtml(s)
          .replace(/`([^`]+)`/g, '<code>$1</code>')
          .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
          .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1'); // strip links, keep label
      }

      while (i < lines.length) {
        const line = lines[i];

        // Fenced code block
        if (line.startsWith('```')) {
          const lang = line.slice(3).trim();
          const codeLines = [];
          i++;
          while (i < lines.length && !lines[i].startsWith('```')) {
            codeLines.push(escHtml(lines[i]));
            i++;
          }
          output.push(`<pre><code${lang ? ` class="language-${lang}"` : ''}>${codeLines.join('\n')}</code></pre>`);
          i++; // consume closing ```
          continue;
        }

        // ATX headings
        const h3 = line.match(/^### (.+)/);
        const h2 = line.match(/^## (.+)/);
        const h1 = line.match(/^# (.+)/);
        if (h1) { output.push(`<h1>${inlineFormat(h1[1])}</h1>`); i++; continue; }
        if (h2) { output.push(`<h2>${inlineFormat(h2[1])}</h2>`); i++; continue; }
        if (h3) { output.push(`<h3>${inlineFormat(h3[1])}</h3>`); i++; continue; }

        // Table: detect by pipe on current and next line (header + separator)
        if (line.startsWith('|') && lines[i+1] && lines[i+1].match(/^\|[\s\-|]+\|/)) {
          const headers = line.split('|').filter((_,idx,arr) => idx > 0 && idx < arr.length - 1).map(h => `<th>${inlineFormat(h.trim())}</th>`).join('');
          i += 2; // skip header + separator
          const rows = [];
          while (i < lines.length && lines[i].startsWith('|')) {
            const cells = lines[i].split('|').filter((_,idx,arr) => idx > 0 && idx < arr.length - 1).map(c => `<td>${inlineFormat(c.trim())}</td>`).join('');
            rows.push(`<tr>${cells}</tr>`);
            i++;
          }
          output.push(`<table><thead><tr>${headers}</tr></thead><tbody>${rows.join('')}</tbody></table>`);
          continue;
        }

        // Unordered list
        if (line.match(/^[-*] /)) {
          const items = [];
          while (i < lines.length && lines[i].match(/^[-*] /)) {
            items.push(`<li>${inlineFormat(lines[i].slice(2))}</li>`);
            i++;
          }
          output.push(`<ul>${items.join('')}</ul>`);
          continue;
        }

        // Ordered list
        if (line.match(/^\d+\. /)) {
          const items = [];
          while (i < lines.length && lines[i].match(/^\d+\. /)) {
            items.push(`<li>${inlineFormat(lines[i].replace(/^\d+\. /,''))}</li>`);
            i++;
          }
          output.push(`<ol>${items.join('')}</ol>`);
          continue;
        }

        // Blank line
        if (line.trim() === '') { i++; continue; }

        // Paragraph
        const paraLines = [];
        while (i < lines.length && lines[i].trim() !== '' && !lines[i].startsWith('#') && !lines[i].startsWith('|') && !lines[i].startsWith('```') && !lines[i].match(/^[-*] /) && !lines[i].match(/^\d+\. /)) {
          paraLines.push(inlineFormat(lines[i]));
          i++;
        }
        if (paraLines.length) output.push(`<p>${paraLines.join(' ')}</p>`);
      }

      return output.join('\n');
    }

    // ── Right-pane switcher ──
    (function initSwitcher() {
      const btnOriginal = document.getElementById('btn-original');
      const btnReport   = document.getElementById('btn-report');
      const rightGraph  = document.getElementById('right-graph');
      const reportPanel = document.getElementById('report-panel');
      const rightLoading = document.getElementById('right-loading');

      let reportLoaded = false;
      let currentMode  = 'graph'; // 'graph' | 'report'

      function showGraph() {
        currentMode = 'graph';
        rightGraph.style.display  = '';
        reportPanel.classList.remove('visible');
        btnOriginal.classList.add('active');
        btnReport.classList.remove('active');
        // Re-fit the right renderer after switching back
        if (window.__renderers && window.__renderers.right) {
          setTimeout(() => window.__renderers.right.fit(), 50);
        }
      }

      function showReport() {
        currentMode = 'graph';
        btnReport.classList.add('active');
        btnOriginal.classList.remove('active');
        rightGraph.style.display = 'none';
        reportPanel.classList.add('visible');

        if (reportLoaded) return;

        reportPanel.innerHTML = '<p style="color:var(--text-muted)">Loading report…</p>';
        fetch(CONFIG.DATA_REPORT)
          .then(r => { if (!r.ok) throw new Error(`Failed to load ${CONFIG.DATA_REPORT}: ${r.status}`); return r.text(); })
          .then(md => {
            reportPanel.innerHTML = parseMarkdown(md);
            reportLoaded = true;
          })
          .catch(err => {
            reportPanel.innerHTML = `<p style="color:#ef4444">Error: ${err.message}</p>`;
          });
      }

      btnOriginal.addEventListener('click', showGraph);
      btnReport.addEventListener('click', showReport);
    })();
  </script>
```

- [ ] **Step 3.2 — Verify switcher**

Open `http://localhost:7700/graph-compare.html`.

Expected:
- Clicking "Report" hides the right graph pane and renders `GRAPH_REPORT.md` as styled HTML (headings, tables, code blocks)
- Clicking "Original Graph" restores the graph and re-fits it
- "Report" button is highlighted (active) when report is shown, "Original Graph" when graph is shown
- GRAPH_REPORT.md community hub table renders as an HTML table
- No console errors

- [ ] **Step 3.3 — Commit**

```bash
git add graphify-out/graph-compare.html
git commit -m "feat(graphify): add right-pane switcher + inline markdown parser"
```

---

## Task 4 — Annotation Drawer

**Agent:** Agent 4 — Annotation Drawer
**Owns:** Sliding annotation drawer, localStorage persistence, add/delete/copy-all
**Deliverable:** Drawer opens/closes, notes persist across page reload, Copy All Notes outputs clean plain text.
**Dependency:** Task 3 complete

### Files:
- Modify: `graphify-out/graph-compare.html` — fill `#annotation-drawer` content and add drawer script

---

- [ ] **Step 4.1 — Replace the annotation-drawer placeholder with full markup**

In `graph-compare.html`, replace:
```html
  <div id="annotation-drawer">
    <!-- Agent 4 fills this in -->
  </div>
```

With:
```html
  <div id="annotation-drawer">
    <div id="drawer-header">
      <span>Notes</span>
      <div id="drawer-actions">
        <button id="btn-copy-notes" title="Copy all notes as plain text">Copy All</button>
        <button id="btn-close-drawer" title="Close drawer">✕</button>
      </div>
    </div>
    <div id="drawer-body">
      <div id="notes-list"></div>
    </div>
    <div id="drawer-footer">
      <textarea id="note-input" placeholder="Add a note… (Ctrl+Enter to save)"></textarea>
      <button id="btn-add-note">Add Note</button>
    </div>
  </div>
```

- [ ] **Step 4.2 — Add drawer CSS**

In `graph-compare.html`, inside the `<style>` block, add before the closing `</style>`:

```css
    /* ── Annotation drawer internals ── */
    #drawer-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      font-size: 13px;
      font-weight: 600;
      color: var(--text);
      flex-shrink: 0;
    }
    #drawer-actions { display: flex; gap: 6px; }
    #drawer-actions button {
      background: var(--bg-deep);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
    }
    #drawer-actions button:hover { border-color: var(--accent); color: var(--text); }

    #drawer-body {
      flex: 1;
      overflow-y: auto;
      padding: 10px;
    }

    .note-item {
      background: var(--bg-deep);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 10px;
      margin-bottom: 8px;
      font-size: 12px;
      line-height: 1.5;
      color: var(--text);
      position: relative;
    }
    .note-item .note-delete {
      position: absolute;
      top: 4px; right: 6px;
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 13px;
      line-height: 1;
      padding: 0 2px;
    }
    .note-item .note-delete:hover { color: #ef4444; }
    .note-item .note-ts {
      font-size: 10px;
      color: var(--text-muted);
      margin-top: 4px;
    }

    #drawer-footer {
      padding: 10px;
      border-top: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex-shrink: 0;
    }
    #note-input {
      width: 100%;
      height: 72px;
      background: var(--bg-deep);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text);
      font-size: 12px;
      padding: 7px 10px;
      resize: none;
      font-family: inherit;
      outline: none;
    }
    #note-input:focus { border-color: var(--accent); }
    #btn-add-note {
      background: var(--accent);
      border: none;
      color: #fff;
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
      align-self: flex-end;
    }
    #btn-add-note:hover { opacity: 0.85; }
```

- [ ] **Step 4.3 — Add drawer script**

Add the following `<script>` block after the switcher script, before `</body>`:

```html
  <script>
    // ── Annotation Drawer ──
    (function initAnnotationDrawer() {
      const drawer      = document.getElementById('annotation-drawer');
      const tab         = document.getElementById('annotation-tab');
      const btnClose    = document.getElementById('btn-close-drawer');
      const btnCopy     = document.getElementById('btn-copy-notes');
      const btnAdd      = document.getElementById('btn-add-note');
      const noteInput   = document.getElementById('note-input');
      const notesList   = document.getElementById('notes-list');

      // ── State ──
      function loadNotes() {
        try { return JSON.parse(localStorage.getItem(CONFIG.LS_ANNOTATIONS) || '[]'); }
        catch { return []; }
      }

      function saveNotes(notes) {
        localStorage.setItem(CONFIG.LS_ANNOTATIONS, JSON.stringify(notes));
      }

      // ── Render note list ──
      function renderNotes() {
        const notes = loadNotes();
        notesList.innerHTML = '';
        if (notes.length === 0) {
          notesList.innerHTML = '<p style="color:var(--text-muted);font-size:12px;text-align:center;padding:20px 0">No notes yet.</p>';
          return;
        }
        notes.forEach((note, idx) => {
          const div = document.createElement('div');
          div.className = 'note-item';
          div.innerHTML = `
            <button class="note-delete" data-idx="${idx}" title="Delete note">✕</button>
            <div class="note-text">${escNoteHtml(note.text)}</div>
            <div class="note-ts">${note.ts}</div>
          `;
          notesList.appendChild(div);
        });
      }

      function escNoteHtml(s) {
        return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
      }

      // ── Add note ──
      function addNote() {
        const text = noteInput.value.trim();
        if (!text) return;
        const notes = loadNotes();
        notes.unshift({ text, ts: new Date().toLocaleString() });
        saveNotes(notes);
        noteInput.value = '';
        renderNotes();
      }

      // ── Delete note ──
      notesList.addEventListener('click', (e) => {
        const btn = e.target.closest('.note-delete');
        if (!btn) return;
        const idx = parseInt(btn.dataset.idx, 10);
        const notes = loadNotes();
        notes.splice(idx, 1);
        saveNotes(notes);
        renderNotes();
      });

      // ── Copy All Notes ──
      function copyAllNotes() {
        const notes = loadNotes();
        if (notes.length === 0) { btnCopy.textContent = 'Nothing to copy'; setTimeout(() => { btnCopy.textContent = 'Copy All'; }, 1500); return; }
        const text = notes.map((n, i) => `[Note ${i+1} — ${n.ts}]\n${n.text}`).join('\n\n---\n\n');
        navigator.clipboard.writeText(text).then(() => {
          btnCopy.textContent = 'Copied!';
          setTimeout(() => { btnCopy.textContent = 'Copy All'; }, 1500);
        }).catch(() => {
          // file:// fallback
          const ta = document.createElement('textarea');
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          btnCopy.textContent = 'Copied!';
          setTimeout(() => { btnCopy.textContent = 'Copy All'; }, 1500);
        });
      }

      // ── Drawer open/close ──
      function openDrawer()  { drawer.classList.add('open'); renderNotes(); }
      function closeDrawer() { drawer.classList.remove('open'); }

      tab.addEventListener('click', () => { drawer.classList.contains('open') ? closeDrawer() : openDrawer(); });
      btnClose.addEventListener('click', closeDrawer);
      btnAdd.addEventListener('click', addNote);
      btnCopy.addEventListener('click', copyAllNotes);

      // Ctrl+Enter to save
      noteInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.ctrlKey) addNote(); });

      // Initial render (notes persist if drawer has been used before)
      renderNotes();
    })();
  </script>
```

- [ ] **Step 4.4 — Verify annotation drawer**

Open `http://localhost:7700/graph-compare.html`.

Expected:
- "Notes" tab visible on far right edge at all times
- Clicking tab slides drawer open (320px panel from right)
- Typing in textarea and clicking "Add Note" (or Ctrl+Enter) creates a note entry
- Note entry shows text + timestamp + delete button
- Refreshing page: notes still present (localStorage persistence)
- "Copy All" copies all notes as clean plain text (format: `[Note N — timestamp]\ntext\n\n---\n\n`)
- Deleting a note removes it from list and localStorage
- `✕` button in drawer header closes drawer

- [ ] **Step 4.5 — Commit**

```bash
git add graphify-out/graph-compare.html
git commit -m "feat(graphify): add annotation drawer with localStorage persistence and Copy All Notes"
```

---

## Task 5 — Extraction Script

**Agent:** Agent 5 — Extraction Script
**Owns:** `scripts/extract_original_graph.py`, `.gitignore` update
**Deliverable:** Script runs, `graphify-out/graph-original.json` is valid JSON matching `graph.json` schema.
**Dependency:** None (runs independently; Task 2 handles the "file not found" state gracefully)

### Files:
- Create: `scripts/extract_original_graph.py`
- Modify: `.gitignore` (add `graphify-out/graph-original.json`)

---

- [ ] **Step 5.1 — Create extraction script**

Create `scripts/extract_original_graph.py`:

```python
# extract_original_graph.py
# Developer: Marcus Daley
# Date: 2026-05-03
# Purpose: Extract graph.json from a prior git commit and write it as graph-original.json.
#          One-time operation; graph-original.json is gitignored.
#
# Usage:
#   python scripts/extract_original_graph.py              # uses default ref (HEAD~2)
#   python scripts/extract_original_graph.py --ref HEAD~5 # specify any git ref
#   python scripts/extract_original_graph.py --ref abc1234

import argparse
import json
import subprocess
import sys
from pathlib import Path

CONFIG = {
    "repo_root":     Path(__file__).resolve().parent.parent,
    "source_path":   "graphify-out/graph.json",
    "output_path":   Path(__file__).resolve().parent.parent / "graphify-out" / "graph-original.json",
    "default_ref":   "HEAD~2",
}


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def validate_graph_schema(data: dict) -> None:
    required_keys = {"nodes", "links"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(f"graph.json schema mismatch — missing keys: {missing}. "
                         f"Found: {list(data.keys())}")
    if not isinstance(data["nodes"], list):
        raise TypeError(f"'nodes' must be a list, got {type(data['nodes']).__name__}")
    if not isinstance(data["links"], list):
        raise TypeError(f"'links' must be a list, got {type(data['links']).__name__}")


def extract(ref: str) -> None:
    repo_root = CONFIG["repo_root"]
    source_path = CONFIG["source_path"]
    output_path = CONFIG["output_path"]

    # Verify we are inside a git repo
    result = run_git(["rev-parse", "--git-dir"], repo_root)
    if result.returncode != 0:
        print(f"ERROR: Not a git repository at {repo_root}", file=sys.stderr)
        sys.exit(1)

    # Resolve the ref to a commit hash for the log
    result = run_git(["rev-parse", "--short", ref], repo_root)
    if result.returncode != 0:
        print(f"ERROR: Cannot resolve git ref '{ref}': {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    short_hash = result.stdout.strip()

    print(f"Extracting {source_path} @ {ref} ({short_hash})…")

    # Extract file content from git object store
    git_path = f"{ref}:{source_path}"
    result = run_git(["show", git_path], repo_root)
    if result.returncode != 0:
        print(f"ERROR: '{source_path}' not found at ref '{ref}'.", file=sys.stderr)
        print(f"       git output: {result.stderr.strip()}", file=sys.stderr)
        print(f"       Tip: try a different --ref (e.g. --ref HEAD~3)", file=sys.stderr)
        sys.exit(1)

    raw_content = result.stdout

    # Parse and validate JSON
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Content at '{git_path}' is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        validate_graph_schema(data)
    except (ValueError, TypeError) as e:
        print(f"ERROR: Schema validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    node_count = len(data["nodes"])
    link_count = len(data["links"])

    # Atomic write: temp file then rename for crash safety
    tmp_path = output_path.with_suffix(".json.tmp")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(raw_content, encoding="utf-8")
    tmp_path.replace(output_path)

    print(f"✓ Written: {output_path}")
    print(f"  Ref:     {ref} ({short_hash})")
    print(f"  Nodes:   {node_count}")
    print(f"  Links:   {link_count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract graph.json from git history as graph-original.json."
    )
    parser.add_argument(
        "--ref",
        default=CONFIG["default_ref"],
        help=f"Git ref to extract from (default: {CONFIG['default_ref']})",
    )
    args = parser.parse_args()
    extract(args.ref)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5.2 — Add graph-original.json to .gitignore**

Check if `.gitignore` exists at repo root. If it does, add the entry. If not, create it.

Add this line to `.gitignore`:
```
graphify-out/graph-original.json
```

- [ ] **Step 5.3 — Run the extraction script**

```bash
cd C:/ClaudeSkills
python scripts/extract_original_graph.py
```

Expected output (exact hashes will differ):
```
Extracting graphify-out/graph.json @ HEAD~2 (e7c973f)…
✓ Written: C:\ClaudeSkills\graphify-out\graph-original.json
  Ref:     HEAD~2 (e7c973f)
  Nodes:   <N>
  Links:   <M>
```

If the output shows 0 nodes or 0 links, try a different ref:
```bash
python scripts/extract_original_graph.py --ref HEAD~3
python scripts/extract_original_graph.py --ref HEAD~5
```

The goal is a ref where `graph.json` existed but reflected the pre-fix state. Use `git log --oneline graphify-out/graph.json` to find commits that modified the file.

- [ ] **Step 5.4 — Validate the output**

```bash
python -c "
import json
d = json.load(open('graphify-out/graph-original.json'))
assert 'nodes' in d, 'Missing nodes key'
assert 'links' in d, 'Missing links key'
assert isinstance(d['nodes'], list), 'nodes is not a list'
assert isinstance(d['links'], list), 'links is not a list'
print(f'VALID: {len(d[\"nodes\"])} nodes, {len(d[\"links\"])} links')
"
```

Expected: `VALID: <N> nodes, <M> links` (both N and M should be > 0).

- [ ] **Step 5.5 — Commit**

```bash
git add scripts/extract_original_graph.py .gitignore
git commit -m "feat(graphify): add extract_original_graph.py — pulls graph.json from git ref"
```

---

## Task 6 — Integration & Validation

**Agent:** Agent 6 — Integration & Validation
**Owns:** End-to-end acceptance criteria verification
**Deliverable:** All 8 acceptance criteria verified and documented. Blockers documented if any criteria fail.
**Dependency:** Tasks 1–5 all complete

### Files:
- Read-only verification (no file ownership)

---

- [ ] **Step 6.1 — Run extraction script to generate graph-original.json**

```bash
cd C:/ClaudeSkills
python scripts/extract_original_graph.py
```

Confirm output shows nodes > 0 and links > 0.

- [ ] **Step 6.2 — Start local server**

```bash
cd C:/ClaudeSkills/graphify-out
python -m http.server 7700
```

Open `http://localhost:7700/graph-compare.html` in Chrome.

- [ ] **Step 6.3 — Verify AC1: All three panels accessible without page reload**

- [ ] Click "Original Graph" button — right pane shows graph (nodes colored by community, edges drawn)
- [ ] Click "Report" button — right pane switches to styled GRAPH_REPORT.md render (headings, tables visible), NO page reload
- [ ] Click "Original Graph" again — graph returns, re-fitted, no reload
- [ ] Left pane graph (fixed) remains stable throughout all toggles

- [ ] **Step 6.4 — Verify AC2: Annotations persist across browser sessions**

- [ ] Click "Notes" tab — drawer slides open
- [ ] Type a test note and click "Add Note"
- [ ] Close tab and reopen `http://localhost:7700/graph-compare.html`
- [ ] Open drawer — note is still present

- [ ] **Step 6.5 — Verify AC3: Copy All Notes produces clean plain text**

- [ ] With at least two notes in drawer, click "Copy All"
- [ ] Paste into a plain text editor
- [ ] Verify format: `[Note 1 — <timestamp>]\n<text>\n\n---\n\n[Note 2 — …]\n<text>`

- [ ] **Step 6.6 — Verify AC4: Standalone HTML opens via file:// protocol**

**Note:** Chrome blocks `fetch()` on `file://` by default. Valid workaround: the `python -m http.server` approach. If the requirement means "no build server / no Node required", the python server satisfies this. Document this in the validation report.

Alternatively, launch Chrome with `--allow-file-access-from-files` flag:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --allow-file-access-from-files graphify-out/graph-compare.html
```

- [ ] **Step 6.7 — Verify AC5: Works in Chrome and Brave**

Open `http://localhost:7700/graph-compare.html` in Brave. Walk AC1–AC3 again.

- [ ] **Step 6.8 — Verify AC6: GraphRenderer abstraction — vis-network never called from layout code**

```bash
grep -n "new vis\.\|vis\.DataSet\|vis\.Network" C:/ClaudeSkills/graphify-out/graph-compare.html
```

Expected: All matches are inside `GraphRenderer.prototype.init` only. Zero matches in the divider IIFE, switcher IIFE, or annotation drawer IIFE.

- [ ] **Step 6.9 — Verify AC7: No external dependencies except vis-network CDN**

```bash
grep -n "https://" C:/ClaudeSkills/graphify-out/graph-compare.html
```

Expected: Exactly one URL — `https://unpkg.com/vis-network@9.1.9/…`. No other CDN references.

- [ ] **Step 6.10 — Verify AC8: graph-original.json extracted from git history**

```bash
python -c "
import json
d = json.load(open('graphify-out/graph-original.json'))
print(f'Nodes: {len(d[\"nodes\"])}, Links: {len(d[\"links\"])}')
"
```

Expected: Both counts > 0.

- [ ] **Step 6.11 — Write validation report**

Create `docs/superpowers/specs/2026-05-03-graph-compare-validation.md`:

```markdown
# Graph Compare Viewer — Validation Report
Date: 2026-05-03

| # | Acceptance Criterion | Status | Notes |
|---|---------------------|--------|-------|
| 1 | All three panels accessible without page reload | PASS/FAIL | |
| 2 | Annotations persist in localStorage across browser sessions | PASS/FAIL | |
| 3 | Copy All Notes produces clean plain text | PASS/FAIL | |
| 4 | Standalone HTML — file:// protocol | PASS/FAIL | python -m http.server used; Chrome requires --allow-file-access-from-files for bare file:// |
| 5 | Works in Chrome and Brave | PASS/FAIL | |
| 6 | GraphRenderer abstraction in place | PASS/FAIL | |
| 7 | No external dependencies except vis-network CDN | PASS/FAIL | |
| 8 | graph-original.json extracted from git history | PASS/FAIL | |

## Blockers
(List any failed criteria and root cause here)
```

- [ ] **Step 6.12 — Final commit**

```bash
git add docs/superpowers/specs/2026-05-03-graph-compare-validation.md
git commit -m "docs(graphify): add validation report for Sub-project 1 acceptance criteria"
```

---

## Self-Review Checklist

### Spec coverage
- [x] AC1 (three panels, no reload) — Task 3 switcher
- [x] AC2 (annotations persist) — Task 4 localStorage
- [x] AC3 (Copy All Notes) — Task 4 copyAllNotes()
- [x] AC4 (file:// standalone) — Task 1 no server deps; Task 6 documents workaround
- [x] AC5 (Chrome + Brave) — Task 6.7
- [x] AC6 (GraphRenderer abstraction) — Task 2; Task 6.8 verifies
- [x] AC7 (one CDN only) — Task 2 CDN tag; Task 6.9 verifies
- [x] AC8 (extraction script) — Task 5

### Type consistency
- `GraphRenderer.init(container, graphData, options)` — `container` is a DOM element, `graphData` is parsed JSON object with `nodes[]` and `links[]`
- `GraphRenderer._communityColor(communityId)` — returns vis color object `{ background, border, highlight }`
- `window.__renderers.right` referenced in Task 3 switcher — set in Task 2 bootGraphs IIFE ✓
- `CONFIG.LS_ANNOTATIONS` used in Task 4 — defined in Task 1 CONFIG object ✓
- `CONFIG.DATA_REPORT` used in Task 3 — defined in Task 1 CONFIG object ✓
- `CONFIG.PHYSICS_TIMEOUT` used in Task 2 — defined in Task 1 CONFIG object ✓

### No placeholders
- All code blocks contain complete, runnable code ✓
- No TBD / TODO / "implement later" ✓
- All commands include expected output ✓
