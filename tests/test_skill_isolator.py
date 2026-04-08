"""Tests for SkillIsolator path traversal validation (Issue #3).

Covers:
  1. Happy path   -- valid names round-trip create/save/load/cleanup
  2. Traversal    -- ``..`` sequences rejected in team_name and agent_name
  3. Separators   -- forward slash, backslash, drive colon rejected
  4. Absolute     -- absolute paths rejected
  4b. Trailing    -- trailing dots and spaces rejected (Windows normalization)
  5. Null/ctrl    -- null byte and control characters rejected
  6. Empty        -- empty and whitespace-only names rejected
  7. Reserved     -- Windows device names rejected
  8. Allowlist    -- characters outside ``[A-Za-z0-9_.-]`` rejected
  9. Symlink      -- symlinks that escape the teams dir are refused (best effort)
 10. Containment  -- every public filesystem method enforces validation
 11. Boundaries   -- length boundaries, numeric names, type validation, error paths
 12. Role mapping -- unknown and empty-bundle roles fall back to core bundle
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Ensure project root is on the path.
BASE_DIR = Path("C:/ClaudeSkills")
sys.path.insert(0, str(BASE_DIR / "scripts"))

from skill_isolator import SkillIsolator  # noqa: E402

PASS = "PASS"
FAIL = "FAIL"
results: list[tuple[str, str, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    results.append((name, status, detail))
    tag = f"  [{status}]"
    print(f"{tag} {name}" + (f" -- {detail}" if detail else ""))


def make_isolator(teams_dir: Path) -> SkillIsolator:
    bundles = {
        "bundles": {
            "core": {"skills": ["core-skill-a", "core-skill-b"]},
            "portfolio-dev": {"skills": ["next-js", "tailwind"]},
        }
    }
    config = {"core_bundle": "core"}
    return SkillIsolator(bundles=bundles, config=config, teams_dir=teams_dir)


def expect_value_error(fn, *args, **kwargs) -> tuple[bool, str]:
    """Call fn; return (True, "") if it raised ValueError, else (False, detail)."""
    try:
        fn(*args, **kwargs)
    except ValueError:
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, f"raised {type(exc).__name__} instead of ValueError: {exc}"
    return False, "did not raise"


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------
print("\n=== Test Group 1: Happy Path ===")

with tempfile.TemporaryDirectory() as tmp:
    teams_dir = Path(tmp)
    iso = make_isolator(teams_dir)

    manifest = iso.create_agent_manifest("team-alpha", "agent_01", "frontend-builder")
    record(
        "create_agent_manifest with valid names",
        manifest["team_name"] == "team-alpha" and manifest["agent_name"] == "agent_01",
        f"keys={sorted(manifest.keys())}",
    )

    saved_path = iso.save_agent_manifest("team-alpha", "agent_01", manifest)
    record(
        "save_agent_manifest writes inside teams_dir",
        saved_path.exists() and teams_dir in saved_path.parents,
        str(saved_path),
    )

    loaded = iso.load_agent_manifest("team-alpha", "agent_01")
    record(
        "load_agent_manifest round-trips data",
        loaded is not None and loaded["agent_role"] == "frontend-builder",
    )

    removed = iso.cleanup_agent_manifest("team-alpha", "agent_01")
    record(
        "cleanup_agent_manifest removes the file",
        removed is True and not saved_path.exists(),
    )

    # load on missing returns None (not an error)
    record(
        "load_agent_manifest returns None for missing file",
        iso.load_agent_manifest("team-alpha", "agent_01") is None,
    )


# ---------------------------------------------------------------------------
# 2. Traversal (``..`` in names)
# ---------------------------------------------------------------------------
print("\n=== Test Group 2: Traversal Sequences ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    traversal_names = [
        "..",
        "../evil",
        "..\\evil",
        "team..name",
        "....",
    ]
    for bad in traversal_names:
        ok, detail = expect_value_error(
            iso.create_agent_manifest, bad, "agent_01", "frontend-builder"
        )
        record(f"create_agent_manifest rejects team_name={bad!r}", ok, detail)

        ok, detail = expect_value_error(
            iso.save_agent_manifest, "team", bad, {}
        )
        record(f"save_agent_manifest rejects agent_name={bad!r}", ok, detail)


# ---------------------------------------------------------------------------
# 3. Separators and drive colons
# ---------------------------------------------------------------------------
print("\n=== Test Group 3: Separators ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    separator_names = [
        "team/name",
        "team\\name",
        "team:name",
        "C:",
        "sub/dir",
    ]
    for bad in separator_names:
        ok, detail = expect_value_error(
            iso.load_agent_manifest, bad, "agent_01"
        )
        record(f"load_agent_manifest rejects team_name={bad!r}", ok, detail)

        ok, detail = expect_value_error(
            iso.cleanup_agent_manifest, "team", bad
        )
        record(f"cleanup_agent_manifest rejects agent_name={bad!r}", ok, detail)


# ---------------------------------------------------------------------------
# 4. Absolute paths
# ---------------------------------------------------------------------------
print("\n=== Test Group 4: Absolute Paths ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    absolute_names = [
        "/etc/passwd",
        "C:/Windows/System32",
        "\\\\server\\share",
    ]
    for bad in absolute_names:
        ok, detail = expect_value_error(
            iso.save_agent_manifest, bad, "agent_01", {}
        )
        record(f"save rejects absolute team_name={bad!r}", ok, detail)


# ---------------------------------------------------------------------------
# 4b. Windows normalization — trailing dots and spaces (CWE-41)
# ---------------------------------------------------------------------------
print("\n=== Test Group 4b: Trailing Dots / Spaces ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    normalization_names = [
        "team.",            # single trailing dot
        "team...",          # multiple trailing dots
        "team ",            # trailing space
        "team. ",           # dot then space
        "team .",           # space then dot
        "a.b.",             # dot mid-name is fine but trailing dot is not
    ]
    for bad in normalization_names:
        ok, detail = expect_value_error(
            iso.create_agent_manifest, bad, "agent_01", "researcher"
        )
        record(f"create rejects team_name={bad!r}", ok, detail)

        ok, detail = expect_value_error(
            iso.save_agent_manifest, "team", bad, {}
        )
        record(f"save rejects agent_name={bad!r}", ok, detail)

    # Sanity: mid-name dots are still allowed
    try:
        m = iso.create_agent_manifest("a.b.c", "agent_01", "researcher")
        record("create accepts mid-name dots 'a.b.c'", m["team_name"] == "a.b.c")
    except ValueError as exc:
        record("create accepts mid-name dots 'a.b.c'", False, str(exc))


# ---------------------------------------------------------------------------
# 5. Null byte and control characters
# ---------------------------------------------------------------------------
print("\n=== Test Group 5: Null / Control Characters ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    control_names = [
        "team\x00name",
        "team\nname",
        "team\tname",
        "\x01bad",
    ]
    for bad in control_names:
        ok, detail = expect_value_error(
            iso.load_agent_manifest, bad, "agent_01"
        )
        record(f"load rejects control char in team_name={bad!r}", ok, detail)


# ---------------------------------------------------------------------------
# 6. Empty and whitespace-only names
# ---------------------------------------------------------------------------
print("\n=== Test Group 6: Empty / Whitespace ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    for bad in ["", "   ", "\t"]:
        ok, detail = expect_value_error(
            iso.create_agent_manifest, bad, "agent_01", "researcher"
        )
        record(f"create rejects team_name={bad!r}", ok, detail)

    for bad in ["", " ", "\n"]:
        ok, detail = expect_value_error(
            iso.create_agent_manifest, "team", bad, "researcher"
        )
        record(f"create rejects agent_name={bad!r}", ok, detail)


# ---------------------------------------------------------------------------
# 7. Windows reserved device names
# ---------------------------------------------------------------------------
print("\n=== Test Group 7: Windows Reserved Names ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    reserved = ["con", "CON", "nul", "COM1", "lpt9", "prn.json"]
    for bad in reserved:
        ok, detail = expect_value_error(
            iso.save_agent_manifest, "team", bad, {}
        )
        record(f"save rejects reserved agent_name={bad!r}", ok, detail)


# ---------------------------------------------------------------------------
# 8. Allowlist — characters outside [A-Za-z0-9_.-]
# ---------------------------------------------------------------------------
print("\n=== Test Group 8: Allowlist ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    out_of_allowlist = [
        "team name",   # space
        "team#hash",
        "team$dollar",
        "team%pct",
        "team&amp",
        "team(paren)",
        "team*star",
        "-leading-dash",  # must start alphanumeric
        ".leading-dot",   # must start alphanumeric
        "_leading-under", # must start alphanumeric
        "a" * 65,         # exceeds 64-char cap
    ]
    for bad in out_of_allowlist:
        ok, detail = expect_value_error(
            iso.create_agent_manifest, bad, "agent_01", "researcher"
        )
        record(f"create rejects team_name={bad!r}", ok, detail)


# ---------------------------------------------------------------------------
# 9. Symlink-based escape (best effort — requires symlink privilege on Windows)
# ---------------------------------------------------------------------------
print("\n=== Test Group 9: Symlink Escape ===")

with tempfile.TemporaryDirectory() as tmp_teams, tempfile.TemporaryDirectory() as tmp_outside:
    teams_dir = Path(tmp_teams)
    outside = Path(tmp_outside)

    # Plant a file outside the teams dir that a traversal could target.
    secret = outside / "secret.json"
    secret.write_text('{"secret": true}', encoding="utf-8")

    # Try to create a symlink inside teams_dir pointing outside.
    link_parent = teams_dir / "team1" / "skills"
    link_parent.mkdir(parents=True, exist_ok=True)
    link_path = link_parent / "agent_01.json"

    symlink_supported = True
    try:
        os.symlink(secret, link_path)
    except (OSError, NotImplementedError):
        # Windows without dev mode / symlink privilege — skip gracefully.
        symlink_supported = False
        record("symlink escape test skipped (no symlink privilege)", True)

    if symlink_supported:
        iso = make_isolator(teams_dir)
        # The symlink itself is inside teams_dir, so the validator should
        # allow resolution, but the resolved target must still be contained.
        # Our implementation resolves BEFORE the containment check, so it
        # will follow the symlink and then reject.
        loaded = None
        rejected = False
        try:
            loaded = iso.load_agent_manifest("team1", "agent_01")
        except ValueError:
            rejected = True
        record(
            "load_agent_manifest rejects symlink pointing outside teams_dir",
            rejected,
            "" if rejected else f"loaded={loaded}",
        )


# ---------------------------------------------------------------------------
# 10. Containment — every method goes through validation
# ---------------------------------------------------------------------------
print("\n=== Test Group 10: Full Coverage ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    bad_team = "../evil"
    bad_agent = "..\\evil"

    methods = [
        ("create_agent_manifest", lambda: iso.create_agent_manifest(bad_team, "a", "researcher")),
        ("save_agent_manifest", lambda: iso.save_agent_manifest(bad_team, "a", {})),
        ("load_agent_manifest", lambda: iso.load_agent_manifest(bad_team, "a")),
        ("cleanup_agent_manifest", lambda: iso.cleanup_agent_manifest(bad_team, "a")),
    ]
    for name, fn in methods:
        ok, detail = expect_value_error(fn)
        record(f"{name} rejects traversal in team_name", ok, detail)

    methods = [
        ("create_agent_manifest", lambda: iso.create_agent_manifest("t", bad_agent, "researcher")),
        ("save_agent_manifest", lambda: iso.save_agent_manifest("t", bad_agent, {})),
        ("load_agent_manifest", lambda: iso.load_agent_manifest("t", bad_agent)),
        ("cleanup_agent_manifest", lambda: iso.cleanup_agent_manifest("t", bad_agent)),
    ]
    for name, fn in methods:
        ok, detail = expect_value_error(fn)
        record(f"{name} rejects traversal in agent_name", ok, detail)


# ---------------------------------------------------------------------------
# 11. Boundary conditions and defensive error paths
# ---------------------------------------------------------------------------
print("\n=== Test Group 11: Boundaries & Defensive Paths ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    # --- Length boundaries ---

    # Single-character names (lower boundary of the allowlist)
    try:
        manifest = iso.create_agent_manifest("a", "b", "researcher")
        record(
            "single-character names accepted",
            manifest["team_name"] == "a" and manifest["agent_name"] == "b",
        )
    except ValueError as exc:
        record("single-character names accepted", False, str(exc))

    # Exact 64-character name (upper boundary — must pass)
    long_name = "a" * 64
    try:
        manifest = iso.create_agent_manifest(long_name, "agent_01", "researcher")
        record(
            "64-character team_name accepted",
            len(manifest["team_name"]) == 64,
        )
    except ValueError as exc:
        record("64-character team_name accepted", False, str(exc))

    # --- Numeric-only names ---

    try:
        manifest = iso.create_agent_manifest("123", "456", "researcher")
        record(
            "all-numeric names accepted",
            manifest["team_name"] == "123" and manifest["agent_name"] == "456",
        )
    except ValueError as exc:
        record("all-numeric names accepted", False, str(exc))

    # --- Non-string input types ---

    bad_types: list[tuple[str, Any]] = [
        ("integer", 123),
        ("None", None),
        ("list", ["team"]),
        ("bytes", b"team"),
    ]
    for label, bad in bad_types:
        ok, detail = expect_value_error(
            iso.create_agent_manifest, bad, "agent_01", "researcher"
        )
        record(f"create rejects {label} team_name", ok, detail)
        ok, detail = expect_value_error(
            iso.create_agent_manifest, "team", bad, "researcher"
        )
        record(f"create rejects {label} agent_name", ok, detail)

    # --- Malformed JSON on load returns None (covers the except branch) ---

    manifest_path = iso._resolve_manifest_path("team_json", "agent_json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("{not valid json", encoding="utf-8")
    loaded = iso.load_agent_manifest("team_json", "agent_json")
    record(
        "load_agent_manifest returns None for malformed JSON",
        loaded is None,
    )
    # Cleanup the corrupt file so the tempdir unwinds cleanly
    manifest_path.unlink()

    # --- Cleanup on non-existent file returns False ---

    removed = iso.cleanup_agent_manifest("never-existed", "never-either")
    record(
        "cleanup_agent_manifest returns False for missing file",
        removed is False,
    )


# ---------------------------------------------------------------------------
# 12. Role mapping fallback behavior
# ---------------------------------------------------------------------------
print("\n=== Test Group 12: Role Mapping ===")

with tempfile.TemporaryDirectory() as tmp:
    iso = make_isolator(Path(tmp))

    core_skills = ["core-skill-a", "core-skill-b"]

    # Unknown role falls back to core bundle only
    skills = iso.get_agent_skills("unknown-role-xyz")
    record(
        "unknown role returns only core skills",
        skills == core_skills,
        f"got {skills}",
    )

    # Empty-bundle roles ("Explore", "Plan") return only core bundle
    for role in ("Explore", "Plan"):
        skills = iso.get_agent_skills(role)
        record(
            f"{role!r} role returns only core skills",
            skills == core_skills,
            f"got {skills}",
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
total = len(results)
print(f"SkillIsolator tests: {passed}/{total} passed, {failed} failed")

if failed:
    print("\nFAILURES:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"  - {name}" + (f" :: {detail}" if detail else ""))
    sys.exit(1)
else:
    print("All SkillIsolator path traversal tests passed.")
    sys.exit(0)
