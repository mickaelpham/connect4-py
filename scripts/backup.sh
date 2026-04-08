#!/bin/bash
set -euo pipefail

BACKUP_DIR=~/connect4/backups
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
COMPOSE_FILE=~/connect4/compose.prod.yaml

# Load env vars for POSTGRES_USER and POSTGRES_DB
set -a
source ~/connect4/.env.prod
set +a

mkdir -p "$BACKUP_DIR"

echo "==> Backing up database..."
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
    | gzip > "$BACKUP_DIR/connect4-$TIMESTAMP.sql.gz"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "==> Backup saved to $BACKUP_DIR/connect4-$TIMESTAMP.sql.gz"
