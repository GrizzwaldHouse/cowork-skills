# test_session_discovery.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Pytest coverage for session_discovery.py. Builds a fake
#          Cowork sessions root inside tmp_path, drops one valid
#          mission-state.json and one corrupt one, and asserts that
#          only the valid one is surfaced and the corrupt file's
#          failure is logged rather than raised.

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from AgenticOS.session_discovery import (
    parse_mission_state,
    scan_active_sessions,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _write_mission_state(
    sessions_root: Path,
    plugin_id: str,
    session_id: str,
    payload: object,
    *,
    raw: str | None = None,
) -> Path:
    """Create a session directory under sessions_root/plugin/session
    and drop a mission-state.json with either ``payload`` (JSON-dumped)
    or ``raw`` (verbatim, used for malformed-input tests)."""
    session_dir = sessions_root / plugin_id / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    target = session_dir / "mission-state.json"
    if raw is not None:
        target.write_text(raw, encoding="utf-8")
    else:
        target.write_text(json.dumps(payload), encoding="utf-8")
    # Touch with a fresh mtime so the file always counts as active in
    # tests; avoids flakes when the runner is slow on CI.
    now = time.time()
    import os
    os.utime(target, (now, now))
    return target


# ---------------------------------------------------------------------------
# scan_active_sessions
# ---------------------------------------------------------------------------

def test_scan_returns_only_valid_sessions(tmp_path, caplog):
    # Arrange — one good, one syntactically-broken mission state.
    good = _write_mission_state(
        tmp_path,
        plugin_id="plugin-a",
        session_id="session-good",
        payload={
            "objective": "build feature x",
            "status": "in_progress",
            "timeline": [
                {"kind": "tool_use", "agent": "AGENT-01"},
                {"kind": "tool_use", "agent": "AGENT-01"},
            ],
        },
    )
    bad = _write_mission_state(
        tmp_path,
        plugin_id="plugin-a",
        session_id="session-bad",
        payload=None,
        raw="this-is-not-json{{",
    )
    # Sanity: both files exist before the scan.
    assert good.exists()
    assert bad.exists()

    # Act — capture warning logs so we can assert the bad session
    # surfaced through the logger and was not silently dropped.
    caplog.set_level(logging.WARNING, logger="agentic_os.session_discovery")
    discovered = scan_active_sessions(
        sessions_root=tmp_path,
        active_threshold_s=120,
        max_sessions=10,
    )

    # Assert — exactly one session, and it is the good one.
    assert len(discovered) == 1
    assert discovered[0].session_id == "session-good"
    assert discovered[0].plugin_id == "plugin-a"
    assert discovered[0].objective == "build feature x"
    assert discovered[0].status == "in_progress"
    assert len(discovered[0].timeline_tail) == 2

    # Bad file produced a warning (covers both the "not JSON" and any
    # follow-up resolution path).
    assert any(
        "session-bad" in record.message or "Malformed JSON" in record.message
        for record in caplog.records
    )


def test_scan_skips_stale_sessions(tmp_path):
    # A session whose mission-state.json has not been touched recently
    # must not appear in the active-session list.
    target = _write_mission_state(
        tmp_path, "plugin-a", "session-cold", {"objective": "old work"}
    )
    # Backdate the mtime well past the threshold.
    import os
    very_old = time.time() - 3600  # one hour ago
    os.utime(target, (very_old, very_old))

    discovered = scan_active_sessions(
        sessions_root=tmp_path,
        active_threshold_s=60,
        max_sessions=10,
    )
    assert discovered == []


def test_scan_returns_empty_when_root_missing(tmp_path):
    # Pointing scan at a non-existent root must return [] and never raise.
    missing = tmp_path / "does-not-exist"
    assert not missing.exists()
    assert scan_active_sessions(sessions_root=missing) == []


def test_scan_respects_max_sessions(tmp_path):
    # Drop more than the cap and confirm only the cap-sized slice
    # is returned.
    for i in range(5):
        _write_mission_state(
            tmp_path,
            plugin_id="plugin-a",
            session_id=f"session-{i:02d}",
            payload={"objective": f"task {i}"},
        )

    discovered = scan_active_sessions(
        sessions_root=tmp_path,
        active_threshold_s=120,
        max_sessions=3,
    )
    assert len(discovered) == 3


# ---------------------------------------------------------------------------
# parse_mission_state
# ---------------------------------------------------------------------------

def test_parse_mission_state_returns_none_on_missing_file(tmp_path):
    # parse_mission_state must never raise on a missing target.
    missing = tmp_path / "nope.json"
    assert parse_mission_state(missing) is None


def test_parse_mission_state_returns_none_on_invalid_json(tmp_path, caplog):
    # Malformed JSON must produce a None return and a logged warning.
    target = _write_mission_state(
        tmp_path, "plugin-a", "session-x", payload=None, raw="{not-json}"
    )
    caplog.set_level(logging.WARNING, logger="agentic_os.session_discovery")
    assert parse_mission_state(target) is None
    assert any("Malformed JSON" in r.message for r in caplog.records)


def test_parse_mission_state_falls_back_for_missing_fields(tmp_path):
    # Mission state without an explicit objective should still parse,
    # using the placeholder default.
    target = _write_mission_state(
        tmp_path, "plugin-a", "session-x", {"status": "complete"}
    )
    session = parse_mission_state(target)
    assert session is not None
    assert session.objective == "(no objective)"
    assert session.status == "complete"


def test_parse_mission_state_uses_mtime_for_last_active(tmp_path):
    # Force a known mtime, parse, and assert last_active_at is derived
    # from filesystem mtime rather than any embedded JSON value.
    import os
    target = _write_mission_state(
        tmp_path, "plugin-a", "session-x", {"objective": "irrelevant"}
    )
    fixed = (datetime.now(timezone.utc) - timedelta(seconds=10)).timestamp()
    os.utime(target, (fixed, fixed))

    session = parse_mission_state(target)
    assert session is not None
    delta = abs(session.last_active_at.timestamp() - fixed)
    assert delta < 1.0
