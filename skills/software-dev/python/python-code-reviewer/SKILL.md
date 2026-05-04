---
name: python-code-reviewer
description: Review Python code for compliance with Marcus Daley's universal coding standards. Checks access control, initialization, event-driven patterns, type hints, error handling, and anti-patterns.
user-invocable: true
---

# Python Code Reviewer

> Automated review tool for validating Python code against Marcus Daley's universal coding standards, focusing on access control, initialization discipline, event-driven communication, type safety, and architectural quality.

## Description

Reviews Python code files, modules, or snippets for adherence to Marcus's universal coding standards. Identifies violations of critical rules including unrestricted mutable state, scattered initialization, polling patterns, missing type hints, and security anti-patterns. Provides severity-rated violation reports with actionable fix recommendations and rationale based on portfolio-quality development principles.

## Prerequisites

- Python 3.10+ (required for modern type hints)
- Understanding of Marcus's coding philosophy (95/5 Rule, Quality Over Speed, Configuration-Driven Design)
- Familiarity with Python best practices (type hints, property decorators, dataclasses)

## Usage

Invoke this skill when reviewing Python code for standards compliance. Specify the review scope and focus areas based on the context.

1. Provide Python file path, code snippet, or module to review
2. Specify review focus: full audit, access control, type safety, performance, security, or standards compliance
3. Set severity threshold: show all issues, warnings and above, or critical only
4. Receive violation report with severity levels, line numbers, explanations, and fix recommendations
5. Apply fixes iteratively and re-review until clean

### Prompt Pattern

```
Review this Python code against Marcus's universal coding standards.
File: [path/to/file.py]
Focus: [full audit | access control | type safety | performance | security | standards]
Severity: [all | warnings+ | critical]

Check for:
- Access control: unrestricted mutable state, missing @property decorators
- Initialization: defaults not in __init__, magic numbers/strings
- Communication: polling instead of events/callbacks
- Type hints: missing annotations on public methods/functions
- Error handling: bare except, swallowed errors, no validation at boundaries
- Anti-patterns: global mutable state, hardcoded config, mutable default arguments
```

## Review Categories

### 1. Access Control & Encapsulation (CRITICAL)

| Violation | Severity | Fix |
|-----------|----------|-----|
| Public mutable attributes without @property | CRITICAL | Add @property decorator for read-only, implement setter only if controlled mutation needed |
| Missing @property for read-only state | CRITICAL | Wrap attribute access with @property decorator, remove or make setter private |
| Class-level mutable state exposed publicly | HIGH | Use class methods for controlled access, or implement singleton pattern with encapsulation |
| Instance attributes modified externally | HIGH | Encapsulate with properties, validate in setters, emit change events |

**Python Implementation:**
```python
# BAD: Unrestricted mutable public state
class Player:
    def __init__(self):
        self.health = 100  # Anyone can modify directly

# GOOD: Read-only public state
class Player:
    def __init__(self):
        self._health = 100

    @property
    def health(self) -> int:
        """Current player health (read-only)."""
        return self._health

    def take_damage(self, amount: int) -> None:
        """Controlled mutation through method."""
        if amount < 0:
            raise ValueError("Damage amount must be non-negative")
        self._health = max(0, self._health - amount)
```

### 2. Initialization Rules (CRITICAL)

| Violation | Severity | Fix |
|-----------|----------|-----|
| Defaults not set in __init__ | CRITICAL | Move all default values to __init__ method |
| Magic numbers in code | CRITICAL | Extract to named constants at module or class level |
| Magic strings for state/enums | CRITICAL | Use Enum or Literal types |
| Mutable default arguments | CRITICAL | Use None, replace in __init__ with fresh mutable object |
| Attributes defined outside __init__ | HIGH | Declare all attributes in __init__ for clarity |

**Python Implementation:**
```python
# BAD: Scattered defaults and magic values
class ApiClient:
    def fetch(self, url):
        if self.retry_count > 3:  # Magic number
            self.status = 'failed'  # Magic string, attr not in __init__

# GOOD: All defaults in __init__, named constants
class ApiClient:
    MAX_RETRY_ATTEMPTS = 3

    def __init__(self, base_url: str, timeout: int = 30):
        self._base_url = base_url
        self._timeout = timeout
        self._retry_count = 0
        self._status = ConnectionStatus.IDLE

    def fetch(self, endpoint: str) -> dict:
        if self._retry_count > self.MAX_RETRY_ATTEMPTS:
            self._status = ConnectionStatus.FAILED
```

### 3. Communication Patterns (CRITICAL)

| Violation | Severity | Fix |
|-----------|----------|-----|
| Polling loops (while/for checking state) | CRITICAL | Implement callback pattern, use signals (Qt/Django), or observer pattern |
| Direct cross-system calls (tight coupling) | HIGH | Emit events, use dependency injection, implement mediator |
| No cleanup for subscriptions/listeners | HIGH | Implement cleanup in __del__ or context manager |

**Python Implementation:**
```python
# BAD: Polling pattern
class DataMonitor:
    def monitor(self):
        while True:
            if self.data_source.has_changed():
                self.update_ui()
            time.sleep(0.1)

# GOOD: Event-driven observer pattern
from typing import Callable, List

class DataSource:
    def __init__(self):
        self._listeners: List[Callable[[dict], None]] = []

    def subscribe(self, listener: Callable[[dict], None]) -> None:
        """Subscribe to data change events."""
        self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[dict], None]) -> None:
        """Clean up subscription."""
        self._listeners.remove(listener)

    def _notify_listeners(self, data: dict) -> None:
        """Notify all subscribers of change."""
        for listener in self._listeners:
            listener(data)
```

### 4. Type Safety (HIGH)

| Violation | Severity | Fix |
|-----------|----------|-----|
| Missing type hints on public functions/methods | HIGH | Add parameter and return type annotations |
| Using Any instead of specific types | MEDIUM | Define specific types, use Protocol for duck typing |
| Missing TYPE_CHECKING imports | LOW | Guard type-hint-only imports to avoid circular deps |
| No validation for external inputs | CRITICAL | Add Pydantic models or validate at boundaries |

**Python Implementation:**
```python
# BAD: No type hints
def process_order(order, user):
    total = calculate_total(order)
    return create_invoice(user, total)

# GOOD: Full type annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import Order, User, Invoice

def process_order(order: 'Order', user: 'User') -> 'Invoice':
    """Process order and generate invoice with validation."""
    if not order.items:
        raise ValueError("Order must contain at least one item")

    total: Decimal = calculate_total(order)
    return create_invoice(user, total)
```

### 5. Error Handling (HIGH)

| Violation | Severity | Fix |
|-----------|----------|-----|
| Bare except: clause | CRITICAL | Catch specific exception types |
| Swallowed errors (pass in except) | CRITICAL | Log, re-raise, or handle explicitly |
| No input validation at boundaries | CRITICAL | Validate all external inputs at entry points |
| Missing null/None checks | HIGH | Check for None before dereferencing |
| No error context in exceptions | MEDIUM | Add context to exception messages |

**Python Implementation:**
```python
# BAD: Bare except and swallowed errors
def load_config(path):
    try:
        return json.load(open(path))
    except:
        pass

# GOOD: Specific exceptions with context
from pathlib import Path
from typing import Optional
import json

def load_config(path: Path) -> dict:
    """Load configuration from JSON file with validation."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with path.open('r') as f:
            config = json.load(f)

        if not isinstance(config, dict):
            raise ValueError(f"Config must be a JSON object, got {type(config).__name__}")

        return config

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {path}: {e}") from e
    except PermissionError as e:
        raise PermissionError(f"Cannot read config file {path}: {e}") from e
```

### 6. File Headers (REQUIRED)

| Violation | Severity | Fix |
|-----------|----------|-----|
| Missing file header | MEDIUM | Add standard header with filename, developer, date, purpose |
| Incomplete header information | LOW | Include all required fields |

**Python Implementation:**
```python
# module_name.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Implements theme management with QSettings persistence and observer pattern for theme change notifications.
```

### 7. Anti-Patterns (HIGH)

| Anti-Pattern | Severity | Replacement |
|-------------|----------|-------------|
| Global mutable state | CRITICAL | Dependency injection, context managers, or scoped state |
| Hardcoded configuration values | CRITICAL | Config files, environment variables, constants |
| Mutable default arguments (def func(items=[])) | CRITICAL | Use None, create fresh list in function body |
| Direct file path hardcoding | HIGH | Use pathlib.Path, environment variables, or config |
| Using var = var or default (masks None/False/0) | MEDIUM | Use explicit None check: var if var is not None else default |

## Examples

### Example 1: Full Audit of ThemeManager

**Input:**
```python
# Review the ThemeManager class from OwlWatcher for standards compliance
# Focus: full audit
# Severity: all

class ThemeManager:
    def __init__(self):
        self.settings = QSettings("OwlWatcher", "Settings")
        self.current_theme = self.settings.value("theme", "light")

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.settings.setValue("theme", self.current_theme)
```

**Output:**
```
VIOLATIONS FOUND: 6

[CRITICAL] Line 4: Unrestricted mutable public state
  - self.current_theme is publicly mutable
  - Fix: Make private (_current_theme), expose via @property decorator
  - Rationale: Prevents external code from modifying theme without going through controlled mutation

[HIGH] Line 6: Magic strings for state values
  - "light" and "dark" are magic strings
  - Fix: Define Enum: class Theme(str, Enum): LIGHT = "light"; DARK = "dark"
  - Rationale: Type safety, autocomplete, prevents typos

[HIGH] Line 3-4: QSettings instantiation in constructor
  - Direct instantiation creates tight coupling
  - Fix: Accept QSettings via dependency injection
  - Rationale: Enables testing with mock settings, follows 95/5 Rule

[MEDIUM] Line 1: Missing file header
  - No developer, date, or purpose documented
  - Fix: Add standard file header comment block

[MEDIUM] Line 7-13: No event emission on theme change
  - UI won't update when theme changes
  - Fix: Implement observer pattern with signal/callback for subscribers
  - Rationale: Event-driven communication, decouples theme manager from UI

[LOW] Line 4: Missing type hints
  - No return type annotation on __init__
  - Fix: Add -> None type hint
  - Rationale: Explicit contracts, better IDE support
```

### Example 2: Security-Focused Review

**Input:**
```python
# Review for security vulnerabilities
# Focus: security
# Severity: warnings+

def execute_query(table, user_input):
    query = f"SELECT * FROM {table} WHERE name = '{user_input}'"
    return db.execute(query)
```

**Output:**
```
VIOLATIONS FOUND: 3

[CRITICAL] Line 2: SQL Injection vulnerability
  - String interpolation creates unparameterized query
  - Fix: Use parameterized queries with placeholders
  - Example: db.execute("SELECT * FROM ? WHERE name = ?", (table, user_input))
  - Rationale: Prevents SQL injection attacks (OWASP Top 10)

[CRITICAL] Line 1: No input validation at boundary
  - user_input accepted without validation
  - Fix: Validate/sanitize input before use, define expected format
  - Rationale: Defense in depth, fail fast on bad input

[HIGH] Line 1: Missing type hints
  - Parameters lack type annotations
  - Fix: Add types: def execute_query(table: str, user_input: str) -> List[dict]:
  - Rationale: Type safety helps catch injection attempts at call site
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| review_depth | standard | Review thoroughness: quick (critical only), standard (high+), thorough (all) |
| focus_areas | all | Comma-separated: access_control, type_hints, error_handling, performance, security |
| severity_threshold | all | Minimum severity to report: all, warnings, critical |
| check_file_headers | true | Enforce file header standard |
| require_type_hints | true | Flag missing type hints as violations |
| check_docstrings | true | Require docstrings on public functions/classes |
| max_function_length | 50 | Warn on functions exceeding this line count |
| max_complexity | 10 | Warn on cyclomatic complexity above threshold |

## File Structure

```
python-code-reviewer/
  SKILL.md              # This skill definition
  README.md             # Quick-start guide
  resources/
    checklist.md        # Human-readable review checklist
    examples/           # Annotated before/after code examples
      access_control.py
      initialization.py
      communication.py
      error_handling.py
```

## Notes

- Private members in Python use single underscore prefix by convention: `_private_attr`
- Use `@property` decorator for read-only state exposure, not manual getter methods
- Type hints are enforced via `from __future__ import annotations` for forward references
- Mutable default arguments (`def func(items=[])`) are a common Python gotcha - always use `None` and create fresh objects in function body
- QSettings and other framework classes should be injected, not instantiated directly in constructors
- When reviewing Qt/PySide6 code, check for proper signal/slot connections and cleanup in closeEvent
- All config values (file paths, URLs, timeouts) must come from environment variables or config files, never hardcoded
- Security reviews should flag any string formatting in SQL/shell commands as CRITICAL
- Performance reviews focus on algorithmic complexity, not micro-optimizations (premature optimization is an anti-pattern)
- The 95/5 Rule applies: 95% of Python code should be reusable library/utility code, 5% project-specific glue
