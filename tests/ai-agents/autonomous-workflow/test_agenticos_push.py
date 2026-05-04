# tests/ai-agents/autonomous-workflow/test_agenticos_push.py
# Marcus Daley — 2026-05-01 — Unit tests for AgenticOS event push

import json
import pytest
import requests
from unittest.mock import patch, MagicMock

from agenticos_push import push_event, build_event_payload, EventType, clear_route_cache


def test_build_event_payload_workflow_started():
    payload = build_event_payload(
        event_type=EventType.WORKFLOW_STARTED,
        workflow_id="abc-123",
        extra={"task": "build auth system"},
    )
    assert payload["event"] == "workflow.started"
    assert payload["workflow_id"] == "abc-123"
    assert payload["task"] == "build auth system"
    assert "timestamp" in payload


def test_build_event_payload_phase_complete():
    payload = build_event_payload(
        event_type=EventType.PHASE_COMPLETE,
        workflow_id="abc-123",
        extra={"phase": "planning"},
    )
    assert payload["event"] == "workflow.phase_complete"
    assert payload["phase"] == "planning"


def test_push_event_success(requests_mock):
    requests_mock.post("http://localhost:8000/events", json={"ok": True}, status_code=200)
    result = push_event(
        event_type=EventType.WORKFLOW_STARTED,
        workflow_id="abc-123",
        base_url="http://localhost:8000",
        extra={"task": "test"},
    )
    assert result is True


def test_push_event_silent_failure_on_connection_error():
    with patch("agenticos_push.requests") as mock_requests:
        mock_requests.post.side_effect = requests.exceptions.ConnectionError("connection refused")
        result = push_event(
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id="abc-123",
            base_url="http://localhost:8000",
            extra={},
        )
    assert result is False


def test_push_event_silent_failure_on_timeout():
    with patch("agenticos_push.requests") as mock_requests:
        mock_requests.post.side_effect = requests.exceptions.Timeout()
        result = push_event(
            event_type=EventType.PHASE_COMPLETE,
            workflow_id="abc-123",
            base_url="http://localhost:8000",
            extra={"phase": "brainstorm"},
        )
    assert result is False


def test_push_event_returns_false_on_500(requests_mock):
    """Non-2xx responses (raise_for_status) must also return False."""
    requests_mock.post("http://localhost:8000/events", status_code=500)
    result = push_event(
        event_type=EventType.WORKFLOW_FAILED,
        workflow_id="abc-123",
        base_url="http://localhost:8000",
        extra={},
    )
    assert result is False


def test_push_event_falls_back_to_state_route(requests_mock):
    """Falls back to /state when /events returns 404."""
    requests_mock.options("http://localhost:8000/events", status_code=404)
    requests_mock.post("http://localhost:8000/state", json={"ok": True}, status_code=200)
    # Clear route cache before test
    clear_route_cache()
    result = push_event(
        event_type=EventType.WORKFLOW_STARTED,
        workflow_id="abc-123",
        base_url="http://localhost:8000",
        extra={"task": "test"},
    )
    assert result is True
    assert requests_mock.last_request.path == "/state"


def test_push_event_uses_cached_route(requests_mock):
    """Uses cached route on second call without re-probing."""
    import agenticos_push
    agenticos_push._route_cache["http://localhost:9999"] = "/events"
    requests_mock.post("http://localhost:9999/events", json={"ok": True}, status_code=200)
    result = push_event(
        event_type=EventType.PHASE_COMPLETE,
        workflow_id="abc-123",
        base_url="http://localhost:9999",
        extra={"phase": "brainstorm"},
    )
    assert result is True
    # OPTIONS should NOT have been called (cached route used)
    assert not any(r.method == "OPTIONS" for r in requests_mock.request_history)
