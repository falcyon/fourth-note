# Fourth Note

> **This is an experiment to see how robust a system can be built using Claude Code as the main developer.**

**Live at:** [fourthnote.leff.in](https://fourthnote.leff.in)

A centralized brain for investors to track every investment. Fourth Note automatically aggregates investment data from multiple sources, extracts key metrics using AI, and provides a unified dashboard for portfolio oversight.

## Current Version: v1.1

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Database:** PostgreSQL 16
- **AI:** Google Gemini
- **Auth:** Google Sign-In, JWT tokens
- **Infrastructure:** Docker, Nginx, Cloudflare Tunnel

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 2. Start services (Windows dev)
docker compose -f docker-compose.dev.yml up --build

# 3. Run migrations
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

Access at: `http://localhost:4444`

## Documentation

| Document | Description |
| -------- | ----------- |
| [PRD.md](docs/PRD.md) | Product Requirements - complete feature list with versions |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, database schema, API design |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment instructions |

## Environment Variables

| Variable | Description |
| -------- | ----------- |
| `GOOGLE_API_KEY` | Gemini API key |
| `GOOGLE_CLIENT_ID` | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `JWT_SECRET_KEY` | JWT signing key |
| `GMAIL_QUERY_SINCE` | Unix timestamp for email fetch cutoff |
| `SCHEDULER_INTERVAL_HOURS` | Hours between auto-fetch (0 to disable) |
