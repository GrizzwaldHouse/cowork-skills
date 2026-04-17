---
name: superpowers-workflow
description: "Advanced software development workflow patterns including test-driven development (TDD), systematic debugging, subagent-driven development, and structured code review. Use when the user mentions TDD, red-green-refactor, systematic debugging, code review process, development workflow, subagent development, parallel development, or wants to follow disciplined software engineering practices. Also trigger for 'write tests first', 'debug this systematically', 'review this code', or 'help me plan this implementation'."
---

# Superpowers Workflow

Advanced development patterns from the Superpowers project (obra/superpowers). Disciplined engineering workflows for test-driven development, systematic debugging, structured code review, and parallel agent development.

## Test-Driven Development (TDD)

### RED-GREEN-REFACTOR Cycle

#### RED: Write a Failing Test
1. Write the simplest test that expresses the desired behavior
2. Run it -- confirm it fails for the RIGHT reason
3. The failure message should clearly describe what's missing

```
# Think about what you want the code to DO, not how to implement it
# Write a test that describes the expected behavior
# Run: confirm FAIL with meaningful error
```

#### GREEN: Make It Pass
1. Write the MINIMUM code to make the test pass
2. Don't think about elegance -- just make it work
3. Run tests -- confirm PASS

```
# Write just enough code to pass
# Resist the urge to write more than needed
# Run: confirm PASS
```

#### REFACTOR: Clean Up
1. Now improve the code while keeping tests green
2. Remove duplication, improve naming, simplify structure
3. Run tests after each change -- they must stay green

```
# Improve code quality
# Run tests after every change
# If a test breaks, you went too far -- undo
```

### TDD Rules
- Never write production code without a failing test
- Write only enough of a test to fail
- Write only enough production code to pass the failing test
- Refactor only when all tests pass
- Each test should test ONE behavior

### Test Quality Checklist
- [ ] Test name describes the behavior being tested
- [ ] Test is independent (doesn't depend on other tests)
- [ ] Test is deterministic (same result every time)
- [ ] Test is fast (< 1 second)
- [ ] Test covers both happy path and edge cases
- [ ] Failure message clearly explains what went wrong

## Systematic Debugging

### 4-Phase Root Cause Process

#### Phase 1: Reproduce
1. Get a reliable reproduction case
2. Simplify to the minimal reproduction
3. Document exact steps, inputs, and environment
4. Confirm the bug isn't intermittent (or document the pattern if it is)

#### Phase 2: Isolate
1. Form a hypothesis about where the bug lives
2. Add logging/breakpoints to narrow the location
3. Use binary search: comment out half the code, which half has the bug?
4. Check recent changes (git log, git diff) for likely culprits

#### Phase 3: Fix
1. Understand WHY the bug exists before changing code
2. Write a test that reproduces the bug (fails before fix, passes after)
3. Make the smallest change that fixes the bug
4. Run the full test suite to check for regressions

#### Phase 4: Prevent
1. Document: What caused it? How was it found? How was it fixed?
2. Add the regression test to the test suite
3. Consider: Could static analysis or linting catch this?
4. Consider: Is this a pattern that could occur elsewhere?

### Debugging Anti-Patterns
- **Shotgun debugging**: Making random changes hoping something works
- **Printf debugging overload**: Adding dozens of print statements without a hypothesis
- **Blame-driven debugging**: Assuming the bug is in someone else's code
- **Fix-the-symptom**: Hiding the error instead of fixing the cause

## Structured Code Review

### Review Checklist

#### Correctness
- [ ] Does the code do what it claims to do?
- [ ] Are edge cases handled?
- [ ] Are error conditions handled properly?
- [ ] Are there off-by-one errors?
- [ ] Is the logic complete (no missing else branches)?

#### Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validation at system boundaries
- [ ] No SQL injection or XSS vulnerabilities
- [ ] Proper authentication/authorization checks
- [ ] Sensitive data not logged

#### Design
- [ ] Single Responsibility Principle followed?
- [ ] Appropriate abstraction level (not too much, not too little)?
- [ ] Dependencies injected, not hardcoded?
- [ ] Interface is clear and minimal?
- [ ] No unnecessary coupling between modules?

#### Maintainability
- [ ] Code is self-documenting (clear naming)?
- [ ] Comments explain WHY, not WHAT?
- [ ] No dead code or commented-out blocks?
- [ ] Consistent style with the rest of the codebase?
- [ ] Tests exist and are meaningful?

### Giving Review Feedback
- Start with what's good (genuine, not perfunctory)
- Ask questions before making demands ("Could you explain why...?")
- Suggest alternatives, don't just criticize
- Distinguish between blocking issues and nitpicks
- Be specific: point to the exact line and explain the concern

### Receiving Review Feedback
- Assume good intent
- Don't take feedback personally
- Ask for clarification if you don't understand
- Thank reviewers for catching issues
- If you disagree, explain your reasoning calmly

## Subagent-Driven Development (SDD)

### When to Use Parallel Agents
- Multiple independent files need changes
- Research and implementation can happen simultaneously
- Different subsystems need independent work
- Test writing and implementation can be parallelized

### SDD Workflow

#### 1. Spec Review
Before any code, review the specification:
- What are the requirements?
- What are the acceptance criteria?
- What are the constraints?
- What questions remain?

#### 2. Implementation Plan
Break work into parallelizable chunks:
- Identify independent units of work
- Define interfaces between units
- Plan integration order
- Assign each chunk to a subagent

#### 3. Parallel Execution
Spawn agents with clear instructions:
```
Agent 1: Implement [module A] with interface [spec]
Agent 2: Implement [module B] with interface [spec]
Agent 3: Write tests for [module A + B integration]
```

#### 4. Two-Stage Review
1. **Automated**: Run tests, linters, type checkers
2. **Manual**: Review each agent's output for correctness and style

### Agent Task Prompt Template
```
## Task
[Specific task description]

## Context
[Relevant files and their purposes]

## Constraints
- Follow [coding standard]
- Use [pattern]
- Do not modify [files]

## Expected Output
[What files should be created/modified]

## Success Criteria
[How to verify the task is complete]
```

## Development Workflow Integration

### Feature Development Flow
1. **Understand**: Read relevant code, ask clarifying questions
2. **Plan**: Design approach, identify affected files
3. **Test First**: Write failing tests for new behavior (TDD)
4. **Implement**: Write minimum code to pass tests
5. **Refactor**: Clean up while keeping tests green
6. **Review**: Self-review or structured code review
7. **Integrate**: Merge, resolve conflicts, verify CI passes

### Bug Fix Flow
1. **Reproduce**: Confirm the bug exists and is consistent
2. **Test**: Write a test that captures the bug
3. **Debug**: Use systematic debugging to find root cause
4. **Fix**: Make minimal change to fix
5. **Verify**: Run full test suite
6. **Document**: Log the bug, cause, and fix for future reference
