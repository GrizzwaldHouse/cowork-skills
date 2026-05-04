# Python Code Review Checklist

Quick reference checklist for reviewing Python code against Marcus Daley's universal coding standards.

## Access Control & Encapsulation [CRITICAL]

- [ ] No public mutable attributes without `@property` decorators
- [ ] All read-only state exposed via `@property` (no manual getters)
- [ ] Private members prefixed with `_` (single underscore)
- [ ] No class-level mutable state accessible publicly
- [ ] Mutable collections returned as copies (not direct references)
- [ ] Setters validate input before mutation
- [ ] State changes emit events/callbacks (if applicable)

**Check:**
```python
# Look for: self.attribute = value (without @property)
# Look for: public attributes modified externally
# Look for: class-level lists/dicts without encapsulation
```

## Initialization Rules [CRITICAL]

- [ ] All default values set in `__init__`
- [ ] No magic numbers in code (extract to constants)
- [ ] No magic strings (use Enum or Literal types)
- [ ] No mutable default arguments (`def func(items=[])`)
- [ ] All instance attributes declared in `__init__`
- [ ] Constructor accepts config via parameters (dependency injection)
- [ ] Complex object creation uses factory methods or builder pattern

**Check:**
```python
# Look for: numeric literals (3, 100, 0.5) outside constants
# Look for: string literals ("active", "pending") for state
# Look for: def func(items=[]) - mutable default args
# Look for: self.new_attr = value outside __init__
```

## Communication Patterns [CRITICAL]

- [ ] No polling loops (`while True` checking state)
- [ ] State changes use callbacks or observer pattern
- [ ] No direct cross-system method calls (use events)
- [ ] Subscriptions cleaned up in `__del__` or context manager
- [ ] Event handlers accept data as parameters (not pulling state)

**Check:**
```python
# Look for: time.sleep() in loops checking conditions
# Look for: while/for loops polling object state
# Look for: tight coupling between unrelated classes
```

## Type Safety [HIGH]

- [ ] Type hints on all public function parameters
- [ ] Return type annotations on all public functions
- [ ] Type hints on all instance attributes (in `__init__`)
- [ ] Use specific types, not `Any` (unless truly dynamic)
- [ ] `TYPE_CHECKING` guard for type-hint-only imports
- [ ] Use `Literal`, `Enum`, or `Protocol` for constrained types
- [ ] External inputs validated with type checks at boundaries

**Check:**
```python
# Look for: def func(arg) - missing parameter types
# Look for: def func(arg: str) - missing return type
# Look for: : Any - should be specific type
# Look for: circular imports in type hints
```

## Error Handling [HIGH]

- [ ] No bare `except:` clauses
- [ ] Specific exception types caught
- [ ] No swallowed errors (`except: pass`)
- [ ] Errors logged or re-raised with context
- [ ] Input validation at system boundaries
- [ ] Null/None checks before dereferencing
- [ ] Error messages include actionable context

**Check:**
```python
# Look for: except: (bare except)
# Look for: except Exception: pass (swallowed)
# Look for: user input used without validation
# Look for: obj.attr without checking if obj is None
```

## File Structure [MEDIUM]

- [ ] File header present (filename, developer, date, purpose)
- [ ] Imports organized: stdlib, third-party, local
- [ ] Constants at module level (UPPER_CASE)
- [ ] Private functions/classes prefixed with `_`
- [ ] Public API clearly defined (`__all__` if library module)

**Check:**
```python
# Look for: missing file header comment block
# Look for: disorganized imports
# Look for: constants mixed with code
```

## Documentation [MEDIUM]

- [ ] Docstrings on all public functions/classes
- [ ] Docstrings explain WHY, not WHAT (obvious from code)
- [ ] Complex algorithms documented with rationale
- [ ] Type hints complement docstrings (don't duplicate)
- [ ] Examples provided for non-obvious usage

**Check:**
```python
# Look for: public functions without docstrings
# Look for: docstrings that just restate the code
# Look for: missing rationale for design decisions
```

## Anti-Patterns [HIGH]

- [ ] No global mutable state
- [ ] No hardcoded file paths (use pathlib.Path + config)
- [ ] No hardcoded URLs, API keys, credentials
- [ ] No `var = var or default` (use explicit `if var is None`)
- [ ] No nested functions with mutable closure state
- [ ] No god classes (classes doing too much)
- [ ] No deep inheritance hierarchies (prefer composition)

**Check:**
```python
# Look for: global variables that change
# Look for: "/path/to/file" hardcoded strings
# Look for: API_KEY = "abc123" in source
# Look for: classes with >10 public methods
```

## Security [CRITICAL]

- [ ] No SQL string interpolation (use parameterized queries)
- [ ] No shell command string formatting (`os.system(f"rm {file}")`)
- [ ] No `eval()` or `exec()` on untrusted input
- [ ] No `pickle.load()` on untrusted data
- [ ] Sensitive data not logged (passwords, tokens, PII)
- [ ] File paths sanitized before use (prevent directory traversal)
- [ ] Cryptography uses established libraries (no custom crypto)

**Check:**
```python
# Look for: f"SELECT * FROM {table}" - SQL injection
# Look for: os.system(f"cmd {input}") - command injection
# Look for: eval(user_input) - code injection
# Look for: print(password) - sensitive data in logs
```

## Performance [MEDIUM]

- [ ] No premature optimization (profile first)
- [ ] Appropriate data structures (set for membership, dict for lookup)
- [ ] No N+1 queries (database)
- [ ] Large data processed in batches/chunks
- [ ] CPU-intensive tasks use multiprocessing (not threading)
- [ ] I/O-bound tasks use async/await or threading

**Check:**
```python
# Look for: nested loops on large collections (O(n²))
# Look for: list comprehensions with side effects
# Look for: repeated database queries in loops
```

## Framework-Specific (Qt/PySide6)

- [ ] QSettings injected via constructor (not instantiated directly)
- [ ] Signals connected with proper slot signatures
- [ ] Signal connections cleaned up in closeEvent
- [ ] UI updates happen on main thread only
- [ ] Long-running tasks use QThread or QThreadPool
- [ ] Resources (icons, fonts) loaded from QResource or config

**Check:**
```python
# Look for: QSettings("app", "settings") in __init__
# Look for: signal.connect() without corresponding disconnect
# Look for: worker thread directly updating UI
```

## Python-Specific Best Practices

- [ ] Use `pathlib.Path` for file operations (not `os.path`)
- [ ] Use `with` statements for file/resource handling
- [ ] Use `@dataclass` for data containers (reduces boilerplate)
- [ ] Use `@functools.lru_cache` for expensive pure functions
- [ ] Use `contextlib.contextmanager` for custom resource managers
- [ ] Use `typing.Protocol` for structural subtyping (duck typing)

## Quick Severity Guide

| Severity | When to Use |
|----------|-------------|
| CRITICAL | Security vulnerability, data corruption risk, violates core standards |
| HIGH | Maintainability issue, coupling problem, missing required patterns |
| MEDIUM | Code quality, documentation, non-critical best practices |
| LOW | Style preferences, minor improvements, nice-to-haves |

## Review Priorities

1. **Security** - Address CRITICAL security issues first
2. **Access Control** - Fix unrestricted mutable state
3. **Error Handling** - Add validation and proper exception handling
4. **Type Safety** - Add missing type hints
5. **Communication** - Replace polling with events
6. **Documentation** - Add file headers and docstrings
7. **Refactoring** - Apply architectural improvements

## Notes

- Use this checklist for both manual and AI-assisted reviews
- Not every item applies to every file (scripts vs libraries)
- Focus on CRITICAL and HIGH severity issues for portfolio work
- Thorough reviews catch issues early, reducing technical debt
- Re-review after fixes to ensure nothing was broken
