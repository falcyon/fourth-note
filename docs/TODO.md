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

## Local Testing Setup (Docker)

### Prerequisites

- Docker Desktop installed
- Google Cloud credentials (credentials.json, token.json)

### Quick Start (Windows)

1. **Setup environment**:

   ```powershell
   cp .env.example .env
   # Edit .env with your Google API credentials
   ```

2. **Start all services**:

   ```powershell
   docker compose -f docker-compose.dev.yml up --build
   ```

3. **Run migrations** (first time only):

   ```powershell
   docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
   ```

4. **Access**:
   - Frontend: http://localhost:4444
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Known Issues
_None yet_

---

## Version 1.1 Features

**Focus:** Multi-tenant auth, UI polish

- [x] **Feature 1:** Update README with server URL (<https://fourthnote.leff.in>) and vision
- [x] **Feature 2:** Gmail-based login with multi-tenant data isolation
  - Google Sign-In authentication
  - Per-user data isolation (user_id FK on all tables)
  - Demo account (`leffin7@gmail.com`) for testing/showcasing
- [x] **Feature 6:** Save markdown files alongside PDFs for reference
- [ ] **Feature 9:** UI improvements
  - Auto-scroll progress panel to latest entry
  - Compact image OCR logs: "(4/40)" instead of multiple lines
- [ ] **Feature 10:** Dashboard improvements
  - Show all JSON attributes in main table
  - Remove source/extracted date columns

---

## Version 2.0 Features (Planned)

**Focus:** Smart filtering, multiple data sources, investment-centric architecture

- [ ] **Feature 3:** Relevance check for PDF attachments
  - First check attachment name + email body
  - If unclear, scan the PDF content
  - Skip irrelevant attachments
- [ ] **Feature 4:** Agentic architecture with multiple agents
- [ ] **Feature 5:** Support PPT and Word files via markitdown (no OCR)
- [ ] **Feature 6a:** Source attribution on hover
  - Show context window with source text for each extracted value
- [ ] **Feature 7:** Document management for investments
  - List relevant docs on investment detail page
  - Download capability
- [ ] **Feature 7a:** In-browser document viewer
- [ ] **Feature 8:** Investment-centric database redesign
  - Track source for each extracted value
  - Support multiple sources per investment
  - Meeting notes, manual updates, web data, quarterly calls

---

## Future Enhancements

- [ ] Competitor/similar fund tracking (vector embeddings)
- [ ] pgvector semantic search
- [ ] Email notifications on extraction errors
- [ ] Bulk re-extraction capability
