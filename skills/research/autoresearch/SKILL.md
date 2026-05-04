---
name: autoresearch
description: "Autonomous research and experimentation skill inspired by Karpathy's autoresearch. Use when the user wants to run autonomous experiments, iterate on code/models overnight, benchmark configurations, or set up a self-improving experiment loop. Trigger when the user mentions 'autoresearch', 'autonomous experiments', 'overnight research', 'experiment loop', 'benchmark iterations', or wants an agent to try multiple approaches and keep what works."
---

# AutoResearch - Autonomous Experiment Loop

Based on Karpathy's autoresearch pattern: give an AI agent a task, let it experiment autonomously, keep what works, discard what doesn't, and iterate indefinitely.

## Core Concept

The agent modifies code, runs experiments with fixed time/resource budgets, evaluates results against a ground truth metric, and advances or reverts based on improvement. The human sleeps while the agent works.

## Setup Phase

Before starting the experiment loop, work with the user to establish:

1. **Run Tag**: Propose a tag based on today's date (e.g., `apr14`). Create branch `autoresearch/<tag>`.
2. **Editable Scope**: Identify which files the agent CAN modify vs. which are immutable.
3. **Metric**: Define the ground truth evaluation metric (lower/higher is better).
4. **Time Budget**: Fixed duration per experiment (default: 5 minutes).
5. **Results Log**: Initialize `results.tsv` with header row.
6. **Baseline**: Run the first experiment with no changes to establish baseline.

## The Experiment Loop

```
LOOP FOREVER:
1. Review current state (git branch, results.tsv history)
2. Generate an experimental idea
3. Implement the change in editable file(s)
4. git commit with descriptive message
5. Run experiment: redirect all output to run.log
6. Extract results: grep key metrics from run.log
7. If crashed: read tail of log, attempt fix or skip
8. Log results to results.tsv
9. If improved: KEEP (advance branch)
10. If equal/worse: DISCARD (git reset to previous commit)
11. NEVER STOP - continue until manually interrupted
```

## Results Logging

Tab-separated `results.tsv` (NOT comma-separated):

```
commit	metric	memory_gb	status	description
a1b2c3d	0.997900	44.0	keep	baseline
b2c3d4e	0.993200	44.2	keep	increase learning rate
c3d4e5f	1.005000	44.0	discard	switch activation function
d4e5f6g	0.000000	0.0	crash	doubled model width (OOM)
```

Status values: `keep`, `discard`, `crash`

## Decision Rules

### Keep Changes When
- Metric improves (even slightly, if code stays clean)
- Same metric but simpler code (simplification win)
- Metric improves with reasonable resource increase

### Discard Changes When
- Metric worsens or stays the same with added complexity
- Small improvement but ugly/complex code added
- Resource usage explodes for marginal gain

### Simplicity Criterion
All else being equal, simpler is better:
- 0.001 improvement + 20 lines of hacky code = probably not worth it
- 0.001 improvement from deleting code = definitely keep
- Same metric + much simpler code = keep

## Crash Handling

- **Trivial fix** (typo, missing import): Fix and re-run
- **Fundamental issue** (architecture broken): Log as crash, revert, move on
- **Timeout** (exceeds 2x time budget): Kill and treat as failure

## Autonomy Rules

- NEVER pause to ask "should I keep going?"
- The user may be asleep or away
- If stuck, think harder: re-read code, try combining near-misses, try radical changes
- Run indefinitely until manually stopped
- At ~5 min per experiment: ~12/hour, ~100 per 8-hour sleep cycle

## Adapting to Different Domains

This pattern applies beyond ML training:

### Software Optimization
- **Editable**: Algorithm implementation, configuration
- **Metric**: Execution time, memory usage, test pass rate
- **Budget**: Time to run benchmark suite

### Game Development
- **Editable**: Game parameters, AI behavior, rendering settings
- **Metric**: FPS, load time, AI win rate, visual quality score
- **Budget**: Time to run simulation/benchmark

### Prompt Engineering
- **Editable**: Prompt templates, system instructions
- **Metric**: Eval score, accuracy, response quality rating
- **Budget**: API calls per iteration

### Configuration Tuning
- **Editable**: Config files, environment variables
- **Metric**: Application-specific KPI
- **Budget**: Time to run integration tests

## File Organization

```
project/
├── program.md          # Agent instructions (human-editable only)
├── editable_file.py    # Agent modifies this
├── eval_harness.py     # Immutable evaluation
├── results.tsv         # Experiment log (untracked by git)
└── run.log             # Latest experiment output (overwritten each run)
```
