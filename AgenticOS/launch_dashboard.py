# launch_dashboard.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: PyQt6-based launcher for the AgenticOS Command Center.
#          Opens a themed QMainWindow with an embedded QWebEngineView
#          pointed at the FastAPI state bus. Follows the OWL Watcher
#          PyQt6 pattern already proven on this machine.
#          Run from C:\ClaudeSkills: pythonw -m AgenticOS.launch_dashboard
#          System tray icon allows show/hide/quit without closing the server.

from __future__ import annotations

import logging
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

AGENTIC_OS_DIR = Path(__file__).parent
SERVER_URL = "http://127.0.0.1:7842/app"
HEALTH_URL = "http://127.0.0.1:7842/healthz"
WINDOW_TITLE = "AgenticOS Command Center"
WINDOW_MIN_W = 1200
WINDOW_MIN_H = 800
TRAY_ICON_PATH = AGENTIC_OS_DIR / "dashboard" / "assets" / "tray-icon.ico"
LOGS_DIR = AGENTIC_OS_DIR / "logs"
LAUNCHER_LOG_PATH = LOGS_DIR / "launcher.log"
SERVER_LOG_PATH = LOGS_DIR / "server.log"

# Gold-on-navy submarine theme — matches OWL Watcher palette
COLOR_DEEP_NAVY = "#1B2838"
COLOR_GOLD = "#C9A94E"
COLOR_BORDER_GOLD = "#8B7435"
COLOR_PARCHMENT = "#F5E6C8"
COLOR_STATUS_BAR = "#0F1A24"

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_DEEP_NAVY};
}}
QWidget#central {{
    background-color: {COLOR_DEEP_NAVY};
    border: 2px solid {COLOR_GOLD};
}}
QLabel#title {{
    color: {COLOR_GOLD};
    font-family: 'Courier New', monospace;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 6px 12px;
    background-color: {COLOR_STATUS_BAR};
    border-bottom: 1px solid {COLOR_BORDER_GOLD};
}}
QLabel#status {{
    color: {COLOR_PARCHMENT};
    font-family: 'Courier New', monospace;
    font-size: 10px;
    padding: 3px 8px;
    background-color: {COLOR_STATUS_BAR};
}}
QStatusBar {{
    background-color: {COLOR_STATUS_BAR};
    color: {COLOR_PARCHMENT};
    font-family: 'Courier New', monospace;
    font-size: 10px;
    border-top: 1px solid {COLOR_BORDER_GOLD};
}}
QPushButton {{
    background-color: {COLOR_STATUS_BAR};
    color: {COLOR_GOLD};
    border: 1px solid {COLOR_BORDER_GOLD};
    font-family: 'Courier New', monospace;
    font-size: 10px;
    padding: 4px 10px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background-color: {COLOR_BORDER_GOLD};
    color: {COLOR_DEEP_NAVY};
}}
"""

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(LAUNCHER_LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(stream=sys.stderr),
    ],
)
logger = logging.getLogger("AgenticOS.launch_dashboard")


def _show_error_dialog(title: str, message: str) -> None:
    """Show a small Windows error dialog when the GUI cannot start."""
    if sys.platform != "win32":
        print(f"{title}: {message}", file=sys.stderr)
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000010)
    except Exception:
        print(f"{title}: {message}", file=sys.stderr)


def _wait_for_server(timeout: int = 15) -> bool:
    """Poll /healthz until the FastAPI server is ready or timeout expires."""
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def _start_server() -> subprocess.Popen | None:
    """Start the FastAPI state bus as a subprocess if not already running."""
    import urllib.request
    import urllib.error

    # Check if server is already up
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1) as resp:
            if resp.status == 200:
                logger.info("FastAPI server already running at %s", HEALTH_URL)
                return None
    except Exception:
        pass

    # Start the server
    logger.info("Starting AgenticOS FastAPI server...")
    server_script = AGENTIC_OS_DIR / "agentic_server.py"

    # Run from ClaudeSkills parent so AgenticOS package imports resolve
    parent_dir = str(AGENTIC_OS_DIR.parent)
    server_log = SERVER_LOG_PATH.open("ab", buffering=0)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "AgenticOS.agentic_server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "7842",
        ],
        cwd=parent_dir,
        stdout=server_log,
        stderr=server_log,
    )
    return proc


def main() -> None:
    """Entry point — starts server, opens PyQt6 window with embedded browser."""
    # Start FastAPI server if needed
    server_proc = _start_server()

    # Wait for server to be ready
    logger.info("Waiting for FastAPI server to be ready...")
    if not _wait_for_server(timeout=20):
        logger.error("FastAPI server did not start within 20 seconds")
        message = (
            f"Could not connect to AgenticOS server at {HEALTH_URL}.\n\n"
            f"Server log:\n{SERVER_LOG_PATH}\n\n"
            "Manual fallback:\n"
            "cd C:\\ClaudeSkills && python -m uvicorn "
            "AgenticOS.agentic_server:app --host 127.0.0.1 --port 7842"
        )
        _show_error_dialog(WINDOW_TITLE, message)
        sys.exit(1)

    logger.info("Server ready. Launching dashboard window...")

    # Import PyQt6 here so startup errors print cleanly before Qt loads
    try:
        from PyQt6.QtCore import QUrl, Qt
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QVBoxLayout,
            QWidget, QLabel, QStatusBar, QHBoxLayout, QPushButton,
            QSystemTrayIcon, QMenu,
        )
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QStyle
    except ImportError as exc:
        logger.exception("PyQt6 launcher import failed")
        message = (
            f"PyQt6 or PyQt6-WebEngine is not installed:\n{exc}\n\n"
            "Opening the AgenticOS dashboard in your browser instead.\n\n"
            f"Launcher log:\n{LAUNCHER_LOG_PATH}"
        )
        _show_error_dialog(WINDOW_TITLE, message)
        webbrowser.open(SERVER_URL)
        if server_proc:
            server_proc.terminate()
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setStyleSheet(STYLESHEET)
    if TRAY_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(TRAY_ICON_PATH)))

    # Main window
    window = QMainWindow()
    window.setWindowTitle(WINDOW_TITLE)
    window.setMinimumSize(WINDOW_MIN_W, WINDOW_MIN_H)

    # Central widget with vertical layout
    central = QWidget()
    central.setObjectName("central")
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # Title bar
    title_bar = QWidget()
    title_layout = QHBoxLayout(title_bar)
    title_layout.setContentsMargins(0, 0, 0, 0)

    title_label = QLabel("AGENTIC OS // COMMAND CENTER")
    title_label.setObjectName("title")
    title_layout.addWidget(title_label)
    title_layout.addStretch()

    # Reload button for refreshing the WebView
    reload_btn = QPushButton("RELOAD")
    reload_btn.setFixedWidth(80)
    title_layout.addWidget(reload_btn)

    layout.addWidget(title_bar)

    # Embedded browser pointed at FastAPI-served React app
    webview = QWebEngineView()
    webview.setUrl(QUrl(SERVER_URL))
    layout.addWidget(webview, stretch=1)

    # Wire reload button
    reload_btn.clicked.connect(webview.reload)

    window.setCentralWidget(central)

    # Status bar
    status = QStatusBar()
    status.showMessage(
        f"Connected // {SERVER_URL}  |  Server PID: "
        f"{server_proc.pid if server_proc else 'external'}"
    )
    window.setStatusBar(status)

    # Clean up server subprocess when window closes
    def _on_close() -> None:
        if server_proc:
            logger.info("Stopping FastAPI server (PID %d)", server_proc.pid)
            server_proc.terminate()

    app.aboutToQuit.connect(_on_close)

    # Build tray icon — use .ico file if present, else fall back to Qt built-in
    if TRAY_ICON_PATH.exists():
        tray_icon: QIcon = QIcon(str(TRAY_ICON_PATH))
        if tray_icon.isNull():
            logger.warning("Tray icon at %s is invalid; using Qt fallback", TRAY_ICON_PATH)
            tray_icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    else:
        tray_icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

    if QSystemTrayIcon.isSystemTrayAvailable():
        tray: QSystemTrayIcon = QSystemTrayIcon(tray_icon, parent=app)
        tray.setToolTip(WINDOW_TITLE)

        # Right-click context menu
        tray_menu: QMenu = QMenu()
        action_show = tray_menu.addAction("Show Window")
        action_hide = tray_menu.addAction("Hide Window")
        tray_menu.addSeparator()
        action_keys = tray_menu.addAction("Manage API Keys")
        tray_menu.addSeparator()
        action_quit = tray_menu.addAction("Quit")

        # Wire menu actions
        action_show.triggered.connect(lambda: (window.show(), window.raise_()))
        action_hide.triggered.connect(window.hide)
        action_quit.triggered.connect(QApplication.quit)

        def _open_key_manager() -> None:
            from AgenticOS.api_key_manager import run_dialog
            run_dialog()

        action_keys.triggered.connect(_open_key_manager)

        # Double-click tray icon shows the window
        def _on_tray_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                window.show()
                window.raise_()

        tray.activated.connect(_on_tray_activated)
        tray.setContextMenu(tray_menu)
        tray.setVisible(True)
    else:
        logger.warning("System tray is not available; running window-only")

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
