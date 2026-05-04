# Coding Standards Applied to This Skill

This skill follows Marcus's stated coding standards. Every pattern below is a specific application of those standards to brainstorm artifact generation.

## No hardcoded values

Every numeric or string value that might change in the future is defined as a named constant near the top of the artifact. Examples:

- `XP_RULES` for XP awards per action
- `RANK_THRESHOLD` for XP per rank
- `THEMES` for visual tokens
- `ACHIEVEMENTS` for the catalog
- `SOUND_CUES` for audio frequencies

When generating an artifact, never inline a magic number or magic string in the rendering code. Add it to a constant first, then reference the constant.

## Configuration-driven design

Adding a feature is adding to a data structure, not modifying rendering code.

- New theme → new entry in THEMES
- New achievement → new entry in ACHIEVEMENTS
- New question type → new renderer registered in a renderer map, not a switch statement
- New section in a brainstorm → new entry in BRAINSTORM_DATA.sections

The rendering code reads the data and renders accordingly. The rendering code does not need to know about specific themes, specific achievements, or specific question types beyond the registered renderers.

## Event-driven architecture

User actions emit events. Subscribers handle the consequences. Adding a new consequence is a new subscriber, not a modification to action emission.

Why this matters for brainstorm artifacts: gamification layers, analytics, autosave, and undo/redo are all separate concerns that need to react to user actions. Coupling them all into the action handler turns it into a god function. Event-driven keeps each concern in its own module.

## Reusable, long-term solutions

This skill is built so a single artifact template handles every brainstorm. The user does not need a custom artifact per project. They need:

- A new BRAINSTORM_DATA object per session
- A new theme entry in THEMES if the project's domain doesn't fit existing themes
- Possibly a new achievement or question type if the project genuinely needs one

The rendering code is project-agnostic. This is the configuration-driven design principle applied at the skill level.

## React component conventions

The wizard component is a single default-export functional component using hooks. Imports use the React + lucide-react + recharts stack available in Claude artifacts. No external dependencies beyond what artifacts ship with.

State persistence uses `window.storage` in Claude artifacts (which has the storage API documented in the artifact rendering environment). For standalone HTML client forms, `localStorage` is used directly since `window.storage` is not available outside Claude artifacts.

## Tailwind utility classes only

The artifact uses only Tailwind's core utility classes. No custom CSS, no Tailwind compiler features that aren't in the base stylesheet. Color values that are not in Tailwind's default palette are applied as inline styles using the theme's tokens.

## Naming conventions

- Constants: `UPPER_SNAKE_CASE`
- Components: `PascalCase`
- Hooks and functions: `camelCase`
- Theme keys, question type names, achievement IDs: `snake_case` (matches BRAINSTORM_DATA convention)
- Event names: `dot.separated.lowercase`

## Avoiding em-dashes

Per Marcus's user preference, this skill's documentation and any artifact-generated text avoid em-dashes. Use commas, periods, parentheses, or restructured sentences instead. This applies to:

- Skill documentation (this file and the SKILL.md)
- Artifact-generated text (question prompts, rationale text, achievement descriptions)
- Export summaries

When in doubt, restructure the sentence rather than reach for an em-dash.
