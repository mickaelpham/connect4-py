# Security Audit Report — Connect 4

**Date:** 2026-04-08 (revision 3)
**Previous audit:** 2026-04-05 (revision 2)
**Scope:** Full stack — backend API, database, Svelte frontend, E2E test infrastructure
**Threat model:** Public-facing side project, internet-exposed

---

## Summary

| Severity | Total | Fixed | Accepted | Acknowledged | Open |
|----------|-------|-------|----------|--------------|------|
| High     | 2     | 2     | —        | —            | 0    |
| Medium   | 5     | 3     | 2        | —            | 0    |
| Low      | 6     | 5     | 1        | —            | 0    |
| Info     | 12    | 2     | —        | 8            | 2    |

---

## Fixed findings

### HIGH-1: No rate limiting on authentication endpoints — FIXED

**Location:** `src/connect4/api/auth.py:42,66,83`

Rate limiting added via `slowapi` with per-IP limits: `/register` 3/min, `/login` 5/min, `/refresh` 10/min.

**Note:** slowapi uses in-memory storage, which resets on restart and does not share state across workers. This is acceptable for single-worker deployment. If the deployment target changes to multi-worker, switch to Redis-backed storage (tracked in `TASKS.md`).

---

### HIGH-2: LoginRequest accepts unbounded password length (hash DoS) — FIXED

**Location:** `src/connect4/api/schemas.py:11`

`LoginRequest.password` now has `Field(max_length=72)`, matching `RegisterRequest`.

---

### MED-1: Refresh token rotation race condition — FIXED

**Location:** `src/connect4/api/auth.py:90`, `src/connect4/db/refresh_tokens.py:39`

The `/refresh` endpoint now wraps the read-revoke-issue sequence in `async with conn.transaction()`, and `get_refresh_token_by_hash` uses `SELECT ... FOR UPDATE` to serialize concurrent access.

---

### MED-3: No CORS middleware configured — FIXED

**Location:** `src/connect4/api/app.py:27-33`

`CORSMiddleware` added with `allow_origins=["http://localhost:5173"]`, scoped `allow_methods=["GET", "POST"]` and `allow_headers=["Authorization", "Content-Type"]`.

**Note:** The origin is currently hardcoded. Making it configurable via environment variable before deployment is tracked in `TASKS.md`.

---

### MED-4: No database CHECK constraints on critical columns — FIXED

**Location:** migration `44709785e863`

CHECK constraints added: `games.status IN ('waiting', 'in_progress', 'won', 'draw')` and `moves.column BETWEEN 0 AND 6`.

---

### LOW-1: assert used for control flow in register endpoint — FIXED

**Location:** `src/connect4/api/auth.py:57-61`

Replaced with explicit `if player is None: raise HTTPException(500, ...)`.

---

### LOW-3: Inconsistent ON DELETE policy across foreign keys — FIXED

**Location:** migration `72161dac332b`

`refresh_tokens.player_id` FK changed from `ON DELETE CASCADE` to `ON DELETE RESTRICT`, consistent with the game tables. All FKs now use RESTRICT (the default).

---

### LOW-4: slowapi asyncio monkeypatch — FIXED

**Severity:** Low
**Location:** `src/connect4/api/rate_limit.py`

slowapi 0.1.9 uses the deprecated `asyncio.iscoroutinefunction` (removed in Python 3.16). The initial workaround monkeypatched `asyncio.iscoroutinefunction = inspect.iscoroutinefunction`, which mutates stdlib global state and could break other libraries.

**Fix applied:** Replaced with a targeted `warnings.filterwarnings("ignore", ...)` to suppress the deprecation warning until slowapi releases a fix.

---

### LOW-5: Bare `except Exception` swallows JWT configuration errors — FIXED (rev 3)

**Severity:** Low
**Location:** `src/connect4/api/dependencies.py:29`, `src/connect4/api/games.py:399`

Both `get_current_player` and `game_stream_endpoint` caught all exceptions from `decode_access_token`, masking `RuntimeError` from missing `JWT_SECRET` as a generic 401.

**Fix applied:** Changed to `except jwt.InvalidTokenError`, allowing non-JWT errors (configuration issues, coding bugs) to propagate as 500s.

---

### LOW-6: Cursor not URL-encoded in query string — FIXED (rev 3)

**Severity:** Low
**Location:** `frontend/src/shared/api.ts:163`

The pagination cursor was interpolated into the URL without `encodeURIComponent`. While the cursor is a ULID (alphanumeric, no special characters in practice), this is a robustness issue — a malformed cursor from a tampered `next_cursor` response could break the URL.

**Fix applied:** Wrapped in `encodeURIComponent(cursor)`.

---

### INFO-2: No iss/aud claims in JWT — FIXED

**Location:** `src/connect4/api/tokens.py:25-26,35`

`iss` and `aud` claims (`"connect4"`) added to token creation and validated in `decode_access_token`.

---

### INFO-8: No pagination on `list_player_games` — FIXED (rev 3)

**Severity:** Info
**Location:** `src/connect4/db/games.py:88-110`

Cursor-based pagination with configurable `limit` (default 20) is now implemented. The `GET /api/games` endpoint returns a `next_cursor` for client-side pagination.

---

## Accepted findings

### MED-2: User enumeration via registration endpoint — ACCEPTED

**Location:** `src/connect4/api/auth.py:53-56`

Still returns HTTP 409 with `"Username already taken"`. Usernames are public in game context, and there is no email-based account recovery. Risk is acceptable for this project's threat model.

---

### MED-5: SSE token passed as URL query parameter — ACCEPTED (rev 3)

**Severity:** Medium
**Location:** `frontend/src/shared/gameStream.ts:38`, `src/connect4/api/games.py:394`

The SSE streaming endpoint receives the access token via `?token=` query parameter. This exposes the token in:
- Browser history and developer tools
- Server access logs
- Proxy/CDN logs (if any)

This is an inherent limitation of the `EventSource` API, which does not support custom headers. The `fetch()` API with `ReadableStream` could replace `EventSource` but would require reimplementing reconnection logic.

**Mitigations in place:**
- Access tokens are short-lived (15 minutes)
- HTTPS encrypts the URL in transit (when deployed behind a reverse proxy)
- The token is properly `encodeURIComponent`-encoded

**Accepted** — the risk is proportionate to the project's threat model. If the project moves to a higher-security context, replace `EventSource` with a `fetch`-based SSE client that sends the token in the `Authorization` header.

---

### LOW-2: Stale refresh tokens accumulate indefinitely — ACCEPTED

**Location:** `src/connect4/db/refresh_tokens.py`

Revoked and expired tokens are never deleted. Token table growth is negligible for a side project with low traffic. A cleanup job can be added later if needed.

---

## Acknowledged findings (no action needed)

### INFO-1: JWT uses HS256 — acceptable for single service

**Location:** `src/connect4/api/tokens.py:30,35`

HS256 is appropriate for the current single-service architecture. Switch to RS256/ES256 if services are split.

---

### INFO-3: Argon2id defaults are OWASP-compliant

**Location:** `src/connect4/api/passwords.py:4`

argon2-cffi defaults (`time_cost=3`, `memory_cost=65536`, `parallelism=4`, `type=argon2id`) meet OWASP minimums. Password max length of 72 prevents hash-DoS.

---

### INFO-4: No security headers or HTTPS enforcement

**Location:** `src/connect4/api/app.py`, `frontend/index.html`

Expected for local development. Security headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS) will be handled at the reverse proxy layer when deploying. The frontend has no CSP meta tag — this is part of the same deployment concern.

---

### INFO-5: Hardcoded DSN with credentials in source

**Location:** `src/connect4/db/connection.py:5`

`DEFAULT_DSN = "postgresql://connect4:connect4@localhost:5432/connect4"` contains a username/password. This is only used as a local dev fallback (overridden by `DATABASE_URL` in production). The credentials are for a local Docker Compose database and are not sensitive.

---

### INFO-6: No `move_number` upper bound constraint

**Severity:** Info
**Location:** migration `3b9771039e7f`, `moves` table

`move_number` has no CHECK constraint. A Connect 4 game has at most 42 moves (7 columns x 6 rows). Adding `CHECK (move_number BETWEEN 1 AND 42)` would prevent invalid data at the DB level. Application logic enforces this via `len(moves) + 1` and the core `Game` class.

---

### INFO-7: `winner_id` can be inconsistent with game status

**Severity:** Info
**Location:** migration `3b9771039e7f`, `games` table

No constraint ensures `winner_id` is null when `status != 'won'` or non-null when `status = 'won'`. Application logic derives `winner_id` from the core `Game` class, making inconsistency unlikely but not impossible at the DB level.

---

### INFO-9: E2E test secrets in `.env.test` (rev 3)

**Severity:** Info
**Location:** `e2e/.env.test`

Contains `POSTGRES_PASSWORD` and `JWT_SECRET` for the test environment. The file is in `.gitignore` and has **never been committed** to git history. These credentials are for a local Docker Compose test database and are not sensitive.

---

### INFO-10: Rate limiting disabled in E2E test config (rev 3)

**Severity:** Info
**Location:** `e2e/playwright.config.ts`

`DISABLE_RATE_LIMIT=1` is set in the Playwright test server environment. This is intentional — rate limiting would cause flaky tests. Rate limiting is independently tested via `test_rate_limit.py`.

---

### INFO-11: Zero production dependencies in frontend (rev 3)

**Severity:** Info (positive finding)
**Location:** `frontend/package.json`

The frontend has no runtime `dependencies` — only `devDependencies` for build tooling and testing. This eliminates supply-chain risk from transitive production dependencies.

---

## Items confirmed secure

### Backend (unchanged from rev 2)

- **SQL injection:** All queries use asyncpg parameterized queries (`$1`, `$2`...). No string interpolation in `src/connect4/db/`.
- **Password hashing:** argon2id with OWASP-compliant defaults, proper verify/hash separation.
- **Refresh token storage:** Only SHA-256 hashes stored; raw tokens never hit the database.
- **Login error messages:** Generic `"Invalid username or password"` — no user enumeration via login.
- **Username normalization:** `.lower()` applied on both register and login.
- **Secrets in git:** `.env` is in `.gitignore`.
- **Token expiry:** 15-minute access tokens, 7-day refresh tokens.
- **Refresh token rotation:** Atomic read-revoke-issue with row-level locking.
- **Rate limiting:** All auth and game endpoints rate-limited per IP.
- **CORS:** Restrictive origin whitelist with scoped methods/headers.

### Game layer (new in rev 3)

- **Self-play prevention:** `POST /games/{id}/join` rejects `player2_id == player1_id`.
- **Move authorization:** Core `Game` class enforces turn order, column bounds, and game-over state before accepting moves.
- **Move + status atomicity:** Move insertion and game status update wrapped in `async with conn.transaction()`.
- **Game status transitions:** Derived from core game logic, not from client input.

### Frontend (new in rev 3)

- **XSS:** No `{@html}`, `innerHTML`, or `dangerouslySetInnerHTML`. All user content auto-escaped by Svelte's default interpolation (`{variable}`).
- **Token storage:** Access token in memory only (Svelte `$state`), not `localStorage` or `sessionStorage`. Refresh token in `httpOnly`/`Secure`/`SameSite=strict` cookie.
- **Token refresh:** Automatic 401 retry with deduplication of concurrent refresh requests.
- **Client-side validation:** `validation.ts` mirrors backend constraints in `schemas.py` (username length/pattern, password length).
- **SSE reconnection:** Exponential backoff (1s–30s), max 5 attempts, token refresh before reconnect.
- **SSE event filtering:** Only known event types (`game_state`, `player_joined`, `move`, `game_over`) are handled.
