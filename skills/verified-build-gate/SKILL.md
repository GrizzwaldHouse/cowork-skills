---
name: verified-build-gate
description: >
  6-step build verification pipeline that prevents unstable code from being pushed.
  Runs: build, launch runtime, 5-minute stability monitor, full test suite,
  independent reviewer agent analysis, and produces a final READY/NOT READY verdict.
  Use when pushing code, before releases, or when /build-gate is invoked.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Verified Build Gate

> Prevents unstable or unverified builds from being marked as complete or pushed to the repository.

## When to Use

- Before `git push` (auto-triggered by pre-push hook in quick mode)
- Before releases or deployments (run full mode manually)
- When `/build-gate` is invoked
- After significant refactoring or dependency changes

## Pipeline (6 Steps)

### Step 1: BUILD
Run the project's build command. Any compile-time error = immediate FAIL.
```bash
npm run build
```

### Step 2: LAUNCH RUNTIME
Start the application and wait for it to respond on its health endpoint.
- Timeout: 60s (full) / 30s (quick)
- Failure: crash, freeze, or no health response within timeout

### Step 3: STABILITY MONITOR (5 min) [full mode only]
Monitor the running application for 5 minutes:
- Subscribe to SSE event stream (Observer pattern, NOT polling)
- Health check every 30 seconds
- Watch for: unhandled errors, memory growth >50%, SSE disconnections
- Any anomaly = immediate FAIL

### Step 4: TEST SUITE
Run all automated tests:
1. **Vitest build-gate tests** — unit/integration (T04-T13)
2. **Playwright E2E tests** — browser tests (T01-T02)
3. **Custom scripts** — memory leak (T03), CPU spike (T14) [full mode only]
Any test failure = immediate FAIL.

### Step 5: REVIEWER AGENT [full mode only]
Spawn an independent `reviewer` subagent (read-only, separate context):
- Reviewer receives: test results JSON, build log, stability metrics
- Reviewer checks: test coverage gaps, suspicious patterns, result consistency
- Reviewer outputs: APPROVED or REJECTED with findings
- Must not share context with the builder agent

```
Launch a reviewer agent with subagent_type="reviewer" and provide it:
1. The contents of build-gate-report.json
2. The server console output from the stability monitor
3. Ask it to verify: all steps passed, no suspicious patterns, results consistent
4. The reviewer must output APPROVED or REJECTED with reasoning
```

### Step 6: FINAL VERIFICATION
Aggregate all results into `build-gate-report.json`:
- All steps PASS + reviewer APPROVED = **READY**
- Any step FAIL or reviewer REJECTED = **NOT READY**
- Kill the dev server process
- Print summary to console

## Modes

| Mode | Steps | Duration | Trigger |
|------|-------|----------|---------|
| **Quick** | 1, 2, 4 (vitest only), 6 | ~2 min | Pre-push hook, `npm run build-gate:quick` |
| **Full** | All 6 | ~8-10 min | Manual, `/build-gate` skill, `npm run build-gate` |

## Commands

```bash
npm run build-gate          # Full pipeline (all 6 steps)
npm run build-gate:quick    # Quick pipeline (pre-push speed)
npm run test:build-gate     # Just the vitest build-gate tests
npm run test:stability      # Just the 5-min stability monitor
```

## Test Registry (15 Tests)

| ID | Name | Runner | Category |
|----|------|--------|----------|
| T01 | Cold Start Boot | Playwright | Integration |
| T02 | Hot Reload Stability | Playwright | Runtime |
| T03 | Memory Leak Detection | Script | Performance |
| T04 | Unhandled Exception Traps | Vitest | Error Handling |
| T05 | File Watcher Config | Vitest | Event-Driven |
| T06 | Concurrent Request Handling | Vitest | Concurrency |
| T07 | DI Contract Integrity | Vitest | Architecture |
| T08 | Configuration Validation | Vitest | Config |
| T09 | Structured Logging | Vitest | Logging |
| T10 | Crash Recovery | Vitest | Resilience |
| T11 | API Contract Validation | Vitest | Integration |
| T12 | State Persistence | Vitest | Data Integrity |
| T13 | Security Boundary Checks | Vitest | Security |
| T14 | CPU Spike Handling | Script | Performance |
| T15 | Long-Running Stability | Script | Stability |

## Success Criteria

- All tests passed
- Runtime stable for 5 minutes (full mode)
- No unhandled errors
- Reviewer agent approved (full mode)
- Memory growth < 50% of baseline
- CPU recovers after load spike (>80% success rate)

## Failure Policy

- Stop pipeline immediately on any failure
- Log detailed failure reason
- Flag build as NOT READY
- Write `build-gate-report.json` with full details
- Never allow partial success
