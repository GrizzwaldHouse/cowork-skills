# constants.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Centralize all magic numbers, colors, and config defaults to prevent scattered hardcoded values

"""
Centralized constants for the OwlWatcher GUI application.

All magic numbers, theme colors, animation durations, and configuration
defaults live here.  No PyQt6 dependency -- consumers construct QColor
and other Qt objects from these raw values.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Theme colors (hex strings)
# ---------------------------------------------------------------------------
NAVY = "#1B2838"
GOLD = "#C9A94E"
PARCHMENT = "#F5E6C8"
TEAL = "#1A3C40"
DARK_PANEL = "#0D1117"
MID_PANEL = "#162230"
HEADER_BG = "#142030"

# Alert row backgrounds
ROW_BG_INFO = DARK_PANEL
ROW_BG_WARNING = "#332D00"
ROW_BG_CRITICAL = "#3D1010"

# Alert text colors
TEXT_INFO = PARCHMENT
TEXT_WARNING = "#FFD54F"
TEXT_CRITICAL = "#FF6B6B"

# Button accents
STOP_BTN_COLOR = "#E74C3C"
PRESSED_BTN_COLOR = "#A8892F"

# Owl state label color
STATE_LABEL_COLOR = "#8899AA"

# ---------------------------------------------------------------------------
# Speech bubble
# ---------------------------------------------------------------------------
BUBBLE_BG = "#F5E6C8"
BUBBLE_TEXT = "#1B2838"
BUBBLE_BORDER = "#C9A94E"
BUBBLE_SHADOW_ALPHA = 40
BUBBLE_FONT_SIZE = 11
BUBBLE_PADDING = 10
BUBBLE_RADIUS = 10
BUBBLE_POINTER_SIZE = 8

# ---------------------------------------------------------------------------
# Animation durations (milliseconds)
# ---------------------------------------------------------------------------
FADE_IN_MS = 300
FADE_OUT_MS = 400
BUBBLE_DEFAULT_DURATION_MS = 5000

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"
MONO_FONT = "'Consolas', 'Cascadia Code', monospace"

# ---------------------------------------------------------------------------
# Window layout
# ---------------------------------------------------------------------------
MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 400
HEADER_HEIGHT = 80
OWL_HEADER_SIZE = 56
OWL_DEFAULT_SIZE = 128

# ---------------------------------------------------------------------------
# Event log
# ---------------------------------------------------------------------------
EVENT_MAX_ROWS = 1000

EVENT_TYPE_LABELS: dict[str, str] = {
    "created": "[NEW]",
    "modified": "[MOD]",
    "deleted": "[DEL]",
    "moved": "[MOV]",
}

# ---------------------------------------------------------------------------
# Status bar
# ---------------------------------------------------------------------------
UPTIME_TICK_MS = 1000

# ---------------------------------------------------------------------------
# Security engine
# ---------------------------------------------------------------------------
SUSPICIOUS_EXTENSIONS: frozenset[str] = frozenset({
    ".exe", ".dll", ".bat", ".cmd", ".ps1",
    ".vbs", ".js", ".scr", ".com", ".msi",
})

MAX_AUDIT_ENTRIES = 10_000
DEFAULT_LARGE_FILE_BYTES = 50 * 1024 * 1024  # 50 MB
BURST_THRESHOLD = 10
BURST_WINDOW_SECONDS = 5.0

# ---------------------------------------------------------------------------
# Event stream enhancements
# ---------------------------------------------------------------------------
ROW_HIGHLIGHT_MS = 200            # Fade duration for new row highlight
ROW_HIGHLIGHT_COLOR = "#2A3A1A"   # Brief green-ish highlight on insert
LEFT_BORDER_WIDTH = 4             # Severity indicator border width (px)
LEFT_BORDER_INFO = "#4CAF50"      # Green for normal events
LEFT_BORDER_WARNING = "#FFD54F"   # Gold for warnings
LEFT_BORDER_CRITICAL = "#FF6B6B"  # Red for critical alerts
TIME_CLUSTER_GAP_SECONDS = 30     # Insert separator after this gap

# File type glyphs (prepended to the Type column)
FILE_TYPE_GLYPHS: dict[str, str] = {
    ".py": "Py",
    ".json": "{}",
    ".md": "Md",
    ".svg": "Sv",
    ".exe": "!!",
    ".dll": "!!",
    ".bat": "Bt",
    ".cmd": "Cm",
    ".ps1": "Ps",
    ".js": "Js",
    ".ts": "Ts",
    ".css": "Cs",
    ".html": "Ht",
    ".yaml": "Ym",
    ".yml": "Ym",
    ".toml": "Tm",
    ".xml": "Xm",
    ".txt": "Tx",
    ".log": "Lg",
    ".csv": "Cv",
}

# ---------------------------------------------------------------------------
# Owl states -> SVG filenames
# ---------------------------------------------------------------------------
STATE_SVG_MAP: dict[str, str] = {
    "sleeping": "owl_sleeping.svg",
    "waking": "owl_waking.svg",
    "idle": "owl_idle.svg",
    "scanning": "owl_scanning.svg",
    "curious": "owl_curious.svg",
    "alert": "owl_alert.svg",
    "alarm": "owl_alarm.svg",
    "proud": "owl_proud.svg",
}

STATE_LABELS: dict[str, str] = {
    "sleeping": "Sleeping...",
    "waking": "Waking up...",
    "idle": "All quiet",
    "scanning": "Scanning files...",
    "curious": "Hmm, interesting...",
    "alert": "Changes detected",
    "alarm": "Security alert!",
    "proud": "All clear!",
}

# ---------------------------------------------------------------------------
# Owl animation parameters
# ---------------------------------------------------------------------------
BREATHING_SCALE_RANGE = 0.02       # 2% scale pulse for sleeping
BREATHING_CYCLE_MS = 4000          # Full sine cycle period
SCANNING_ROTATION_DEG = 3.0        # Head turn degrees for scanning
SCANNING_CYCLE_MS = 3000           # Full rotation oscillation cycle
BRANCH_SWAY_DEG = 0.5             # Ambient sway on branch
BRANCH_SWAY_CYCLE_MS = 6000       # Full sway oscillation cycle
ANIMATION_FPS = 30                 # Target frames per second for animations

# ---------------------------------------------------------------------------
# Ambient widget
# ---------------------------------------------------------------------------
AMBIENT_FPS = 20                   # Frames per second for star field animation
AMBIENT_FRAME_MS = 1000 // AMBIENT_FPS  # Milliseconds per frame

# ---------------------------------------------------------------------------
# System tray
# ---------------------------------------------------------------------------
TRAY_BADGE_RADIUS = 10             # Notification badge circle radius
TRAY_BADGE_PADDING = 2             # Badge border padding

# ---------------------------------------------------------------------------
# Threat scoring (main_window.py)
# ---------------------------------------------------------------------------
THREAT_CRITICAL_MULTIPLIER = 15    # Weight multiplier for critical alerts
THREAT_WARNING_MULTIPLIER = 5      # Weight multiplier for warnings

# ---------------------------------------------------------------------------
# QSettings organization/application names
# ---------------------------------------------------------------------------
QSETTINGS_ORG = "ClaudeSkills"
QSETTINGS_APP = "OwlWatcher"
