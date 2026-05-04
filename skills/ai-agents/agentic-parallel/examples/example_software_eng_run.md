<!--
filename: example_software_eng_run.md
developer: Marcus Daley
date: 2026-04-29
purpose: Worked example of a 3-agent full-stack software-engineering run under the AgenticOS Command Center. Demonstrates a frontend builder, a backend integrator, and an end-to-end test author with one REVIEW BY AGENT invocation. Stack matches Marcus's preferred posture: Next.js + Zustand + TanStack Query + Drizzle + Zod + Playwright.
-->

# Worked Example: Software Engineering - Bookmark Sync Endpoint

A fully filled-in `task_template.md` for a single feature on a Next.js / FastAPI hybrid app: add a "sync bookmarks" endpoint plus the UI that calls it, with end-to-end coverage. Three agents run in parallel: AGENT-01 builds the frontend, AGENT-02 wires the backend, AGENT-03 writes the e2e test. One REVIEW BY AGENT pass at the backend stage 3.

Skill reference: `skills/ai-agents/agentic-parallel/SKILL.md`. Constants come from `AgenticOS/config.py`.

---

## 1. Header

```
TASK NAME:    Bookmark Sync Endpoint - Full-Stack Slice
DOMAIN:       software-eng
CREATED:      2026-04-29
OWNER:        Marcus Daley
SESSION GOAL: Ship a "sync bookmarks" feature end-to-end. Frontend exposes a
              SyncBookmarksButton that calls a server action; backend persists
              the sync via Drizzle with Zod-validated input and Arcjet rate
              limiting; a Playwright e2e test exercises the happy path and
              one rate-limit boundary. Each layer compiles, types cleanly,
              and is wired through Zustand state and TanStack Query.
```

---

## 2. Agent Roster

| agent_id | role | total_stages | output_ref (terminal stage) |
|---|---|---|---|
| AGENT-01 | frontend-builder | 4 | state/outputs/agent-01-stage-4.md |
| AGENT-02 | backend-integrator | 4 | state/outputs/agent-02-stage-4.md |
| AGENT-03 | e2e-tester | 3 | state/outputs/agent-03-stage-3.md |

---

## 3. Stage Definitions

### Agent AGENT-01 - frontend-builder

```
agent_id:     AGENT-01
domain:       software-eng
task:         Build the SyncBookmarksButton React component plus the Zustand
              store slice and TanStack Query mutation that drive it. Connect
              to the sync endpoint via a typed server-action client. Loading,
              error, and success states must be visually distinct.
spawned_by:   null
total_stages: 4
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Drafting Zustand store slice and TanStack Query mutation hook | 25 min | No |
| 2 | Building SyncBookmarksButton component with three visual states | 30 min | Yes |
| 3 | Wiring the typed server-action client and error toast surface | 25 min | Yes |
| 4 | Writing component-level tests with Vitest and React Testing Library | 25 min | Yes |

Initial prompt for AGENT-01:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-01.
Your domain is software-eng.
Your task is: Build SyncBookmarksButton plus the Zustand store slice and
TanStack Query mutation. Connect via typed server-action client. Visually
distinct loading / error / success states.
Your total_stages is 4.
Your spawned_by is null.

Your stages are:
  Stage 1: Drafting Zustand store slice and TanStack Query mutation hook
  Stage 2: Building SyncBookmarksButton component with three visual states
  Stage 3: Wiring the typed server-action client and error toast surface
  Stage 4: Writing component-level tests with Vitest and React Testing Library

Approval gates after stages: 2, 3, 4

Stack alignment from CLAUDE.md:
  - Zustand for client state, TanStack Query for server state
  - Zod schemas shared with backend (single source of truth, see AGENT-02)
  - No hardcoded URLs - read endpoint from config

Wait for AGENT-02 stage 1 output (state/outputs/agent-02-stage-1.md, the
Zod schema) to exist before wrapping Stage 3; you can begin Stages 1 and 2
in parallel against an interface contract.

Use AgenticOS.state_store and AgenticOS.config for every state write.
```

---

### Agent AGENT-02 - backend-integrator

```
agent_id:     AGENT-02
domain:       software-eng
task:         Wire the POST sync-bookmarks server action: Zod-validated input,
              Drizzle persistence, Arcjet rate limit, NextAuth session check,
              and structured JSON response. Server action is treated as a
              public endpoint per CLAUDE.md guardrails.
spawned_by:   null
total_stages: 4
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Defining Zod schemas (request, response, error envelope) | 20 min | No |
| 2 | Implementing Drizzle migration and repository function | 30 min | Yes |
| 3 | Implementing the server action with auth, rate limit, and validation | 35 min | Yes |
| 4 | Adding structured logging (no PII) and unit tests | 25 min | Yes |

Initial prompt for AGENT-02:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-02.
Your domain is software-eng.
Your task is: Wire the POST sync-bookmarks server action with Zod-validated
input, Drizzle persistence, Arcjet rate limiting, NextAuth session check, and
a structured JSON response.
Your total_stages is 4.
Your spawned_by is null.

Your stages are:
  Stage 1: Defining Zod schemas (request, response, error envelope)
  Stage 2: Implementing Drizzle migration and repository function
  Stage 3: Implementing the server action with auth, rate limit, and validation
  Stage 4: Adding structured logging (no PII) and unit tests

Approval gates after stages: 2, 3, 4

Critical rules from CLAUDE.md Enterprise Secure AI Engineering section:
  - Server-side validation required (Zod), never trust client validation alone
  - Parameterized queries only (Drizzle handles this; do not concatenate SQL)
  - Rate limiting required on all public endpoints (Arcjet)
  - No sensitive data in logs (mask user identifiers, never log tokens or PII)
  - No hardcoded credentials - read from env via process.env

Use AgenticOS.state_store and AgenticOS.config for every state write.
```

---

### Agent AGENT-03 - e2e-tester

```
agent_id:     AGENT-03
domain:       software-eng
task:         Write a Playwright e2e test that covers: (a) successful sync of
              a small bookmark batch, (b) Arcjet rate-limit boundary at the
              configured threshold, and (c) auth-failure path when the user
              session is missing. Each path asserts visible UI state matches
              the response.
spawned_by:   null
total_stages: 3
```

| Stage | stage_label | Expected duration | Gate after stage? |
|---|---|---|---|
| 1 | Drafting Playwright fixtures (auth, db reset, network mocks) | 25 min | No |
| 2 | Writing the three test cases (happy, rate-limit, auth-fail) | 35 min | No |
| 3 | Running the suite locally and writing a results report | 20 min | Yes |

Initial prompt for AGENT-03:

```
Read C:\ClaudeSkills\skills\ai-agents\agentic-parallel\SKILL.md before doing anything else.

Your agent_id is AGENT-03.
Your domain is software-eng.
Your task is: Write Playwright e2e tests covering the happy path, the Arcjet
rate-limit boundary, and the auth-failure path for the sync-bookmarks endpoint.
Your total_stages is 3.
Your spawned_by is null.

Your stages are:
  Stage 1: Drafting Playwright fixtures (auth, db reset, network mocks)
  Stage 2: Writing the three test cases (happy, rate-limit, auth-fail)
  Stage 3: Running the suite locally and writing a results report

Approval gates after stages: 3

Wait for both upstream terminal output files to exist before starting Stage 1:
  - state/outputs/agent-01-stage-4.md (frontend complete)
  - state/outputs/agent-02-stage-4.md (backend complete)

Upsert initial state with stage_label "Waiting for frontend and backend outputs"
immediately, then poll for both files every 30 seconds.

Use AgenticOS.state_store and AgenticOS.config for every state write.
```

---

## 4. Approval Policy

| agent_id | Gate after stage | Policy | Operator evaluation criteria |
|---|---|---|---|
| AGENT-01 | 2 | Human approval | Verify the three visual states are clearly distinct (color, icon, motion). RESEARCH MORE if loading state could be missed. |
| AGENT-01 | 3 | Human approval | Verify endpoint URL is read from config, not hardcoded. Verify error toast surface is wired. |
| AGENT-01 | 4 | Human approval | Verify component tests cover loading / error / success branches. |
| AGENT-02 | 2 | Human approval | Verify Drizzle migration is reversible (down() is non-empty). |
| AGENT-02 | 3 | Human approval | Verify server-action enforces auth FIRST, then rate limit, then validation. REVIEW BY AGENT recommended (security path). |
| AGENT-02 | 4 | Human approval | Verify structured logs do not contain PII (no email, no token, no password). |
| AGENT-03 | 3 | Human approval (mandatory) | All three test cases must PASS. Any FAIL aborts the merge. |

---

## 5. Reviewer Policy

| agent_id | Stage requiring reviewer | Verdict format expected | Why review here |
|---|---|---|---|
| AGENT-02 | 3 (recommended) | PASS / REVISE / REJECT + 1-3 notes on auth-rate-validate ordering and PII handling | The server-action stage is the OWASP-relevant path; an independent Haiku pass catches missing auth checks, rate-limit bypass paths, and validation skips that the worker model would defend. |

Scheduled invocation: at AGENT-02 stage 3, the operator clicks REVIEW BY AGENT. The dashboard spawns the Haiku reviewer (`config.REVIEWER_MODEL`), passes `state/outputs/agent-02-stage-3.md` (which contains the full server-action source) as `reviewer_context`, and writes the verdict to `state/outputs/agent-02-review.md`.

Sample verdict produced by the Haiku reviewer:

```markdown
PASS

Note 1: NextAuth session check runs before Arcjet rate-limit check; ordering
        is correct. Auth failure returns 401 with a non-revealing error envelope.
Note 2: Zod schema is parsed via safeParse; validation errors return 400 with
        field-level messages. Good.
Note 3: Drizzle insert uses the parameterized helper. No raw SQL detected.
        Recommend adding a unit test that asserts a malformed payload does not
        reach the repository function.
```

AGENT-02 reads the verdict, sets `reviewer_verdict = "PASS - NextAuth session check runs before Arcjet rate-limit check; ordering is correct. Auth failure returns 401 with a non-revealing error envelope..."` (truncated to 200 chars), transitions to `status=waiting_approval`, and waits for the operator's PROCEED. Operator reads the third note, agrees with the recommendation, clicks PROCEED. AGENT-02 advances to stage 4 and adds the malformed-payload test as part of the unit-test stage.

---

## 6. Output Paths

| Artifact | Path |
|---|---|
| AGENT-01 stage outputs | state/outputs/agent-01-stage-{1..4}.md |
| AGENT-02 stage outputs | state/outputs/agent-02-stage-{1..4}.md |
| AGENT-03 stage outputs | state/outputs/agent-03-stage-{1..3}.md |
| Reviewer verdicts | state/outputs/agent-02-review.md |
| Frontend source artifacts | repo `app/` and `components/` (owned by AGENT-01) |
| Backend source artifacts | repo `app/api/` and `db/` (owned by AGENT-02) |
| Playwright tests | repo `tests/e2e/sync-bookmarks.spec.ts` (owned by AGENT-03) |

---

## 7. Success Criteria

- [ ] All three agents reach `status=complete`.
- [ ] AGENT-01: zero TypeScript errors, zero ESLint errors, component tests green.
- [ ] AGENT-02: Drizzle migration applies and rolls back cleanly, server-action enforces auth-rate-validate in order, no PII in logs.
- [ ] AGENT-02 reviewer verdict is PASS, OR REVISE notes were resolved before stage 4.
- [ ] AGENT-03: all three Playwright tests pass on a clean local run.
- [ ] No `waiting_approval` rows remain in `config.AGENTS_JSON` at session end.

---

## 8. Rollback Plan

- AGENT-01 type errors compound: revert `components/SyncBookmarksButton.tsx` to the prior commit, re-spawn AGENT-01 with a continuation seeded from `state/outputs/agent-01-stage-1.md`.
- AGENT-02 Drizzle migration breaks the dev database: run the down migration, restore from the most recent dev snapshot, mark AGENT-02 `status=error` with `error_msg="MigrationError: Down migration failed at stage 2, snapshot restored."`. Investigate before re-running.
- AGENT-02 reviewer returns REJECT: do not redo in place. Spawn AGENT-02-bis with the reject reasoning as a negative example. Continue under the same `agent_id`.
- AGENT-03 Playwright suite cannot connect to the local app: confirm both AGENT-01 and AGENT-02 outputs are committed and the dev server is running on the documented port. Mark AGENT-03 `status=error` with `error_msg="EnvError: Dev server not reachable at stage 3"` if the issue is environmental.

---

## 9. agents.json Seed

```json
[
  {
    "agent_id": "AGENT-01",
    "domain": "software-eng",
    "task": "Build SyncBookmarksButton plus Zustand store slice and TanStack Query mutation. Visually distinct loading / error / success states.",
    "stage_label": "Not started",
    "stage": 1,
    "total_stages": 4,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "2026-04-29T11:00:00Z"
  },
  {
    "agent_id": "AGENT-02",
    "domain": "software-eng",
    "task": "Wire the POST sync-bookmarks server action with Zod validation, Drizzle persistence, Arcjet rate limiting, and NextAuth session check.",
    "stage_label": "Not started",
    "stage": 1,
    "total_stages": 4,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "2026-04-29T11:00:00Z"
  },
  {
    "agent_id": "AGENT-03",
    "domain": "software-eng",
    "task": "Write Playwright e2e tests covering happy, rate-limit, and auth-failure paths for sync-bookmarks.",
    "stage_label": "Waiting for frontend and backend outputs",
    "stage": 1,
    "total_stages": 3,
    "progress_pct": 0,
    "status": "active",
    "context_pct_used": 0,
    "output_ref": null,
    "awaiting": null,
    "error_msg": null,
    "spawned_by": null,
    "reviewer_verdict": null,
    "updated_at": "2026-04-29T11:00:00Z"
  }
]
```
