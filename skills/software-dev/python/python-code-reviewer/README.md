# Python Code Reviewer

Quick-start guide for reviewing Python code against Marcus Daley's universal coding standards.

## Overview

Automated code review skill that validates Python code for compliance with portfolio-quality development standards. Focuses on access control, initialization, type safety, event-driven patterns, and security.

## Quick Start

### Basic Review

```
Review this Python code against Marcus's universal coding standards.
File: my_module.py
Focus: full audit
Severity: all
```

### Targeted Reviews

**Access Control Check:**
```
Review for access control violations:
- Unrestricted mutable public state
- Missing @property decorators
- Public attributes that should be private

File: [path]
```

**Type Safety Check:**
```
Review for type safety:
- Missing type hints on public functions
- Use of Any instead of specific types
- No validation at boundaries

File: [path]
```

**Security Check:**
```
Review for security vulnerabilities:
- SQL injection risks
- Hardcoded credentials
- Unvalidated inputs
- Swallowed errors

File: [path]
Severity: warnings+
```

## Common Violations

### Critical

1. **Unrestricted Mutable State** - Use `@property` for read-only access
2. **Magic Numbers/Strings** - Extract to named constants or Enums
3. **Polling Patterns** - Replace with event-driven callbacks
4. **SQL Injection** - Use parameterized queries only
5. **Bare Except** - Catch specific exception types

### High

1. **Missing Type Hints** - Annotate all public functions/methods
2. **No Input Validation** - Validate at system boundaries
3. **Tight Coupling** - Use dependency injection
4. **Defaults Outside __init__** - Set all defaults at construction

### Medium

1. **Missing File Headers** - Document developer, date, purpose
2. **No Docstrings** - Explain WHY for public APIs
3. **Long Functions** - Break down complex logic

## Python-Specific Rules

### Access Control
- Prefix private members with `_` (single underscore)
- Use `@property` for read-only state, not manual getters
- Never expose mutable collections directly (return copies or use `@property`)

### Initialization
- All defaults in `__init__`, never in function signatures (except `None`)
- Avoid mutable default arguments: `def func(items=None)` not `def func(items=[])`
- Initialize all instance attributes in `__init__` for clarity

### Type Hints
- Use `from __future__ import annotations` for forward references
- Use `TYPE_CHECKING` guard for imports needed only for type hints
- Prefer `Literal`, `Enum`, or `Protocol` over `Any`

### Error Handling
- Catch specific exceptions: `FileNotFoundError`, `ValueError`, etc.
- Add context to exceptions: `raise ValueError(f"Invalid config: {reason}") from e`
- Validate inputs at boundaries with clear error messages

### Communication
- Use callbacks, signals (Qt), or observer pattern for state changes
- Never poll in loops: `while True: if changed(): update()`
- Clean up subscriptions in `__del__` or context managers

## Review Workflow

1. **Run Review** - Provide file/snippet and focus areas
2. **Analyze Report** - Check severity levels and line numbers
3. **Prioritize Fixes** - Address CRITICAL first, then HIGH
4. **Apply Fixes** - Refactor code following recommendations
5. **Re-Review** - Verify fixes resolved violations
6. **Document** - Update docstrings and comments as needed

## Configuration Options

| Option | Values | Description |
|--------|--------|-------------|
| review_depth | quick, standard, thorough | How deep to analyze |
| focus_areas | access_control, type_hints, error_handling, performance, security | What to check |
| severity_threshold | all, warnings, critical | Minimum severity to report |

## Integration with Marcus's Standards

This skill enforces rules from `universal-coding-standards` and `enterprise-secure-ai-engineering`:

- **95/5 Rule** - Code should be 95% reusable library code
- **Quality Over Speed** - No shortcuts or 'quick fixes'
- **Configuration-Driven** - No hardcoded values
- **Event-Driven** - No polling loops
- **Type Safety** - Type hints on all public APIs
- **Security First** - Validate inputs, parameterize queries

## Example: Refactoring to Standards

**Before (Violations):**
```python
class ConfigManager:
    config = {}  # Mutable class state

    def load(self, path):
        try:
            self.config = json.load(open(path))
        except:
            pass
```

**After (Compliant):**
```python
# config_manager.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Manages application configuration with type-safe loading and validation.

from pathlib import Path
from typing import Any
import json


class ConfigManager:
    """Thread-safe configuration manager with validation."""

    def __init__(self):
        self._config: dict[str, Any] = {}

    @property
    def config(self) -> dict[str, Any]:
        """Current configuration (read-only copy)."""
        return self._config.copy()

    def load(self, path: Path) -> None:
        """Load configuration from JSON file with validation."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with path.open('r', encoding='utf-8') as f:
                config = json.load(f)

            if not isinstance(config, dict):
                raise ValueError(f"Config must be JSON object, got {type(config).__name__}")

            self._config = config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}") from e
        except PermissionError as e:
            raise PermissionError(f"Cannot read {path}: {e}") from e
```

**Changes:**
1. Added file header with required information
2. Made `_config` private with `@property` for read-only access
3. Replaced bare `except:` with specific exception types
4. Added type hints on all methods and attributes
5. Validated inputs and provided contextual error messages
6. Used pathlib.Path for type-safe file operations
7. Added docstrings explaining WHY, not WHAT

## Additional Resources

- `universal-coding-standards/SKILL.md` - Complete standards reference
- `enterprise-secure-ai-engineering/SKILL.md` - Security guardrails
- `architecture-patterns/SKILL.md` - Design patterns and practices

## Support

For questions about specific violations or refactoring guidance:
1. Reference the violation in context
2. Provide the current code snippet
3. Ask for architectural trade-offs
4. Discuss multiple solution approaches
