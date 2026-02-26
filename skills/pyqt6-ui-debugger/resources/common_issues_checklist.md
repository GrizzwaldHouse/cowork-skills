# PyQt6 Common Issues Checklist

Quick reference for diagnosing PyQt6 UI problems.

## Widget Not Visible

- [ ] Is `show()` called on the **top-level widget** (not the child)?
- [ ] Are all parent widgets visible? Check with `check_visibility_chain(widget)`
- [ ] Is the widget explicitly hidden? Check `widget.isHidden()`
- [ ] Is the widget's size greater than zero? Check `widget.size()`
- [ ] Is the widget behind another widget (z-order)? Try `widget.raise_()`
- [ ] Does the widget have `opacity: 0` or `visibility: hidden` in stylesheet?

## Widget Clipped or Cut Off

- [ ] Is the parent widget large enough? Check `parent.size()` vs `child.sizeHint()`
- [ ] Does the parent have a layout? Check `parent.layout() is not None`
- [ ] Are layout margins too large? Check `layout.contentsMargins()`
- [ ] Is the widget's minimum size too large? Check `widget.minimumSize()`
- [ ] Is the parent using a scroll area? Add `QScrollArea` if content exceeds bounds
- [ ] Is `setFixedSize()` on child larger than parent's available space?

## Widget Wrong Size

- [ ] Is the QSizePolicy appropriate? Check with `check_size_constraints(widget)`
  - Fixed: Widget cannot resize
  - Expanding: Widget should grow to fill space
  - Preferred: Widget can resize but prefers sizeHint()
- [ ] Is `sizeHint()` implemented for custom widgets?
- [ ] Is `minimumSize()` or `maximumSize()` too restrictive?
- [ ] Are stretch factors set correctly in layout? Check `layout.setStretch()`
- [ ] Is the parent layout distributing space correctly?

## Layout Not Working

- [ ] Is a layout actually set on the parent? Check `parent.setLayout(layout)`
- [ ] Are widgets added to the layout? Check `layout.addWidget(widget)`
- [ ] Is the correct layout type used?
  - QVBoxLayout: Vertical stacking
  - QHBoxLayout: Horizontal side-by-side
  - QGridLayout: Grid positioning
  - QFormLayout: Label-field pairs
- [ ] Are margins and spacing set? Default is 11px margin, 6px spacing
- [ ] Did you call `layout.update()` after dynamic changes?

## Signal/Slot Not Working

- [ ] Is the connection syntax correct?
  - WRONG: `signal.connect(slot())` (calls slot immediately)
  - RIGHT: `signal.connect(slot)` (passes function reference)
- [ ] Is the signal name correct? Common signals:
  - QPushButton: `clicked`, `pressed`, `released`
  - QLineEdit: `textChanged`, `editingFinished`, `returnPressed`
  - QCheckBox: `stateChanged`, `toggled`
- [ ] Is the slot raising an exception? Wrap in try/except to check
- [ ] Is the object still alive? Check if widget was deleted
- [ ] For lambdas, are variables captured correctly?
  - WRONG: `connect(lambda: self.func(i))` (i captured by reference)
  - RIGHT: `connect(lambda val=i: self.func(val))` (i captured by value)

## Stylesheet Not Applying

- [ ] Is the stylesheet syntax valid? Check for typos
- [ ] Is specificity correct? More specific selectors override general ones
  - General: `QPushButton { color: red; }`
  - Specific: `QPushButton#myButton { color: blue; }` (wins)
- [ ] Is the stylesheet inherited? Child widgets inherit parent styles
- [ ] Is `qproperty-` used for custom properties?
- [ ] Did you call `widget.style().unpolish(widget)` and `widget.style().polish(widget)` after dynamic changes?
- [ ] Are there conflicts with system theme? Try `QApplication.setStyle('Fusion')`

## Custom Widget Issues

- [ ] Is `super().__init__(parent)` called in `__init__()`?
- [ ] Is `sizeHint()` overridden to return appropriate size?
- [ ] Is `minimumSizeHint()` overridden?
- [ ] Is `paintEvent()` calling `super().paintEvent(event)` if needed?
- [ ] Is `update()` called after internal state changes?
- [ ] Are signals emitted at the right time?

## Performance Issues

- [ ] Is `paintEvent()` doing too much work? Use profiling
- [ ] Are signals emitted too frequently? Use debouncing
- [ ] Is the widget tree too deep? Simplify hierarchy
- [ ] Are large images scaled efficiently? Use QPixmap.scaled()
- [ ] Is text rendering slow? Cache QFont and QFontMetrics
- [ ] Are timers running faster than needed? Increase interval

## Memory Leaks

- [ ] Are parent-child relationships set correctly? Parent owns children
- [ ] Are signals disconnected when objects are destroyed?
- [ ] Are large objects (images, data) released when no longer needed?
- [ ] Are circular references avoided? (widget A references B, B references A)
- [ ] Is `deleteLater()` used instead of `del` for widgets?

## Threading Issues

- [ ] Are UI updates only on the main thread? Use `QMetaObject.invokeMethod`
- [ ] Are long-running tasks in QThread, not main thread?
- [ ] Are thread-safe signals used for cross-thread communication?
- [ ] Is shared data protected with QMutex?

## Debug Commands

### Check Widget Hierarchy
```python
from debug_helpers import dump_widget_tree
dump_widget_tree(main_window, verbose=True)
```

### Check Size Constraints
```python
from debug_helpers import check_size_constraints
check_size_constraints(problematic_widget)
```

### Check Visibility Chain
```python
from debug_helpers import check_visibility_chain
check_visibility_chain(invisible_widget)
```

### Trace Signals
```python
from debug_helpers import trace_signals
trace_signals(button, 'clicked')
```

### Check Layout Info
```python
from debug_helpers import check_layout_info
check_layout_info(container_widget)
```

## Qt Inspector (Advanced)

### Linux (with Gammaray)
```bash
sudo apt install gammaray
gammaray ./your_app.py
```

### Windows (with Qt Creator)
- Open project in Qt Creator
- Run in Debug mode
- Use "QML/Widget Debugger" view

### Mac (with Qt Inspector)
```bash
brew install gammaray
gammaray ./your_app.py
```

## Environment Variables for Debugging

```bash
# Enable Qt debug output
export QT_LOGGING_RULES="*.debug=true"

# Show widget paint rectangles
export QT_DEBUG_BACKINGSTORE=1

# Log layout calculations
export QT_DEBUG_LAYOUTS=1

# Show font rendering info
export QT_LOGGING_RULES="qt.text*=true"
```

## Common Error Messages

### "QWidget: Must construct a QApplication before a QWidget"
**Cause**: Creating widgets before `QApplication(sys.argv)`
**Fix**: Create `QApplication` first

### "RuntimeError: wrapped C/C++ object of type ... has been deleted"
**Cause**: Accessing widget after parent deleted it
**Fix**: Check if widget exists before accessing, or keep reference

### "QPixmap: It is not safe to use pixmaps outside the GUI thread"
**Cause**: Creating QPixmap in worker thread
**Fix**: Use QImage in thread, convert to QPixmap in main thread

### "QPainter::begin: Paint device returned engine == 0, type: 1"
**Cause**: Painting on invalid device or at wrong time
**Fix**: Ensure painting only in paintEvent() on valid widget

### "QLayout: Attempting to add QLayout ... to QWidget ..., which already has a layout"
**Cause**: Setting layout twice on same widget
**Fix**: Set layout only once, or delete old layout first

## Problem Tracker Template

```
Symptom:    [Widget not visible / Widget clipped / Signal not firing / etc.]
Root Cause: [Parent too small / Wrong size policy / Signal syntax error / etc.]
Solution:   [Increased parent height / Changed to Expanding policy / Fixed connect() / etc.]
Prevention: [Check parent size >= child size + margins / Verify size policy / Use function reference not call / etc.]
```

---

**Last Updated**: 2026-02-24
**Maintainer**: Marcus Daley
