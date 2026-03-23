---
name: ue5-blueprint-organization
description: >
  Nine best practices for keeping Unreal Engine 5 Blueprint graphs clean, readable,
  and maintainable. Covers DRY functions, commenting, reroute nodes, node reduction,
  modular components, subgraphs, variable categories, alignment tools, and productivity
  plugins. Use when reviewing or building Blueprint-heavy projects.
user-invocable: true
argument-hint: "[tip-number|all|checklist]"
---

# UE5 Blueprint Organization

> Nine proven tips for eliminating spaghetti Blueprints and keeping graphs maintainable.

## Description

Provides a structured set of best practices for organizing Unreal Engine 5 Blueprint graphs. Each tip targets a specific source of visual clutter or maintenance burden. Apply individually or as a complete cleanup pass. Works for any UE5 project regardless of genre.

## Prerequisites

- An Unreal Engine 5 project (5.0+, some features require 5.7+)
- Basic familiarity with Blueprint Editor (Event Graph, My Blueprint panel, Details panel)
- For Tip 9: access to Fab marketplace (optional)

## Usage

1. Identify which Blueprint graphs are getting messy or hard to follow
2. Apply the relevant tips from the checklist below
3. For a full cleanup pass, work through all 9 tips in order
4. Use the cleanup checklist at the end for code review

### Prompt Pattern

```
Review [Blueprint name] for organization issues using the 9-tip checklist.
Focus on [specific concern: duplicated logic / wire clutter / variable chaos / etc.]
Engine version: [5.x]
```

## The Nine Tips

### Tip 1: Functions / Custom Events for Repeated Logic

**Rule:** If the same logic exists in more than one place, that is a problem.

- Never duplicate the same nodes twice — extract into a **Function** and call it
- For logic reused across multiple Blueprints, use a **Blueprint Function Library**
  - Creates a global function library callable from any Blueprint in the project

| Use Case | Choose |
|----------|--------|
| Needs a return value | Function |
| Fire-and-forget execution | Custom Event |
| Called from other Blueprints | Custom Event (with dispatcher) or Function Library |
| Latent (Delay, Timeline) | Custom Event (functions cannot be latent) |

### Tip 2: Comment Your Code

You will NOT remember what a node does 3 months later.

**Method A — Node Comment:**
- Right-click any node > Add Comment
- Good for flagging nodes that need attention

**Method B — Comment Box:**
- Select a group of nodes > press **C**
- Wraps them in a labeled comment box
- Describe what an entire section of logic does

**Best Practices:**
- Describe the WHY, not the what
- Color-code comment boxes by system (movement = blue, combat = red, UI = green)

### Tip 3: Reroute Nodes

- **Double-click** anywhere on a wire to create a reroute node
- Acts as a movable handle to guide wires around obstacles
- Prevents wires from crossing over nodes
- Makes flow direction explicit and easier to follow

### Tip 4: Use Fewer Nodes for the Same Result

**Select Node** — Replaces Branch/Switch patterns:
- Picks a value from a list based on Boolean, Enum, or Integer
- Same job, less graph space

**Validated Get** — Replaces IsValid chains:
- Right-click variable > Convert to Validated Get
- Combines get + IsValid in one node

**Branch Conversion (UE 5.7+):**
- Right-click a Boolean variable > convert into a Branch node directly
- Eliminates separate Branch node + wire

### Tip 5: Modular Design with Components

Do NOT dump all code into one massive Blueprint.

- Split functionality into **Blueprint Components** (ActorComponents)
- Each component encapsulates one system (inventory, health, movement)
- Add the component to any actor that needs it

**Benefits:**
- Flexibility: same component works on Player, NPC, or any actor
- Cleanliness: character graph stays focused on character-specific logic
- Reusability: components are plug-and-play across projects

### Tip 6: Collapse Complex Sections into Subgraphs

- Select nodes > Right-click > Collapse
- Wraps them into a subgraph with input/output pins
- Main graph stays readable; double-click to edit internals

| Pro | Con |
|-----|-----|
| Main graph is cleaner | Logic hidden one level deeper |
| Inputs/outputs are explicit | Can confuse if overused |
| Good for long sequential chains | Debugging requires navigating in/out |

**Guideline:** Use sparingly. Prefer components (Tip 5) for reusable systems; reserve collapse for one-off complex sequences.

### Tip 7: Assign Variable Categories

As Blueprints grow, variables multiply. Organize them:

1. Select a variable in the My Blueprint panel
2. In the Details panel, type a Category name
3. Drag-and-drop variables between categories

**Suggested Categories:**
- `Config` — Tweakable settings
- `State` — Runtime state tracking
- `References` — Cached component/actor references
- `Combat` — Weapon, damage, ammo
- `Movement` — Speed, direction, physics
- `UI` — Widget references and display state

### Tip 8: Use Alignment Tools

- Right-click any node > Alignment section
- Select multiple nodes > align or distribute evenly
- Options: Align Left/Right/Top/Bottom, Distribute Horizontally/Vertically
- Not always perfect but worth using as a first pass

### Tip 9: Third-Party Productivity Plugins

**Blueprint Assist (Paid — Fab Marketplace):**
- Auto-formats nodes when placed on the graph
- One-click formatting algorithm repositions all nodes for readability
- Prevents spaghetti code automatically

Check Fab for other productivity tools (node organization, wire management, graph navigation).

## Examples

### Example 1: Extracting Repeated Logic

**Before (bad):** Health check duplicated in 3 event graphs
```
EventGraph A:  GetHealth > Branch > (True: DoThing) > (False: Die)
EventGraph B:  GetHealth > Branch > (True: DoThing) > (False: Die)
EventGraph C:  GetHealth > Branch > (True: DoThing) > (False: Die)
```

**After (good):** Single function called everywhere
```
Function: IsAlive() → Returns Bool
  GetHealth > Return (Health > 0)

EventGraph A:  IsAlive > Branch > ...
EventGraph B:  IsAlive > Branch > ...
EventGraph C:  IsAlive > Branch > ...
```

### Example 2: Variable Category Organization

**Before:** 20 variables in a flat unsorted list
**After:**
```
|- Config
|   |- MaxHealth
|   |- MoveSpeed
|   |- JumpHeight
|- State
|   |- bIsAlive
|   |- CurrentHealth
|   |- bIsJumping
|- References
|   |- MeshComponent
|   |- AnimInstance
|   |- AIController
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| tip | all | Which tip to focus on (1-9 or "all") |
| engine_version | 5.7 | UE version (affects Tip 4 availability) |
| scope | checklist | Output mode: "checklist", "review", or "guide" |

## File Structure

```
ue5-blueprint-organization/
  SKILL.md              # This skill definition
  README.md             # Overview and quick-start
  resources/
    cleanup-checklist.md  # Printable review checklist
    naming-conventions.md # BP naming and folder standards
```

## Notes

- Tips 1-8 work in all UE5 versions. Tip 4 (Bool-to-Branch) requires UE 5.7+.
- Tip 5 (modular components) aligns with C++ ActorComponent architecture.
- Tip 9 (Blueprint Assist) is a paid plugin; all other tips use built-in features.
- These tips apply to both gameplay and UI Blueprints.
- For C++ projects, these patterns have direct parallels (functions = methods, components = UActorComponent subclasses, etc.).
