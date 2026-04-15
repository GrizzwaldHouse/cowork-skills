# Supervisor Review Protocol

## Purpose
The supervisor agent is a quality gate that ensures all recovered/completed code
meets the project's architectural standards before being marked as done. This
prevents "technically compiles but architecturally wrong" from passing review.

## Review Checklist

The supervisor evaluates each submission against these criteria:

### 1. Comment-Code Alignment (Weight: 25%)
- [ ] Every function has CDD step-comments BEFORE the implementation
- [ ] Comments explain WHY decisions were made, not WHAT the code does
- [ ] Implementation beneath each comment matches the described intent
- [ ] If comment and code disagree, the comment has been updated (not deleted)

### 2. Architecture Constraint Compliance (Weight: 30%)
- [ ] **Event-driven only**: No polling loops, no `setInterval` checks, no timer-based state detection
- [ ] **Dependency injection**: No `new ConcreteClass()` in business logic; dependencies injected via constructor/parameter
- [ ] **Separation of concerns**: Each class/module has a single clear responsibility
- [ ] **Config-driven**: No magic numbers, no hardcoded URLs/colors/timeouts/strings
- [ ] **Repository pattern**: Data access abstracted behind interfaces
- [ ] **Access control**: No public mutable state; proper getters/readonly/private set

### 3. Build Cleanliness (Weight: 20%)
- [ ] Zero compilation errors
- [ ] Zero warnings (or warnings suppressed at narrowest scope with justification)
- [ ] No deprecated API usage
- [ ] Dependencies minimized in headers/declarations

### 4. Defensive Programming (Weight: 15%)
- [ ] Input validation at system boundaries
- [ ] Null/undefined checks before dereference in unsafe languages
- [ ] Typed error handling (no bare catch/except)
- [ ] Fail-fast on invalid state (no silent corruption)
- [ ] Subscription cleanup in destructors/teardown

### 5. Documentation Quality (Weight: 10%)
- [ ] File headers present (Developer, Date, Purpose)
- [ ] Single-line comment style used (no /* */ blocks for explanation)
- [ ] Design decisions documented where non-obvious
- [ ] No tutorial-style comments explaining basic syntax

## Scoring

Each criterion is scored 0-100:
- **90-100**: Exceeds standards. Portfolio-quality.
- **70-89**: Meets standards. Minor improvements possible.
- **50-69**: Below standards. Requires revision.
- **0-49**: Fails standards. Major rework needed.

**Passing score: 70+ on ALL criteria (not averaged)**

A single criterion below 70 requires revision on that criterion specifically.

## Supervisor Response Format

```json
{
  "review_id": "SR-2026-0323-001",
  "timestamp": "2026-03-23T14:30:00Z",
  "verdict": "APPROVED | REVISION_REQUIRED | REJECTED",
  "overall_score": 85,
  "criteria_scores": {
    "comment_code_alignment": 90,
    "architecture_compliance": 85,
    "build_cleanliness": 100,
    "defensive_programming": 75,
    "documentation_quality": 80
  },
  "issues": [
    {
      "severity": "HIGH | MEDIUM | LOW",
      "criterion": "architecture_compliance",
      "file": "SpawnManager.cs",
      "line": 47,
      "description": "Direct instantiation of HttpClient instead of injection",
      "fix": "Accept IHttpClientFactory via constructor parameter"
    }
  ],
  "commendations": [
    "Excellent use of event-driven patterns in the notification system",
    "Clean separation between data access and business logic"
  ]
}
```

## Multi-Agent Supervisor Mode

When using the multi-agent pipeline (Claude ↔ ChatGPT ↔ Audit):

1. **Claude Worker** completes the implementation
2. **Claude Worker** self-reviews against this checklist
3. **ChatGPT Auditor** performs independent review using the same checklist
4. **Supervisor** reconciles both reviews and makes final verdict
5. If either reviewer flags a HIGH severity issue, automatic REVISION_REQUIRED

This cross-agent review catches blind spots that a single agent might miss.
