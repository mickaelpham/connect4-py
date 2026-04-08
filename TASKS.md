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

### Backend changes
- [x] Add `username` field to `TokenResponse` (login/register/refresh responses include it)
- [x] Refresh token as `httpOnly` cookie (`Set-Cookie` on login/register/refresh; `POST /refresh` reads from cookie instead of JSON body)
  - Cookie flags: `httpOnly`, `secure`, `sameSite=strict`, `path=/api/refresh`, 7-day `max_age`
  - Removed `RefreshRequest` schema (no longer needed)
- [x] `POST /api/logout` endpoint — revokes refresh token + clears cookie (204 response)
- [x] CORS updated with `allow_credentials=True`
- [x] Backend tests updated for cookie-based flow — 108 tests pass (2 new logout tests)

### Frontend
- [x] `src/auth/validation.ts` — shared validation constants (synced with `src/connect4/api/schemas.py`): username 3–20 chars `\w+`, password 8–72 chars
- [x] `src/shared/api.ts` — typed `apiFetch` wrapper with 401 intercept + refresh retry, `ApiError` class, typed helpers: `login`, `register`, `logout`, `createGame`, `joinGame`, `getGame`, `getGames`, `getMoves`, `playMove`
- [x] Auth store (`$state`): access token in memory (never localStorage), refresh token in `httpOnly` cookie (invisible to JS), `initialized` flag for app load
- [x] `App.svelte` — calls `tryRefresh()` on mount to restore session from cookie, shows "Loading..." until initialized
- [x] `LoginPage` component — username + password form, client-side validation, calls `POST /api/login`, error display, "Don't have an account?" link
- [x] `RegisterPage` component — username + password form, client-side validation, calls `POST /api/register`, auto-login on success, "Already have an account?" link
- [x] Logout: calls `POST /api/logout` (best-effort), clears token state, redirects to `/login`
- [x] `vitest.config.ts` — added `resolve.conditions: ['browser']` for Svelte 5 component tests
- [x] `eslint.config.ts` — disabled `no-unsafe-call`/`no-unsafe-member-access` in `*.test.ts` (testing-library type resolution)
- [x] Tests: 49 frontend tests pass (33 new) — validation logic (10), LoginPage (7), RegisterPage (7), apiFetch 401 intercept + refresh retry (5), auth store + login/register API (4)

## Phase 9: Game Lobby

### Backend changes
- [x] Added `move_count: int = 0` to `GameResponse` schema (derived from `LEFT JOIN moves` + `COUNT`)
- [x] Modified `list_player_games()` to join moves table and return `move_count`
- [x] New `list_open_games()` repo function — returns waiting games excluding own (`WHERE status = 'waiting' AND player1_id != $1`)
- [x] New `GET /api/games/open` endpoint — returns `list[GameResponse]`, no pagination, 20 most recent
- [x] Updated `_game_response()` helper and `get_game_endpoint` to pass `move_count`
- [x] Backend tests: 6 new (move_count in list, open games visibility/exclusion/auth, DB-level open games) — 114 total

### Frontend
- [x] Added `move_count: number` to `GameResponse` type, added `getOpenGames()` API helper
- [x] `gameStatus.ts` — `getDisplayStatus(game, username)` derives your-turn/their-turn/you-won/you-lost/draw/waiting from `move_count` + player position; `statusLabel()` for display strings
- [x] `LobbyPage` component with two sections:
  - [x] "Your Games" — `GET /games` with cursor pagination, shows opponent, status badge (color-coded), relative time
  - [x] "Open Games" — `GET /api/games/open`, shows creator + join button
- [x] "New Game" button — `POST /games`, navigates to `/games/:id`
- [x] Join game — `POST /games/:id/join`, navigates to `/games/:id`
- [x] No auto-refresh (deferred to SSE in Phase 11)
- [x] Tests: 22 new (10 gameStatus unit, 11 LobbyPage component with MSW, 1 waitingGame status) — 71 frontend total

## Phase 10: Game Board & Play

- [x] `GamePage` component — fetches `GET /games/:id`, orchestrates state/polling/optimistic updates
- [x] `Board` component — 7×6 CSS grid, renders red/yellow pieces on `#213547` dark board
- [x] Column hover indicator (ghost piece on mouseover when it's your turn)
- [x] Click to play — `POST /games/:id/moves`, optimistic update with rollback on error
- [x] CSS transition for piece drop animation (simple `translateY`)
- [x] Win highlight — outline 4 winning cells (white box-shadow) + dim other pieces (opacity 0.3)
- [x] Game status display: waiting for opponent, your turn, opponent's turn, you won, you lost, draw
- [x] `WaitingView` — separate view with share link + copy button for game creator
- [x] `InfoPanel` — right panel with status badge, player list, error display, move history placeholder
- [x] Two-column layout: board left, info panel right
- [x] `winCells.ts` — pure function to find 4 winning cell coordinates from board array
- [x] Polling (2s) while game is active, stops when game ends
- [x] Tests: 22 new (8 winCells unit + 14 GamePage component with MSW) — 93 frontend total

## Phase 11: SSE Real-Time Updates

- [x] Backend: `GameEventBroker` — shared asyncpg LISTEN/NOTIFY fan-out via per-client `asyncio.Queue` (`src/connect4/api/sse.py`)
- [x] Backend: `pg_notify('game_events', ...)` inside transactions for `play_move_endpoint` (move/game_over) and `join_game_endpoint` (player_joined)
- [x] Backend: SSE endpoint `GET /games/:id/stream?token=...` — token auth via query param, full state on connect, streams events, 30s keepalive
- [x] Backend: tests for SSE — 10 tests (auth errors, broker unit tests, notification integration)
- [x] Frontend: `createGameStream()` utility — `EventSource` with auto-reconnect (exponential backoff) + token refresh (`src/shared/gameStream.ts`)
- [x] Frontend: replaced polling with SSE `$effect` in `GamePage.svelte`, optimistic moves confirmed by SSE (no re-fetch)
- [x] Frontend: close SSE connection when navigating away from game page (effect cleanup)
- [x] Frontend tests: 11 SSE tests (connect, events, reconnect, cleanup, error) + `MockEventSource` test utility
- [x] Fix: SSE reconnect loop — `$effect` was tracking `game` state directly, causing teardown/reconnect on every SSE event. Extracted `shouldStream` as `$derived` boolean so the effect only re-runs on status transitions.

## Phase 11.5: Game Page Enhancements

- [x] Move history panel — display move-by-move list in InfoPanel (replace placeholder)
- [~] ~~Bounce/spring drop animation (upgrade from simple `translateY` to bounce easing)~~ — won't do, current animation is good enough

## Phase 12: Error Handling & Polish

- [x] Toast/notification system for API errors — `toast.svelte.ts` store + `Toast.svelte` component, mounted in `App.svelte`, integrated into `apiFetch`; errors persist until dismissed, warnings auto-dismiss after 5s, deduplicates identical messages
- [x] Skeleton loading states — `Skeleton.svelte` component with shimmer animation; lobby shows skeleton game rows, game page shows skeleton board + info panel
- [x] 404 page — `NotFoundPage.svelte`; router returns `not-found` for unrecognized paths instead of falling through to lobby
- [x] Disable inputs while requests are in flight — lobby list links greyed out during create/join (other inputs already handled)
- [x] Fix pre-existing lint issues in Board, InfoPanel, WaitingView, winCells.test
- [x] Tests: 106 frontend tests pass (3 updated for skeleton/404 changes)

## Phase 13: E2E Tests

- [x] Set up Playwright in top-level `e2e/` directory (`playwright.config.ts`, `package.json`, npm scripts + Makefile targets `e2e`, `e2e-ui`)
- [x] Playwright `webServer` config starts both backend (uvicorn :8000) and frontend (vite :5173) automatically
- [x] Global setup: creates `connect4_test` database, runs alembic migrations, truncates tables
- [x] Custom fixtures: `player1`/`player2` with separate browser contexts, `dbCleanup` auto-truncation between tests
- [x] Backend: `DISABLE_RATE_LIMIT` env var to disable slowapi for E2E, `COOKIE_SECURE` env var for HTTP localhost
- [x] E2E: auth tests (7) — register, login, logout, auth guard redirect, validation errors, duplicate username, wrong password
- [x] E2E: lobby tests (4) — empty lobby, create game, open games visible, join game
- [x] E2E: two-player game tests (5) — SSE player joined, SSE move propagation, vertical win, turn enforcement, horizontal win with highlights
- [x] E2E: error state tests (3) — full column disabled, board disabled after game over, game not found
- [x] 19 E2E tests total, all passing (~10s)
