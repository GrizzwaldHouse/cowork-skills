# Phase: Verification
<!-- Marcus Daley — 2026-05-01 — Automated review and security gate -->

## Purpose
Validate that execution output is correct, performant, and secure before declaring the workflow complete.

## Input
All files produced during the execution phase.

## Method
Run three verification passes in order. All three must pass.

### Pass 1: Test Suite
```bash
python -m pytest --tb=short -q
```
Expected: 0 failures, 0 errors. Any failure blocks completion.

### Pass 2: Security Scan
Check for:
- [ ] No hardcoded secrets (grep for password, api_key, token = "...)
- [ ] No `eval()` or `exec()` on external input
- [ ] No path traversal vulnerabilities (unvalidated user paths)
- [ ] No SQL string interpolation

### Pass 3: Code Review Agent
Spawn a review subagent with this prompt:
```
Review the code produced in the execution phase against these criteria:
1. Does every public function have a clear single responsibility?
2. Are all error cases handled explicitly (no silent swallowing)?
3. Does the implementation match the acceptance criteria in phases.json?
4. Are there any race conditions or shared mutable state issues?

Return: PASS or FAIL with specific line references for any failures.
```

## Output Contract
Produces `verification_report.md` with:
- Test results (pass/fail counts)
- Security scan findings (or "clean")
- Code review verdict (PASS/FAIL + findings)
- Overall status: COMPLETE or BLOCKED

## Completion Criteria
`verification_report.md` exists and overall status is COMPLETE.
