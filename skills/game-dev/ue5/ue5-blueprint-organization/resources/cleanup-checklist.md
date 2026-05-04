# Blueprint Cleanup Checklist

> Print this out or use as a review template when auditing Blueprint graphs.

## Per-Blueprint Review

### DRY (Don't Repeat Yourself)
- [ ] No duplicated logic — all repeated patterns extracted to Functions
- [ ] Cross-Blueprint shared logic uses Blueprint Function Libraries
- [ ] Custom Events used for fire-and-forget / latent operations
- [ ] Functions used where return values are needed

### Readability
- [ ] Every complex section has a comment box (press C to create)
- [ ] Individual tricky nodes have right-click comments where needed
- [ ] Comment boxes are color-coded by system
- [ ] Reroute nodes used where wires would cross over nodes
- [ ] No wire tangles or overlapping paths

### Node Efficiency
- [ ] Select nodes used instead of Branch/Switch where applicable
- [ ] Validated Gets used instead of IsValid + Get chains
- [ ] Bool-to-Branch conversion used where possible (UE 5.7+)

### Architecture
- [ ] Logic split into ActorComponents, not monolithic BPs
- [ ] Each component handles exactly one system
- [ ] Player/Character BP only contains character-specific logic
- [ ] Complex one-off sequences collapsed into subgraphs (sparingly)

### Variables
- [ ] All variables assigned to categories (Config, State, References, etc.)
- [ ] Variable names are descriptive (not Var1, TempBool, MyFloat)
- [ ] Boolean variables prefixed with "b" (bIsAlive, bCanFire)

### Layout
- [ ] Nodes aligned using alignment tools (Right-click > Alignment)
- [ ] Graph reads left-to-right (execution flow)
- [ ] Related nodes grouped visually
- [ ] No "spaghetti" wire tangles remaining

## Project-Wide Review

- [ ] No Blueprint has more than ~100 nodes in a single graph
- [ ] Function Libraries exist for shared utility logic
- [ ] Component-based architecture used consistently
- [ ] Naming conventions followed (see naming-conventions.md)
