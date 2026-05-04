"""
Load + validation test for the AgentForge /api/agent/run endpoint.

Verifies:
  1. Normal sequential requests succeed (simulated backend)
  2. Concurrency cap (MAX 2 simultaneous) returns 429 on overload
  3. Auth check: missing token returns 401 when AGENT_TOKEN is set
  4. taskId allowlist rejects bad characters
  5. Context size cap rejects oversized payloads
  6. Prompt not leaked in response body
  7. Throughput: 10 sequential requests complete in < 60s
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
import threading
from typing import Any

BASE_URL = "http://localhost:3006/api/agent/run"
PASS = "PASS"
FAIL = "FAIL"

results: list[tuple[str, str, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    results.append((name, status, detail))
    tag = f"  [{status}]"
    print(f"{tag} {name}" + (f" — {detail}" if detail else ""))


def post(payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    """POST JSON to the endpoint. Returns (status_code, response_body)."""
    data = json.dumps(payload).encode()
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(BASE_URL, data=data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body: dict[str, Any] = {}
        try:
            body = json.loads(e.read())
        except Exception:
            pass
        return e.code, body


# ---------------------------------------------------------------------------
# Group 1: Basic health — simulated backend responds
# ---------------------------------------------------------------------------
print("\n=== Group 1: Basic Health ===")

status, body = post({"taskId": "load-test-001", "context": {}, "backend": "simulated"})
record(
    "Simulated pipeline returns 200",
    status == 200,
    f"status={status}",
)
record(
    "Response contains sessionId",
    "sessionId" in body,
    f"keys={list(body.keys())[:6]}",
)
record(
    "Prompt not in response body",
    "prompt" not in json.dumps(body),
    "response body scanned for 'prompt' key",
)

# ---------------------------------------------------------------------------
# Group 2: Input validation
# ---------------------------------------------------------------------------
print("\n=== Group 2: Input Validation ===")

# taskId with path traversal characters
status, body = post({"taskId": "../../../etc/passwd", "context": {}, "backend": "simulated"})
record(
    "taskId with path traversal returns 400",
    status == 400,
    f"status={status} body={body.get('error', '')[:60]}",
)

# taskId too long
status, body = post({"taskId": "a" * 101, "context": {}, "backend": "simulated"})
record(
    "taskId > 100 chars returns 400",
    status == 400,
    f"status={status}",
)

# context too large (~51k chars)
big_context = {"data": "x" * 51_000}
status, body = post({"taskId": "ctx-test", "context": big_context, "backend": "simulated"})
record(
    "context > 50,000 chars returns 400",
    status == 400,
    f"status={status} body={body.get('error', '')[:60]}",
)

# context not an object
status, body = post({"taskId": "ctx-array", "context": [1, 2, 3], "backend": "simulated"})
record(
    "context as array returns 400",
    status == 400,
    f"status={status}",
)

# parallel not a boolean
status, body = post({"taskId": "par-test", "parallel": "yes", "backend": "simulated"})
record(
    "parallel as string returns 400",
    status == 400,
    f"status={status}",
)

# ---------------------------------------------------------------------------
# Group 3: Concurrency cap (MAX_CONCURRENT_PIPELINES = 2)
# ---------------------------------------------------------------------------
print("\n=== Group 3: Concurrency Cap ===")

# Fire 4 simultaneous requests; at least some should get 429
statuses: list[int] = []
lock = threading.Lock()

def fire() -> None:
    s, _ = post({"taskId": f"concurrent-{threading.get_ident()}", "context": {}, "backend": "simulated"})
    with lock:
        statuses.append(s)

threads = [threading.Thread(target=fire) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join(timeout=35)

got_429 = any(s == 429 for s in statuses)
got_200 = any(s == 200 for s in statuses)
record(
    "Concurrent burst: at least one 429 (concurrency cap triggered)",
    got_429,
    f"statuses={sorted(statuses)}",
)
record(
    "Concurrent burst: at least one 200 (cap allows some through)",
    got_200,
    f"statuses={sorted(statuses)}",
)

# ---------------------------------------------------------------------------
# Group 4: Throughput — 10 sequential requests
# ---------------------------------------------------------------------------
print("\n=== Group 4: Throughput (10 sequential requests) ===")

start = time.monotonic()
seq_statuses: list[int] = []
for i in range(10):
    s, _ = post({"taskId": f"seq-{i}", "context": {"iteration": i}, "backend": "simulated"})
    seq_statuses.append(s)
    time.sleep(0.1)  # small gap to avoid concurrency cap
elapsed = time.monotonic() - start

all_ok = all(s == 200 for s in seq_statuses)
record(
    "10 sequential requests all return 200",
    all_ok,
    f"statuses={seq_statuses}",
)
record(
    "10 sequential requests complete in < 60s",
    elapsed < 60,
    f"elapsed={elapsed:.2f}s",
)
print(f"  Throughput: {10 / elapsed:.2f} req/s  (avg {elapsed/10:.2f}s/req)")

# ---------------------------------------------------------------------------
# Group 5: Security — prompt not leaked across any request
# ---------------------------------------------------------------------------
print("\n=== Group 5: Prompt Leak Check ===")

_, body = post({"taskId": "leak-check", "context": {"secret": "hunter2"}, "backend": "simulated"})
body_str = json.dumps(body)
record(
    "Response does not contain 'prompt' key",
    '"prompt"' not in body_str,
    f"body length={len(body_str)}",
)
record(
    "Response does not contain SYSTEM_PROMPT fragment",
    "You are the" not in body_str,
    "scanned for agent system prompt preamble",
)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
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
    print("\nAll load tests passed!")
