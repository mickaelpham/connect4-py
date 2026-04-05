# Security Audit Report — Connect 4 API

**Date:** 2026-04-04
**Scope:** Auth layer, DB schema, connection setup (pre-Phase 5)
**Threat model:** Public-facing side project, internet-exposed

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 2     |
| Medium   | 4     |
| Low      | 3     |
| Info     | 4     |

---

## Findings

### HIGH-1: No rate limiting on authentication endpoints

**Severity:** High
**Location:** `src/connect4/api/auth.py:40,58,73`

The `/register`, `/login`, and `/refresh` endpoints have no rate limiting. An attacker can brute-force passwords, spam registrations, or exhaust refresh tokens without restriction.

**Recommendation:** Add rate limiting middleware. Options:
- [`slowapi`](https://github.com/laurentS/slowapi) (built on `limits`, easiest to integrate with FastAPI)
- Reverse proxy rate limiting (nginx/Caddy) if deployed behind one
- Suggested limits: `/login` 5 req/min per IP, `/register` 3 req/min per IP, `/refresh` 10 req/min per IP

---

### HIGH-2: LoginRequest accepts unbounded password length (hash DoS)

**Severity:** High
**Location:** `src/connect4/api/schemas.py:9-11`

`LoginRequest` has no `max_length` on the `password` field. Argon2 will attempt to hash arbitrarily large input, which is CPU- and memory-intensive. An attacker can send multi-MB passwords to exhaust server resources.

**Recommendation:** Add `password: str = Field(max_length=72)` to `LoginRequest`, matching `RegisterRequest`. The 72-byte limit is a standard ceiling for password hashing.

---

### MED-1: Refresh token rotation race condition

**Severity:** Medium
**Location:** `src/connect4/api/auth.py:73-92`

The `/refresh` endpoint reads the token, revokes it, then issues a new pair — but these operations are not wrapped in a transaction. Two concurrent requests with the same refresh token could both pass the `get_refresh_token_by_hash` check before either revokes it, resulting in two valid token pairs from a single refresh token.

**Recommendation:** Wrap the read-revoke-issue sequence in an explicit `async with conn.transaction():` block. Alternatively, use `SELECT ... FOR UPDATE` on the refresh token row to serialize concurrent access.

---

### MED-2: User enumeration via registration endpoint

**Severity:** Medium
**Location:** `src/connect4/api/auth.py:48-53`

The `/register` endpoint returns HTTP 409 with `"Username already taken"` when a duplicate username is submitted. This allows an attacker to enumerate valid usernames.

**Recommendation:** Return a generic error (e.g., `"Registration failed"`) or a 200 with a message like `"If this username is available, check your email"` (if email verification is added later). For a side project, this is an acceptable tradeoff if acknowledged — but flag it before adding any sensitive features.

**Status:** Accepted. Usernames are not sensitive (public in game context), and there is no email-based account recovery. Risk is acceptable for this project's threat model.

---

### MED-3: No CORS middleware configured

**Severity:** Medium
**Location:** `src/connect4/api/app.py:16`

The FastAPI app has no CORS configuration. If a browser-based frontend is added (Phase 6), cross-origin requests will be blocked. More importantly, the absence of an explicit CORS policy means any misconfiguration at the proxy level could expose the API to cross-origin attacks.

**Recommendation:** Add `CORSMiddleware` with an explicit `allow_origins` list. Even before the frontend exists, setting a restrictive default is good practice:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], ...)
```

---

### MED-4: No database CHECK constraints on critical columns

**Severity:** Medium
**Location:** migrations `3b9771039e7f` lines 31,43

- `games.status` accepts any string — should be constrained to `('waiting', 'in_progress', 'won', 'draw')`
- `moves.column` accepts any smallint — should be constrained to `0..6`

Without these, a bug in the application layer could write invalid data that corrupts game state silently.

**Recommendation:** Add a migration with:
```sql
ALTER TABLE games ADD CONSTRAINT chk_game_status
  CHECK (status IN ('waiting', 'in_progress', 'won', 'draw'));
ALTER TABLE moves ADD CONSTRAINT chk_move_column
  CHECK ("column" BETWEEN 0 AND 6);
```

---

### LOW-1: assert used for control flow in register endpoint

**Severity:** Low
**Location:** `src/connect4/api/auth.py:54`

`assert player is not None` will be stripped if Python is run with `-O` (optimize). If the assertion is removed, the code proceeds with `player = None` and will fail at `player["id"]` with an unhelpful `TypeError`.

**Recommendation:** Replace with an explicit check:
```python
if player is None:
    raise HTTPException(status_code=500, detail="Failed to create player")
```

---

### LOW-2: Stale refresh tokens accumulate indefinitely

**Severity:** Low
**Location:** `src/connect4/db/refresh_tokens.py`

Revoked and expired refresh tokens are never deleted — only soft-revoked via `revoked_at`. Over time, this table will grow unboundedly.

**Recommendation:** Add a periodic cleanup job or a migration to add a cron-triggered `DELETE FROM refresh_tokens WHERE revoked_at IS NOT NULL OR expires_at < now()`. For a side project, a manual `make db-cleanup` target is sufficient.

**Status:** Accepted. Token table growth is negligible for a side project with low traffic. A cleanup job can be added later if the table becomes large.

---

### LOW-3: Inconsistent ON DELETE policy across foreign keys

**Severity:** Low
**Location:** migrations `3b9771039e7f:37-38`, `ce6b09c779e0:23`

`refresh_tokens.player_id` has `ON DELETE CASCADE`, but `games.player1_id`, `games.player2_id`, and `moves.player_id` do not. If a player is deleted, their refresh tokens are cleaned up but their games and moves become orphaned with dangling FK references (blocked by the FK constraint, so the DELETE would fail).

**Recommendation:** Decide on a consistent policy — either all cascade, all restrict, or use soft deletes across the board. For a game app, `RESTRICT` (the default) is probably correct for games/moves, and `CASCADE` is correct for refresh tokens. Document this decision.

---

### INFO-1: JWT uses HS256 — acceptable for single service

**Severity:** Info
**Location:** `src/connect4/api/tokens.py:28,32`

HS256 (symmetric) is fine for a single-service app where the same service issues and verifies tokens. If you ever split into multiple services, switch to RS256/ES256 (asymmetric) so that verifiers don't need the signing key.

No action needed now.

**Status:** Acknowledged. HS256 is appropriate for the current single-service architecture.

---

### INFO-2: No iss/aud claims in JWT

**Severity:** Info
**Location:** `src/connect4/api/tokens.py:22-27`

The JWT payload lacks `iss` (issuer) and `aud` (audience) claims. In a single-service setup this is fine. If other services are added, tokens could be accepted across services unintentionally.

**Recommendation for future:** Add `"iss": "connect4"` and `"aud": "connect4"` to the payload, and validate them in `decode_access_token`.

**Status:** Fixed. Added `iss` and `aud` claims to token creation and validation.

---

### INFO-3: Argon2id defaults are OWASP-compliant

**Severity:** Info
**Location:** `src/connect4/api/passwords.py:4`

The argon2-cffi defaults are: `time_cost=3`, `memory_cost=65536` (64 MiB), `parallelism=4`, `type=argon2id`. This meets or exceeds OWASP's minimum recommendation (19 MiB, 2 iterations). Password max length of 72 prevents hash-DoS on registration.

No action needed.

**Status:** Acknowledged. Argon2id defaults meet OWASP recommendations.

---

### INFO-4: No security headers or HTTPS enforcement

**Severity:** Info
**Location:** `src/connect4/api/app.py`

The app does not set security headers (`Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`) or enforce HTTPS. For local development this is expected. In production, these should be set — typically at the reverse proxy (nginx/Caddy) rather than in the app.

**Recommendation:** When deploying, ensure the reverse proxy adds these headers. If serving directly, consider adding `starlette-security-headers` or equivalent middleware.

**Status:** Acknowledged. Security headers will be handled at the reverse proxy layer when deploying.

---

## Items confirmed secure

- **SQL injection:** All database queries use asyncpg parameterized queries (`$1`, `$2`...). No string interpolation found in `src/connect4/db/`.
- **Password hashing:** argon2id with strong defaults, proper verify/hash separation.
- **Refresh token storage:** Only SHA-256 hashes are stored; raw tokens never hit the database.
- **Login error messages:** Generic `"Invalid username or password"` — no user enumeration via login.
- **Username normalization:** `.lower()` applied on both register and login — consistent.
- **Secrets in git:** `.env` is in `.gitignore`.
- **Token expiry:** 15-minute access tokens and 7-day refresh tokens are reasonable defaults.
