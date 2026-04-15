# User-Provided Strategy Document (AUTHORITATIVE INPUT)

**Source:** Provided directly by Marcus Daley in the audit request.
**Status:** Authoritative reference. Downstream agents must reconcile their recommendations against this document. Disagreements must be explicitly called out with justification.

**Scope note:** This document covers 4 repos (grizz-optimizer, BrightForge, HoneyBadgerVault, Bob-AICompanion). The full audit covers 9 local paths. The extra 5 (Agent-Alexander, portfolio-website, DeveloperProductivityTracker Capstone, SeniorDevBuddy, second BrightForge) must be integrated as "adjacent portfolio assets" and cross-referenced where applicable.

---

# GrizzwaldHouse ecosystem: architecture, AI pipeline, and strategy blueprint

**The four-repository GrizzwaldHouse ecosystem -- grizz-optimizer, BrightForge, HoneyBadgerVault, and Bob-AICompanion -- has the ingredients of a compelling AI-powered developer toolkit, and HoneyBadgerVault should be the flagship product.** An AI image pipeline combining CLIP zero-shot classification, IBM Granite-Docling OCR, and Qwen2.5-VL vision-language understanding can run with a hybrid local+API architecture where two of three models cost nothing to operate locally, while the heaviest model falls back to HuggingFace Inference Providers. This report delivers the complete technical architecture, model-by-model integration plan, scaffolding structure ready for Claude Code, and a prioritized roadmap across all four repos.

Note: All four repositories are private and could not be directly inspected. The analysis below is built from the detailed feature descriptions provided, extensive research into the specified models and architecture patterns, and best-practice frameworks for this class of system.

---

## Repository ecosystem assessment and inter-project synergies

Based on naming conventions, stated purposes, and the features described, each repository occupies a distinct role in the ecosystem:

**HoneyBadgerVault** is the storage and asset management layer -- the natural home for an AI-powered image pipeline handling ingestion, classification, OCR, intelligent renaming, and search/retrieval. This is the highest-value project because AI image management tools are **underserved relative to image generation tools**, and the combination of CLIP + Granite-Docling + Qwen2.5-VL creates genuine differentiation. The vault metaphor maps perfectly to project-based indexing and secure asset organization.

**Bob-AICompanion** serves as the intelligence and orchestration layer. An AI companion can function as the unifying context bridge across the entire ecosystem -- querying HoneyBadgerVault's indexed assets, leveraging grizz-optimizer's capabilities, and providing educational guidance. Bob should evolve into an **MCP-enabled agent** (Model Context Protocol, Anthropic's standard for agent-tool coordination) that dynamically discovers and invokes tools registered by sibling repositories.

**grizz-optimizer** acts as the performance and optimization foundation. Whether this targets code optimization, build performance, or model inference tuning, it provides shared utility that other projects consume. This positions well as a library/service layer that BrightForge and HoneyBadgerVault call into for performance-critical operations.

**BrightForge** rounds out the ecosystem as the development workflow tool. The "forge" metaphor suggests building, compiling, or transforming -- likely a dev-tool or code-generation utility. This complements HoneyBadgerVault (asset management) and Bob (AI guidance) to form a complete developer workflow.

The cross-repo integration architecture should use **Redis as the shared event bus** with BullMQ for job orchestration, a **shared vector store** (ChromaDB or sqlite-vec) for embeddings that all projects can query, and **shared TypeScript type packages** for API contracts and event schemas.

---

## The three AI models: capabilities, sizing, and deployment strategy

### CLIP ViT-L/14 -- the classification backbone that runs everywhere

OpenAI's `clip-vit-large-patch14` is the ideal zero-shot image classifier for this pipeline. It encodes images and text into a shared **768-dimensional embedding space**, enabling classification against arbitrary categories without fine-tuning. Feed it an image and the labels "screenshot," "photograph," "diagram," "document" -- it returns probability scores for each.

The model weighs **1.71 GB in safetensors format** and requires only **~816 MB VRAM at FP16** or **~204 MB at INT4 quantization**. Inference takes approximately 20-50ms on GPU and 200-500ms on CPU. This makes CLIP the easiest model to run locally -- it should **always run on-device** as the first pipeline stage. In Node.js, `@huggingface/transformers` (the successor to `@xenova/transformers`) runs CLIP via ONNX Runtime with quantized models, requiring no Python at all. CLIP embeddings also power semantic image search: store the 768-dim vector alongside each image, then query with text embeddings for "find photos of sunset over mountains."

### IBM Granite-Docling 258M -- document understanding in a tiny package

The `ibm-granite/granite-docling-258M` model represents a breakthrough in compact document AI. At just **258 million parameters**, it replaces an entire pipeline of separate tools (layout detection, OCR, table extraction, equation parsing, code recognition) with a single vision-language model. It outputs **DocTags** -- IBM's structured markup format that preserves tables, equations, code blocks, and document hierarchy.

Performance numbers are impressive for its size: **0.97 TEDS-structure on table recognition** (FinTabNet), **0.988 F1 on code recognition**, and **0.968 F1 on equation extraction**. It significantly outperforms Tesseract for any document with structure beyond plain text. The model runs comfortably on CPU with the `docling` Python library, via Ollama (`ibm/granite-docling:258m`), or through ONNX export. At 258M parameters, this is the **second "always local" model** in the pipeline. License is Apache 2.0 -- free for commercial use.

### Qwen2.5-VL 7B Instruct -- the heavy hitter for rich understanding

Alibaba's `Qwen/Qwen2.5-VL-7B-Instruct` is the most capable model in the stack, excelling at detailed image descriptions, multi-language OCR, chart/table parsing to structured formats, and even UI screenshot understanding. It's the model that generates human-readable descriptions and intelligent file names.

However, it demands **~17 GB VRAM at FP16** (a 24 GB GPU like an RTX 4090 is recommended) or **~4-5 GB at INT4 quantization** (viable on 8 GB GPUs). This makes it the only model that **should default to API inference** with local as an opt-in for users with capable hardware. HuggingFace Inference Providers route Qwen2.5-VL through multiple backends (Together AI, Novita AI, and others) with a free monthly credit allocation. Local deployment via Ollama (`qwen2.5vl:7b`) is straightforward for those with the GPU headroom.

### The hybrid inference architecture

The three-tier model deployment strategy follows a clear principle: **run locally what you can, call APIs for what you can't**:

| Model | Size | Local Viable? | Default Mode | Fallback |
|-------|------|--------------|--------------|----------|
| CLIP ViT-L/14 | 1.71 GB | Yes, even CPU | **Always local** (Transformers.js/ONNX) | HF Inference API |
| Granite-Docling | 258M params | Yes, even CPU | **Always local** (Ollama or FastAPI) | HF Space (free CPU) |
| Qwen2.5-VL-7B | ~17 GB FP16 | Only with 24GB+ GPU | **API-first** (HF Inference Providers) | Local Ollama if GPU available |

The unified client should implement a **circuit breaker pattern**: detect local failures (OOM, timeout, service unavailable), route to cloud, and cache all inference results by content hash. The `@huggingface/inference` npm package (v4.13+) provides `InferenceClient` with `provider: "auto"` routing, while `@huggingface/transformers` handles local ONNX execution -- both from the same Node.js process.

---

## Event-driven pipeline architecture for image processing

The image pipeline should decompose into five discrete stages, orchestrated by **BullMQ with Redis** as the job queue. BullMQ's `FlowProducer` natively supports directed acyclic graph (DAG) execution, where a parent job waits for all child jobs to complete:

**Stage 1 -- Ingest**: Chokidar v5 watches designated directories for new image files. The `awaitWriteFinish` option (stabilityThreshold: 2000ms) prevents processing half-written files. Each file gets SHA-256 hashed for deduplication, then a job enters the BullMQ pipeline.

**Stage 2 -- Classify**: CLIP runs zero-shot classification against configurable category sets (e.g., "screenshot," "photo," "diagram," "document," "artwork"). The 768-dim embedding is extracted simultaneously for later search indexing. This runs in-process via Transformers.js -- no Python needed.

**Stage 3 -- Extract**: Granite-Docling processes documents and text-heavy images for structured OCR. For photographs, EXIF metadata is extracted via `sharp` or `exif-parser`. Qwen2.5-VL generates rich natural-language descriptions for images that benefit from deeper understanding.

**Stage 4 -- Rename & Organize**: Based on classification results, OCR content, and AI descriptions, the system generates intelligent file names and sorts into project-based directory structures. Rule engines allow user-customizable naming patterns.

**Stage 5 -- Index**: All metadata, embeddings, OCR text, and descriptions are written to the search index. **SQLite with FTS5 + sqlite-vec** is the recommended starting stack -- zero infrastructure, supports both keyword search (via FTS5 full-text indexing) and semantic search (via sqlite-vec vector similarity on CLIP embeddings), and handles hundreds of thousands of images without breaking a sweat.

Real-time progress flows to the React dashboard via **Server-Sent Events (SSE)**, not WebSocket. SSE provides automatic reconnection, works through all proxies, requires roughly 50 lines of server code versus 200+ for WebSocket, and handles the unidirectional server->client data flow that pipeline monitoring needs. User actions (cancel, retry, configure) use standard REST endpoints.

---

## Scaffolding structure for HoneyBadgerVault's AI image pipeline

This structure is designed to be handed directly to Claude Code for implementation. It uses **Turborepo + pnpm workspaces** to manage the Node.js API, Python inference service, and React dashboard as a coordinated monorepo:

```
honeybadgervault/
|-- turbo.json
|-- package.json
|-- pnpm-workspace.yaml
|-- .env.example
|-- docker-compose.yml              # Redis + API + Inference + optional GPU
|
|-- apps/
|   |-- web/                         # React dashboard (Vite + React 19)
|   |   |-- package.json
|   |   |-- vite.config.ts
|   |   |-- index.html
|   |   \-- src/
|   |       |-- main.tsx
|   |       |-- App.tsx
|   |       |-- hooks/
|   |       |   |-- usePipelineEvents.ts    # SSE hook for real-time updates
|   |       |   |-- useImageSearch.ts       # Hybrid text + semantic search
|   |       |   \-- useProjects.ts          # Project-based organization
|   |       |-- components/
|   |       |   |-- Dashboard.tsx            # Pipeline status overview
|   |       |   |-- ImageGrid.tsx            # Browsable image gallery
|   |       |   |-- SearchBar.tsx            # Text + semantic search
|   |       |   |-- PipelineMonitor.tsx      # Real-time job progress
|   |       |   |-- ProjectSidebar.tsx       # Project navigation
|   |       |   \-- ImageDetail.tsx          # Full metadata + AI descriptions
|   |       |-- lib/
|   |       |   \-- api.ts                   # API client (TanStack Query)
|   |       \-- types/                       # Imports from @hbv/shared-types
|   |
|   |-- api/                         # Node.js API server (Express/Fastify)
|   |   |-- package.json
|   |   |-- tsconfig.json
|   |   \-- src/
|   |       |-- index.ts                     # Server entry point
|   |       |-- routes/
|   |       |   |-- images.ts                # CRUD + search endpoints
|   |       |   |-- projects.ts              # Project management
|   |       |   |-- pipeline.ts              # Pipeline control (start/stop/retry)
|   |       |   \-- events.ts                # SSE endpoint for real-time updates
|   |       |-- services/
|   |       |   |-- file-watcher.ts          # Chokidar v5 directory monitoring
|   |       |   |-- pipeline-orchestrator.ts # BullMQ FlowProducer pipeline DAG
|   |       |   |-- sse-broadcaster.ts       # EventEmitter -> SSE bridge
|   |       |   \-- hybrid-inference.ts      # Local/API model routing
|   |       |-- workers/
|   |       |   |-- classify-worker.ts       # CLIP via Transformers.js (ONNX)
|   |       |   |-- rename-worker.ts         # Intelligent file renaming logic
|   |       |   \-- index-worker.ts          # SQLite FTS5 + sqlite-vec indexing
|   |       \-- lib/
|   |           |-- db.ts                    # SQLite connection + migrations
|   |           |-- cache.ts                 # Redis inference result cache
|   |           \-- config.ts                # Environment configuration
|   |
|   \-- inference/                   # Python AI microservice (FastAPI)
|       |-- pyproject.toml
|       |-- Dockerfile
|       |-- requirements.txt
|       \-- src/
|           |-- server.py                    # FastAPI app with endpoints
|           |-- model_pool.py                # Singleton lazy-loading model manager
|           |-- models/
|           |   |-- docling_ocr.py           # Granite-Docling-258M wrapper
|           |   \-- qwen_vision.py           # Qwen2.5-VL-7B-Instruct wrapper
|           |-- routes/
|           |   |-- ocr.py                   # POST /ocr -- document extraction
|           |   \-- describe.py              # POST /describe -- image description
|           \-- utils/
|               \-- image_prep.py            # Resize, format conversion
|
|-- packages/
|   |-- shared-types/                # TypeScript types shared across apps
|   |   |-- package.json
|   |   \-- src/
|   |       |-- events.ts                    # PipelineEvent, JobStatus types
|   |       |-- jobs.ts                      # BullMQ job data interfaces
|   |       |-- api.ts                       # Request/response schemas
|   |       \-- models.ts                    # Model configuration types
|   |-- db/                          # Database access layer
|   |   |-- package.json
|   |   \-- src/
|   |       |-- schema.sql                   # SQLite schema (images, projects, FTS5, vec)
|   |       |-- queries.ts                   # Prepared statement wrappers
|   |       \-- migrations/
|   \-- config/                      # Shared configuration
|       \-- src/
|           |-- redis.ts
|           |-- paths.ts                     # Watch dirs, output dirs, model cache
|           \-- models.ts                    # Model tier definitions + fallback rules
|
|-- models/                          # Local model cache directory
|   \-- .gitkeep
|
\-- scripts/
    |-- setup.sh                     # Install deps, pull models, init DB
    |-- seed-test-images.sh          # Sample images for development
    \-- download-models.sh           # Pull ONNX CLIP + Ollama models
```

The key design decisions embedded in this structure: CLIP classification runs **inside the Node.js process** via Transformers.js (no Python dependency for the most frequent operation), Granite-Docling and Qwen2.5-VL run in a **separate Python FastAPI service** with a singleton model pool for efficient memory management, and **BullMQ orchestrates the entire pipeline** with Redis as the backbone for both job queues and inference result caching.

---

## HuggingFace integration patterns and deployment options

The HuggingFace ecosystem provides three integration surfaces relevant to this project. The **`@huggingface/inference` npm package** (v4.13+, ~157K weekly downloads) provides `InferenceClient` with unified access to 15+ inference providers -- a single `provider: "auto"` parameter routes requests to the cheapest available backend. The **`@huggingface/transformers` package** (formerly `@xenova/transformers`) runs ONNX-converted models directly in Node.js, with quantized CLIP models as small as 200 MB. And **HuggingFace Spaces** can host Gradio or Docker-based inference endpoints for free on CPU hardware -- a perfect fallback for Granite-Docling.

The free tier of HuggingFace Inference Providers offers generous monthly credits sufficient for development and light production use. The PRO tier at **$9/month** provides 20x more credits and ZeroGPU priority on Spaces -- an excellent value for early-stage products. For production scale, Inference Endpoints offer dedicated GPU instances with pay-per-second billing.

A practical deployment ladder looks like this: start with free-tier API calls during development, deploy Granite-Docling to a free CPU Space as a backup endpoint, run CLIP locally from day one via ONNX, and add local Qwen2.5-VL via Ollama only when users have appropriate hardware. This approach keeps **infrastructure costs at effectively zero** during development and early launch.

---

## Monetization strategy and portfolio prioritization

The AI developer tools market is experiencing explosive growth -- **AI tools now represent 26.4% of all SaaS transactions**, up from 8.8% in early 2025. The dominant pricing model for tools like Cursor ($20/mo), Windsurf ($15/mo), and GitHub Copilot ($10/mo) is **tiered freemium with usage-based AI metering**. The recommended pricing structure for HoneyBadgerVault:

- **Free**: Core pipeline features, 50 AI classifications/month, local-only inference
- **Pro ($15/month)**: 1,000 AI credits, batch processing, priority queuing, API access
- **Team ($35/user/month)**: Shared projects, SSO, admin controls, unlimited local inference
- **Enterprise (custom)**: Self-hosted, SLA, audit logs, BYOK (Bring Your Own Key)

The critical insight is to **implement usage metering from day one** -- track every inference call before monetizing. This creates the data needed to set pricing tiers and proves product-market fit. Offering BYOK (users provide their own HuggingFace API key) reduces compute costs while increasing stickiness.

**Portfolio priority should be:** HoneyBadgerVault first (strongest market opportunity, most monetizable, demonstrates full-stack AI integration), Bob-AICompanion second (unique educational angle, potential as ecosystem unifier via MCP), BrightForge third (polish to production quality), and grizz-optimizer as the maintained utility foundation.

---

## Implementation roadmap across all four repos

**Phase 1 -- Foundation Sprint (Weeks 1-3)**
Focus exclusively on HoneyBadgerVault. Initialize the Turborepo scaffolding structure above. Implement the file watcher with Chokidar, BullMQ pipeline orchestration with Redis, and CLIP classification via Transformers.js. Build the SQLite schema with FTS5 + sqlite-vec. Create a minimal React dashboard showing pipeline status via SSE. Goal: **drop an image into a watched folder and see it classified, renamed, and searchable within seconds.**

**Phase 2 -- AI Depth (Weeks 4-6)**
Add the Python inference service with Granite-Docling for document OCR and Qwen2.5-VL for rich descriptions. Implement the hybrid inference client with local/API fallback logic and circuit breakers. Add semantic search using CLIP embeddings. Build project-based organization in the UI. Goal: **full five-stage pipeline operational with all three models.**

**Phase 3 -- Polish and Ecosystem (Weeks 7-10)**
Polish all four repos: upgrade READMEs with screenshots, architecture diagrams, and GIFs. Add GitHub Actions CI/CD, automated tests, and badges. Deploy a HoneyBadgerVault demo to HuggingFace Spaces. Begin Bob-AICompanion development as an MCP-enabled agent that can query HoneyBadgerVault's index. Wire grizz-optimizer into the pipeline for performance monitoring. Goal: **portfolio-ready repositories with live demos.**

**Phase 4 -- Monetization and Education (Weeks 11-16)**
Implement usage metering and the freemium pricing tier. Build Bob's educational quest system: progressive challenges teaching AI pipeline concepts (data collection -> model selection -> pipeline design -> deployment). Create the shared embedding store accessible across all repos. Launch landing pages and validate willingness to pay. Goal: **first paying users and an educational product that demonstrates the full ecosystem.**

---

## Conclusion: where this ecosystem can go

The GrizzwaldHouse ecosystem has a clear competitive moat available to it: **the combination of three complementary open-source AI models (CLIP + Granite-Docling + Qwen2.5-VL) running in a hybrid local+API architecture that costs nearly nothing to operate.** Most competing image management tools rely entirely on cloud APIs, creating ongoing costs and privacy concerns. A local-first pipeline that falls back to APIs only when needed addresses both.

The scaffolding structure provided above is intentionally Claude Code-ready -- every directory, file, and technology choice is specified with enough detail to begin implementation immediately. The most critical architectural decision is **keeping CLIP inference inside the Node.js process** via ONNX (eliminating the Python dependency for the most frequent operation) while isolating the heavier VLMs behind a FastAPI microservice that can scale independently.

Bob-AICompanion's long-term value is as the **intelligence mesh** connecting all four repos -- an MCP client that discovers tools from HoneyBadgerVault ("search_images," "classify_batch"), grizz-optimizer ("benchmark_pipeline"), and BrightForge, providing a unified conversational interface to the entire ecosystem. Combined with educational gamification (quest-based learning of AI system building), this positions the portfolio not just as a set of tools but as a learning platform for the next generation of AI-native developers.
