---
name: pyqt6-ui-debugger
description: Diagnose and fix PyQt6 layout issues, widget visibility problems, signal/slot connections, and styling conflicts. Specializes in debugging clipping, overflow, z-index, and layout constraint issues.
user-invocable: true
---

# PyQt6 UI Debugger

> Systematic debugging methodology for PyQt6 user interface issues including layout problems, widget visibility, signal/slot connections, and styling conflicts.

## Description

Provides a structured approach to diagnosing and resolving common PyQt6 UI bugs such as widgets being clipped, hidden, or incorrectly sized. Covers layout constraint analysis, size policy debugging, parent-child hierarchy issues, and runtime inspection techniques. Specializes in problems related to QSizePolicy, sizeHint(), minimumSize(), layout margins, spacing, and z-order issues.

## Prerequisites

- PyQt6 installed (`pip install PyQt6`)
- Python 3.10+
- Basic understanding of Qt's layout system
- Qt Inspector (optional, for advanced runtime debugging)

## Usage

Follow this systematic debugging workflow when encountering PyQt6 UI issues.

### Prompt Pattern

```
I have a PyQt6 UI issue: [describe visual bug - widget missing, clipped, wrong size, etc.]

Here's the relevant code:
[paste widget/layout code]

Debug using the PyQt6 UI Debugger methodology:
1. Identify symptom category (layout, visibility, sizing, styling)
2. Check common causes for that category
3. Verify parent-child hierarchy
4. Inspect size policies and constraints
5. Provide root cause analysis and fix
```

## Debugging Methodology

### 1. Symptom Categorization

Identify which category your issue falls into:

| Category | Symptoms |
|----------|----------|
| **Layout Issues** | Widgets overlapping, incorrect positioning, not filling space |
| **Visibility Issues** | Widgets not appearing, partially visible, hidden behind others |
| **Sizing Issues** | Widgets too small/large, clipped content, incorrect aspect ratio |
| **Styling Issues** | Wrong colors, fonts, borders, background not showing |
| **Signal/Slot Issues** | Events not firing, incorrect behavior on interaction |

### 2. Common Causes by Category

#### Layout Issues

- **Parent layout not set**: Widget added but parent has no layout manager
- **Wrong layout type**: Using QHBoxLayout when QVBoxLayout needed, or vice versa
- **Stretch factors**: One widget consuming all space due to high stretch factor
- **Margins/spacing**: Layout margins or spacing set to 0 preventing proper sizing
- **Missing addWidget**: Widget created but never added to layout

**Checklist:**
```python
# Verify parent has layout
assert parent.layout() is not None

# Check if widget is in layout
assert layout.indexOf(widget) != -1

# Inspect margins
print(f"Margins: {layout.contentsMargins()}")

# Inspect spacing
print(f"Spacing: {layout.spacing()}")
```

#### Visibility Issues

- **Hidden by parent**: Widget visible but parent is hidden
- **Z-order**: Widget behind another widget (use `raise_()` to bring forward)
- **Size zero**: Widget exists but has width or height of 0
- **Clipping**: Parent too small to display child widget
- **Stylesheet hiding**: `opacity: 0` or `visibility: hidden` in stylesheet

**Checklist:**
```python
# Check visibility chain
widget_chain = []
current = widget
while current:
    widget_chain.append((current.__class__.__name__, current.isVisible()))
    current = current.parent()
print(f"Visibility chain: {widget_chain}")

# Check size
print(f"Size: {widget.size()}, Min: {widget.minimumSize()}, Hint: {widget.sizeHint()}")

# Check position
print(f"Position: {widget.pos()}, Geometry: {widget.geometry()}")
```

#### Sizing Issues

- **QSizePolicy too restrictive**: Widget has Fixed policy when it should be Expanding
- **minimumSize() too large**: Widget's minimum size exceeds parent's size
- **sizeHint() not implemented**: Custom widget doesn't override sizeHint()
- **Parent size insufficient**: Parent container too small to accommodate child
- **Aspect ratio constraints**: Widget enforcing aspect ratio that doesn't fit layout

**Checklist:**
```python
# Inspect size policy
policy = widget.sizePolicy()
print(f"Horizontal: {policy.horizontalPolicy()}, Vertical: {policy.verticalPolicy()}")

# Check size constraints
print(f"Min: {widget.minimumSize()}, Max: {widget.maximumSize()}")
print(f"Size Hint: {widget.sizeHint()}")

# Check parent size
if widget.parent():
    print(f"Parent Size: {widget.parent().size()}")
```

#### Signal/Slot Issues

- **Connection not made**: Signal emitted but no slot connected
- **Wrong signal**: Connected to wrong signal (e.g., `clicked` vs `pressed`)
- **Lambda capture**: Lambda capturing variable by reference instead of value
- **Disconnected slot**: Slot was disconnected or object deleted
- **Exception in slot**: Slot raises exception, silently failing

**Checklist:**
```python
# Verify connection (PyQt6 syntax)
widget.signal.connect(slot)

# Debug with print
def debug_slot(*args, **kwargs):
    print(f"Slot called with args={args}, kwargs={kwargs}")
widget.signal.connect(debug_slot)

# Check for exceptions
def safe_slot():
    try:
        actual_slot()
    except Exception as e:
        print(f"Slot exception: {e}")
        import traceback
        traceback.print_exc()
```

### 3. Root Cause Investigation

Use this decision tree:

```
Is the widget visible in hierarchy?
├─ NO: Check parent visibility, isHidden(), show() called?
└─ YES: Is the widget the correct size?
    ├─ NO: Check sizeHint(), minimumSize(), QSizePolicy, parent size
    └─ YES: Is the widget styled correctly?
        ├─ NO: Check stylesheet inheritance, QPalette, style conflicts
        └─ YES: Are signals/slots connected?
            ├─ NO: Verify connection syntax, check for typos
            └─ YES: Add debug logging to narrow down issue
```

### 4. Runtime Inspection Tools

#### Built-in Debugging

```python
# Enable Qt debug output
import os
os.environ['QT_LOGGING_RULES'] = '*.debug=true'

# Widget tree dump
def dump_widget_tree(widget, indent=0):
    print("  " * indent + f"{widget.__class__.__name__} - "
          f"Visible: {widget.isVisible()}, Size: {widget.size()}, "
          f"Pos: {widget.pos()}")
    for child in widget.children():
        if isinstance(child, QWidget):
            dump_widget_tree(child, indent + 1)

# Call on root widget
dump_widget_tree(main_window)
```

#### Qt Inspector (Advanced)

- Set `QT_QPA_PLATFORM=xcb` (Linux) or use built-in tools
- Run `gammaray` (KDE's Qt inspector) for live hierarchy inspection
- Use Qt Creator's debugger views

## Examples

### Example 1: Widget Clipping Due to Insufficient Parent Size

**Input:**
```
My OwlWidget is being clipped at the bottom. The owl's body is cut off.

Code:
class OwlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        # ... drawing code ...

class HeaderBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(150)  # Too small!
        layout = QHBoxLayout(self)
        self.owl_widget = OwlWidget(self)
        layout.addWidget(self.owl_widget)
```

**Root Cause Analysis:**
1. OwlWidget has `setFixedSize(300, 300)` requiring 300px height
2. HeaderBar has `setFixedHeight(150)` providing only 150px height
3. Layout cannot fit 300px widget in 150px parent
4. Result: Widget is clipped at parent's boundary

**Solution:**
```python
class HeaderBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(320)  # Accommodate 300px owl + 20px margins
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.owl_widget = OwlWidget(self)
        layout.addWidget(self.owl_widget)
```

**Prevention:**
- Always check parent size >= child minimum size + margins
- Use `sizeHint()` instead of `setFixedSize()` when possible
- Test with `dump_widget_tree()` to verify hierarchy sizes

### Example 2: Hidden Widget Due to Visibility Chain

**Input:**
```
My button isn't appearing even though I called show() on it.

Code:
container = QWidget()
layout = QVBoxLayout(container)
button = QPushButton("Click Me")
layout.addWidget(button)
button.show()  # Called but doesn't help
```

**Root Cause Analysis:**
1. Button's `show()` was called, making button visible
2. However, `container` widget was never shown
3. Qt's visibility is hierarchical: child can't be visible if parent is hidden
4. Result: Button logically visible but not displayed

**Solution:**
```python
container = QWidget()
layout = QVBoxLayout(container)
button = QPushButton("Click Me")
layout.addWidget(button)
container.show()  # Show the parent, not the child
```

**Prevention:**
- Always show the top-level widget, not individual children
- Use `dump_widget_tree()` to check visibility chain
- Remember: `widget.isVisible()` returns True even if parent is hidden

### Example 3: QSizePolicy Preventing Expansion

**Input:**
```
My text edit won't expand to fill available space.

Code:
text_edit = QTextEdit()
layout.addWidget(text_edit)
```

**Root Cause Analysis:**
1. QTextEdit's default size policy might be too restrictive
2. Layout has stretch factors favoring other widgets
3. Parent container doesn't have enough space
4. Result: Text edit stays at minimum size

**Solution:**
```python
text_edit = QTextEdit()
text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
layout.addWidget(text_edit, stretch=1)  # Add stretch factor
```

**Prevention:**
- Check size policy when widgets don't behave as expected
- Use `Expanding` or `MinimumExpanding` for widgets that should grow
- Verify stretch factors in layouts

### Example 4: Signal Not Firing Due to Wrong Connection Syntax

**Input:**
```
My button click handler isn't being called.

Code (PyQt6):
button = QPushButton("Click")
button.clicked.connect(self.on_click())  # Bug: calling the function!
```

**Root Cause Analysis:**
1. `connect()` expects a callable (function reference)
2. Code passes `self.on_click()` which calls the function immediately
3. The return value (None) is what gets connected
4. Result: No valid connection made

**Solution:**
```python
button = QPushButton("Click")
button.clicked.connect(self.on_click)  # Pass function reference, not call it
```

**Prevention:**
- Never use `()` when connecting signals unless wrapping in lambda
- Use lambda for passing arguments: `button.clicked.connect(lambda: self.on_click(42))`
- Test connections with debug print in slot

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| debug_level | quick | `quick` (checklist only), `thorough` (with tree dump), `performance` (add timing) |
| dump_tree | false | Automatically dump widget tree on issue detection |
| log_signals | false | Log all signal emissions for debugging |
| style_debug | false | Show stylesheet resolution chain |

### Usage with Configuration

```python
# Enable thorough debugging
os.environ['PYQT6_DEBUG_LEVEL'] = 'thorough'

# Dump widget tree on every layout change
def debug_layout_change():
    dump_widget_tree(main_window)

main_window.layout().changed.connect(debug_layout_change)
```

## File Structure

```
pyqt6-ui-debugger/
  SKILL.md                           # This skill definition
  README.md                          # Quick-start guide
  resources/
    debug_helpers.py                 # Reusable debugging functions
    common_issues_checklist.md       # Quick reference checklist
    qt_inspector_guide.md            # Qt Inspector setup and usage
```

## Notes

- **PyQt6 vs PyQt5**: Signal/slot syntax differs (`clicked.connect` vs `SIGNAL/SLOT` macros)
- **Stylesheet specificity**: More specific selectors override general ones (like CSS)
- **Layout invalidation**: Call `layout.update()` or `widget.updateGeometry()` after size changes
- **Event handling**: Override `paintEvent`, `resizeEvent`, etc. for custom drawing/layout
- **Thread safety**: UI updates MUST happen on main thread (use `QMetaObject.invokeMethod`)
- **Memory leaks**: Parent widgets own children; deleting parent deletes children
- **Common pitfall**: Forgetting to call `super().__init__(parent)` in custom widgets

### Quick Reference: Size Policy Values

| Policy | Horizontal Behavior | Vertical Behavior |
|--------|---------------------|-------------------|
| Fixed | Widget cannot grow or shrink | Widget cannot grow or shrink |
| Minimum | Widget can grow but not shrink | Widget can grow but not shrink |
| Maximum | Widget can shrink but not grow | Widget can shrink but not grow |
| Preferred | Widget can grow or shrink | Widget can grow or shrink |
| Expanding | Widget should grow to fill space | Widget should grow to fill space |
| MinimumExpanding | Widget can grow, has minimum size | Widget can grow, has minimum size |
| Ignored | Layout ignores sizeHint() | Layout ignores sizeHint() |

### Debugging Checklist (Quick Mode)

Use this checklist for rapid triage:

- [ ] Is `show()` called on the top-level widget?
- [ ] Does the parent have a layout manager set?
- [ ] Is the widget added to the layout?
- [ ] Does the parent have sufficient size for the child?
- [ ] Is the widget's QSizePolicy appropriate?
- [ ] Is `minimumSize()` <= parent size?
- [ ] Are signals connected with correct syntax (no `()` unless lambda)?
- [ ] Is there a stylesheet hiding the widget?
- [ ] Is the widget behind another widget (z-order issue)?
- [ ] Are all required Qt modules imported?

### Performance Profiling

For performance issues (slow redraws, lag):

```python
import time

class TimedWidget(QWidget):
    def paintEvent(self, event):
        start = time.perf_counter()
        super().paintEvent(event)
        elapsed = time.perf_counter() - start
        if elapsed > 0.016:  # Slower than 60fps
            print(f"Slow paint: {elapsed*1000:.2f}ms")
```

### Resources

- [Qt Documentation: Layout Management](https://doc.qt.io/qt-6/layout.html)
- [Qt Documentation: QSizePolicy](https://doc.qt.io/qt-6/qsizepolicy.html)
- [Qt Documentation: Debugging Techniques](https://doc.qt.io/qt-6/debug.html)
- [Stack Overflow: PyQt6 Tag](https://stackoverflow.com/questions/tagged/pyqt6)

---

**Lesson Learned Template (use when documenting PyQt6 bugs):**

```
ID:         PQ6-###
Title:      [Short descriptive title]
Date:       YYYY-MM-DD
Category:   Layout | Visibility | Sizing | Styling | Signals
Severity:   Critical | High | Medium | Low
Symptom:    [What you observed]
Root Cause: [Why it happened]
Solution:   [How you fixed it]
Prevention: [How to avoid this in the future]
Reusable:   yes (PyQt6 pattern applies to all projects)
```
