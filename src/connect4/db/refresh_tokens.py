from datetime import UTC, datetime, timedelta

import asyncpg

from connect4.db.ulid import generate_ulid

REFRESH_TOKEN_EXPIRE_DAYS = 7


async def create_refresh_token(
    conn: asyncpg.Connection,
    player_id: str,
    token_hash: str,
) -> asyncpg.Record | None:
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return await conn.fetchrow(
        """
        INSERT INTO refresh_tokens (id, player_id, token_hash, expires_at)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        generate_ulid(),
        player_id,
        token_hash,
        expires_at,
    )


async def get_refresh_token_by_hash(
    conn: asyncpg.Connection,
    token_hash: str,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT * FROM refresh_tokens
        WHERE token_hash = $1
          AND revoked_at IS NULL
          AND expires_at > now()
        """,
        token_hash,
    )


async def revoke_refresh_token(
    conn: asyncpg.Connection,
    token_id: str,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        UPDATE refresh_tokens
        SET revoked_at = now()
        WHERE id = $1
        RETURNING *
        """,
        token_id,
    )


async def revoke_all_player_tokens(
    conn: asyncpg.Connection,
    player_id: str,
) -> None:
    await conn.execute(
        """
        UPDATE refresh_tokens
        SET revoked_at = now()
        WHERE player_id = $1
          AND revoked_at IS NULL
        """,
        player_id,
    )
