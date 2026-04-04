import os
import subprocess
from collections.abc import AsyncGenerator

import asyncpg
import httpx
import pytest_asyncio

TEST_DSN = "postgresql://connect4:connect4@localhost:5432/connect4_test"
TEST_DSN_ALEMBIC = "postgresql+psycopg://connect4:connect4@localhost:5432/connect4_test"
TEST_JWT_SECRET = "test-secret-key-do-not-use-in-production"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_pool() -> AsyncGenerator[asyncpg.Pool]:
    # Ensure the test database exists
    sys_conn = await asyncpg.connect(
        "postgresql://connect4:connect4@localhost:5432/connect4"
    )
    try:
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'connect4_test'"
        )
        if not exists:
            await sys_conn.execute("CREATE DATABASE connect4_test")
    finally:
        await sys_conn.close()

    # Run Alembic migrations on the test database
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": TEST_DSN_ALEMBIC},
        check=True,
    )

    pool = await asyncpg.create_pool(TEST_DSN, min_size=2, max_size=5)
    yield pool
    await pool.close()


@pytest_asyncio.fixture(loop_scope="session")
async def db_conn(
    db_pool: asyncpg.Pool,
) -> AsyncGenerator[asyncpg.pool.PoolConnectionProxy]:
    conn = await db_pool.acquire()
    tx = conn.transaction()
    await tx.start()
    yield conn
    await tx.rollback()
    await db_pool.release(conn)


@pytest_asyncio.fixture(loop_scope="session")
async def app_client(
    db_pool: asyncpg.Pool,
) -> AsyncGenerator[httpx.AsyncClient]:
    os.environ["JWT_SECRET"] = TEST_JWT_SECRET

    from fastapi import FastAPI

    from connect4.api.auth import router as auth_router

    test_app = FastAPI()
    test_app.state.db_pool = db_pool
    test_app.include_router(auth_router)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client


