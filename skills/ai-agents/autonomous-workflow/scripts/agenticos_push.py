# skills/ai-agents/autonomous-workflow/scripts/agenticos_push.py
# Marcus Daley — 2026-05-01 — Fire-and-forget event broadcast to AgenticOS

import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import requests

_logger = logging.getLogger(__name__)
_TIMEOUT_S = 2


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
    base_url: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> bool:
    """POST event to AgenticOS. Returns True on success, False on any failure.
    Never raises — AgenticOS unavailability must not block workflow execution."""
    url = (base_url or os.environ.get("AGENTICOS_URL", "http://localhost:8000")) + "/events"
    payload = build_event_payload(event_type, workflow_id, extra or {})
    try:
        resp = requests.post(url, json=payload, timeout=_TIMEOUT_S)
        resp.raise_for_status()
        return True
    except Exception as exc:
        _logger.debug("AgenticOS push failed (non-blocking): %s", exc)
        return False
