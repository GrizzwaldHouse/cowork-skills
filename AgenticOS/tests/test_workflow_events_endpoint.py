# AgenticOS/tests/test_workflow_events_endpoint.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Tests for GET /workflow-events endpoint.

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from AgenticOS.agentic_server import create_app


@pytest.fixture()
def client(tmp_path: Path):
    events_file = tmp_path / "workflow_events.json"
    events_file.write_text(
        json.dumps([
            {
                "event": "workflow.started",
                "workflow_id": "wf-001",
                "task": "Build something",
                "timestamp": "2026-05-01T10:00:00Z",
            },
            {
                "event": "workflow.phase_started",
                "workflow_id": "wf-001",
                "phase": "brainstorm",
                "timestamp": "2026-05-01T10:00:01Z",
            },
            {
                "event": "workflow.started",
                "workflow_id": "wf-002",
                "task": "Other task",
                "timestamp": "2026-05-01T10:01:00Z",
            },
        ]),
        encoding="utf-8",
    )
    with patch("AgenticOS.agentic_server.OUTPUTS_DIR", tmp_path):
        app = create_app()
        yield TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def client_no_file(tmp_path: Path):
    with patch("AgenticOS.agentic_server.OUTPUTS_DIR", tmp_path):
        app = create_app()
        yield TestClient(app, raise_server_exceptions=True)


def test_returns_all_events(client):
    resp = client.get("/workflow-events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["since"] == 0
    assert body["count"] == 3
    assert len(body["events"]) == 3


def test_since_cursor_slices_events(client):
    resp = client.get("/workflow-events?since=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["since"] == 1
    assert body["count"] == 2
    assert body["events"][0]["event"] == "workflow.phase_started"


def test_workflow_id_filter(client):
    resp = client.get("/workflow-events?workflow_id=wf-002")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["events"][0]["workflow_id"] == "wf-002"


def test_since_beyond_length_returns_empty(client):
    resp = client.get("/workflow-events?since=99")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["events"] == []


def test_missing_file_returns_empty(client_no_file):
    resp = client_no_file.get("/workflow-events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["events"] == []
