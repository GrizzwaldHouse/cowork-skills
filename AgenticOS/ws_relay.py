# ws_relay.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Authenticated WebSocket relay that forwards /ws frames over
#          Tailscale so Marcus's iPhone and Claude Desktop can see the
#          live AgenticOS HUD without a separate browser session.
#          Adds a token-check gate (TAILSCALE_AUTH_TOKEN from .env) so
#          only Marcus's devices can connect. The desktop React HUD
#          connects to the main server unchanged; this relay is the
#          additional remote access path.

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.client import WebSocketClientProtocol

from AgenticOS.config import (
    LOGGER_NAME,
    TAILSCALE_AUTH_TOKEN,
    WEBSOCKET_PORT,
    SERVER_HOST,
)

_logger = logging.getLogger(f"{LOGGER_NAME}.ws_relay")

# Port the relay binds on (distinct from the main server port so both
# can run simultaneously). Phone browser connects to this port.
RELAY_PORT = WEBSOCKET_PORT + 1  # 7843 by default

# Internal upstream (the main FastAPI WebSocket).
_UPSTREAM_URL = f"ws://127.0.0.1:{WEBSOCKET_PORT}/ws"


# ---------------------------------------------------------------------------
# Auth check
# ---------------------------------------------------------------------------

def _check_token(websocket: WebSocketServerProtocol) -> bool:
    """Return True if the connecting client supplies the correct token.

    Token is passed as a query param: wss://hostname:7843/?token=<secret>.
    When TAILSCALE_AUTH_TOKEN is empty (dev/test), all connections pass.
    """
    if not TAILSCALE_AUTH_TOKEN:
        _logger.debug("No auth token configured; relay running open (dev mode)")
        return True
    query = websocket.request.path if hasattr(websocket, "request") else ""
    token_param = ""
    if "token=" in query:
        # Parse the token query param manually to avoid adding urllib overhead.
        for part in query.split("&"):
            if part.startswith("token=") or part.startswith("?token="):
                token_param = part.split("=", 1)[1]
                break
    return token_param == TAILSCALE_AUTH_TOKEN


# ---------------------------------------------------------------------------
# Per-connection relay coroutine
# ---------------------------------------------------------------------------

async def _relay_connection(
    remote: WebSocketServerProtocol,
) -> None:
    """Bridge one remote client to the upstream AgenticOS WebSocket."""
    if not _check_token(remote):
        await remote.close(code=4401, reason="Unauthorized")
        _logger.warning("Rejected unauthenticated relay connection from %s", remote.remote_address)
        return

    _logger.info("Relay connection from %s", remote.remote_address)

    try:
        async with websockets.connect(_UPSTREAM_URL) as upstream:
            # Bidirectional relay: forward frames in both directions
            # concurrently until either side disconnects.
            async def forward_up() -> None:
                async for msg in remote:
                    await upstream.send(msg)

            async def forward_down() -> None:
                async for msg in upstream:
                    await remote.send(msg)

            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(forward_up()),
                    asyncio.create_task(forward_down()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
    except websockets.exceptions.ConnectionClosed:
        pass
    except OSError as exc:
        _logger.warning("Could not connect to upstream AgenticOS WS: %s", exc)
    finally:
        _logger.info("Relay connection closed for %s", remote.remote_address)


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

async def run_relay(stop_event: Optional[asyncio.Event] = None) -> None:
    """Start the relay server and run until stop_event is set (or forever)."""
    _logger.info("WS relay starting on 0.0.0.0:%d", RELAY_PORT)
    async with websockets.serve(
        _relay_connection,
        "0.0.0.0",
        RELAY_PORT,
    ) as server:
        _logger.info(
            "WS relay ready — remote clients connect to ws://<tailscale-host>:%d/?token=<secret>",
            RELAY_PORT,
        )
        if stop_event is not None:
            await stop_event.wait()
        else:
            await asyncio.get_running_loop().create_future()  # run forever


def main() -> None:
    """CLI entry point: ``python -m AgenticOS.ws_relay``."""
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        stream=sys.stderr,
    )
    asyncio.run(run_relay())


if __name__ == "__main__":
    main()
