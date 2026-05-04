# test_progress_log.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Coverage for progress_log.ProgressLog. Includes a thread-based
#          concurrency test that exercises the in-process RLock and the
#          OS-level advisory lock together.

from __future__ import annotations

import json
import threading

from AgenticOS.progress_log import ProgressLog


# ---------------------------------------------------------------------------
# Single-thread sanity
# ---------------------------------------------------------------------------

def test_append_assigns_monotonic_seq(tmp_path):
    log = ProgressLog(tmp_path / "progress.log")
    seq_a = log.append({"kind": "added", "agent_id": "AGENT-01"})
    seq_b = log.append({"kind": "updated", "agent_id": "AGENT-01"})
    seq_c = log.append({"kind": "removed", "agent_id": "AGENT-01"})
    assert (seq_a, seq_b, seq_c) == (0, 1, 2)
    assert log.latest_seq() == 2


def test_read_since_filters_by_seq(tmp_path):
    log = ProgressLog(tmp_path / "progress.log")
    for kind in ("added", "updated", "stuck", "loop"):
        log.append({"kind": kind, "agent_id": "AGENT-01"})

    all_recent = log.read_since(0)
    assert len(all_recent) == 4
    # read_since is inclusive of the seq it is called with.
    later = log.read_since(2)
    assert [r["kind"] for r in later] == ["stuck", "loop"]
    # A seq beyond the end returns no rows.
    none = log.read_since(99)
    assert none == []


def test_seq_resumes_after_restart(tmp_path):
    # Simulate a process restart: write some events, drop the instance,
    # construct a new one, and confirm the seq picks up where it left off.
    log_path = tmp_path / "progress.log"
    first = ProgressLog(log_path)
    first.append({"kind": "added", "agent_id": "AGENT-01"})
    first.append({"kind": "added", "agent_id": "AGENT-02"})
    assert first.latest_seq() == 1
    del first

    resumed = ProgressLog(log_path)
    seq = resumed.append({"kind": "added", "agent_id": "AGENT-03"})
    assert seq == 2


def test_corrupt_line_is_skipped_not_fatal(tmp_path):
    # Write a deliberately broken line, then make sure read_since
    # returns the surviving good lines.
    path = tmp_path / "progress.log"
    log = ProgressLog(path)
    log.append({"kind": "added", "agent_id": "AGENT-01"})
    # Inject a malformed line by hand.
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("this-is-not-json\n")
    log.append({"kind": "added", "agent_id": "AGENT-02"})

    rows = log.read_since(0)
    assert len(rows) == 2
    assert {r["agent_id"] for r in rows} == {"AGENT-01", "AGENT-02"}


# ---------------------------------------------------------------------------
# Multi-thread concurrency
# ---------------------------------------------------------------------------

def test_concurrent_appends_assign_unique_seqs(tmp_path):
    # 8 threads each append 25 events; all 200 records must end up with
    # distinct seqs and the file must contain 200 valid NDJSON lines.
    log = ProgressLog(tmp_path / "progress.log")
    events_per_thread = 25
    thread_count = 8

    seqs_lock = threading.Lock()
    seqs: list[int] = []

    def worker(thread_id: int) -> None:
        for i in range(events_per_thread):
            seq = log.append(
                {
                    "kind": "added",
                    "agent_id": f"AGENT-T{thread_id}-{i:02d}",
                }
            )
            with seqs_lock:
                seqs.append(seq)

    threads = [
        threading.Thread(target=worker, args=(t,)) for t in range(thread_count)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected = thread_count * events_per_thread
    assert len(seqs) == expected
    # No duplicate seqs; the in-process RLock + OS lock combo prevents collisions.
    assert len(set(seqs)) == expected

    # Every line on disk parses and carries a unique seq.
    raw = (tmp_path / "progress.log").read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if line.strip()]
    assert len(lines) == expected
    parsed_seqs = set()
    for line in lines:
        record = json.loads(line)
        parsed_seqs.add(record["seq"])
    assert parsed_seqs == set(seqs)
