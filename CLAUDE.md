# Fourth Note - Claude Code Context

## Project Overview

Fourth Note is an investment tracking application that:

1. Fetches investor update emails from Gmail
2. Extracts PDF attachments and converts to text (with OCR)
3. Uses Gemini AI to extract structured investment data
4. Provides a web dashboard for viewing and managing investments

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Database:** PostgreSQL 16
- **APIs:** Gmail API (OAuth2), Google Gemini AI
- **Auth:** Google Sign-In, JWT tokens

## Project Structure

```
fourth-note/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic
│   │   └── middleware/        # Auth middleware
│   ├── alembic/               # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── api/               # API client
│   │   ├── components/        # UI components
│   │   ├── context/           # React context (auth)
│   │   └── pages/             # Page components
│   ├── Dockerfile
│   └── package.json
│
├── scripts/
│   └── init-oauth.py          # Gmail OAuth setup
│
├── config/
│   └── nginx/                 # Nginx configs for deployment
│
├── .env.example               # Environment template
├── docker-compose.yml         # Production (Linux server)
├── docker-compose.dev.yml     # Local development (Windows)
├── credentials.json           # Google Cloud credentials (gitignored)
└── token.json                 # Gmail OAuth token (gitignored)
```

## Quick Start

### 1. Setup Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Run with Docker

**Local Development (Windows):**

```bash
docker compose -f docker-compose.dev.yml up --build
```

**Production (Linux server):**

```bash
docker compose up -d --build
```

### 3. Run Migrations

```bash
docker compose exec backend alembic upgrade head
```

Access at: http://localhost:4444

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `GOOGLE_CLIENT_ID` | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `JWT_SECRET_KEY` | JWT signing key |
| `GMAIL_QUERY_SINCE` | Unix timestamp for email fetch cutoff |
| `SCHEDULER_INTERVAL_HOURS` | Hours between auto-fetch (0 to disable) |

## API Endpoints

- `POST /api/v1/auth/login` - Google Sign-In
- `GET /api/v1/auth/me` - Current user info
- `GET /api/v1/investments` - List investments
- `GET /api/v1/investments/{id}` - Investment details
- `GET /api/v1/trigger/fetch-emails/stream` - Trigger email fetch (SSE)
- `GET /api/v1/status` - Health check

## Development & Testing

**IMPORTANT:** All building and testing must be done through Docker containers. Do not run `npm run build`, `tsc`, or other build commands directly on the host machine.

```bash
# Build and test frontend changes
docker compose -f docker-compose.dev.yml build frontend
docker compose -f docker-compose.dev.yml up -d

# Build and test backend changes
docker compose -f docker-compose.dev.yml build backend
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f frontend
docker compose -f docker-compose.dev.yml logs -f backend
```

## Database Migrations

```bash
# Inside container
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"
```

## Key Files

- `backend/app/main.py` - FastAPI app entry point
- `backend/app/services/extraction_service.py` - Gemini AI extraction
- `backend/app/services/gmail_service.py` - Gmail API integration
- `frontend/src/App.tsx` - React app with routing
- `frontend/src/context/AuthContext.tsx` - Authentication state

## Feature Tracking

- **PRD.md** = Planning (what we want to build, with "planned for vX.X")
- **CHANGELOG.md** = History (what actually shipped, with dates)

When completing a feature:

1. Update PRD.md status from "planned" to "completed in vX.X"
2. Add entry to CHANGELOG.md under `[Unreleased]`

## Version Management

**IMPORTANT:** Use git tags and CHANGELOG.md for version tracking.

### When to Release

- **Patch** (v1.1.1 → v1.1.2): Bug fixes, minor UI tweaks
- **Minor** (v1.1 → v1.2): New features, significant changes
- **Major** (v1.x → v2.0): Breaking changes, major rewrites

### Release Steps

1. Update `CHANGELOG.md`:
   - Move items from `[Unreleased]` to new version section
   - Add release date
   - Categorize changes: Added, Changed, Fixed, Removed

2. Update `README.md` version number

3. Commit and tag:

   ```bash
   git add -A
   git commit -m "Release v1.1.2"
   git tag -a v1.1.2 -m "Demo mode improvements"
   git push origin main --tags
   ```

### Change Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Fixed**: Bug fixes
- **Removed**: Removed features
- **Security**: Security-related changes

### Git Push Policy

**IMPORTANT:** Do NOT automatically push to git. Only push when:

1. A meaningful, complete change has been made (not partial work)
2. The user explicitly asks to push

Wait for user confirmation before running `git push`. It's fine to commit locally, but pushing should be deliberate.

## Documentation

- `README.md` - Project overview and setup
- `CHANGELOG.md` - Version history (what changed when)
- `docs/PRD.md` - Product requirements (feature planning)
- `docs/DEPLOYMENT.md` - Deployment instructions
- `docs/ARCHITECTURE.md` - System architecture
