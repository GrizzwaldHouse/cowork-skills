# Question Types Reference

Six question types are supported. Pick the type that matches the natural shape of the decision being captured. Do not force a question into the wrong type, the user produces bad answers and the locked decisions corrupt downstream consumers.

## single

Pick exactly one option from a stack of pills.

```js
{
  id: "draft_storage",
  type: "single",
  prompt: "Where do in-progress drafts live?",
  options: [
    { label: "Local-first IndexedDB", rationale: "Works offline, sync on save." },
    { label: "Cloud-first Postgres", rationale: "Multi-device, requires connection." }
  ]
}
```

Rendering: vertical stack of pill buttons. Selected pill has inverted background. Rationale appears in lighter text below the label.

Use when: the question forces a binary or n-ary architectural choice where only one path can be taken.

## multi

Pick any subset (zero or more) from pills.

```js
{
  id: "a11y_features",
  type: "multi",
  prompt: "Which accessibility features are non-negotiable for the MVP?",
  options: [
    { label: "Screen reader support", rationale: "ARIA labels and semantic HTML." },
    { label: "Keyboard navigation", rationale: "Full app usable without mouse." },
    { label: "High contrast mode", rationale: "WCAG AAA color ratios." }
  ]
}
```

Rendering: vertical stack of pill buttons. Each selected pill shows a checkmark and inverted background.

Use when: compatible options can be combined.

## true_false

Two side-by-side pills, larger than `single` pills.

```js
{
  id: "auth_required",
  type: "true_false",
  prompt: "Should the platform require authentication before any draft can be created?",
  options: [
    { label: "Yes", rationale: "Tied to an account from minute one." },
    { label: "No", rationale: "Anonymous drafts allowed, claim later." }
  ]
}
```

Rendering: two pills side by side, larger than `single`. Rationale below each pill rather than inline.

Use when: clean binary decision that does not benefit from elaborate option treatment.

## ranked

Reorder options into a priority sequence with up/down arrows.

```js
{
  id: "feature_priority",
  type: "ranked",
  prompt: "Rank these features by which would be cut last if forced.",
  options: [
    { label: "Voice input on questions" },
    { label: "Multi-user collaboration" },
    { label: "Offline mode" },
    { label: "Export to PDF" }
  ]
}
```

Rendering: vertical stack with up/down arrows next to each option and a rank number on the left (1 is highest). Drag-and-drop optional but arrows mandatory for accessibility.

Use when: the question forces a hierarchy decision. Output captures both inclusion and ordering.

## numeric_scale

Grid where each row is a labeled subject and each column is a numeric scale value.

```js
{
  id: "disclaimer_intensity",
  type: "numeric_scale",
  prompt: "Rate the disclaimer intensity required at each touchpoint.",
  scale: {
    min: 0,
    max: 4,
    labels: ["None", "Subtle", "Moderate", "Prominent", "Mandatory modal"]
  },
  rows: [
    { id: "homepage", label: "Homepage" },
    { id: "first_draft", label: "First draft creation" },
    { id: "submission", label: "Final submission" }
  ]
}
```

Rendering: grid with scale labels above. User clicks one cell per row.

Use when: rating multiple subjects on the same dimension.

## abc_match

Grid where each row maps to a category column.

```js
{
  id: "ai_capability_tier",
  type: "abc_match",
  prompt: "Assign each AI-related capability to its tier.",
  categories: [
    { id: "must", label: "Must-have", description: "MVP blocker if missing" },
    { id: "should", label: "Should-have", description: "Important but not blocking" },
    { id: "could", label: "Could-have", description: "Nice if time permits" }
  ],
  rows: [
    { id: "summarize", label: "Summarize uploaded documents" },
    { id: "draft", label: "Draft a response from scratch" },
    { id: "translate", label: "Translate between languages" }
  ]
}
```

Rendering: grid with category labels and descriptions in legend above. User clicks one cell per row to assign.

Use when: mapping many items to a smaller number of categories. Common patterns are MoSCoW, MVP/V1/V2 phasing, and tier allocation.

## Adding a seventh type

If a question genuinely does not fit any of the six, add a new type rather than forcing it. The pattern is:

1. Define the type's data shape (what fields go in the question object)
2. Add a renderer to the artifact's question component
3. Add an XP rule in the gamification layer if internal mode supports the new type
4. Document it here

New types are pure additions. Do not modify existing types.
