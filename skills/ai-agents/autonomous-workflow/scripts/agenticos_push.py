# skills/ai-agents/autonomous-workflow/scripts/agenticos_push.py
# Marcus Daley — 2026-05-01 — Fire-and-forget event broadcast to AgenticOS

import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import requests
from requests.exceptions import RequestException

_logger = logging.getLogger(__name__)
_TIMEOUT_S = 2

# Route detection cache: maps base_url -> "/events" or "/state"
_route_cache: dict[str, str] = {}


class EventType(str, Enum):
    WORKFLOW_STARTED = "workflow.started"
    PHASE_STARTED = "workflow.phase_started"
    PHASE_COMPLETE = "workflow.phase_complete"
    VOTE_CAST = "workflow.vote_cast"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_FAILED = "workflow.failed"


def build_event_payload(
    event_type: EventType,
    workflow_id: str,
    extra: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event": event_type.value,
        "workflow_id": workflow_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


def push_event(
    event_type: EventType,
    workflow_id: str,
    base_url: str | None = None,
    extra: dict[str, Any] | None = None,
) -> bool:
    """POST event to AgenticOS. Returns True on success, False on any failure.
    Never raises — AgenticOS unavailability must not block workflow execution.
    Falls back to /state route if /events is not available."""
    resolved_base = (base_url or os.environ.get("AGENTICOS_URL", "http://localhost:8000")).rstrip("/")
    payload = build_event_payload(event_type, workflow_id, extra or {})
    try:
        route = _get_route(resolved_base)
        if route == "/events":
            resp = requests.post(f"{resolved_base}/events", json=payload, timeout=_TIMEOUT_S)
        else:
            resp = requests.post(f"{resolved_base}/state", json={"workflow_event": payload}, timeout=_TIMEOUT_S)
        resp.raise_for_status()
        return True
    except Exception as exc:
        _logger.debug("AgenticOS push failed (non-blocking): %s", exc)
        return False


def _get_route(base_url: str) -> str:
    """Detect which route AgenticOS supports; cache result per base_url."""
    if base_url in _route_cache:
        return _route_cache[base_url]
    try:
        # Use OPTIONS to probe without sending data
        resp = requests.options(f"{base_url}/events", timeout=_TIMEOUT_S)
        if resp.status_code in (404, 405):
            _route_cache[base_url] = "/state"
        else:
            _route_cache[base_url] = "/events"
    except Exception:
        # Connection failed entirely — default to /events, will fail gracefully later
        _route_cache[base_url] = "/events"
    return _route_cache[base_url]
