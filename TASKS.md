# Connect 4 — Task Plan

## Phase 1: Project Setup

- [x] Initialize uv project (pyproject.toml, Python 3.13+)
- [x] Configure ruff (linting + formatting + import sorting)
- [x] Set up pytest with `tests/` folder structure (`tests/core/`, `tests/db/`, `tests/api/`)
- [x] Create base project layout: `src/connect4/core/`, `src/connect4/db/`, `src/connect4/api/`
- [x] Add Makefile (`test`, `lint`, `format`, `check`)
- [x] Add `.gitignore`

## Phase 2: Core Game Logic (pure Python, no dependencies)

- [x] `Board` class — 7×6 grid, drop piece in column, check full column, get cell
- [x] Win detection — horizontal, vertical, diagonal (both directions)
- [x] Draw detection — board full with no winner
- [x] `Game` class — event-sourced: stores list of moves, derives board state
  - [x] `play(column)` — validate turn, drop piece, check win/draw
  - [x] `replay()` — rebuild board from move history
  - [x] Game status tracking: in_progress, won, draw (waiting handled at API layer)
- [x] Custom exceptions: `Connect4Error`, `InvalidMoveError`, `ColumnFullError`, `GameOverError`
- [x] Models: `Player` (IntEnum), `GameStatus` (StrEnum)
- [x] Tests for all core logic (`tests/core/`) — 31 tests

## Phase 3: Database & Storage

- [x] Docker Compose file for PostgreSQL 17
- [x] Alembic setup and initial migration (psycopg driver, `DATABASE_URL` env override)
- [x] Schema: `players` table (id, username, password_hash, created_at, updated_at)
- [x] Schema: `games` table (id, player1_id, player2_id, status, winner_id, created_at, updated_at)
- [x] Schema: `moves` table (id, game_id, player_id, column, move_number, created_at)
- [x] `created_at` defaults to `now()`, `updated_at` trigger on players and games (moves are immutable)
- [x] ULID primary keys stored as `char(26)` via `python-ulid`
- [x] Game status: `waiting` (player2 not joined), `in_progress`, `won`, `draw`
- [x] Database connection pool (asyncpg, min=2, max=10)
- [x] Repository layer — plain async functions with raw SQL (players, games, moves)
- [x] Tests for DB layer (`tests/db/`) — 18 tests, transaction rollback isolation
- [x] Makefile targets: `db-up`, `db-down`, `migrate`

## Phase 4: Authentication

- [ ] Password hashing (bcrypt/argon2)
- [ ] Player registration endpoint
- [ ] Player login endpoint (JWT tokens)
- [ ] Auth middleware/dependency for FastAPI

## Phase 5: API

- [ ] FastAPI app setup
- [ ] `POST /games` — create a new game
- [ ] `POST /games/{id}/join` — second player joins
- [ ] `POST /games/{id}/moves` — play a move
- [ ] `GET /games/{id}` — get game state (board derived from moves)
- [ ] `GET /games/{id}/moves` — get move history
- [ ] `GET /games` — list player's games
- [ ] Error handling (invalid moves, wrong turn, game over)
- [ ] Tests for API endpoints (`tests/api/`)

## Phase 6 (later): Frontend

- [ ] TBD — to be planned separately
