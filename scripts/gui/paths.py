"""
paths.py
Developer: Marcus Daley
Date: 2026-02-20
Purpose: Centralized path resolution for OwlWatcher, supporting both
         source execution and frozen PyInstaller bundles.

When PyInstaller bundles the app, __file__ paths point to a temporary
extraction directory.  This module provides a single source of truth
for locating bundled assets regardless of execution mode.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Frozen-aware base path
# ---------------------------------------------------------------------------
# PyInstaller sets sys.frozen = True and stores extracted data in sys._MEIPASS.
# In source mode, resolve relative to this file's directory (scripts/gui/).
if getattr(sys, "frozen", False):
    _BUNDLE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    _BUNDLE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------
ASSETS_DIR: Path = _BUNDLE_DIR / "assets"
"""Directory containing SVG owl assets (owl_idle.svg, owl_alert.svg, etc.)."""

BASE_DIR: Path = Path("C:/ClaudeSkills")
"""Root directory of the Claude Skills project (watched directory)."""

CONFIG_PATH: Path = BASE_DIR / "config" / "watch_config.json"
"""Path to the watch configuration file."""

SECURITY_DIR: Path = BASE_DIR / "security"
"""Directory for security audit logs and integrity databases."""
