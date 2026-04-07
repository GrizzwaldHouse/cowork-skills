# Idea Intelligence System — Task Checklist

// Author: Marcus Daley
// Date: 2026-04-06
// Purpose: Executable task list for implementing the Idea Intelligence System
// Use with: Claude Code Tasks system or as a reference checklist

---

## How to Use

This file is the canonical task list for the Idea Intelligence System. Either:

1. **Manual mode**: Walk through checkboxes one at a time
2. **Claude Code mode**: Ask Claude to "Read tasks.md from the idea-intelligence-system skill and execute it"
3. **Multi-agent mode**: Use `/orchestrate feature-build` and feed this file as the task breakdown

Each task includes: file path, dependencies, acceptance criteria, and validation command.

---

## Wave 1 — Foundation (Parallel)

### TASK 1.1: Database Migration
- **File**: `src/orchestration/storage.js` (modify)
- **Dependencies**: None
- **Reference**: `references/phase-4-schema.md`

- [ ] Add migration v2 to MIGRATIONS array (after existing v1)
- [ ] Create `ideas` table with 19 columns + CHECK constraints
- [ ] Create `idea_relationships` table with foreign keys
- [ ] Add 7 indexes (priority, category, score, hash, status, both rel sides)
- [ ] Add insertIdea(idea) method
- [ ] Add getIdea(id) method
- [ ] Add updateIdea(id, fields) method with auto updated_at
- [ ] Add deleteIdea(id) method
- [ ] Add getIdeasByPriority(label) method
- [ ] Add getIdeasByCategory(cat) method
- [ ] Add getIdeasByStatus(status) method
- [ ] Add findByHash(hash) method
- [ ] Add searchIdeas(query) method
- [ ] Add getTopIdeas(limit) method
- [ ] Add getAllIdeas() method
- [ ] Add insertRelationship(rel) method
- [ ] Add getRelationships(ideaId) method
- [ ] Add findDuplicates(ideaId) method
- [ ] Update --test block to cover new CRUD methods
- [ ] **Validate**: `node src/orchestration/storage.js --test` passes

### TASK 1.2: Event Types
- **File**: `src/orchestration/event-bus.js` (modify), `config/orchestration.yaml` (modify)
- **Dependencies**: None

- [ ] Add 9 events to VALID_EVENT_TYPES array in event-bus.js:
  - idea_detected
  - idea_classified
  - idea_duplicate
  - idea_scored
  - idea_ranked
  - research_started
  - research_completed
  - idea_indexed
  - idea_linked
- [ ] Add same 9 events to config/orchestration.yaml under event_bus.valid_event_types
- [ ] Add 5 agents under task_state.valid_agents:
  - IngestionAgent
  - ClassificationAgent
  - ScoringAgent
  - ResearchAgent
  - IndexingAgent
- [ ] Add new idea_intelligence config section (see SKILL.md section 7)
- [ ] **Validate**: `node src/orchestration/event-bus.js --test` passes

### TASK 1.3: LLM Provider Routing
- **File**: `config/llm-providers.yaml` (modify)
- **Dependencies**: None

- [ ] Add task routing entries:
  - idea_classification: prefer [ollama, groq], max_tokens 200
  - idea_scoring: prefer [ollama, groq], max_tokens 300
  - idea_research: prefer [ollama, groq, claude], max_tokens 1000
  - idea_embedding: prefer [ollama], model_override nomic-embed-text

### TASK 1.4: Bridge Spec (Design Only)
- **File**: `docs/honeybadger-bridge-spec.md` (create new)
- **Dependencies**: None
- **Reference**: SKILL.md section 8

- [ ] Write architecture for HTTP POST event bridge
- [ ] Define event schema (event_id, timestamp, source, target, type, payload, status)
- [ ] Include ASCII architecture diagram
- [ ] Document event flow: idea_scored → HBV → indexed → ack
- [ ] Integration instructions for both repos
- [ ] Testing plan with curl examples
- [ ] **NO CODE** — design document only

### TASK 1.5: Test Fixtures
- **File**: `src/idea/fixtures/` (create new directory + 3 files)
- **Dependencies**: None

- [ ] Create `sample-idea-1.md` with frontmatter tags + heading
- [ ] Create `sample-idea-2.txt` with inline #tags
- [ ] Create `sample-idea-3.json` with structured fields
- [ ] Each file represents a different category for testing classification

---

## Wave 2 — Core Engines (Parallel, after Wave 1)

### TASK 2.1: Ingestion Engine (Phase 1)
- **File**: `src/idea/idea-ingestion.js` (create new)
- **Dependencies**: TASK 1.1 (storage), TASK 1.2 (events), TASK 1.5 (fixtures)
- **Reference**: `references/phase-1-ingestion.md`

- [ ] File header with Marcus Daley convention
- [ ] ESM imports (fs/promises, path, crypto, error-handler)
- [ ] Class IdeaIngestion with constructor(storage, eventBus)
- [ ] Method: scan(directory) — recursive walk, dedup, emit events
- [ ] Method: walkDirectory(dir) — recursive readdir filter
- [ ] Method: processFile(filePath) — hash, dedup check, extract metadata
- [ ] Method: extractMarkdownMeta(content, filePath)
- [ ] Method: extractTextMeta(content, filePath)
- [ ] Method: extractJsonMeta(content, filePath)
- [ ] --test self-test block
- [ ] Export class
- [ ] **Validate**: `node src/idea/idea-ingestion.js --test` passes

### TASK 2.2: Scoring Algorithm (Phase 3)
- **File**: `src/idea/idea-scoring.js` (create new)
- **Dependencies**: TASK 1.1 (storage), TASK 1.2 (events)
- **Reference**: `references/phase-3-scoring.md`

- [ ] File header
- [ ] Class IdeaScoring with constructor(storage, eventBus, llmClient, config)
- [ ] DEFAULT_WEIGHTS constant (sums to 1.00)
- [ ] THRESHOLDS constant (HIGH 0.75, MID 0.50, LOW 0.25)
- [ ] Method: score(ideaRecord) — LLM call, validate, compute, label, persist
- [ ] Method: validateDimensions(parsed) — clamp to 0.0-1.0
- [ ] Method: computeScore(d) — weighted sum with complexity inversion
- [ ] Method: assignPriority(score) — threshold lookup
- [ ] Method: buildPrompt(ideaRecord)
- [ ] --test self-test block (math only, no LLM needed)
- [ ] **Validate**: `node src/idea/idea-scoring.js --test` passes

---

## Wave 3 — Intelligence (Parallel, after Wave 2)

### TASK 3.1: Classification Engine (Phase 2)
- **File**: `src/idea/idea-classifier.js` (create new)
- **Dependencies**: TASK 2.1 (ingestion), TASK 1.1 (storage)
- **Reference**: `references/phase-2-classification.md`

- [ ] File header
- [ ] Class IdeaClassifier with constructor(storage, eventBus, llmClient)
- [ ] validCategories constant
- [ ] duplicateThreshold (0.92), relatedThreshold (0.70)
- [ ] Method: classify(ideaRecord) — LLM call, validate, persist
- [ ] Method: detectDuplicates(ideaRecord, allIdeas) — embedding compare
- [ ] Method: cosineSimilarity(a, b) — pure math helper
- [ ] Method: buildPrompt(ideaRecord)
- [ ] --test self-test block (cosine math)
- [ ] **Validate**: `node src/idea/idea-classifier.js --test` passes

### TASK 3.2: Research Agent (Phase 5)
- **File**: `src/idea/research-agent.js` (create new)
- **Dependencies**: TASK 2.2 (scoring), TASK 1.1 (storage)
- **Reference**: `references/phase-5-research.md`

- [ ] File header
- [ ] Class ResearchAgent with constructor(storage, eventBus, llmClient, config)
- [ ] minPriority filter (default 'MID')
- [ ] Method: getAllowedPriorities() — derive from minPriority
- [ ] Method: analyze(scoredIdea) — skip if priority too low, LLM call, persist
- [ ] Method: validateReport(report) — required fields check
- [ ] Method: analyzeBatch(scoredIdeas)
- [ ] Method: buildPrompt(idea)
- [ ] --test self-test block (priority filtering, validation)
- [ ] **Validate**: `node src/idea/research-agent.js --test` passes

---

## Wave 4 — Indexing (After Wave 3)

### TASK 4.1: Indexing Engine (Phase 6)
- **File**: `src/idea/idea-indexer.js` (create new)
- **Dependencies**: TASK 3.1 (classification), TASK 1.1 (storage)
- **Reference**: `references/phase-6-indexing.md`

- [ ] File header
- [ ] Class IdeaIndexer with constructor(storage, eventBus, llmClient, config)
- [ ] embeddingModel (default 'nomic-embed-text')
- [ ] Method: generateEmbedding(text) — LLM call
- [ ] Method: index(ideaRecord) — embed, store, emit
- [ ] Method: crossLink(ideaId) — pairwise similarity, create relationships
- [ ] Method: search(queryText, topK) — semantic search
- [ ] Method: indexAll() — process all unindexed ideas
- [ ] Static method: cosineSimilarity(a, b) with zero-vector handling
- [ ] --test self-test block (cosine math, edge cases)
- [ ] **Validate**: `node src/idea/idea-indexer.js --test` passes

---

## Wave 5 — Integration

### TASK 5.1: Idea Intelligence Facade
- **File**: `src/idea/index.js` (create new)
- **Dependencies**: All Wave 1-4 tasks complete

- [ ] File header
- [ ] Import all 5 phase modules
- [ ] Class IdeaIntelligence with constructor(orchestrator, llmClient)
- [ ] Instantiate all 5 sub-modules
- [ ] Method: processIdea(ideaRecord) — classify → score → research → index
- [ ] Method: runPipeline(directory) — full end-to-end
- [ ] Method: search(query, topK) — delegate to indexer
- [ ] Method: getStats() — counts by priority, category, status
- [ ] --test self-test block
- [ ] Export class

### TASK 5.2: Integration Test
- **File**: `src/idea/test-pipeline.js` (create new)
- **Dependencies**: TASK 5.1

- [ ] Initialize Orchestrator
- [ ] Initialize IdeaIntelligence
- [ ] Create temp ideas/ directory with fixtures
- [ ] Run runPipeline() end-to-end
- [ ] Verify: 3 ideas ingested, classified, scored
- [ ] Verify: HIGH/MID ideas got research reports
- [ ] Verify: semantic search returns ranked results
- [ ] Verify: cross-links created
- [ ] Cleanup temp data
- [ ] PASS/FAIL report per step
- [ ] **Note**: If Ollama unavailable, skip LLM-dependent assertions

### TASK 5.3: Package.json Scripts
- **File**: `package.json` (modify)
- **Dependencies**: All previous tasks

- [ ] Add test-ingestion script
- [ ] Add test-classifier script
- [ ] Add test-scoring script
- [ ] Add test-research script
- [ ] Add test-indexer script
- [ ] Add test-idea-facade script
- [ ] Add test-idea-pipeline script
- [ ] Add test-ideas aggregate script

### TASK 5.4: CLAUDE.md Update
- **File**: `CLAUDE.md` (modify)
- **Dependencies**: All previous tasks

- [ ] Add Idea Intelligence section under Architecture
- [ ] Add test commands to Commands section
- [ ] Add src/idea/ to file structure diagram
- [ ] Document the 6 phases briefly
- [ ] Link to docs/idea-intelligence-spec.md

### TASK 5.5: Final Validation
- **Dependencies**: All previous tasks

- [ ] `npm run lint` — zero errors, zero warnings
- [ ] `npm run test-ideas` — all 6 module tests pass
- [ ] `node src/orchestration/storage.js --test` — no regression
- [ ] `node src/orchestration/event-bus.js --test` — no regression
- [ ] `node src/idea/test-pipeline.js --test` — integration passes
- [ ] No `/* */` or `/** */` comments anywhere in new files
- [ ] Every new file has Marcus Daley file header
- [ ] Every function has // comment documentation
- [ ] All imports use ESM
- [ ] Git commit with descriptive message

---

## Dependency Graph

```
TASK 1.1 (storage) ────┬──► TASK 2.1 (ingestion) ──► TASK 3.1 (classifier) ──┐
                       │                                                      │
                       ├──► TASK 2.2 (scoring) ─────► TASK 3.2 (research) ────┤
                       │                                                      │
                       └──► TASK 4.1 (indexer) ◄──────────────────────────────┘
                                    │
TASK 1.2 (events)                   │
TASK 1.3 (LLM config)               │
TASK 1.4 (bridge spec)              ▼
TASK 1.5 (fixtures)         TASK 5.1 (facade)
                                    │
                                    ▼
                            TASK 5.2 (integration test)
                                    │
                                    ▼
                            TASK 5.3 (package.json)
                                    │
                                    ▼
                            TASK 5.4 (CLAUDE.md)
                                    │
                                    ▼
                            TASK 5.5 (final validation)
```

## Total Task Count

- Wave 1: 5 tasks (parallel)
- Wave 2: 2 tasks (parallel)
- Wave 3: 2 tasks (parallel)
- Wave 4: 1 task
- Wave 5: 5 tasks (sequential)

**Total: 15 tasks**

## Estimated Effort

- Wave 1: 2-3 hours (foundation)
- Wave 2: 2-3 hours (core engines)
- Wave 3: 2-3 hours (intelligence)
- Wave 4: 1-2 hours (indexing)
- Wave 5: 2-3 hours (integration)

**Total: 9-14 hours of focused implementation**

When parallelized with multi-agent team: ~4-6 hours wall clock
