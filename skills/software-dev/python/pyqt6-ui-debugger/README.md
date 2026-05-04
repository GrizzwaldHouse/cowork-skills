# PyQt6 UI Debugger

A systematic debugging skill for diagnosing and fixing PyQt6 user interface issues.

## Quick Start

1. **Identify the symptom**: Widget missing, clipped, wrong size, not responding?
2. **Pick the category**: Layout, Visibility, Sizing, Styling, or Signals
3. **Run the checklist**: Use category-specific debugging steps
4. **Inspect the hierarchy**: Use `dump_widget_tree()` to see the widget tree
5. **Apply the fix**: Based on root cause analysis

## Most Common Issues

### Widget Not Visible
```python
# Check visibility chain
def check_visibility(widget):
    current = widget
    while current:
        if not current.isVisible():
            print(f"Hidden: {current.__class__.__name__}")
        current = current.parent()
```

### Widget Clipped
```python
# Check parent size vs child size
print(f"Parent: {parent.size()}")
print(f"Child min: {child.minimumSize()}")
print(f"Child hint: {child.sizeHint()}")
# Fix: Increase parent size or decrease child size
```

### Widget Wrong Size
```python
# Check size policy
policy = widget.sizePolicy()
print(f"H: {policy.horizontalPolicy()}, V: {policy.verticalPolicy()}")
# Fix: Use Expanding or MinimumExpanding for flexible sizing
```

### Signal Not Firing
```python
# Common mistake
button.clicked.connect(self.handler())  # WRONG - calls handler immediately

# Correct syntax
button.clicked.connect(self.handler)  # RIGHT - passes function reference
```

## Debug Helper Functions

```python
# File: resources/debug_helpers.py

def dump_widget_tree(widget, indent=0):
    """Print widget hierarchy with visibility and size info"""
    print("  " * indent + f"{widget.__class__.__name__} - "
          f"Visible: {widget.isVisible()}, "
          f"Size: {widget.size()}, "
          f"Pos: {widget.pos()}")
    for child in widget.children():
        if hasattr(child, 'isVisible'):  # Is a QWidget
            dump_widget_tree(child, indent + 1)

def check_size_constraints(widget):
    """Verify size policy and constraints"""
    print(f"\n{widget.__class__.__name__} Size Constraints:")
    print(f"  Current: {widget.size()}")
    print(f"  Minimum: {widget.minimumSize()}")
    print(f"  Maximum: {widget.maximumSize()}")
    print(f"  Hint: {widget.sizeHint()}")
    policy = widget.sizePolicy()
    print(f"  Policy H: {policy.horizontalPolicy()}")
    print(f"  Policy V: {policy.verticalPolicy()}")

def trace_signals(obj, signal_name):
    """Debug signal emissions"""
    signal = getattr(obj, signal_name)
    def tracer(*args, **kwargs):
        print(f"Signal {signal_name} emitted: args={args}, kwargs={kwargs}")
    signal.connect(tracer)
```

## When to Use This Skill

- Widget doesn't appear where expected
- Widget is clipped or cut off
- Widget won't resize properly
- Button clicks or signals not working
- Stylesheet not applying correctly
- Layout not behaving as expected

## See Also

- `SKILL.md` for full debugging methodology
- `resources/common_issues_checklist.md` for quick reference
- `resources/debug_helpers.py` for reusable debug functions

## Example Session

```
User: "My owl widget is being clipped at the bottom"

Claude (using PyQt6 UI Debugger skill):
1. Identify symptom category: Sizing issue (widget clipped)
2. Check parent size vs child size:
   - Child: OwlWidget with setFixedSize(300, 300)
   - Parent: HeaderBar with setFixedHeight(150)
3. Root cause: Parent height (150px) < child height (300px)
4. Solution: Increase parent height to 320px (300 + margins)
5. Prevention: Always verify parent size >= child min size + margins
```

## Integration with Dev Workflow

This skill follows Marcus Daley's brainstorm-first methodology:

1. **Research**: Check if Qt has built-in debugging tools (Qt Inspector, QWidget::dump())
2. **Categorize**: Layout, Visibility, Sizing, Styling, or Signals?
3. **Investigate**: Run category checklist, inspect widget tree
4. **Fix**: Apply solution based on root cause
5. **Document**: Log in Problem Tracker format (dev-workflow skill)

---

**Created**: 2026-02-24
**Developer**: Marcus Daley
**Purpose**: Systematic PyQt6 UI debugging for portfolio-quality applications
