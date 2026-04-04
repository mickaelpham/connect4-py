from datetime import UTC, datetime, timedelta

import jwt
import pytest

from connect4.api.tokens import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_refresh_token,
)

SECRET = "test-secret-that-is-at-least-32-bytes!"


@pytest.fixture(autouse=True)
def _set_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)


def test_create_and_decode_access_token():
    token = create_access_token("player123", "alice")
    payload = decode_access_token(token)
    assert payload["sub"] == "player123"
    assert payload["username"] == "alice"
    assert payload["type"] == "access"


def test_access_token_expired():
    now = datetime.now(UTC)
    payload = {
        "sub": "player123",
        "username": "alice",
        "type": "access",
        "iat": now - timedelta(hours=1),
        "exp": now - timedelta(minutes=1),
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_invalid_token():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not.a.valid.token")


def test_decode_rejects_non_access_token():
    payload = {
        "sub": "player123",
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError, match="Not an access token"):
        decode_access_token(token)


def test_create_refresh_token_is_random():
    t1 = create_refresh_token()
    t2 = create_refresh_token()
    assert t1 != t2


def test_hash_refresh_token_deterministic():
    token = "some-token-value"
    assert hash_refresh_token(token) == hash_refresh_token(token)
