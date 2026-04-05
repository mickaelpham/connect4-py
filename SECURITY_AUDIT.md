# Security Audit Report — Connect 4 API

**Date:** 2026-04-05 (revision 2)
**Previous audit:** 2026-04-04
**Scope:** Auth layer, DB schema, connection setup, game DB layer (pre-Phase 5)
**Threat model:** Public-facing side project, internet-exposed

---

## Summary

| Severity | Total | Fixed | Accepted | Acknowledged | Open |
|----------|-------|-------|----------|--------------|------|
| High     | 2     | 2     | —        | —            | 0    |
| Medium   | 4     | 3     | 1        | —            | 0    |
| Low      | 5     | 3     | 1        | —            | 1    |
| Info     | 8     | 1     | —        | 5            | 2    |

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

**Location:** `src/connect4/api/app.py:21-26`

`CORSMiddleware` added with `allow_origins=["http://localhost:5173"]`, scoped `allow_methods` and `allow_headers`.

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

### INFO-2: No iss/aud claims in JWT — FIXED

**Location:** `src/connect4/api/tokens.py:25-26,35`

`iss` and `aud` claims (`"connect4"`) added to token creation and validated in `decode_access_token`.

---

## Accepted findings

### MED-2: User enumeration via registration endpoint — ACCEPTED

**Location:** `src/connect4/api/auth.py:53-56`

Still returns HTTP 409 with `"Username already taken"`. Usernames are public in game context, and there is no email-based account recovery. Risk is acceptable for this project's threat model.

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

**Location:** `src/connect4/api/app.py`

Expected for local development. Security headers will be handled at the reverse proxy layer when deploying.

---

## New findings (revision 2)

### LOW-4: slowapi asyncio monkeypatch — FIXED

**Severity:** Low
**Location:** `src/connect4/api/rate_limit.py`

slowapi 0.1.9 uses the deprecated `asyncio.iscoroutinefunction` (removed in Python 3.16). The initial workaround monkeypatched `asyncio.iscoroutinefunction = inspect.iscoroutinefunction`, which mutates stdlib global state and could break other libraries.

**Fix applied:** Replaced with a targeted `warnings.filterwarnings("ignore", ...)` to suppress the deprecation warning until slowapi releases a fix.

---

### LOW-5: Bare `except Exception` swallows JWT configuration errors

**Severity:** Low
**Location:** `src/connect4/api/dependencies.py:29`

`get_current_player` catches all exceptions from `decode_access_token` and returns a generic 401. If `JWT_SECRET` is unset, the `RuntimeError` from `_get_secret()` is swallowed and reported as "Invalid or expired token" instead of surfacing as a 500.

**Recommendation:** Catch `jwt.InvalidTokenError` (and subclasses) specifically, and let other exceptions propagate:
```python
except jwt.InvalidTokenError:
    raise HTTPException(status_code=401, detail="Invalid or expired token")
```

---

### INFO-5: Hardcoded DSN with credentials in source

**Severity:** Info
**Location:** `src/connect4/db/connection.py:5`

`DEFAULT_DSN = "postgresql://connect4:connect4@localhost:5432/connect4"` contains a username/password. This is only used as a local dev fallback (overridden by `DATABASE_URL` in production). The credentials are for a local Docker Compose database and are not sensitive.

No action needed unless this code is deployed without `DATABASE_URL` set.

---

### INFO-6: No `move_number` upper bound constraint

**Severity:** Info
**Location:** migration `3b9771039e7f`, `moves` table

`move_number` has no CHECK constraint. A Connect 4 game has at most 42 moves (7 columns x 6 rows). Adding `CHECK (move_number BETWEEN 1 AND 42)` would prevent invalid data at the DB level.

**Recommendation:** Add in a future migration:
```sql
ALTER TABLE moves ADD CONSTRAINT chk_move_number
  CHECK (move_number BETWEEN 1 AND 42);
```

---

### INFO-7: `winner_id` can be inconsistent with game status

**Severity:** Info
**Location:** migration `3b9771039e7f`, `games` table

No constraint ensures `winner_id` is null when `status != 'won'` or non-null when `status = 'won'`. The application layer could write inconsistent states (e.g., `status='draw'` with a `winner_id`).

**Recommendation:** Add a CHECK constraint:
```sql
ALTER TABLE games ADD CONSTRAINT chk_winner_status_consistency
  CHECK (
    (status = 'won' AND winner_id IS NOT NULL)
    OR (status != 'won' AND winner_id IS NULL)
  );
```

---

### INFO-8: No pagination on `list_player_games`

**Severity:** Info
**Location:** `src/connect4/db/games.py:67-78`

`list_player_games` returns all games for a player with no `LIMIT`/`OFFSET`. For a prolific player, this could return an unbounded result set.

**Recommendation:** Add pagination parameters when building the `GET /games` endpoint in Phase 5.

---

## Game layer — pre-implementation notes (Phase 5)

The following are not bugs — the game API endpoints don't exist yet. These are authorization and validation concerns to address when building Phase 5 endpoints.

### GAME-1: Self-play prevention

`join_game` (`src/connect4/db/games.py:21`) does not check that `player2_id != player1_id`. The API endpoint should reject a player joining their own game.

### GAME-2: Move authorization

`create_move` (`src/connect4/db/moves.py:6`) does not verify that the player is a participant in the game or that it is their turn. These checks should be enforced at the API layer using the core `Game` class.

### GAME-3: Game status update authorization

`update_game_status` (`src/connect4/db/games.py:48`) accepts any status and winner_id without validating that the winner is a participant. The API layer should derive status transitions from the core game logic, not from client input.

### GAME-4: Move + status update atomicity

When a move results in a win or draw, the move insertion and game status update must happen in a single transaction. Ensure the Phase 5 endpoint wraps both operations in `async with conn.transaction()`.

---

## Items confirmed secure

- **SQL injection:** All queries use asyncpg parameterized queries (`$1`, `$2`...). No string interpolation in `src/connect4/db/`.
- **Password hashing:** argon2id with OWASP-compliant defaults, proper verify/hash separation.
- **Refresh token storage:** Only SHA-256 hashes stored; raw tokens never hit the database.
- **Login error messages:** Generic `"Invalid username or password"` — no user enumeration via login.
- **Username normalization:** `.lower()` applied on both register and login.
- **Secrets in git:** `.env` is in `.gitignore`.
- **Token expiry:** 15-minute access tokens, 7-day refresh tokens.
- **Refresh token rotation:** Atomic read-revoke-issue with row-level locking.
- **Rate limiting:** All auth endpoints rate-limited per IP.
- **CORS:** Restrictive origin whitelist with scoped methods/headers.
