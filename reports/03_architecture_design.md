# Architecture Design & Reconciliation Report

**Team:** ai-audit-2026 | **Agent:** architect | **Task:** #3
**Date:** 2026-04-08
**Scope:** Reconcile the user's authoritative strategy doc (`00_user_strategy_doc.md`) against the live repo audit (`01_repo_audit.md`) and HF 2026 model research (`02_huggingface_reference.md`). Produce a revised pipeline, cross-repo architecture, per-repo targets, and an extended roadmap.

**Constraint:** Plan-only. No code edits. Markdown deliverable only. All claims cross-verified against actual files in `D:\Agent-Alexander`, `D:\BrightForge`, and `C:\Users\daley\Projects\Bob-AICompanion` prior to writing.

**Revision note (2026-04-08, post-initial-draft):** Team-lead issued a correction after the first draft. HoneyBadgerVault's current domain is **LMS document extraction** (Canvas / Blackboard / Moodle / D2L connectors, ts-fsrs spaced repetition, flashcard generation) — the AI **image** pipeline described in the user strategy doc is entirely aspirational in that repo. Additionally, neither BrightForge copy is unilaterally canonical: D:\BrightForge is at Phase 12 (Idea Intelligence) and is missing `src/model-intelligence/`; C:\Users\daley\Projects\BrightForge is at Phase 10 and is missing `src/idea/`. The canonical trunk is the **merged** result. Section 1 has been updated with three new reconciliation rows (#22-24) and Section 5 has been restructured with a dedicated Phase 0 / Pre-work block that blocks user-doc Phase 1.

---

## Section 1 — Reconciliation Report

Every substantive claim in the user's strategy doc is tabled below. Status values:
**CONFIRMED** (audit supports), **CONTRADICTED** (audit reveals otherwise), **OBSOLETE** (HF research supersedes), **NEEDS INVESTIGATION** (not visible from current artifacts).

| # | Claim (paraphrased from 00_user_strategy_doc.md) | Status | Evidence | Recommendation |
|---|---|---|---|---|
| 1 | "All four repositories are private and could not be directly inspected" | CONTRADICTED | `D:\Agent-Alexander` (= HoneyBadgerVault) and `D:\BrightForge` are locally cloned and fully readable. The user's planning doc was written blind; the audit is ground-truth. | Treat the audit as authoritative where it disagrees with the strategy doc. |
| 2 | "HoneyBadgerVault should be the flagship product" (positioned as greenfield) | CONFIRMED (as flagship) / CONTRADICTED (as greenfield) | It is already the flagship-quality codebase: 17-table Drizzle schema (`shared/schema.ts`), 12-file `server/ai/` directory with Ollama+OpenAI orchestration (`ai-orchestrator.ts:1-80`), RRF-based hybrid search (`hybrid-search.ts:48-72`), vitest + Playwright E2E, verified-build-gate. This is beta/near-production, not a blank scaffold. | Keep HBV as flagship. Replace "scaffold HBV" guidance with "extend HBV." |
| 3 | Ecosystem consists of four repos (grizz-optimizer, BrightForge, HoneyBadgerVault, Bob) | CONTRADICTED | Audit shows 9 local paths resolving to **8 distinct codebases**: Agent-Alexander and HoneyBadgerVault are the same repo (origin: `github.com/GrizzwaldHouse/HoneyBadgerVault.git`), and the two BrightForge copies are divergent branches of the same GitHub repo. The missing repos are portfolio-website, DeveloperProductivityTracker (UE5 Capstone), and SeniorDevBuddy/agentforge_autonomous. | Redraw the ecosystem at 8 nodes, collapse A-A/HBV, merge the two BrightForge copies. |
| 4 | "Agent-Alexander and HoneyBadgerVault are separate repos" (implied by the 9-repo scope note) | CONTRADICTED | `cd D:\Agent-Alexander && git remote -v` prints `origin https://github.com/GrizzwaldHouse/HoneyBadgerVault.git`. Directory layout is 1:1 with HBV. | Rename the local folder to match GitHub. Kill the dual identity. |
| 5 | "BrightForge is the development workflow tool" | CONTRADICTED | It is a 40k-line multi-agent AI studio with 9-provider LLM chain (`src/core/llm-client.js`), full agent taxonomy (`src/agents/{master,planner,builder,reviewer,tester,recorder,survey,cloud,local}-agent.js`), Forge3D SDXL+InstantMesh pipeline (`src/forge3d/`), and Phase 12 Idea Intelligence (`src/idea/{ingestion,classifier,scoring,research,indexer}`). 12 documented dev phases, version 4.2.0. | Reclassify BrightForge as "multi-agent AI studio with 3D asset pipeline." It is the canonical home of the LLM fallback chain. |
| 6 | "Bob-AICompanion serves as intelligence/orchestration layer" and should become MCP-enabled | CONFIRMED (vision) / CONTRADICTED (current state) | Current Bob is a scheduled-automation + job-intelligence pipeline running serverlessly on GitHub Actions (`.github/workflows/morning-brief.yml`, 8-provider YAML LLM chain, Discord webhook delivery, job fraud/scoring sub-system). It is **not** an MCP server today. The vision is good; the baseline needs correction. | Keep MCP-enablement as the Phase-3 target. Baseline Bob as "cost-optimal serverless automation + job intelligence, future MCP unifier." |
| 7 | "grizz-optimizer as performance foundation" (implied utility library) | CONTRADICTED | grizz-optimizer is a production-grade Electron app with typed contextBridge IPC, 5-tier AI fallback (Ollama -> HF ONNX -> HF API -> Groq -> Cerebras), $1/day budget cap, advisory-only AI principle, red team scanner, plugin SDK, and a RuntimeWatcher agent. It is **not** a shared library other projects import. Per `MEMORY.md`, it owns the canonical LLM orchestration for its domain. | Keep grizz as the security-and-safety exemplar. Extract its `llm-client.ts` as the basis of `@grizzwald/llm-client`, but do not treat the app itself as a library. |
| 8 | "Combination of CLIP + Granite-Docling + Qwen2.5-VL" as the image pipeline | OBSOLETE (partial) | Per `02_huggingface_reference.md`: (a) SigLIP 2 / DINOv3 dominate CLIP ViT-L/14 on zero-shot classification and feature quality. (b) GOT-OCR 2.0 (Apache-2.0, structured output for tables/charts/math) is a better fit than Granite-Docling 258M for screenshots specifically. (c) Qwen2.5-VL-7B-Instruct is **confirmed** as the VLM pick. | Swap CLIP -> SigLIP 2 base, Granite-Docling -> GOT-OCR 2.0, keep Qwen2.5-VL. |
| 9 | "CLIP ViT-L/14 should always run locally as stage 1" | OBSOLETE | SigLIP 2 base (93M) is cheaper and better than CLIP ViT-L/14 (428M); DINOv3 ViT-B/16 gives stronger frozen features at the same param count. Both are CPU-viable and local-first-friendly. | Replace CLIP with SigLIP 2 base for zero-shot; DINOv3 ViT-B/16 as the frozen backbone when a fine-tuned head is needed. |
| 10 | "Granite-Docling 258M is the OCR stage" | OBSOLETE | GOT-OCR 2.0 (560M, Apache-2.0) is trained for structured output — tables, charts, math, music — which is exactly what IDE/dashboard/study screenshots contain. Granite-Docling is document-layout focused; GOT is screenshot-native. | Use GOT-OCR 2.0 as the primary OCR stage. Retain Tesseract 5 as the "no-deps" floor. Drop Granite-Docling from the primary pipeline. |
| 11 | "Qwen2.5-VL-7B as the heavy VLM, API-first" | CONFIRMED | Both the user doc and the HF research independently pick Qwen2.5-VL-7B-Instruct. Apache-2.0, ~17GB bf16 VRAM, routed via HF Inference Providers (Hyperbolic, Fireworks, OVHcloud, Novita, Nscale, Together, Featherless, HF Inference — Cerebras and Groq are **LLM-only** so cannot serve this). | Keep Qwen2.5-VL. Apply `:cheapest` routing for batch, `:fastest` for interactive. Gate all VLM traffic at grizz's existing `$1/day` cap. |
| 12 | "Turborepo + pnpm workspaces" as the HBV scaffolding layout | CONTRADICTED | HBV's existing layout is `client/` + `server/` + `shared/` with a single `package.json`, Express 5, better-sqlite3 + Drizzle, Vitest, Playwright E2E, verified-build-gate. No monorepo. Forcing Turborepo onto it is a migration cost with no visible benefit — HBV has one API server, one React client, and one shared types module, which is a 3-package workspace that does not need Turborepo's caching. | Drop the Turborepo recommendation. Extend the existing `server/` and `client/` with new `server/pipeline/` and `server/vision/` sub-modules. |
| 13 | "Redis + BullMQ as the job queue backbone" | NEEDS INVESTIGATION / OBSOLETE | HBV already has `download-queue.ts` and `extraction-manager.ts` in `server/extraction/` — a working in-process queue with retry + event-bus. Adding Redis is net-new infrastructure for a single-machine desktop app. BullMQ's DAG is valuable only if pipeline complexity exceeds what `extraction-manager` can handle. | Reuse `server/extraction/` primitives. Introduce BullMQ only if a second worker process is ever needed. Redis is not justified today. |
| 14 | "SQLite FTS5 + sqlite-vec for search" | PARTIALLY CONFIRMED / CONTRADICTED | HBV already has the hybrid search **infrastructure**: `hybrid-search.ts` implements Reciprocal Rank Fusion (RRF with K=60, 0.4 keyword / 0.6 semantic weighting) over FTS5 keyword results and cosine-similarity vector results via `vector-search.ts` and `embedding-service.ts`. It currently indexes **documents**, not images. The primitive is proven and reusable; it just doesn't have an image corpus yet. | Reuse the RRF algorithm and `hybrid-search.ts` module verbatim. Add a new `image_embeddings` column to a new `images` table in `shared/schema.ts`. Do NOT re-architect search — write a thin adapter that feeds image rows into the same RRF function. |
| 15 | "Stage 1 Ingest via Chokidar v5" | NEEDS INVESTIGATION | HBV's `scheduler.ts` exists in `server/extraction/` for scheduled sync. A file watcher for image ingest is not visible — this is a legitimate greenfield addition. | Add `server/pipeline/image-watcher.ts` using Chokidar v5. This is the one piece of the user's pipeline spec that HBV does not already have. |
| 16 | "SSE over WebSocket for pipeline progress" | NEEDS INVESTIGATION / CONFIRMED | Defensible choice. HBV's current AI-event handler (`ai-event-handler.ts`) is in-process; a client-facing event stream is not wired. SSE is the right fit for the unidirectional case. | Add a single `GET /api/pipeline/events` SSE endpoint. Reuse the existing Express server. |
| 17 | Python FastAPI microservice for heavy VLMs | CONTRADICTED | HBV is TypeScript-only (`shared/schema.ts` is the single source of truth, validated by Zod server+client). Adding a Python service introduces a second runtime, a second dependency tree, a second deploy target, and a second test harness. It directly violates Marcus's 95/5 Rule. The routed HF Inference Providers path (`@huggingface/inference` in Node) covers Qwen2.5-VL without any Python. | Route VLM traffic through `@huggingface/inference` from Node. No Python microservice. Reserve Python only for training/fine-tuning work, which stays outside HBV. |
| 18 | "CLIP embeddings run inside Node via Transformers.js (ONNX)" | PARTIALLY OBSOLETE | The pattern is correct; the model is wrong. SigLIP 2 base has ONNX exports and runs in `@huggingface/transformers`. DINOv3 ViT-B/16 also has ONNX exports. | Run SigLIP 2 base in-process via `@huggingface/transformers`. Use DINOv3 ViT-B/16 as a frozen feature extractor when a fine-tuned head is wanted. |
| 19 | "`gte-modernbert-base` / `mxbai-embed-large-v1` for embeddings" (HF research) vs HBV's current `embedding-service.ts` | NEEDS INVESTIGATION | HBV's current embedding model is not visible in the audit (service exists, model choice is not). | Audit `server/ai/embedding-service.ts` and consider upgrading to `gte-modernbert-base` (149M, 8K context, Apache-2.0). Low-risk change; one-column reindex. |
| 20 | "HoneyBadgerVault Free/Pro/Team/Enterprise pricing" | CONFIRMED (structurally) | Freemium with usage metering is the correct SaaS pattern for this class of tool. No contradiction with audit. | Defer pricing specifics to `04_feature_gap_monetization.md` (task #4). |
| 21 | "Phase 1-4 roadmap across 16 weeks" | CONFIRMED (scaffold) / INCOMPLETE (coverage) | The 4-phase plan is structurally sound but covers only HBV + Bob + hints at grizz/BrightForge. It ignores the 4 non-flagship repos and the D:\BrightForge workspace hygiene problem. | Extend the roadmap with Section 5 of this document. |
| 22 | "HoneyBadgerVault is the natural home for an AI image pipeline" (implies image support is already there or near-there) | CONTRADICTED | HBV's current domain is **LMS document extraction**, not image management. `server/extraction/` contains `canvas-connector.ts`, `blackboard-connector.ts`, `moodle-connector.ts`, `playwright-connector.ts`, `generic-scraper.ts`. `shared/schema.ts` has zero references to `image`, `screenshot`, `png`, or `jpg` — the `documents` table stores PDFs and course materials via `mimeType`, not images. The AI integrations that exist (summarization, flashcards via `ts-fsrs`, knowledge graph extraction, OCR for document text) are all text-doc-centric. The image pipeline **does not exist yet** in HBV; it is entirely aspirational in the user's strategy doc. | Build the image pipeline as a **new subsystem** inside HBV (`server/pipeline/` + `server/vision/` + new `images` table) that **reuses ~80% of the existing infrastructure**: `base-connector.ts` pattern for vision workers, `download-queue.ts` primitives for the image job queue, `hybrid-search.ts` verbatim for image search, `ai-orchestrator.ts` consent gating for all VLM calls, Drizzle schema conventions for the new tables. The pipeline is net-new code; the plumbing is reused. |
| 23 | "BrightForge has a single canonical trunk" (implied by the strategy doc treating BrightForge as one project) | CONTRADICTED | There are **two divergent local branches of the same GitHub repo**. `D:\BrightForge` is at commit `46d1cd7 feat(idea): Idea Intelligence System (Phase 12)` and has `src/idea/` (7 files: ingestion/classifier/scoring/research/indexer/index/test-pipeline) but **lacks** `src/model-intelligence/`. `C:\Users\daley\Projects\BrightForge` is at Phase 10 `feat(model-intelligence): smart model routing and dashboard panel` and **has** `src/model-intelligence/` but **lacks** `src/idea/`. Both copies inherit the same mixed-workspace pollution (nested UE5 plugin, lab assignments, mangled `C:Usersdaley...` directories, stray `nul` file). Neither is canonical alone; the canonical trunk is the **merge** of both plus workspace hygiene. | Merge strategy: take D: as base (more recent HEAD, has Phase 12), cherry-pick `src/model-intelligence/` from Projects, run tests, push as the new trunk on `github.com/GrizzwaldHouse/BrightForge.git`. After merge, demote the Projects path to a read-only worktree or delete it. |
| 24 | "Free-first LLM fallback chain belongs in each repo" (implied by strategy doc not calling out duplication) | CONTRADICTED | The **same** free-first LLM fallback chain is reimplemented **four times** across the portfolio: `grizz-optimizer/src/main/ai/llm-client.ts` (5-tier: Ollama -> HF ONNX -> HF API -> Groq -> Cerebras, advisory-only, $1/day cap, most feature-rich), `BrightForge/src/core/llm-client.js` (9-provider YAML-driven, widest provider matrix), `Bob-AICompanion/src/core/llm-client.js` (8-provider, cleanest smallest surface area, zero exposed ports), and `SeniorDevBuddy/agentforge_autonomous/src/backend/services/ModelService.ts` (skeleton with intent for 7-provider chain). Four implementations of the same concept is exactly the 95/5 Rule anti-pattern. | Extract **one canonical package** as `@grizzwald/llm-client`. Base the core API on Bob's clean surface, absorb BrightForge's YAML-driven provider config and widest provider matrix, absorb grizz-optimizer's $1/day budget cap and advisory-only safety principle. Publish to GitHub Packages. Migrate HBV, Bob, SeniorDevBuddy to consume it. **grizz-optimizer keeps its own local copy** per `MEMORY.md` — its 5-tier chain has domain-specific Ollama lifecycle management (hardware detect, first-run pull, install-manager) that the generic package should not couple to. Result: one canonical library consumed by three repos, one domain-specific local copy in grizz. |

**Top reconciliation findings** (five, after team-lead correction):

1. **HoneyBadgerVault is a document-extraction vault, not an image vault — but its infrastructure is ~80% reusable for the image pipeline.** It already implements dual-provider consent-gated AI, RRF hybrid search, 17-table Drizzle schema, verified-build-gate, and Playwright E2E — all currently wired to LMS documents (Canvas/Blackboard/Moodle). The image pipeline is entirely net-new **as a subsystem**, but it should be built **inside** HBV by extending `server/extraction/` patterns, `hybrid-search.ts`, `ai-orchestrator.ts`, and the Drizzle schema. Greenfield code, brownfield plumbing.
2. **The Turborepo + Redis + BullMQ + Python FastAPI stack is wrong for HBV.** It adds three runtimes and two new infrastructure components to a working single-process Node monolith that already has a job queue (`download-queue.ts`), event bus (`event-bus.ts`), and TypeScript+Zod shared schema. Use Variant B of the revised pipeline below.
3. **CLIP + Granite-Docling is obsolete for the screenshot case.** Per the HF research, SigLIP 2 base (zero-shot, 93M) + GOT-OCR 2.0 (structured output, Apache-2.0, 560M) + Qwen2.5-VL-7B (confirmed) is strictly better. The classification/OCR pair both gain capability and shed licensing/runtime complexity.
4. **Neither BrightForge copy is canonical alone; the trunk must be a merge.** D: has Phase 12 Idea Intelligence (`src/idea/`); Projects has Phase 10 `src/model-intelligence/`. Both inherit the mixed-workspace pollution. The Phase 0 merge is the single largest tech-debt resolution in the portfolio.
5. **The free-first LLM fallback chain is duplicated four times across the portfolio.** grizz-optimizer, BrightForge, Bob, and SeniorDevBuddy each reimplement the same pattern. Extracting one canonical `@grizzwald/llm-client` package (with grizz-optimizer keeping a domain-specific local copy per MEMORY.md) eliminates weeks of drift risk and is a prerequisite for Variant B of the pipeline cleanly consuming the canonical chain.

---

## Section 2 — Revised Screenshot Intelligence Pipeline

Two variants, same business outcome (drop a screenshot into a watched folder, get it classified, OCR'd, described, renamed, indexed, searchable).

### Variant A — User's Original Spec (CLIP + Granite-Docling + Qwen2.5-VL, Turborepo, BullMQ+Redis, Python FastAPI)

```
                           +-------------------+
                           |  Chokidar watcher |
                           +---------+---------+
                                     |
                                     v
                           +-------------------+        +---------------+
                           |  BullMQ FlowProd  | <----> |    Redis      |
                           +---------+---------+        +---------------+
                                     |
             +-----------+-----------+-----------+-----------+
             |           |           |           |           |
             v           v           v           v           v
         +-------+  +---------+  +--------+  +---------+  +---------+
         | CLIP  |  |Granite- |  |Qwen2.5 |  | Rename  |  |SQLite   |
         |Trans- |  |Docling  |  |  -VL   |  | logic   |  |FTS5+vec |
         |former |  |FastAPI  |  |FastAPI |  |         |  |         |
         |.js    |  |(Python) |  |(Python)|  |         |  |         |
         +-------+  +---------+  +--------+  +---------+  +---------+
             ^           ^           ^                          |
             |           |           |                          v
             +--- HF Inference API (fallback) ---+         +---------+
                                                           |  React  |
                                                           |  SSE    |
                                                           +---------+
```

**Pros:**
- Clean separation of heavy Python inference from the Node API.
- BullMQ DAG natively supports parent/child job waiting.
- Redis-backed queue survives process restarts and enables horizontal scaling.

**Cons (vs. HBV reality):**
- **Two runtimes** (Node + Python) and **two dependency trees**. Violates 95/5.
- **Redis is new infrastructure** that HBV does not currently need or have.
- **Turborepo migration** requires restructuring an already-working `client/`+`server/`+`shared/` layout.
- **Duplicates existing HBV code**: `extraction-manager.ts`, `download-queue.ts`, `hybrid-search.ts`, `vector-search.ts`, `embedding-service.ts` are all rebuilt from scratch.
- **CLIP and Granite-Docling are both superseded** per HF research.

**Migration cost:** ~4 weeks of refactor work that delivers no new capability over Variant B. ~30% rework of HBV's existing `server/` directory.

**Timeline delta:** +2-3 weeks vs Variant B before the first working end-to-end screenshot → search result.

---

### Variant B — Audit-Aware HBV Extension (SigLIP 2 + GOT-OCR 2.0 + Qwen2.5-VL, extends existing HBV stack, no Turborepo/Redis/Python)

```
               HoneyBadgerVault Express server (existing)
   +--------------------------------------------------------------+
   |                                                              |
   |   +-------------------+     server/pipeline/ (NEW)           |
   |   | image-watcher.ts  |  (Chokidar v5, SHA-256 dedup)         |
   |   +---------+---------+                                      |
   |             |                                                |
   |             v                                                |
   |   +-------------------+                                      |
   |   | image-job-queue.ts|  <-- reuses server/extraction/       |
   |   |                   |      download-queue.ts primitives    |
   |   +---------+---------+                                      |
   |             |                                                |
   |    +--------+--------+--------+--------+--------+            |
   |    |        |        |        |        |        |            |
   |    v        v        v        v        v        v            |
   |  classify  ocr     describe  rename  index   broadcast       |
   |  worker    worker   worker    worker  worker    worker       |
   |    |        |         |        |       |        |            |
   |    v        v         v        v       v        v            |
   | SigLIP2  GOT-OCR   Qwen2.5    rule-  existing  existing      |
   | (local,   2.0      -VL-7B     based  hybrid-   SSE via       |
   | ONNX,    (routed   (routed    engine search    ai-event-     |
   | in-proc) HF)       HF)                reused   handler       |
   |    ^        ^         ^                                      |
   |    |        |         |                                      |
   |    +--- @huggingface/inference (Node) ---+                   |
   |                                                              |
   |   shared/schema.ts -- adds `images` table + `image_embeddings`|
   |                       column. Drizzle migration only.        |
   +--------------------------------------------------------------+
                              |
                              v
                    existing React client
                   (ImageGrid, SearchBar reuse
                    TanStack Query + existing
                    hybrid-search API)
```

**Pros:**
- **Zero new runtimes.** Pure TypeScript, all inference through `@huggingface/transformers` (local ONNX) or `@huggingface/inference` (routed).
- **Zero new infra.** No Redis, no Python, no FastAPI, no Turborepo. The existing Express process handles everything.
- **Reuses 70-80% of HBV internals**: `shared/schema.ts` gets one new table + one vector column, `hybrid-search.ts` is unchanged, `extraction-manager.ts` primitives back the new image job queue, `ai-orchestrator.ts`'s consent gating applies to the VLM calls too.
- **SigLIP 2 base ONNX is ~90MB** — ships with the app, runs on CPU, no first-run model pull required.
- **GOT-OCR 2.0 is Apache-2.0** — no licensing wrinkles, unlike Surya (NC license).
- **Consent-gated by construction.** The existing `checkAIConsent()` gate in `ai-orchestrator.ts:55` wraps VLM calls with zero additional work.
- **Marcus's universal coding standards apply directly**: no new dependency management, no new file header conventions, no access-control rewrites.

**Cons:**
- No horizontal scaling path until a second process is introduced later. For a single-user desktop app this is a **non-issue**.
- VLM traffic is routed (API) in the default config. Local-VLM users (RTX 4080+) can opt in via Ollama `qwen2.5vl:7b`, but that's a Phase-2 setting.
- SigLIP 2 base has fewer downstream fine-tuning examples than CLIP (smaller ecosystem), though the HF Transformers pipeline API covers the zero-shot path completely.

**Migration cost:** ~1 week to add `server/pipeline/` + `shared/schema.ts` migration + one React route. No refactor of existing code.

**Timeline delta:** -2-3 weeks vs Variant A (no Turborepo migration, no Python service bootstrap, no Redis deployment).

---

### Recommendation

**Adopt Variant B.** Justification:

1. **It matches reality.** HBV is not greenfield; rebuilding its job queue and search layer is pure waste.
2. **It matches Marcus's 95/5 Rule.** 95% of the work is config and small modules added to an existing system; Turborepo+Redis+Python+FastAPI would be ~40% new-runtime scaffolding.
3. **It matches the enterprise-secure-ai-engineering skill.** Reusing `ai-orchestrator.ts` consent gating means no parallel privacy codepath to audit.
4. **It matches the HF research.** SigLIP 2 + GOT-OCR 2.0 are strict upgrades over CLIP + Granite-Docling per `02_huggingface_reference.md`.
5. **It matches the BrightForge synergy.** VLM routing can reuse BrightForge's 9-provider chain once that is extracted as `@grizzwald/llm-client` — Variant A duplicates that logic.

**Variant A is a reasonable Phase-3 target** for a hypothetical multi-user SaaS deployment, not a Phase-1 starting point.

---

## Section 3 — Cross-Repo Architecture (8 Distinct Codebases)

```
                  ┌───────────────────────────────────────────────────┐
                  │   @grizzwald/llm-client  (NEW shared package)   │
                  │  Canonical 9-provider chain, extracted from       │
                  │  BrightForge src/core/llm-client.js               │
                  │  Ollama → Groq → Cerebras → Together → Mistral →  │
                  │  Gemini → Claude → OpenAI → OpenRouter            │
                  │  YAML-driven, $1/day budget enforced              │
                  └───────────────────────────────────────────────────┘
                               ▲        ▲        ▲        ▲
                    consumes   │        │        │        │
       ┌───────────────────────┴──┐     │        │        └──────────────────────────┐
       │                          │     │        │                                   │
       ▼                          ▼     │        ▼                                   ▼
┌─────────────┐           ┌──────────────┐  ┌───────────────┐                ┌─────────────┐
│  HBV        │           │ BrightForge  │  │ Bob-AI        │                │ grizz-      │
│ (flagship)  │           │ (canonical   │  │ Companion     │                │ optimizer   │
│             │           │  LLM source) │  │               │                │ (advisory   │
│  Screenshot │           │              │  │  Serverless   │                │  only)      │
│  Intel      │           │  Multi-agent │  │  via GH       │                │             │
│  (Variant B)│           │  AI studio   │  │  Actions      │                │  Electron + │
│             │           │              │  │               │                │  PowerShell │
│  ai-orch    │           │  Forge3D 3D  │  │  Job intel    │                │             │
│  +hybrid    │           │  pipeline    │  │  (fraud +     │                │  Red team   │
│  search     │           │              │  │  scoring)     │                │  scanner    │
│  +SigLIP2/  │           │  Idea Intel  │  │               │                │             │
│  GOT-OCR/   │           │  Phase 12    │  │  Morning brief│                │  5-tier AI  │
│  Qwen2.5-VL │           │              │  │  → Discord    │                │  fallback   │
└─────┬───────┘           └──────┬───────┘  └───────┬───────┘                └─────┬───────┘
      │                          │                  │                              │
      │  exposes                 │ exposes          │ exposes                      │ exposes
      │  MCP tools               │ MCP tools        │ MCP tools                    │ (runtime
      │  (search_images,         │ (generate_mesh,  │ (morning_brief,              │  errors)
      │  classify_batch,         │ plan_code_task,  │ score_job,                   │
      │  extract_text)           │ research_idea)   │ send_discord)                │
      │                          │                  │                              │
      ▼                          ▼                  ▼                              ▼
      ┌──────────────────────────────────────────────────────────────┐
      │       Bob-AICompanion (future Phase-3 MCP Unifier)           │
      │  MCP client that discovers and invokes tools from each repo  │
      │  via the Model Context Protocol. Single conversational       │
      │  entrypoint over the whole ecosystem.                        │
      └──────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ consumed by
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
      ┌──────────────┐    ┌────────────────┐   ┌──────────────────┐
      │ portfolio-   │    │ Developer      │   │ SeniorDevBuddy   │
      │ website      │    │ Productivity   │   │ (agentforge_     │
      │              │    │ Tracker        │   │ autonomous)      │
      │ Next.js 15   │    │ (UE5 Capstone) │   │                  │
      │              │    │                │   │ Next.js +        │
      │ ISR cards    │    │ C++ subsystem  │   │ Electron wrapper │
      │ pull live    │    │ DI, no AI      │   │                  │
      │ repo stats   │    │ today;         │   │ Replaces skeleton│
      │              │    │ opt-in AI      │   │ agents with      │
      │ Agent        │    │ layer via      │   │ BrightForge's    │
      │ sidecar      │    │ grizz-         │   │ tested ones      │
      │ migrates     │    │ optimizer      │   │                  │
      │ into Bob     │    │ HTTP bridge    │   │ Markdown         │
      │              │    │                │   │ orchestrator     │
      └──────┬───────┘    └────────────────┘   │ pattern extracts │
             │                                 │ to @grizzwald/   │
             │                                 │ markdown-        │
             │                                 │ orchestrator     │
             │                                 └──────────────────┘
             │
             ▼
      ┌──────────────────────────────┐
      │ @grizzwald/embeddings-index  │  (NEW shared package)
      │ Wraps HBV's hybrid-search    │
      │ (RRF + FTS5 + sqlite-vec)    │
      │ for reuse by SeniorDevBuddy  │
      │ skill/task retrieval         │
      └──────────────────────────────┘
```

**Shared components** (extract-then-consume pattern):

1. **`@grizzwald/llm-client`** — canonical LLM chain. Source: `BrightForge/src/core/llm-client.js`. Consumers: HBV (replaces `ai-orchestrator.ts`'s inline routing), Bob (already has a near-identical impl to merge), SeniorDevBuddy (replaces skeleton `ModelService.ts`), portfolio-website agent sidecar. grizz-optimizer keeps its own local copy because its 5-tier fallback has domain-specific Ollama lifecycle management that the generic package should not know about (see `MEMORY.md`).

2. **`@grizzwald/embeddings-index`** — hybrid BM25+vector search. Source: `HoneyBadgerVault/server/ai/hybrid-search.ts` + `vector-search.ts` + `embedding-service.ts`. Consumers: SeniorDevBuddy (task/skill retrieval), Bob (job corpus indexing), optionally ClaudeSkills (skill registry).

3. **`@grizzwald/connector-kit`** — base connector + retry + event bus. Source: `HoneyBadgerVault/server/extraction/base-connector.ts`. Consumers: Bob (Discord webhook adapter hardening), BrightForge (provider adapter hardening).

4. **`@grizzwald/secure-ipc`** — typed contextBridge + zod payloads. Source: `grizz-optimizer/src/main/ipc/`. Consumers: HBV Tauri shell, SeniorDevBuddy Electron wrapper.

5. **`@grizzwald/markdown-orchestrator`** — doctrine-as-code pattern. Source: `SeniorDevBuddy/grizz_modular_system/`. Consumers: ClaudeSkills, Bob (orchestration layer).

**Observer Pattern compliance**: Every repo in the diagram already uses events over polling (HBV `event-bus.ts`, BrightForge `ws-event-bus.js`, grizz-optimizer `runtime-error-bus`, portfolio-website re-entrancy-guarded Observer, UE5 `DeveloperProductivityTracker` subsystem events). The shared packages must expose event-emitter interfaces, never `poll()` APIs, per Marcus's universal coding standards.

---

## Section 4 — Per-Repo Architecture Targets

### 4.1 HoneyBadgerVault (HBV) — flagship

**Current:** Beta. **Domain: LMS document extraction vault**, not image management. Connectors for Canvas, Blackboard, Moodle, D2L, generic scraping, Playwright CDP. Express 5 + better-sqlite3 + Drizzle (17 tables, document-centric — zero references to `image`, `screenshot`, `png`, `jpg`). React+Vite client. Dual-provider AI orchestrator (Ollama+OpenAI, consent-gated via `checkAIConsent`). RRF hybrid search over FTS5 + vector cosine. ts-fsrs spaced repetition, flashcard generation, knowledge graph extraction, verification pipeline, tesseract OCR (document-level). Playwright E2E, verified-build-gate with 15 tests + pre-push hook. Tauri shell skeleton (not yet CI-packaged).

**Target:** Production dual-domain vault. Retains LMS extraction as the core business. **Adds Screenshot Intelligence as a parallel subsystem** (Variant B) — a new `server/pipeline/` + `server/vision/` module that reuses the existing `base-connector.ts`/`download-queue.ts`/`event-bus.ts`/`hybrid-search.ts`/`ai-orchestrator.ts` primitives for a **completely new corpus type** (images instead of documents). Also: `@grizzwald/llm-client` replaces inline provider routing in `ai-orchestrator.ts` (while `checkAIConsent` remains the outer gate), `@grizzwald/secure-ipc` hardens the Tauri boundary, encryption-at-rest verified with automated key-rotation test, Tauri CI packaging green, MCP server exposing `search_documents`, `search_images`, `classify_image`, `extract_text`, `generate_flashcards`.

**Gap:** New subsystem: `shared/schema.ts` gets a new `images` table with `image_embeddings` column; `server/pipeline/` (~6 files: watcher, job-queue, rename, index-adapter); `server/vision/` (~3 files: siglip2-classifier, got-ocr-worker, qwen-vlm-worker); React `ImageGrid` / `ImageDetail` routes. Existing code touched: `server/ai/ai-orchestrator.ts` refactored to consume `@grizzwald/llm-client`, `server/ai/hybrid-search.ts` adapter that accepts an image-corpus parameter. Infra: MCP server module, Tauri CI packaging pipeline, encryption-at-rest integration test. **Crucially: the LMS extractors are not modified** — the image pipeline runs alongside them on the same Express process, sharing the same Drizzle connection and same consent gate.

---

### 4.2 BrightForge — multi-agent AI studio + 3D

**Current (D: branch):** Beta. 9-provider LLM chain, full agent taxonomy, Forge3D SDXL+InstantMesh, Phase 12 Idea Intelligence. Workspace is polluted with a UE5 plugin clone, MarcusDaley_Lab3/4, mangled `C:Usersdaley...` path directories, and a stray `nul` file.

**Current (Projects branch):** Beta, slightly behind D:, but has a unique `src/model-intelligence/` smart-routing directory not in D:.

**Target:** Production-ready, single trunk. `src/core/llm-client.js` extracted as `@grizzwald/llm-client`. `src/model-intelligence/` merged into trunk. Workspace hygiene: nested unrelated projects moved to a sibling `_archive/` or deleted. Forge3D pipeline has a CI smoke test. vitest wrapping the existing `--test` blocks.

**Gap:** Branch merge (Projects model-intelligence -> D: trunk), workspace cleanup, LLM chain extraction, vitest migration, Forge3D CI smoke test, MCP server exposing `plan_code_task`, `generate_mesh`, `research_idea`, `score_idea`.

---

### 4.3 Bob-AICompanion — serverless automation + MCP unifier

**Current:** Beta. 8-provider YAML LLM chain, GitHub Actions cron, job-intelligence sub-system (fraud + scoring), Discord delivery. Zero exposed ports.

**Target:** Adds MCP client and server roles. As **client**, discovers and invokes tools from HBV, BrightForge, grizz-optimizer, SeniorDevBuddy. As **server**, exposes `morning_brief`, `score_job`, `check_fraud`, `send_discord` tools for other repos to call. Optional: always-on API host (Fly.io) for interactive use without waiting for cron. Replaces internal `src/core/llm-client.js` with `@grizzwald/llm-client`.

**Gap:** MCP client module, MCP server module, optional Fly.io deployment, `src/api/server.js` hardening with rate limiting, job-intelligence unit tests with adversarial fraud fixtures, README section for `job-intelligence/`.

---

### 4.4 grizz-optimizer — security + safety exemplar

**Current:** Alpha->Beta. Electron + PowerShell + 5-tier AI fallback, red team scanner, advisory-only AI, plugin SDK, RuntimeWatcher. Two acknowledged stubs: `execution.handler.ts` RUN dispatch and `install-manager.ts` model pull.

**Target:** Production. RUN dispatch wired to real PowerShell executor with `-WhatIf` dry runs and rollback manifests. `install-manager.ts` model pull implemented against real Ollama registry. Installer signing + notarization. Red team scanner runs as a CI gate on every PR.

**Gap:** Close the two stubs, signing/notarization pipeline, 55-test framework completion, red team CI gate. Does NOT consume `@grizzwald/llm-client` — keeps its domain-specific 5-tier chain per MEMORY.md. Does expose `@grizzwald/secure-ipc` as a package for reuse.

---

### 4.5 portfolio-website — portfolio + split sidecar

**Current:** Beta. Next.js 15 App Router, React 19, dual-platform deploy (Vercel + Netlify), GitHub ISR README enrichment, Full Sail design system, Observer with re-entrancy guard. `agents/ollama-listener.js` sidecar bolted on.

**Target:** Public portfolio stays. Agent sidecar is **moved to Bob-AICompanion** (same problem space). Resume PDFs and `Claude_task.txt` removed from `main` branch. Analytics (Plausible or Umami) added. Dedicated project cards for HBV, BrightForge, grizz-optimizer, DeveloperProductivityTracker linking to live demos. Unit test count stays at 50+.

**Gap:** Sidecar migration, PDF cleanup, analytics integration, project card content refresh, live demo URLs populated.

---

### 4.6 DeveloperProductivityTracker (UE5 Capstone)

**Current:** Beta, portfolio-ready. Cleanest expression of Marcus's coding standards anywhere in the portfolio. Subsystem-based DI, session tracking, Pomodoro, wellness, visualization, UI — all rule-based, no AI.

**Target:** Optional AI layer as opt-in upgrade. HTTP bridge exposes session data to `portfolio-website` ("Marcus has been coding for N hours today"). Optional Ollama integration via a bridge subsystem that calls `grizz-optimizer`'s local LLM for natural-language session summaries and burnout detection. Marketplace metadata populated. UE5 Automation Framework unit tests.

**Gap:** HTTP bridge subsystem, optional AI bridge, marketplace metadata, UE5 Automation Framework wiring, keyboard shortcut defaults.

---

### 4.7 SeniorDevBuddy / agentforge_autonomous

**Current:** Alpha. Markdown doctrine is complete; TypeScript agents are skeleton stubs. Zip archive graveyard at root. CI is a placeholder echo. Name mismatch between `package.json` and folder name.

**Target:** Alpha -> Beta. Skeleton agents replaced by **BrightForge's tested `planner-agent.js`, `builder-agent.js`, `reviewer-agent.js`, `tester-agent.js`** (same problem, working implementations exist one repo over). CI runs vitest + eslint on push. Zip archives moved to `archive/` or deleted. Folder renamed to match `package.json` or vice versa. Markdown orchestrator extracted as `@grizzwald/markdown-orchestrator`. Consumes `@grizzwald/llm-client` and `@grizzwald/embeddings-index` for skill retrieval.

**Gap:** Agent replacement (cross-repo refactor), CI wiring, workspace cleanup, naming reconciliation, package extraction.

---

### 4.8 D:\BrightForge mixed-workspace cleanup — pre-work

**Current:** Single D: directory contains the BrightForge trunk **plus**:
- `BrightForge/` — nested second copy
- `DeveloperProductivityTracker/` — nested UE5 plugin
- `MarcusDaley_Lab3/`, `MarcusDaleyComputer Graphics_lab4/` — Full Sail lab assignments
- `C:UsersdaleyProjectsBrightForge.githubworkflows`, `C:UsersdaleyProjectsBrightForgedocs`, `C:UsersdaleyProjectsBrightForgesrcapimiddleware`, `C:UsersdaleyProjectsLLCApppython`, `C:UsersdaleyProjectsLLCAppsrcforge3d` — mangled path-names from a failed recursive copy
- `nul` — a 0-byte file literally named `nul` (Windows reserved name, likely from a bad redirect)

**Target:** D:\BrightForge contains only the BrightForge trunk. Everything else moved to a new `D:\_archive\brightforge-workspace-2026-04/` subdirectory for preservation, or deleted after verification that nothing is referenced.

**Gap:** Manual audit of each stray directory to confirm no unique work, then move or delete. The `nul` file cannot be deleted with a normal `rm nul` on Windows — requires `del \\.\D:\BrightForge\nul`.

---

## Section 5 — Implementation Roadmap Extension

The user doc has 4 phases over 16 weeks focused on HBV + Bob + hints at BrightForge/grizz. This extension adds the 4 non-flagship repos, specific file paths, cross-repo dependencies, and — critically — a **Phase 0 / Pre-work block that BLOCKS user-doc Phase 1**. Per team-lead correction on 2026-04-08, doing these four pre-work tasks first saves weeks of rework later; attempting Phase 1 before Phase 0 means the image pipeline is built against divergent BrightForge branches, a misnamed HBV working copy, and four duplicate LLM clients that all drift independently.

### Phase 0 — BLOCKING Pre-work (Week 0, MUST complete before any user-doc Phase-1 feature work)

#### P0.1 — BrightForge canonical trunk merge (3-way merge, D: + Projects)

**Problem:** Neither `D:\BrightForge` (Phase 12, has `src/idea/`) nor `C:\Users\daley\Projects\BrightForge` (Phase 10, has `src/model-intelligence/`) is canonical alone. Both are divergent branches of `github.com/GrizzwaldHouse/BrightForge.git` with unique features the other lacks. The canonical trunk must be the **merged** result.

**Strategy (three-way merge with D: as base):**

1. From `D:\BrightForge`, confirm clean working tree and `git status` is empty apart from the mixed-workspace pollution slated for P0.2.
2. Create a feature branch: `git checkout -b feat/merge-phase10-model-intelligence`.
3. Add the Projects copy as a remote: `git remote add projects-copy C:\Users\daley\Projects\BrightForge` and `git fetch projects-copy`.
4. Cherry-pick the model-intelligence commit(s) from `projects-copy/main` into the new branch. If cherry-pick conflicts on shared files, resolve manually keeping D:'s Phase-12 additions intact.
5. Run `npm test` (all `--test` blocks) to verify neither `src/idea/` nor `src/model-intelligence/` is broken by the merge.
6. Push the feature branch to `origin`, open PR against `origin/main`, merge after self-review.
7. Demote `C:\Users\daley\Projects\BrightForge` to a read-only git worktree pointed at `origin/main`, or delete it entirely after confirming nothing unique remains.

**Files touched:** `D:\BrightForge\src\model-intelligence\` (new, cherry-picked), `D:\BrightForge\src\core\llm-client.js` (merge target if conflicts), `C:\Users\daley\Projects\BrightForge\` (demoted or deleted).

**Blocks:** P0.4 (LLM client extraction needs one canonical BrightForge source), Phase 1 BrightForge work.

#### P0.2 — Workspace hygiene cleanup (prune pollution from both BrightForge copies)

**Problem:** `D:\BrightForge` contains a nested `BrightForge/` sub-directory (second full copy of the project), a `DeveloperProductivityTracker/` clone of the UE5 Capstone, `MarcusDaley_Lab3/` and `MarcusDaleyComputer Graphics_lab4/` Full Sail lab assignments, several mangled-path directories from a failed recursive copy (`C:UsersdaleyProjectsBrightForge.githubworkflows`, `C:UsersdaleyProjectsBrightForgedocs`, `C:UsersdaleyProjectsBrightForgesrcapimiddleware`, `C:UsersdaleyProjectsLLCApppython`, `C:UsersdaleyProjectsLLCAppsrcforge3d`), and a literal `nul` file (a Windows reserved name, likely from a bad shell redirect). The Projects copy inherits a subset of the same pollution.

**Strategy:**

1. Create `D:\_archive\brightforge-workspace-2026-04\` as the quarantine target.
2. For each polluted directory, audit with `ls` for anything that could contain unique work before moving. Directories named after Full Sail courses or mangled `C:Usersdaley...` paths are almost certainly safe to move unread — they're accidents of a failed copy.
3. Move all polluted directories: `move D:\BrightForge\BrightForge D:\_archive\brightforge-workspace-2026-04\nested-brightforge-copy`, and similarly for `DeveloperProductivityTracker/`, `MarcusDaley_Lab3/`, `MarcusDaleyComputer Graphics_lab4/`, and each `C:Usersdaley...` directory.
4. Delete the `nul` file using the Windows UNC path syntax: `del \\.\D:\BrightForge\nul` (a normal `rm nul` will fail because Windows reserves the name).
5. Repeat the cleanup for `C:\Users\daley\Projects\BrightForge\` — same polluted directory names, same strategy.
6. Verify `git status` shows only intentional changes; commit workspace-hygiene commit.

**Files touched:** `D:\BrightForge\BrightForge\`, `D:\BrightForge\DeveloperProductivityTracker\`, `D:\BrightForge\MarcusDaley_Lab3\`, `D:\BrightForge\MarcusDaleyComputer Graphics_lab4\`, `D:\BrightForge\C:Usersdaley*\` (all 5), `D:\BrightForge\nul`, `C:\Users\daley\Projects\BrightForge\` (equivalent subset).

**Blocks:** P0.1 (merge is easier on a clean working tree), portfolio presentation.

#### P0.3 — Agent-Alexander / HoneyBadgerVault name reconciliation

**Problem:** `D:\Agent-Alexander` is a working copy whose `origin` points at `github.com/GrizzwaldHouse/HoneyBadgerVault.git`. The directory name and the repo name are out of sync. "Agent-Alexander" is an internal codename; "HoneyBadgerVault" is the public product name. Two identities for one codebase causes script path drift, documentation confusion, and audit-trail noise.

**Strategy (keep the public name, archive the codename):**

1. Close any open editors, terminals, or IDEs pointed at `D:\Agent-Alexander\`.
2. Rename the working copy: `move D:\Agent-Alexander D:\HoneyBadgerVault`.
3. Re-open the project in IDE; verify `git status` still works and `git remote -v` still points at the correct origin.
4. Grep the entire portfolio for any scripts, CI workflows, docs, or tool configs referencing `D:\Agent-Alexander` and update them to `D:\HoneyBadgerVault`. Likely hits: `MEMORY.md`, `CLAUDE.md`, any build-gate scripts, VS Code workspace files.
5. If no unique work remains under the old name, the rename is complete. If a duplicate clone exists anywhere, delete the duplicate after verifying no unique branches.

**Files touched:** `D:\Agent-Alexander\` → `D:\HoneyBadgerVault\` (full directory rename). Grep-driven path updates across `MEMORY.md`, shell aliases, CI workflows.

**Blocks:** Phase 1 HBV work (confused paths cause CI failures and imports).

#### P0.4 — Extract `@grizzwald/llm-client` canonical package

**Problem:** The same free-first LLM fallback chain is reimplemented **four times** across the portfolio: `grizz-optimizer/src/main/ai/llm-client.ts` (5-tier Ollama -> HF ONNX -> HF API -> Groq -> Cerebras, advisory-only, $1/day cap, most feature-rich), `BrightForge/src/core/llm-client.js` (9-provider YAML-driven), `Bob-AICompanion/src/core/llm-client.js` (8-provider, cleanest small surface), `SeniorDevBuddy/agentforge_autonomous/src/backend/services/ModelService.ts` (skeleton). Four duplicates drift independently — a bug fix in one never propagates to the others.

**Strategy:**

1. Create a new repo `github.com/GrizzwaldHouse/llm-client` (or a `packages/llm-client/` workspace inside an existing monorepo if a shared repo emerges).
2. **API surface** (adopted from Bob's clean small surface):
   - `class UniversalLLMClient(configOverride?)` constructor reads `config/llm-providers.yaml` by default.
   - Methods: `chat(messages, options)`, `complete(prompt, options)`, `embed(texts, options)` (where applicable), `getDailyUsage()`, `isProviderAvailable(name)`.
   - `options` includes `task`, `preferredProvider`, `timeout`, `maxTokens`.
3. **Provider matrix** (adopted from BrightForge's widest provider list): Ollama, Groq, Cerebras, Together, Mistral, Gemini, Claude, OpenAI, OpenRouter. Plus HF Inference Providers with `:cheapest` / `:fastest` routing hints (new, not in any existing copy).
4. **Safety features** (adopted from grizz-optimizer's hardening): $1/day budget cap, advisory-only AI principle (configurable flag that routes all responses through a "suggest-don't-execute" wrapper), circuit breaker on repeated failures, health cache to avoid repeated timeouts, telemetry hooks.
5. **Config schema:** YAML with `providers.<name>.{enabled, base_url, api_key_env, models, priority, cost_per_1k_tokens}` and `task_routing.<task>.{prefer[], fallback}`. Validated by Zod at construction time.
6. **Migration order:**
   - HBV: replace inline routing in `server/ai/ai-orchestrator.ts` — it continues to own the `checkAIConsent()` gate as the outer boundary; `UniversalLLMClient` sits inside the gate. `ai-orchestrator.ts` becomes a thin wrapper: consent check -> `client.chat(...)`.
   - Bob: delete `src/core/llm-client.js`, import from `@grizzwald/llm-client`. The YAML config in `config/llm-providers.yaml` is already compatible.
   - SeniorDevBuddy: delete skeleton `ModelService.ts`, import from `@grizzwald/llm-client`. Wire into the existing `AgentOrchestrator.ts` parallel executor.
   - **grizz-optimizer DOES NOT migrate.** Per `MEMORY.md`, it keeps its own local `src/main/ai/llm-client.ts` because its 5-tier chain has domain-specific Ollama lifecycle management (`ollama/manager.ts`, `ollama/first-run.ts`, `ollama/hardware-detect.ts`) that should not couple to a generic package. The canonical API can be informed by grizz's implementation but grizz does not consume the package.
7. Publish to GitHub Packages (`@grizzwald/llm-client` scoped to GrizzwaldHouse org) or npm public.

**Files touched:** `packages/llm-client/src/` (new), `HoneyBadgerVault/server/ai/ai-orchestrator.ts` (refactor), `Bob-AICompanion/src/core/llm-client.js` (delete), `SeniorDevBuddy/agentforge_autonomous/src/backend/services/ModelService.ts` (delete or delegate), `BrightForge/src/core/llm-client.js` (source reference, not modified).

**Blocks:** Phase 1 HBV work on routing (task 2.3 in the original roadmap), Phase 2 Bob migration, Phase 3 SeniorDevBuddy agent replacement.

#### P0.5 through P0.8 — Non-blocking housekeeping (can run in parallel with feature work)

| Task | Paths | Dependency | Cross-repo? |
|---|---|---|---|
| P0.5 SeniorDevBuddy: move `*.zip` archives from root to `archive/` | `C:\Users\daley\Projects\SeniorDevBuddy\*.zip` | None | No |
| P0.6 SeniorDevBuddy: resolve name mismatch (`agentforge_autonomous` folder vs `agentforge-observability` in `package.json`) | `C:\Users\daley\Projects\SeniorDevBuddy\agentforge_autonomous\package.json` | None | No |
| P0.7 portfolio-website: remove resume PDFs + `Claude_task.txt` from `main` branch, archive under `.local/` (gitignored) | `D:\portfolio-website\*.pdf`, `Claude_task.txt` | None | No |
| P0.8 SeniorDevBuddy: consolidate `grizz_modular_system_fixed/` mirror into `grizz_modular_system/` with a CI copy script if a mirror is truly needed | `C:\Users\daley\Projects\SeniorDevBuddy\grizz_modular_system_fixed\` | None | No |

**Phase 0 exit criteria:** single canonical BrightForge trunk pushed to origin, both BrightForge workspaces hygienic, `D:\HoneyBadgerVault` is the only HBV working copy and path references are updated, `@grizzwald/llm-client` published and HBV+Bob+SeniorDevBuddy migrated. Only then does user-doc Phase 1 begin.

### Phase 1 — Foundation Sprint (Weeks 1-3) — extended from user doc

| Task | Paths | Dependency | Cross-repo? |
|---|---|---|---|
| 1.1 HBV: add `images` table + `image_embeddings` column to `shared/schema.ts` Drizzle schema, write migration | `D:\HoneyBadgerVault\shared\schema.ts`, `server/db/migrations/` | P0.1 | No |
| 1.2 HBV: create `server/pipeline/` with `image-watcher.ts` (Chokidar v5, SHA-256 dedup) | `D:\HoneyBadgerVault\server\pipeline\image-watcher.ts` | 1.1 | No |
| 1.3 HBV: create `server/pipeline/image-job-queue.ts` reusing `server/extraction/download-queue.ts` primitives | `D:\HoneyBadgerVault\server\pipeline\image-job-queue.ts`, `server/extraction/download-queue.ts` | 1.2 | No |
| 1.4 HBV: create `server/vision/siglip2-classifier.ts` using `@huggingface/transformers` with ONNX SigLIP 2 base | `D:\HoneyBadgerVault\server\vision\siglip2-classifier.ts` | 1.2 | No |
| 1.5 HBV: write model download script (SigLIP 2 base ONNX into `models/` cache, gitignored) | `D:\HoneyBadgerVault\scripts\download-vision-models.ts` | 1.4 | No |
| 1.6 HBV: React client — add `ImageGrid.tsx` and `ImageDetail.tsx` to `client/src/pages/` reusing TanStack Query + existing hybrid-search API | `D:\HoneyBadgerVault\client\src\pages\ImageGrid.tsx`, `ImageDetail.tsx` | 1.1-1.4 | No |
| 1.7 HBV: vitest coverage for new `server/pipeline/` and `server/vision/` modules, minimum 80% | `D:\HoneyBadgerVault\server\pipeline\*.test.ts` | 1.2-1.4 | No |
| 1.8 BrightForge: wrap 40+ `--test` blocks in vitest runner so CI produces coverage (extraction of the LLM chain already completed in P0.4) | `D:\BrightForge\vitest.config.js`, package.json scripts | P0.2 | No |

**Goal:** Drop a screenshot into a watched folder → see it classified (SigLIP 2), persisted, and searchable via the existing hybrid search in under 5 seconds. BrightForge vitest migration complete so CI produces real coverage. (The `@grizzwald/llm-client` extraction was Phase 0; Phase 1 consumes it.)

### Phase 2 — AI Depth (Weeks 4-6) — extended

| Task | Paths | Dependency | Cross-repo? |
|---|---|---|---|
| 2.1 HBV: create `server/vision/got-ocr-worker.ts` routing to GOT-OCR 2.0 via `@huggingface/inference` (routed, `:cheapest`) | `D:\HoneyBadgerVault\server\vision\got-ocr-worker.ts` | 1.2 | No |
| 2.2 HBV: create `server/vision/qwen-vlm-worker.ts` routing to Qwen2.5-VL-7B via `@huggingface/inference` with `:cheapest` routing and `response_format: json_object` | `D:\HoneyBadgerVault\server\vision\qwen-vlm-worker.ts` | 1.2 | No |
| 2.3 HBV: VERIFY that Phase 0's `@grizzwald/llm-client` migration (from P0.4) is consumed by `server/ai/ai-orchestrator.ts` and that `checkAIConsent` still wraps all `client.chat()` calls | `D:\HoneyBadgerVault\server\ai\ai-orchestrator.ts` | P0.4 | Yes |
| 2.4 HBV: implement rename+organize engine as `server/pipeline/intelligent-rename.ts`, rule-based + VLM-suggested, user-override-able | `D:\HoneyBadgerVault\server\pipeline\intelligent-rename.ts` | 2.2 | No |
| 2.5 HBV: add SSE endpoint `GET /api/pipeline/events` for React progress monitoring, reusing `server/ai/ai-event-handler.ts` as the event source | `D:\HoneyBadgerVault\server\routes\pipeline.ts`, `client/src/hooks/usePipelineEvents.ts` | 1.2 | No |
| 2.6 HBV: verify encryption-at-rest (`server/encryption.ts`) with automated key-rotation integration test | `D:\HoneyBadgerVault\server\encryption.ts`, `server/encryption.test.ts` | None | No |
| 2.7 HBV: audit `server/ai/embedding-service.ts` current model choice, upgrade to `Alibaba-NLP/gte-modernbert-base` if not already | `D:\HoneyBadgerVault\server\ai\embedding-service.ts` | None | No |
| 2.8 Bob: VERIFY that P0.4's migration to `@grizzwald/llm-client` is complete and the local `src/core/llm-client.js` has been deleted; add a regression test that fails if the local file ever re-appears | `C:\Users\daley\Projects\Bob-AICompanion\src\core\llm-client.js` (deleted), `tests/package-migration.test.js` (new) | P0.4 | Yes |
| 2.9 Bob: add unit tests with adversarial fraud fixtures to `src/job-intelligence/fraud-detector.js` | `C:\Users\daley\Projects\Bob-AICompanion\src\job-intelligence\fraud-detector.test.js` | None | No |

**Goal:** Full five-stage pipeline operational (Ingest → Classify → Extract → Rename → Index). VLM calls consent-gated, $1/day budget enforced. `@grizzwald/llm-client` verified-in-consumption across HBV and Bob with regression tests that fail if any local copies re-appear.

### Phase 3 — Polish and Ecosystem (Weeks 7-10) — extended

| Task | Paths | Dependency | Cross-repo? |
|---|---|---|---|
| 3.1 HBV: MCP server module exposing `search_documents`, `search_images`, `classify_image`, `extract_text`, `generate_flashcards` | `D:\HoneyBadgerVault\server\mcp\` | Phase 2 | Yes |
| 3.2 HBV: Tauri CI packaging pipeline green (GitHub Action produces signed `.msi`) | `D:\HoneyBadgerVault\src-tauri\`, `.github\workflows\tauri-build.yml` | 2.6 | No |
| 3.3 BrightForge: MCP server module exposing `plan_code_task`, `generate_mesh`, `research_idea`, `score_idea` | `D:\BrightForge\src\mcp\` | P0.4, 1.8 | Yes |
| 3.4 BrightForge: Forge3D CI smoke test (text → image → mesh), GPU-optional | `D:\BrightForge\test\forge3d-smoke.test.js`, `.github\workflows\forge3d.yml` | 1.8 | No |
| 3.5 Bob: MCP client module — discovers tools from HBV, BrightForge, SeniorDevBuddy | `C:\Users\daley\Projects\Bob-AICompanion\src\mcp\client.js` | 3.1, 3.3, 3.8 | Yes |
| 3.6 Bob: MCP server module exposing `morning_brief`, `score_job`, `check_fraud`, `send_discord` | `C:\Users\daley\Projects\Bob-AICompanion\src\mcp\server.js` | None | Yes |
| 3.7 grizz-optimizer: close `execution.handler.ts` RUN stub and `install-manager.ts` model-pull stub | `C:\Users\daley\grizz-optimizer\src\main\execution\handler.ts`, `src\main\ai\install-manager.ts` | None | No |
| 3.8 SeniorDevBuddy: replace skeleton agents with BrightForge's `planner`/`builder`/`reviewer`/`tester`-agent.js, now importing from `@grizzwald/llm-client` | `C:\Users\daley\Projects\SeniorDevBuddy\agentforge_autonomous\src\agents\` | P0.4 | Yes |
| 3.9 SeniorDevBuddy: wire real CI (vitest + eslint), not placeholder echo | `.github\workflows\ci.yml` | None | No |
| 3.10 portfolio-website: migrate `agents/ollama-listener.js` sidecar into Bob-AICompanion, delete from portfolio repo | `D:\portfolio-website\agents\`, `C:\Users\daley\Projects\Bob-AICompanion\src\integrations\` | 2.8 | Yes |
| 3.11 portfolio-website: add Plausible or Umami analytics | `D:\portfolio-website\src\app\layout.tsx` | None | No |
| 3.12 DeveloperProductivityTracker: HTTP bridge subsystem exposing session data | `D:\FSO\Capstone Project\DeveloperProductivityTracker\Source\...\Public\External\SessionHttpBridge.h` | None | No |
| 3.13 DeveloperProductivityTracker: wire UE5 Automation Framework for unit tests | `D:\FSO\Capstone Project\DeveloperProductivityTracker\Source\...\Tests\` | None | No |
| 3.14 grizz-optimizer: extract `src/main/ipc/` as `@grizzwald/secure-ipc` package | `C:\Users\daley\grizz-optimizer\src\main\ipc\`, `packages/secure-ipc/` | None | Yes |
| 3.15 Deploy HBV demo to HuggingFace Space (Docker-based, free CPU) | HF Space: `grizzwaldhouse/honeybadgervault-demo` | 3.2 | No |

**Goal:** MCP ecosystem operational — Bob can drive HBV, BrightForge, and SeniorDevBuddy from a single conversational surface. All repos have real CI. portfolio-website has a live demo link per project. Shared packages on npm or GitHub Packages.

### Phase 4 — Monetization, Education, Non-flagship Depth (Weeks 11-16) — extended

| Task | Paths | Dependency | Cross-repo? |
|---|---|---|---|
| 4.1 HBV: usage metering middleware (every inference call logged with user, model, tokens, cost) | `D:\HoneyBadgerVault\server\middleware\metering.ts` | Phase 3 | No |
| 4.2 HBV: freemium tier enforcement (Free/Pro/Team/Enterprise) behind metering | `D:\HoneyBadgerVault\server\middleware\billing-gate.ts` | 4.1 | No |
| 4.3 HBV: BYOK flow (user provides own HF token, bypasses grizz $1/day cap) | `D:\HoneyBadgerVault\server\routes\settings.ts` | 4.1 | No |
| 4.4 Bob: always-on host on Fly.io (optional, gated by user decision) | `C:\Users\daley\Projects\Bob-AICompanion\fly.toml` | Phase 3 | No |
| 4.5 Bob: educational quest system — progressive challenges teaching AI pipeline concepts | `C:\Users\daley\Projects\Bob-AICompanion\src\quests\` | 3.5, 3.6 | No |
| 4.6 DeveloperProductivityTracker: optional AI layer consumes grizz-optimizer Ollama endpoint for session summaries | UE5 `SessionAISubsystem.h` + grizz-optimizer HTTP endpoint | 3.7, 3.12 | Yes |
| 4.7 portfolio-website: live project cards for HBV, BrightForge, grizz-optimizer with demo links | `D:\portfolio-website\src\data\projects.ts` | 3.15 | No |
| 4.8 SeniorDevBuddy: markdown orchestrator extracted as `@grizzwald/markdown-orchestrator` package | `C:\Users\daley\Projects\SeniorDevBuddy\grizz_modular_system\`, `packages/markdown-orchestrator/` | 3.8 | Yes |
| 4.9 grizz-optimizer: installer signing + notarization + red team CI gate | `C:\Users\daley\grizz-optimizer\.github\workflows\` | 3.7 | No |
| 4.10 Cross-repo: landing page validating willingness to pay for HBV (Gumroad pre-order link or equivalent) | `D:\portfolio-website\src\app\hbv\page.tsx` | 4.1-4.3 | No |

**Goal:** First paying HBV users. Educational quest system live in Bob. All 8 codebases have CI green, MCP-enabled where applicable, real demo links. The ecosystem tells a single story: local-first AI ingestion → multi-agent generation → cross-repo orchestration → advisory safety → coding-standards exemplar.

---

## Appendix A — Cross-Repo Dependency Graph

```
@grizzwald/llm-client  ◄── BrightForge (source)
          ▲
          ├── HBV (consumer, Phase 2.3)
          ├── Bob (consumer, Phase 2.8)
          └── SeniorDevBuddy (consumer, Phase 3.8 via BrightForge agents)

@grizzwald/embeddings-index  ◄── HBV (source)
          ▲
          └── SeniorDevBuddy (consumer, skill retrieval)

@grizzwald/secure-ipc  ◄── grizz-optimizer (source, Phase 3.14)
          ▲
          ├── HBV Tauri shell (consumer)
          └── SeniorDevBuddy Electron wrapper (consumer)

@grizzwald/markdown-orchestrator  ◄── SeniorDevBuddy (source, Phase 4.8)
          ▲
          ├── ClaudeSkills (consumer)
          └── Bob MCP (consumer)

@grizzwald/connector-kit  ◄── HBV (source)
          ▲
          ├── Bob Discord webhook (consumer)
          └── BrightForge provider adapters (consumer)
```

## Appendix B — Model Migration Delta (User Doc → This Doc)

| Stage | User Doc Pick | This Doc Pick | Rationale |
|---|---|---|---|
| Zero-shot classification | `openai/clip-vit-large-patch14` (428M) | `google/siglip2-base-patch16-224` (93M) | 4.6x smaller, higher zero-shot accuracy, Apache-2.0, sigmoid loss better-suited to multi-label. |
| Frozen feature extractor | (same CLIP) | `facebook/dinov3-vitb16-pretrain-lvd1689m` (86M) | SOTA self-supervised features for retrieval and downstream heads. |
| OCR | `ibm-granite/granite-docling-258M` (258M) | `stepfun-ai/GOT-OCR-2.0-hf` (560M) | Trained for structured output (tables, charts, math, music) — exactly what screenshots contain. Apache-2.0. |
| VLM | `Qwen/Qwen2.5-VL-7B-Instruct` | `Qwen/Qwen2.5-VL-7B-Instruct` | CONFIRMED. Both docs independently pick this. |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (implied) | `Alibaba-NLP/gte-modernbert-base` (149M) | ModernBERT 8K context, CLS pooling, Apache-2.0, matches BGE-large at 45% of the size. |
| Inference runtime | Python FastAPI microservice | `@huggingface/inference` + `@huggingface/transformers` in Node | Zero new runtime. Matches HBV's TypeScript-only architecture. |
| Job queue | BullMQ + Redis | Reuse HBV `server/extraction/download-queue.ts` | Zero new infrastructure. Single-machine desktop app does not need horizontal scaling. |
| Monorepo tool | Turborepo + pnpm workspaces | Keep HBV's existing `client/`+`server/`+`shared/` layout | HBV does not need a monorepo tool; it has a 3-package workspace. |

---

*End of architecture design — architect, ai-audit-2026, 2026-04-08.*
