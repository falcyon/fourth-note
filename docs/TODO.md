# Fourth Note - Implementation Progress

**Version 1.0.0**

## Phase 0: Project Initialization
- [x] Create project directory structure
- [x] Create docs/ARCHITECTURE.md
- [x] Create docs/TODO.md
- [x] Create README.md
- [x] Create docs/DEPLOYMENT.md
- [x] Create .gitignore
- [x] Create .env.example

## Phase 1: Backend Setup
- [x] Create requirements.txt with dependencies
- [x] Create backend Dockerfile
- [x] Set up PostgreSQL in docker-compose
- [x] Create SQLAlchemy models (emails, documents, investments)
- [x] Configure Alembic for migrations
- [x] Create initial migration
- [x] Implement FastAPI main.py with health endpoint
- [x] Create config.py for environment variables
- [x] Create database.py for session management

## Phase 2: Refactor Services
- [x] Create gmail_service.py (OAuth with JSON token, auto-refresh)
- [x] Create email_processor.py (fetch emails, save to DB)
- [x] Create pdf_converter.py (OCR + markdown)
- [x] Create extraction_service.py (Gemini extraction, save to DB)

## Phase 3: API Layer
- [x] Create investment routes (CRUD)
- [x] Create email routes (list)
- [x] Create document routes (markdown view)
- [x] Create trigger routes (manual fetch)
- [x] Create status routes (health, scheduler)
- [x] Create CSV export endpoint
- [x] Add pagination support
- [x] Add search/filter support

## Phase 4: Scheduler
- [x] Integrate APScheduler
- [x] Create 6-hour cron job
- [x] Add scheduler status endpoint
- [x] Handle graceful shutdown

## Phase 5: React Frontend
- [x] Initialize Vite + TypeScript project
- [x] Configure Tailwind CSS
- [x] Create API client (fetch wrapper)
- [x] Build Dashboard page (investments table)
- [x] Add search and filter UI
- [x] Add pagination controls
- [x] Add "Fetch Emails" button
- [x] Build InvestmentDetail page
- [x] Build Settings page
- [x] Add status indicators
- [x] Create frontend Dockerfile with nginx

## Phase 6: Docker Integration
- [x] Create backend Dockerfile (with Tesseract)
- [x] Create frontend Dockerfile (nginx)
- [x] Create docker-compose.yml
- [x] Configure volume mounts
- [x] Test full stack locally

## Phase 7: Deployment
- [x] Document deployment steps
- [x] Create init-oauth.sh script
- [ ] Test on target Ubuntu machine

## Phase 8: Version 1.0.0 Release
- [x] Full pipeline tested (Gmail → PDF → OCR → Gemini → Database)
- [x] Real-time progress tracking via SSE
- [x] Rename project to "Fourth Note"
- [x] Update all documentation

---

## Local Testing Setup

### Prerequisites
- Python 3.11+ installed
- Node.js 18+ installed
- PostgreSQL running (via Docker or local install)
- Tesseract-OCR installed (already in PATH)

### Quick Start (Windows)

1. **Start PostgreSQL** (one of these options):
   ```cmd
   # Option A: Docker Desktop (if installed)
   docker run -d --name fourth-note-postgres -e POSTGRES_USER=pitchdeck -e POSTGRES_PASSWORD=devpassword -e POSTGRES_DB=pitchdeck -p 5432:5432 postgres:16-alpine

   # Option B: Local PostgreSQL - create database manually
   psql -U postgres -c "CREATE USER pitchdeck WITH PASSWORD 'devpassword';"
   psql -U postgres -c "CREATE DATABASE pitchdeck OWNER pitchdeck;"
   ```

2. **Backend setup**:
   ```cmd
   cd fourth-note\backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

3. **Frontend setup** (new terminal):
   ```cmd
   cd fourth-note\frontend
   npm install
   npm run dev
   ```

4. **Access**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Known Issues
_None yet_

## Future Enhancements
- [ ] Email notifications on extraction errors
- [ ] Bulk re-extraction capability
- [ ] Document preview in UI
- [ ] Multi-user support with authentication
- [ ] pgvector semantic search
