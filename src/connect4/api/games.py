import asyncio
import json

import asyncpg
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from starlette.responses import StreamingResponse

from connect4.api.dependencies import get_current_player, get_db_conn
from connect4.api.rate_limit import limiter
from connect4.api.schemas import (
    GameDetailResponse,
    GameResponse,
    MoveResponse,
    PaginatedGamesResponse,
    PlayerInfo,
    PlayMoveRequest,
)
from connect4.api.sse import GameEventBroker
from connect4.api.tokens import decode_access_token
from connect4.core.board import COLUMNS, ROWS
from connect4.core.exceptions import ColumnFullError, GameOverError, InvalidMoveError
from connect4.core.game import Game
from connect4.core.models import Player
from connect4.db.games import (
    create_game,
    get_game_by_id,
    join_game,
    list_open_games,
    list_player_games,
    update_game_status,
)
from connect4.db.moves import create_move, get_game_moves
from connect4.db.players import get_player_by_id

router = APIRouter(prefix="/games", tags=["games"])


def _player_info(record: asyncpg.Record) -> PlayerInfo:
    return PlayerInfo(id=record["id"], username=record["username"])


async def _resolve_players(
    conn: asyncpg.Connection,
    game: asyncpg.Record,
) -> tuple[PlayerInfo, PlayerInfo | None, PlayerInfo | None]:
    p1 = await get_player_by_id(conn, game["player1_id"])
    assert p1 is not None
    p2 = None
    if game["player2_id"]:
        p2 = await get_player_by_id(conn, game["player2_id"])
    winner = None
    if game["winner_id"]:
        if game["winner_id"] == game["player1_id"]:
            winner = _player_info(p1)
        elif p2 and game["winner_id"] == game["player2_id"]:
            winner = _player_info(p2)
    return (
        _player_info(p1),
        _player_info(p2) if p2 else None,
        winner,
    )


def _game_response(
    game: asyncpg.Record,
    p1: PlayerInfo,
    p2: PlayerInfo | None,
    winner: PlayerInfo | None,
    *,
    move_count: int = 0,
) -> GameResponse:
    return GameResponse(
        id=game["id"],
        player1=p1,
        player2=p2,
        status=game["status"],
        winner=winner,
        created_at=game["created_at"].isoformat(),
        updated_at=game["updated_at"].isoformat(),
        move_count=move_count,
    )


def _board_to_row_major(game_engine: Game) -> list[list[int]]:
    board = game_engine.board
    rows: list[list[int]] = []
    for r in range(ROWS - 1, -1, -1):
        row = []
        for c in range(COLUMNS):
            cell = board.get(c, r)
            row.append(int(cell) if cell is not None else 0)
        rows.append(row)
    return rows


def _replay_game(moves: list[asyncpg.Record]) -> Game:
    game = Game()
    for move in moves:
        game.play(move["column"])
    return game


def _current_player_number(
    game_record: asyncpg.Record, game_engine: Game
) -> int | None:
    if game_record["status"] != "in_progress":
        return None
    return int(game_engine.current_player)


async def _notify_game_event(
    conn: asyncpg.Connection,
    game_id: str,
    event_type: str,
) -> None:
    """Build full GameDetailResponse and pg_notify inside the current transaction."""
    detail = await _build_game_detail(conn, game_id)
    payload = json.dumps({
        "game_id": game_id,
        "event": event_type,
        "data": detail.model_dump(),
    })
    await conn.execute("SELECT pg_notify('game_events', $1)", payload)


@router.post("", response_model=GameResponse, status_code=201)
@limiter.limit("10/minute")
async def create_game_endpoint(
    request: Request,
    conn: asyncpg.Connection = Depends(get_db_conn),
    player: asyncpg.Record = Depends(get_current_player),
) -> GameResponse:
    game = await create_game(conn, player["id"])
    p1 = _player_info(player)
    return _game_response(game, p1, None, None)


@router.post("/{game_id}/join", response_model=GameResponse)
@limiter.limit("10/minute")
async def join_game_endpoint(
    game_id: str,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db_conn),
    player: asyncpg.Record = Depends(get_current_player),
) -> GameResponse:
    game = await get_game_by_id(conn, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    if game["status"] != "waiting":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Game is not waiting for a player"
        )
    if game["player1_id"] == player["id"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot join your own game")
    async with conn.transaction():
        updated = await join_game(conn, game_id, player["id"])
        await _notify_game_event(conn, game_id, "player_joined")
    p1 = await get_player_by_id(conn, game["player1_id"])
    assert p1 is not None
    return _game_response(updated, _player_info(p1), _player_info(player), None)


@router.post("/{game_id}/moves", response_model=MoveResponse, status_code=201)
@limiter.limit("30/minute")
async def play_move_endpoint(
    game_id: str,
    request: Request,
    body: PlayMoveRequest,
    conn: asyncpg.Connection = Depends(get_db_conn),
    player: asyncpg.Record = Depends(get_current_player),
) -> MoveResponse:
    async with conn.transaction():
        game = await conn.fetchrow(
            "SELECT * FROM games WHERE id = $1 FOR UPDATE",
            game_id,
        )
        if game is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
        if game["status"] != "in_progress":
            raise HTTPException(status.HTTP_409_CONFLICT, "Game is not in progress")

        moves = await get_game_moves(conn, game_id)
        game_engine = _replay_game(moves)

        expected_player_id = (
            game["player1_id"]
            if game_engine.current_player == Player.ONE
            else game["player2_id"]
        )
        if player["id"] != expected_player_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "It is not your turn")

        try:
            game_engine.play(body.column)
        except (InvalidMoveError, ColumnFullError) as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))
        except GameOverError as e:
            raise HTTPException(status.HTTP_409_CONFLICT, str(e))

        move_number = len(moves) + 1
        move = await create_move(conn, game_id, player["id"], body.column, move_number)
        assert move is not None

        if game_engine.status.value != game["status"]:
            winner_id = None
            if game_engine.winner == Player.ONE:
                winner_id = game["player1_id"]
            elif game_engine.winner == Player.TWO:
                winner_id = game["player2_id"]
            await update_game_status(conn, game_id, game_engine.status.value, winner_id)

        if game_engine.status.value != "in_progress":
            event_type = "game_over"
        else:
            event_type = "move"
        await _notify_game_event(conn, game_id, event_type)

    return MoveResponse(
        id=move["id"],
        player=_player_info(player),
        column=move["column"],
        move_number=move["move_number"],
        created_at=move["created_at"].isoformat(),
    )


@router.get("/open", response_model=list[GameResponse])
@limiter.limit("30/minute")
async def list_open_games_endpoint(
    request: Request,
    conn: asyncpg.Connection = Depends(get_db_conn),
    player: asyncpg.Record = Depends(get_current_player),
) -> list[GameResponse]:
    games = await list_open_games(conn, player["id"])
    player_cache: dict[str, PlayerInfo] = {}

    async def _get_player(pid: str) -> PlayerInfo:
        if pid not in player_cache:
            p = await get_player_by_id(conn, pid)
            assert p is not None
            player_cache[pid] = _player_info(p)
        return player_cache[pid]

    results = []
    for g in games:
        p1 = await _get_player(g["player1_id"])
        results.append(
            _game_response(g, p1, None, None, move_count=g["move_count"])
        )
    return results


@router.get("/{game_id}", response_model=GameDetailResponse)
@limiter.limit("60/minute")
async def get_game_endpoint(
    game_id: str,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db_conn),
    _player: asyncpg.Record = Depends(get_current_player),
) -> GameDetailResponse:
    game = await get_game_by_id(conn, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    p1, p2, winner = await _resolve_players(conn, game)
    moves = await get_game_moves(conn, game_id)
    game_engine = _replay_game(moves)
    return GameDetailResponse(
        id=game["id"],
        player1=p1,
        player2=p2,
        status=game["status"],
        winner=winner,
        created_at=game["created_at"].isoformat(),
        updated_at=game["updated_at"].isoformat(),
        move_count=len(moves),
        board=_board_to_row_major(game_engine),
        current_player=_current_player_number(game, game_engine),
    )


@router.get("/{game_id}/moves", response_model=list[MoveResponse])
@limiter.limit("30/minute")
async def get_moves_endpoint(
    game_id: str,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db_conn),
    _player: asyncpg.Record = Depends(get_current_player),
) -> list[MoveResponse]:
    game = await get_game_by_id(conn, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    moves = await get_game_moves(conn, game_id)
    player_cache: dict[str, PlayerInfo] = {}
    result = []
    for move in moves:
        pid = move["player_id"]
        if pid not in player_cache:
            p = await get_player_by_id(conn, pid)
            assert p is not None
            player_cache[pid] = _player_info(p)
        result.append(
            MoveResponse(
                id=move["id"],
                player=player_cache[pid],
                column=move["column"],
                move_number=move["move_number"],
                created_at=move["created_at"].isoformat(),
            )
        )
    return result


@router.get("", response_model=PaginatedGamesResponse)
@limiter.limit("30/minute")
async def list_games_endpoint(
    request: Request,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_db_conn),
    player: asyncpg.Record = Depends(get_current_player),
) -> PaginatedGamesResponse:
    games = await list_player_games(conn, player["id"], cursor=cursor, limit=limit + 1)
    has_next = len(games) > limit
    if has_next:
        games = games[:limit]
    player_cache: dict[str, PlayerInfo] = {}

    async def _get_player(pid: str) -> PlayerInfo:
        if pid not in player_cache:
            p = await get_player_by_id(conn, pid)
            assert p is not None
            player_cache[pid] = _player_info(p)
        return player_cache[pid]

    results = []
    for g in games:
        p1 = await _get_player(g["player1_id"])
        p2 = await _get_player(g["player2_id"]) if g["player2_id"] else None
        winner = None
        if g["winner_id"]:
            winner = await _get_player(g["winner_id"])
        results.append(_game_response(g, p1, p2, winner, move_count=g["move_count"]))
    return PaginatedGamesResponse(
        games=results,
        next_cursor=games[-1]["id"] if has_next else None,
    )


async def _build_game_detail(
    conn: asyncpg.Connection,
    game_id: str,
) -> GameDetailResponse:
    game = await get_game_by_id(conn, game_id)
    assert game is not None
    p1, p2, winner = await _resolve_players(conn, game)
    moves = await get_game_moves(conn, game_id)
    game_engine = _replay_game(moves)
    player_map = {p1.id: p1}
    if p2 is not None:
        player_map[p2.id] = p2
    move_responses = [
        MoveResponse(
            id=m["id"],
            player=player_map[m["player_id"]],
            column=m["column"],
            move_number=m["move_number"],
            created_at=m["created_at"].isoformat(),
        )
        for m in moves
    ]
    return GameDetailResponse(
        id=game["id"],
        player1=p1,
        player2=p2,
        status=game["status"],
        winner=winner,
        created_at=game["created_at"].isoformat(),
        updated_at=game["updated_at"].isoformat(),
        move_count=len(moves),
        board=_board_to_row_major(game_engine),
        current_player=_current_player_number(game, game_engine),
        moves=move_responses,
    )


def _format_sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


@router.get("/{game_id}/stream")
async def game_stream_endpoint(
    game_id: str,
    request: Request,
    token: str = Query(...),
    conn: asyncpg.Connection = Depends(get_db_conn),
) -> StreamingResponse:
    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired token"
        )
    player = await get_player_by_id(conn, payload["sub"])
    if player is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Player not found")

    game = await get_game_by_id(conn, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")

    initial = await _build_game_detail(conn, game_id)
    broker: GameEventBroker = request.app.state.event_broker

    async def event_generator():
        yield _format_sse("game_state", initial.model_dump_json())

        async with broker.subscribe(game_id) as queue:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    raw = await asyncio.wait_for(queue.get(), timeout=30.0)
                    msg = json.loads(raw)
                    yield _format_sse(msg["event"], json.dumps(msg["data"]))
                    if msg["event"] == "game_over":
                        break
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
