# Deployment

Connect 4 is deployed to a single VPS at `connect4.mickael.dev` using Docker Compose.

## Architecture

```
Internet → Caddy (auto HTTPS) → /api/* → uvicorn:8000
                                → /*    → static files
         Internal: uvicorn → postgres:5432
```

Three containers in one `compose.prod.yaml` stack:
- **caddy** — serves the Svelte frontend, reverse-proxies `/api` to backend, handles TLS
- **backend** — FastAPI app with uvicorn, runs Alembic migrations on startup
- **postgres** — PostgreSQL 18 with a persistent volume

## First-Time Server Setup

1. **DNS**: Point `connect4.mickael.dev` A record to the server IP.

2. **Create the project directory**:
   ```bash
   ssh user@server "mkdir -p ~/connect4"
   ```

3. **Create `.env.prod`** on the server at `~/connect4/.env.prod`:
   ```env
   POSTGRES_USER=connect4
   POSTGRES_DB=connect4
   POSTGRES_PASSWORD=<generate-a-strong-password>
   JWT_SECRET=<generate-a-strong-secret>
   CORS_ORIGINS=https://connect4.mickael.dev
   DOMAIN=connect4.mickael.dev
   ```

4. **Copy the compose file**:
   ```bash
   scp compose.prod.yaml user@server:~/connect4/
   ```

5. **Deploy**:
   ```bash
   ./scripts/deploy.sh user@server
   ```

Caddy automatically provisions a Let's Encrypt certificate on first request.

## Deploying Updates

```bash
./scripts/deploy.sh user@server
```

This builds images locally, transfers them via SSH (no registry), and restarts the stack. Expect a few seconds of downtime during restart.

## Manual Operations

**View logs:**
```bash
ssh user@server "cd ~/connect4 && docker compose -f compose.prod.yaml logs -f"
```

**Restart a single service:**
```bash
ssh user@server "cd ~/connect4 && docker compose -f compose.prod.yaml restart backend"
```

**Run a migration manually:**
```bash
ssh user@server "cd ~/connect4 && docker compose -f compose.prod.yaml exec backend uv run alembic upgrade head"
```

**Open a psql shell:**
```bash
ssh user@server "cd ~/connect4 && docker compose -f compose.prod.yaml exec postgres psql -U connect4 connect4"
```
