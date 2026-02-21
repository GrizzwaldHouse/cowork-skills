# paths.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Centralized path constants for GUI modules to avoid hardcoding and support flexible deployment

"""
Path constants for the OwlWatcher GUI.

Provides BASE_DIR (project root) and ASSETS_DIR (GUI assets) to all modules.
"""

from __future__ import annotations

from pathlib import Path

# Project root (C:\ClaudeSkills)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# GUI assets directory (scripts/gui/assets/)
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
