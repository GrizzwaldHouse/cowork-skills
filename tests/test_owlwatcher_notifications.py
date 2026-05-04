# test_owlwatcher_notifications.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Verifies OwlWatcher notification throttling and Ollama scope guard
#          behavior without requiring the PyQt GUI runtime.

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from gui.notification_policy import NotificationPolicy
from gui.security_engine import _evaluate_ollama_scope


def test_notification_policy_suppresses_info_and_duplicates() -> None:
    policy = NotificationPolicy({
        "notification_policy": {
            "min_level": "WARNING",
            "cooldown_seconds": 60,
            "duplicate_window_seconds": 300,
        }
    })

    info = policy.evaluate(
        {"level": "INFO", "message": "Normal change", "file_path": "a.py"},
        now=100.0,
    )
    assert not info.should_notify
    assert info.reason == "below-min-level"

    first = policy.evaluate(
        {"level": "WARNING", "message": "Careful", "file_path": "a.py"},
        now=200.0,
    )
    assert first.should_notify

    duplicate = policy.evaluate(
        {"level": "WARNING", "message": "Careful", "file_path": "a.py"},
        now=220.0,
    )
    assert not duplicate.should_notify
    assert duplicate.reason == "duplicate"


def test_notification_policy_rate_limits_warning_burst() -> None:
    policy = NotificationPolicy({
        "notification_policy": {
            "min_level": "WARNING",
            "cooldown_seconds": 60,
            "duplicate_window_seconds": 300,
        }
    })

    first = policy.evaluate(
        {"level": "WARNING", "message": "First", "file_path": "a.py"},
        now=100.0,
    )
    second = policy.evaluate(
        {"level": "WARNING", "message": "Second", "file_path": "b.py"},
        now=120.0,
    )

    assert first.should_notify
    assert not second.should_notify
    assert second.reason == "cooldown"


def test_ollama_guard_is_inert_without_scope() -> None:
    alert = _evaluate_ollama_scope(
        "modified",
        Path("C:/ClaudeSkills/README.md"),
        "2026-05-01T00:00:00Z",
        {
            "enabled": True,
            "allowed_paths": [],
            "allowed_globs": [],
            "allow_deletes": False,
        },
    )

    assert alert is None


def test_ollama_guard_allows_assigned_file() -> None:
    alert = _evaluate_ollama_scope(
        "modified",
        Path("C:/ClaudeSkills/AgenticOS/task_store.py"),
        "2026-05-01T00:00:00Z",
        {
            "enabled": True,
            "agent_id": "ollama",
            "allowed_paths": ["C:/ClaudeSkills/AgenticOS/task_store.py"],
            "allowed_globs": [],
            "allow_deletes": False,
        },
    )

    assert alert is None


def test_ollama_guard_flags_out_of_scope_change() -> None:
    alert = _evaluate_ollama_scope(
        "modified",
        Path("C:/ClaudeSkills/AgenticOS/agentic_server.py"),
        "2026-05-01T00:00:00Z",
        {
            "enabled": True,
            "agent_id": "ollama",
            "allowed_paths": ["C:/ClaudeSkills/AgenticOS/task_store.py"],
            "allowed_globs": [],
            "allow_deletes": False,
        },
    )

    assert alert is not None
    assert alert.level.value == "CRITICAL"
    assert "outside its assigned scope" in alert.message


def test_ollama_guard_flags_delete_without_permission() -> None:
    alert = _evaluate_ollama_scope(
        "deleted",
        Path("C:/ClaudeSkills/AgenticOS/task_store.py"),
        "2026-05-01T00:00:00Z",
        {
            "enabled": True,
            "agent_id": "ollama",
            "allowed_paths": ["C:/ClaudeSkills/AgenticOS/task_store.py"],
            "allowed_globs": [],
            "allow_deletes": False,
            "delete_allowed_paths": [],
            "delete_allowed_globs": [],
        },
    )

    assert alert is not None
    assert alert.level.value == "CRITICAL"
    assert "deleted a file without delete permission" in alert.message
