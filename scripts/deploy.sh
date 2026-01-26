#!/bin/bash
# Fourth Note - Quick Deploy Script
# Copy and paste this entire block into your Ubuntu terminal

cd ~/fourth-note && \
git pull && \
docker compose build && \
docker compose up -d && \
docker compose exec backend alembic upgrade head && \
echo "Deploy complete! Check status with: docker compose ps"
