# test_handoff.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Unit tests for handoff_writer — manifest creation, reading,
#          updating, and status payload.

from __future__ import annotations

import json
from pathlib import Path

import pytest

import AgenticOS.config as _config
import AgenticOS.handoff_writer as _writer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(tmp_path: Path) -> Path:
    """Write a minimal agent handoff manifest and return its path."""
    return _writer.write_handoff_manifest(
        agent_id="AGENT-TEST",
        domain="software-eng",
        task="Build the handoff feature",
        last_completed_stage=2,
        total_stages=5,
        last_output_ref=None,
        resume_instructions="Continue from stage 3.",
        claude_session_id="session-abc",
    )


# ---------------------------------------------------------------------------
# Test 1: write creates the file
# ---------------------------------------------------------------------------

def test_write_manifest_creates_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Redirect HANDOFF_MANIFEST_PATH to a temp location so nothing touches real state.
    fake_path = tmp_path / "handoff_manifest.json"
    monkeypatch.setattr(_config, "HANDOFF_MANIFEST_PATH", fake_path)
    monkeypatch.setattr(_writer, "HANDOFF_MANIFEST_PATH", fake_path)

    result_path = _make_manifest(tmp_path)

    assert result_path.exists(), "write_handoff_manifest must create the file"
    data = json.loads(result_path.read_text(encoding="utf-8"))
    assert data["agent_id"] == "AGENT-TEST"


# ---------------------------------------------------------------------------
# Test 2: written manifest contains every required schema key
# ---------------------------------------------------------------------------

def test_write_manifest_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_path = tmp_path / "handoff_manifest.json"
    monkeypatch.setattr(_config, "HANDOFF_MANIFEST_PATH", fake_path)
    monkeypatch.setattr(_writer, "HANDOFF_MANIFEST_PATH", fake_path)

    _make_manifest(tmp_path)

    data = json.loads(fake_path.read_text(encoding="utf-8"))
    required_keys = [
        "manifest_version",
        "created_at",
        "claude_session_id",
        "agent_id",
        "domain",
        "task",
        "last_completed_stage",
        "total_stages",
        "last_output_ref",
        "resume_instructions",
        "ollama_model",
        "status",
        "ollama_output_ref",
        "ollama_completed_at",
        "claude_reviewed_at",
        "claude_verdict",
    ]
    for key in required_keys:
        assert key in data, f"Required key missing from manifest: {key}"

    assert data["status"] == "pending_ollama"
    assert data["manifest_version"] == 1
    assert data["ollama_output_ref"] is None
    assert data["claude_verdict"] is None


# ---------------------------------------------------------------------------
# Test 3: read returns None when no file exists
# ---------------------------------------------------------------------------

def test_read_manifest_returns_none_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_path = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(_config, "HANDOFF_MANIFEST_PATH", fake_path)
    monkeypatch.setattr(_writer, "HANDOFF_MANIFEST_PATH", fake_path)

    result = _writer.read_handoff_manifest()
    assert result is None


# ---------------------------------------------------------------------------
# Test 4: read returns a dict after a successful write
# ---------------------------------------------------------------------------

def test_read_manifest_returns_dict_when_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_path = tmp_path / "handoff_manifest.json"
    monkeypatch.setattr(_config, "HANDOFF_MANIFEST_PATH", fake_path)
    monkeypatch.setattr(_writer, "HANDOFF_MANIFEST_PATH", fake_path)

    _make_manifest(tmp_path)
    result = _writer.read_handoff_manifest()

    assert isinstance(result, dict)
    assert result["agent_id"] == "AGENT-TEST"
    assert result["task"] == "Build the handoff feature"
    assert result["last_completed_stage"] == 2
    assert result["total_stages"] == 5


# ---------------------------------------------------------------------------
# Test 5: update_handoff_status changes the status field atomically
# ---------------------------------------------------------------------------

def test_update_handoff_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_path = tmp_path / "handoff_manifest.json"
    monkeypatch.setattr(_config, "HANDOFF_MANIFEST_PATH", fake_path)
    monkeypatch.setattr(_writer, "HANDOFF_MANIFEST_PATH", fake_path)

    _make_manifest(tmp_path)

    # Confirm initial status.
    before = json.loads(fake_path.read_text(encoding="utf-8"))
    assert before["status"] == "pending_ollama"

    # Update status and an extra field.
    ts = "2026-04-30T10:00:00+00:00"
    _writer.update_handoff_status(
        "ollama_complete",
        ollama_output_ref="/some/path/output.md",
        ollama_completed_at=ts,
    )

    after = json.loads(fake_path.read_text(encoding="utf-8"))
    assert after["status"] == "ollama_complete"
    assert after["ollama_output_ref"] == "/some/path/output.md"
    assert after["ollama_completed_at"] == ts
    # Other fields must be preserved.
    assert after["agent_id"] == "AGENT-TEST"
    assert after["manifest_version"] == 1


# ---------------------------------------------------------------------------
# Test 6: handoff_status_payload returns {"status": "none"} when no manifest
# ---------------------------------------------------------------------------

def test_handoff_status_payload_when_no_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_path = tmp_path / "no_manifest_here.json"
    monkeypatch.setattr(_config, "HANDOFF_MANIFEST_PATH", fake_path)
    monkeypatch.setattr(_writer, "HANDOFF_MANIFEST_PATH", fake_path)

    payload = _writer.handoff_status_payload()

    assert payload == {"status": "none"}
