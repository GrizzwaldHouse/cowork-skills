# test_websocket_broadcaster.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Verifies the WebSocketBroadcaster manages connections and
#          diff/snapshot frames correctly. Uses AsyncMock for the
#          websocket protocol so tests are entirely in-process.

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from AgenticOS.models import AgentDomain, AgentState, AgentStatus
from AgenticOS.websocket_broadcaster import (
    MESSAGE_TYPE_DIFF,
    MESSAGE_TYPE_SNAPSHOT,
    WebSocketBroadcaster,
    compute_diff,
)


# ---------------------------------------------------------------------------
# Test data builders
# ---------------------------------------------------------------------------

# Stable epoch used by the tests so two AgentState instances with otherwise
# identical fields serialise identically. Without this, datetime.now would
# make every rebuilt agent look "updated" between broadcasts.
_FIXED_TS = datetime(2026, 4, 29, 12, 0, 0, tzinfo=timezone.utc)


def _make_agent(
    agent_id: str = "AGENT-01",
    progress: int = 50,
    updated_at: datetime = _FIXED_TS,
) -> AgentState:
    """Build a minimal valid AgentState; progress and timestamp are
    parameterised so tests can produce truly-equal or truly-different
    instances on demand."""
    return AgentState(
        agent_id=agent_id,
        domain=AgentDomain.GENERAL,
        task="ws test",
        stage_label="step",
        stage=1,
        total_stages=2,
        progress_pct=progress,
        status=AgentStatus.ACTIVE,
        context_pct_used=10,
        updated_at=updated_at,
    )


# ---------------------------------------------------------------------------
# 1. Connect accepts the handshake and sends an initial snapshot
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_connect_sends_snapshot_and_registers() -> None:
    """A new client must receive a snapshot frame and end up in the
    active connections list."""
    broadcaster = WebSocketBroadcaster()
    client = AsyncMock()

    await broadcaster.connect(client)

    # Handshake accepted and one snapshot frame sent.
    client.accept.assert_awaited_once()
    client.send_text.assert_awaited_once()

    # The frame must declare itself a snapshot.
    payload = json.loads(client.send_text.call_args.args[0])
    assert payload["type"] == MESSAGE_TYPE_SNAPSHOT
    assert payload["agents"] == []

    # Connection must be tracked.
    assert broadcaster.connection_count == 1


# ---------------------------------------------------------------------------
# 2. Disconnect removes a registered client cleanly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disconnect_removes_client() -> None:
    """Disconnecting a registered client must drop the count to zero
    and not raise even if called twice."""
    broadcaster = WebSocketBroadcaster()
    client = AsyncMock()
    await broadcaster.connect(client)

    await broadcaster.disconnect(client)
    assert broadcaster.connection_count == 0

    # Idempotent: a second call must be a no-op rather than KeyError.
    await broadcaster.disconnect(client)
    assert broadcaster.connection_count == 0


# ---------------------------------------------------------------------------
# 3. Diff broadcast sends only the changed agents
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diff_broadcast_sends_only_changes() -> None:
    """After a snapshot baseline, broadcasting a modified state must
    produce a diff frame that lists added/updated/removed correctly."""
    broadcaster = WebSocketBroadcaster()
    client = AsyncMock()
    await broadcaster.connect(client)
    client.send_text.reset_mock()

    # First broadcast establishes baseline; AGENT-01 appears as "added"
    # because the broadcaster's previous state was empty.
    await broadcaster.broadcast_state([_make_agent("AGENT-01", progress=30)])

    assert client.send_text.await_count == 1
    first_frame = json.loads(client.send_text.await_args_list[0].args[0])
    assert first_frame["type"] == MESSAGE_TYPE_DIFF
    assert [a["agent_id"] for a in first_frame["added"]] == ["AGENT-01"]
    assert first_frame["updated"] == []
    assert first_frame["removed"] == []

    client.send_text.reset_mock()

    # Second broadcast: bump AGENT-01 progress (so it appears as updated)
    # and add AGENT-02 fresh. AGENT-02 uses the fixed timestamp default
    # so it will compare equal between the second and third broadcasts.
    await broadcaster.broadcast_state(
        [
            _make_agent("AGENT-01", progress=80),
            _make_agent("AGENT-02", progress=10),
        ]
    )
    assert client.send_text.await_count == 1
    second_frame = json.loads(client.send_text.await_args_list[0].args[0])
    assert second_frame["type"] == MESSAGE_TYPE_DIFF
    assert [a["agent_id"] for a in second_frame["added"]] == ["AGENT-02"]
    assert [a["agent_id"] for a in second_frame["updated"]] == ["AGENT-01"]
    assert second_frame["removed"] == []

    client.send_text.reset_mock()

    # Third broadcast: drop AGENT-01 entirely. AGENT-02 is unchanged so
    # only the removal should appear in the diff.
    await broadcaster.broadcast_state([_make_agent("AGENT-02", progress=10)])
    third_frame = json.loads(client.send_text.await_args_list[0].args[0])
    assert third_frame["removed"] == ["AGENT-01"]
    assert third_frame["added"] == []
    assert third_frame["updated"] == []


# ---------------------------------------------------------------------------
# 4. Multiple clients each receive the same diff frame
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multiple_clients_each_receive_broadcasts() -> None:
    """A broadcast must reach every connected client exactly once."""
    broadcaster = WebSocketBroadcaster()
    clients = [AsyncMock() for _ in range(3)]
    for client in clients:
        await broadcaster.connect(client)

    # Reset the snapshot calls so we count only diff broadcasts below.
    for client in clients:
        client.send_text.reset_mock()

    await broadcaster.broadcast_state([_make_agent("AGENT-01")])

    for client in clients:
        client.send_text.assert_awaited_once()
        payload = json.loads(client.send_text.await_args.args[0])
        assert payload["type"] == MESSAGE_TYPE_DIFF
        assert [a["agent_id"] for a in payload["added"]] == ["AGENT-01"]


# ---------------------------------------------------------------------------
# 5. A client whose send_text raises is pruned from the active list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dead_client_is_pruned_on_broadcast() -> None:
    """If send_text raises during a broadcast, the broadcaster must
    drop that connection and continue without raising."""
    broadcaster = WebSocketBroadcaster()
    healthy = AsyncMock()
    dead = AsyncMock()
    await broadcaster.connect(healthy)
    await broadcaster.connect(dead)
    dead.send_text.side_effect = Exception("connection closed")

    # Broadcast must complete without raising even though one client fails.
    await broadcaster.broadcast_state([_make_agent("AGENT-01")])

    # Dead client gone; healthy client retained.
    assert broadcaster.connection_count == 1
    assert broadcaster.active_connections == [healthy]


# ---------------------------------------------------------------------------
# 6. compute_diff is field-order independent
# ---------------------------------------------------------------------------

def test_compute_diff_is_field_order_independent() -> None:
    """Two dicts with identical content but different key order must
    not register as 'updated'."""
    previous = [{"agent_id": "AGENT-01", "stage": 2, "progress_pct": 40}]
    current = [{"progress_pct": 40, "stage": 2, "agent_id": "AGENT-01"}]
    frame = compute_diff(previous, current)
    assert frame.added == []
    assert frame.updated == []
    assert frame.removed == []
