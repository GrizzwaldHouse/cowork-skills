---
name: doc-coauthoring
description: Guide structured workflow for collaborative documentation. Use when writing documentation, proposals, technical specs, decision docs, PRDs, design docs, RFCs, or any substantial written document that benefits from iterative development. Trigger when the user wants to write, draft, or create any long-form technical or business document, especially when they say things like "help me write", "draft a proposal", "create a spec", or "let's work on a document together".
---

# Doc Co-Authoring Skill

A structured three-stage workflow for producing high-quality documentation collaboratively.

## Stage 1: Context Gathering

Begin by understanding the full picture before writing anything.

### Initial Questions
1. **Purpose**: What decision or action should this document drive?
2. **Audience**: Who will read this? What's their technical level?
3. **Scope**: What's in scope and out of scope?
4. **Format**: Is there a required template or structure?
5. **Constraints**: Deadlines, word limits, tone requirements?
6. **Existing Material**: Any prior docs, notes, or data to incorporate?

### Context Sources
- Ask the user for relevant files, data, or prior documents
- Check for existing templates in the project
- If integrations are available (Slack, Drive, SharePoint, MCP servers), offer to pull relevant context

### Output
A brief context summary confirming understanding before proceeding.

## Stage 2: Refinement & Structure

Build the document iteratively through brainstorming and editing cycles.

### Step 2a: Outline
- Propose a detailed outline based on gathered context
- Include section headers, key points per section, and approximate length
- Get user approval before writing prose

### Step 2b: Section-by-Section Development
For each section:
1. **Brainstorm**: Generate 2-3 approaches for the section content
2. **Draft**: Write the strongest approach
3. **Review**: Present to user for feedback
4. **Iterate**: Refine based on feedback before moving to next section

### Step 2c: Integration Pass
- Ensure consistent voice and terminology throughout
- Verify cross-references between sections
- Check that the document flows logically from start to finish
- Add transitions between sections

### Writing Principles
- **Front-load key information**: Put the most important point first in each section
- **Use concrete examples**: Abstract claims need specific supporting evidence
- **Eliminate filler**: Every sentence should advance the document's purpose
- **Match tone to audience**: Technical for engineers, accessible for stakeholders
- **Active voice**: Prefer "The team implemented X" over "X was implemented"

## Stage 3: Reader Testing

Test the document's effectiveness before finalizing.

### Self-Review Checklist
- [ ] Does the introduction clearly state the document's purpose?
- [ ] Can someone unfamiliar with the project understand it?
- [ ] Are all acronyms defined on first use?
- [ ] Are claims supported with evidence or data?
- [ ] Is there a clear call-to-action or next steps section?
- [ ] Are images and diagrams properly captioned with alt text?

### Blind Spot Detection
Read the document as if seeing it for the first time:
- What questions would a reader have that aren't answered?
- What assumptions are made but not stated?
- Are there logical gaps between sections?

### Final Polish
- Proofread for grammar, spelling, and formatting
- Verify all links and references
- Ensure consistent formatting (headers, lists, code blocks)
- Add table of contents for documents longer than 3 pages

## Document Templates

### Technical Spec
```
# [Feature Name] Technical Specification
## Summary (1 paragraph)
## Goals and Non-Goals
## Background / Context
## Detailed Design
## Alternatives Considered
## Security / Privacy Considerations
## Testing Plan
## Rollout Plan
## Open Questions
```

### Decision Document
```
# [Decision Title]
## Context
## Decision
## Consequences
## Alternatives Considered
## Decision Criteria
```

### PRD (Product Requirements Document)
```
# [Product/Feature Name] PRD
## Problem Statement
## User Stories
## Requirements (Must-Have / Nice-to-Have)
## Success Metrics
## Technical Constraints
## Timeline
## Open Questions
```

### RFC (Request for Comments)
```
# RFC: [Title]
## Status: [Draft | Review | Accepted | Rejected]
## Author(s)
## Summary
## Motivation
## Detailed Design
## Drawbacks
## Alternatives
## Unresolved Questions
```
