---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

## Core Loop

1. Decide what you want the skill to do and roughly how it should do it
2. Write a draft of the skill
3. Create test prompts and run them
4. Evaluate results qualitatively and quantitatively
5. Rewrite the skill based on feedback
6. Repeat until satisfied
7. Expand the test set and try again at larger scale

## Creating a Skill

### Capture Intent

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works?

### Write the SKILL.md

- **name**: Skill identifier (lowercase, hyphens for spaces)
- **description**: When to trigger + what it does. Make descriptions "pushy" -- Claude tends to undertrigger skills, so be explicit about when to use them
- **the rest of the skill**: Instructions Claude follows when the skill activates

### Skill Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions (<500 lines ideal)
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

Keep SKILL.md under 500 lines; if approaching this limit, add reference files with clear pointers.

### Writing Patterns

**Defining output formats:**
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern:**
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Writing Style

- Explain WHY things are important rather than heavy-handed MUSTs
- Use theory of mind -- make the skill general, not narrow to specific examples
- Write a draft, then look at it with fresh eyes and improve it
- Prefer imperative form in instructions

## Evaluating Skills

### Test Cases

Create 2-3 realistic test prompts -- the kind of thing a real user would actually say. Save to `evals/evals.json`:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

### Improvement Guidelines

1. **Generalize from feedback**: Don't overfit to test examples. Skills will be used across many prompts.
2. **Keep the prompt lean**: Remove things that aren't pulling their weight.
3. **Explain the why**: LLMs are smart -- explaining reasoning is more effective than rigid rules.
4. **Look for repeated work**: If all test runs independently wrote similar helper scripts, bundle that script.
5. **Simplicity criterion**: A 0.001 improvement that adds 20 lines of complexity? Probably not worth it.

## Description Optimization

The description field is the primary triggering mechanism. To optimize:

### Generate Trigger Eval Queries

Create 20 eval queries -- mix of should-trigger and should-not-trigger. Make them realistic with file paths, personal context, casual speech.

**Good queries**: Specific, realistic, with context
**Bad queries**: Abstract, generic, obvious

### Test and Iterate

Run queries against the skill description, measure trigger accuracy, iterate on the description to improve precision and recall.

## Skill Quality Checklist

- [ ] Clear, descriptive name (lowercase-hyphens)
- [ ] Pushy description covering all trigger scenarios
- [ ] Instructions under 500 lines
- [ ] Examples included for complex outputs
- [ ] Reference files for deep knowledge
- [ ] Test cases covering edge cases
- [ ] No malware, exploits, or misleading content
