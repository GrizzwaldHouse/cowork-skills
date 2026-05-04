# api_key_manager.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Standalone PyQt6 dialog for securely storing API keys into the
#          project .env file. Keys are never hardcoded — they live only in
#          .env (gitignored). Run standalone or import set_env_key() directly.
#          Usage: python -m AgenticOS.api_key_manager

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# .env read / write helpers (no third-party deps required)
# ---------------------------------------------------------------------------

ENV_PATH = Path(__file__).parent.parent / ".env"

# Keys managed by this dialog, in display order.
MANAGED_KEYS: list[tuple[str, str]] = [
    ("TAILSCALE_AUTH_TOKEN",  "Tailscale Auth Token"),
    ("OLLAMA_HANDOFF_MODEL",  "Ollama Handoff Model"),
    ("ANTHROPIC_API_KEY",     "Anthropic API Key"),
    ("OPENAI_API_KEY",        "OpenAI API Key"),
]


def _read_env() -> dict[str, str]:
    """Parse .env and return a key→value dict (comments and blanks ignored)."""
    result: dict[str, str] = {}
    if not ENV_PATH.exists():
        return result
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def set_env_key(key: str, value: str) -> None:
    """Write or update a single key in .env using atomic temp-then-rename.

    All other lines (including comments and blank lines) are preserved
    exactly, so running this repeatedly never degrades the file.
    """
    lines: list[str] = []
    found = False

    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped == key:
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f"{key}={value}")

    content = "\n".join(lines) + "\n"

    # Atomic write: write to temp file then rename so a crash mid-write
    # never produces a truncated .env.
    tmp = ENV_PATH.with_suffix(".env.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, ENV_PATH)


# ---------------------------------------------------------------------------
# PyQt6 dialog
# ---------------------------------------------------------------------------

COLOR_NAVY   = "#1B2838"
COLOR_GOLD   = "#C9A94E"
COLOR_DGOLD  = "#8B7435"
COLOR_PARCH  = "#F5E6C8"
COLOR_BAR    = "#0F1A24"
COLOR_INPUT  = "#0D1520"
COLOR_RED    = "#8B1A1A"

STYLESHEET = f"""
QDialog, QWidget {{
    background-color: {COLOR_NAVY};
    color: {COLOR_PARCH};
    font-family: 'Courier New', monospace;
    font-size: 11px;
}}
QLabel#title {{
    color: {COLOR_GOLD};
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 10px 14px;
    background-color: {COLOR_BAR};
    border-bottom: 1px solid {COLOR_DGOLD};
}}
QLabel {{
    color: {COLOR_PARCH};
    font-size: 10px;
    padding: 2px 0;
}}
QLineEdit {{
    background-color: {COLOR_INPUT};
    color: {COLOR_GOLD};
    border: 1px solid {COLOR_DGOLD};
    padding: 5px 8px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    selection-background-color: {COLOR_DGOLD};
}}
QLineEdit:focus {{
    border: 1px solid {COLOR_GOLD};
}}
QPushButton {{
    background-color: {COLOR_BAR};
    color: {COLOR_GOLD};
    border: 1px solid {COLOR_DGOLD};
    padding: 6px 16px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    letter-spacing: 1px;
    min-width: 80px;
}}
QPushButton:hover {{
    background-color: {COLOR_DGOLD};
    color: {COLOR_NAVY};
}}
QPushButton#save {{
    background-color: {COLOR_DGOLD};
    color: {COLOR_NAVY};
    font-weight: bold;
}}
QPushButton#save:hover {{
    background-color: {COLOR_GOLD};
}}
QCheckBox {{
    color: {COLOR_PARCH};
    spacing: 6px;
}}
QStatusBar {{
    background-color: {COLOR_BAR};
    color: {COLOR_PARCH};
    font-size: 9px;
    border-top: 1px solid {COLOR_DGOLD};
}}
"""


def run_dialog() -> None:
    """Launch the API key manager dialog."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QCheckBox,
        QStatusBar, QWidget, QFrame,
    )

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    icon_path = Path(__file__).parent / "dashboard" / "assets" / "tray-icon.ico"

    dlg = QDialog()
    dlg.setWindowTitle("AgenticOS — API Key Manager")
    dlg.setMinimumWidth(520)
    dlg.setWindowFlags(
        Qt.WindowType.Window |
        Qt.WindowType.WindowCloseButtonHint |
        Qt.WindowType.WindowTitleHint
    )
    if icon_path.exists():
        dlg.setWindowIcon(QIcon(str(icon_path)))

    root = QVBoxLayout(dlg)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    # Title bar
    title = QLabel("⚓  API KEY MANAGER")
    title.setObjectName("title")
    root.addWidget(title)

    # Form area
    form_widget = QWidget()
    form_layout = QVBoxLayout(form_widget)
    form_layout.setContentsMargins(18, 14, 18, 8)
    form_layout.setSpacing(10)

    env_data = _read_env()
    fields: dict[str, QLineEdit] = {}

    for env_key, label_text in MANAGED_KEYS:
        row_label = QLabel(label_text)
        form_layout.addWidget(row_label)

        field_row = QHBoxLayout()
        field_row.setSpacing(6)

        line = QLineEdit()
        line.setPlaceholderText(f"Enter {label_text}…")
        line.setEchoMode(QLineEdit.EchoMode.Password)
        current = env_data.get(env_key, "")
        # Show placeholder text if value looks like a placeholder
        if current and current not in ("your-secret-here", ""):
            line.setText(current)
        field_row.addWidget(line, stretch=1)

        # Toggle visibility button
        toggle = QPushButton("Show")
        toggle.setFixedWidth(52)
        toggle.setCheckable(True)

        def _make_toggle(l: QLineEdit, b: QPushButton) -> None:
            def _toggled(checked: bool) -> None:
                l.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked
                    else QLineEdit.EchoMode.Password
                )
                b.setText("Hide" if checked else "Show")
            b.toggled.connect(_toggled)

        _make_toggle(line, toggle)
        field_row.addWidget(toggle)

        form_layout.addLayout(field_row)
        fields[env_key] = line

        # Separator between keys
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLOR_DGOLD}; background: {COLOR_DGOLD};")
        sep.setFixedHeight(1)
        form_layout.addWidget(sep)

    root.addWidget(form_widget, stretch=1)

    # Status bar
    status = QStatusBar()
    status.showMessage(f"Keys stored in: {ENV_PATH}")
    root.addWidget(status)

    # Button row
    btn_row = QHBoxLayout()
    btn_row.setContentsMargins(18, 8, 18, 14)
    btn_row.setSpacing(8)
    btn_row.addStretch()

    btn_cancel = QPushButton("Cancel")
    btn_save   = QPushButton("Save Keys")
    btn_save.setObjectName("save")

    btn_row.addWidget(btn_cancel)
    btn_row.addWidget(btn_save)
    root.addLayout(btn_row)

    def _save() -> None:
        saved = []
        skipped = []
        for env_key, label_text in MANAGED_KEYS:
            value = fields[env_key].text().strip()
            if value:
                set_env_key(env_key, value)
                saved.append(label_text)
            else:
                skipped.append(label_text)

        parts = []
        if saved:
            parts.append(f"Saved: {', '.join(saved)}")
        if skipped:
            parts.append(f"Skipped (empty): {', '.join(skipped)}")
        status.showMessage(" | ".join(parts))

        if saved:
            # Brief confirmation then close
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1200, dlg.accept)

    btn_save.clicked.connect(_save)
    btn_cancel.clicked.connect(dlg.reject)

    dlg.exec()


def main() -> None:
    run_dialog()


if __name__ == "__main__":
    main()
