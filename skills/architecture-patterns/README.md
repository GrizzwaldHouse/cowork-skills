# Architecture Patterns

Marcus Daley's architecture playbook for structuring projects across all languages and frameworks.

## Quick Start

When designing any feature or system, apply these patterns:

1. **Observer Pattern** -- Primary communication for all cross-system state changes. Never poll.
2. **Component Composition** -- Small, focused, composable units over deep inheritance.
3. **Interface-Driven Design** -- Code to abstractions, not implementations.
4. **Data-Driven Design** -- Separate data/config from logic. Non-programmers can change behavior.
5. **Repository Pattern** -- Abstract data access behind consistent interfaces.
6. **Separation of Concerns** -- One clear responsibility per module/class/function.

## What's Covered

- Six core architecture patterns with language-specific implementations
- UI architecture rules (state separate from rendering, event-driven updates)
- File organization by project type (UE5, web frontend, backend, Python)
- Naming conventions by language (C++/UE5, TypeScript/React, Python, C#)
- Pattern selection guidance
