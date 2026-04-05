import os
from collections.abc import AsyncGenerator

import asyncpg
import httpx
import pytest
import pytest_asyncio
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

pytestmark = pytest.mark.usefixtures("_clean_tables")


@pytest_asyncio.fixture()
async def rate_limited_client(
    db_pool: asyncpg.Pool,
) -> AsyncGenerator[httpx.AsyncClient]:
    os.environ["JWT_SECRET"] = "test-secret-key-do-not-use-in-production"

    from fastapi import FastAPI

    from connect4.api.auth import router as auth_router
    from connect4.api.rate_limit import limiter

    limiter.enabled = True
    limiter.reset()

    test_app = FastAPI()
    test_app.state.limiter = limiter
    test_app.state.db_pool = db_pool
    test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    test_app.include_router(auth_router)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client

    limiter.enabled = False


async def test_register_rate_limit(rate_limited_client: httpx.AsyncClient):
    for i in range(3):
        resp = await rate_limited_client.post(
            "/register",
            json={"username": f"ratelimit{i}", "password": "password123"},
        )
        assert resp.status_code == 201, f"Request {i + 1} should succeed"

    resp = await rate_limited_client.post(
        "/register",
        json={"username": "ratelimit_blocked", "password": "password123"},
    )
    assert resp.status_code == 429


async def test_login_rate_limit(rate_limited_client: httpx.AsyncClient):
    # Create a user to log in with
    await rate_limited_client.post(
        "/register",
        json={"username": "loginrl", "password": "password123"},
    )

    for i in range(5):
        resp = await rate_limited_client.post(
            "/login",
            json={"username": "loginrl", "password": "password123"},
        )
        assert resp.status_code == 200, f"Request {i + 1} should succeed"

    resp = await rate_limited_client.post(
        "/login",
        json={"username": "loginrl", "password": "password123"},
    )
    assert resp.status_code == 429


async def test_refresh_rate_limit(rate_limited_client: httpx.AsyncClient):
    from connect4.api.rate_limit import limiter

    # Temporarily disable rate limiting to register 11 users for setup
    limiter.enabled = False
    tokens = []
    for i in range(11):
        reg = await rate_limited_client.post(
            "/register",
            json={"username": f"refreshrl{i}", "password": "password123"},
        )
        tokens.append(reg.json()["refresh_token"])
    limiter.enabled = True
    limiter.reset()

    for i in range(10):
        resp = await rate_limited_client.post(
            "/refresh",
            json={"refresh_token": tokens[i]},
        )
        assert resp.status_code == 200, f"Request {i + 1} should succeed"

    resp = await rate_limited_client.post(
        "/refresh",
        json={"refresh_token": tokens[10]},
    )
    assert resp.status_code == 429
