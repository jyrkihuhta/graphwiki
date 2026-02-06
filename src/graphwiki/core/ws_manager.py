"""WebSocket connection manager with event fanout.

Polls the graph engine for events and broadcasts them to all
connected WebSocket clients via per-client asyncio queues.
"""

import asyncio
import logging
from typing import Any

from graphwiki.core.graph import get_engine

logger = logging.getLogger(__name__)


def _event_to_dict(event: Any) -> dict[str, Any]:
    """Convert a GraphEvent to a JSON-serializable dict."""
    d: dict[str, Any] = {"type": event.event_type()}
    if event.page_name() is not None:
        d["page"] = event.page_name()
    if event.link_from() is not None:
        d["from"] = event.link_from()
        d["to"] = event.link_to()
    return d


class ConnectionManager:
    """Manages WebSocket connections and fans out graph events."""

    def __init__(self) -> None:
        self._clients: dict[int, asyncio.Queue[dict[str, Any]]] = {}
        self._next_id: int = 0
        self._poll_task: asyncio.Task | None = None
        self._running: bool = False

    def connect(self) -> tuple[int, asyncio.Queue[dict[str, Any]]]:
        """Register a new client. Returns (client_id, queue)."""
        client_id = self._next_id
        self._next_id += 1
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        self._clients[client_id] = queue
        logger.info(
            "WebSocket client %d connected (%d total)",
            client_id,
            len(self._clients),
        )
        return client_id, queue

    def disconnect(self, client_id: int) -> None:
        """Unregister a client."""
        self._clients.pop(client_id, None)
        logger.info(
            "WebSocket client %d disconnected (%d total)",
            client_id,
            len(self._clients),
        )

    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self._clients)

    def start_polling(self, interval: float = 0.5) -> None:
        """Start the background polling task."""
        if self._poll_task is not None:
            return
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop(interval))

    def stop_polling(self) -> None:
        """Stop the background polling task."""
        self._running = False
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None

    async def _poll_loop(self, interval: float) -> None:
        """Poll engine for events and broadcast to all clients."""
        while self._running:
            try:
                engine = get_engine()
                if engine is not None and engine.has_pending_events():
                    events = engine.poll_events()
                    for event in events:
                        msg = _event_to_dict(event)
                        await self._broadcast(msg)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error polling graph events")
            await asyncio.sleep(interval)

    async def _broadcast(self, msg: dict[str, Any]) -> None:
        """Send a message to all connected clients."""
        for client_id, queue in list(self._clients.items()):
            try:
                queue.put_nowait(msg)
            except asyncio.QueueFull:
                logger.warning("Client %d queue full, dropping event", client_id)


# Module-level singleton
manager = ConnectionManager()
