# config_manager.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Eliminate duplicate config loading code by providing single source of truth for watch_config.json

"""
Centralized configuration loading for the Claude Skills system.

Replaces duplicate ``load_config()`` implementations scattered across
``observer.py``, ``watcher_thread.py``, and ``main_window.py``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
CONFIG_PATH = BASE_DIR / "config" / "watch_config.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("config_manager")

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULTS: dict[str, Any] = {
    "watched_paths": [str(BASE_DIR)],
    "ignored_patterns": [
        "__pycache__", ".git", "*.pyc", "backups", "logs", "dist",
    ],
    "sync_interval": 5,
    "enabled_skills": [],
}


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load watch configuration from *path*, falling back to defaults.

    Missing keys are filled from ``_DEFAULTS`` so callers never need to
    handle partial config dicts.
    """
    config: dict[str, Any] = {}

    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as fh:
                config = json.load(fh)
            logger.info("Loaded config from %s", path)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read config %s: %s -- using defaults", path, exc)
    else:
        logger.warning("Config file not found at %s -- using defaults", path)

    # Merge defaults for any missing keys.
    for key, default in _DEFAULTS.items():
        config.setdefault(key, default)

    return config


def watched_paths(config: dict[str, Any] | None = None) -> list[str]:
    """Return the list of watched directories from config."""
    if config is None:
        config = load_config()
    return config.get("watched_paths", _DEFAULTS["watched_paths"])
