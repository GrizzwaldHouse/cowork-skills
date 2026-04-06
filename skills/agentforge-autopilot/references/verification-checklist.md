# Verification Checklist

Run these checks before committing or advancing to the next phase. All must pass.

---

## Checks

### 1. TypeScript Build

```bash
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx tsc --noEmit
```

| Result | Action |
|--------|--------|
| No output | PASS |
| Error lines | FAIL — fix all type errors before proceeding |

### 2. Test Suite

```bash
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx vitest run
```

| Result | Action |
|--------|--------|
| All tests pass | PASS |
| Failures exist | FAIL — fix failing tests, retry up to 3 times |
| No tests found | WARN — acceptable only for Phase 4 (UI-only), otherwise FAIL |

### 3. Lint

```bash
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx next lint
```

| Result | Action |
|--------|--------|
| No warnings/errors | PASS |
| Warnings only | PASS (with note) |
| Errors | FAIL — fix lint errors |

### 4. Git Status

```bash
git -C "C:/Users/daley/Projects/SeniorDevBuddy" status --short
```

| Result | Action |
|--------|--------|
| Only expected files modified | PASS |
| Untracked `.env` or credential files | FAIL — do not commit secrets |
| Unexpected files modified | WARN — review before committing |

### 5. Test Count Regression

Compare test count to previous phase:

```bash
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx vitest run --reporter=verbose 2>&1 | grep -c "✓\|✗"
```

| Result | Action |
|--------|--------|
| Count >= previous phase | PASS |
| Count < previous phase | FAIL — tests were deleted or broken |

**Known test counts by phase:**
- Phase 1+2: baseline
- Phase 3: 20+ tests (execution, observability, event bus, orchestrator)
- Phase 4+: must not decrease

### 6. Import Graph

Verify no circular imports:

```bash
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && npx tsc --noEmit --listFiles 2>&1 | head -5
```

If TypeScript compiles, no circular dependency issues exist at the type level.

### 7. Interface Contracts

Verify all agent implementations match the `Agent` interface:

```bash
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && grep -r "implements Agent" src/agents/ --include="*.ts"
```

| Result | Action |
|--------|--------|
| All agent files found | PASS |
| Missing implementations | FAIL — every agent must implement the interface |

### 8. Event Bus Consistency

Verify event types used in code match the type definitions:

```bash
cd "C:/Users/daley/Projects/SeniorDevBuddy/agentforge_autonomous" && grep -r "emit\|subscribe" src/ --include="*.ts" -l
```

Cross-reference with `src/core/events/types.ts` to ensure no undeclared event types.

| Result | Action |
|--------|--------|
| All events match type definitions | PASS |
| Undeclared event types found | FAIL — add missing types to `types.ts` |

---

## Failure Remediation

| Failure | Common Fix |
|---------|-----------|
| Type error: property missing | Add the property to the interface or implementation |
| Type error: incompatible types | Check interface definition, update implementation to match |
| Test timeout | Increase timeout in test config, check for async leaks |
| Test assertion failure | Verify expected values match current implementation |
| Lint: unused import | Remove the import |
| Lint: any type | Add proper type annotation |
| Circular import | Extract shared types to a separate `types.ts` file |
| Event type mismatch | Update `src/core/events/types.ts` with the new event |

## Retry Protocol

1. On first failure: read the error, apply the fix, re-run the check
2. On second failure: re-read the relevant source files, apply a different fix
3. On third failure: stop, report the error, and ask for guidance
