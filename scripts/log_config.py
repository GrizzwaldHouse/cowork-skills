# log_config.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Centralize logging setup to ensure consistent format across all entry points

"""
Centralized logging configuration for the Claude Skills system.

Call ``configure_logging()`` once at application entry points.  Replaces
the duplicate ``logging.basicConfig()`` calls in ``app.py``,
``observer.py``, ``broadcaster.py``, and ``main.py``.
"""

from __future__ import annotations

import logging

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"
_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Set up root logger with a consistent format.

    Safe to call multiple times -- only the first call takes effect.
    """
    global _configured
    if _configured:
        return
    logging.basicConfig(level=level, format=_FORMAT, datefmt=_DATEFMT)
    _configured = True
