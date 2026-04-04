import asyncpg

from connect4.db.ulid import generate_ulid


async def create_move(
    conn: asyncpg.Connection,
    game_id: str,
    player_id: str,
    column: int,
    move_number: int,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO moves (id, game_id, player_id, "column", move_number)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        generate_ulid(),
        game_id,
        player_id,
        column,
        move_number,
    )


async def get_game_moves(
    conn: asyncpg.Connection,
    game_id: str,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT * FROM moves
        WHERE game_id = $1
        ORDER BY move_number
        """,
        game_id,
    )
