---
name: brainstorm-artifact
description: Generate a structured, full-scope brainstorming artifact before writing any code or producing any deliverable on a new project, feature, or system. Use this skill whenever Marcus says "brainstorm", "let's plan out", "before we start", "scope this", "what should this do", or kicks off any new project, feature, milestone, or architectural decision. Also use when Marcus references a project name without prior scope (e.g. "let's start AgentForge", "begin SentinelMail Phase 2"). The artifact captures intent, constraints, and decisions as multi-question grouped checklists with mutually exclusive AND multi-select options, so Claude understands the FULL scope of what Marcus wants added before doing any work. Always present the artifact for review and confirmation before writing code.
user-invocable: true
---

# Brainstorm Artifact

Marcus's standard pre-work brainstorming format. Captures intent, scope, and decisions as grouped checklist sections so the full picture is locked in before any code, documents, or deliverables are produced.

This skill enforces Marcus's brainstorm-first methodology from his Universal Coding Standards: research before code, multiple approaches with trade-offs, scope locked before implementation.

## When To Use This Skill

Trigger automatically when Marcus:

- Mentions a new project name, system, or feature without prior scope context
- Says "brainstorm", "scope this", "let's plan", "before we start", "what should this do"
- Begins a new phase, milestone, or major architectural decision on an existing project
- Asks for help deciding between multiple implementation paths
- Requests a "kickoff" or "starter doc" for any work

Do NOT use when:

- Marcus is asking a quick syntax question, debugging a known bug, or doing pure code review
- Scope is already locked from a previous session and Marcus is just continuing implementation
- Marcus explicitly says "skip brainstorming" or "just write the code"

## Output Format Specification

The artifact is a single markdown file (or in-conversation artifact) titled:

```
[PROJECT_NAME] BRAINSTORM RESPONSES
Captured: [DATE]
```

The body is organized into 3 to 6 thematic SECTIONS, each containing 3 to 6 grouped QUESTIONS, each question containing 2 to 8 OPTION rows.

Every option row uses one of two formats:

```
[ ] Option label: One-sentence rationale or trade-off explanation
[x] Option label: One-sentence rationale or trade-off explanation
```

Sections are uppercase headers. Questions are sentence-case prompts ending in a question mark. Options are concrete, mutually informative choices. Each option includes a short justification after the colon so Marcus can scan trade-offs without expanding anything.

Some questions are single-select (choose one). Others are multi-select (check all that apply). The skill does not lock this; it follows the natural shape of the question. When in doubt, treat it as multi-select and let Marcus mark only the ones he wants.

## Section Taxonomy

Most Marcus projects break into a recognizable shape. Use these section archetypes when relevant:

**For platform or product builds**: Positioning and audience. Tech stack and architecture. AI and ML engine choices. MVP feature lock and scope cut. Compliance and security gates. Funding and infrastructure. Launch channel and marketing voice.

**For game development features**: Gameplay loop and player intent. AI and behavior systems. Data model and component structure. UI and feedback. Performance budget and target hardware. Polish and game feel. Testing and validation gates.

**For backend systems**: API surface and contract. Data model and persistence. Authentication and authorization. Observability and logging. Deployment and infrastructure. Failure modes and recovery. Testing and CI gates.

**For AI agent or skill builds**: Trigger conditions and intent capture. Tool use and action surface. Output format and structure. Safety gates and refusals. Memory and context budget. Evaluation and benchmarking. Distribution and packaging.

You may invent section names when the project does not fit these archetypes, but always group related decisions together so Marcus can think through one theme at a time.

## Question Design Rules

Each question must satisfy these constraints:

The question forces a decision Marcus actually needs to make before code is written. Avoid questions whose answer is already implied by Marcus's universal coding standards (event-driven communication, no polling, etc.) unless he is explicitly debating a deviation.

Each option includes the trade-off in the same line. Format: "Option label: One sentence on what you get and what you give up." This lets Marcus scan a question in five seconds.

Options are concrete and mutually informative. Avoid generic options like "Use a database" or "Add tests". Prefer specific options like "Postgres with row-level security: Strong constraint enforcement, slower iteration during prototyping" versus "MongoDB Atlas free tier: Faster iteration, weaker schema guarantees, fits Phase 1 of Bob and Sentinel".

If an option references a tool, library, or service Marcus has used before, mention it. The agent should pull from `userMemories` (Bob, SentinelMail, AgentForge, MCP Command Panel, Quidditch AI, IslandEscape, etc.) to make options feel anchored to his actual stack.

## Output Anatomy Example

```
[PROJECT_NAME] BRAINSTORM RESPONSES
Captured: 4/28/2026

## SECTION ONE NAME

Question text ending in a question mark?
[ ] Option A: Trade-off explanation in one sentence
[ ] Option B: Trade-off explanation in one sentence
[ ] Option C: Trade-off explanation in one sentence

Another question for this section?
[ ] Option A: Trade-off explanation in one sentence
[ ] Option B: Trade-off explanation in one sentence

## SECTION TWO NAME

Question text?
[ ] Option A: Trade-off explanation in one sentence
[ ] Option B: Trade-off explanation in one sentence
```

Refer to `examples/vetassist_reference.md` in this skill folder for a full real-world example.

## Workflow

Follow these phases in order. Do not skip ahead.

### Phase 1: Capture Intent

Before drafting the artifact, confirm or ask:

- What is the project or feature name?
- One-sentence purpose. What does this enable that does not exist today?
- Which existing Marcus projects, if any, does this connect to or borrow from?
- Hard constraints: deadlines, budgets, GitHub Student Pack expirations, family time, hardware limits.
- Are there any decisions already locked from prior sessions that should be marked `[x]` before Marcus reviews?

If Marcus has already provided this context in the current chat, extract it and skip the explicit question. Move to Phase 2.

### Phase 2: Draft the Artifact

Generate the full artifact following the section taxonomy and question design rules above. Three rules:

The artifact must cover the full scope of the project end-to-end, not just the next session's work. The point is to lock the picture so Claude Code does not implement only a slice and miss adjacent decisions.

Pre-check options Marcus has already decided. If he said "we're using FastAPI and MongoDB" earlier in the conversation, render those options as `[x]` not `[ ]`. The artifact is a record of decisions, not just open questions.

Include trade-offs that respect Marcus's standards. Never offer "quick and dirty" options or "just hardcode it for now" choices. Options should be quality-tier alternatives, not shortcuts versus correct.

### Phase 3: Present for Review

Present the artifact in the conversation. Explicitly ask Marcus to:

- Mark any open `[ ]` boxes with `[x]` for the choices he wants
- Strike through or remove options he wants to discard
- Add new options or sections you missed

Do NOT begin coding, scaffolding, or producing any other deliverable until Marcus has reviewed the artifact and given the go-ahead.

### Phase 4: Lock and Reference

Once Marcus confirms, save the artifact to the project's `docs/` folder as `BRAINSTORM_[YYYY-MM-DD].md` so it is version-controlled and referenceable in later sessions.

For Claude Code sessions, also append a one-line reference to `CLAUDE.md` or `SESSION_HANDOFF.md`:

```
- Brainstorm scope: docs/BRAINSTORM_2026-04-28.md (locked 2026-04-28)
```

This lets future sessions resume work without re-litigating settled decisions.

## Personality and Tone

Marcus has stated that he gets bored while programming and wants the interfaces he works with to be entertaining. The artifact is allowed to have personality. A few guidelines:

Section headers can lean into the project's theme. For a Quidditch AI project, sections might be "Broom Physics and Flight Loop" rather than "Gameplay Loop". For a dark academia portfolio site, section headers might use sigil or rune flavor.

Trade-off lines stay concise and informative. Personality goes in headers and intro lines, not in the actual decision rationale. Decisions need to be readable in five seconds.

Never sacrifice clarity for flavor. If a flavored header makes the question harder to understand, drop the flavor.

## Anti-Patterns to Avoid

Do NOT produce a brainstorm artifact that:

Is just a list of questions without options. Marcus needs to see trade-offs, not open-ended prompts.

Has fewer than three sections or fewer than three questions per section. That is not enough scope coverage to lock a project picture.

Includes "shortcut" or "quick and dirty" options. This violates Marcus's quality-over-speed principle from his Universal Coding Standards.

Buries the decisions in prose paragraphs. The format must be scannable checklists, not narrative.

Begins implementation before Marcus has reviewed and confirmed the artifact.

## Cross-References

This skill works alongside other cowork-skills:

- `universal-coding-standards`: Trade-off options must respect Marcus's coding rules. Never offer options that violate access control, initialization, or event-driven communication principles.
- `dev-workflow`: This skill IS the brainstorm-first methodology in operational form. Use it as the entry point for every new project.
- `architecture-patterns`: When sections touch on system architecture, options should reference specific patterns (Observer, Repository, Composition, Data-driven) rather than generic descriptions.
- `skill-creator`: When Marcus brainstorms a new skill, use this skill for the brainstorm artifact, then hand off to skill-creator for the implementation phase.

## Bundled Resources

- `templates/blank_brainstorm.md`: Empty template Marcus can copy into a new project as a starting point.
- `examples/vetassist_reference.md`: Full real-world brainstorm Marcus produced for the VetAssist platform. Use this as the gold-standard reference for tone, depth, and structure.
- `templates/section_archetypes.md`: Pre-built section templates for the four common project shapes (platform build, game feature, backend system, AI agent build).
