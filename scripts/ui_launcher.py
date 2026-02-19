"""
WPF UI launcher for the Claude Skills sync system.

Loads XAML templates via pythonnet (Python.NET) and presents a themed progress
dialog when sync operations occur.  Falls back to a console-based UI when
pythonnet is not available.

Integration
-----------
Called by broadcaster.py to show pending changes and collect user decisions.

    from ui_launcher import show_sync_dialog
    accepted = show_sync_dialog(changes)
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
UI_TEMPLATES_DIR = BASE_DIR / "UI_Templates"
PROGRESS_BAR_XAML = UI_TEMPLATES_DIR / "progress-bar-template.xaml"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("ui_launcher")

# ---------------------------------------------------------------------------
# WPF availability check
# ---------------------------------------------------------------------------
_wpf_available: bool | None = None


def _check_wpf() -> bool:
    """Check whether pythonnet and WPF are available."""
    global _wpf_available
    if _wpf_available is not None:
        return _wpf_available

    try:
        import clr  # type: ignore[import-untyped]
        clr.AddReference("PresentationFramework")
        clr.AddReference("PresentationCore")
        clr.AddReference("WindowsBase")
        _wpf_available = True
    except Exception as exc:
        logger.debug("WPF not available: %s", exc)
        _wpf_available = False

    return _wpf_available


# ---------------------------------------------------------------------------
# WPF window helper
# ---------------------------------------------------------------------------

def _load_xaml_window(xaml_path: Path) -> Any:
    """Load a WPF Window from a XAML file.

    Returns the parsed Window object ready for data binding.
    """
    import clr  # type: ignore[import-untyped]
    from System.IO import StreamReader  # type: ignore[import-untyped]
    from System.Windows.Markup import XamlReader  # type: ignore[import-untyped]

    with open(str(xaml_path), "r", encoding="utf-8") as f:
        xaml_content = f.read()

    # Remove x:Key and x:Name attributes that require a compilation context
    # (XamlReader.Parse handles anonymous XAML).
    window = XamlReader.Parse(xaml_content)
    return window


class SyncDialogViewModel:
    """Simple data context for the progress-bar XAML template.

    Exposes properties that match the {Binding} paths in
    progress-bar-template.xaml.
    """

    def __init__(self, changes: list[dict[str, str]]) -> None:
        self._changes = changes
        self._accepted: bool | None = None

        # Bound properties
        self.WindowTitle = "Syncing Skills..."
        self.HeaderText = "Sync Preview"
        self.CurrentFileName = "waiting..."
        self.ProgressPercent = 0.0
        self.StatusText = f"{len(changes)} file(s) pending"
        self.FileCountText = f"{len(changes)} files"
        self.ElapsedText = ""
        self.IsComplete = True

    @property
    def accepted(self) -> bool | None:
        """User decision: True = accept, False = cancel, None = pending."""
        return self._accepted

    def on_accept(self, sender: Any = None, e: Any = None) -> None:
        self._accepted = True

    def on_cancel(self, sender: Any = None, e: Any = None) -> None:
        self._accepted = False


def _build_file_change_items(changes: list[dict[str, str]]) -> Any:
    """Convert change dicts to a .NET ObservableCollection for the ListView."""
    from System.Collections.ObjectModel import ObservableCollection  # type: ignore[import-untyped]
    from System.Dynamic import ExpandoObject  # type: ignore[import-untyped]

    collection = ObservableCollection[object]()

    for change in changes:
        item = ExpandoObject()
        item_dict = dict(item)  # type: ignore[arg-type]
        change_type = change.get("change_type", change.get("action", "Modified"))
        file_path = change.get("file_path", change.get("file", "unknown"))

        # ExpandoObject acts as a dynamic dictionary.
        item.ChangeType = change_type  # type: ignore[attr-defined]
        item.FilePath = file_path  # type: ignore[attr-defined]
        collection.Add(item)

    return collection


def _show_wpf_dialog(changes: list[dict[str, str]]) -> bool:
    """Show the WPF progress dialog and return the user's decision.

    Must be called from an STA thread (or will create one).
    """
    from System.Windows import Application, Window  # type: ignore[import-untyped]

    window = _load_xaml_window(PROGRESS_BAR_XAML)
    vm = SyncDialogViewModel(changes)

    # Set data context for bindings.
    window.DataContext = vm

    # Wire up Accept/Cancel buttons by finding them in the visual tree.
    _wire_button(window, "Accept", vm.on_accept, close_window=True)
    _wire_button(window, "Cancel", vm.on_cancel, close_window=True)

    # Populate the file changes list.
    file_list = _find_element(window, "FileChangesList")
    if file_list is not None:
        file_list.ItemsSource = _build_file_change_items(changes)

    # Show as modal dialog.
    window.ShowDialog()

    return vm.accepted is True


def _wire_button(
    window: Any,
    content_text: str,
    handler: Any,
    close_window: bool = False,
) -> None:
    """Find a Button by its Content text and wire up a Click handler."""
    from System.Windows.Controls import Button  # type: ignore[import-untyped]

    def _search(element: Any) -> Any:
        if isinstance(element, Button):
            try:
                if str(element.Content) == content_text:
                    return element
            except Exception:
                pass
        # Recurse into children.
        try:
            from System.Windows.Media import VisualTreeHelper  # type: ignore[import-untyped]
            count = VisualTreeHelper.GetChildrenCount(element)
            for i in range(count):
                child = VisualTreeHelper.GetChild(element, i)
                result = _search(child)
                if result is not None:
                    return result
        except Exception:
            pass
        return None

    # The visual tree is only built after the window is loaded, so we
    # use the Loaded event to defer the search.
    def _on_loaded(sender: Any, e: Any) -> None:
        btn = _search(window)
        if btn is not None:
            def _click(s: Any, ev: Any) -> None:
                handler(s, ev)
                if close_window:
                    window.Close()
            btn.Click += _click
        else:
            logger.debug("Button '%s' not found in visual tree", content_text)

    window.Loaded += _on_loaded


def _find_element(window: Any, name: str) -> Any:
    """Find a named element in the XAML logical tree."""
    try:
        element = window.FindName(name)
        return element
    except Exception:
        return None


def _run_on_sta_thread(func: Any, *args: Any) -> Any:
    """Run *func* on a new STA thread and return its result."""
    result_holder: list[Any] = [None]
    error_holder: list[Exception | None] = [None]

    def _wrapper() -> None:
        try:
            result_holder[0] = func(*args)
        except Exception as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=_wrapper)
    thread.daemon = True
    # pythonnet requires STA for WPF.
    try:
        import clr  # type: ignore[import-untyped]
        thread.SetApartmentState(clr.System.Threading.ApartmentState.STA)  # type: ignore[attr-defined]
    except Exception:
        pass
    thread.start()
    thread.join(timeout=300)  # 5 minute timeout.

    if error_holder[0] is not None:
        raise error_holder[0]
    return result_holder[0]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def show_sync_dialog(changes: list[dict[str, str]]) -> bool:
    """Show the sync dialog and return the user's decision.

    Tries WPF first. Falls back to console UI if pythonnet is not installed.

    Parameters
    ----------
    changes:
        List of dicts with keys ``change_type`` (Added/Modified/Deleted)
        and ``file_path``.

    Returns True if the user accepted the sync, False if cancelled.
    """
    if not changes:
        logger.info("No changes to display.")
        return False

    if _check_wpf():
        logger.info("Launching WPF sync dialog with %d change(s)...", len(changes))
        try:
            return _run_on_sta_thread(_show_wpf_dialog, changes)
        except Exception as exc:
            logger.warning("WPF dialog failed (%s), falling back to console.", exc)

    # Fallback to console UI.
    logger.info(
        "pythonnet/WPF not available. Using console fallback. "
        "Install pythonnet for the full graphical UI: pip install pythonnet"
    )
    from ui_console_fallback import show_sync_ui
    return show_sync_ui(changes)


# ---------------------------------------------------------------------------
# CLI entry point (for testing)
# ---------------------------------------------------------------------------

def main() -> None:
    """Launch the sync dialog with sample data for testing."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    sample_changes = [
        {"change_type": "Modified", "file_path": "Example_Skills/game-dev-helper/SKILL.md"},
        {"change_type": "Added", "file_path": "Example_Skills/new-skill/SKILL.md"},
        {"change_type": "Added", "file_path": "Example_Skills/new-skill/README.md"},
        {"change_type": "Deleted", "file_path": "Example_Skills/old-skill/SKILL.md"},
        {"change_type": "Modified", "file_path": "Skill_Creator/SKILL.md"},
    ]

    accepted = show_sync_dialog(sample_changes)
    print(f"\nUser decision: {'ACCEPTED' if accepted else 'CANCELLED'}")


if __name__ == "__main__":
    main()
