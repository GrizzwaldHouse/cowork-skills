---
name: architecture-patterns
description: Architecture patterns, file organization, and UI architecture standards for all projects. Covers Observer, composition, interface-driven design, data-driven design, repository pattern, and separation of concerns.
user-invocable: false
---

# Architecture Patterns

> Design patterns, file organization conventions, and UI architecture standards that apply across all of Marcus Daley's projects.

## Description

Provides the architectural playbook for structuring projects. Covers the six core patterns (Observer, component composition, interface-driven design, data-driven design, repository pattern, separation of concerns), UI architecture rules, and file organization conventions by project type. Includes language-specific implementations for each pattern.

## Prerequisites

- None -- these patterns apply universally

## Usage

When designing or reviewing architecture for any project, reference these patterns. The Observer pattern is the primary communication mechanism across all projects.

1. Identify which patterns apply to the feature being built
2. Select the language-specific implementation from the tables
3. Verify UI code separates state management from rendering
4. Organize files by feature/domain, not by file type

### Prompt Pattern

```
Design the architecture for [feature] in [language/framework].
Apply Marcus's architecture patterns: Observer for communication,
composition over inheritance, interface-driven contracts,
data-driven configuration.
```

## Core Patterns

### Observer Pattern (Primary)

The primary communication pattern across ALL projects. Systems broadcast events, listeners respond.

**Use for:** State changes, UI updates, cross-service communication, plugin/extension systems
**Never use:** Polling loops or timers to detect changes

| Language | Implementation |
|----------|---------------|
| C++ (UE5) | DECLARE_DYNAMIC_MULTICAST_DELEGATE with UPROPERTY(BlueprintAssignable) |
| C# | `event` keyword with delegate types, or `IObservable<T>` |
| TypeScript | EventEmitter, RxJS, or typed event bus |
| Python | Signals (Django), blinker library, or custom observer |
| React | Context + useReducer, Zustand, or Redux for global state; callbacks/events for component communication |
| Rust | Channels (tokio::sync or std::sync::mpsc) |

### Component Composition

Prefer small, focused, composable units over deep inheritance hierarchies. Components can be mixed and matched without complex inheritance chains. Easier to test, reuse, and reason about.

| Context | Implementation |
|---------|---------------|
| UE5 | ActorComponents that can be added to any actor |
| React | Small focused components composed together, custom hooks for shared logic |
| Backend | Middleware/interceptors, mixins, decorators, strategy pattern |
| General | Interfaces/traits/protocols define contracts, concrete classes implement specific behavior |

### Interface-Driven Design

Define contracts through interfaces/protocols/traits. Code to abstractions, not implementations. Enables loose coupling, testability (mock implementations), and swappable behavior.

| Language | Implementation |
|----------|---------------|
| C++ | Pure virtual classes (interfaces) or UE5 UInterfaces |
| TypeScript | `interface` keyword or abstract classes |
| Python | ABC (Abstract Base Class) or Protocol (structural typing) |
| C# | `interface` keyword |
| Rust | `trait` keyword |
| Java | `interface` keyword |
| Go | Implicit interfaces (structural typing) |

### Data-Driven Design

Separate data/configuration from logic. Let non-programmers or config files drive behavior.

| Context | Implementation |
|---------|---------------|
| UE5 | Data Assets, Data Tables, Blueprint configuration |
| Unity | ScriptableObjects, JSON config files |
| Web | JSON/YAML config files, CMS-driven content, feature flags, theme tokens |
| Backend | Database-driven configuration, feature flag services, environment variables |
| General | Anything a designer/PM/ops person might want to change should not require code changes |

### Repository Pattern

Abstract data access behind a consistent interface regardless of storage mechanism. Swap databases, APIs, or mock data without changing business logic.

**Applies to:** Database access, API clients, File I/O, Cache layers

- Bad: `class OrderService { private db = new PostgresDB(); }`
- Good: `class OrderService { constructor(private repo: OrderRepository) {} }`

### Separation of Concerns

Each module/class/function should have one clear responsibility. If you can't describe a module's purpose in one sentence, it's doing too much.

| Context | How to Separate |
|---------|----------------|
| UE5 | C++ handles logic and state, Blueprint handles visual configuration and level design |
| React | Components handle rendering, hooks handle state/effects, utilities handle pure logic |
| Backend | Controllers handle HTTP, services handle business logic, repositories handle data access |

## UI Architecture

**Principle:** Logic layer broadcasts state changes. Presentation layer listens and renders.

### Rules

1. **State management code must be completely separable from rendering code.** Enables testing logic without UI, swapping UI frameworks, and clear debugging.

2. **UI binds to state change events, never polls for updates.**

| Context | Implementation |
|---------|---------------|
| UE5 | C++ components broadcast delegates, Blueprint widgets bind and update visuals |
| React | State/context changes trigger re-renders automatically. Never use setInterval to check state |
| Vue | Reactive data system handles updates. Computed properties over watchers where possible |
| Vanilla JS | Custom events or observer pattern. MutationObserver only for DOM-level observation |

3. **Clean up event listeners/subscriptions when UI components are destroyed.**

| Context | Cleanup Location |
|---------|-----------------|
| UE5 | Unbind delegates in NativeDestruct |
| React | Return cleanup from useEffect |
| Vue | Use onUnmounted lifecycle hook |
| Vanilla JS | removeEventListener in teardown |

## File Organization

**Principle:** Group by feature/domain, not by file type, when projects grow beyond trivial size.

### UE5 Game Project

```
Source/ProjectName/Code/
  Actors/          # Physical game objects
  AI/              # Controllers, behavior tree tasks/services/decorators
  Components/      # Reusable ActorComponents
  Utility/         # Interfaces, helpers, enums, type definitions
  UI/              # Widget classes
  GameModes/       # Match logic and win conditions
```

### Web Frontend

```
src/
  components/      # Reusable UI components
  features/        # Feature-specific modules (components + hooks + utils grouped)
  hooks/           # Shared custom hooks
  utils/           # Pure utility functions
  types/           # Shared type definitions
  services/        # API client and data fetching
  styles/          # Global styles, theme tokens
```

### Backend Service

```
src/
  controllers/     # HTTP/transport layer
  services/        # Business logic
  repositories/    # Data access layer
  models/          # Data models/schemas
  middleware/      # Cross-cutting concerns (auth, logging, validation)
  utils/           # Pure utility functions
  types/           # Shared type definitions
  config/          # Configuration loading and validation
```

### Python Project

```
src/project_name/
  models/          # Data models/dataclasses
  services/        # Business logic
  api/             # HTTP handlers
  utils/           # Utility functions
  config/          # Settings and configuration
```

## Naming Conventions

### General Rules

- Be consistent within a project -- pick a convention and stick to it
- Names describe WHAT something is, not HOW it's implemented
- Prefix interfaces/abstractions consistently (I prefix in C#/UE5, no prefix in TS/Go)

### Language-Specific

| Language | Convention |
|----------|-----------|
| C++ (UE5) | Components: `AC_Name`, Interfaces: `IName`, AI Controllers: `AIC_Name`, BT nodes: `BTTask_`/`BTService_`/`BTDecorator_`, Blueprints: `BP_Name` |
| TS/React | Components: PascalCase (`UserProfile.tsx`), Hooks: `use` prefix (`useAuth.ts`), Utilities: camelCase, Types: PascalCase, Constants: SCREAMING_SNAKE_CASE |
| Python | Modules: snake_case, Classes: PascalCase, Functions: snake_case, Constants: SCREAMING_SNAKE_CASE, Private: `_leading_underscore` |
| C# | Classes: PascalCase, Interfaces: `I` prefix, Methods: PascalCase, Private fields: `_camelCase`, Properties: PascalCase |

## Examples

### Example 1: Event-Driven Health System

**Input:**
```
Design a health system for a game character that notifies the UI when health changes.
```

**Output:**
Uses Observer pattern: HealthComponent broadcasts OnHealthChanged delegate. UI widget subscribes and updates health bar. HealthComponent never references UI directly. Multiple listeners (UI, AI, audio) can subscribe independently.

### Example 2: Web API with Repository Pattern

**Input:**
```
Design the data access layer for a user management API.
```

**Output:**
Define UserRepository interface with CRUD methods. Implement PostgresUserRepository. Inject into UserService. Service contains business logic, repo handles SQL. Can swap to MockUserRepository for tests without changing service code.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| primary_pattern | observer | Default communication pattern |
| file_organization | feature-based | Group by feature, not file type |
| composition_preference | composition | Prefer composition over inheritance |

## File Structure

```
architecture-patterns/
  SKILL.md                    # This skill definition
  README.md                   # Quick-start guide
  resources/
    pattern-decision-tree.md  # When to use which pattern
```

## Notes

- The Observer pattern is non-negotiable for cross-system communication. If you're tempted to poll, use an event instead.
- File organization conventions can be adapted per project, but the principle of grouping by feature holds universally.
- When choosing between patterns, prefer the one that maximizes the 95/5 Rule (reusable logic, minimal project-specific code).
