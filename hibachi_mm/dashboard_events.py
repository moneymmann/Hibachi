from __future__ import annotations

import asyncio
from collections import deque
from typing import Any


class DashboardEventBus:
    def __init__(self, max_history: int = 2000):
        self._subs: set[asyncio.Queue] = set()
        self._history: deque[dict[str, Any]] = deque(maxlen=max_history)
        self._lock = asyncio.Lock()

    async def publish(self, event: dict[str, Any]) -> None:
        async with self._lock:
            self._history.append(event)
            dead: list[asyncio.Queue] = []
            for q in self._subs:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead.append(q)
            for q in dead:
                self._subs.discard(q)

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subs.add(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            self._subs.discard(q)

    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self._history)[-limit:]
