# agent_event_bus.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Typed event dispatch bus for inter-agent communication

from __future__ import annotations
import logging
import threading
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Callable

from scripts.agent_events import AgentEvent

logger = logging.getLogger("agent.event_bus")

# Sentinel type for wildcard subscriptions (receive ALL events)
_WILDCARD = type("_WILDCARD", (), {})

# Maximum audit log entries before oldest are discarded
_AUDIT_LOG_CAPACITY: int = 1000


class EventBus:
    """Typed event dispatch bus for inter-agent communication.

    Handlers subscribe to specific event classes. Publishing an event
    dispatches to all handlers registered for that exact type PLUS
    any wildcard (*) handlers. Thread-safe via reentrant lock.
    """

    def __init__(self) -> None:
        self._lock: threading.RLock = threading.RLock()
        self._handlers: dict[type, list[Callable]] = defaultdict(list)
        self._audit_log: list[dict[str, Any]] = []

    def subscribe(self, event_type: type | None, handler: Callable) -> None:
        """Register a handler for a specific event type.

        Pass event_type=None for wildcard subscription (receives all events).
        """
        with self._lock:
            key = _WILDCARD if event_type is None else event_type
            if handler not in self._handlers[key]:
                self._handlers[key].append(handler)
                logger.debug(
                    "Subscribed handler %s to %s",
                    getattr(handler, "__qualname__", str(handler)),
                    "WILDCARD" if key is _WILDCARD else key.__name__,
                )

    def unsubscribe(self, event_type: type | None, handler: Callable) -> None:
        """Remove a handler for a specific event type."""
        with self._lock:
            key = _WILDCARD if event_type is None else event_type
            handlers = self._handlers.get(key, [])
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, event: AgentEvent) -> None:
        """Dispatch event to exact-type handlers + wildcard handlers.

        Handler exceptions are caught and logged — one bad handler
        does not prevent others from receiving the event.
        """
        with self._lock:
            exact_handlers = list(self._handlers.get(type(event), []))
            wildcard_handlers = list(self._handlers.get(_WILDCARD, []))
            self._append_audit(event)

        for handler in exact_handlers + wildcard_handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Handler %s failed for event %s",
                    getattr(handler, "__qualname__", str(handler)),
                    type(event).__name__,
                )

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent audit entries (newest first)."""
        with self._lock:
            return list(reversed(self._audit_log[-limit:]))

    def clear(self) -> None:
        """Remove all handlers and audit entries."""
        with self._lock:
            self._handlers.clear()
            self._audit_log.clear()

    @property
    def handler_count(self) -> int:
        """Total number of registered handlers across all event types."""
        with self._lock:
            return sum(len(h) for h in self._handlers.values())

    def _append_audit(self, event: AgentEvent) -> None:
        """Add event to bounded audit log, discarding oldest if at capacity."""
        entry = {
            "event_type": type(event).__name__,
            "event_id": event.event_id,
            "timestamp": event.timestamp,
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > _AUDIT_LOG_CAPACITY:
            overflow = len(self._audit_log) - _AUDIT_LOG_CAPACITY
            del self._audit_log[:overflow]
