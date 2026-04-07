from pydantic import BaseModel, Field

# --- Auth ---


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    username: str
    password: str = Field(max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# --- Games ---


class PlayerInfo(BaseModel):
    id: str
    username: str


class PlayMoveRequest(BaseModel):
    column: int = Field(ge=0, le=6)


class MoveResponse(BaseModel):
    id: str
    player: PlayerInfo
    column: int
    move_number: int
    created_at: str


class GameResponse(BaseModel):
    id: str
    player1: PlayerInfo
    player2: PlayerInfo | None
    status: str
    winner: PlayerInfo | None
    created_at: str
    updated_at: str
    move_count: int = 0


class GameDetailResponse(GameResponse):
    board: list[list[int]]
    current_player: int | None
    moves: list[MoveResponse] = []


class PaginatedGamesResponse(BaseModel):
    games: list[GameResponse]
    next_cursor: str | None
