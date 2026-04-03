"""In-memory terminal session registry for live task streaming.

Each session corresponds to an active task (status=in_progress).
The orchestrator pushes PTY chunks via the API; the WebSocket endpoint
drains them to the browser.
"""

import asyncio

_sessions: dict[str, asyncio.Queue[str | None]] = {}


def create_session(task_name: str) -> None:
    """Open a new terminal session for *task_name*.

    Called when a task transitions to ``in_progress``.
    Silently replaces any existing session for the same task.
    """
    _sessions[task_name] = asyncio.Queue(maxsize=10_000)


def get_session(task_name: str) -> "asyncio.Queue[str | None] | None":
    """Return the active queue for *task_name*, or ``None`` if not running."""
    return _sessions.get(task_name)


async def put_chunk(task_name: str, data: str) -> None:
    """Enqueue a PTY data chunk.  Drops silently if the queue is full."""
    q = _sessions.get(task_name)
    if q is not None:
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass


async def close_session(task_name: str) -> None:
    """Close the session by pushing a sentinel and removing it from the registry.

    The WebSocket handler will exit its loop when it dequeues ``None``.
    Called when a task transitions away from ``in_progress``.
    """
    q = _sessions.pop(task_name, None)
    if q is not None:
        try:
            q.put_nowait(None)
        except asyncio.QueueFull:
            pass
