# Phase: Planning
<!-- Marcus Daley — 2026-05-01 — GSD decomposition into phases.json -->

## Purpose
Decompose spec.md into discrete executable phases and produce phases.json.

## Input
`spec.md` in the working directory.

## Method: GSD Phase Decomposition
1. Read spec.md functional requirements
2. Group requirements into 3-7 cohesive phases (each phase must be independently testable)
3. For each phase define: name, goal, inputs, outputs, acceptance criteria, estimated complexity (S/M/L)
4. Identify dependencies between phases
5. Order phases by dependency graph (topological sort)

## Output Contract
Produces `phases.json` in the working directory:

```json
{
  "workflow_id": "uuid",
  "spec_path": "spec.md",
  "phases": [
    {
      "id": "phase-slug",
      "name": "Human-readable name",
      "goal": "One sentence",
      "inputs": ["file or state dependency"],
      "outputs": ["file or artifact produced"],
      "acceptance_criteria": ["testable criterion"],
      "complexity": "S|M|L",
      "depends_on": ["other-phase-slug"]
    }
  ]
}
```

## Completion Criteria
`phases.json` exists, parses as valid JSON, contains at least one phase, and all phases have non-empty acceptance_criteria arrays.
