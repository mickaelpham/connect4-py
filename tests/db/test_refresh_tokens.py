import asyncpg

from connect4.db.players import create_player
from connect4.db.refresh_tokens import (
    create_refresh_token,
    get_refresh_token_by_hash,
    revoke_all_player_tokens,
    revoke_refresh_token,
)


async def _make_player(conn: asyncpg.Connection, username: str) -> str:
    player = await create_player(conn, username, "hashed_pw")
    assert player is not None
    return player["id"]


async def test_create_and_get_refresh_token(db_conn):
    player_id = await _make_player(db_conn, "tokenuser1")
    token_hash = "a" * 64

    record = await create_refresh_token(db_conn, player_id, token_hash)
    assert record is not None
    assert record["player_id"] == player_id
    assert record["token_hash"] == token_hash
    assert record["revoked_at"] is None

    fetched = await get_refresh_token_by_hash(db_conn, token_hash)
    assert fetched is not None
    assert fetched["id"] == record["id"]


async def test_get_expired_token_returns_none(db_conn):
    player_id = await _make_player(db_conn, "tokenuser2")
    token_hash = "b" * 64

    # Insert a token that already expired
    await db_conn.execute(
        """
        INSERT INTO refresh_tokens (id, player_id, token_hash, expires_at)
        VALUES ('00000000000000000000000001', $1, $2, now() - interval '1 day')
        """,
        player_id,
        token_hash,
    )

    fetched = await get_refresh_token_by_hash(db_conn, token_hash)
    assert fetched is None


async def test_revoke_refresh_token(db_conn):
    player_id = await _make_player(db_conn, "tokenuser3")
    token_hash = "c" * 64

    record = await create_refresh_token(db_conn, player_id, token_hash)
    assert record is not None

    revoked = await revoke_refresh_token(db_conn, record["id"])
    assert revoked is not None
    assert revoked["revoked_at"] is not None

    fetched = await get_refresh_token_by_hash(db_conn, token_hash)
    assert fetched is None


async def test_revoke_all_player_tokens(db_conn):
    player_id = await _make_player(db_conn, "tokenuser4")

    await create_refresh_token(db_conn, player_id, "d" * 64)
    await create_refresh_token(db_conn, player_id, "e" * 64)

    await revoke_all_player_tokens(db_conn, player_id)

    assert await get_refresh_token_by_hash(db_conn, "d" * 64) is None
    assert await get_refresh_token_by_hash(db_conn, "e" * 64) is None
