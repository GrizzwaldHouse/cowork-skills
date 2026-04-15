# P0.1 Add/Add Conflict Diff Analysis

**Generated:** 2026-04-08
**Status:** Read-only research output. No code changes. No conflicts resolved.
**Scope:** 7 files in add/add conflict state from `git merge projects-copy/main` on `D:\BrightForge`
**Purpose:** Inform per-file resolution strategy under Q1-revised-A policy (read both, pick more complete base, union unique features)

---

## Executive Finding

**The 7 add/add conflicts are NOT divergent implementations of the same logic.** They are an **API contract mismatch** where Phase 10 (`projects-copy/main`) and Phase 12 (`D:\BrightForge main`) evolved divergent method names and field shapes for the *same* `forge3dDb` database operations on what is otherwise mostly-identical scaffold code.

This means:

1. The blanket "Phase 10 wins" rule from the original Q1 would have **deleted** Phase 12's reliability fixes in `world.js` (DB sync callbacks, SSE pre-completion check, race-condition recheck, 10-minute safety timeout).
2. The conflicts cannot be safely resolved at the file level until **`forge3dDb`'s actual API surface** is known. Whichever side calls method names that don't exist on the merged `forge3dDb` will crash at runtime.
3. The merged `src/forge3d/database.js` (Phase 3 of the conflict resolution) is the **single point of truth** that determines which side's call sites are correct. Resolution order matters: **`database.js` MUST be resolved before any of these 7 add/add files.**

This inverts the original execution order. Database last → database FIRST (or at least: database before the call sites that depend on it).

---

## Per-File Reports

### 1. `src/api/routes/prototype.js`

| Field | Value |
|---|---|
| **Phase 12 lines** | 361 |
| **Phase 10 lines** | 361 |
| **Diff lines** | 15 (one hunk) |
| **Functional divergence** | 3 method names on `forge3dDb` |
| **Risk level** | LOW |

**Phase 12 features:**
- Calls `forge3dDb.getNPCsByPrototype(prototypeId)`
- Calls `forge3dDb.getQuestsByPrototype(prototypeId)`
- Calls `forge3dDb.getInteractionsByPrototype(prototypeId)`

**Phase 10 features:**
- Calls `forge3dDb.getPrototypeNPCs(prototypeId)`
- Calls `forge3dDb.getPrototypeQuests(prototypeId)`
- Calls `forge3dDb.getPrototypeInteractions(prototypeId)`

**Conflicts:** Pure rename. Same prototypeId argument, same return shape expected. The two sides chose opposite naming conventions (`getXByY` vs `getYX`).

**Recommended merge strategy:** Defer until `database.js` is merged. After database resolution, call whichever method names actually exist on the merged `forge3dDb`. If both naming conventions are kept, alias one to the other. If neither exists, add both.

**Resolution dependency:** `src/forge3d/database.js`

---

### 2. `src/api/routes/world.js`

| Field | Value |
|---|---|
| **Phase 12 lines** | 422 |
| **Phase 10 lines** | 361 |
| **Diff lines** | 105 |
| **Functional divergence** | Phase 12 has 3 unique reliability features Phase 10 lacks |
| **Risk level** | HIGH (silent regression risk) |

**Phase 12 features (UNIQUE — must preserve):**

1. **Pipeline status DB sync callbacks** (~26 lines) — Listens to `pipeline_complete` and `pipeline_failed` events on `assetPipelineRunner`, syncs `forge3dDb.updateWorld(world.id, { status: 'complete' | 'failed' })`. Without this, the world status field stays in `'generating'` forever after the pipeline finishes.
2. **SSE pre-completion check** (~22 lines) — Before opening the SSE stream, checks if the pipeline already finished. If so, sends completion immediately and closes. Falls back to DB lookup if pipeline entry was already cleaned up. Prevents stuck "loading" UI when client connects late.
3. **SSE 10-minute safety timeout** (~6 lines) — `setTimeout(..., 600000)` that closes the SSE connection after 10 minutes to prevent stuck connections. Cleared by `cleanup()`.
4. **SSE post-listener race recheck** (~9 lines) — After registering pipeline event listeners, re-checks pipeline status. Catches the race where the pipeline completed between the initial check and listener registration. This is a **textbook async race-condition fix**.

**Phase 10 features (UNIQUE):**

- Adds `clearInterval(heartbeat)` inside the `onComplete` handler. Phase 12 only clears it in `cleanup()`. Both end up cleared but Phase 10 clears it slightly earlier.

**Conflicts:** Phase 12 is **strictly more correct**. Phase 10 is missing 4 production-grade reliability fixes that exist in Phase 12.

**Recommended merge strategy:** **Use Phase 12 as base.** Add only the one Phase 10 micro-improvement (`clearInterval(heartbeat)` inside `onComplete`). Discard nothing from Phase 12.

**Resolution dependency:** None — `world.js` does not depend on the `database.js` merge outcome for these reliability features. It uses `forge3dDb.updateWorld()` and `forge3dDb.getWorld()` which are stable across both branches.

---

### 3. `src/forge3d/pipeline/stages/generate-interactions.js`

| Field | Value |
|---|---|
| **Phase 12 lines** | 125 |
| **Phase 10 lines** | 123 |
| **Diff lines** | 22 (one hunk in `forge3dDb.createInteraction()` call) |
| **Functional divergence** | Schema field shape for `Interaction` |
| **Risk level** | MEDIUM |

**Phase 12 features:**
- `createInteraction({ prototypeId, targetNode, type, parameters: { trigger, dialogueOptions, outcomes }, regionId })`
- Nests `trigger`, `dialogueOptions`, `outcomes` inside a `parameters` object
- Has `targetNode` field (resolves to `npcId || targetNode`)
- Has `regionId` field

**Phase 10 features:**
- `createInteraction({ prototypeId, interactionId, npcId, type, trigger, dialogueOptions: JSON.stringify(...), outcomes: JSON.stringify(...) })`
- Flat field shape, JSON-stringifies arrays/objects (matches SQLite TEXT columns)
- Has explicit `interactionId` field
- Has explicit `npcId` field (no `targetNode` indirection)
- Has no `regionId` field

**Conflicts:** Two genuinely different schemas for the `interactions` table. Phase 10 stores JSON strings (idiomatic for `better-sqlite3`); Phase 12 stores nested objects (which would only work if `database.js` does its own JSON.stringify on insert).

**Recommended merge strategy:** Whichever schema lands in the merged `database.js` wins. Phase 10's flat-with-stringified-JSON pattern is the more standard `better-sqlite3` idiom. Phase 12's `regionId` field is unique and should be added to the merged schema if region-tagged interactions are still wanted (likely yes — Phase 12's idea-intelligence system probably uses regions).

**Resolution dependency:** `src/forge3d/database.js` schema for `interactions` table.

---

### 4. `src/forge3d/pipeline/stages/generate-npcs.js`

| Field | Value |
|---|---|
| **Phase 12 lines** | 111 |
| **Phase 10 lines** | 112 |
| **Diff lines** | 18 (one hunk in `forge3dDb.createNPC()` call) |
| **Functional divergence** | Schema field shape for `NPC` |
| **Risk level** | MEDIUM |

**Phase 12 features:**
- `createNPC({ prototypeId, name, role, behavior, regionId, dialogueSeed })`
- Maps `npc.personality` → `behavior` (with `'idle'` default)
- Maps `npc.location` → `regionId` (nullable)
- Maps `npc.backstory` → `dialogueSeed` (nullable)
- Schema vocabulary: behavior, region, dialogue seed (game-engine-flavored)

**Phase 10 features:**
- `createNPC({ prototypeId, npcId, name, role, personality, location, backstory })`
- Has explicit `npcId` field
- Stores raw `personality`, `location`, `backstory` field names
- Schema vocabulary: personality, location, backstory (LLM-output-flavored)

**Conflicts:** Genuine schema mismatch. Phase 12 has done a renaming/coercion pass to map LLM JSON output into game-engine domain language. Phase 10 stores the raw LLM fields.

**Recommended merge strategy:** Phase 12's mapping is the more polished design (separates LLM output schema from DB schema). But Phase 10's `npcId` field is critical — without it, NPCs can't be referenced by other tables. **Merge both:** keep Phase 12's renaming/defaulting logic, add Phase 10's `npcId` field passthrough.

**Resolution dependency:** `src/forge3d/database.js` schema for `npcs` table.

---

### 5. `src/forge3d/pipeline/stages/generate-quests.js`

| Field | Value |
|---|---|
| **Phase 12 lines** | 140 |
| **Phase 10 lines** | 141 |
| **Diff lines** | 24 (one hunk in `forge3dDb.createQuest()` call) |
| **Functional divergence** | Schema field shape for `Quest` |
| **Risk level** | MEDIUM |

**Phase 12 features:**
- `createQuest({ prototypeId, title, objectives, triggers, rewards, chainOrder, prerequisiteQuestId, npcGiverId })`
- Maps `quest.name || quest.title` → `title` (handles both LLM output keys)
- Maps `quest.prerequisites` → `triggers` field
- Has `chainOrder` and `prerequisiteQuestId` fields (quest chain support)
- Coerces `rewards` to array if scalar

**Phase 10 features:**
- `createQuest({ prototypeId, questId, name, type, npcGiverId, description, objectives: JSON.stringify(...), rewards: JSON.stringify(...), prerequisites: JSON.stringify(...) })`
- Has explicit `questId`, `name`, `type`, `description` fields
- JSON-stringifies arrays/objects on insert
- No quest chain fields

**Conflicts:** Two different quest schemas. Phase 12 has quest-chain support (more advanced data modeling). Phase 10 has more denormalized fields.

**Recommended merge strategy:** **Union both schemas** in `database.js`. Keep Phase 12's chain fields (`chainOrder`, `prerequisiteQuestId`). Keep Phase 10's `questId`, `type`, `description` fields. Use Phase 10's JSON stringify pattern for storage. The merged `createQuest` call site should pass all fields.

**Resolution dependency:** `src/forge3d/database.js` schema for `quests` table.

---

### 6. `src/forge3d/pipeline/stages/generate-world-map.js`

| Field | Value |
|---|---|
| **Phase 12 lines** | 108 |
| **Phase 10 lines** | 108 |
| **Diff lines** | 11 (one line) |
| **Functional divergence** | Method name on `biomeGenerator` |
| **Risk level** | LOW |

**Phase 12 features:**
- Calls `biomeGenerator.validateBiomeAdjacency(worldGraph)`

**Phase 10 features:**
- Calls `biomeGenerator.validateAdjacency(worldGraph)`

**Conflicts:** Pure rename. Same `worldGraph` argument, same return shape (`{ violations: [] }`).

**Recommended merge strategy:** Defer until `src/forge3d/world/biome-generator.js` is inspected. Whichever method name exists on the merged `BiomeGenerator` class wins. If both exist, pick one and alias.

**Resolution dependency:** `src/forge3d/world/biome-generator.js` (NOT in conflict list — auto-merged cleanly. Read it post-merge to confirm method name.)

---

### 7. `src/forge3d/pipeline/stages/streaming-layout-stage.js`

| Field | Value |
|---|---|
| **Phase 12 lines** | 112 |
| **Phase 10 lines** | 112 |
| **Diff lines** | 25 (one hunk) |
| **Functional divergence** | Method name + return shape on `streamingLayout` |
| **Risk level** | MEDIUM |

**Phase 12 features:**
- Calls `streamingLayout.generateChunks(worldGraph)` returning `Array<Chunk>`
- Calls `streamingLayout.toStreamingManifest(chunks, worldGraph)` taking the chunks array
- Computes `chunkCount` directly from `chunks.length`
- API: chunks-first, manifest-derived-from-chunks

**Phase 10 features:**
- Calls `streamingLayout.generateLayout(worldGraph)` returning `{ chunks }` object
- Calls `streamingLayout.generateManifest(worldGraph)` taking only the worldGraph (not chunks)
- Computes `chunkCount = layout.chunks ? layout.chunks.length : 0`
- API: layout-first, manifest-derived-from-worldGraph

**Conflicts:** This is a **genuine API design difference**, not just renaming. Phase 12 explicitly produces chunks then derives the manifest from them. Phase 10 produces a layout object and produces the manifest independently from worldGraph.

**Recommended merge strategy:** Need to read `src/forge3d/world/streaming-layout.js` from the merged tree to see which API actually exists. If both APIs exist post-merge (would be a multi-implementation file), pick the more recent one. If one is missing, the call site must use the surviving API.

**Resolution dependency:** `src/forge3d/world/streaming-layout.js` (NOT in conflict list — auto-merged cleanly. Inspection required post-merge.)

---

## Cross-Cutting Findings

### Finding 1 — All 7 conflicts are surface symptoms of deeper API divergence

The conflicts in these 7 files are not the real conflict. They're symptoms of three underlying API divergences that exist in **non-conflicting** files (auto-merged by git but **not** validated):

| Underlying conflict | Files affected (call sites) | Surface file (auto-merged, NEEDS INSPECTION) |
|---|---|---|
| `forge3dDb.createNPC/createQuest/createInteraction` schema shape | `generate-npcs.js`, `generate-quests.js`, `generate-interactions.js` | `src/forge3d/database.js` (in conflict list — Phase 4) |
| `biomeGenerator.validateAdjacency` vs `validateBiomeAdjacency` | `generate-world-map.js` | `src/forge3d/world/biome-generator.js` (auto-merged, **must verify which method exists**) |
| `streamingLayout.generateLayout/Chunks/Manifest` API | `streaming-layout-stage.js` | `src/forge3d/world/streaming-layout.js` (auto-merged, **must verify which API exists**) |
| `forge3dDb.getNPCsByPrototype` vs `getPrototypeNPCs` | `prototype.js` | `src/forge3d/database.js` (in conflict list — Phase 4) |

**Implication:** The clean auto-merges of `biome-generator.js` and `streaming-layout.js` are **suspect**. Git was able to text-merge them but the resulting file may contain **only one** of the two API surfaces, leaving the call sites broken regardless of how I resolve the add/add conflicts.

### Finding 2 — Resolution order must change

The original plan was: Add/Add → Config → Core → Database (last). The diff analysis says: **Database FIRST, then add/add files (which depend on database), then config, then the remaining core files.**

**Revised order:**

1. **Phase 1: Inspect auto-merged dependencies** (read-only) — Read `database.js` HEAD vs MERGED state, read `biome-generator.js` post-merge, read `streaming-layout.js` post-merge. Confirm what the API surface actually looks like in each.
2. **Phase 2: Resolve `database.js`** (the highest-risk file) — Manual deep merge per Q3 policy, producing a unified schema.
3. **Phase 3: Resolve add/add files** (5 of 7 depend on Phase 2) — `world.js` and `generate-world-map.js` can be resolved independently of `database.js`. The other 5 cannot.
4. **Phase 4: Resolve config files** (`package.json`, `asset-pipelines.yaml`, `llm-providers.yaml`, `index.html`, `app.js`) — Mechanical union per Q2 policy.
5. **Phase 5: Resolve remaining core logic files** (`server.js`, `error-handler.js`, `model-bridge.js`, `pipeline/stages/index.js`).

### Finding 3 — `world.js` is the easy win

Of the 7 add/add files, only `world.js` has a clear "Phase 12 strictly wins" answer. The other 6 require inspecting `database.js`, `biome-generator.js`, or `streaming-layout.js` first. Resolving `world.js` early gives one quick win without depending on anything.

### Finding 4 — Risk distribution

| Risk | Files |
|---|---|
| **HIGH** (silent regression risk) | `world.js` |
| **MEDIUM** (schema-dependent) | `generate-interactions.js`, `generate-npcs.js`, `generate-quests.js`, `streaming-layout-stage.js` |
| **LOW** (pure rename) | `prototype.js`, `generate-world-map.js` |

`world.js` is HIGH-risk because the wrong resolution silently deletes 4 production reliability features. The MEDIUM files are schema-dependent — they cannot be resolved correctly until `database.js` is settled. The LOW files are trivial post-inspection.

---

## Recommended Per-File Resolution Strategy (Q1-revised-A)

| # | File | Strategy | Base | Add from other side | Depends on |
|---|---|---|---|---|---|
| 1 | `prototype.js` | Defer until DB merged | (TBD) | (TBD) | `database.js` |
| 2 | `world.js` | **Phase 12 base** + add Phase 10's `clearInterval(heartbeat)` inside `onComplete` | Phase 12 | 1 line from Phase 10 | None |
| 3 | `generate-interactions.js` | Defer until DB merged | (TBD) | (TBD) | `database.js` |
| 4 | `generate-npcs.js` | Defer until DB merged | (TBD) | (TBD) | `database.js` |
| 5 | `generate-quests.js` | Defer until DB merged | (TBD) | (TBD) | `database.js` |
| 6 | `generate-world-map.js` | Defer until biome-generator inspected | (TBD) | (TBD) | `biome-generator.js` post-merge |
| 7 | `streaming-layout-stage.js` | Defer until streaming-layout inspected | (TBD) | (TBD) | `streaming-layout.js` post-merge |

**Files I can resolve right now without further input:** 1 of 7 (`world.js`).
**Files that need `database.js` resolved first:** 5 of 7.
**Files that need post-merge inspection of an auto-merged file:** 2 of 7.

---

## Open Questions for User

1. **Resolution order:** Approve revised order (Database FIRST → add/add second → config third → remaining core last)? The original "database last" plan no longer works because 5 of 7 add/add files depend on `database.js`.
2. **`world.js` standalone resolution:** Can I resolve `world.js` immediately under the recommended strategy (Phase 12 base + 1 line from Phase 10), or do you want it batched with the rest after `database.js` is merged?
3. **Auto-merge inspection of `biome-generator.js` and `streaming-layout.js`:** Confirm I should inspect these read-only post-database-merge to verify which API surface survived the auto-merge?

---

*End of Add/Add Diff Analysis. No code modified. Merge state unchanged: 17 files still UU/AA in working tree.*
