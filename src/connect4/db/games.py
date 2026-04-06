import asyncpg

from connect4.db.ulid import generate_ulid


async def create_game(
    conn: asyncpg.Connection,
    player1_id: str,
) -> asyncpg.Record | None:
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
) -> asyncpg.Record | None:
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
) -> asyncpg.Record | None:
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


async def list_open_games(
    conn: asyncpg.Connection,
    player_id: str,
    *,
    limit: int = 20,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT g.*, COUNT(m.id)::int AS move_count
        FROM games g
        LEFT JOIN moves m ON m.game_id = g.id
        WHERE g.status = 'waiting' AND g.player1_id != $1
        GROUP BY g.id
        ORDER BY g.id DESC
        LIMIT $2
        """,
        player_id,
        limit,
    )


async def list_player_games(
    conn: asyncpg.Connection,
    player_id: str,
    *,
    cursor: str | None = None,
    limit: int = 20,
) -> list[asyncpg.Record]:
    if cursor is not None:
        return await conn.fetch(
            """
            SELECT g.*, COUNT(m.id)::int AS move_count
            FROM games g
            LEFT JOIN moves m ON m.game_id = g.id
            WHERE (g.player1_id = $1 OR g.player2_id = $1)
              AND g.id < $2
            GROUP BY g.id
            ORDER BY g.id DESC
            LIMIT $3
            """,
            player_id,
            cursor,
            limit,
        )
    return await conn.fetch(
        """
        SELECT g.*, COUNT(m.id)::int AS move_count
        FROM games g
        LEFT JOIN moves m ON m.game_id = g.id
        WHERE g.player1_id = $1 OR g.player2_id = $1
        GROUP BY g.id
        ORDER BY g.id DESC
        LIMIT $2
        """,
        player_id,
        limit,
    )
