#!/bin/bash
# Fourth Note - Production Deploy Script
# Usage: ./scripts/deploy.sh
#
# Pulls latest code, rebuilds containers, runs migrations, and verifies health.

set -e

cd "$(dirname "$0")"

echo "=== Fourth Note Deploy ==="
echo ""

# 1. Pull latest code
echo "[1/5] Pulling latest code..."
git pull
echo ""

# 2. Build containers
echo "[2/5] Building containers..."
docker compose build
echo ""

# 3. Start containers
echo "[3/5] Starting containers..."
docker compose up -d
echo ""

# 4. Wait for backend to be ready, then run migrations
echo "[4/5] Waiting for backend to be ready..."
for i in $(seq 1 30); do
    if docker compose exec -T backend python -c "import app.main" 2>/dev/null; then
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Backend failed to start. Check logs:"
        echo "  docker compose logs --tail 50 backend"
        exit 1
    fi
    sleep 2
done

echo "Running database migrations..."
docker compose exec -T backend alembic upgrade head
echo ""

# 5. Verify
echo "[5/5] Verifying deployment..."
sleep 2
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/status 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo "Backend: OK"
else
    echo "Backend: WARNING (HTTP $HEALTH) - check logs with: docker compose logs --tail 50 backend"
fi

FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4444 2>/dev/null || echo "000")
if [ "$FRONTEND" = "200" ]; then
    echo "Frontend: OK"
else
    echo "Frontend: WARNING (HTTP $FRONTEND) - check logs with: docker compose logs --tail 50 frontend"
fi

echo ""
echo "=== Deploy complete ==="
docker compose ps --format "table {{.Name}}\t{{.Status}}"
