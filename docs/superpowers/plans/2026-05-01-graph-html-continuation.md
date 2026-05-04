# graph.html — Audit Fixes Continuation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify all 10 completed graph.html fixes are correct in the browser, commit the changes, and implement the two remaining known issues identified in the final code review.

**Architecture:** All work is confined to a single self-contained HTML file (`graphify-out/graph.html`, 3.2MB) — a vis-network interactive graph of the ClaudeSkills codebase. JS/HTML logic occupies lines 1–310; everything after is embedded JSON data (RAW_NODES, RAW_EDGES, LEGEND, hyperedges). Never read the full file — use Grep to locate sections, then Read with offset+limit.

**Tech Stack:** HTML5, vis-network (CDN), vanilla JS, Canvas API (Graham scan convex hull, afterDrawing hook)

---

## Session Context (2026-05-01)

All 10 fixes from the audit were applied and reviewed this session:

| Fix | Lines | Status |
|-----|-------|--------|
| Convex hull for hyperedge polygons | ~293–362 | ✅ done |
| Confidence-coded hyperedge colors (indigo/amber/red) | ~312–316 | ✅ done |
| Edge hiding on toggleAllCommunities | ~234–248 | ✅ done |
| Edge hiding on per-community legend toggle | ~257–283 | ✅ done |
| Null guard in showInfo() neighbors | ~136–140 | ✅ done |
| Stats bar: 163→135 communities | line 71 | ✅ done |
| Export PNG button | ~213–219 | ✅ done |
| INFERRED toggle — polarity fix (false→true on call) | ~219–232 | ✅ done |
| Font scaling by zoom level | ~352–353 | ✅ done |
| Neighbor link CSS — merged duplicate rule | line 24 | ✅ done |

**Two remaining items from final reviewer (suggestions, not blockers):**
1. Per-community edge-hide logic has ambiguous operator precedence (lines ~274–280)
2. Mojibake fix is a runtime workaround — real fix is upstream in the graph generator

**Execution plan JSON:** `graphify-out/graph_subagent_plan.json`

---

## File Structure

| File | Role |
|------|------|
| `graphify-out/graph.html` | The only file being modified — all JS, CSS, HTML in lines 1–310 |
| `graphify-out/graph_subagent_plan.json` | Task manifest with specs and acceptance criteria for all 10 tasks |
| `graphify-out/GRAPH_REPORT.md` | Source of truth for node/edge/community counts and god nodes |

---

### Task 1: Browser Verification

**Files:**
- Read: `graphify-out/graph.html` (lines 1–310 only)

- [ ] **Step 1: Open graph.html in browser**

Run in terminal:
```powershell
Start-Process "C:\ClaudeSkills\graphify-out\graph.html"
```
Or if that doesn't work:
```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "C:\ClaudeSkills\graphify-out\graph.html"
```

- [ ] **Step 2: Verify toolbar renders**

Expected: Three buttons visible at top of sidebar — "Export PNG", "Hide INFERRED", "Fit All"
The "Hide INFERRED" button should have amber border/text (active state) after ~800ms

- [ ] **Step 3: Verify INFERRED edges auto-hide**

Expected: After ~800ms the graph becomes less cluttered (3642 INFERRED edges disappear, leaving 4229 EXTRACTED edges)
Button label should read "Hide INFERRED" in amber

- [ ] **Step 4: Verify hyperedge regions render as convex hulls**

Expected: Colored shaded regions around node clusters — no self-intersecting polygons
Three color tiers visible: indigo (EXTRACTED), amber (INFERRED), red (AMBIGUOUS, if any)

- [ ] **Step 5: Verify community legend toggle hides edges**

Click any community in the legend sidebar.
Expected: Nodes disappear AND their edges disappear (no orphaned floating lines)

- [ ] **Step 6: Test Export PNG**

Click "Export PNG".
Expected: File download dialog opens, file named `graph-2026-05-01.png`

- [ ] **Step 7: Test node info panel**

Click any node.
Expected: Info panel shows label, type, community, source, degree, and colored neighbor chips with no JS console errors.

- [ ] **Step 8: Commit if all checks pass**

```powershell
git add graphify-out/graph.html graphify-out/graph_subagent_plan.json
git commit -m "fix(graph): audit fixes — convex hull, confidence colors, edge hiding, INFERRED toggle, export PNG"
```

---

### Task 2: Fix Per-Community Edge-Hide Operator Precedence

**Files:**
- Modify: `graphify-out/graph.html` lines ~273–280

**Context:** The per-community edge-hide logic uses `hiddenCommunities.has(...) || communityNodeIds.has(e.from) && nowHidden` without explicit parentheses. JavaScript evaluates `&&` before `||` so it's technically correct, but a future reader could misread it as `(A || B) && C`. Add explicit parentheses.

- [ ] **Step 1: Locate the exact lines**

Run:
```powershell
Select-String -Path "C:\ClaudeSkills\graphify-out\graph.html" -Pattern "communityNodeIds.has" | Select-Object LineNumber, Line
```
Expected: Two matches around lines 267 and 275.

- [ ] **Step 2: Read the block**

Read lines 270–285 with `offset:270 limit:16`.

- [ ] **Step 3: Apply the parentheses fix**

Find this pattern:
```js
      const fromHidden = hiddenCommunities.has(
        (nodesDS.get(e.from) || {})[`_community`] ?? -1
      ) || communityNodeIds.has(e.from) && nowHidden;
      const toHidden = hiddenCommunities.has(
        (nodesDS.get(e.to) || {})[`_community`] ?? -1
      ) || communityNodeIds.has(e.to) && nowHidden;
```

Replace with (explicit parentheses, no logic change):
```js
      const fromHidden = hiddenCommunities.has(
        (nodesDS.get(e.from) || {})[`_community`] ?? -1
      ) || (communityNodeIds.has(e.from) && nowHidden);
      const toHidden = hiddenCommunities.has(
        (nodesDS.get(e.to) || {})[`_community`] ?? -1
      ) || (communityNodeIds.has(e.to) && nowHidden);
```

Use Edit with the exact old_string.

- [ ] **Step 4: Verify no logic changed**

Re-read lines 270–285. Confirm only parentheses added, no other diff.

- [ ] **Step 5: Commit**

```powershell
git add graphify-out/graph.html
git commit -m "fix(graph): add explicit parentheses to edge-hide operator precedence"
```

---

### Task 3: Document the Mojibake Root Cause in GRAPH_REPORT.md

**Files:**
- Modify: `graphify-out/GRAPH_REPORT.md`

**Context:** The runtime `â†' → →` replacement in graph.html is a workaround for a UTF-8/Latin-1 encoding mismatch in the upstream graph generator. The real fix belongs in the generator, not the viewer. Document it so it's not forgotten.

- [ ] **Step 1: Read end of GRAPH_REPORT.md**

```powershell
Get-Content "C:\ClaudeSkills\graphify-out\GRAPH_REPORT.md" | Select-Object -Last 20
```

- [ ] **Step 2: Append Known Issues section**

Edit GRAPH_REPORT.md — add to the end:

```markdown

## Known Issues & Deferred Fixes

### Mojibake Arrow Characters in Hyperedge Labels
- **Symptom:** Hyperedge labels containing `→` appear as `â†'` in the raw JSON.
- **Root cause:** The graph generator writes JSON with UTF-8 encoding but the label strings were captured as Latin-1 (Windows cp1252 codepage). The 3-byte UTF-8 sequence for `→` (0xE2 0x80 0x99) is decoded as three Latin-1 characters `â†'`.
- **Current workaround:** `graph.html` applies `h.label.replace(/â†'/g, '→')` at canvas render time.
- **Real fix:** In the graph generator script, ensure `json.dumps(..., ensure_ascii=False)` is used with an explicit `encoding='utf-8'` file open, OR post-process `graph.json` with: `python -c "import json,pathlib; p=pathlib.Path('graph.json'); p.write_text(p.read_text(encoding='utf-8').replace('â†"', '→'), encoding='utf-8')"`
- **Priority:** Low — workaround is stable. Fix when regenerating graph.json.

### 876 Isolated Nodes
- **Symptom:** 876 nodes have ≤1 connection — they appear as orphaned dots.
- **Root cause:** The extractor ran on 832 files but edge inference only covered ~54% of files. Build artifacts, doc files, and standalone scripts were parsed but not semantically linked.
- **Real fix:** Re-run extractor with `--no-semantic` flag and increase AST edge depth, or filter isolated nodes from the output with `--min-degree 2`.
- **Priority:** Medium — run when regenerating the graph.
```

- [ ] **Step 3: Verify append looks correct**

```powershell
Get-Content "C:\ClaudeSkills\graphify-out\GRAPH_REPORT.md" | Select-Object -Last 30
```

- [ ] **Step 4: Commit**

```powershell
git add graphify-out/GRAPH_REPORT.md
git commit -m "docs(graph): document mojibake root cause and isolated node fix in GRAPH_REPORT"
```

---

### Task 4: Final Branch Cleanup

- [ ] **Step 1: Verify all files committed**

```powershell
git status
```
Expected: Clean working tree.

- [ ] **Step 2: Run finishing-a-development-branch skill**

Invoke: `superpowers:finishing-a-development-branch`

This handles: final diff review, PR description, merge/push decision.

---

## Subagent Context Block

Copy this into every implementer subagent prompt for this plan:

```
FILE: C:/ClaudeSkills/graphify-out/graph.html (3.2MB)
- Use Grep to locate sections, then Read with offset+limit. NEVER read the full file.
- JS/HTML is in lines 1–310 only. Everything after is embedded JSON data — do not touch it.
- Library: vis-network (vis.DataSet, vis.Network) from unpkg CDN
- Data vars: RAW_NODES, RAW_EDGES (has .confidence: "EXTRACTED"/"INFERRED"/"AMBIGUOUS"), LEGEND, hyperedges
- DataSets: nodesDS, edgesDS (vis.DataSet wrappers — update these, never mutate RAW_* arrays)
- Theme: dark (#0f0f1a bg, #3a3a5e borders, #4E79A7 accent, #d97706 amber for INFERRED)
```
