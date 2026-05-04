---
name: prompt-engineering
description: "Design, test, evaluate, and optimize prompts for LLMs. Use when the user wants to write better prompts, test prompt quality, benchmark prompts across models, create evaluation suites, or mentions promptfoo, prompt testing, prompt optimization, few-shot examples, chain-of-thought, or systematic prompt improvement. Also trigger for 'help me write a prompt', 'evaluate this prompt', 'why is this prompt not working', or A/B testing prompts."
---

# Prompt Engineering Skill

Design effective prompts, test them systematically, and iterate based on evidence.

## Prompt Design Patterns

### Role / Persona Prompting
Assign a specific expert role to focus the model's knowledge:
```
You are a senior security engineer reviewing code for vulnerabilities.
Focus on: SQL injection, XSS, CSRF, authentication bypasses.
For each finding, rate severity (Critical/High/Medium/Low) and provide a fix.
```

### Chain-of-Thought (CoT)
Force step-by-step reasoning for complex problems:
```
Think through this step-by-step:
1. First, identify the core problem
2. Then, list the constraints
3. Generate 3 possible approaches
4. Evaluate each approach against the constraints
5. Recommend the best approach with reasoning
```

Variants:
- **Zero-shot CoT**: Add "Let's think step by step" at the end
- **Few-shot CoT**: Provide worked examples showing the reasoning process
- **Self-consistency**: Generate multiple reasoning paths, take majority answer

### Few-Shot Examples
Provide 2-5 examples of input/output pairs:
```
Convert these descriptions to git commit messages:

Description: Added user login with email and password
Commit: feat(auth): implement email/password login flow

Description: Fixed crash when uploading files larger than 10MB
Commit: fix(upload): handle large file uploads without crashing

Description: Reorganized the database module into smaller files
Commit: refactor(db): split monolithic module into focused files

Description: {user's description}
Commit:
```

**Example selection matters:**
- Cover the range of expected inputs (happy path + edge cases)
- Order from simple to complex
- Include examples that demonstrate tricky decisions

### Structured Output
Guide the model to produce parseable output:
```
Respond in this exact JSON format:
{
  "summary": "One sentence summary",
  "severity": "low|medium|high|critical",
  "affected_files": ["list", "of", "files"],
  "recommendation": "What to do"
}
```

Use XML tags for sections in long outputs:
```
<analysis>Your analysis here</analysis>
<recommendation>Your recommendation here</recommendation>
<code>Any code changes</code>
```

### Constitutional / Self-Critique
Have the model review its own output:
```
After generating your response, review it against these criteria:
1. Is every claim supported by evidence from the provided context?
2. Are there any logical gaps or unsupported assumptions?
3. Could this advice cause harm if followed incorrectly?
Revise your response to address any issues found.
```

### Tree of Thought
Explore multiple reasoning branches for complex decisions:
```
Consider three different approaches to this problem.
For each approach:
- Describe the approach in 2-3 sentences
- List pros and cons
- Rate feasibility (1-5) and quality (1-5)

Then select the best approach and implement it fully.
```

## Prompt Testing with promptfoo

### Config Structure
```yaml
# promptfooconfig.yaml
prompts:
  - file://prompts/v1.txt
  - file://prompts/v2.txt

providers:
  - anthropic:messages:claude-sonnet-4-5-20250929
  - openai:gpt-4o

tests:
  - vars:
      input: "What is the capital of France?"
    assert:
      - type: contains
        value: "Paris"
      - type: not-contains
        value: "I don't know"

  - vars:
      input: "Explain quantum computing to a 5-year-old"
    assert:
      - type: llm-rubric
        value: "Response uses simple language appropriate for a young child"
      - type: javascript
        value: "output.length < 500"
```

### Assertion Types
| Type | Purpose | Example |
|------|---------|---------|
| `contains` | Output includes text | `"Paris"` |
| `not-contains` | Output excludes text | `"I don't know"` |
| `is-json` | Valid JSON output | - |
| `javascript` | Custom JS check | `"output.length < 500"` |
| `llm-rubric` | AI-judged quality | `"Uses professional tone"` |
| `similar` | Semantic similarity | `value: "expected", threshold: 0.8` |
| `regex` | Pattern matching | `"\\d{4}-\\d{2}-\\d{2}"` |

### Running Evals
```bash
npx promptfoo@latest eval                    # Run all tests
npx promptfoo@latest eval --no-cache         # Force fresh responses
npx promptfoo@latest view                    # View results in browser
npx promptfoo@latest eval -o results.json    # Export results
```

## Evaluation Strategies

### Ground Truth Comparison
Best for tasks with objectively correct answers (math, factual lookups, code output):
- Compare output against known-correct answer
- Use exact match, contains, or regex assertions
- Track accuracy as percentage of passing tests

### LLM-as-Judge
Best for subjective quality (writing, analysis, creative tasks):
```yaml
assert:
  - type: llm-rubric
    value: |
      Rate this response on a 1-5 scale for:
      1. Accuracy: Are all facts correct?
      2. Completeness: Does it address the full question?
      3. Clarity: Is it easy to understand?
      A score of 4+ on all dimensions passes.
```

### Pairwise Comparison
Compare two prompt versions head-to-head:
- Show both outputs to a judge model
- Ask "Which response better addresses the user's need?"
- Track win rate across test cases

### Regression Testing
Ensure prompt changes don't break existing behavior:
- Maintain a "golden set" of test cases that must always pass
- Run golden set before deploying any prompt change
- Add new test cases when bugs are found (regression tests)

## Optimization Techniques

### Iterative Refinement Loop
1. Write initial prompt
2. Run against 5-10 test cases
3. Identify failure patterns (not individual failures)
4. Modify prompt to address the PATTERN, not specific cases
5. Re-run all tests (including previously passing ones)
6. Repeat until quality plateaus

### Prompt Compression
Same quality with fewer tokens saves cost and latency:
- Remove redundant instructions (the model already knows basic things)
- Replace verbose examples with concise ones
- Use structured formats (tables, lists) over prose
- Test compressed version against original to verify quality holds

### Temperature Tuning
| Use Case | Temperature | Why |
|----------|------------|-----|
| Code generation | 0.0-0.2 | Deterministic, correct output |
| Analysis/reasoning | 0.2-0.5 | Focused but allows nuance |
| Creative writing | 0.7-1.0 | Diverse, unexpected ideas |
| Brainstorming | 0.8-1.2 | Maximum variety |

## Anti-Patterns

- **Overfitting to test cases**: Prompt works perfectly on tests, fails on real inputs. Fix: Use diverse, realistic test cases
- **Over-constraining**: Too many rules make the model rigid and unable to handle edge cases. Fix: Explain principles, not just rules
- **Prompt injection blindness**: Not testing for adversarial inputs. Fix: Include injection attempts in test suite
- **Cargo-cult prompting**: Copying prompt patterns without understanding why they work. Fix: Test each element's contribution
- **Kitchen sink**: Adding every possible instruction upfront. Fix: Start minimal, add only what's needed based on failures
