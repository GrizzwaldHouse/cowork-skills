# Scoring Rubric Reference

Detailed scoring criteria for each evaluation dimension.

---

## Accuracy (Weight: 30%)

| Score | Criteria |
|-------|----------|
| 90-100 | Output exactly matches expected answer. All facts correct. No omissions. |
| 75-89 | Minor inaccuracies that don't affect usability. 1-2 small omissions. |
| 60-74 | Some correct elements but notable gaps or partial errors. |
| 40-59 | Significant inaccuracies. Multiple wrong facts or missing requirements. |
| 0-39 | Mostly wrong. Hallucinated content. Fundamentally misunderstood the task. |

---

## Code Quality (Weight: 25%)

| Score | Criteria |
|-------|----------|
| 90-100 | Zero lint warnings. Follows all coding standards. Clean, idiomatic code. Proper error handling. |
| 75-89 | Minor style issues. 1-2 lint warnings. Good structure overall. |
| 60-74 | Several style issues. Missing error handling in some paths. Acceptable but needs polish. |
| 40-59 | Poor variable naming. Magic numbers. Missing validation. Mixed patterns. |
| 0-39 | Broken code. Security vulnerabilities. Global state. No error handling. CommonJS mixed in. |

### Code Quality Checklist (Auto-Scored)

```
+10: Uses const/let appropriately (no var)
+10: Named constants (no magic numbers)
+10: Functions have single responsibility
+10: Error handling at boundaries
+10: Input validation present
+10: ES Module syntax (import/export)
+10: Proper async/await (no unhandled promises)
+10: Descriptive variable/function names
+10: No hardcoded secrets or paths
+10: Clean separation of concerns

Deductions:
-20: Security vulnerability (SQL injection, XSS, etc.)
-15: Swallowed errors (empty catch blocks)
-10: Global mutable state
-10: Magic numbers in logic
-5: var usage
-5: console.log left in production code
-5: Inconsistent formatting
```

---

## Consistency (Weight: 20%)

Run the same prompt 3 times. Measure variance.

| Score | Criteria |
|-------|----------|
| 90-100 | All 3 outputs structurally identical. Same key points. Same format. |
| 75-89 | Same structure, minor wording differences. Key points preserved. |
| 60-74 | Same general approach but different details. Some key points missing in 1 run. |
| 40-59 | Different structures across runs. Contradictory details between runs. |
| 0-39 | Completely different outputs each time. Unreliable. |

### Consistency Measurement

```
For 3 runs of the same prompt:
  structural_match = compare section headers and format (0-100)
  content_overlap = Jaccard similarity of key facts extracted (0-100)
  quality_variance = standard deviation of individual quality scores

  consistency_score = (structural_match * 0.4) + (content_overlap * 0.4) + ((100 - quality_variance * 10) * 0.2)
```

---

## Logical Reasoning (Weight: 15%)

| Score | Criteria |
|-------|----------|
| 90-100 | Clear chain of reasoning. Each step follows logically. Handles edge cases. Considers tradeoffs. |
| 75-89 | Sound reasoning with minor gaps. Most edge cases considered. |
| 60-74 | Basic reasoning present but some logical jumps. Key tradeoffs missed. |
| 40-59 | Shallow reasoning. Conclusions don't follow from premises. Major gaps. |
| 0-39 | No reasoning visible. Contradictory statements. Non-sequiturs. |

---

## Response Structure (Weight: 10%)

| Score | Criteria |
|-------|----------|
| 90-100 | Perfect formatting. Valid JSON/Markdown. Clear headers. Logical flow. Proper code blocks. |
| 75-89 | Good formatting with minor issues. All sections present. |
| 60-74 | Readable but inconsistent formatting. Some sections missing or poorly structured. |
| 40-59 | Hard to parse. Mixed formats. No clear organization. |
| 0-39 | Broken formatting. Invalid JSON. No structure. Wall of text. |

### Structure Auto-Check

```
+20: Uses markdown headers (##, ###)
+20: Code blocks use proper language tags (```javascript)
+20: Lists are properly formatted
+20: JSON output is valid (parseable)
+20: Response follows requested format exactly

Deductions:
-20: Invalid JSON when JSON was requested
-15: No code blocks for code output
-10: Missing requested sections
-5: Inconsistent header levels
-5: No bullet points when listing items
```

---

## Overall Score Calculation

```
overall = (accuracy * 0.30)
        + (code_quality * 0.25)
        + (consistency * 0.20)
        + (reasoning * 0.15)
        + (structure * 0.10)
```

### Grade Scale

| Overall Score | Grade | Action |
|--------------|-------|--------|
| 90-100 | A | Model is excellent for this task. Lock in config. |
| 80-89 | B | Model is good. Minor prompt refinements may help. |
| 70-79 | C | Model is acceptable. Apply training adjustments. |
| 60-69 | D | Model struggles. Try different model or heavy prompt engineering. |
| 0-59 | F | Model unsuitable for this task. Do not use. Route elsewhere. |
