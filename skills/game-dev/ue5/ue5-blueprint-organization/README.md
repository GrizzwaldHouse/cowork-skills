# UE5 Blueprint Organization

Nine best practices for keeping Unreal Engine 5 Blueprint graphs clean and readable.

## Quick Start

Invoke in Claude Code:
```
/ue5-blueprint-organization
/ue5-blueprint-organization 5        # Focus on Tip 5 (modular components)
/ue5-blueprint-organization checklist # Run full cleanup review
```

## The 9 Tips at a Glance

| # | Problem | Solution | Shortcut |
|---|---------|----------|----------|
| 1 | Duplicated logic | Functions / Function Libraries | — |
| 2 | Forgot what nodes do | Comments | **C** key / Right-click |
| 3 | Wires crossing everywhere | Reroute nodes | Double-click wire |
| 4 | Too many nodes for simple ops | Select / ValidatedGet / Bool-to-Branch | Right-click variable |
| 5 | One giant Blueprint | Blueprint Components | — |
| 6 | Long node chains | Collapse to Subgraph | Right-click > Collapse |
| 7 | Variable list is chaos | Category assignments | Details panel |
| 8 | Nodes scattered randomly | Alignment tools | Right-click > Alignment |
| 9 | Manual formatting tedium | Blueprint Assist plugin | Fab marketplace |

## Requirements

- Unreal Engine 5.0+ (Tip 4 Bool-to-Branch requires 5.7+)
- Blueprint Editor access
- Tip 9 requires Blueprint Assist plugin from Fab (paid, optional)

## See Also

- `SKILL.md` — Full skill definition with examples and configuration
- `resources/cleanup-checklist.md` — Printable review checklist
- `resources/naming-conventions.md` — Blueprint naming and folder standards
