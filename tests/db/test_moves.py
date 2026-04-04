import asyncpg
import pytest

from connect4.db.games import create_game, join_game
from connect4.db.moves import create_move, get_game_moves
from connect4.db.players import create_player


async def _setup_game(conn: asyncpg.Connection) -> tuple[str, str, str]:
    """Create two players and an in-progress game. Returns (game_id, p1_id, p2_id)."""
    p1 = await create_player(conn, "alice", "hashed_pw")
    p2 = await create_player(conn, "bob", "hashed_pw")
    assert p1 is not None
    assert p2 is not None
    game = await create_game(conn, p1["id"])
    assert game is not None
    await join_game(conn, game["id"], p2["id"])
    return game["id"], p1["id"], p2["id"]


async def test_create_move(db_conn: asyncpg.Connection) -> None:
    game_id, p1_id, _ = await _setup_game(db_conn)
    move = await create_move(db_conn, game_id, p1_id, column=3, move_number=1)
    assert move is not None
    assert move["game_id"] == game_id
    assert move["player_id"] == p1_id
    assert move["column"] == 3
    assert move["move_number"] == 1
    assert len(move["id"]) == 26


async def test_get_game_moves_ordered(db_conn: asyncpg.Connection) -> None:
    game_id, p1_id, p2_id = await _setup_game(db_conn)
    await create_move(db_conn, game_id, p1_id, column=3, move_number=1)
    await create_move(db_conn, game_id, p2_id, column=4, move_number=2)
    await create_move(db_conn, game_id, p1_id, column=3, move_number=3)

    moves = await get_game_moves(db_conn, game_id)
    assert len(moves) == 3
    assert [m["move_number"] for m in moves] == [1, 2, 3]
    assert [m["column"] for m in moves] == [3, 4, 3]


async def test_get_game_moves_empty(db_conn: asyncpg.Connection) -> None:
    game_id, _, _ = await _setup_game(db_conn)
    moves = await get_game_moves(db_conn, game_id)
    assert moves == []


async def test_duplicate_move_number_raises(db_conn: asyncpg.Connection) -> None:
    game_id, p1_id, p2_id = await _setup_game(db_conn)
    await create_move(db_conn, game_id, p1_id, column=3, move_number=1)
    with pytest.raises(asyncpg.UniqueViolationError):
        await create_move(db_conn, game_id, p2_id, column=4, move_number=1)
