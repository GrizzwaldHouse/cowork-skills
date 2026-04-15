# AI Audit 2026 — Unified Execution Blueprint

**Team:** ai-audit-2026 | **Compiled:** 2026-04-08
**Source reports:** `00_user_strategy_doc.md`, `01_repo_audit.md`, `02_huggingface_reference.md`, `03_architecture_design.md`, `04_strategy.md`
**Resolution rule applied:** Later reports override earlier ones (04 > 03 > 02 > 01 > 00). Audit is ground truth on code; user doc is authoritative on intent.

---

## 1. Executive Summary

- Portfolio contains **8 distinct codebases**, not 4. `D:\Agent-Alexander` and `HoneyBadgerVault` are the same git repo [see 01_repo_audit.md Critical Finding].
- **HoneyBadgerVault is beta LMS document extraction**, not a greenfield image vault. The image pipeline is additive on ~80% reusable infrastructure (Variant B) [see 03_architecture_design.md section 2 Variant B].
- **Model stack locked:** SigLIP 2 base + GOT-OCR 2.0 + Qwen2.5-VL-7B-Instruct + gte-modernbert-base + Qwen2.5-Coder-32B. CLIP + Granite-Docling + Python FastAPI from the user doc are obsolete [see 02_huggingface_reference.md sections 1-5, 03_architecture_design.md Appendix B].
- **Four Phase-0 blockers** must complete before any feature work: BrightForge branch merge, workspace hygiene, HBV rename, `@grizzwald/llm-client` extraction [see 03_architecture_design.md section 5 Phase 0].
- **Year-1 revenue reality:** freelance + job offers ($30k-$80k) dwarf all SaaS attempts combined ($4.5k-$20.5k). Build products as portfolio proof, run freelance as income [see 04_strategy.md section 2.5, Monetization Summary Table].

---

## 2. Final Unified Architecture

```
                  +-----------------------------------------------+
                  |  @grizzwald/llm-client   (NEW shared package) |
                  |  Source: BrightForge src/core/llm-client.js   |
                  |  Ollama -> Groq -> Cerebras -> Together ->    |
                  |  Mistral -> Gemini -> Claude -> OpenAI ->     |
                  |  OpenRouter + HF Inference Providers routing  |
                  |  YAML-driven, $1/day budget cap enforced      |
                  +-----------------------------------------------+
                       ^        ^        ^                ^
            consumes   |        |        |                | (NOT consumed)
            +----------+        |        +--------+       |
            |                   |                 |       |
            v                   v                 v       |
     +-------------+     +--------------+  +------------+ |
     |  HBV        |     | BrightForge  |  | Bob-AI     | |   +--------------+
     | (flagship)  |     | (canonical   |  | Companion  | |   | grizz-       |
     |             |     |  LLM source) |  |            | |   | optimizer    |
     | Screenshot  |     | Multi-agent  |  | Serverless | |   | (domestic    |
     | Intel via   |     | AI studio +  |  | GH Actions | |   | 5-tier)      |
     | Variant B:  |     | Forge3D +    |  | Morning    | |   |              |
     | SigLIP2 /   |     | Idea Intel   |  | brief +    | |   | Electron +   |
     | GOT-OCR /   |     | Phase 12     |  | job intel  | |   | PowerShell + |
     | Qwen2.5-VL  |     |              |  |            | |   | red team     |
     | over Express|     | Merged       |  |            | |   | scanner      |
     | + Drizzle + |     | trunk (D: +  |  |            | |   |              |
     | RRF hybrid  |     | Projects)    |  |            | |   | Keeps own    |
     | search      |     |              |  |            | |   | llm-client   |
     +------+------+     +------+-------+  +-----+------+ |   +------+-------+
            |                   |                |        |          |
            | MCP tools         | MCP tools      | MCP    |          | (runtime
            | search_images     | plan_code_task | tools  |          |  errors)
            | classify_image    | generate_mesh  |        |          |
            | extract_text      | research_idea  |        |          |
            v                   v                v        |          v
     +----------------------------------------------------+----------+
     |  Bob-AICompanion MCP Unifier (Phase 3 role)                   |
     |  MCP client discovers tools from all sibling repos via        |
     |  @modelcontextprotocol/sdk. Single conversational surface.    |
     +----------------------------+----------------------------------+
                                  ^
                                  | consumed by
                 +----------------+--------------+
                 |                |               |
                 v                v               v
         +--------------+  +------------+  +----------------+
         | portfolio-   |  | Developer  |  | SeniorDevBuddy |
         | website      |  | Productiv- |  | (agentforge_   |
         |              |  | ityTracker |  |  autonomous)   |
         | Next.js 15   |  | UE5 C++    |  |                |
         | ISR cards    |  | subsystem  |  | Skeleton TS    |
         | agent side-  |  | DI, rule-  |  | agents replaced|
         | car migrates |  | based only |  | with Bright-   |
         | into Bob     |  | + HTTP     |  | Forge agents   |
         |              |  | bridge     |  |                |
         +------+-------+  +------------+  +-------+--------+
                |                                  |
                v                                  v
         +-------------------------+   +----------------------------+
         | @grizzwald/embeddings-  |   | @grizzwald/markdown-       |
         |   index (from HBV       |   |   orchestrator (from       |
         |   hybrid-search.ts)     |   |   SeniorDevBuddy doctrine) |
         +-------------------------+   +----------------------------+
```

---

## 3. Final Model Stack

All model picks reconciled from [02_huggingface_reference.md sections 1-5] and [03_architecture_design.md Appendix B Model Migration Delta].

| Task | Primary | Fallback | Runtime | License |
|---|---|---|---|---|
| Zero-shot image classification | `google/siglip2-base-patch16-224` (93M) | `google/vit-base-patch16-224` | `@huggingface/transformers` local ONNX | Apache-2.0 |
| OCR (structured screenshots) | `stepfun-ai/GOT-OCR-2.0-hf` (560M) | Tesseract 5 (floor) | `@huggingface/inference` routed `:cheapest` | Apache-2.0 |
| Vision-Language (description) | `Qwen/Qwen2.5-VL-7B-Instruct` (8.3B) | `Qwen/Qwen2.5-VL-3B-Instruct` | HF Inference Providers (Hyperbolic / OVHcloud / Together / Nscale / Featherless / Novita / HF Inference). **NOT Cerebras, NOT Groq** [see 02_huggingface_reference.md section 6 provider matrix]. | Apache-2.0 |
| Embeddings (RAG + hybrid search) | `Alibaba-NLP/gte-modernbert-base` (149M, 8K ctx) | `mixedbread-ai/mxbai-embed-large-v1` | `@huggingface/inference` (`hf-inference` provider) or local | Apache-2.0 |
| Code analysis (Qwen2.5-Coder-32B) | `Qwen/Qwen2.5-Coder-32B-Instruct` | `Qwen/Qwen2.5-Coder-7B-Instruct` (local GGUF) | HF Inference Providers (Nscale / Featherless / Scaleway) | Apache-2.0 |

---

## 4. Repo Role Map

Sourced from [01_repo_audit.md sections 1-8], [04_strategy.md section 2 Monetization Summary Table], and [03_architecture_design.md section 4 Per-Repo Architecture Targets].

| Repo | Role | Maturity | Next Action | Monetization |
|---|---|---|---|---|
| **HoneyBadgerVault** (was `D:\Agent-Alexander`) | LMS doc vault + added Screenshot Intelligence subsystem (flagship) | Beta | Phase 0 rename; then extend `server/` with `pipeline/` + `vision/` modules | Freemium SaaS: Free / $15 Pro / $35 Team / Enterprise BYOK |
| **BrightForge** (merged trunk) | Multi-agent AI studio + Forge3D + Idea Intelligence Phase 12 | Beta | Phase 0 merge + hygiene; extract `@grizzwald/llm-client` | Desktop Pro ($29/mo or $249/yr) + optional Forge Marketplace Phase 2 |
| **grizz-optimizer** | Security/safety exemplar, Windows 11 optimizer (domestic LLM client) | Alpha-Beta | Close `execution.handler.ts` + `install-manager.ts` stubs; sign installer | Free + $19/yr Pro + $49/yr Pro+Security |
| **Bob-AICompanion** | Serverless cron + job intelligence + future MCP unifier | Beta | Migrate to `@grizzwald/llm-client`; add MCP client + server | GH Actions free + $9/mo Hosted + $19/seat Teams |
| **portfolio-website** | Conversion surface for recruiters + freelance lead-gen (not a SaaS) | Beta | Split agent sidecar into Bob; remove PDFs from main; add Hire Me page | Freelance + job offers ($30k-$80k year 1) |
| **DeveloperProductivityTracker** (Capstone) | UE5 C++ editor plugin — only C++ codebase, AAA practices showcase | Beta | Add UE5 Automation Framework tests; populate `.uplugin` metadata | Epic Marketplace $14.99 one-time + $9.99 Pro upgrade |
| **SeniorDevBuddy / agentforge_autonomous** | Markdown-as-doctrine R&D lab | Alpha | Replace skeleton agents with BrightForge's; fix CI; harvest doctrine to ClaudeSkills | OSS (AGPL) — $0-$500 year 1, doctrine > revenue |
| **Agent-Alexander** | (Duplicate of HoneyBadgerVault — same git remote) | n/a | Rename folder to `D:\HoneyBadgerVault`; delete codename | n/a |

---

## 5. Top 5 Portfolio-Wide Priority Features

Derived from feature gap tables in [04_strategy.md section 1] and Phase 0 blockers in [03_architecture_design.md section 5].

| # | Feature | Lives In Repo | Blocks | Unlocks |
|---|---|---|---|---|
| 1 | BrightForge canonical trunk merge (D: Phase 12 + Projects `src/model-intelligence/`) | BrightForge | All BrightForge feature work, `@grizzwald/llm-client` extraction | Portfolio presentation, shared package ecosystem |
| 2 | `@grizzwald/llm-client` extraction and migration (HBV + Bob + SeniorDevBuddy consume) | New repo `github.com/GrizzwaldHouse/llm-client` | HBV Phase 2.3, Bob Phase 2.8, SeniorDevBuddy Phase 3.8 | Drift elimination across 4 duplicate implementations |
| 3 | HBV `images` table + `server/pipeline/` + `server/vision/siglip2-classifier.ts` | HoneyBadgerVault | All downstream VLM workers, React ImageGrid, HF Space demo | Screenshot intelligence MVP, HBV flagship story |
| 4 | DeveloperProductivityTracker UE5 Automation Framework tests + marketplace metadata | DeveloperProductivityTracker | Epic Marketplace submission, Full Sail graduation launch moment | Only C++ codebase + AAA-practices recruiter narrative |
| 5 | HBV MCP server exposing `search_documents`, `search_images`, `classify_image`, `extract_text`, `generate_flashcards` | HoneyBadgerVault | Bob's MCP-unifier role (Phase 3.5) | Cross-repo conversational surface via Bob |

---

## 6. Execution Blockers

1. **BrightForge divergent branches** — neither `D:\BrightForge` (Phase 12, has `src/idea/`) nor `C:\Users\daley\Projects\BrightForge` (Phase 10, has `src/model-intelligence/`) is canonical alone. Blocks all BrightForge work [see 01_repo_audit.md sections 2, 6; 03_architecture_design.md reconciliation row 23].
2. **Workspace hygiene** — both BrightForge copies contain a nested UE5 plugin clone, Full Sail lab assignments, four mangled-path directories (`C:UsersdaleyProjectsBrightForge.githubworkflows` etc.), and a `nul` file that cannot be deleted via `rm nul` on Windows. Blocks portfolio presentation [see 01_repo_audit.md section 2 and Adjacent Portfolio Assets > D:\BrightForge; 03_architecture_design.md section 4.8].
3. **HBV name collision** — `D:\Agent-Alexander` origin points at `github.com/GrizzwaldHouse/HoneyBadgerVault.git`. Two identities for one codebase. Blocks CI path stability [see 01_repo_audit.md Critical Finding and section 1].
4. **LLM client quadruplication** — grizz-optimizer, BrightForge, Bob, and SeniorDevBuddy each reimplement the same free-first chain. Blocks drift elimination and Phase 2+ shared-package work [see 01_repo_audit.md Top Portfolio-Level Observations #3; 03_architecture_design.md reconciliation row 24].
5. **HBV is not greenfield** — attempting the user doc's Turborepo + Redis + BullMQ + Python FastAPI stack rebuilds existing working code (`extraction-manager.ts`, `download-queue.ts`, `hybrid-search.ts`, `event-bus.ts`). Variant B is the correct path [see 03_architecture_design.md section 2 Variant B, reconciliation rows 2, 12, 13, 14, 17, 22].
6. **Cerebras and Groq cannot serve VLMs** — both are LLM-only per HF Inference Providers matrix. Any VLM fallback chain that includes them is broken by construction [see 02_huggingface_reference.md section 6 provider capability matrix].
7. **MEMORY.md constraint** — `grizz-optimizer` stays domestic with its own 5-tier `llm-client.ts` due to domain-specific Ollama lifecycle management. It does NOT consume `@grizzwald/llm-client` [see MEMORY.md Related Projects > grizz-optimizer; 03_architecture_design.md reconciliation row 24].

---

## 7. Phase 0 Pre-Work

All four Phase 0 tasks sourced from [03_architecture_design.md section 5 Phase 0 BLOCKING Pre-work].

### P0.1 — BrightForge Canonical Trunk Merge

**Commands:**
```
cd D:\BrightForge
git status                                       # must be clean of intended work
git checkout -b feat/merge-phase10-model-intelligence
git remote add projects-copy C:\Users\daley\Projects\BrightForge
git fetch projects-copy
git log projects-copy/main --oneline | grep model-intelligence
git cherry-pick <model-intelligence-commit-SHAs>
npm test                                          # run all --test blocks
git push -u origin feat/merge-phase10-model-intelligence
```

**File Paths:**
- `D:\BrightForge\src\model-intelligence\` (new after cherry-pick)
- `D:\BrightForge\src\core\llm-client.js` (merge target if conflicts)
- `D:\BrightForge\src\idea\` (preserved from base)
- `C:\Users\daley\Projects\BrightForge\` (demoted or deleted after push)

**Acceptance Criteria:**
- Feature branch pushed to `origin` with both `src/idea/` (Phase 12) and `src/model-intelligence/` present.
- `npm test` passes on the merged branch.
- PR opened and self-merged into `origin/main`.
- `C:\Users\daley\Projects\BrightForge` deleted after verification.

### P0.2 — Workspace Hygiene Cleanup

**Commands:**
```
mkdir D:\_archive\brightforge-workspace-2026-04
move D:\BrightForge\BrightForge D:\_archive\brightforge-workspace-2026-04\nested-brightforge-copy
move D:\BrightForge\DeveloperProductivityTracker D:\_archive\brightforge-workspace-2026-04\nested-dpt
move "D:\BrightForge\MarcusDaley_Lab3" D:\_archive\brightforge-workspace-2026-04\
move "D:\BrightForge\MarcusDaleyComputer Graphics_lab4" D:\_archive\brightforge-workspace-2026-04\
move "D:\BrightForge\C:UsersdaleyProjectsBrightForge.githubworkflows" D:\_archive\brightforge-workspace-2026-04\
move "D:\BrightForge\C:UsersdaleyProjectsBrightForgedocs" D:\_archive\brightforge-workspace-2026-04\
move "D:\BrightForge\C:UsersdaleyProjectsBrightForgesrcapimiddleware" D:\_archive\brightforge-workspace-2026-04\
move "D:\BrightForge\C:UsersdaleyProjectsLLCApppython" D:\_archive\brightforge-workspace-2026-04\
move "D:\BrightForge\C:UsersdaleyProjectsLLCAppsrcforge3d" D:\_archive\brightforge-workspace-2026-04\
del \\.\D:\BrightForge\nul
```

**File Paths:**
- `D:\BrightForge\BrightForge\`
- `D:\BrightForge\DeveloperProductivityTracker\`
- `D:\BrightForge\MarcusDaley_Lab3\`
- `D:\BrightForge\MarcusDaleyComputer Graphics_lab4\`
- `D:\BrightForge\C:Usersdaley...` (5 mangled-path directories)
- `D:\BrightForge\nul` (Windows-reserved-name file)

**Acceptance Criteria:**
- `ls D:\BrightForge` shows only BrightForge project files (`src/`, `config/`, `package.json`, etc.).
- `del \\.\D:\BrightForge\nul` succeeds (normal `del nul` fails on Windows reserved name).
- `git status` shows only intentional changes; hygiene commit made.
- Repeat cleanup confirmed on `C:\Users\daley\Projects\BrightForge\` (or the path is deleted entirely after P0.1).

### P0.3 — HoneyBadgerVault Rename

**Commands:**
```
# Close all editors, terminals, IDEs pointed at D:\Agent-Alexander
move D:\Agent-Alexander D:\HoneyBadgerVault
cd D:\HoneyBadgerVault
git status
git remote -v                                    # must still show HoneyBadgerVault.git
```

**File Paths:**
- `D:\Agent-Alexander\` -> `D:\HoneyBadgerVault\` (full directory rename)
- `MEMORY.md`, `CLAUDE.md`, any CI workflows, VS Code workspace files (grep for `Agent-Alexander` and update)

**Acceptance Criteria:**
- `D:\Agent-Alexander` no longer exists.
- `D:\HoneyBadgerVault\.git` works; `git remote -v` confirms origin unchanged.
- Grep of entire portfolio for `Agent-Alexander` returns only historical/documentation mentions.
- IDE workspace files re-opened successfully at the new path.

### P0.4 — Extract `@grizzwald/llm-client`

**Commands:**
```
gh repo create GrizzwaldHouse/llm-client --public --clone
cd llm-client
# Seed from BrightForge/src/core/llm-client.js as the reference implementation
# API surface adopted from Bob-AICompanion/src/core/llm-client.js (cleanest small surface)
# Safety features adopted from grizz-optimizer/src/main/ai/llm-client.ts ($1/day cap, advisory-only)
npm init -y
# Implement UniversalLLMClient with chat/complete/embed/getDailyUsage/isProviderAvailable
# Provider matrix: Ollama, Groq, Cerebras, Together, Mistral, Gemini, Claude, OpenAI, OpenRouter, HF Inference
# Zod-validated YAML config schema
npm publish --access public    # or GitHub Packages
```

**Migration file paths:**
- **HBV:** `D:\HoneyBadgerVault\server\ai\ai-orchestrator.ts` — refactor to consume `@grizzwald/llm-client`. `checkAIConsent()` remains the outer gate; client sits inside.
- **Bob:** `C:\Users\daley\Projects\Bob-AICompanion\src\core\llm-client.js` — delete, import from package. YAML config in `config/llm-providers.yaml` is already compatible.
- **SeniorDevBuddy:** `C:\Users\daley\Projects\SeniorDevBuddy\agentforge_autonomous\src\backend\services\ModelService.ts` — delete skeleton, import from package. Wire into `AgentOrchestrator.ts`.
- **grizz-optimizer:** `C:\Users\daley\grizz-optimizer\src\main\ai\llm-client.ts` — **DO NOT MIGRATE** per MEMORY.md. Keeps domain-specific Ollama lifecycle management.

**Acceptance Criteria:**
- `@grizzwald/llm-client` published to GitHub Packages or npm.
- HBV `ai-orchestrator.ts` imports and calls `new UniversalLLMClient()` inside `checkAIConsent()`.
- Bob's local `src/core/llm-client.js` deleted; regression test `tests/package-migration.test.js` fails if file reappears.
- SeniorDevBuddy `ModelService.ts` delegated or deleted.
- grizz-optimizer untouched; MEMORY.md note preserved.
- All four consumer repos (HBV, Bob, SeniorDevBuddy, and future SeniorDevBuddy agents) build and pass tests.

---

## 8. Phased Roadmap

Phase task detail and cross-repo dependencies sourced from [03_architecture_design.md section 5 Phases 0-4] and [04_strategy.md section 3.4 Full Sail Graduation Launch Moment].

| Phase | Weeks | Deliverable | Blocks | Unlocks |
|---|---|---|---|---|
| **Phase 0** | Week 0 | P0.1 merge, P0.2 hygiene, P0.3 rename, P0.4 llm-client extraction | Phase 1 | Shared-package ecosystem, canonical trunks |
| **Phase 1** | Weeks 1-3 | HBV `images` table + `server/pipeline/image-watcher.ts` + `server/vision/siglip2-classifier.ts` + React `ImageGrid.tsx`. BrightForge vitest wrapping `--test` blocks. | Phase 2 | Drop screenshot -> classified -> searchable in under 5s |
| **Phase 2** | Weeks 4-6 | HBV `got-ocr-worker.ts` + `qwen-vlm-worker.ts` via `@huggingface/inference`. SSE endpoint `/api/pipeline/events`. Encryption-at-rest verification test. Embedding upgrade audit (gte-modernbert-base). Bob migration regression tests. | Phase 3 | Full 5-stage pipeline with VLM descriptions |
| **Phase 3** | Weeks 7-10 | HBV MCP server. Tauri CI packaging. BrightForge MCP server + Forge3D smoke test. Bob MCP client + server. grizz-optimizer stub closures + signed installer. SeniorDevBuddy agent replacement + real CI. portfolio-website sidecar migration. DeveloperProductivityTracker HTTP bridge + UE5 Automation tests. HBV HuggingFace Space demo live. | Phase 4 | Cross-repo MCP conversational surface; graduation-ready portfolio |
| **Phase 4** | Weeks 11-16 | HBV usage metering + freemium enforcement + BYOK. Bob Fly.io deploy + quest system. DeveloperProductivityTracker opt-in AI layer. portfolio-website live project cards. SeniorDevBuddy markdown-orchestrator package. grizz-optimizer red team CI gate. HBV waitlist / pre-order landing page. | — | First paying users; monetization ring-fenced; Full Sail graduation launch moment Feb 6 2026 |

---

## 9. Three Educational Game Ideas

All three ideas condensed from [04_strategy.md section 4 Educational Game / Tool Concepts]. Forge Quest flagged as strategist's favorite.

### Idea A — Forge Quest (Marcus's Highest-Leverage Concept)

- **Concept:** UE5 narrative questline (~15 minutes) where the player is a new apprentice at "the Forge" and must pick correct AI tools from a holographic inventory (SigLIP 2 for classification, GOT-OCR for extraction, Qwen2.5-VL for description, gte-modernbert for search) to help NPCs solve problems. Final quest builds a real pipeline that calls HBV's backend and succeeds/fails on real inference results.
- **Learner:** Non-technical learners + recruiters. Also the single strongest crossover portfolio artifact (UE5 C++ + AI pipeline + narrative design + cross-repo integration).
- **Mechanics:** (1) NPC dialogue -> pick right tool from inventory UI. (2) Drag 3D stage icons onto a quest board to assemble a pipeline. (3) Final rescue mission calls HBV `/api/pipeline/*` endpoints, real success/failure.
- **Stack:** UE5 C++ (game layer) + UE5 Blueprints (dialogue/quest state) + UE5 HTTP subsystem -> HBV backend + HBV does the real inference.
- **Repo:** New `D:\Forge-Quest\`, cross-linked from BrightForge and HBV.
- **MVP (weekend):** 1 of 5 quests — "Classify the photo". Single map, 2 NPCs, inventory UI with 3 tools, one HBV API call returning SigLIP 2 result, branching dialogue. UE5 ThirdPerson template, no custom art. ~700 lines C++ + Blueprints.
- **Hook:** The only deliverable that exercises C++ + UE5 + AI + narrative + cross-repo in one artifact. Highest viral-content probability in the portfolio; lands on both game-dev and AI-dev Twitter.

### Idea B — Vector Space Explorer

- **Concept:** UE5 walkable 3D t-SNE/PCA visualization. Load gte-modernbert-base embeddings from HBV `embedding-service.ts`, reduce to 3D, render each document as a floating glowing orb. Player walks up to orbs, sees previews, casts a "query beam" that highlights semantically-similar neighbors.
- **Learner:** CS students learning vector spaces and embeddings. Walkable 3D is the single most memorable intuition for "what does an embedding mean."
- **Mechanics:** (1) First-person walk through document orb clusters. (2) Type query -> embed with gte-modernbert-base -> highlight N closest orbs. (3) Toggle PCA (clean axes) vs t-SNE (tighter clusters) to see dim-reduction differences.
- **Stack:** UE5 C++ + Python export helper (`umap-learn` or `openTSNE`) + HBV `embedding-service.ts` as the source of truth + pre-computed CSV of (id, x, y, z, title).
- **Repo:** DeveloperProductivityTracker as a companion UE5 project, or standalone in `D:\HBV-Explorer\`.
- **MVP (weekend):** Load pre-computed CSV, spawn sphere actors, first-person camera, text box types query and highlights nearest N via pre-computed k-NN table. No live embedding on click. ~500 lines C++.
- **Hook:** Combines Capstone's UE5 chops with AI visualization territory; positions Marcus for AI+game-engine hybrid roles that almost nobody else can fill.

### Idea C — Prompt Garden

- **Concept:** Headless daemon watches a `prompts/` folder. Every prompt is scored on five axes (specificity, constraint density, example count, output-format explicitness, anti-hallucination guardrails) via SigLIP 2 + Qwen2.5-VL. Each score maps to plant growth stages (seed -> sprout -> sapling -> tree -> flowering tree -> fruit-bearing tree). Web UI visualizes the garden; plants wilt over time if prompts are not revisited.
- **Learner:** Junior developers and students leveling up from "write boilerplate for me" to production-grade prompt engineering.
- **Mechanics:** (1) Write prompt -> drop in folder -> watch plant grow based on score. (2) Iterate on low scorers; plants transition stages for immediate feedback. (3) "Harvest" high-scoring prompts into a personal exportable library.
- **Stack:** Node.js Chokidar + `@huggingface/transformers` (SigLIP 2 local) + `@huggingface/inference` (Qwen2.5-VL routed `:cheapest`) + React + D3 + sqlite.
- **Repo:** `C:\ClaudeSkills\` — natural home per CLAUDE.md (prompt-template management system).
- **MVP (weekend):** File watcher + 5-axis scorer (each axis = SigLIP 2 zero-shot call) + static HTML visualization with 5 plant stages as SVG. JSON file, no DB. ~400 lines.
- **Hook:** Portfolio content — "I built a prompt garden that grows plants based on prompt quality" is inherently viral-blog material. Not a revenue surface; an attention asset.

---

## 10. Source Reports

- [`00_user_strategy_doc.md`](./00_user_strategy_doc.md) — Marcus's authoritative input
- [`01_repo_audit.md`](./01_repo_audit.md) — 8-codebase ground-truth audit
- [`02_huggingface_reference.md`](./02_huggingface_reference.md) — 2026 model reference
- [`03_architecture_design.md`](./03_architecture_design.md) — 24-row reconciliation, Variant B, Phase 0 pre-work
- [`04_strategy.md`](./04_strategy.md) — Portfolio re-ranking, freelance > SaaS, Forge Quest

---

*End of AI_AUDIT_2026 — compiled 2026-04-08.*
