import asyncpg

from connect4.db.games import (
    create_game,
    get_game_by_id,
    join_game,
    list_player_games,
    update_game_status,
)
from connect4.db.players import create_player


async def _make_player(conn: asyncpg.Connection, username: str) -> asyncpg.Record:
    return await create_player(conn, username, "hashed_pw")


async def test_create_game(db_conn: asyncpg.Connection) -> None:
    player = await _make_player(db_conn, "alice")
    game = await create_game(db_conn, player["id"])
    assert game["player1_id"] == player["id"]
    assert game["player2_id"] is None
    assert game["status"] == "waiting"
    assert game["winner_id"] is None
    assert len(game["id"]) == 26


async def test_join_game(db_conn: asyncpg.Connection) -> None:
    p1 = await _make_player(db_conn, "alice")
    p2 = await _make_player(db_conn, "bob")
    game = await create_game(db_conn, p1["id"])
    updated = await join_game(db_conn, game["id"], p2["id"])
    assert updated["player2_id"] == p2["id"]
    assert updated["status"] == "in_progress"


async def test_get_game_by_id(db_conn: asyncpg.Connection) -> None:
    player = await _make_player(db_conn, "alice")
    game = await create_game(db_conn, player["id"])
    found = await get_game_by_id(db_conn, game["id"])
    assert found is not None
    assert found["id"] == game["id"]


async def test_get_game_by_id_not_found(db_conn: asyncpg.Connection) -> None:
    found = await get_game_by_id(db_conn, "00000000000000000000000000")
    assert found is None


async def test_update_game_status_won(db_conn: asyncpg.Connection) -> None:
    p1 = await _make_player(db_conn, "alice")
    p2 = await _make_player(db_conn, "bob")
    game = await create_game(db_conn, p1["id"])
    await join_game(db_conn, game["id"], p2["id"])
    updated = await update_game_status(db_conn, game["id"], "won", p1["id"])
    assert updated["status"] == "won"
    assert updated["winner_id"] == p1["id"]


async def test_update_game_status_draw(db_conn: asyncpg.Connection) -> None:
    p1 = await _make_player(db_conn, "alice")
    p2 = await _make_player(db_conn, "bob")
    game = await create_game(db_conn, p1["id"])
    await join_game(db_conn, game["id"], p2["id"])
    updated = await update_game_status(db_conn, game["id"], "draw")
    assert updated["status"] == "draw"
    assert updated["winner_id"] is None


async def test_list_player_games(db_conn: asyncpg.Connection) -> None:
    p1 = await _make_player(db_conn, "alice")
    p2 = await _make_player(db_conn, "bob")
    await create_game(db_conn, p1["id"])
    game2 = await create_game(db_conn, p2["id"])
    await join_game(db_conn, game2["id"], p1["id"])

    games = await list_player_games(db_conn, p1["id"])
    assert len(games) == 2


async def test_list_player_games_empty(db_conn: asyncpg.Connection) -> None:
    player = await _make_player(db_conn, "alice")
    games = await list_player_games(db_conn, player["id"])
    assert games == []
