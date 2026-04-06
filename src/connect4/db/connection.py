import asyncpg

from connect4.config import get_settings


async def create_pool(
    dsn: str | None = None,
    *,
    min_size: int = 2,
    max_size: int = 10,
) -> asyncpg.Pool:
    dsn = dsn or str(get_settings().database_url)
    return await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()
