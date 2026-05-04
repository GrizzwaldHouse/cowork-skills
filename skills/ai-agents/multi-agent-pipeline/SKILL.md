# Multi-Agent Pipeline Framework
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Production-grade event-driven multi-agent execution framework with quality gates, parallel execution, and self-improvement loops

---
name: multi-agent-pipeline
description: Production-grade, event-driven multi-agent execution framework that enforces strict quality gates, parallel execution, and multi-layer validation. Eliminates low-quality outputs through mandatory cross-review, supervisor validation, and automated self-improvement loops.
user-invocable: false
---

# Multi-Agent Pipeline Framework

> Event-driven orchestration framework for multi-agent systems with typed communication, quality scoring, and self-improvement loops

## Description

Provides a production-grade, event-driven multi-agent execution framework that enforces strict quality gates, parallel execution, and multi-layer validation. Eliminates low-quality outputs through mandatory cross-review, supervisor validation, and automated self-improvement loops. Designed for universal reuse across any project requiring orchestrated agent pipelines.

Built on the principle that no single agent should complete a task end-to-end without cross-validation. Every artifact passes through typed event communication, immutable data contracts, and configurable quality scoring before reaching production. Enforces Marcus's 95/5 Rule: 95% of code must be reusable across projects without modification.

## Prerequisites

- Python 3.10+
- PyQt6 (for GUI integration)
- dataclasses (stdlib)
- threading (stdlib)

## Usage

### 1. Define Agent Protocol Implementations

Any class implementing the Agent Protocol contract can participate in the pipeline:

```python
from scripts.agent_protocol import Agent
from scripts.agent_base import BaseAgent, AgentStatus

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MyAgent", agent_type="custom")

    def on_configure(self, config: dict) -> None:
        # Load configuration, lazy import dependencies
        pass

    def on_start(self) -> None:
        # Subscribe to events, start background threads
        self.event_bus.subscribe(SomeEvent, self.handle_event)

    def on_stop(self) -> None:
        # Clean up resources, unsubscribe
        self.event_bus.unsubscribe(SomeEvent, self.handle_event)

    def handle_event(self, event: SomeEvent) -> None:
        # Process event, emit new events
        result = self.process(event.data)
        self.event_bus.publish(ResultEvent(data=result))
```

### 2. Bootstrap Runtime

```python
from scripts.agent_runtime import AgentRuntime

runtime = AgentRuntime(config_path="config/agent_config.json")
runtime.bootstrap()  # Creates all agents from config
runtime.start()      # Starts all agents

# Inject external events
runtime.inject_event(FileChangeEvent(path="skills/new-skill/SKILL.md"))

# Graceful shutdown
runtime.stop()
```

### 3. Monitor Quality Scores

```python
from scripts.quality_scoring import QualityScorer

scorer = QualityScorer()
score_card = scorer.score_skill(skill_data)

print(f"Overall: {score_card.overall_score:.2f}")
print(f"Disposition: {score_card.disposition}")
print(f"Architecture: {score_card.dimension_scores['architecture']:.2f}")
print(f"Security: {score_card.dimension_scores['security']:.2f}")
```

### Prompt Pattern

```
Create an agent that processes [event type] and emits [result event type].
Follow the Agent Protocol pattern from multi-agent-pipeline skill.
Include lifecycle hooks, error handling, and event subscription cleanup.
```

## Core Philosophy

### No Direct Agent Communication

All agents communicate exclusively through the EventBus. No agent directly calls another agent's methods. This enforces loose coupling, enables parallel execution, and allows agents to be added/removed without modifying existing agents.

### Immutable Event Artifacts

All events are frozen dataclasses. Once emitted, they cannot be modified. Agents produce new events as outputs, never mutate inputs. This prevents race conditions and makes event flows traceable.

### Fail-Safe Handler Isolation

A failing event handler never blocks other handlers. The EventBus catches exceptions, logs them, and continues dispatching to remaining handlers. This prevents one bad agent from crashing the entire pipeline.

### Quality Over Velocity

Every artifact passes through multi-dimensional quality scoring before approval. Scores below threshold enter self-improvement loops with regression prevention. Failed improvements escalate to human review after max attempts.

## Architecture

### Core Components

#### 1. Agent Protocol (`agent_protocol.py`)

Structural typing via Python Protocol. Any class implementing these methods satisfies the contract:

- `name: str` — Unique identifier
- `agent_type: str` — Category (extractor, validator, refactor, sync, etc.)
- `status: AgentStatus` — Current lifecycle state
- `configure(config: dict) -> None` — Configure from external settings
- `start() -> None` — Begin operation
- `stop() -> None` — Graceful shutdown
- `pause() -> None` — Temporary suspension
- `resume() -> None` — Resume from pause
- `get_info() -> dict` — Status and metrics

No forced inheritance. Agents can implement the protocol through composition, inheritance from BaseAgent, or standalone implementation.

#### 2. BaseAgent (`agent_base.py`)

Optional composition helper with:

- **Validated State Machine**: UNINITIALIZED → CONFIGURED → RUNNING → PAUSED → STOPPED, plus ERROR
- **Thread-Safe Metrics**: Lock-protected counters for events processed, errors, successes
- **Lifecycle Hooks**: `on_configure()`, `on_start()`, `on_stop()`, `on_pause()`, `on_resume()`, `on_error()`
- **Event Bus Access**: Auto-injected during registration

Agents extending BaseAgent only need to implement lifecycle hooks, not the full protocol.

#### 3. EventBus (`agent_event_bus.py`)

Typed dispatch system:

- **Subscribe by Event Class**: `event_bus.subscribe(SkillExtractedEvent, handler)`
- **Publish Dispatches**: Exact-type + wildcard handlers receive events
- **Thread-Safe**: RLock protects subscriber registry
- **Bounded Audit Log**: Configurable capacity with automatic pruning
- **Isolated Handlers**: Handler exceptions are caught, logged, and isolated

#### 4. AgentRegistry (`agent_registry.py`)

Central registration and lifecycle management:

- `register(agent: Agent)` — Add agent to registry
- `start_all()` / `stop_all()` — Bulk lifecycle operations
- `get_by_type(agent_type: str)` — Query by category
- `get_by_status(status: AgentStatus)` — Query by lifecycle state
- `get_all_status()` — Snapshot of all agent states

Thread-safe with RLock protection.

#### 5. AgentRuntime (`agent_runtime.py`)

Top-level orchestrator:

- `bootstrap()` — Creates all agents from config, injects EventBus, registers agents
- `start()` / `stop()` — Delegates to AgentRegistry
- `inject_event(event)` — Bridge external systems into the event pipeline

### Pipeline Pattern

```
FileChangeEvent → ExtractorAgent → SkillExtractedEvent → ValidatorAgent → SkillValidatedEvent
                                                                              |
                   +----------------------------------------------------------+
                   |                        |                                 |
              [APPROVED]            [NEEDS_REFACTOR]                    [REJECTED]
                   |                        |                                 |
                   v                        v                             Logged
              SyncAgent              RefactorAgent
                   |                   |         |
                   v              [improved]  [failed]
           SkillSyncedEvent           |         |
                                      v      Logged + Cooldown
                              Re-enters ValidatorAgent
```

### Quality Scoring (5 Dimensions)

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| **Architecture** | 0.20 | No polling, no globals, no monolithic blocks, event-driven design |
| **Security** | 0.25 | No blocked patterns, no hardcoded credentials, path confinement |
| **Quality** | 0.15 | Execution logic depth, constraints, failure modes, confidence score |
| **Reusability** | 0.25 | 95/5 rule enforcement, no project-specific indicators, parameterized inputs |
| **Completeness** | 0.15 | All SKILL.md sections present and substantive |

Weights sum to 1.0. All scores clamped to [0.0, 1.0].

### Disposition Gates

| Disposition | Score Range | Action |
|------------|-------------|--------|
| **Approved** | >= 0.80 | Auto-install and sync |
| **Needs Refactor** | 0.50-0.79 | Enters self-improvement loop |
| **Needs Review** | 0.40-0.49 | Flagged for human review |
| **Rejected** | < 0.40 | Logged and discarded |

### Self-Improvement Loop

1. **Receive** SkillRefactorRequestedEvent → check cooldown
2. **Run** SkillImprover targeting quality threshold (Karpathy-style eval loop)
3. **Check Regression**: Score must not decrease from historical best
4. **If Improved**: Re-validate → if approved, install
5. **If Failed**: Enter cooldown, max 3 consecutive failures → escalate to needs_review (human)

### Multi-Agent Team Pattern (for Claude Code)

When orchestrating multiple Claude Code agent instances:

```
Researcher (read-only) → Implementers (parallel, write) → Reviewer (read-only, parallel)
                                                                    ↓
                                                          Supervisor (final gate) → APPROVED
```

- **Researcher**: Read-only access, gathers context, identifies patterns
- **Implementers**: Parallel write access, each handles separate files/modules
- **Reviewer**: Read-only, checks against coding standards and architecture
- **Supervisor**: Final quality gate, approves or requests refactoring

## Input Pattern

- `requirements: dict` — Task specification with success criteria
- `config: dict` — Agent configuration (weights, thresholds, cooldowns) from `agent_config.json`
- `event_bus: EventBus` — Shared typed event dispatch bus
- `agents: list[Agent]` — Agent instances satisfying the Agent Protocol

## Expected Output

- Fully orchestrated agent pipeline with typed event routing
- Quality reports with 5-dimension weighted scores and dispositions
- Improvement trend tracking with regression prevention
- Configurable cooldown and escalation for failed refactoring
- CLI (`--agents`) and GUI integration (status badges, refactor progress)

## Constraints

- All events MUST be frozen dataclasses (immutable artifacts)
- All communication MUST go through EventBus — no direct calls between agents
- Existing modules are WRAPPED via composition, never modified
- All thresholds and weights MUST be externalized to config (no magic numbers)
- Thread safety required on all shared state (Lock or RLock)
- Handler exceptions MUST be isolated — one failure never blocks others
- Quality scores MUST be clamped to [0.0, 1.0]
- Dimension weights MUST sum to 1.0
- Agent state transitions MUST follow validated state machine (no invalid transitions)
- Event handlers MUST clean up subscriptions in lifecycle teardown

## Failure Modes

| Failure | Handling |
|---------|----------|
| **Import failure** | Lazy imports in `on_configure()` handle missing dependencies gracefully |
| **Handler crash** | EventBus catches and logs exceptions, continues dispatching to other handlers |
| **Regression** | ImprovementTrendTracker blocks score decreases from historical best |
| **Rapid-fire refactoring** | RefactorCooldownTracker enforces configurable cooldown period |
| **Max failures** | After 3 consecutive failures, skill escalates to needs_review (human) |
| **Config missing** | All modules fall back to sensible defaults when config unavailable |
| **Invalid state transition** | BaseAgent validates state machine, logs error, transitions to ERROR state |
| **Event bus shutdown** | All agents receive stop signal, unsubscribe cleanly |

## Configuration

Configuration loaded from `config/agent_config.json`:

```json
{
    "quality_thresholds": {
        "approved": 0.80,
        "needs_refactor": 0.50,
        "needs_review": 0.40
    },
    "dimension_weights": {
        "architecture": 0.20,
        "security": 0.25,
        "quality": 0.15,
        "reusability": 0.25,
        "completeness": 0.15
    },
    "improvement_config": {
        "max_consecutive_failures": 3,
        "refactor_cooldown_seconds": 300,
        "regression_tolerance": 0.0
    },
    "event_bus_config": {
        "audit_log_capacity": 1000
    },
    "agents": {
        "extractor": {"enabled": true},
        "validator": {"enabled": true},
        "refactor": {"enabled": true},
        "sync": {"enabled": true}
    }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `quality_thresholds.approved` | 0.80 | Minimum score for auto-approval |
| `quality_thresholds.needs_refactor` | 0.50 | Minimum score to enter improvement loop |
| `quality_thresholds.needs_review` | 0.40 | Minimum score before rejection |
| `dimension_weights.*` | See above | Relative importance of each quality dimension (must sum to 1.0) |
| `improvement_config.max_consecutive_failures` | 3 | Max refactor attempts before human escalation |
| `improvement_config.refactor_cooldown_seconds` | 300 | Minimum time between refactor attempts |
| `improvement_config.regression_tolerance` | 0.0 | Maximum allowed score decrease from historical best |
| `event_bus_config.audit_log_capacity` | 1000 | Maximum audit log entries before pruning |

## File Structure

```
multi-agent-pipeline/
  SKILL.md                          # This skill definition
  metadata.json                     # Skill metadata and file registry
  README.md                         # Quick-start guide
  examples/
    custom_agent_example.py         # Example custom agent implementation
    pipeline_orchestration.py       # Example multi-agent pipeline setup
```

## Integration Points

### CLI Integration

```bash
python scripts/main.py --agents              # Show agent status
python scripts/main.py --agent-validate      # Run validation on all skills
python scripts/main.py --agent-improve       # Trigger improvement loop
```

### GUI Integration

- Status badges for each agent (RUNNING, STOPPED, ERROR)
- Quality score visualization with 5-dimension breakdown
- Refactor progress bar with cooldown timer
- Event flow diagram showing pipeline state

### External Systems

Inject events from external systems:

```python
# File watcher integration
watcher.on_change(lambda path: runtime.inject_event(FileChangeEvent(path=path)))

# GitHub webhook integration
@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    event = parse_github_event(request.json)
    runtime.inject_event(event)
    return '', 200
```

## Notes

- The Agent Protocol uses structural typing (Protocol) rather than abstract base classes, allowing agents to satisfy the contract through any means (composition, inheritance, standalone implementation).
- BaseAgent provides sensible defaults and lifecycle management but is optional — agents can implement the protocol directly.
- EventBus uses RLock rather than Lock to allow reentrant subscriptions (handler can publish new events during handling).
- Quality scoring weights are configurable to allow different projects to emphasize different quality dimensions.
- The self-improvement loop prevents regression by tracking historical best scores and rejecting improvements that decrease quality.
- Cooldown enforcement prevents rapid-fire refactoring attempts that consume resources without meaningful improvement.
- All agents are threaded — EventBus and AgentRegistry use thread-safe primitives (RLock) for shared state protection.
