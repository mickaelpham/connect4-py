import os
import subprocess
from collections.abc import AsyncGenerator

import asyncpg
import httpx
import pytest_asyncio
from pydantic import PostgresDsn

# Override env vars before any app code calls get_settings()
os.environ["POSTGRES_DB"] = "connect4_test"
os.environ["JWT_SECRET"] = "test-secret-key-do-not-use-in-production"

from connect4.config import get_settings  # noqa: E402

TEST_DB = "connect4_test"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_pool() -> AsyncGenerator[asyncpg.Pool]:
    settings = get_settings()

    # Ensure the test database exists — connect to the default "postgres" database
    sys_dsn = PostgresDsn.build(
        scheme="postgresql",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        path="postgres",
    )
    sys_conn = await asyncpg.connect(str(sys_dsn))
    try:
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB
        )
        if not exists:
            await sys_conn.execute(f"CREATE DATABASE {TEST_DB}")
    finally:
        await sys_conn.close()

    # Run Alembic migrations on the test database
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        check=True,
    )

    pool = await asyncpg.create_pool(
        str(settings.database_url), min_size=2, max_size=5
    )
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
    from fastapi import FastAPI

    from connect4.api.auth import router as auth_router
    from connect4.api.games import router as games_router
    from connect4.api.rate_limit import limiter

    limiter.enabled = False
    test_app = FastAPI()
    test_app.state.db_pool = db_pool
    test_app.include_router(auth_router, prefix="/api")
    test_app.include_router(games_router, prefix="/api")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client

    limiter.enabled = True
