import os

import asyncpg

DEFAULT_DSN = "postgresql://connect4:connect4@localhost:5432/connect4"


async def create_pool(
    dsn: str | None = None,
    *,
    min_size: int = 2,
    max_size: int = 10,
) -> asyncpg.Pool:
    dsn = dsn or os.environ.get("DATABASE_URL", DEFAULT_DSN)
    return await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()
