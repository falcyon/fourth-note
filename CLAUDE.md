# Fourth Note - Claude Code Context

## Project Overview

Fourth Note is a pitch deck tracking application that automatically fetches investor update emails from Gmail, extracts PDF attachments, converts them to text, and uses Gemini AI to extract structured investment data.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL │
│  React/Vite │     │   FastAPI   │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    ▼           ▼
               Gmail API    Gemini AI
```

**Tech Stack:**
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Database:** PostgreSQL 16 Alpine
- **APIs:** Gmail API (OAuth2), Google Gemini AI

## Key Directories

```
backend/
├── app/
│   ├── api/          # FastAPI route handlers
│   ├── models/       # SQLAlchemy models (email, document, investment)
│   ├── schemas/      # Pydantic schemas
│   └── services/     # Business logic
│       ├── gmail_service.py      # Gmail API integration
│       ├── pdf_converter.py      # PDF to text (markitdown + OCR)
│       ├── extraction_service.py # Gemini AI data extraction
│       └── scheduler.py          # Background job scheduler

frontend/
├── src/
│   ├── pages/        # Dashboard, InvestmentDetail, Settings
│   ├── components/   # Reusable UI components
│   └── api/          # API client

scripts/
├── init-oauth.py     # Gmail OAuth setup (run locally with browser)
```

## Deployment

**Target:** Ubuntu NUC with external drive

**Folder Layout:**
```
~/fourth-note/                    # Git repo
├── .env                          # Secrets (not in git)
├── token.json                    # Gmail OAuth token (not in git)
├── credentials.json              # Google Cloud credentials (not in git)

/mnt/WD1/fourth-note/             # External drive data
├── postgres/                     # Database files
└── data/emails/                  # Downloaded PDFs
```

**Docker volumes use bind mounts to `/mnt/WD1/fourth-note/`** for persistence on external storage.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `POSTGRES_PASSWORD` | Database password (required) |
| `GOOGLE_API_KEY` | Gemini API key (required) |
| `GMAIL_QUERY_SINCE` | Unix timestamp for email fetch cutoff |
| `SCHEDULER_INTERVAL_HOURS` | Hours between automatic email checks |

## Common Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f backend

# Rebuild after code changes
docker compose build && docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Re-authenticate Gmail (requires browser)
python3 scripts/init-oauth.py
```

## API Endpoints

- `GET /api/v1/status` - Health check
- `GET /api/v1/investments` - List all investments
- `GET /api/v1/investments/{id}` - Investment details
- `POST /api/v1/trigger/fetch` - Manually trigger email fetch
- `GET /api/v1/oauth/status` - Gmail OAuth status

## Data Flow

1. **Email Fetch:** Gmail API queries for emails with PDF attachments since `GMAIL_QUERY_SINCE`
2. **PDF Download:** Attachments saved to `/mnt/WD1/fourth-note/data/emails/`
3. **Text Extraction:** markitdown converts PDF to markdown (falls back to OCR)
4. **AI Extraction:** Gemini extracts structured data (company, metrics, dates)
5. **Storage:** Results saved to PostgreSQL with status tracking

## Notes for Development

- Frontend runs on port 4444 (nginx), backend on port 8000
- PostgreSQL not exposed externally (internal Docker network only)
- OAuth token refresh is automatic; manual re-auth needed if revoked
- Scheduler runs in-process with FastAPI (APScheduler)
