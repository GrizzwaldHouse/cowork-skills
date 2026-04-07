# Idea Intelligence System
# Developer: Marcus Daley
# Date: 2026-04-06
# Purpose: Reusable skill for building autonomous idea ingestion, classification, scoring, research, and indexing pipelines

---
name: idea-intelligence-system
description: Build event-driven Idea Intelligence pipelines that ingest idea files, classify with AI, score on weighted dimensions, research competitive gaps, and index with semantic embeddings. Use this skill when the user wants to build an autonomous idea processing system, an idea vault, an idea ranking engine, a competitive research tool, or anything that scans markdown/text/json files and applies AI scoring + categorization. Triggers on phrases like "idea system", "idea pipeline", "idea scoring", "brightforge ideas", "rank ideas with AI", "score ideas", or "idea intelligence".
user-invocable: false
---

# Idea Intelligence System

> Reusable architecture and implementation pattern for building autonomous idea processing pipelines that integrate with existing orchestration layers (event bus, task state, supervisor, storage) instead of creating parallel infrastructure.

## Description

Provides a complete blueprint for building event-driven idea intelligence systems. The pattern was originally designed for BrightForge but applies to any project that needs to:

- Scan a directory for idea files (markdown, text, JSON)
- Extract structured metadata (title, summary, tags, hash)
- Classify ideas with AI into categories
- Score ideas on weighted dimensions (profitability, portfolio value, etc.)
- Research competitive gaps via LLM analysis
- Generate vector embeddings for semantic search
- Cross-link related ideas in a graph

The skill enforces Marcus's coding standards: build ON existing orchestration (never beside it), Ollama-first AI, SQLite persistence, observer pattern (no polling), event-driven communication, and self-test blocks on every module.

## Prerequisites

- An existing orchestration layer with: EventBus, Storage (SQLite), TaskState (FSM), Supervisor (audit), LLMClient (provider chain)
- Ollama running locally OR access to a free LLM provider chain (Groq, Together, Cerebras)
- Node.js 18+ (for the JavaScript reference implementation) OR Python 3.10+ (for porting)
- better-sqlite3 (Node) or sqlite3 (Python) for persistence

## Usage

When a user requests an idea intelligence system, follow this 6-phase pattern:

1. **Research** the existing orchestration layer to understand integration points
2. **Design** the schema, events, and module structure (do NOT skip this)
3. **Implement** in 4 waves of parallel work (see Waves section)
4. **Validate** every module with --test self-test blocks
5. **Document** in a CLAUDE.md or architecture spec
6. **Integrate** with bridge layer if cross-system communication is needed

### Prompt Pattern

```
Build an Idea Intelligence System for [project] that:
- Scans [directory] for [file types]
- Classifies ideas into [categories]
- Scores on these dimensions: [list with weights]
- Stores in existing [database/orchestration layer]
- Integrates with [other systems] via decoupled bridge
Apply Marcus's coding standards from universal-coding-standards skill.
```

## The 6 Phases

### Phase 1: Ingestion Engine
Recursive directory scanner that detects idea files and extracts structured metadata.

**Key responsibilities:**
- Recursive readdir filtered by extension (.md, .txt, .json)
- SHA-256 content hashing for dedup
- Extract title (first heading or filename)
- Extract tags (frontmatter or inline #tags)
- Extract summary (first paragraph, max 500 chars)
- Emit `idea_detected` event per new idea

See `references/phase-1-ingestion.md` for full implementation pattern.

### Phase 2: Classification Engine
AI-powered categorization with embedding-based duplicate detection.

**Key responsibilities:**
- Structured LLM prompt returning JSON with category + confidence
- Embedding generation for each idea summary
- Cosine similarity comparison against existing ideas
- Threshold-based relationship creation: >0.92 = duplicate, 0.70-0.91 = related
- Emit `idea_classified` and `idea_duplicate` events

See `references/phase-2-classification.md` for prompt templates and similarity logic.

### Phase 3: Scoring Algorithm
Weighted scoring model with priority labels.

**Default weights** (configurable per project):
- profitability: 0.30
- portfolio_value: 0.25
- execution_speed: 0.15
- complexity_inverse: 0.15 (lower complexity = higher score)
- novelty: 0.15

**Priority thresholds:**
- HIGH: >= 0.75
- MID: 0.50-0.74
- LOW: 0.25-0.49
- SHINY_OBJECT: < 0.25

See `references/phase-3-scoring.md` for the LLM prompt and formula.

### Phase 4: Database Schema
Two tables added as a migration to existing orchestration storage.

**ideas table** (19 columns): id, title, summary, category, score_total, priority_label, 5 dimension scores, related_projects (JSON), missing_features (JSON), source_path, content_hash, embedding (JSON), vault_path, status, timestamps.

**idea_relationships table**: id, idea_id, related_idea_id, similarity_score, relationship_type, created_at.

**Indexes**: priority, category, score_total DESC, content_hash, status, both relationship sides.

See `references/phase-4-schema.md` for full SQL.

### Phase 5: Research Intelligence
Competitive analysis via LLM (only HIGH/MID priority ideas).

**Output structure:**
- similar_projects: array of competitor objects
- top_features: features competitors have
- missing_features: gaps the idea could fill
- gap_analysis: written analysis
- competitive_advantage: differentiator

See `references/phase-5-research.md` for prompt template.

### Phase 6: Indexing Engine
Vector embedding generation and semantic search.

**Key responsibilities:**
- Generate embeddings via Ollama nomic-embed-text (768-dim)
- Store as JSON array in ideas.embedding column
- Cosine similarity search function
- Cross-link via pairwise similarity computation
- Top-K semantic search API

See `references/phase-6-indexing.md` for cosine similarity implementation.

## Implementation Waves (Parallel Execution)

When implementing with a multi-agent team, structure work in 5 waves:

### Wave 1 — Foundation (Parallel)
- Add database migration to existing storage module (Phase 4)
- Add new event types to existing event bus
- Update LLM provider routing config
- Write bridge spec (if cross-system integration needed)
- Create test fixtures

### Wave 2 — Core Engines (Parallel, after Wave 1)
- Implement Phase 1 (Ingestion)
- Implement Phase 3 (Scoring) — math is testable without LLM

### Wave 3 — Intelligence (Parallel, after Wave 2)
- Implement Phase 2 (Classification) — needs ingestion
- Implement Phase 5 (Research) — needs scoring

### Wave 4 — Indexing (After Wave 3)
- Implement Phase 6 (Indexing + Cross-linking)

### Wave 5 — Integration
- Build the IdeaIntelligence facade class
- Write integration test (test-pipeline)
- Update package.json scripts and CLAUDE.md
- Run final lint + test verification

## Architecture Rules (Non-Negotiable)

1. **Build ON existing orchestration** — never create a parallel event bus, parallel database, or parallel task state
2. **Ollama-first** — use the existing UniversalLLMClient or equivalent provider chain, never hardcode a specific provider
3. **Migration-based schema** — add tables via migrations to existing DB, never create a separate idea database
4. **Observer pattern** — emit events for every state change, never poll
5. **Self-test blocks** — every module must include a `--test` block that validates structurally without requiring LLM availability
6. **Configuration-driven** — weights, thresholds, categories must come from config files, never hardcoded
7. **No external dependencies** — use only what the parent project already has installed
8. **Decoupled bridges** — cross-system integration via HTTP POST or pub/sub, never shared imports

## Files Created Per Implementation

```
src/idea/idea-ingestion.js       # Phase 1
src/idea/idea-classifier.js      # Phase 2
src/idea/idea-scoring.js         # Phase 3
src/idea/research-agent.js       # Phase 5
src/idea/idea-indexer.js         # Phase 6
src/idea/index.js                # Facade
src/idea/test-pipeline.js        # Integration test
src/idea/fixtures/               # Test idea files
docs/idea-intelligence-spec.md   # Architecture spec
docs/IDEA_SYSTEM_TODO.md         # Execution checklist
```

## Files Modified Per Implementation

```
src/orchestration/storage.js     # Add migration v2 + CRUD
src/orchestration/event-bus.js   # Add 9 new event types
config/orchestration.yaml        # Events, agents, idea_intelligence section
config/llm-providers.yaml        # Task routing for idea_* tasks
package.json                     # Test scripts
CLAUDE.md                        # Architecture docs update
```

## Reference Implementations

This skill includes a complete reference implementation built for BrightForge:

- **Spec**: `D:\BrightForge\docs\idea-intelligence-spec.md`
- **TODO**: `D:\BrightForge\docs\IDEA_SYSTEM_TODO.md`
- **Handoff**: `D:\BrightForge\docs\IDEA_SYSTEM_HANDOFF.md`

To port to a new project:
1. Read the spec to understand the architecture
2. Read the TODO for step-by-step file creation
3. Substitute project-specific paths (storage location, event bus class name, LLM client import)
4. Adjust scoring weights and categories to match the project's domain
5. Run the integration test to verify

## Related Skills

- **architecture-patterns** — Observer pattern, file organization (auto-loaded)
- **universal-coding-standards** — Comment style, file headers, error handling (auto-loaded)
- **multi-agent-pipeline** — Quality gate enforcement for orchestrated builds
- **dev-workflow** — Brainstorm-first methodology (auto-loaded)

## Triggers

Use this skill when the user says any of:
- "Build an idea system"
- "Idea intelligence pipeline"
- "Score and rank ideas"
- "Idea classification"
- "BrightForge ideas"
- "Idea vault with AI"
- "Competitive research for ideas"
- "Semantic search for ideas"
- "Autonomous idea processing"
