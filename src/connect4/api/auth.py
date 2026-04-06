import asyncpg as _asyncpg
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from connect4.api.dependencies import get_db_conn
from connect4.api.passwords import hash_password, verify_password
from connect4.api.rate_limit import limiter
from connect4.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from connect4.api.tokens import (
    REFRESH_TOKEN_EXPIRE_DAYS,
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

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, raw_refresh: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/refresh",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/refresh",
    )


async def _issue_tokens(
    conn: _asyncpg.Connection,
    response: Response,
    player_id: str,
    username: str,
) -> TokenResponse:
    raw_refresh = create_refresh_token()
    await store_refresh_token(conn, player_id, hash_refresh_token(raw_refresh))
    access = create_access_token(player_id, username)
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access, username=username)


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("3/minute")
async def register(
    request: Request,
    response: Response,
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
    return await _issue_tokens(conn, response, player["id"], username)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
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
    return await _issue_tokens(conn, response, player["id"], username)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    response: Response,
    conn: _asyncpg.Connection = Depends(get_db_conn),
    refresh_token: str | None = Cookie(default=None),
) -> TokenResponse:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    token_hash = hash_refresh_token(refresh_token)
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
        return await _issue_tokens(
            conn, response, stored["player_id"], player["username"]
        )


@router.post("/logout", status_code=204)
@limiter.limit("10/minute")
async def logout(
    request: Request,
    response: Response,
    conn: _asyncpg.Connection = Depends(get_db_conn),
    refresh_token: str | None = Cookie(default=None),
) -> None:
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)
        stored = await get_refresh_token_by_hash(conn, token_hash)
        if stored:
            await revoke_refresh_token(conn, stored["id"])
    _clear_refresh_cookie(response)
