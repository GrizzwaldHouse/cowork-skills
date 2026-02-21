# Universal Coding Standards

Marcus Daley's non-negotiable coding rules that apply across ALL programming languages, frameworks, and platforms.

## Quick Start

These standards are auto-loaded. When writing or reviewing any code for Marcus, every implementation must pass these checks:

1. **Access Control** -- Most restrictive access level that allows function. No unrestricted mutable state.
2. **Initialization** -- All defaults at construction. No magic numbers or strings.
3. **Communication** -- Event-driven (Observer pattern). Never polling.
4. **Dependencies** -- Minimal imports in declarations. Dependency injection. Composition over inheritance.
5. **Comments** -- Explain WHY, not WHAT. Line comments only. File headers required.
6. **Error Handling** -- Validate at boundaries. Typed errors. Fail fast.

## Key Principle

**The 95/5 Rule**: 95% of code should be reusable across projects without modification. Only 5% should be project-specific configuration.

## What's Covered

- Core philosophy (95/5 Rule, quality over speed, config-driven design)
- Access control and encapsulation rules by language
- Initialization discipline
- Event-driven communication patterns by language
- Dependency management
- Comment standards and file header format
- Error handling and defensive programming
- Comprehensive anti-patterns list
