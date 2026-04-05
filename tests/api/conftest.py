from collections.abc import AsyncGenerator

import asyncpg
import pytest_asyncio


@pytest_asyncio.fixture(loop_scope="session")
async def _clean_tables(db_pool: asyncpg.Pool) -> AsyncGenerator[None]:
    """Truncate tables after each API integration test for isolation."""
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE refresh_tokens, moves, games, players CASCADE")
