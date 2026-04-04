import asyncpg
import pytest

from connect4.db.players import create_player, get_player_by_id, get_player_by_username


async def test_create_player(db_conn: asyncpg.Connection) -> None:
    player = await create_player(db_conn, "alice", "hashed_pw")
    assert player is not None
    assert player["username"] == "alice"
    assert player["password_hash"] == "hashed_pw"
    assert len(player["id"]) == 26
    assert player["created_at"] is not None
    assert player["updated_at"] is not None


async def test_create_player_duplicate_username(db_conn: asyncpg.Connection) -> None:
    await create_player(db_conn, "alice", "hashed_pw")
    with pytest.raises(asyncpg.UniqueViolationError):
        await create_player(db_conn, "alice", "other_pw")


async def test_get_player_by_id(db_conn: asyncpg.Connection) -> None:
    player = await create_player(db_conn, "bob", "hashed_pw")
    assert player is not None
    found = await get_player_by_id(db_conn, player["id"])
    assert found is not None
    assert found["username"] == "bob"


async def test_get_player_by_id_not_found(db_conn: asyncpg.Connection) -> None:
    found = await get_player_by_id(db_conn, "00000000000000000000000000")
    assert found is None


async def test_get_player_by_username(db_conn: asyncpg.Connection) -> None:
    await create_player(db_conn, "carol", "hashed_pw")
    found = await get_player_by_username(db_conn, "carol")
    assert found is not None
    assert found["username"] == "carol"


async def test_get_player_by_username_not_found(db_conn: asyncpg.Connection) -> None:
    found = await get_player_by_username(db_conn, "nonexistent")
    assert found is None
