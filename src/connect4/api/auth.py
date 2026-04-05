import asyncpg as _asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from connect4.api.dependencies import get_db_conn
from connect4.api.passwords import hash_password, verify_password
from connect4.api.rate_limit import limiter
from connect4.api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from connect4.api.tokens import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from connect4.db.players import create_player, get_player_by_id, get_player_by_username
from connect4.db.refresh_tokens import (
    create_refresh_token as store_refresh_token,
)
from connect4.db.refresh_tokens import (
    get_refresh_token_by_hash,
    revoke_refresh_token,
)

router = APIRouter(tags=["auth"])


async def _issue_tokens(
    conn: _asyncpg.Connection,
    player_id: str,
    username: str,
) -> TokenResponse:
    raw_refresh = create_refresh_token()
    await store_refresh_token(conn, player_id, hash_refresh_token(raw_refresh))
    access = create_access_token(player_id, username)
    return TokenResponse(access_token=access, refresh_token=raw_refresh)


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    conn: _asyncpg.Connection = Depends(get_db_conn),
) -> TokenResponse:
    username = body.username.lower()
    password_hashed = hash_password(body.password)
    try:
        player = await create_player(conn, username, password_hashed)
    except _asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create player",
        )
    return await _issue_tokens(conn, player["id"], username)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    conn: _asyncpg.Connection = Depends(get_db_conn),
) -> TokenResponse:
    username = body.username.lower()
    player = await get_player_by_username(conn, username)
    if player is None or not verify_password(body.password, player["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return await _issue_tokens(conn, player["id"], username)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    conn: _asyncpg.Connection = Depends(get_db_conn),
) -> TokenResponse:
    token_hash = hash_refresh_token(body.refresh_token)
    async with conn.transaction():
        stored = await get_refresh_token_by_hash(conn, token_hash)
        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        await revoke_refresh_token(conn, stored["id"])
        player = await get_player_by_id(conn, stored["player_id"])
        if player is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Player not found",
            )
        return await _issue_tokens(conn, stored["player_id"], player["username"])
