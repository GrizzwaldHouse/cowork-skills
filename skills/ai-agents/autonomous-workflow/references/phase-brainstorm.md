# Phase: Brainstorm
<!-- Marcus Daley — 2026-05-01 — GStack role simulation protocol -->

## Purpose
Clarify intent and produce a locked spec.md before any planning or code.

## Method: GStack Role Simulation (single context)
Simulate four roles sequentially. Each role reasons from its own incentives.

### CEO
- What is the business/user value?
- What does success look like in one sentence?
- What would kill this project?

### Engineer
- What is technically feasible in the first iteration?
- What are the hidden complexity traps?
- What dependencies does this introduce?

### Designer
- Who uses this and what is their mental model?
- Where will users get confused?
- What is the minimal interface that covers the use cases?

### Security
- What are the trust boundaries?
- What data is sensitive and where does it flow?
- What is the blast radius of a failure?

## Output Contract
Produces `spec.md` in the working directory with sections:
- Goal (one sentence)
- Roles and stakeholders
- Functional requirements (numbered)
- Non-functional requirements (performance, security, scale)
- Out of scope (explicit)
- Open questions (for human review)

## Completion Criteria
`spec.md` exists and contains all six sections with no "TBD" placeholders.
