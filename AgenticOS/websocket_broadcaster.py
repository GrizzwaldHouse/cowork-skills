# websocket_broadcaster.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Manages all connected WebSocket clients for the AgenticOS
#          Command Center and broadcasts state to them. Computes the
#          diff between the previously broadcast state and the current
#          state so that clients receive minimal payloads. Handles
#          disconnects cleanly, removing dead sockets without raising.

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

from AgenticOS.config import LOGGER_NAME
from AgenticOS.models import AgentState


# Module logger; child of the project-wide AgenticOS logger.
_logger = logging.getLogger(f"{LOGGER_NAME}.websocket_broadcaster")


class WebSocketLike(Protocol):
    """Structural type for the subset of starlette WebSocket we use.
    Defining it as a Protocol lets the unit tests inject AsyncMocks
    without depending on the real FastAPI runtime."""

    async def accept(self) -> None: ...
    async def send_text(self, data: str) -> None: ...
    async def close(self, code: int = 1000) -> None: ...


# ---------------------------------------------------------------------------
# Diff message shape
# ---------------------------------------------------------------------------

# Discriminator strings sent over the wire. Constants so the React
# client and the Python server share a single source of truth at code
# review time even though the languages do not share an enum type.
MESSAGE_TYPE_SNAPSHOT = "snapshot"
MESSAGE_TYPE_DIFF = "diff"


@dataclass
class _BroadcastFrame:
    """In-memory representation of a single broadcast frame. Converted
    to JSON via ``to_json`` before transmission."""

    # 'snapshot' for the initial frame on connect; 'diff' thereafter.
    message_type: str

    # When ``message_type == 'snapshot'``, this is the full agent list.
    # When ``message_type == 'diff'``, the lists below are populated.
    agents: list[dict[str, Any]] = field(default_factory=list)

    # Agents present in the new state but not the previous.
    added: list[dict[str, Any]] = field(default_factory=list)

    # Agents whose serialised payload changed between the two states.
    updated: list[dict[str, Any]] = field(default_factory=list)

    # agent_ids that disappeared from the new state.
    removed: list[str] = field(default_factory=list)

    # ISO 8601 UTC server timestamp when this frame was generated.
    sent_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_json(self) -> str:
        """Serialize this frame to a JSON string for WebSocket transmission."""
        return json.dumps(
            {
                "type": self.message_type,
                "agents": self.agents,
                "added": self.added,
                "updated": self.updated,
                "removed": self.removed,
                "sent_at": self.sent_at,
            },
            default=str,
        )


# ---------------------------------------------------------------------------
# Diff computation
# ---------------------------------------------------------------------------

def _index_by_id(agents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return a dict keyed by agent_id for O(1) lookup during diffing.
    Skips entries lacking an agent_id so a malformed row cannot crash
    the broadcaster."""
    index: dict[str, dict[str, Any]] = {}
    for agent in agents:
        agent_id = agent.get("agent_id")
        if isinstance(agent_id, str) and agent_id:
            index[agent_id] = agent
    return index


def compute_diff(
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> _BroadcastFrame:
    """Return a diff frame comparing ``previous`` to ``current``. The
    comparison is structural: two agent dicts are considered equal iff
    their JSON serialisations match. Field order does not matter."""
    prev_index = _index_by_id(previous)
    curr_index = _index_by_id(current)

    added: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []
    removed: list[str] = []

    for agent_id, agent in curr_index.items():
        if agent_id not in prev_index:
            # New agent appeared between snapshots.
            added.append(agent)
        else:
            # Compare canonicalised JSON to detect content changes.
            # sort_keys ensures field order does not generate false diffs.
            if json.dumps(agent, sort_keys=True, default=str) != json.dumps(
                prev_index[agent_id], sort_keys=True, default=str
            ):
                updated.append(agent)

    for agent_id in prev_index:
        if agent_id not in curr_index:
            # Agent disappeared from the live state.
            removed.append(agent_id)

    return _BroadcastFrame(
        message_type=MESSAGE_TYPE_DIFF,
        added=added,
        updated=updated,
        removed=removed,
    )


# ---------------------------------------------------------------------------
# WebSocketBroadcaster
# ---------------------------------------------------------------------------

class WebSocketBroadcaster:
    """Owns the set of active WebSocket clients and broadcasts diffs.

    The broadcaster is event-driven: ``broadcast_state`` is called by
    the file watcher on every change to agents.json, and the
    broadcaster sends only the diff (additions, updates, removals) to
    every connected client. New clients receive a full snapshot on
    connect so they can rebuild their local view from scratch."""

    def __init__(self) -> None:
        # All currently connected clients.
        self._connections: list[WebSocketLike] = []

        # Last full state we broadcast, used as the baseline for diffs.
        self._last_state: list[dict[str, Any]] = []

        # asyncio lock that serialises mutations to ``_connections`` and
        # ``_last_state`` so concurrent broadcasts cannot interleave.
        self._lock: asyncio.Lock = asyncio.Lock()

    # ----- Connection management -----------------------------------------

    @property
    def active_connections(self) -> list[WebSocketLike]:
        """Read-only view of the active connection list. Returned as a
        copy so callers cannot mutate the broadcaster's internal state."""
        return list(self._connections)

    @property
    def connection_count(self) -> int:
        """Number of currently connected WebSocket clients."""
        return len(self._connections)

    async def connect(self, websocket: WebSocketLike) -> None:
        """Accept the WebSocket handshake, register the connection, and
        immediately send the latest known state as a snapshot frame so
        the new client renders from a complete baseline."""
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)
            snapshot = _BroadcastFrame(
                message_type=MESSAGE_TYPE_SNAPSHOT,
                agents=list(self._last_state),
            )
        # Send the snapshot outside the lock to avoid holding it while
        # network I/O is in progress.
        try:
            await websocket.send_text(snapshot.to_json())
        except Exception as exc:
            # If the very first send fails the connection is already
            # dead; remove it and keep going.
            _logger.warning(
                "Snapshot send failed on new connection: %s; dropping", exc
            )
            await self._remove(websocket)
            return

        _logger.info(
            "WebSocket client connected; total active = %d",
            self.connection_count,
        )

    async def disconnect(self, websocket: WebSocketLike) -> None:
        """Remove a client that has disconnected cleanly."""
        await self._remove(websocket)
        _logger.info(
            "WebSocket client disconnected; total active = %d",
            self.connection_count,
        )

    async def _remove(self, websocket: WebSocketLike) -> None:
        """Internal helper to drop a connection from the active list."""
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    # ----- Broadcast paths ------------------------------------------------

    async def broadcast_state(self, current_state: list[AgentState]) -> None:
        """Diff ``current_state`` against the last broadcast and send the
        result to every connected client. If there are no connections
        we still update the cached state so a subsequent connect sends
        an accurate snapshot."""
        # Serialise once, up front, so every connection receives an
        # identical payload and we do not pay the JSON cost per client.
        current_payload = [agent.model_dump(mode="json") for agent in current_state]

        async with self._lock:
            previous_payload = list(self._last_state)
            self._last_state = current_payload
            connections_snapshot = list(self._connections)

        if not connections_snapshot:
            # Nothing to do; cached state has been updated above.
            return

        frame = compute_diff(previous_payload, current_payload)

        # Skip empty diffs to avoid spamming clients with no-ops. An
        # initial connect always receives a snapshot via connect(), so
        # there is no risk of a brand-new client missing data here.
        if not frame.added and not frame.updated and not frame.removed:
            return

        await self._send_to_all(frame.to_json(), connections_snapshot)

    async def broadcast_snapshot(self, current_state: list[AgentState]) -> None:
        """Force a full-snapshot broadcast to every client. Useful after
        a server-side reset or when clients explicitly request a resync."""
        current_payload = [agent.model_dump(mode="json") for agent in current_state]

        async with self._lock:
            self._last_state = current_payload
            connections_snapshot = list(self._connections)

        if not connections_snapshot:
            return

        frame = _BroadcastFrame(
            message_type=MESSAGE_TYPE_SNAPSHOT,
            agents=current_payload,
        )
        await self._send_to_all(frame.to_json(), connections_snapshot)

    async def _send_to_all(
        self,
        payload: str,
        connections: list[WebSocketLike],
    ) -> None:
        """Send ``payload`` to every connection; remove any that fail."""
        # asyncio.gather collects every send in parallel and surfaces
        # exceptions per-connection without aborting the others.
        results = await asyncio.gather(
            *(self._safe_send(conn, payload) for conn in connections),
            return_exceptions=False,
        )

        # Each ``False`` in results means that send failed; drop the
        # corresponding connection.
        dead: list[WebSocketLike] = [
            conn for conn, ok in zip(connections, results) if not ok
        ]
        if dead:
            async with self._lock:
                for conn in dead:
                    if conn in self._connections:
                        self._connections.remove(conn)
            _logger.info(
                "Pruned %d dead WebSocket connections; total active = %d",
                len(dead),
                self.connection_count,
            )

    async def _safe_send(
        self,
        connection: WebSocketLike,
        payload: str,
    ) -> bool:
        """Send a payload to one connection; return True on success."""
        try:
            await connection.send_text(payload)
            return True
        except Exception as exc:
            # Any exception means the socket is unusable. Logged at
            # warning level rather than error because routine client
            # disconnects produce these constantly.
            _logger.warning("WebSocket send failed: %s", exc)
            return False

    async def reset(self) -> None:
        """Drop all connections and clear cached state. Used by tests
        and by the server when it needs to start from a clean slate."""
        async with self._lock:
            for connection in list(self._connections):
                # close() may itself fail on a dead socket; suppress.
                try:
                    await connection.close()
                except Exception:
                    pass
            self._connections.clear()
            self._last_state = []


# ---------------------------------------------------------------------------
# Module-level singleton
#
# Exported so the FastAPI app and the file_watcher callback share the
# same broadcaster instance without having to plumb it through every
# function call. This is the only mutable module-level state in the
# package and it is encapsulated inside the class.
# ---------------------------------------------------------------------------

broadcaster: Optional[WebSocketBroadcaster] = None


def get_broadcaster() -> WebSocketBroadcaster:
    """Return the process-wide broadcaster, instantiating it lazily on
    first call. Callers must use this rather than ``broadcaster`` so
    tests can substitute their own instance via patching."""
    global broadcaster
    if broadcaster is None:
        broadcaster = WebSocketBroadcaster()
    return broadcaster
