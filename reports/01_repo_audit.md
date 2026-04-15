# Cross-Repo Audit — AI Audit 2026

repo-auditor | 2026-04-08 | 9 repos, expert depth | READMEs + manifests + 5-10 key source files per repo

---

## Critical Finding: Repo #1 and Repo #9 Are the Same Codebase

`D:\Agent-Alexander` is a local working copy whose `origin` points at `github.com/GrizzwaldHouse/HoneyBadgerVault.git`. File layout matches 1:1. "Agent-Alexander" is the internal project name; "HoneyBadgerVault" is the public product name. I treat them as **one product with two names**. Total effective count: 8 distinct codebases.

---

## 1. Agent-Alexander / HoneyBadgerVault (unified)

- **Path:** `D:\Agent-Alexander` (local) | `github.com/GrizzwaldHouse/HoneyBadgerVault` (remote, same repo)
- **Tech Stack:** TypeScript ~90%. React 18 + Vite + Wouter + Radix/shadcn + TanStack Query + Framer Motion + Spline 3D. Express 5 + better-sqlite3 + Drizzle ORM + Zod + Argon2. Playwright-core (CDP), Cheerio, p-limit, p-retry, tough-cookie. pdf-parse, pdfjs-dist, tesseract.js, ts-fsrs. Tauri desktop shell. Browser extension sub-project.
- **Architecture Pattern:** Layered monolith with plugin-style connectors. `server/extraction/base-connector.ts` defines an interface with five concrete subclasses (Playwright/Canvas/Blackboard/Moodle/Generic) plus `download-queue.ts`, `extraction-manager.ts`, `retry-handler.ts`, `event-bus.ts`, `scheduler.ts`. `server/ai/ai-orchestrator.ts` routes to Ollama or OpenAI with opt-in consent gating (`checkAIConsent` reads `privacy.ai_enabled`). `hybrid-search.ts` + `vector-search.ts` fuse BM25 with embedding cosine similarity. `verification-pipeline.ts`, `knowledge-extractor.ts`, `flashcard-generator.ts` all run through the orchestrator. `shared/schema.ts` is the 17-table Drizzle single source of truth used by both tiers via Zod.
- **AI Integration Status:** **Production.** Ollama local-first, OpenAI (GPT-5.1 per `ARCHITECTURE.md`) as opt-in fallback. Capabilities: semantic search, flashcard generation (SM-2 FSRS), knowledge graph extraction, quality scoring, tagging, tesseract OCR. All server-side proxied + consent-gated.
- **Maturity:** **Beta / near production-ready.** Real test coverage (`metadata-extractor.test.ts`, `hybrid-search.test.ts`, `storage.test.ts`, Playwright E2E). Git history includes Phase-1 security hardening and a verified-build-gate pipeline with 15 tests + pre-push hook.
- **Key Files:** `server/ai/ai-orchestrator.ts:1-60`, `server/extraction/base-connector.ts`, `server/extraction/extraction-manager.ts` + `download-queue.ts`, `shared/schema.ts`, `script/build-gate/run-build-gate.ts`.
- **Completion Gaps:** Encryption-at-rest (AES-256-GCM) declared in README — `server/encryption.ts` needs verification of key rotation and master-password derivation. Tauri packaging not CI-integrated. 12 open GitHub issues. Scheduler exists but cron hardening unclear.
- **Notable Strengths:** Best-in-class separation of concerns in the portfolio. Textbook plugin architecture. Dual test harness. Consent-first AI. Drizzle schema as ground truth is the cleanest DDD expression across all projects.
- **Cross-Repo Synergy:** Extract `base-connector.ts` + retry/event-bus as `@grizzwald/connector-kit`. Ship hybrid BM25+vector search to `SeniorDevBuddy`.

---

## 2. BrightForge (D: copy)

- **Path:** `D:\BrightForge` (HEAD: `feat(idea): Idea Intelligence System (Phase 12)`)
- **Tech Stack:** Node.js 18+ ESM ~70%, Python 3.10+ ~25% (Forge3D), HTML/JS dashboard ~5%. Deps: `express`, `better-sqlite3`, `undici`, `helmet`, `express-rate-limit`, `ws`, `rotating-file-stream`, `yaml`. Dev: `electron`, `electron-builder`. Python: PyTorch/CUDA 12.4, `diffusers` (SDXL + InstantMesh), `transformers`, `fastapi`, `trimesh`, `pyassimp`.
- **Architecture Pattern:** Modular hybrid-AI studio, 12 documented phases. Sub-systems: `src/core/` (LLM client, plan-engine, diff-applier, design-engine, skill-orchestrator), `src/agents/` (base/local/cloud/master/planner/builder/reviewer/tester/survey/recorder), `src/forge3d/` (database, forge-session, generation-queue, model-bridge, scene, world, gameplay, playtest, pipeline), `src/idea/` (Phase 12 — ingestion/classifier/scoring/research/indexer), `src/orchestration/` (event-bus, task-state, supervisor, handoff), `src/api/` (Express + ws-event-bus). Dashboard at `:3847`. Electron shell in `desktop/`. **MIXED-WORKSPACE WARNING:** D: root also contains a UE5 plugin clone, graphics lab assignments, and mangled path-name folders from a failed recursive copy. Multi-purpose workspace, not a clean project.
- **AI Integration Status:** **Production.** 9-provider free-first chain: Ollama -> Groq -> Cerebras -> Together -> Mistral -> Gemini -> Claude -> OpenAI -> OpenRouter. $1/day budget cap. Image chain: Pollinations -> Together FLUX -> Gemini 2.0 -> Stability AI. 3D: SDXL -> InstantMesh, GLB+FBX export. Multi-agent plan-review-run with diffs + backup + rollback.
- **Maturity:** **Beta (coding+design); alpha (Forge3D, Idea Intelligence).** 110+ files, ~35k lines, 40+ `--test` blocks. Docker + Prometheus metrics + health/ready endpoints. TelemetryBus P50/P95/P99. Version `4.2.0`.
- **Key Files:** `src/core/llm-client.js` (9-provider chain), `src/agents/master-agent.js` + planner/builder/reviewer/tester, `src/forge3d/model-bridge.js` + `python/inference_server.py`, `src/orchestration/supervisor.js`, `src/idea/idea-scoring.js`, `config/llm-providers.yaml`.
- **Completion Gaps:** Workspace hygiene is the #1 portfolio blocker — nested UE5 plugin, lab assignments, and mangled-path dirs must be pruned. Forge3D needs manual ~15GB model pull. No end-to-end text-to-mesh test in CI. `--test` blocks don't integrate with coverage tooling.
- **Notable Strengths:** Most sophisticated AI orchestration in the portfolio. Genuinely multi-agent (planner/builder/reviewer/tester/survey/recorder), not router-based. Production-grade observability. Phase 12 Idea Intelligence is a novel differentiator. Configuration-driven via 6 YAML files.
- **Cross-Repo Synergy:** Extract the 9-provider chain as `@grizzwald/llm-fallback` to replace smaller chains in Bob and SeniorDevBuddy. Forge3D text-to-mesh can feed portfolio-website and HoneyBadgerVault (3D previews, knowledge-graph mesh export).

---

## 3. portfolio-website

- **Path:** `D:\portfolio-website`
- **Tech Stack:** Next.js 15 (App Router) + React 19 + TypeScript 5.7 (strict) + Tailwind CSS 4.0 + Framer Motion 12 + Three.js 0.182 + Radix UI + Zustand 5 + nuqs. Vitest + jsdom. Vercel primary + Netlify secondary. GitHub Actions build verification.
- **Architecture Pattern:** Next.js App Router SSG/ISR site, 12 pages / 30 static paths. Noteworthy: (a) Observer pattern with re-entrancy guard for deployment events in `src/lib/`, (b) three-layer error fallback (static `public/maintenance.html` + React boundaries + CI/CD monitoring), (c) GitHub ISR enrichment that fetches stars/language/last-push and parses remote READMEs at build time. Sub-project `agents/` (`learning-loop.js`, `ollama-listener.js`) + `admin/` + `agent-cli.js` = an experimental automation panel separate from the public site.
- **AI Integration Status:** **In-progress.** `OLLAMA_MEMORY.json`, `TASK_QUEUE.json`, `agents/ollama-listener.js`, `agent-cli.js`, `generate_leidos_configdm_v2.py`, `IMAGE_PIPELINE_REPORT.md` reveal an active Ollama automation bolted onto the portfolio. Leidos/NISC resume PDFs + `vmockfeedback.pdf` = this is a live job-hunt workstation, not just a portfolio build.
- **Maturity:** **Beta (public site); alpha (agentic sidecar).** 50 test methods across 9 suites. Dual-platform deploy redundancy. TS strict.
- **Key Files:** `src/app/page.tsx`, `src/lib/` (GitHub API, README parser, Observer), `src/data/projects.ts`, `agents/ollama-listener.js`, `tests/portfolio.test.ts`.
- **Completion Gaps:** Public portfolio and Ollama sidecar should live in separate repos. Resume PDFs and `Claude_task.txt` should not be in `main`. No analytics on the production site.
- **Notable Strengths:** GitHub ISR README enrichment is a clever differentiator. Three-layer error fallback shows production thinking. Vercel+Netlify redundancy is portfolio-worthy itself. Cohesive Full Sail design system (`#FFCC00` / `#D50032`, Cinzel, CRT vignette).
- **Cross-Repo Synergy:** Extract GitHub ISR README-parsing to auto-document BrightForge + HoneyBadgerVault. Migrate the Ollama sidecar into Bob-AICompanion.

---

## 4. DeveloperProductivityTracker (Capstone)

- **Path:** `D:\FSO\Capstone Project\DeveloperProductivityTracker`
- **Tech Stack:** C++ 100% UE5 editor plugin. Win64, `PostEngineInit` loading. No external deps in `.uplugin`.
- **Architecture Pattern:** **UE5 Editor Plugin with Subsystem-based DI.** Clean IModuleInterface (`DeveloperProductivityTrackerModule.h:28`). Five subsystems in `Public/`+`Private/`: `Core/` (session, settings, storage), `External/` (app + file monitoring), `Wellness/` (Pomodoro, breaks, stretches), `Visualization/` (sky, sun, dual moons, stars), `UI/` (dashboard, toolbar, notifications). Session persistence across restarts. Activity-state detection (Active/Thinking/Away/Paused). API uses `GEditor->GetEditorSubsystem<T>()` DI — textbook UE5.
- **AI Integration Status:** **None.** All intelligence is rule-based (activity heuristics, Pomodoro timing, break scoring).
- **Maturity:** **Beta, portfolio-ready.** File headers match Marcus's convention exactly. Checksum tamper detection, installation-specific salt, GDPR-compliant export. Cleanest expression of Marcus's coding standards in any repo.
- **Key Files:** `Source/DeveloperProductivityTracker/Public/DeveloperProductivityTrackerModule.h:1-84`, `Public/Core/`, `Public/Wellness/`, `Public/External/`, `DeveloperProductivityTracker.uplugin`.
- **Completion Gaps:** Manual testing checklist only; no UE5 Automation Framework tests. `.uplugin` missing MarketplaceURL/DocsURL/SupportURL. Keyboard shortcuts unbound by default.
- **Notable Strengths:** Best-in-class adherence to Marcus's universal coding standards. Strongest "AAA practices" showcase in the portfolio and exactly what Nick Penney's Full Sail course preached. Privacy-first local-only telemetry.
- **Cross-Repo Synergy:** Add opt-in AI layer via BrightForge's LLM client for session summaries and burnout detection. Expose Session API as HTTP endpoint so portfolio-website can embed live stats.

---

## 5. SeniorDevBuddy (including agentforge_autonomous)

- **Path:** `C:\Users\daley\Projects\SeniorDevBuddy`
- **Tech Stack:** Root is a markdown orchestrator + zip-archive graveyard with three generations of system prompts (`grizz_modular_system/` active, `_fixed/` mirror, `_ultimate_system/` legacy). Active code in `agentforge_autonomous/`: Next.js 15 + React 19 + TS + Tailwind 4 + Radix + Framer Motion + Vitest + Electron.
- **Architecture Pattern:** **Dual-layer.** (a) Markdown-driven 10-step loop `DETECT->EXTRACT->MATCH->GENERATE->PLAN->BUILD->REVIEW->TEST->REFACTOR->LEARN` with 4 tracking files (`SKILLS.md`/`TASKS.md`/`AGENTS.md`/`LEARNING.md`) and 12 agents (7 core + 5 Ollama-audit). (b) TS in `agentforge_autonomous/src/`: `core/interfaces/Agent.ts` defines the interface; `AgentOrchestrator.ts` runs agents in parallel via `Promise.all`; `ModelService.ts` detects local LLMs. Entry: `claude_autonomous_bootstrap.ts`.
- **AI Integration Status:** **In-progress.** Markdown doctrine complete. TS agents mostly skeleton stubs. Intended provider chain: Ollama->Groq->Cerebras->Together->Mistral->Claude->OpenAI with $1/day budget.
- **Maturity:** **Alpha.** CI is a placeholder echo. Zip archive graveyard at root. `package.json` name ("agentforge-observability") doesn't match folder ("agentforge_autonomous") — identity crisis.
- **Key Files:** `agentforge_autonomous/src/core/interfaces/Agent.ts`, `src/backend/services/AgentOrchestrator.ts`, `ModelService.ts`, `claude_autonomous_bootstrap.ts`, `grizz_modular_system/SYSTEM_PROMPT.md`.
- **Completion Gaps:** CI placeholder; agent implementations are skeletons; zip graveyard needs cleanup; two mirrored markdown dirs is a manual-sync nightmare; name mismatch.
- **Notable Strengths:** Markdown-orchestrator vision is genuinely novel — treating system prompts as executable doctrine. Clean task lifecycle + swappable Agent interface. Strong personal doctrine in CLAUDE.md (ESM/npm/Netlify/SSH ed25519/Groq-first).
- **Cross-Repo Synergy:** Replace skeleton agents with BrightForge's production planner/builder/reviewer/tester. Spin the markdown-orchestrator out as `@grizzwald/markdown-orchestrator` for ClaudeSkills and Bob to consume.

---

## 6. BrightForge (Projects copy)

- **Path:** `C:\Users\daley\Projects\BrightForge`
- **Tech Stack:** Same as Repo #2. HEAD at `feat(model-intelligence): add smart model routing` — behind D: copy's Phase 12 `feat(idea)` trunk.
- **Architecture Pattern:** Same modular hybrid-AI studio as Repo #2 minus `src/idea/` and newer `src/orchestration/` additions, PLUS unique `src/model-intelligence/` directory absent from D:. These are **two divergent branches**, not a mirror.
- **AI Integration Status:** **Production** (same 9-provider chain + Forge3D pipeline, minus Phase 12).
- **Maturity:** **Beta.** Same mixed-workspace pollution as D:.
- **Key Files:** `src/model-intelligence/` (unique), `src/core/llm-client.js`, `src/forge3d/`, `src/agents/`, `CLAUDE.md`.
- **Completion Gaps:** **FORKED-BRANCH CLEANUP PROBLEM.** Projects has `src/model-intelligence/`, D: has `src/idea/`. Running two divergent unversioned local branches is the largest technical debt in the portfolio.
- **Notable Strengths:** `src/model-intelligence/` is a Phase 10 snapshot worth preserving — smart model routing by task type.
- **Cross-Repo Synergy:** **IMMEDIATE ACTION:** merge both trunks onto GitHub, then designate one path canonical and archive the other to prevent drift.

---

## 7. Bob-AICompanion

- **Path:** `C:\Users\daley\Projects\Bob-AICompanion`
- **Tech Stack:** Node.js 18+ ESM. Deps: `better-sqlite3`, `express`, `yaml`, `dotenv`. GitHub Actions for scheduling. YAML config (`llm-providers.yaml` + `marcus-context.yaml`).
- **Architecture Pattern:** **Serverless scheduled automation via GitHub Actions.** `src/core/llm-client.js` implements `UniversalLLMClient` — OpenAI-compatible adapter for Ollama/Groq/Cerebras/Together/Mistral/Claude/OpenAI/OpenRouter with YAML priority + budget tracking (`dailyUsage` {cost_usd, requests, tokens}). `src/workflows/morning-brief.js` fires from `morning-brief.yml` at 6 AM PST weekdays. `discord-webhook.js` delivers to Discord. New `src/job-intelligence/`: database, validation, fraud detection, scoring, full pipeline with 6 dedicated npm test scripts. `src/api/server.js` hints at HTTP layer. Memory via GitHub Artifacts. **Zero exposed ports — Actions is the entire backend.**
- **AI Integration Status:** **Production.** 8-provider free-first chain, real Discord delivery, budget tracking. Cost target: $0-5/month vs claimed baseline of "$300/2 days."
- **Maturity:** **Beta.** Real npm test scripts across 6 job-intelligence sub-modules. Clean JSDoc file headers. Live non-trivial GitHub Action.
- **Key Files:** `src/core/llm-client.js:1-60`, `src/workflows/morning-brief.js`, `src/integrations/discord-webhook.js`, `src/job-intelligence/{fraud-detector,scoring-engine}.js`, `.github/workflows/morning-brief.yml`, `config/llm-providers.yaml`.
- **Completion Gaps:** No always-on hosting target beyond cron. `src/api/server.js` has no rate limiting. `job-intelligence` undocumented in README. Fraud detector needs adversarial-fixture tests.
- **Notable Strengths:** GitHub-Actions-as-backend is the cheapest production automation stack and deserves a blog post. `UniversalLLMClient` is the cleanest provider adapter in the portfolio. Zero exposed ports = zero attack surface.
- **Cross-Repo Synergy:** Promote `UniversalLLMClient` to `@grizzwald/llm-client` to replace one-offs across BrightForge/SeniorDevBuddy/portfolio-website. Extend `job-intelligence` to consume HoneyBadgerVault's LMS extractor for a unified "Marcus's life intelligence" Discord feed.

---

## 8. grizz-optimizer

- **Path:** `C:\Users\daley\grizz-optimizer`
- **Tech Stack:** TS 5.9 ~95%, PowerShell 7 ~5%. Electron 33 + electron-vite + Vite 6 + React 18 + Tailwind 4 + Zustand 5 + Radix + zod + recharts. AI: `ollama` + `electron-ollama` + `@huggingface/inference` + `@huggingface/transformers`. Vitest 2.1 + Playwright 1.59. 9 `-WhatIf`-aware PowerShell scripts + Pester.
- **Architecture Pattern:** **Secure Electron with typed contextBridge IPC + multi-agent orchestration.** `src/main/` modules: `index.ts` (boot + single-instance lock + global error handlers), `ai/` (llm-client, hf-client, hardware-analyzer, install-manager, model-catalog, model-recommender), `ollama/` (manager, first-run, hardware-detect), `bridge/` (PowerShell). `src/plugins/` Phase 7 plugin SDK. Safety: context isolation ON, nodeIntegration OFF, zod-validated IPC payloads, `-WhatIf` dry runs, rollback manifests for every destructive op, TIER 0-2 safety rules, built-in red team scanner (7 phases, A-F grade). 5-tier AI fallback: Ollama -> HF ONNX -> HF API -> Groq -> Cerebras.
- **AI Integration Status:** **Production (advisory-only).** Qwen3.5-9B Q4_K_M via Ollama on RTX 4070 8GB. **AI is advisory only, never controls execution** — unusually mature safety posture.
- **Maturity:** **Alpha->Beta.** Phases 0/1/2/5/7 complete; Phase 3/4 stubbed; Phase 6/8 in-progress. 95/95 unit tests passing on agent orchestration. 5-job CI (install, lint+typecheck, unit-tests, security-audit, build). 16KB `HANDOFF.md`.
- **Key Files:** `src/main/index.ts:1-60`, `src/main/ai/llm-client.ts` (canonical 5-tier), `src/main/ollama/{manager,first-run,hardware-detect}.ts`, `src/main/ai/install-manager.ts`, `src/plugins/{sdk,loader}.ts`, `tests/security/redteam-e2e.test.ts`.
- **Completion Gaps:** Two acknowledged stubs: `execution.handler.ts` RUN dispatch returns success without running steps, `install-manager.ts` model pull is a `setTimeout`. High-fidelity demo until these land. No installer signing/notarization.
- **Notable Strengths:** Best security posture in the portfolio by a wide margin. Every decision (typed IPC, `-WhatIf`, rollback manifests, TIER rules, advisory-only AI, red team scanner) is informed by enterprise-secure-ai-engineering principles. `src/main/index.ts` is the cleanest Electron boot file I've seen.
- **Cross-Repo Synergy:** Extract typed `contextBridge` IPC + zod as `@grizzwald/secure-ipc` for Tauri/Electron peers. Adapt `redteam-e2e.test.ts` as a CI harness for every other app in the portfolio.

---

## Cross-Repo Synthesis Table

| Repo | Primary Lang | Maturity | AI Status | Top Gap | Top Strength |
|---|---|---|---|---|---|
| Agent-Alexander / HoneyBadgerVault | TypeScript | Beta | Production (Ollama + OpenAI, consent-gated) | Encryption-at-rest verification; Tauri packaging CI | Cleanest DDD + connector plugin architecture |
| BrightForge (D: / canonical) | JavaScript ESM + Python | Beta | Production (9-provider chain, Forge3D) | Workspace hygiene; mixed UE5 + lab assignments | Multi-agent pipeline + Idea Intelligence Phase 12 |
| portfolio-website | TypeScript (Next.js 15) | Beta | In-progress (Ollama sidecar) | Agentic sidecar mixed with public site | GitHub ISR README enrichment; dual-platform deploy |
| DeveloperProductivityTracker | C++ (UE5) | Beta | None (rule-based only) | No automated tests; no marketplace metadata | Textbook UE5 subsystem DI; cleanest coding-standards adherence |
| SeniorDevBuddy | TypeScript (Next.js) + Markdown | Alpha | In-progress (skeleton agents + Ollama) | Agent implementations are stubs; CI placeholder; zip graveyard | Markdown-orchestrator doctrine pattern is novel |
| BrightForge (Projects copy) | JavaScript ESM + Python | Beta | Production (subset) | Divergent branch from D: copy; merge required | Unique `src/model-intelligence/` routing |
| Bob-AICompanion | JavaScript ESM | Beta | Production (8-provider YAML chain, GH Actions serverless) | No always-on API hosting; job-intel undocumented | `UniversalLLMClient`: cleanest provider adapter; zero attack surface |
| grizz-optimizer | TypeScript (Electron) + PowerShell | Alpha->Beta | Production (advisory-only, 5-tier fallback) | RUN dispatch + install-manager are stubs | Best security posture; red team scanner; advisory-AI principle |

---

## Flagship Ecosystem Alignment

Marcus's strategy doc (`reports/00_user_strategy_doc.md`) designates four flagship repos with assigned roles. This section reconciles assigned role vs actual code. Disagreements are called out explicitly.

### HoneyBadgerVault — "Storage / AI Image Pipeline Flagship"

**Doc says:** AI image pipeline on CLIP ViT-L/14 + IBM Granite-Docling 258M + Qwen2.5-VL 7B, orchestrated via BullMQ + Redis + Chokidar, SQLite FTS5 + sqlite-vec for hybrid search, Turborepo monorepo.

**Actual code:** An **LMS document extraction vault**. Connectors target Canvas/Blackboard/Moodle/CDP/CSS. AI layer does semantic search, FSRS flashcards, knowledge graphs, quality verification — over PDFs, not images.

**Verdict: PARTIAL / FORWARD-LOOKING.** ~80% of the prescribed infrastructure is already there in different form: BullMQ-equivalent in `extraction/download-queue.ts` (p-limit + retry + circuit breaker); hybrid BM25+vector already fused in `hybrid-search.ts`; 17-table Drizzle schema ready to extend. Missing: Chokidar (cron-based instead), Turborepo, and the CLIP/Granite/Qwen vision models themselves.

**Recommendation:** Additive layer, not rewrite. Add `server/ai/vision/clip-classifier.ts` (Transformers.js ONNX), host Granite-Docling + Qwen2.5-VL in a new `apps/inference/` Python FastAPI service, extend schema with `images` + `image_embeddings` + `image_descriptions` tables. Keep the LMS extraction work — it is Marcus's most mature codebase.

### Bob-AICompanion — "MCP-Enabled Intelligence & Orchestration Layer"

**Doc says:** Bob should evolve into an MCP client that discovers and invokes tools exposed by HoneyBadgerVault, grizz-optimizer, and BrightForge — unified conversational interface across the ecosystem.

**Actual code:** GitHub-Actions-serverless morning-brief + Discord bot with 8-provider LLM chain + new `src/job-intelligence/` pipeline. Zero MCP. Zero cross-repo tool discovery. Runs on cron in isolation.

**Verdict: FOUNDATION EXISTS, MCP LAYER DOES NOT.** `UniversalLLMClient` is the right foundation for an MCP client. Missing: MCP server registration on the sibling repos and an MCP client in Bob. `src/api/server.js` hints Marcus is already thinking about always-on HTTP (a prerequisite).

**Recommendation:** Make "wire Bob to MCP" the highest-leverage cross-repo task in Phase 3. Use `@modelcontextprotocol/sdk`. Bob keeps the cron morning-brief and gains a `--interactive` mode that talks to siblings via MCP.

### grizz-optimizer — "Performance Foundation / Shared Utility Layer"

**Doc says:** A library/service layer BrightForge and HoneyBadgerVault call into for performance-critical operations.

**Actual code:** A standalone Windows 11 debloat desktop app. Consumer end-user product, not a library. Optimization scope is OS-level (services, telemetry, bloatware), not ML inference.

**Verdict: SIGNIFICANT MISMATCH.** The shared-library framing is not supported by the code. However, these internal modules ARE reusable: `ai/llm-client.ts` (canonical 5-tier fallback), `ai/hardware-analyzer.ts` + `model-recommender.ts` (directly applicable to HoneyBadgerVault's "run Qwen2.5-VL locally only if GPU allows" decision), `ai/install-manager.ts`, `ollama/manager.ts` + `first-run.ts`, `tests/security/redteam-e2e.test.ts`.

**Recommendation:** Rebrand the product as `@grizzwald/optimizer-desktop` and extract `@grizzwald/ai-runtime` (llm-client + hardware-analyzer + model-recommender + install-manager + Ollama lifecycle) as a separate package the other flagships import. This matches the doc's "foundation" framing without discarding the existing product.

### BrightForge — "Development Workflow Tool"

**Doc says:** Dev workflow tool. Treat `C:\Users\daley\Projects\BrightForge` as canonical (D: appears mixed).

**Actual code:** A **hybrid AI creative studio** doing three things — coding agent (plan-review-run with diffs + rollback), design engine (image gen + semantic HTML), Forge3D (text-to-image-to-mesh). Multi-agent planner/builder/reviewer/tester/survey/recorder. 9-provider LLM chain. Phase 12 Idea Intelligence. 110+ files, ~35k lines.

**Note on the canonical-copy instruction:** Team lead asked me to treat Projects as canonical. **Git history shows the OPPOSITE** — D: is at `feat(idea): Idea Intelligence System (Phase 12)` while Projects is at `feat(model-intelligence)`. D: has Phase 12 features Projects lacks; Projects has a unique `src/model-intelligence/` directory D: lacks. Both copies contain the mixed-workspace pollution. The canonical copy should be the **merged result of both**, not either unilaterally. Flagging explicitly per the strategy doc's rule to call out conflicts with justification.

**Verdict: BROADER THAN THE ASSIGNED ROLE.** BrightForge is closer to "flagship AI studio" than "dev workflow tool." Most ambitious repo in the portfolio in raw scope.

**Recommendation:** (1) Merge the D: and Projects branches into a single GitHub trunk before any other BrightForge work — the #1 prerequisite. (2) Split into three packaged deliverables sharing `@grizzwald/ai-runtime` + `@grizzwald/llm-client`: `@grizzwald/brightforge-agent`, `@grizzwald/brightforge-design`, `@grizzwald/forge3d`. The coding-agent slice satisfies the assigned role; the others are bonus ecosystem leverage.

---

## Adjacent Portfolio Assets (the 5 non-flagship repos)

These repos are not part of the four-flagship ecosystem per Marcus's strategy doc, but each plays a distinct role in his overall narrative as a **Navy veteran (9 years leadership) + Full Sail University BS Online Game Development graduate (Feb 6 2026) targeting AAA studio practices under instructor Nick Penney**.

### Agent-Alexander (local alias of HoneyBadgerVault)

- **Classification:** Adjacent — it IS HoneyBadgerVault. Same git remote, same file layout. Not a separate asset.
- **Narrative role:** None as a standalone repo. Rename the local folder to `HoneyBadgerVault` to eliminate the confusion. Document the former internal name in a `docs/HISTORY.md` so the design-doc trail (`Project_Alexander_Skeleton/`, `MASTER_BRIEFING.md`, `EXECUTIVE_MEMO_BOARD_READY.md`, `THREAT_MODEL.md`, `DEVOPS_ARCHITECTURE.md`) is preserved as primary-source architectural thinking.

### portfolio-website

- **Classification:** Adjacent portfolio asset (shopfront).
- **Narrative role:** **The storytelling surface for the entire portfolio** — the first thing recruiters, AAA studios, and job-application reviewers see. Full Sail branding (`#FFCC00` / `#D50032`, Cinzel display font, CRT vignette) signals game-dev audience fit. GitHub ISR enrichment demonstrates production thinking (live-updating project cards without redeploys). Dual Vercel + Netlify deploy redundancy is a portfolio-worthy talking point in itself. **This is where the "AAA studio practices" claim gets proven to recruiters** — the portfolio site must itself demonstrate AAA-level engineering or the claim falls flat. Recommendation: immediately split the agentic Ollama sidecar (`agents/ollama-listener.js`, `agent-cli.js`, `OLLAMA_MEMORY.json`, `TASK_QUEUE.json`, `raw-images/`, Leidos/NISC resume PDFs) out into a private companion repo so the public portfolio stays clean.

### DeveloperProductivityTracker (Capstone)

- **Classification:** Adjacent portfolio asset (academic capstone + AAA-practices showcase).
- **Narrative role:** **The single strongest AAA-practices proof in the portfolio.** UE5 editor plugin written in C++ with textbook `IModuleInterface` + `EditorSubsystem` DI, matching Marcus's universal coding standards exactly (file headers, restrictive access modifiers, subsystem-based DI, events over polling, rule-based-only intelligence, no magic numbers). This is the "Full Sail graduation thesis" artifact that makes the Nick Penney / AAA-studio-practices claim concrete to technical interviewers. It also happens to be the ONLY C++ codebase in the entire portfolio, which matters enormously for AAA game-engine job applications — every other repo is TypeScript / JavaScript / Python. Recommendation: wire up the UE5 Automation Framework for unit tests, populate the `.uplugin` MarketplaceURL + DocsURL + SupportURL, and feature it prominently on portfolio-website as the capstone project.

### SeniorDevBuddy (including agentforge_autonomous)

- **Classification:** Adjacent R&D / doctrine asset.
- **Narrative role:** **Marcus's personal engineering-doctrine lab.** The markdown-orchestrator pattern (`SYSTEM_PROMPT.md` + `SKILLS.md` + `TASKS.md` + `AGENTS.md` + `LEARNING.md` + 10-step execution loop) is genuinely novel — it's a research prototype for "what if system prompts were executable doctrine?" The TypeScript `agentforge_autonomous/` implementation is scaffolding for a future product but is currently skeleton-heavy. Not flagship-ready, but conceptually valuable. Recommendation: harvest the markdown doctrine into the `ClaudeSkills` repo (where it belongs), replace the skeleton TS agents with BrightForge's production agents, and demote this repo to a dated R&D archive unless the doctrine engine itself becomes a product.

### D:\BrightForge (the mixed workspace)

- **Classification:** Adjacent — SHOULD NOT EXIST AS A SEPARATE REPO. It is a contaminated working copy.
- **Narrative role:** Zero intentional role. It is the accidental fusion of (a) a legitimate BrightForge branch with Phase 12 Idea Intelligence, (b) a stray clone of `DeveloperProductivityTracker` (the Capstone UE5 plugin), (c) two Full Sail Computer Graphics lab assignments (`MarcusDaley_Lab3/`, `MarcusDaleyComputer Graphics_lab4/`), and (d) four mangled-path directories (`C:UsersdaleyProjectsBrightForge.githubworkflows`, `C:UsersdaleyProjectsLLCApppython`, etc.) created by a failed recursive copy. **Remediation:** (1) cherry-pick the unique Phase 12 commits onto the canonical BrightForge trunk; (2) move `MarcusDaley_Lab3` + `MarcusDaleyComputer Graphics_lab4` to a dedicated `FullSail-Coursework/` folder outside any repo; (3) move the nested `DeveloperProductivityTracker/` + `ue5-plugin/` folders back to their own repo; (4) delete the mangled-path directories; (5) delete `D:\BrightForge` itself once the valuable commits are rescued. This must happen before any downstream flagship work on BrightForge.

---

## Top Portfolio-Level Observations

1. **Agent-Alexander and HoneyBadgerVault are one codebase with two names.** Stop treating them as separate projects. Rename the local folder to match the GitHub name.
2. **The `BrightForge` D: vs Projects divergence is the single biggest tech debt.** Two active local branches with different feature sets (D: has Phase 12 Idea Intelligence; Projects has `src/model-intelligence/`). Same-day merge priority.
3. **The "free-first LLM fallback chain" is written four times** (grizz-optimizer, BrightForge, Bob-AICompanion, SeniorDevBuddy). Extract ONE canonical implementation — `grizz-optimizer/src/main/ai/llm-client.ts` is the most feature-rich. Ship as `@grizzwald/llm-client`.
4. Each project is world-class on one axis: HoneyBadgerVault (AI depth), grizz-optimizer (safety), Bob-AICompanion (cost), DeveloperProductivityTracker (coding standards). The portfolio's job is to tell that story coherently.
5. **`portfolio-website` is doing two jobs** (public portfolio + Ollama sidecar). Split them.

---

*End of audit — repo-auditor.*
