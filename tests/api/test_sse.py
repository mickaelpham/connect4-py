import asyncio
import json
from collections.abc import AsyncGenerator

import asyncpg
import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from connect4.api.auth import router as auth_router
from connect4.api.games import router as games_router
from connect4.api.rate_limit import limiter
from connect4.api.sse import GameEventBroker
from connect4.config import get_settings

pytestmark = pytest.mark.usefixtures("_clean_tables")


@pytest_asyncio.fixture(loop_scope="session")
async def broker(db_pool: asyncpg.Pool) -> AsyncGenerator[GameEventBroker]:
    b = GameEventBroker()
    await b.start(str(get_settings().database_url))
    yield b
    await b.stop()


@pytest_asyncio.fixture(loop_scope="session")
async def sse_app(
    db_pool: asyncpg.Pool,
    broker: GameEventBroker,
) -> AsyncGenerator[FastAPI]:
    limiter.enabled = False

    test_app = FastAPI()
    test_app.state.db_pool = db_pool
    test_app.state.event_broker = broker

    test_app.include_router(auth_router, prefix="/api")
    test_app.include_router(games_router, prefix="/api")

    yield test_app

    limiter.enabled = True


@pytest_asyncio.fixture(loop_scope="session")
async def sse_client(
    sse_app: FastAPI,
) -> AsyncGenerator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=sse_app),
        base_url="http://test",
    ) as client:
        yield client


async def _register(client: httpx.AsyncClient, username: str) -> dict:
    resp = await client.post(
        "/api/register",
        json={"username": username, "password": "password123"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _get_token(client: httpx.AsyncClient, username: str) -> str:
    tokens = await _register(client, username)
    return tokens["access_token"]


async def _auth_header(client: httpx.AsyncClient, username: str) -> dict[str, str]:
    tokens = await _register(client, username)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _create_game(client: httpx.AsyncClient, headers: dict[str, str]) -> dict:
    resp = await client.post("/api/games", headers=headers)
    assert resp.status_code == 201
    return resp.json()


# --- SSE endpoint auth/error tests (non-streaming, verified via status code) ---


async def test_sse_invalid_token(sse_client: httpx.AsyncClient):
    resp = await sse_client.get("/api/games/fake-game/stream?token=bad-token")
    assert resp.status_code == 401


async def test_sse_missing_token(sse_client: httpx.AsyncClient):
    resp = await sse_client.get("/api/games/fake-game/stream")
    assert resp.status_code == 422


async def test_sse_game_not_found(sse_client: httpx.AsyncClient):
    token = await _get_token(sse_client, "sse_notfound")
    resp = await sse_client.get(f"/api/games/nonexistent/stream?token={token}")
    assert resp.status_code == 404


# --- GameEventBroker unit tests ---


async def test_broker_subscribe_receives_notification(
    broker: GameEventBroker, db_pool: asyncpg.Pool
):
    """Subscriber receives pg_notify payload for its game."""
    game_id = "test-game-1"
    payload = json.dumps({
        "game_id": game_id,
        "event": "move",
        "data": {"board": []},
    })

    async with broker.subscribe(game_id) as queue:
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT pg_notify('game_events', $1)", payload)

        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        parsed = json.loads(msg)
        assert parsed["game_id"] == game_id
        assert parsed["event"] == "move"


async def test_broker_ignores_other_games(
    broker: GameEventBroker, db_pool: asyncpg.Pool
):
    """Subscriber does not receive notifications for other games."""
    payload = json.dumps({
        "game_id": "other-game",
        "event": "move",
        "data": {},
    })

    async with broker.subscribe("my-game") as queue:
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT pg_notify('game_events', $1)", payload)

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.5)


async def test_broker_multiple_subscribers(
    broker: GameEventBroker, db_pool: asyncpg.Pool
):
    """Multiple subscribers to the same game all receive the event."""
    game_id = "multi-sub-game"
    payload = json.dumps({
        "game_id": game_id,
        "event": "move",
        "data": {},
    })

    async with (
        broker.subscribe(game_id) as q1,
        broker.subscribe(game_id) as q2,
    ):
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT pg_notify('game_events', $1)", payload)

        msg1 = await asyncio.wait_for(q1.get(), timeout=2.0)
        msg2 = await asyncio.wait_for(q2.get(), timeout=2.0)
        assert json.loads(msg1)["game_id"] == game_id
        assert json.loads(msg2)["game_id"] == game_id


async def test_broker_cleanup_on_unsubscribe(broker: GameEventBroker):
    """After unsubscribe, game_id is removed from subscribers dict."""
    game_id = "cleanup-game"

    async with broker.subscribe(game_id):
        assert game_id in broker._subscribers

    assert game_id not in broker._subscribers


# --- Integration: pg_notify fired from game endpoints ---


async def test_move_fires_notification(
    sse_client: httpx.AsyncClient,
    broker: GameEventBroker,
):
    """Playing a move sends a pg_notify with the correct event type."""
    h1 = await _auth_header(sse_client, "notify_p1")
    h2 = await _auth_header(sse_client, "notify_p2")
    game = await _create_game(sse_client, h1)
    await sse_client.post(f"/api/games/{game['id']}/join", headers=h2)

    async with broker.subscribe(game["id"]) as queue:
        resp = await sse_client.post(
            f"/api/games/{game['id']}/moves",
            json={"column": 3},
            headers=h1,
        )
        assert resp.status_code == 201

        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        parsed = json.loads(msg)
        assert parsed["event"] == "move"
        assert parsed["data"]["move_count"] == 1
        assert parsed["data"]["board"][5][3] != 0


async def test_join_fires_notification(
    sse_client: httpx.AsyncClient,
    broker: GameEventBroker,
):
    """Joining a game sends a pg_notify with player_joined event."""
    h1 = await _auth_header(sse_client, "notifyjoin_p1")
    h2 = await _auth_header(sse_client, "notifyjoin_p2")
    game = await _create_game(sse_client, h1)

    async with broker.subscribe(game["id"]) as queue:
        resp = await sse_client.post(
            f"/api/games/{game['id']}/join",
            headers=h2,
        )
        assert resp.status_code == 200

        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        parsed = json.loads(msg)
        assert parsed["event"] == "player_joined"
        assert parsed["data"]["status"] == "in_progress"
        assert parsed["data"]["player2"]["username"] == "notifyjoin_p2"


async def test_winning_move_fires_game_over(
    sse_client: httpx.AsyncClient,
    broker: GameEventBroker,
):
    """A winning move sends a game_over notification."""
    h1 = await _auth_header(sse_client, "notifywin_p1")
    h2 = await _auth_header(sse_client, "notifywin_p2")
    game = await _create_game(sse_client, h1)
    await sse_client.post(f"/api/games/{game['id']}/join", headers=h2)

    # P1 wins with horizontal 4: cols 0,1,2,3
    moves = [(h1, 0), (h2, 0), (h1, 1), (h2, 1), (h1, 2), (h2, 2)]
    for headers, col in moves:
        resp = await sse_client.post(
            f"/api/games/{game['id']}/moves",
            json={"column": col},
            headers=headers,
        )
        assert resp.status_code == 201

    async with broker.subscribe(game["id"]) as queue:
        # P1 winning move
        resp = await sse_client.post(
            f"/api/games/{game['id']}/moves",
            json={"column": 3},
            headers=h1,
        )
        assert resp.status_code == 201

        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        parsed = json.loads(msg)
        assert parsed["event"] == "game_over"
        assert parsed["data"]["status"] == "won"
        assert parsed["data"]["winner"]["username"] == "notifywin_p1"
