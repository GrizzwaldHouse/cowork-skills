# Voting Protocol
<!-- Marcus Daley — 2026-05-01 — Hybrid voting rules and thresholds -->

## When to Vote

### Simulated (single context — faster, lower cost)
Use for:
- Routine implementation decisions (which library, naming, file structure)
- Minor architectural choices within a single phase
- Style and formatting decisions

Procedure: reason through each role's perspective in sequence, reach a conclusion, proceed.

### Parallel Subagents (4 concurrent — higher quality, higher cost)
Use for:
- Architecture decisions that affect 2 or more phases
- Security boundary definitions (trust boundaries, auth, data flow)
- Integration contracts with external systems (AgenticOS, MCP servers, external APIs)
- Any decision where the four roles have conflicting incentives

## Parallel Vote Procedure

1. Spawn four subagents concurrently, each with a role-scoped prompt:

**Engineer prompt:**
```
You are the Engineer on a 4-person review panel. Evaluate this decision from a technical implementation perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

**Architect prompt:**
```
You are the Architect on a 4-person review panel. Evaluate this decision from a systems design and long-term maintainability perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

**PM prompt:**
```
You are the Product Manager on a 4-person review panel. Evaluate this decision from a user value and scope perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

**Security prompt:**
```
You are the Security Engineer on a 4-person review panel. Evaluate this decision from a security and risk perspective only.
Decision: [DECISION TEXT]
Context: [RELEVANT SPEC SECTIONS]
Return JSON: {"vote": "pass|fail", "justification": "one sentence", "concerns": ["concern if any"]}
```

2. Aggregate results:
   - 3 or 4 "pass" votes → PASS
   - 2 "pass" votes → Architect is tiebreaker
   - 0 or 1 "pass" votes → FAIL → escalate to human

3. **Security veto:** If Security returns `fail` with a non-empty `concerns` array, the decision is BLOCKED regardless of other votes.

4. Log to `state/votes.json`:
```json
{
  "votes": [
    {
      "decision": "description",
      "timestamp": "ISO8601",
      "ballots": {
        "Engineer": {"vote": "pass", "justification": "...", "concerns": []},
        "Architect": {"vote": "pass", "justification": "...", "concerns": []},
        "PM": {"vote": "pass", "justification": "...", "concerns": []},
        "Security": {"vote": "fail", "justification": "...", "concerns": ["XSS risk"]}
      },
      "result": "BLOCKED",
      "blocking_role": "Security"
    }
  ]
}
```
