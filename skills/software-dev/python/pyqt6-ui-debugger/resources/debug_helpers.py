"""
File: debug_helpers.py
Developer: Marcus Daley
Date: 2026-02-24
Purpose: Reusable debugging functions for PyQt6 UI troubleshooting

Usage:
    from debug_helpers import dump_widget_tree, check_size_constraints, trace_signals

    # Dump entire widget hierarchy
    dump_widget_tree(main_window)

    # Check size constraints for a specific widget
    check_size_constraints(problematic_widget)

    # Trace signal emissions
    trace_signals(button, 'clicked')
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import QObject


def dump_widget_tree(widget: QWidget, indent: int = 0, verbose: bool = False) -> None:
    """
    Print widget hierarchy with visibility and size information.

    Args:
        widget: Root widget to start dumping from
        indent: Current indentation level (used for recursion)
        verbose: If True, show additional details like geometry and policies
    """
    # Basic info
    info = (f"{'  ' * indent}{widget.__class__.__name__} - "
            f"Visible: {widget.isVisible()}, "
            f"Size: {widget.size()}, "
            f"Pos: {widget.pos()}")

    # Verbose info
    if verbose:
        policy = widget.sizePolicy()
        info += (f"\n{'  ' * indent}  "
                f"Min: {widget.minimumSize()}, "
                f"Max: {widget.maximumSize()}, "
                f"Hint: {widget.sizeHint()}, "
                f"Policy: H={_policy_name(policy.horizontalPolicy())}, "
                f"V={_policy_name(policy.verticalPolicy())}")

    print(info)

    # Recurse through children
    for child in widget.children():
        if isinstance(child, QWidget):
            dump_widget_tree(child, indent + 1, verbose)


def check_size_constraints(widget: QWidget) -> None:
    """
    Print detailed size constraint information for a widget.

    Useful for debugging sizing issues, clipping, or layout problems.

    Args:
        widget: Widget to inspect
    """
    print(f"\n{widget.__class__.__name__} Size Constraints:")
    print(f"  Current Size: {widget.size()} (W: {widget.width()}, H: {widget.height()})")
    print(f"  Minimum Size: {widget.minimumSize()} (W: {widget.minimumWidth()}, H: {widget.minimumHeight()})")
    print(f"  Maximum Size: {widget.maximumSize()} (W: {widget.maximumWidth()}, H: {widget.maximumHeight()})")
    print(f"  Size Hint: {widget.sizeHint()}")

    policy = widget.sizePolicy()
    print(f"  Size Policy:")
    print(f"    Horizontal: {_policy_name(policy.horizontalPolicy())}")
    print(f"    Vertical: {_policy_name(policy.verticalPolicy())}")
    print(f"    Horizontal Stretch: {policy.horizontalStretch()}")
    print(f"    Vertical Stretch: {policy.verticalStretch()}")

    # Check parent size if exists
    if widget.parent():
        parent_size = widget.parent().size()
        print(f"  Parent Size: {parent_size} (W: {parent_size.width()}, H: {parent_size.height()})")

        # Highlight potential clipping
        if widget.sizeHint().width() > parent_size.width() or \
           widget.sizeHint().height() > parent_size.height():
            print(f"  ⚠ WARNING: Widget size hint exceeds parent size - potential clipping!")


def check_visibility_chain(widget: QWidget) -> None:
    """
    Print visibility status of widget and all ancestors.

    Useful for debugging widgets that should be visible but aren't.

    Args:
        widget: Widget to check
    """
    print(f"\nVisibility Chain for {widget.__class__.__name__}:")

    chain = []
    current = widget
    while current:
        chain.append((current.__class__.__name__, current.isVisible(), current.isHidden()))
        current = current.parent()

    # Print from root to target widget
    for i, (name, visible, hidden) in enumerate(reversed(chain)):
        indent = "  " * i
        status = "✓ Visible" if visible else "✗ Hidden"
        if hidden:
            status += " (explicitly hidden)"
        print(f"{indent}{name}: {status}")

    # Summary
    if all(visible for _, visible, _ in chain):
        print("\n✓ Entire visibility chain is valid")
    else:
        hidden_ancestors = [name for name, visible, _ in chain if not visible]
        print(f"\n✗ Hidden ancestors preventing visibility: {', '.join(hidden_ancestors)}")


def trace_signals(obj: QObject, signal_name: str, label: str = None) -> None:
    """
    Connect a debug tracer to a signal to log when it's emitted.

    Args:
        obj: Object containing the signal
        signal_name: Name of the signal attribute (e.g., 'clicked', 'textChanged')
        label: Optional custom label for logging (defaults to object class name)
    """
    if not hasattr(obj, signal_name):
        print(f"⚠ WARNING: {obj.__class__.__name__} has no signal '{signal_name}'")
        return

    signal = getattr(obj, signal_name)
    display_label = label or f"{obj.__class__.__name__}.{signal_name}"

    def tracer(*args, **kwargs):
        if args or kwargs:
            print(f"[SIGNAL] {display_label} emitted with args={args}, kwargs={kwargs}")
        else:
            print(f"[SIGNAL] {display_label} emitted")

    signal.connect(tracer)
    print(f"✓ Tracing signal: {display_label}")


def check_layout_info(widget: QWidget) -> None:
    """
    Print layout information for a widget.

    Args:
        widget: Widget to inspect
    """
    print(f"\n{widget.__class__.__name__} Layout Info:")

    layout = widget.layout()
    if layout is None:
        print("  No layout set")
        return

    print(f"  Layout Type: {layout.__class__.__name__}")
    print(f"  Margins: {layout.contentsMargins()}")
    print(f"  Spacing: {layout.spacing()}")
    print(f"  Widget Count: {layout.count()}")

    # List all widgets in layout
    print(f"  Widgets in layout:")
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item.widget():
            w = item.widget()
            print(f"    [{i}] {w.__class__.__name__} - Visible: {w.isVisible()}, Size: {w.size()}")
        elif item.layout():
            print(f"    [{i}] Nested layout: {item.layout().__class__.__name__}")
        else:
            print(f"    [{i}] Spacer or other item")


def compare_sizes(widget: QWidget, expected_width: int = None, expected_height: int = None) -> None:
    """
    Compare widget's current size to expected dimensions.

    Args:
        widget: Widget to check
        expected_width: Expected width in pixels
        expected_height: Expected height in pixels
    """
    current = widget.size()
    print(f"\n{widget.__class__.__name__} Size Comparison:")

    if expected_width is not None:
        width_diff = current.width() - expected_width
        width_status = "✓" if width_diff == 0 else ("⚠" if abs(width_diff) < 10 else "✗")
        print(f"  Width: {current.width()} px (expected {expected_width} px) "
              f"{width_status} Diff: {width_diff:+d} px")

    if expected_height is not None:
        height_diff = current.height() - expected_height
        height_status = "✓" if height_diff == 0 else ("⚠" if abs(height_diff) < 10 else "✗")
        print(f"  Height: {current.height()} px (expected {expected_height} px) "
              f"{height_status} Diff: {height_diff:+d} px")


def _policy_name(policy: QSizePolicy.Policy) -> str:
    """Convert QSizePolicy.Policy enum to readable string."""
    policy_names = {
        QSizePolicy.Policy.Fixed: "Fixed",
        QSizePolicy.Policy.Minimum: "Minimum",
        QSizePolicy.Policy.Maximum: "Maximum",
        QSizePolicy.Policy.Preferred: "Preferred",
        QSizePolicy.Policy.Expanding: "Expanding",
        QSizePolicy.Policy.MinimumExpanding: "MinimumExpanding",
        QSizePolicy.Policy.Ignored: "Ignored"
    }
    return policy_names.get(policy, f"Unknown({policy})")


# Example usage
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTextEdit
    import sys

    app = QApplication(sys.argv)

    # Create test UI
    window = QMainWindow()
    window.setWindowTitle("PyQt6 Debug Helper Demo")

    central = QWidget()
    layout = QVBoxLayout(central)

    button = QPushButton("Test Button")
    text_edit = QTextEdit()

    layout.addWidget(button)
    layout.addWidget(text_edit)

    window.setCentralWidget(central)
    window.resize(600, 400)
    window.show()

    # Demonstrate debug functions
    print("=== Widget Tree ===")
    dump_widget_tree(window, verbose=True)

    print("\n=== Button Size Constraints ===")
    check_size_constraints(button)

    print("\n=== Button Layout Info ===")
    check_layout_info(central)

    print("\n=== Button Visibility Chain ===")
    check_visibility_chain(button)

    print("\n=== Trace Button Click ===")
    trace_signals(button, 'clicked', 'Test Button Click')

    sys.exit(app.exec())
