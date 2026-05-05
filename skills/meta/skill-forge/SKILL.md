---
name: skill-forge
description: >
  Meta-skill that runs the full skill lifecycle in one command: create, eval, improve, and publish.
  Use when the user says "forge a skill", "create and improve a skill", "run the skill loop on X",
  "build and publish a skill", "skill-forge", or wants to go from idea to production-ready skill
  without manually chaining skill-creator and skill-self-improver. Also trigger when the user wants
  to combine or upgrade existing skills, write eval.json for a skill, or push skills to GitHub.
  Wraps skill-creator + skill-self-improver into one /skill-forge command.
user-invocable: true
argument-hint: "<skill-name-or-idea> [--eval-only] [--improve-only] [--no-publish]"
---

# Skill Forge

Runs the complete skill lifecycle: capture intent, write SKILL.md, create evals, run the
improvement loop, and publish to GrizzwaldHouse/cowork-skills. One command replaces the
manual chain of skill-creator + skill-self-improver + git push.

## Phase Overview

```
CAPTURE → DRAFT → EVAL → IMPROVE → GATE → PUBLISH
```

Each phase is idempotent. If a phase artifact already exists (SKILL.md, eval/eval.json,
eval/history.json), the forge picks up from the next incomplete phase rather than restarting.

## Phase 1: Capture Intent

Ask (or extract from context) these four questions before writing anything:

1. What should this skill enable Claude to do? (one sentence)
2. When should it trigger? List 3-5 specific user phrases or contexts.
3. What is the expected output? (format, length, structure)
4. Are there existing skills it should replace, combine with, or reference?

If the user has already answered these in the current conversation, extract them and skip
the questions. Move directly to Phase 2.

For combination requests ("merge X and Y"), read both source SKILL.md files before drafting.
Identify overlapping content (canonicalize in one place, reference from the other) and
conflicting instructions (resolve with the more specific skill winning).

## Phase 2: Draft SKILL.md

Follow the skill-creator structure:

- **name**: lowercase-hyphens
- **description**: Pushy trigger text -- Claude undertriggers, so be explicit. Cover all
  realistic phrasings a user would say when they need this skill.
- **body**: Instructions under 500 lines. Use reference files for deep content.

Place the file at: `C:\ClaudeSkills\skills\<category>\<name>\SKILL.md`

Category guidance:
- `meta/` -- skills that operate on the skill system itself
- `ai-agents/` -- agent orchestration, handoff, session management
- `_core/` -- doctrine applied universally (coding standards, workflow)
- `software-dev/` -- language/framework specific
- `qa-testing/` -- testing, build gates, visual regression
- `research/` -- research loops, brainstorming, analysis

After drafting, do a self-review pass:
- Trigger description covers at least 5 distinct phrasings
- No em-dashes anywhere (Marcus hard rule -- use commas, colons, or parentheses)
- Under 500 lines in SKILL.md body
- Deep content moved to references/ with clear load instructions

## Phase 3: Write Evals

Create `C:\ClaudeSkills\skills\<category>\<name>\eval\eval.json` with 3-5 test cases.

Each test case needs binary assertions (true/false statements about the expected output):

```json
{
  "skill_name": "<name>",
  "version": "1.0.0",
  "test_cases": [
    {
      "id": 1,
      "prompt": "A realistic prompt a real user would say",
      "assertions": [
        {
          "id": "trigger_fires",
          "check": "The skill activates and does not produce a generic response",
          "category": "compliance"
        },
        {
          "id": "output_format_correct",
          "check": "The output matches the expected structure defined in the skill",
          "category": "structure"
        },
        {
          "id": "no_em_dashes",
          "check": "The output contains no em-dashes (-- or —)",
          "category": "compliance"
        }
      ]
    }
  ]
}
```

Standard assertions to include on every skill:
- `no_em_dashes`: output contains no em-dashes
- `trigger_fires`: skill activates and does not produce generic filler
- `output_format_correct`: output matches the structure described in SKILL.md

Add skill-specific assertions for the behaviors that matter most.

## Phase 4: Run Improvement Loop

Run skill-self-improver on the new skill:

```bash
python C:\ClaudeSkills\scripts\main.py --self-improve <name> --max-iterations 10 --target-score 0.9
```

If `scripts/main.py` is unavailable, run a manual improvement cycle:
1. Execute each test prompt mentally against the current SKILL.md
2. Check each assertion -- pass or fail?
3. For each failing assertion, propose ONE targeted change to SKILL.md
4. Apply the change, re-check assertions
5. Repeat until score >= 0.9 or 10 iterations reached

Track changes in a scratch log so no change is proposed twice.

## Phase 5: Publish Gate

Before pushing to GitHub, all of these must be true:

- [ ] Eval pass rate >= 0.9 (9 of 10 assertions passing minimum)
- [ ] SKILL.md under 500 lines
- [ ] No em-dashes in any skill text
- [ ] Skill name unique in C:\ClaudeSkills\skills\ (grep to verify)
- [ ] At least one real-world invocation tested in this session

If `--no-publish` flag is set, stop here and report the gate results.

## Phase 6: Publish

```powershell
cd C:\ClaudeSkills
git add skills\<category>\<name>\
git commit -m "feat(<name>): add <one-line description>"
git push origin master
.\setup.ps1
```

After pushing, run setup.ps1 to sync the new skill to `~/.claude/skills/` so it is
immediately available in Claude Code.

Report: skill name, category path, eval pass rate, and the git commit hash.

## Flags

| Flag | Effect |
|------|--------|
| `--eval-only` | Skip drafting, run evals on existing SKILL.md only |
| `--improve-only` | Skip drafting and evals, run improvement loop on existing skill |
| `--no-publish` | Stop after the gate check, do not push to GitHub |
| `--from=<phase>` | Jump to a specific phase (capture, draft, eval, improve, gate, publish) |

## AgenticOS Integration

After each phase completes, broadcast to the AgenticOS event bus if available:

```python
# Fire-and-forget, never block on this
from scripts.agenticos_push import push_event, EventType
push_event(EventType.PHASE_COMPLETE, workflow_id="skill-forge", extra={"phase": "draft", "skill": name})
```

If the push script is unavailable, skip silently -- AgenticOS integration is never on the
critical path.

## Cross-References

- `meta/skill-creator`: The underlying create-and-eval methodology this skill automates
- `meta/skill-self-improver`: The Karpathy-style improvement loop this skill drives
- `_core/universal-coding-standards`: Coding rules that apply to any skill's generated content
- `brainstorm-artifact`: Use before skill-forge when the skill's purpose is not yet clear
