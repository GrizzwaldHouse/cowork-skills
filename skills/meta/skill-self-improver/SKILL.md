---
name: skill-self-improver
description: >
  Launch and manage autonomous skill self-improvement loops using binary assertions
  and Karpathy-style eval-modify-test cycles. Use when the user says "improve skill",
  "self-improve", "run eval loop", "optimize skill", or invokes /skill-self-improver.
user-invocable: true
argument-hint: "[skill-name] [--max-iterations N] [--target-score F] [--eval-only]"
---

# Skill Self-Improver

> Autonomous Karpathy-style eval-modify-test loop for improving Claude Code skill
> output quality through binary assertion grading.

## Description

Runs an automated improvement cycle on any skill that has an `eval/eval.json` file.
The loop reads the skill's SKILL.md, executes test prompts, grades output against
binary true/false assertions, and if failures exist, proposes targeted edits to
SKILL.md. Changes that improve the pass rate are kept (committed to a git branch);
changes that don't are reverted. The loop continues until perfect score or the
iteration limit is reached.

Inspired by Andrej Karpathy's auto-research loop pattern.

## Prerequisites

- Python 3.10+
- `claude` CLI available on PATH (for `claude -p` subprocess calls)
- Git repository initialized at C:/ClaudeSkills
- Target skill must have `eval/eval.json` with binary assertions

## Usage

### From CLI

```bash
# Run eval only (no modifications)
python scripts/main.py --eval canva-designer

# Start self-improvement loop (default: max 50 iterations, target 1.0)
python scripts/main.py --self-improve canva-designer

# Custom limits
python scripts/main.py --self-improve canva-designer --max-iterations 10 --target-score 0.9
```

### From Claude Code

```
/skill-self-improver canva-designer
/skill-self-improver desktop-ui-designer --eval-only
/skill-self-improver python-code-reviewer --max-iterations 20
```

## How It Works

### Layer 1 vs Layer 2

- **Layer 1** (Anthropic's built-in): Improves skill description and trigger matching
- **Layer 2** (this system): Improves skill output quality via binary assertion testing

### The Loop

1. Create git branch: `skill-improve/<skill-name>-<timestamp>`
2. Run baseline eval against all test cases and assertions
3. For each iteration:
   a. Analyze which assertions failed and why
   b. Ask Claude to propose ONE targeted change to SKILL.md
   c. Apply the change (atomic write with backup)
   d. Re-run eval
   e. If score improved: commit the change, continue
   f. If score did not improve: revert via git checkout, log the failed attempt
4. Stop when: perfect score, max iterations reached, or manual interrupt (Ctrl+C)
5. Print summary: baseline score, final score, iterations, time elapsed

### Safety Mechanisms

- All changes happen on a dedicated git branch (never on master)
- Original SKILL.md is backed up before first modification
- Failed changes are immediately reverted via git checkout
- Max iteration cap prevents infinite loops
- Consecutive failure limit triggers strategy change after 5 failed attempts
- Full audit trail in `eval/history.json`
- Graceful Ctrl+C handling: commits/reverts cleanly, writes summary

## eval.json Schema

Each skill's `eval/eval.json` defines test cases with binary assertions:

```json
{
  "skill_name": "example-skill",
  "version": "1.0.0",
  "test_cases": [
    {
      "id": 1,
      "prompt": "The prompt to test against the skill",
      "assertions": [
        {
          "id": "unique_assertion_id",
          "check": "A statement that is TRUE or FALSE about the output",
          "category": "structure | content | quality | format | compliance"
        }
      ]
    }
  ]
}
```

### Assertion Categories

| Category | What It Checks |
|----------|---------------|
| structure | Output organization, sections, hierarchy |
| content | Required information present |
| quality | No vague language, no placeholders, specificity |
| format | Correct formatting, dimensions, units |
| compliance | Follows skill rules and conventions |

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_iterations | 50 | Maximum improvement iterations before stopping |
| target_score | 1.0 | Pass rate to stop at (0.0 to 1.0) |
| eval_only | false | Run evaluation without modification loop |
| eval_timeout | 120s | Timeout per test case execution |
| grader_timeout | 30s | Timeout per assertion grading call |
| max_consecutive_failures | 5 | Failed attempts before trying different strategy |

## Output Files

| File | Location | Purpose |
|------|----------|---------|
| Run results | `eval/results/run-<timestamp>.json` | Full grading results per eval run |
| History | `eval/history.json` | Iteration-by-iteration audit trail |
| Logs | `logs/` | Detailed execution logs |

## Notes

- The self-improvement loop runs autonomously and does not ask for permission during iterations
- Each proposed change targets exactly ONE failing assertion to isolate impact
- Failed attempts are tracked so the same change is never proposed twice
- The grader uses a separate `claude -p` call with a strict binary TRUE/FALSE prompt
- On Windows, subprocess calls remove the CLAUDECODE env var for safe nesting
