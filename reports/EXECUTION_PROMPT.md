# EXECUTION PROMPT — AI Audit 2026 Handoff

**Usage:** Paste this entire document into a fresh Claude Code session at `C:\ClaudeSkills\`. It contains everything needed to begin executing the 2026 portfolio consolidation.

---

## 1. Mission

You will execute Phase 0 pre-work and Phase 1 foundation sprint for Marcus Daley's 8-codebase portfolio, following the locked decisions in `C:\ClaudeSkills\reports\AI_AUDIT_2026.md`. Your job is to eliminate the four blocking tech-debt items and ship the Screenshot Intelligence MVP inside HoneyBadgerVault.

---

## 2. Context

Read `C:\ClaudeSkills\reports\AI_AUDIT_2026.md` first. It is the single source of truth. Everything else in `C:\ClaudeSkills\reports\` is reference material (numbered 00-04).

### Non-negotiable architectural decisions (do not re-debate)

- **Model stack is locked:** SigLIP 2 base (`google/siglip2-base-patch16-224`), GOT-OCR 2.0 (`stepfun-ai/GOT-OCR-2.0-hf`), Qwen2.5-VL-7B-Instruct (`Qwen/Qwen2.5-VL-7B-Instruct`), gte-modernbert-base (`Alibaba-NLP/gte-modernbert-base`), Qwen2.5-Coder-32B-Instruct (`Qwen/Qwen2.5-Coder-32B-Instruct`). Do not substitute CLIP, Granite-Docling, or any other model without user approval [see 02_huggingface_reference.md sections 1-5; 03_architecture_design.md Appendix B].
- **Variant B only:** Extend HoneyBadgerVault's existing TypeScript stack (Express 5 + better-sqlite3 + Drizzle + RRF hybrid-search). Do NOT introduce Turborepo, Redis, BullMQ, Python FastAPI, or any monorepo tooling. HBV is beta, not greenfield [see 03_architecture_design.md section 2 Variant B, reconciliation rows 12, 13, 17, 22].
- **VLM routing:** Qwen2.5-VL and GOT-OCR run via `@huggingface/inference` with `:cheapest` for batch and `:fastest` for interactive. **Cerebras and Groq are LLM-only — they cannot serve any VLM.** Valid VLM providers: HF Inference, Fireworks, Hyperbolic, Novita, Nscale, OVHcloud, Together, Featherless, Z.ai [see 02_huggingface_reference.md section 6 provider capability matrix].
- **`@grizzwald/llm-client` is the one canonical LLM package.** Consumers: HBV, Bob-AICompanion, SeniorDevBuddy. Exception: grizz-optimizer keeps its own local `src/main/ai/llm-client.ts` per `C:\Users\daley\.claude\projects\C--ClaudeSkills\memory\MEMORY.md` [see 03_architecture_design.md reconciliation row 24 and section 5 P0.4].
- **HBV's `checkAIConsent()` gate stays as the outer boundary.** `UniversalLLMClient` sits INSIDE the gate, not in front of it. Consent-first AI is non-negotiable [see 01_repo_audit.md section 1 AI Integration Status; 03_architecture_design.md section 4.1].
- **BrightForge has divergent branches.** `D:\BrightForge` (Phase 12 `src/idea/`) and `C:\Users\daley\Projects\BrightForge` (Phase 10 `src/model-intelligence/`) must be merged before any other BrightForge work. Neither is canonical alone [see 01_repo_audit.md sections 2, 6; 03_architecture_design.md section 5 P0.1].
- **No commit attribution to AI.** Per Marcus's MEMORY.md, never add `Co-Authored-By: Claude` lines. Marcus pushes manually [see MEMORY.md User Preferences].
- **Portfolio top 3 for Full Sail graduation Feb 6 2026:** (1) DeveloperProductivityTracker Capstone, (2) HoneyBadgerVault, (3) BrightForge post-merge. Capstone is the only C++ codebase and the single strongest AAA-practices proof point [see 04_strategy.md sections 3.1, 3.2, 3.4].

---

## 3. Step-by-Step Build Plan

Execute in strict order. Do not skip ahead. Phase 0 blocks Phase 1. Each task has a task ID format `PX.Y` [see 03_architecture_design.md section 5 Phase 0 BLOCKING Pre-work and Phase 1 Foundation Sprint].

### Phase 0 — Pre-work (Week 0, BLOCKING)

**P0.1 — Merge BrightForge canonical trunk** [see 01_repo_audit.md sections 2, 6; 03_architecture_design.md section 5 P0.1].
1. `cd D:\BrightForge` and verify `git status` is clean of intended work.
2. `git checkout -b feat/merge-phase10-model-intelligence`
3. `git remote add projects-copy C:\Users\daley\Projects\BrightForge`
4. `git fetch projects-copy`
5. Identify the `src/model-intelligence/` commits on `projects-copy/main`: `git log projects-copy/main --oneline --all -- src/model-intelligence`
6. Cherry-pick those commits onto the feature branch. Resolve conflicts keeping D:'s Phase 12 `src/idea/` additions intact.
7. Run `npm test` — all `--test` blocks must pass on the merged branch.
8. Push the branch, open PR against `origin/main`, self-merge.
9. After merge, delete or demote `C:\Users\daley\Projects\BrightForge` to a read-only worktree.

**P0.2 — Workspace hygiene** [see 01_repo_audit.md section 2 Workspace Pollution; 03_architecture_design.md section 5 P0.2].
1. `mkdir D:\_archive\brightforge-workspace-2026-04`
2. Move polluted directories into the archive: nested `BrightForge\`, nested `DeveloperProductivityTracker\`, `MarcusDaley_Lab3\`, `MarcusDaleyComputer Graphics_lab4\`, and all five `C:Usersdaley...` mangled-path directories.
3. Delete the `nul` file using `del \\.\D:\BrightForge\nul` — a normal `del nul` will fail because `nul` is a Windows reserved name.
4. Verify `ls D:\BrightForge` shows only project files.
5. Repeat for `C:\Users\daley\Projects\BrightForge` if that path still exists after P0.1.
6. Commit hygiene changes.

**P0.3 — HoneyBadgerVault rename** [see 01_repo_audit.md section 1 Agent-Alexander/HoneyBadgerVault identity finding; 03_architecture_design.md section 5 P0.3].
1. Close all editors, terminals, and IDEs pointed at `D:\Agent-Alexander`.
2. `move D:\Agent-Alexander D:\HoneyBadgerVault`
3. `cd D:\HoneyBadgerVault && git status && git remote -v` — verify origin still points at `github.com/GrizzwaldHouse/HoneyBadgerVault.git`.
4. Grep the entire portfolio for `Agent-Alexander` and update CI workflows, docs, VS Code workspaces, `MEMORY.md`.

**P0.4 — Extract `@grizzwald/llm-client`** [see 03_architecture_design.md reconciliation row 24 and section 5 P0.4; 01_repo_audit.md sections 3, 4, 7 llm-client duplication finding].
1. Create `github.com/GrizzwaldHouse/llm-client` via `gh repo create GrizzwaldHouse/llm-client --public --clone`.
2. Seed the TypeScript implementation using `D:\BrightForge\src\core\llm-client.js` as the reference (widest provider matrix) and `C:\Users\daley\Projects\Bob-AICompanion\src\core\llm-client.js` as the API surface (cleanest). Absorb grizz-optimizer's $1/day budget cap and advisory-only flag pattern without importing grizz code.
3. API: `class UniversalLLMClient(configOverride?)` with methods `chat(messages, options)`, `complete(prompt, options)`, `embed(texts, options)`, `getDailyUsage()`, `isProviderAvailable(name)`.
4. Provider matrix: Ollama, Groq, Cerebras, Together, Mistral, Gemini, Claude, OpenAI, OpenRouter, HF Inference Providers with `:cheapest`/`:fastest` routing hints. Mark Cerebras and Groq as LLM-only in provider metadata so VLM routing skips them.
5. YAML config schema validated with Zod at construction time.
6. Publish to GitHub Packages as `@grizzwald/llm-client`.
7. **Migration:**
   - HBV: refactor `D:\HoneyBadgerVault\server\ai\ai-orchestrator.ts` to import and instantiate `UniversalLLMClient` INSIDE the existing `checkAIConsent()` gate. Do not move the gate.
   - Bob: delete `C:\Users\daley\Projects\Bob-AICompanion\src\core\llm-client.js`; import from the package. Add `tests/package-migration.test.js` that fails if the local file reappears.
   - SeniorDevBuddy: delete or delegate `C:\Users\daley\Projects\SeniorDevBuddy\agentforge_autonomous\src\backend\services\ModelService.ts` to the package; wire into `AgentOrchestrator.ts`.
   - **grizz-optimizer: do NOT migrate.** Per MEMORY.md, it keeps its own `src/main/ai/llm-client.ts`.

### Phase 1 — Foundation Sprint (Weeks 1-3)

[see 03_architecture_design.md section 5 Phase 1 Foundation Sprint; 02_huggingface_reference.md section 1 SigLIP 2 model card; 01_repo_audit.md section 1 HBV existing infrastructure].

**1.1** HBV: Add `images` table and `image_embeddings` column to `D:\HoneyBadgerVault\shared\schema.ts` Drizzle schema. Write migration in `server/db/migrations/`.

**1.2** HBV: Create `D:\HoneyBadgerVault\server\pipeline\image-watcher.ts` using Chokidar v5 with `awaitWriteFinish: { stabilityThreshold: 2000 }` and SHA-256 deduplication.

**1.3** HBV: Create `D:\HoneyBadgerVault\server\pipeline\image-job-queue.ts` by reusing `server/extraction/download-queue.ts` primitives (`p-limit`, retry, circuit-breaker). Do not add BullMQ or Redis.

**1.4** HBV: Create `D:\HoneyBadgerVault\server\vision\siglip2-classifier.ts` using `@huggingface/transformers` with SigLIP 2 base ONNX in-process. Runs on CPU.

**1.5** HBV: Write `D:\HoneyBadgerVault\scripts\download-vision-models.ts` to pull SigLIP 2 base ONNX weights into `models/` (gitignored).

**1.6** HBV: Add React pages `D:\HoneyBadgerVault\client\src\pages\ImageGrid.tsx` and `ImageDetail.tsx` reusing TanStack Query and the existing hybrid-search API.

**1.7** HBV: vitest coverage for new `server/pipeline/` and `server/vision/` modules, minimum 80%. Test files beside sources as `*.test.ts`.

**1.8** BrightForge: Wrap the 40+ existing `--test` blocks in a vitest runner so CI produces real coverage. Add `vitest.config.js` and `npm test:coverage` script.

**Phase 1 exit criteria:** Drop a screenshot into the watched folder. Within 5 seconds it is classified by SigLIP 2, persisted in the `images` table, and returned by the existing hybrid-search endpoint when queried.

---

## 4. Sub-Agent Assignments

[see 03_architecture_design.md section 5 Sub-Agent Routing; 04_strategy.md section 3.4 execution sequencing].

| Task | Agent Type | Justification |
|---|---|---|
| P0.1 BrightForge merge | implementer | Git cherry-pick + conflict resolution; needs direct file access |
| P0.2 Workspace hygiene | general-purpose | Filesystem moves, low risk |
| P0.3 HBV rename | implementer | Path-sensitive; needs grep + update pass |
| P0.4 `@grizzwald/llm-client` extraction | planner | Architecture + API design; Zod schema; multi-repo migration coordination |
| P0.4 Consumer migrations (HBV, Bob, SeniorDevBuddy) | implementer | Mechanical refactors once package API is fixed |
| 1.1 Drizzle schema migration | implementer | Schema + migration writing |
| 1.2 Chokidar image watcher | implementer | Straightforward Node module |
| 1.3 image-job-queue reuse | implementer | Adapter over existing primitives |
| 1.4 SigLIP 2 classifier | researcher | Verify ONNX export availability + `@huggingface/transformers` usage before implementing |
| 1.5 Model download script | implementer | Simple CLI script |
| 1.6 React ImageGrid/ImageDetail | frontend-builder | React + TanStack Query UI work |
| 1.7 vitest coverage | reviewer | Test authoring + coverage enforcement |
| 1.8 BrightForge vitest wrapper | implementer | Tooling migration |
| Phase 2+ planning | Plan | Use plan mode before Phase 2 starts to re-baseline |
| Architecture questions | Explore | Use for codebase investigation when implementation requires deeper context |

---

## 5. Testing Strategy

[see 01_repo_audit.md section 1 HBV verified-build-gate; 03_architecture_design.md section 4.3 Testing Stack; 04_strategy.md section 3.4 Capstone C++ testing].

- **HBV (TypeScript/Node):** vitest for unit tests (`*.test.ts` beside sources); Playwright for E2E (`tests/e2e/`). Reuse the existing `verified-build-gate` pre-push hook — it already runs 15 tests. Add new pipeline/vision tests to that gate.
- **BrightForge (Node ESM + Python):** vitest wrapping the 40+ existing `--test` blocks; Python tests via pytest inside `src/forge3d/python/` when Forge3D work resumes (not in Phase 1).
- **Bob-AICompanion (Node ESM):** existing 6 `job-intelligence` npm test scripts stay; add `tests/package-migration.test.js` regression test for P0.4.
- **SeniorDevBuddy (TypeScript):** vitest + eslint CI (replaces the placeholder echo CI).
- **grizz-optimizer (TypeScript Electron):** vitest 2.1 + Playwright 1.59 already in place. Do NOT modify its test setup in Phase 0 or 1.
- **DeveloperProductivityTracker (C++ UE5):** Google Test inside UE5 Automation Framework. Phase 3 work — not in Phase 0 or 1.
- **Test file locations:** co-located with sources (`*.test.ts` beside the source) for all TypeScript repos; `tests/` for Playwright E2E only.
- **verified-build-gate reuse:** HBV's `script/build-gate/run-build-gate.ts` is the reference pattern. All new HBV test files must be picked up by it. Never bypass with `--no-verify`.
- **Minimum coverage:** 80% on new modules. Do not backfill tests on untouched existing code.

---

## 6. Definition of Done

[see 03_architecture_design.md section 5 exit criteria; CLAUDE.md Critical Rules; MEMORY.md User Preferences].

### Per-task
- [ ] Code implemented and committed.
- [ ] Unit tests written and passing.
- [ ] 80%+ coverage on new files.
- [ ] `npm run lint` and `npm run typecheck` (or equivalent) pass.
- [ ] File headers match Marcus's convention: filename, developer (Marcus Daley), date, purpose.
- [ ] No magic numbers, no magic strings, no hardcoded configuration values.
- [ ] Access modifiers set to most restrictive level that allows function.
- [ ] Observer-pattern compliance: events/callbacks, never polling.
- [ ] No `Co-Authored-By: Claude` or similar AI attribution in commit messages.

### Per-phase

**Phase 0 exit:**
- [ ] Single canonical BrightForge trunk pushed to `origin/main` with both `src/idea/` and `src/model-intelligence/` present.
- [ ] Both BrightForge workspaces contain only project files (no nested repos, no lab assignments, no mangled paths, no `nul`).
- [ ] `D:\Agent-Alexander` no longer exists; `D:\HoneyBadgerVault` is the only working copy.
- [ ] `@grizzwald/llm-client` published, consumed by HBV + Bob + SeniorDevBuddy, NOT consumed by grizz-optimizer.
- [ ] All four consumer repos build and tests pass.

**Phase 1 exit:**
- [ ] Drop screenshot -> classified by SigLIP 2 -> persisted -> returned by hybrid-search within 5 seconds end-to-end.
- [ ] `images` + `image_embeddings` tables live in HBV Drizzle schema.
- [ ] React `ImageGrid.tsx` and `ImageDetail.tsx` pages render and query the hybrid-search API.
- [ ] BrightForge vitest produces coverage report green in CI.
- [ ] No new Python, no new Redis, no new Turborepo dependencies introduced anywhere.

---

## 7. Known Landmines

1. **Cerebras and Groq are LLM-only.** Per `reports/02_huggingface_reference.md` Section 6, neither provider can serve Qwen2.5-VL, Pixtral, SmolVLM, GOT-OCR, or any VLM. Do not add them to VLM fallback chains. For VLM traffic, use HF Inference, Fireworks, Hyperbolic, Novita, Nscale, OVHcloud, Together, Featherless, or Z.ai [see 02_huggingface_reference.md section 6 provider capability matrix].

2. **BrightForge branches diverge on unique features.** `D:\BrightForge` has `src/idea/` (Phase 12); `C:\Users\daley\Projects\BrightForge` has `src/model-intelligence/` (Phase 10). Neither is canonical alone. Taking either unilaterally deletes unique work [see 01_repo_audit.md sections 2, 6; 03_architecture_design.md reconciliation row 23 and section 5 P0.1].

3. **HoneyBadgerVault is NOT greenfield.** It is a beta LMS document extraction vault with 17-table Drizzle schema, RRF hybrid-search, dual-provider AI orchestrator, verified-build-gate, and Playwright E2E already shipped. The image pipeline is additive. Do not rebuild `extraction-manager.ts`, `download-queue.ts`, `hybrid-search.ts`, or `ai-orchestrator.ts` — extend them [see 01_repo_audit.md section 1 HBV maturity; 03_architecture_design.md section 2 Variant B rationale].

4. **The `nul` file on `D:\BrightForge` needs Windows UNC syntax to delete.** A normal `del nul` fails because `nul` is a Windows reserved name. Use exactly: `del \\.\D:\BrightForge\nul` [see 01_repo_audit.md section 2 Workspace Pollution; 03_architecture_design.md section 5 P0.2].

5. **Local `llm-client` duplicates must not regress.** After P0.4, HBV, Bob, and SeniorDevBuddy each have regression tests that fail if a local `llm-client.js` or `llm-client.ts` reappears in their source trees. Do not satisfy a failing import by adding a local shim [see 01_repo_audit.md sections 3, 4, 7 llm-client duplication; 03_architecture_design.md section 5 P0.4].

6. **MEMORY.md: grizz-optimizer stays domestic.** `C:\Users\daley\grizz-optimizer\src\main\ai\llm-client.ts` keeps its own 5-tier fallback chain. It has domain-specific Ollama lifecycle management (`ollama/manager.ts`, `ollama/first-run.ts`, `ollama/hardware-detect.ts`) that the generic package must not know about. Do not migrate grizz-optimizer to `@grizzwald/llm-client` — ever [see MEMORY.md Related Projects; 03_architecture_design.md reconciliation row 24].

7. **No AI attribution in commits.** Per Marcus's MEMORY.md, never add `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` or similar lines to commit messages. Marcus pushes manually and reviews every commit [see MEMORY.md User Preferences].

8. **`checkAIConsent()` is the outer gate, not the inner one.** When migrating HBV to `@grizzwald/llm-client`, the consent gate stays OUTSIDE the client. Do not move consent checking into the package. HBV's privacy model depends on `ai-orchestrator.ts` being the single enforcement point [see 01_repo_audit.md section 1 AI Integration Status; 03_architecture_design.md section 4.1 Consent Boundary].

9. **Turborepo / Redis / BullMQ / Python FastAPI are forbidden for HBV.** The user's original strategy doc specifies these; the architect's Variant B report overrides them. HBV is single-process TypeScript. Adding new runtimes violates the 95/5 Rule and duplicates existing working code [see 00_user_strategy_doc.md vs 03_architecture_design.md section 2 Variant B, reconciliation rows 12, 13, 17, 22].

10. **Drizzle schema is the single source of truth.** When adding the `images` table, the migration goes in `shared/schema.ts` + `server/db/migrations/`. Do not create a parallel schema file or bypass Drizzle [see 01_repo_audit.md section 1 HBV schema; 03_architecture_design.md section 4.2 Database Layer].

11. **Verified-build-gate must stay green.** HBV's `script/build-gate/run-build-gate.ts` runs 15 tests on every push. New pipeline/vision modules must pass the gate before any commit ships. Never bypass with `--no-verify` [see 01_repo_audit.md section 1 verified-build-gate; 03_architecture_design.md section 4.3 Testing Stack].

12. **Full Sail graduation is Feb 6 2026.** The DeveloperProductivityTracker Capstone must be portfolio-ready and submitted to Epic Marketplace before that date (Phase 3 work). Phase 0 + Phase 1 must not consume time that belongs to Capstone polish [see 04_strategy.md sections 3.1, 3.2, 3.4 Capstone priority].

---

*End of EXECUTION_PROMPT — compiled 2026-04-08 by ai-audit-2026 compiler.*
