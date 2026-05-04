# notification_policy.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Rate-limit OwlWatcher desktop notifications so audit visibility
#          stays complete while tray balloons only fire for useful signals.

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


_LEVEL_RANK: dict[str, int] = {
    "INFO": 0,
    "WARNING": 1,
    "CRITICAL": 2,
}


@dataclass(frozen=True)
class NotificationDecision:
    """Decision returned by NotificationPolicy.evaluate."""

    should_notify: bool
    title: str
    message: str
    icon_type: str
    reason: str


class NotificationPolicy:
    """Config-driven tray notification filter.

    The full alert stream still goes to the dashboard and audit log. This
    policy only controls whether a balloon notification is shown.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        policy = config.get("notification_policy", {})
        if not isinstance(policy, dict):
            policy = {}

        self._desktop_enabled = bool(policy.get("desktop_enabled", True))
        self._min_level = str(policy.get("min_level", "WARNING")).upper()
        self._cooldown_seconds = float(policy.get("cooldown_seconds", 60))
        self._critical_cooldown_seconds = float(
            policy.get("critical_cooldown_seconds", 15)
        )
        self._duplicate_window_seconds = float(
            policy.get("duplicate_window_seconds", 300)
        )
        self._max_message_chars = int(policy.get("max_message_chars", 160))

        self._last_any_at = 0.0
        self._last_by_key: dict[tuple[str, str, str], float] = {}

    def evaluate(
        self,
        alert: dict[str, Any],
        now: float | None = None,
    ) -> NotificationDecision:
        """Return whether this alert deserves a desktop notification."""
        if now is None:
            now = time.monotonic()

        level = str(alert.get("level", "INFO")).upper()
        message = str(alert.get("message", "Security alert"))
        file_path = str(alert.get("file_path", ""))

        title = f"OwlWatcher [{level}]"
        icon_type = {
            "INFO": "info",
            "WARNING": "warning",
            "CRITICAL": "critical",
        }.get(level, "info")

        if not self._desktop_enabled:
            return NotificationDecision(False, title, message, icon_type, "disabled")

        if _LEVEL_RANK.get(level, 0) < _LEVEL_RANK.get(self._min_level, 1):
            return NotificationDecision(False, title, message, icon_type, "below-min-level")

        key = (level, message, file_path)
        last_for_key = self._last_by_key.get(key)
        if (
            last_for_key is not None
            and now - last_for_key < self._duplicate_window_seconds
        ):
            return NotificationDecision(False, title, message, icon_type, "duplicate")

        cooldown = (
            self._critical_cooldown_seconds
            if level == "CRITICAL"
            else self._cooldown_seconds
        )
        if now - self._last_any_at < cooldown:
            return NotificationDecision(False, title, message, icon_type, "cooldown")

        self._last_any_at = now
        self._last_by_key[key] = now

        if len(message) > self._max_message_chars:
            message = message[: self._max_message_chars - 3] + "..."

        return NotificationDecision(True, title, message, icon_type, "accepted")
