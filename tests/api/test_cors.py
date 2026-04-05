import os
from collections.abc import AsyncGenerator

import asyncpg
import httpx
import pytest_asyncio

from connect4.api.app import app


@pytest_asyncio.fixture()
async def cors_client(
    db_pool: asyncpg.Pool,
) -> AsyncGenerator[httpx.AsyncClient]:
    os.environ["JWT_SECRET"] = "test-secret-key-do-not-use-in-production"

    from connect4.api.rate_limit import limiter

    limiter.enabled = False
    app.state.db_pool = db_pool

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    limiter.enabled = True


async def test_cors_allowed_origin(cors_client: httpx.AsyncClient):
    resp = await cors_client.options(
        "/api/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in resp.headers["access-control-allow-methods"]
    assert "authorization" in resp.headers["access-control-allow-headers"].lower()


async def test_cors_disallowed_origin(cors_client: httpx.AsyncClient):
    resp = await cors_client.options(
        "/api/login",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in resp.headers


async def test_cors_disallowed_method(cors_client: httpx.AsyncClient):
    resp = await cors_client.options(
        "/api/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert "DELETE" not in resp.headers.get("access-control-allow-methods", "")
