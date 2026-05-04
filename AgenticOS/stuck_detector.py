# stuck_detector.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Pure functions that classify an agent as stuck, looping, or
#          silently failing based on its recent transition history. The
#          functions in this module are deliberately stateless: they take
#          the inputs they need, return a boolean, and never own a timer
#          or background task. The session_bridge invokes them on every
#          discovery cycle so the timing source is the discovery scan,
#          not a polling loop here.
#
# Why pure functions: every condition this module detects has the same
# shape -- "given recent history, is this agent in a degenerate state?"
# Pulling those checks out of the bridge keeps the policy reviewable in
# one file and makes unit testing trivial.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from AgenticOS.config import (
    LOOP_IDENTICAL_THRESHOLD,
    LOOP_WINDOW_SIZE,
    STUCK_IDLE_THRESHOLD_S,
)


# ---------------------------------------------------------------------------
# Idle / stuck detection
# ---------------------------------------------------------------------------

def is_stuck(
    last_progress_at: Optional[datetime],
    now: datetime,
    threshold_s: int = STUCK_IDLE_THRESHOLD_S,
) -> bool:
    """Return True iff the agent has not made forward progress in the
    last ``threshold_s`` seconds.

    A None ``last_progress_at`` means "the bridge has never observed
    progress for this agent yet" -- treated as not-stuck so a brand-new
    agent does not flash red on its first frame. The caller is expected
    to set last_progress_at on the first observation and update it on
    every subsequent forward-progress event.
    """
    if last_progress_at is None:
        # Never observed progress yet; cannot be stuck by definition.
        return False

    # If callers pass naive datetimes by mistake, normalise to UTC so the
    # subtraction does not raise. Cheaper than asserting and clearer than
    # silently returning False.
    if last_progress_at.tzinfo is None:
        last_progress_at = last_progress_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    elapsed = (now - last_progress_at).total_seconds()
    return elapsed >= float(threshold_s)


# ---------------------------------------------------------------------------
# Tight-loop detection
# ---------------------------------------------------------------------------

def is_looping(
    timeline: Iterable[dict[str, Any]],
    window: int = LOOP_WINDOW_SIZE,
    threshold: int = LOOP_IDENTICAL_THRESHOLD,
) -> bool:
    """Return True iff the last ``window`` timeline entries contain at
    least ``threshold`` identical (kind, agent) tuples.

    Two design decisions worth calling out:

    1. We compare on a small key tuple (kind, agent) rather than the
       full entry. Tool calls often differ in tiny argument fields even
       though the agent is doing the same thing; we want "this agent
       keeps invoking the same tool" to count as a loop.

    2. ``threshold == window`` would require literally every entry to
       match. We default both to 5 in config so that is the policy, but
       leaving the parameters separate lets the bridge tune one without
       the other if Cowork's timeline shape changes.
    """
    # Materialize once: the caller may have passed a generator.
    entries = list(timeline)

    if window <= 0 or threshold <= 0:
        # Defensive: a zero-or-negative window can never produce a loop.
        return False

    # Need at least `window` entries for the policy to apply at all.
    if len(entries) < window:
        return False

    tail = entries[-window:]

    # Count occurrences of each (kind, agent) tuple in the tail. Any
    # bucket >= threshold means the agent is looping.
    counts: dict[tuple[str, str], int] = {}
    for entry in tail:
        if not isinstance(entry, dict):
            # Malformed timeline entries cannot identify a loop.
            continue
        key = (
            str(entry.get("kind", "")),
            str(entry.get("agent", "")),
        )
        counts[key] = counts.get(key, 0) + 1
        if counts[key] >= threshold:
            return True

    return False


# ---------------------------------------------------------------------------
# Silent failure detection
# ---------------------------------------------------------------------------

def detect_silent_failure(
    mission_status: str,
    has_running_process: bool,
) -> bool:
    """Return True iff the mission file claims work is in progress but
    no live claude process is backing it.

    The two-input contract is intentional: the discovery layer already
    knows both signals (it parsed the JSON status and counted live
    processes via psutil), so this function does not need to touch the
    filesystem or call psutil itself. Keeping the inputs primitive
    makes the logic trivially testable.
    """
    # Be permissive about how Cowork spells "in progress". Future Cowork
    # builds may add new in-progress states; whitelisting is safer than
    # blacklisting here so a new not-running status does not mis-classify.
    in_progress_aliases = {"in_progress", "running", "active", "working"}
    is_in_progress = mission_status.lower() in in_progress_aliases

    # Silent failure = JSON says we're working, but no process is.
    return is_in_progress and not has_running_process
