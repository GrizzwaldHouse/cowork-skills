# owl_state_machine.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Event-driven state machine for owl mascot with auto-return transitions to prevent stuck states

"""
Owl state machine for the OwlWatcher mascot.

Manages transitions between 8 owl states with auto-timed fallbacks
and high-level command methods.  Emits ``state_changed(str)`` whenever
the owl transitions to a new state.

States
------
SLEEPING -> WAKING -> SCANNING -> (event-driven transitions)
SCANNING is the default "active watching" state.
"""

from __future__ import annotations

import logging
from enum import Enum

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger("owl_state_machine")


class OwlState(str, Enum):
    """All possible owl states."""

    SLEEPING = "sleeping"
    WAKING = "waking"
    IDLE = "idle"
    SCANNING = "scanning"
    CURIOUS = "curious"
    ALERT = "alert"
    ALARM = "alarm"
    PROUD = "proud"


# ---------------------------------------------------------------------------
# Transition table: source -> set of allowed targets
# ---------------------------------------------------------------------------
_TRANSITIONS: dict[OwlState, set[OwlState]] = {
    OwlState.SLEEPING: {OwlState.WAKING},
    OwlState.WAKING: {OwlState.SCANNING, OwlState.IDLE},
    OwlState.IDLE: {OwlState.SLEEPING, OwlState.WAKING, OwlState.SCANNING},
    OwlState.SCANNING: {
        OwlState.CURIOUS, OwlState.ALERT, OwlState.ALARM,
        OwlState.PROUD, OwlState.IDLE, OwlState.SLEEPING,
    },
    OwlState.CURIOUS: {OwlState.SCANNING, OwlState.ALERT, OwlState.ALARM},
    OwlState.ALERT: {OwlState.SCANNING, OwlState.ALARM, OwlState.PROUD, OwlState.IDLE},
    OwlState.ALARM: {OwlState.ALERT, OwlState.SCANNING},
    OwlState.PROUD: {OwlState.SCANNING, OwlState.ALERT, OwlState.ALARM},
}

# Auto-return transitions: state -> (target, delay_ms)
_AUTO_TRANSITIONS: dict[OwlState, tuple[OwlState, int]] = {
    OwlState.WAKING: (OwlState.SCANNING, 1500),
    OwlState.CURIOUS: (OwlState.SCANNING, 5000),
    OwlState.PROUD: (OwlState.SCANNING, 4000),
    OwlState.ALARM: (OwlState.ALERT, 10000),
}


class OwlStateMachine(QObject):
    """Event-driven state machine for the owl mascot.

    Signals
    -------
    state_changed(str):
        Emitted with the new state name whenever a transition occurs.
    """

    state_changed = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = OwlState.IDLE
        self._watching = False

        # Instance copy of transition table to prevent shared state mutation
        self._transitions = {k: set(v) for k, v in _TRANSITIONS.items()}

        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._on_auto_transition)
        self._auto_target: OwlState | None = None

    @property
    def state(self) -> OwlState:
        """Current owl state."""
        return self._state

    # ------------------------------------------------------------------
    # Core transition logic
    # ------------------------------------------------------------------

    def _transition(self, target: OwlState) -> bool:
        """Attempt to transition to *target*.  Returns True on success."""
        if target == self._state:
            return False

        allowed = self._transitions.get(self._state, set())
        if target not in allowed:
            logger.debug(
                "Blocked transition %s -> %s (not allowed)",
                self._state.value, target.value,
            )
            return False

        old = self._state
        self._state = target
        logger.info("Owl: %s -> %s", old.value, target.value)

        # Cancel any pending auto-transition from the old state.
        self._auto_timer.stop()
        self._auto_target = None

        # Schedule new auto-transition if the target state has one.
        auto = _AUTO_TRANSITIONS.get(target)
        if auto is not None:
            self._auto_target, delay = auto
            self._auto_timer.start(delay)

        self.state_changed.emit(target.value)
        return True

    def _on_auto_transition(self) -> None:
        """Execute a scheduled auto-return transition."""
        if self._auto_target is not None:
            target = self._auto_target
            self._auto_target = None
            self._transition(target)

    # ------------------------------------------------------------------
    # High-level commands (used by app.py)
    # ------------------------------------------------------------------

    def command_start_watching(self) -> None:
        """Watcher has started -- wake the owl from sleep/idle."""
        self._watching = True
        if self._state == OwlState.SLEEPING:
            self._transition(OwlState.WAKING)
        elif self._state == OwlState.IDLE:
            # Dynamic transition allows cold-start from IDLE without requiring sleep cycle
            self._transitions[OwlState.IDLE].add(OwlState.SCANNING)
            self._transition(OwlState.SCANNING)
        elif self._state == OwlState.WAKING:
            pass  # Already waking up; auto-timer will reach SCANNING.
        else:
            self._transition(OwlState.SCANNING)

    def command_stop_watching(self) -> None:
        """Watcher has stopped -- go to idle or sleep."""
        self._watching = False
        if self._state in (OwlState.SCANNING, OwlState.ALERT, OwlState.CURIOUS, OwlState.PROUD):
            self._transition(OwlState.IDLE)

    def command_file_event(self) -> None:
        """A normal file event was received."""
        # Most file events don't change state -- the owl stays scanning.
        # But if we're in a temporary state, nudge back to scanning.
        if self._state in (OwlState.CURIOUS, OwlState.PROUD):
            self._transition(OwlState.SCANNING)

    def command_security_alert(self, level: str) -> None:
        """A security alert was received.

        Parameters
        ----------
        level:
            ``"WARNING"`` or ``"CRITICAL"``.
        """
        if level == "CRITICAL":
            # Force transition even from states that don't normally allow it.
            if self._state != OwlState.ALARM:
                # Temporarily allow the transition.
                self._transitions.setdefault(self._state, set()).add(OwlState.ALARM)
                self._transition(OwlState.ALARM)
        else:
            if self._state not in (OwlState.ALARM,):
                self._transitions.setdefault(self._state, set()).add(OwlState.ALERT)
                self._transition(OwlState.ALERT)

    def command_unusual_event(self) -> None:
        """An unusual (but not dangerous) event was received."""
        if self._state == OwlState.SCANNING:
            self._transition(OwlState.CURIOUS)

    def command_integrity_clean(self) -> None:
        """Integrity verification passed -- owl is proud."""
        if self._state in (OwlState.SCANNING, OwlState.ALERT):
            self._transition(OwlState.PROUD)

    def command_go_to_sleep(self) -> None:
        """Put the owl to sleep (used in first-run or idle timeout)."""
        if self._state == OwlState.IDLE:
            self._transition(OwlState.SLEEPING)
        elif self._state == OwlState.SCANNING:
            self._transition(OwlState.IDLE)
