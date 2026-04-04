import asyncpg

from connect4.db.ulid import generate_ulid


async def create_game(
    conn: asyncpg.Connection,
    player1_id: str,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO games (id, player1_id, status)
        VALUES ($1, $2, 'waiting')
        RETURNING *
        """,
        generate_ulid(),
        player1_id,
    )


async def join_game(
    conn: asyncpg.Connection,
    game_id: str,
    player2_id: str,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        UPDATE games
        SET player2_id = $2, status = 'in_progress'
        WHERE id = $1
        RETURNING *
        """,
        game_id,
        player2_id,
    )


async def get_game_by_id(
    conn: asyncpg.Connection,
    game_id: str,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT * FROM games WHERE id = $1",
        game_id,
    )


async def update_game_status(
    conn: asyncpg.Connection,
    game_id: str,
    status: str,
    winner_id: str | None = None,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        UPDATE games
        SET status = $2, winner_id = $3
        WHERE id = $1
        RETURNING *
        """,
        game_id,
        status,
        winner_id,
    )


async def list_player_games(
    conn: asyncpg.Connection,
    player_id: str,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT * FROM games
        WHERE player1_id = $1 OR player2_id = $1
        ORDER BY created_at DESC
        """,
        player_id,
    )
