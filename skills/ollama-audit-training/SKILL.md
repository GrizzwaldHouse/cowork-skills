---
name: ollama-audit-training
description: Analyze, benchmark, auto-select, optimize, and track local Ollama models. Includes behavior audit, multi-model benchmarking, task-based auto-selection, speed/quality optimization, and historical scoring dashboard.
user-invocable: true
---

# Ollama Agent Audit & Training System

Analyze, evaluate, and continuously improve local Ollama AI models. Extends into benchmarking, auto-selection, optimization, and historical tracking.

---

## WHEN TO USE

Trigger this skill when:

- A local Ollama model is detected or configured
- Model outputs are inconsistent or low quality
- Before production deployment of any LLM-driven feature
- After major system updates or new model installs
- During performance or behavior testing
- User asks to compare models or optimize LLM selection
- Task routing config needs tuning (llm-providers.yaml)

---

## PART 1: CORE AUDIT SYSTEM

### 1.1 Model Detection

Query Ollama for active models and capture metadata.

```javascript
// Detection via Ollama API
const response = await fetch('http://127.0.0.1:11434/api/tags');
const { models } = await response.json();

// Extract per model:
// - name, size, parameter_count, quantization, modified_date
// - family (llama, qwen, glm, etc.)
// - capabilities (chat, code, embedding, vision)
```

**Current Local Models (detected 2026-04-05):**

| Model | Size | Family | Best For |
|-------|------|--------|----------|
| llama3.3:70b | 42 GB | Llama 3.3 | Complex reasoning, code review, analysis |
| glm-4.7-flash:latest | 19 GB | GLM-4 | Fast general tasks, Chinese/English |
| llama3:8b | 4.7 GB | Llama 3 | Quick responses, autocomplete, drafts |

### 1.2 Behavior Analysis

Evaluate model output on five dimensions:

| Dimension | Method | Weight |
|-----------|--------|--------|
| Accuracy | Compare output to expected/reference answer | 30% |
| Code Quality | Lint check, standards validation, pattern match | 25% |
| Consistency | Run same prompt 3x, measure variance | 20% |
| Logical Reasoning | Multi-step problem solving, chain-of-thought | 15% |
| Response Structure | JSON validity, markdown formatting, section headers | 10% |

### 1.3 Error Classification

Categorize every failure:

| Category | Detection Method | Severity |
|----------|-----------------|----------|
| Logic Error | Output contradicts input constraints | HIGH |
| Hallucination | Claims unsupported by input context | CRITICAL |
| Poor Structure | Missing headers, broken JSON, no code blocks | MEDIUM |
| Standards Violation | Magic numbers, global state, missing types | HIGH |
| Inefficient Solution | O(n^2) when O(n) exists, redundant operations | LOW |
| Incomplete Output | Truncated response, missing required sections | MEDIUM |

### 1.4 Coding Standard Validation

Check output against Marcus's universal coding standards:

```
[x] No magic numbers — named constants only
[x] Dependency injection — no hardcoded dependencies
[x] Separation of concerns — single responsibility per function/module
[x] No global mutable state
[x] Typed error handling — no catch-all swallows
[x] Clear function purpose — name describes exactly what it does
[x] ES Modules only (import/export, never require)
[x] Input validation at system boundaries
[x] Observer/delegate pattern for decoupling
[x] No ConstructorHelpers (UE5)
[x] No EditAnywhere without reason (UE5)
```

### 1.5 Performance Scoring

```json
{
  "model": "llama3.3:70b",
  "task": "code_review",
  "scores": {
    "accuracy": 85,
    "code_quality": 78,
    "consistency": 92,
    "reasoning": 80,
    "structure": 88,
    "overall": 84
  },
  "timestamp": "2026-04-05T10:00:00Z",
  "tokens_used": 1247,
  "latency_ms": 3200
}
```

Scoring formula:
```
overall = (accuracy * 0.30) + (code_quality * 0.25) + (consistency * 0.20)
        + (reasoning * 0.15) + (structure * 0.10)
```

### 1.6 Training Adjustments

When a model scores below threshold (< 70 overall):

1. **Prompt refinements** — Add explicit constraints, examples, output format
2. **System prompt hardening** — Inject coding standards into system message
3. **Few-shot injection** — Add 1-2 correct examples before the task
4. **Temperature tuning** — Lower temp for code (0.1-0.3), moderate for creative (0.5-0.7)
5. **Chain-of-thought** — Force step-by-step reasoning with "Think through this step by step"

### 1.7 Safety Rules

Models MUST NOT:
- Modify critical system files (SYSTEM_PROMPT.md, .env, .gitconfig)
- Bypass validation gates
- Execute shell commands without confirmation
- Generate code that disables error handling
- Produce outputs that skip test requirements

Every model output MUST pass through:
1. Validation step (schema/format check)
2. Standards check (coding standards)
3. Safety check (no dangerous operations)

---

## PART 2: BENCHMARK SYSTEM

Compare multiple models on identical tasks to find the best performer per task type.

### 2.1 Benchmark Suite

Standard test prompts covering all task types from llm-providers.yaml:

| Benchmark ID | Task Type | Prompt Template | Expected Output Format |
|-------------|-----------|-----------------|----------------------|
| BM-001 | morning_brief | "Generate a morning brief for a freelance developer..." | Markdown with sections |
| BM-002 | code_review | "Review this JavaScript function for quality..." | Structured feedback with line references |
| BM-003 | email_parsing | "Extract order details from this Fiverr email..." | JSON with fields: client, project, deadline, budget |
| BM-004 | pr_analysis | "Analyze this pull request diff..." | Risk assessment, suggestions, approval/reject |
| BM-005 | complex_reasoning | "Design an architecture for a plugin marketplace..." | Component diagram, tradeoffs, recommendation |
| BM-006 | client_communication | "Draft a professional response to this client..." | Email body, tone-appropriate, actionable |
| BM-007 | autocomplete | "Complete this function: function calculateScore(..." | Valid code, correct logic, typed |
| BM-008 | coding_standards | "Refactor this code to follow clean architecture..." | Compliant code with no violations |

### 2.2 Benchmark Execution Flow

```
For each benchmark in suite:
  For each model in [llama3.3:70b, glm-4.7-flash, llama3:8b]:
    Run prompt 3 times (consistency check)
    Measure:
      - latency_ms (time to first token, total time)
      - tokens_per_second
      - output_quality (scored 0-100 per Part 1 rubric)
      - token_count (input + output)
      - memory_usage_gb (via ollama ps)
    Average scores across 3 runs
  Rank models per benchmark
  Record to benchmark-results.json
```

### 2.3 Benchmark Results Format

```json
{
  "benchmark_id": "BM-002",
  "task_type": "code_review",
  "date": "2026-04-05",
  "results": [
    {
      "model": "llama3.3:70b",
      "avg_score": 84,
      "avg_latency_ms": 3200,
      "tokens_per_second": 18.5,
      "consistency": 92,
      "rank": 1
    },
    {
      "model": "glm-4.7-flash",
      "avg_score": 71,
      "avg_latency_ms": 1400,
      "tokens_per_second": 42.0,
      "consistency": 85,
      "rank": 2
    },
    {
      "model": "llama3:8b",
      "avg_score": 58,
      "avg_latency_ms": 450,
      "tokens_per_second": 95.0,
      "consistency": 78,
      "rank": 3
    }
  ],
  "recommendation": "llama3.3:70b for quality, glm-4.7-flash for speed/quality balance"
}
```

### 2.4 Cloud Provider Benchmarks

Extend benchmarks to include cloud providers for comparison:

| Provider | Model | Cost/1k Tokens | Included |
|----------|-------|---------------|----------|
| Groq | llama-3.3-70b-versatile | $0 | Yes |
| Cerebras | llama-3.3-70b | $0 | Yes |
| Together | Llama-3.3-70B-Instruct-Turbo | $0.0008 | Yes (within free credit) |
| Mistral | mistral-small-latest | $0 | Yes |
| Local | llama3.3:70b | $0 | Yes |
| Local | glm-4.7-flash | $0 | Yes |
| Local | llama3:8b | $0 | Yes |

This produces a **local vs cloud comparison** showing when local models are good enough vs when cloud is worth the latency tradeoff.

---

## PART 3: AUTO MODEL SELECTOR

Automatically choose the best model for each task based on benchmark data and runtime conditions.

### 3.1 Selection Algorithm

```
function selectModel(taskType, constraints):
  candidates = getModelsForTask(taskType)  // from benchmark rankings

  // Filter by constraints
  if constraints.maxLatencyMs:
    candidates = candidates.filter(m => m.avg_latency_ms <= constraints.maxLatencyMs)

  if constraints.minQuality:
    candidates = candidates.filter(m => m.avg_score >= constraints.minQuality)

  if constraints.localOnly:
    candidates = candidates.filter(m => m.provider === 'ollama')

  if constraints.freeOnly:
    candidates = candidates.filter(m => m.cost_per_1k === 0)

  // Score remaining candidates
  for each candidate:
    candidate.selection_score = calculateSelectionScore(candidate, constraints.priority)

  return candidates.sortBy(selection_score).first()
```

### 3.2 Selection Score Formula

```
// priority = "quality" | "speed" | "balanced" | "cost"

if priority === "quality":
  score = (quality * 0.60) + (consistency * 0.25) + (speed * 0.10) + (cost * 0.05)

if priority === "speed":
  score = (speed * 0.50) + (quality * 0.25) + (cost * 0.15) + (consistency * 0.10)

if priority === "balanced":
  score = (quality * 0.35) + (speed * 0.30) + (consistency * 0.20) + (cost * 0.15)

if priority === "cost":
  score = (cost * 0.50) + (quality * 0.25) + (speed * 0.15) + (consistency * 0.10)
```

### 3.3 Task-to-Model Mapping (Auto-Generated)

Updated automatically after each benchmark run:

```yaml
# auto-model-routing.yaml (generated from benchmark results)
task_routing:
  morning_brief:
    primary: groq:llama-3.3-70b-versatile    # Fast + free + good quality
    local_fallback: llama3.3:70b              # Offline capable
    fast_fallback: llama3:8b                  # When speed matters most

  code_review:
    primary: ollama:llama3.3:70b              # Best quality for code
    cloud_fallback: together:code             # If local unavailable
    fast_fallback: glm-4.7-flash              # Quick scan

  email_parsing:
    primary: groq:fast                        # Simple extraction, speed wins
    local_fallback: llama3:8b                 # Lightweight local
    fast_fallback: llama3:8b

  autocomplete:
    primary: ollama:llama3:8b                 # Ultra-fast, local only
    local_fallback: glm-4.7-flash             # Still fast
    fast_fallback: null                       # No cloud for autocomplete

  complex_reasoning:
    primary: ollama:llama3.3:70b              # Heavyweight local
    cloud_fallback: claude:balanced           # When local can't handle it
    fast_fallback: null                       # Never compromise on complex tasks
```

### 3.4 Runtime Adaptation

The auto-selector adapts in real-time:

- **Ollama down?** → Route to cloud providers automatically
- **Rate limited on Groq?** → Switch to Cerebras or local
- **Budget approaching limit?** → Prefer local/free only
- **High-quality task?** → Force quality-priority selection
- **User waiting interactively?** → Force speed-priority selection

### 3.5 Integration with Existing LLM Client

Extends `UniversalLLMClient` in Bob-AICompanion:

```javascript
// In llm-client.js, add auto-selection method:

async chatSmart(messages, options = {}) {
  const taskType = options.task || 'default';
  const constraints = {
    maxLatencyMs: options.maxLatency || null,
    minQuality: options.minQuality || 60,
    localOnly: options.localOnly || false,
    freeOnly: options.freeOnly || true,
    priority: options.priority || 'balanced'  // quality|speed|balanced|cost
  };

  const selectedModel = this.autoSelector.select(taskType, constraints);

  // Override routing with auto-selected model
  return this.chat(messages, {
    ...options,
    task: taskType,
    forcedProvider: selectedModel.provider,
    forcedModel: selectedModel.model
  });
}
```

---

## PART 4: PERFORMANCE OPTIMIZER

Tune the speed vs quality tradeoff per task.

### 4.1 Optimization Dimensions

| Dimension | Speed Lever | Quality Lever |
|-----------|------------|---------------|
| Model Size | Smaller (8B) = faster | Larger (70B) = better |
| Temperature | Lower (0.1) = more deterministic | Higher (0.5) = more creative |
| Max Tokens | Fewer = faster response | More = complete answers |
| System Prompt | Shorter = less processing | Longer = better guidance |
| Context Window | Less context = faster | More context = better answers |
| Quantization | Q4 = faster, less memory | Q8/FP16 = higher quality |
| Batch Size | Smaller = lower latency | Larger = higher throughput |

### 4.2 Optimization Profiles

```yaml
profiles:
  ultra_fast:
    description: "Autocomplete, quick drafts, simple extraction"
    model_preference: smallest_available    # llama3:8b
    temperature: 0.1
    max_tokens: 256
    system_prompt: minimal                  # < 200 tokens
    target_latency_ms: 500
    min_quality: 50

  fast:
    description: "Email parsing, simple summaries, notifications"
    model_preference: medium_available      # glm-4.7-flash
    temperature: 0.3
    max_tokens: 1024
    system_prompt: standard                 # < 500 tokens
    target_latency_ms: 2000
    min_quality: 65

  balanced:
    description: "Morning briefs, client comms, documentation"
    model_preference: best_available        # llama3.3:70b or groq
    temperature: 0.5
    max_tokens: 2048
    system_prompt: full                     # with coding standards
    target_latency_ms: 5000
    min_quality: 75

  quality:
    description: "Code review, PR analysis, architecture decisions"
    model_preference: best_available
    temperature: 0.2
    max_tokens: 4096
    system_prompt: full_with_examples       # standards + few-shot
    target_latency_ms: 15000
    min_quality: 85

  max_quality:
    description: "Complex reasoning, business strategy, critical decisions"
    model_preference: best_available_or_cloud  # local 70B or Claude
    temperature: 0.1
    max_tokens: 8192
    system_prompt: full_with_chain_of_thought
    target_latency_ms: 60000
    min_quality: 90
```

### 4.3 Adaptive Optimization

Monitor real-time performance and adapt:

```
After each LLM call:
  Record: model, task_type, latency_ms, quality_score, token_count

  If latency > target for profile:
    → Try smaller model next time
    → Reduce max_tokens
    → Shorten system prompt

  If quality < min for profile:
    → Try larger model next time
    → Add few-shot examples
    → Lower temperature
    → Increase max_tokens

  If both latency AND quality are good:
    → Current config is optimal, no changes
```

### 4.4 Ollama-Specific Optimizations

```bash
# Keep models loaded in memory (avoid cold start)
ollama run llama3.3:70b --keepalive 30m

# Monitor GPU/CPU utilization
ollama ps

# Parallel requests (if GPU memory allows)
# Only possible with smaller models on consumer hardware

# Quantization tradeoffs:
# Q4_K_M: 50% size reduction, ~5% quality loss — good for llama3:8b
# Q5_K_M: 40% size reduction, ~2% quality loss — good for daily use
# Q8_0:   minimal quality loss, larger size — good for critical tasks
```

---

## PART 5: AI DASHBOARD (Historical Scoring)

Track model performance over time to identify trends, regressions, and improvements.

### 5.1 Data Schema

```json
{
  "dashboard_version": "1.0",
  "data_points": [
    {
      "date": "2026-04-05",
      "model": "llama3.3:70b",
      "task_type": "code_review",
      "runs": 3,
      "avg_score": 84,
      "avg_latency_ms": 3200,
      "tokens_per_second": 18.5,
      "errors": 0,
      "scores": {
        "accuracy": 85,
        "code_quality": 78,
        "consistency": 92,
        "reasoning": 80,
        "structure": 88
      }
    }
  ]
}
```

### 5.2 Dashboard Storage

```
C:\Users\daley\Projects\Bob-AICompanion\
  data/
    ollama-benchmarks/
      benchmark-results.json       # Latest benchmark run
      benchmark-history.json       # All historical runs
      model-rankings.json          # Current model-per-task rankings
      auto-model-routing.yaml      # Generated routing config
      optimization-profiles.yaml   # Performance profiles
      dashboard-data.json          # Dashboard visualization data
```

### 5.3 Dashboard Metrics (Per Model, Per Task Type, Over Time)

**Trend Tracking:**
- Quality score trend (7-day, 30-day moving averages)
- Latency trend (detect degradation)
- Error rate trend (detect regressions)
- Cost per task trend (for cloud providers)
- Tokens-per-second trend (hardware utilization)

**Alerts:**
- Quality drops > 10 points from 7-day average → WARNING
- Latency increases > 50% from baseline → WARNING
- Error rate exceeds 5% → CRITICAL
- New model available that benchmarks higher → INFO
- Budget approaching daily limit → WARNING

### 5.4 Dashboard Output Format (Markdown for Discord)

```markdown
## AI Model Performance — 2026-04-05

### Model Rankings (by overall score)
| Rank | Model | Overall | Speed | Quality | Cost |
|------|-------|---------|-------|---------|------|
| 1 | llama3.3:70b | 84 | 18 tok/s | 85 | $0 |
| 2 | groq:llama-3.3-70b | 82 | 120 tok/s | 83 | $0 |
| 3 | glm-4.7-flash | 71 | 42 tok/s | 72 | $0 |
| 4 | llama3:8b | 58 | 95 tok/s | 56 | $0 |

### Task Winners
| Task | Best Model | Score | Latency |
|------|-----------|-------|---------|
| code_review | llama3.3:70b | 84 | 3.2s |
| morning_brief | groq | 82 | 0.8s |
| email_parsing | llama3:8b | 72 | 0.4s |
| autocomplete | llama3:8b | 65 | 0.2s |

### Trends (7-day)
- llama3.3:70b quality: 84 → stable
- glm-4.7-flash quality: 71 → improving (+3)
- Daily LLM cost: $0.12 avg (budget: $1.00)

### Alerts
- None
```

### 5.5 Integration with Morning Brief

Add dashboard summary to Bob-AICompanion's morning brief:

```javascript
// In morning-brief.js workflow, add section:
const dashboardSummary = await generateDashboardSummary();
briefSections.push({
  title: 'AI Model Health',
  content: dashboardSummary,
  priority: 'low'  // Only include if space allows
});
```

---

## AGENT INTEGRATION

| Agent | Role in This Skill |
|-------|-------------------|
| AuditAgent | Runs Part 1 evaluation on model outputs |
| BenchmarkAgent | Runs Part 2 benchmark suite across models |
| SelectorAgent | Runs Part 3 auto-selection logic |
| OptimizerAgent | Runs Part 4 performance tuning |
| DashboardAgent | Runs Part 5 data collection and reporting |
| TestAgent | Validates improvements after adjustments |
| LearningAgent | Logs all findings to LEARNING.md |
| TokenMonitorAgent | Monitors benchmark token usage, prevents overrun |

---

## AUTOMATION SCHEDULE

| Trigger | What Runs |
|---------|-----------|
| New model installed (ollama pull) | Full benchmark suite (Part 2) |
| After every major task completion | Quick audit of outputs (Part 1) |
| Daily (6 AM PST with morning brief) | Dashboard update (Part 5) |
| Weekly (Sunday) | Full benchmark + optimization review (Parts 2-4) |
| Quality drops below threshold | Emergency audit + training adjustments (Parts 1, 4) |
| Budget approaching limit | Re-optimize for cost priority (Part 4) |

---

## SELF-IMPROVEMENT LOOP

```
1. Benchmark all models (Part 2)
2. Generate auto-routing config (Part 3)
3. Apply optimization profiles (Part 4)
4. Run tasks for one cycle
5. Audit outputs (Part 1)
6. Update dashboard with results (Part 5)
7. Compare to previous cycle
8. If regression: adjust prompts, temperature, model selection
9. If improvement: lock in current config
10. Log everything to LEARNING.md
11. Repeat
```

---

## FILES PRODUCED

| File | Purpose | Location |
|------|---------|----------|
| benchmark-results.json | Latest benchmark data | Bob-AICompanion/data/ollama-benchmarks/ |
| benchmark-history.json | Historical benchmark data | Bob-AICompanion/data/ollama-benchmarks/ |
| model-rankings.json | Best model per task | Bob-AICompanion/data/ollama-benchmarks/ |
| auto-model-routing.yaml | Generated routing config | Bob-AICompanion/data/ollama-benchmarks/ |
| optimization-profiles.yaml | Performance tuning profiles | Bob-AICompanion/data/ollama-benchmarks/ |
| dashboard-data.json | Dashboard visualization | Bob-AICompanion/data/ollama-benchmarks/ |
| LEARNING.md | All findings and patterns | SeniorDevBuddy/grizz_modular_system/ |

---

## SUCCESS CRITERIA

- Models produce consistent outputs (consistency > 85)
- Code follows system standards (code_quality > 75)
- Error rate decreases over time (< 5%)
- Performance score improves per cycle
- Auto-selector picks optimal model 90%+ of the time
- Daily LLM cost stays under $1.00
- Dashboard shows clear improvement trends
- Zero regressions go undetected
