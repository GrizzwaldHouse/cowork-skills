# CLAUDE.md Addition: Brainstorming Artifact Standard

Append the section below to your existing global `CLAUDE.md` file, anywhere after your "Coding Standards" section but before the closing meta-rules. The block is self-contained and reinforces what the `brainstorm-artifact` skill does, so behavior stays consistent whether or not the skill auto-loads.

---

## Brainstorming Artifact Standard

When Marcus opens any new project, feature, milestone, or major architectural decision, the response begins with a structured **Brainstorm Artifact**, never with code.

This applies whether the trigger is explicit ("brainstorm this", "scope this", "what should this do") or implicit (a project name appears without prior scope, a new phase begins, or a decision between implementation paths is requested). When in doubt, default to producing the artifact.

### Required Format

The artifact is a markdown document titled `[PROJECT_NAME] BRAINSTORM RESPONSES` with a `Captured: [DATE]` line below the title. The body is organized into three to six thematic SECTIONS, each containing three to six grouped QUESTIONS, each question containing two to eight OPTION rows.

Every option is rendered as either `[ ] Label: Trade-off rationale` (open decision) or `[x] Label: Trade-off rationale` (decision already locked from the conversation or from prior sessions). The trade-off rationale is one sentence describing what the option gives and what it costs, so Marcus can scan a question in five seconds without expanding anything.

### Required Coverage

The artifact must cover the full scope of the project end-to-end, not just the immediate next session's work. The point of locking the picture is to prevent Claude or Claude Code from implementing only a slice and missing adjacent decisions that would force rework later. If the project has audience, tech stack, AI engine, MVP lock, compliance, funding, and launch dimensions, all of them appear as sections even if some have only one or two questions.

### Decision Pre-Checking

Options Marcus has already decided in the current chat or in prior sessions are pre-checked with `[x]` before the artifact is presented. The artifact is a record of decisions plus open questions, not just open questions. If a stack choice was locked three sessions ago in a related project, render it as locked here too with a note like "(carried from Bob)" so Marcus sees the link.

### Rules That Cannot Be Violated

Trade-off options must respect the Universal Coding Standards. Never offer "quick and dirty", "just hardcode for now", "skip the tests for MVP", or any time-pressure shortcut as a valid option. Options are quality-tier alternatives only. Speed-versus-correctness is a false dichotomy in Marcus's portfolio work.

Never begin coding, scaffolding files, or generating any other deliverable until Marcus has reviewed the artifact and given explicit confirmation. The brainstorm gate is non-negotiable. If Marcus says "skip it" or "just write the code" he can override, but the default is always artifact first.

Never bury the decisions inside prose paragraphs. The format is scannable checklists. Personality and theme can live in section headers and intro lines, but the decision rows themselves are clean checkbox format.

### Lock and Reference

After Marcus reviews and confirms, save the artifact to the project's `docs/` folder as `BRAINSTORM_[YYYY-MM-DD].md` and append a one-line reference to the project's `CLAUDE.md` or `SESSION_HANDOFF.md`:

```
- Brainstorm scope: docs/BRAINSTORM_2026-04-28.md (locked 2026-04-28)
```

This makes the locked scope discoverable in future sessions without re-litigating settled decisions.

### Reference Skill

The full implementation of this behavior lives in the `brainstorm-artifact` skill in `cowork-skills`. When that skill is loaded, follow it as the source of truth. When it is not loaded (because of context budget or a fresh environment), follow this section verbatim.

---

End of CLAUDE.md addition.
