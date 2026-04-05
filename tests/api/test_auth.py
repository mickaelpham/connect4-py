import asyncio

import httpx
import pytest

pytestmark = pytest.mark.usefixtures("_clean_tables")


async def test_register_success(app_client: httpx.AsyncClient):
    resp = await app_client.post(
        "/register",
        json={"username": "alice", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_username(app_client: httpx.AsyncClient):
    await app_client.post(
        "/register",
        json={"username": "dupuser", "password": "password123"},
    )
    resp = await app_client.post(
        "/register",
        json={"username": "dupuser", "password": "password456"},
    )
    assert resp.status_code == 409


async def test_register_username_case_insensitive(app_client: httpx.AsyncClient):
    await app_client.post(
        "/register",
        json={"username": "CaseUser", "password": "password123"},
    )
    resp = await app_client.post(
        "/register",
        json={"username": "caseuser", "password": "password456"},
    )
    assert resp.status_code == 409


async def test_register_username_too_short(app_client: httpx.AsyncClient):
    resp = await app_client.post(
        "/register",
        json={"username": "ab", "password": "password123"},
    )
    assert resp.status_code == 422


async def test_register_username_bad_chars(app_client: httpx.AsyncClient):
    resp = await app_client.post(
        "/register",
        json={"username": "bad user!", "password": "password123"},
    )
    assert resp.status_code == 422


async def test_register_password_too_short(app_client: httpx.AsyncClient):
    resp = await app_client.post(
        "/register",
        json={"username": "validuser", "password": "short"},
    )
    assert resp.status_code == 422


async def test_register_500_when_create_player_returns_none(
    app_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    async def _returning_none(*args, **kwargs):
        return None

    monkeypatch.setattr("connect4.api.auth.create_player", _returning_none)
    resp = await app_client.post(
        "/register",
        json={"username": "newuser", "password": "password123"},
    )
    assert resp.status_code == 500
    assert resp.json()["detail"] == "Failed to create player"


async def test_login_password_too_long(app_client: httpx.AsyncClient):
    resp = await app_client.post(
        "/login",
        json={"username": "anyuser", "password": "a" * 73},
    )
    assert resp.status_code == 422


async def test_login_success(app_client: httpx.AsyncClient):
    await app_client.post(
        "/register",
        json={"username": "loginuser", "password": "password123"},
    )
    resp = await app_client.post(
        "/login",
        json={"username": "loginuser", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(app_client: httpx.AsyncClient):
    await app_client.post(
        "/register",
        json={"username": "loginuser2", "password": "password123"},
    )
    resp = await app_client.post(
        "/login",
        json={"username": "loginuser2", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_login_nonexistent_user(app_client: httpx.AsyncClient):
    resp = await app_client.post(
        "/login",
        json={"username": "nouser", "password": "password123"},
    )
    assert resp.status_code == 401


async def test_refresh_success(app_client: httpx.AsyncClient):
    reg = await app_client.post(
        "/register",
        json={"username": "refreshuser", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]

    resp = await app_client.post(
        "/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New refresh token should differ from old one
    assert data["refresh_token"] != refresh_token


async def test_refresh_reuse_revoked_token(app_client: httpx.AsyncClient):
    reg = await app_client.post(
        "/register",
        json={"username": "reuseuser", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]

    # First use succeeds
    resp1 = await app_client.post(
        "/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp1.status_code == 200

    # Second use of same token fails
    resp2 = await app_client.post(
        "/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp2.status_code == 401


async def test_refresh_concurrent_reuse(app_client: httpx.AsyncClient):
    """Two concurrent refreshes with the same token: only one should succeed."""
    reg = await app_client.post(
        "/register",
        json={"username": "raceuser", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]

    results = await asyncio.gather(
        app_client.post("/refresh", json={"refresh_token": refresh_token}),
        app_client.post("/refresh", json={"refresh_token": refresh_token}),
    )
    status_codes = sorted(r.status_code for r in results)
    assert status_codes == [200, 401]


async def test_refresh_invalid_token(app_client: httpx.AsyncClient):
    resp = await app_client.post(
        "/refresh",
        json={"refresh_token": "completely-invalid-token"},
    )
    assert resp.status_code == 401
