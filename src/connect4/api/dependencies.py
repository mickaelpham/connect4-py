from collections.abc import AsyncIterator

import asyncpg
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import jwt

from connect4.api.tokens import decode_access_token
from connect4.db.players import get_player_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_conn(request: Request) -> AsyncIterator[asyncpg.Connection]:
    async with request.app.state.db_pool.acquire() as conn:
        yield conn


async def get_current_player(
    conn: asyncpg.Connection = Depends(get_db_conn),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> asyncpg.Record:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    player = await get_player_by_id(conn, payload["sub"])
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player not found",
        )
    return player
