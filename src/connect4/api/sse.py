import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg


class GameEventBroker:
    """Shared PG LISTEN/NOTIFY fan-out for SSE game events.

    One dedicated asyncpg connection listens on the ``game_events`` channel.
    Each SSE client subscribes with a game_id and gets an asyncio.Queue that
    receives JSON payloads for that game only.
    """

    def __init__(self) -> None:
        self._conn: asyncpg.Connection | None = None
        self._subscribers: dict[str, set[asyncio.Queue[str]]] = {}

    async def start(self, dsn: str) -> None:
        self._conn = await asyncpg.connect(dsn)
        await self._conn.add_listener("game_events", self._on_notification)

    async def stop(self) -> None:
        if self._conn is not None:
            await self._conn.remove_listener("game_events", self._on_notification)
            await self._conn.close()
            self._conn = None

    def _on_notification(
        self,
        conn: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return
        game_id = data.get("game_id")
        if game_id is None:
            return
        for queue in self._subscribers.get(game_id, set()):
            queue.put_nowait(payload)

    @asynccontextmanager
    async def subscribe(self, game_id: str) -> AsyncIterator[asyncio.Queue[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        subs = self._subscribers.setdefault(game_id, set())
        subs.add(queue)
        try:
            yield queue
        finally:
            subs.discard(queue)
            if not subs:
                self._subscribers.pop(game_id, None)
