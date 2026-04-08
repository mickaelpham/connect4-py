#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: ./deploy.sh user@server"
    exit 1
fi

SERVER=$1
REMOTE_DIR="~/connect4"

echo "==> Building images..."
docker buildx build --platform linux/amd64 -f Dockerfile.backend -t connect4-backend .
docker buildx build --platform linux/amd64 -f Dockerfile.frontend -t connect4-caddy .

echo "==> Transferring images to $SERVER..."
docker save connect4-backend connect4-caddy | ssh "$SERVER" docker load

echo "==> Restarting services..."
ssh "$SERVER" "cd $REMOTE_DIR && docker compose -f compose.prod.yaml --env-file=.env.prod up -d"

echo "==> Done!"
