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

- [x] Password hashing (argon2id via `argon2-cffi`)
- [x] Player registration endpoint (`POST /register`)
- [x] Player login endpoint (`POST /login`, JWT access tokens via PyJWT)
- [x] Refresh token flow (`POST /refresh`, token rotation, DB-backed revocation)
- [x] Auth middleware/dependency for FastAPI (`get_current_player`)
- [x] Minimal FastAPI app setup with lifespan (pool management)
- [x] Tests for auth layer — 21 tests (unit + DB + integration)

## Phase 5: API

- [x] FastAPI app setup (done in Phase 4)
- [x] `POST /games` — create a new game
- [x] `POST /games/{id}/join` — second player joins
- [x] `POST /games/{id}/moves` — play a move (SELECT FOR UPDATE + unique constraint on move_number)
- [x] `GET /games/{id}` — get game state (row-major 6×7 board derived from moves)
- [x] `GET /games/{id}/moves` — get move history
- [x] `GET /games` — list player's games (cursor pagination, ULID-based)
- [x] Error handling (invalid moves, wrong turn, game over, self-join, not found)
- [x] Tests for API endpoints (`tests/api/`) — 22 tests

## Pre-deployment

- [ ] Make CORS `allow_origins` configurable via environment variable (currently hardcoded to `http://localhost:5173` in `src/connect4/api/app.py:23`)
- [ ] If switching to multi-worker deployment, replace slowapi in-memory storage with Redis-backed storage (`src/connect4/api/rate_limit.py`)

## Phase 6: Frontend Scaffolding

- [x] Scaffold Svelte 5 app with Vite in `frontend/` (svelte-ts template)
- [x] Clean up boilerplate (remove default assets, counter component, etc.)
- [x] Configure Vite dev server proxy (`/api` → `http://localhost:8000`) to avoid CORS in dev
- [x] Add npm scripts: `dev`, `build`, `preview`, `lint`, `lint:fix`
- [x] Add Makefile targets: `fe-dev`, `fe-build`, `fe-lint`, `fe-lint-fix`
- [x] Set up fnm + Node 22 LTS (`.node-version` file)
- [x] Set up @antfu/eslint-config with Svelte + type-checked TS
- [x] Create feature directory structure (`auth/`, `lobby/`, `game/`, `shared/`)
- [x] Add `/api` prefix to FastAPI routers + update backend tests

## Phase 7: Router & Layout Shell

- [x] Set up Vitest + @testing-library/svelte + happy-dom (`vitest.config.ts`, `npm test`/`test:watch`, Makefile `fe-test`)
  - happy-dom over jsdom (jsdom v29 has ESM compat issues with Node)
  - `vitest/globals` added to `tsconfig.app.json` types
  - Test infra in `frontend/test/` (setup, server, handlers), component tests co-located in `src/`
- [x] Set up MSW (Mock Service Worker) for API mocking in tests
  - `test/handlers.ts` — shared default handlers, `test/server.ts` — MSW server
  - Wired into `test/setup.ts`: start/reset/close lifecycle, `onUnhandledRequest: 'error'`
  - Per-test overrides via `server.use(...)`
- [x] Hand-rolled history router (~30 lines): push/replace/listen on `popstate`
- [x] Route table: `/login`, `/register`, `/` (lobby), `/games/:id`
- [x] App layout shell: nav bar (logo, logged-in player name, logout button), `<main>` slot
- [x] Redirect unauthenticated users to `/login`
- [x] Tests: route matching, `navigate()`/`back()`, auth redirect logic (`src/router.test.ts` — 13 tests)

## Phase 8: Auth Pages & Token Management

- [ ] `LoginPage` component — username + password form, calls `POST /login`
- [ ] `RegisterPage` component — username + password form, calls `POST /register`, auto-login on success
- [ ] Auth store (`$state`): holds access token in memory (never localStorage)
- [ ] `apiFetch` wrapper — injects `Authorization` header, intercepts 401, calls `POST /refresh` transparently, retries original request
- [ ] Logout: clears token state, redirects to `/login`
- [ ] Tests: `apiFetch` 401 intercept + token refresh retry (MSW), auth store state transitions, login/register form submission + error display

## Phase 9: Game Lobby

- [ ] `LobbyPage` component with two sections:
  - [ ] "Your games" — `GET /games` with cursor pagination, shows status/opponent/last move
  - [ ] "Open games" — `GET /games?status=waiting` (needs new backend filter), shows creator + join button
- [ ] "New game" button — `POST /games`, navigates to `/games/:id`
- [ ] Join game — `POST /games/:id/join`, navigates to `/games/:id`
- [ ] Tests: game list rendering, pagination, create/join actions (MSW)

## Phase 10: Game Board & Play

- [ ] `GamePage` component — fetches `GET /games/:id` and `GET /games/:id/moves`
- [ ] `Board` component — 7×6 HTML/CSS grid, renders pieces as colored circles
- [ ] Column hover indicator (highlights column on mouseover when it's your turn)
- [ ] Click to play — `POST /games/:id/moves`, optimistic update
- [ ] CSS transition for piece drop animation
- [ ] Win highlight — highlight the four winning cells
- [ ] Game status display: waiting for opponent, your turn, opponent's turn, you won, you lost, draw
- [ ] Polling fallback (2s) if SSE connection drops, stops when game is over
- [ ] Tests: board rendering from game state, click-to-play dispatches move, optimistic update + rollback on error, win cell highlighting, status display per game state

## Phase 11: SSE Real-Time Updates

- [ ] Backend: add `pg_notify()` calls in `create_move()`, `join_game()`, and game-over logic
- [ ] Backend: SSE endpoint `GET /games/:id/stream` — listens on `game_{id}` channel via asyncpg, yields events (`player_joined`, `move`, `game_over`)
- [ ] Backend: full state fetch on SSE connect (so client never misses prior events)
- [ ] Backend: tests for SSE endpoint
- [ ] Frontend: `EventSource` connection to `/games/:id/stream` when on game page
- [ ] Frontend: auto-reconnect with full state refetch on reconnection
- [ ] Frontend: close SSE connection when navigating away from game page
- [ ] Frontend tests: SSE reconnect logic, state sync on reconnection, connection cleanup on navigate-away

## Phase 12: Error Handling & Polish

- [ ] Toast/notification system for API errors (invalid move, game full, etc.)
- [ ] Loading states (skeleton/spinner) for async fetches
- [ ] 404 page for unknown routes
- [ ] Disable inputs while requests are in flight

## Phase 13: E2E Tests

- [ ] Set up Playwright (install, `playwright.config.ts`, npm scripts + Makefile targets)
- [ ] Helper: start backend + frontend dev servers for test runs
- [ ] E2E: register → login → create game flow
- [ ] E2E: two-player game to completion (win + draw)
- [ ] E2E: lobby list updates after game creation / join
- [ ] E2E: error states (wrong turn, full column, game over)
