# test_inject_agent.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Integration test — injects a mock agent into agents.json and
#          progresses it through stages to verify live dashboard updates.

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Force UTF-8 stdout so ✓ and → render correctly on Windows cp1252 consoles.
sys.stdout.reconfigure(encoding="utf-8")

# Ensure C:\ClaudeSkills is on sys.path so AgenticOS is importable when the
# script is invoked directly (py -3.13 AgenticOS\test_inject_agent.py).
_REPO_ROOT: Path = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from AgenticOS.config import AGENTS_JSON, STATE_DIR

# ID used throughout the test — never hardcoded at individual write sites
TEST_AGENT_ID: str = "TEST-AGENT-01"


def utc_now_str() -> str:
    # Return ISO 8601 UTC timestamp with seconds precision (no microseconds)
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_agents() -> list[dict[str, Any]]:
    # Read agents.json; return empty list if the file does not exist yet
    try:
        raw: str = AGENTS_JSON.read_text(encoding="utf-8")
        return json.loads(raw)
    except FileNotFoundError:
        return []


def upsert_agent(entry: dict[str, Any]) -> None:
    # Read existing array, find-or-replace by agent_id, write back atomically
    agents: list[dict[str, Any]] = read_agents()
    idx: int = next(
        (i for i, a in enumerate(agents) if a.get("agent_id") == entry["agent_id"]),
        -1,
    )
    if idx == -1:
        agents.append(entry)
    else:
        agents[idx] = entry

    # Atomic write: temp file in same directory, then rename over target
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path: Path = AGENTS_JSON.with_suffix(f".tmp.{os.getpid()}")
    tmp_path.write_text(json.dumps(agents, indent=2, default=str), encoding="utf-8")
    tmp_path.replace(AGENTS_JSON)


def make_initial_entry() -> dict[str, Any]:
    # Build the initial AgentState dict for TEST-AGENT-01
    return {
        "agent_id": TEST_AGENT_ID,
        "domain": "software-eng",
        "task": "Integration test: verifying live dashboard updates",
        "stage_label": "Initializing test sequence",
        "stage": 1,
        "total_stages": 10,
        "progress_pct": 0,
        "status": "active",
        "context_pct_used": 5,
        "output_ref": None,
        "awaiting": None,
        "error_msg": None,
        "spawned_by": None,
        "reviewer_verdict": None,
        "updated_at": utc_now_str(),
    }


def main() -> None:
    print("AgenticOS Integration Test — Mock Agent Injection")

    # Step 1: write initial state
    entry: dict[str, Any] = make_initial_entry()
    upsert_agent(entry)
    print(f"✓ Agent {TEST_AGENT_ID} written to agents.json")

    # Step 2: pause so the dashboard can pick up the initial state
    print("Waiting 2s for dashboard to pick up initial state...")
    time.sleep(2)

    # Step 3: progress from 0% to 100% in 10% increments, one per second
    for pct in range(10, 110, 10):
        # Recalculate stage proportionally (1-indexed, bounded to total_stages)
        stage: int = max(1, round(pct / 10))

        # Determine status and awaiting based on current percentage
        if pct == 50:
            status: str = "waiting_approval"
            awaiting: str | None = "proceed"
            label: str = "Awaiting operator approval at 50%"
        elif pct >= 60:
            status = "active"
            awaiting = None
            label = f"Processing stage {stage} of 10"
        else:
            status = "active"
            awaiting = None
            label = f"Processing stage {stage} of 10"

        # Apply special label for 100% before marking complete below
        if pct == 100:
            label = "Finalizing all stages"

        entry["progress_pct"] = pct
        entry["stage"] = stage
        entry["stage_label"] = label
        entry["status"] = status
        entry["awaiting"] = awaiting
        entry["updated_at"] = utc_now_str()

        upsert_agent(entry)
        print(f"→ progress: {pct}% | status: {status} | stage: {stage}/10")
        time.sleep(1)

    # Step 4: mark the agent as complete
    entry["status"] = "complete"
    entry["awaiting"] = None
    entry["stage_label"] = "All stages complete"
    entry["updated_at"] = utc_now_str()
    upsert_agent(entry)
    print(f"✓ Agent reached complete")

    # Step 5: summary
    print("Test complete. Check dashboard at http://127.0.0.1:7842/app")
    print(f"Agent card should show {TEST_AGENT_ID} with status COMPLETE")
    print("Remove it from agents.json manually or restart the server to clear.")


if __name__ == "__main__":
    main()
