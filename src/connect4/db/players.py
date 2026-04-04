import asyncpg

from connect4.db.ulid import generate_ulid


async def create_player(
    conn: asyncpg.Connection,
    username: str,
    password_hash: str,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO players (id, username, password_hash)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        generate_ulid(),
        username,
        password_hash,
    )


async def get_player_by_id(
    conn: asyncpg.Connection,
    player_id: str,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT * FROM players WHERE id = $1",
        player_id,
    )


async def get_player_by_username(
    conn: asyncpg.Connection,
    username: str,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT * FROM players WHERE username = $1",
        username,
    )
