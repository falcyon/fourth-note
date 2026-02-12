#!/bin/bash
# Fourth Note - Reset all investment data and re-fetch
# Usage: bash scripts/reset-data.sh
#
# Clears all emails, documents, and investments from the database,
# removes cached files, then triggers a fresh email fetch.

set -e

cd "$(dirname "$0")/.."

echo "=== Fourth Note Data Reset ==="
echo ""
echo "This will DELETE all emails, documents, and investments."
echo "Users and Gmail connections will be preserved."
echo ""
read -p "Are you sure? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "[1/3] Clearing database tables..."
docker compose exec -T postgres psql -U pitchdeck -d pitchdeck -c \
    "DELETE FROM investments; DELETE FROM documents; DELETE FROM emails;"
echo ""

echo "[2/3] Removing cached files..."
docker compose exec backend rm -rf /app/data/emails/* /app/data/markdown/*
echo ""

echo "[3/3] Triggering fresh email fetch..."
curl -s -X POST http://localhost:8000/api/v1/trigger/fetch-emails | head -c 500
echo ""
echo ""
echo "=== Reset complete ==="
echo "Watch progress at http://localhost:4444 or with: docker compose logs -f backend"
