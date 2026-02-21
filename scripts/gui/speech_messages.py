# speech_messages.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Personality injection via randomized owl speech bubbles with occasional humor

"""
Speech bubble message pools for the OwlWatcher mascot.

Each owl state has a pool of ambient messages. ``get_message(state)``
picks one at random with a small chance of returning a humorous variant.

Usage::

    from gui.speech_messages import get_message
    owl.say(get_message("scanning"))
"""

from __future__ import annotations

import random

# ---------------------------------------------------------------------------
# Message pools per state (normal + rare humor)
# ---------------------------------------------------------------------------

_MESSAGES: dict[str, list[str]] = {
    "sleeping": [
        "Zzz...",
        "Dreaming of safe files...",
        "Shhh... owl is resting.",
        "All quiet on the western drive.",
    ],
    "waking": [
        "Good morning! Stretching my wings...",
        "Booting up my owl senses...",
        "Rise and scan!",
        "*yawns* Ready for duty.",
    ],
    "idle": [
        "Standing by.",
        "Waiting patiently.",
        "All quiet here.",
        "Ready when you are.",
    ],
    "scanning": [
        "Scanning your files...",
        "Watching for changes...",
        "Eyes on every folder.",
        "Keeping watch diligently.",
        "All directories accounted for.",
    ],
    "curious": [
        "Hmm, what's this?",
        "Something caught my eye...",
        "That's interesting...",
        "Let me take a closer look.",
    ],
    "alert": [
        "Changes detected!",
        "Something has changed.",
        "New activity spotted.",
        "Files in motion!",
    ],
    "alarm": [
        "Security alert!",
        "Potential threat detected!",
        "Warning -- suspicious activity!",
        "Red alert! Investigating now.",
    ],
    "proud": [
        "All clear! Great job.",
        "Everything checks out.",
        "Integrity verified!",
        "Clean sweep -- well done.",
    ],
}

# Rare messages (5% chance) -- keyed by state
_RARE_MESSAGES: dict[str, list[str]] = {
    "sleeping": [
        "Do owls count sheep? Asking for a friend.",
    ],
    "waking": [
        "Coffee? I run on pure vigilance.",
    ],
    "idle": [
        "I could reorganize your desktop... just saying.",
        "Is it weird that I enjoy watching files?",
    ],
    "scanning": [
        "I've seen things you wouldn't believe. Mostly .tmp files.",
        "One does not simply modify a file unnoticed.",
    ],
    "curious": [
        "My spidey senses are tingling... wait, wrong animal.",
    ],
    "alert": [
        "Somebody touched the files. I saw it. I see everything.",
    ],
    "alarm": [
        "This is NOT a drill! ...probably.",
    ],
    "proud": [
        "Another day, another clean audit. I'm basically a superhero.",
    ],
}

_RARE_CHANCE = 0.05  # 5% chance of humor message


def get_message(state: str) -> str:
    """Return a random speech bubble message for the given owl state.

    Parameters
    ----------
    state:
        One of the 8 owl states.

    Returns
    -------
    str
        A message string suitable for ``owl.say()``.
    """
    # Try rare pool first
    if random.random() < _RARE_CHANCE:
        rare_pool = _RARE_MESSAGES.get(state)
        if rare_pool:
            return random.choice(rare_pool)

    pool = _MESSAGES.get(state)
    if not pool:
        return ""
    return random.choice(pool)


def get_alert_message(level: str, detail: str = "") -> str:
    """Return a specific alert message (not randomized).

    Parameters
    ----------
    level:
        Alert severity (``"INFO"``, ``"WARNING"``, ``"CRITICAL"``).
    detail:
        Optional detail text to include.

    Returns
    -------
    str
        Alert-specific message for ``owl.say()``.
    """
    if level == "CRITICAL":
        base = "CRITICAL: "
    elif level == "WARNING":
        base = "Warning: "
    else:
        base = ""
    return f"{base}{detail}" if detail else get_message("alarm" if level == "CRITICAL" else "alert")
