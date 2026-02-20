"""Tests for the three security engine feedback-loop fixes.

Exercises:
  1. Temp file filtering   -- atomic writes must not generate alerts or audit entries
  2. Self-exclusion        -- audit_log.json changes must be ignored
  3. Lock file filtering   -- .lock files must be ignored
  4. Legitimate detection  -- real threats must still trigger alerts
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Ensure project root is on the path.
BASE_DIR = Path("C:/ClaudeSkills")
sys.path.insert(0, str(BASE_DIR / "scripts"))

from gui.security_engine import SecurityEngine, AUDIT_LOG_PATH, SECURITY_DIR

PASS = "PASS"
FAIL = "FAIL"
results: list[tuple[str, str, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    results.append((name, status, detail))
    tag = f"  [{status}]"
    print(f"{tag} {name}" + (f" -- {detail}" if detail else ""))


def fresh_engine() -> SecurityEngine:
    """Return a SecurityEngine with a clean audit log."""
    # Reset audit log on disk so each test starts clean.
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG_PATH.write_text("[]", encoding="utf-8")
    engine = SecurityEngine()
    engine._audit_log = None  # force reload from disk
    return engine


def audit_count(engine: SecurityEngine) -> int:
    """Return number of entries currently in the audit log on disk."""
    engine._audit_log = None  # force reload
    return len(engine._load_audit_log())


# -----------------------------------------------------------------------
# 1. Temp file filtering
# -----------------------------------------------------------------------
print("\n=== Test Group 1: Temp File Filtering ===")

engine = fresh_engine()

# sync_utils style: .tmp_abc123.json
alert = engine.scan_event("created", BASE_DIR / ".tmp_abc123.json")
record(
    "Atomic write (.tmp_abc123.json) produces no alert",
    alert is None,
    f"alert={alert}",
)
record(
    "Atomic write produces no audit entry",
    audit_count(engine) == 0,
    f"count={audit_count(engine)}",
)

# Claude Code style: foo.tmp.12345.67890
engine = fresh_engine()
alert = engine.scan_event("modified", BASE_DIR / "config" / "watch_config.json.tmp.12345.67890")
record(
    "Claude Code temp (.tmp.PID.TS) produces no alert",
    alert is None,
)
record(
    "Claude Code temp produces no audit entry",
    audit_count(engine) == 0,
    f"count={audit_count(engine)}",
)

# -----------------------------------------------------------------------
# 2. Self-exclusion (security directory)
# -----------------------------------------------------------------------
print("\n=== Test Group 2: Self-Exclusion ===")

engine = fresh_engine()

alert = engine.scan_event("modified", AUDIT_LOG_PATH)
record(
    "audit_log.json modification produces no alert",
    alert is None,
)
record(
    "audit_log.json modification produces no audit entry",
    audit_count(engine) == 0,
    f"count={audit_count(engine)}",
)

engine = fresh_engine()
alert = engine.scan_event("created", SECURITY_DIR / "integrity_db.json")
record(
    "integrity_db.json creation produces no alert",
    alert is None,
)
record(
    "integrity_db.json creation produces no audit entry",
    audit_count(engine) == 0,
    f"count={audit_count(engine)}",
)

# -----------------------------------------------------------------------
# 3. Lock file filtering
# -----------------------------------------------------------------------
print("\n=== Test Group 3: Lock File Filtering ===")

engine = fresh_engine()

alert = engine.scan_event("created", BASE_DIR / "cloud" / "main_cloud.json.lock")
record(
    ".lock file produces no alert",
    alert is None,
)
record(
    ".lock file produces no audit entry",
    audit_count(engine) == 0,
    f"count={audit_count(engine)}",
)

# -----------------------------------------------------------------------
# 4. Legitimate threat detection still works
# -----------------------------------------------------------------------
print("\n=== Test Group 4: Legitimate Threat Detection ===")

engine = fresh_engine()

# Suspicious extension
alert = engine.scan_event("created", BASE_DIR / "malware.exe")
record(
    ".exe file triggers CRITICAL alert",
    alert is not None and alert.level.value == "CRITICAL",
    f"alert={alert}",
)
record(
    ".exe file is logged to audit trail",
    audit_count(engine) == 1,
    f"count={audit_count(engine)}",
)

engine = fresh_engine()
alert = engine.scan_event("created", BASE_DIR / "script.bat")
record(
    ".bat file triggers alert",
    alert is not None,
    f"level={alert.level.value if alert else None}",
)

engine = fresh_engine()
alert = engine.scan_event("created", BASE_DIR / ".hidden_config")
record(
    "Hidden file triggers WARNING alert",
    alert is not None and alert.level.value == "WARNING",
    f"alert={alert}",
)

# Normal file should produce no alert but SHOULD produce an audit entry
engine = fresh_engine()
alert = engine.scan_event("modified", BASE_DIR / "scripts" / "main.py")
record(
    "Normal .py file produces no alert",
    alert is None,
)
record(
    "Normal .py file IS logged to audit trail",
    audit_count(engine) == 1,
    f"count={audit_count(engine)}",
)

# -----------------------------------------------------------------------
# 5. Feedback loop stress test
# -----------------------------------------------------------------------
print("\n=== Test Group 5: Feedback Loop Stress Test ===")

engine = fresh_engine()
# Simulate rapid audit_log.json modifications (the old feedback loop)
for i in range(20):
    engine.scan_event("modified", AUDIT_LOG_PATH)

record(
    "20 rapid audit_log events produce 0 audit entries",
    audit_count(engine) == 0,
    f"count={audit_count(engine)}",
)

# Mix of transient and real events
engine = fresh_engine()
engine.scan_event("created", BASE_DIR / ".tmp_xyz.json")
engine.scan_event("modified", AUDIT_LOG_PATH)
engine.scan_event("created", BASE_DIR / "cloud" / "foo.lock")
engine.scan_event("modified", BASE_DIR / "scripts" / "observer.py")  # real
engine.scan_event("created", BASE_DIR / "test.tmp.999.888")

record(
    "Mixed events: only 1 real event logged",
    audit_count(engine) == 1,
    f"count={audit_count(engine)}",
)

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
print("\n" + "=" * 55)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
total = len(results)
print(f"Results: {passed}/{total} passed, {failed} failed")

if failed:
    print("\nFailed tests:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"  - {name}: {detail}")
    sys.exit(1)
else:
    print("\nAll tests passed!")

# Clean up audit log after tests.
AUDIT_LOG_PATH.write_text("[]", encoding="utf-8")
