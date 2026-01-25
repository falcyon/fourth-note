# Fourth Note - Architecture Documentation

**Version 1.0.0**

## System Overview

Fourth Note is a three-tier application designed for automated extraction of investment information from PDF pitch decks received via email.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│                    Port 80 (nginx reverse proxy)                 │
├─────────────────────────────────────────────────────────────────┤
│                       Backend (FastAPI)                          │
│                          Port 8000                               │
│  ┌──────────────┬──────────────┬──────────────┬───────────────┐ │
│  │ Gmail Service│ PDF Converter│  Extraction  │   Scheduler   │ │
│  │              │   (OCR)      │   (Gemini)   │ (APScheduler) │ │
│  └──────────────┴──────────────┴──────────────┴───────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                     PostgreSQL + pgvector                        │
│                          Port 5432                               │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React + Vite + TypeScript | Single-page application |
| Styling | Tailwind CSS | Utility-first CSS framework |
| Backend | FastAPI (Python 3.11+) | REST API server |
| Database | PostgreSQL 16 | Primary data store |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Migrations | Alembic | Schema versioning |
| OCR | Tesseract + PyMuPDF | PDF text extraction |
| AI | Google Gemini API | Field extraction |
| Scheduler | APScheduler | Periodic job execution |
| Deployment | Docker Compose | Container orchestration |

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│   emails    │       │  documents  │       │   investments   │
├─────────────┤       ├─────────────┤       ├─────────────────┤
│ id (PK)     │──────<│ id (PK)     │──────<│ id (PK)         │
│ gmail_id    │       │ email_id(FK)│       │ document_id(FK) │
│ subject     │       │ filename    │       │ investment_name │
│ sender      │       │ markdown    │       │ firm            │
│ received_at │       │ status      │       │ strategy_desc   │
│ status      │       └─────────────┘       │ leaders         │
└─────────────┘                             │ mgmt_fees       │
                                            │ incentive_fees  │
                                            │ liquidity_lock  │
                                            │ target_returns  │
                                            │ raw_json        │
                                            │ created_at      │
                                            └─────────────────┘
```

### Table Definitions

**emails** - Tracks processed Gmail messages
- `id`: UUID primary key
- `gmail_message_id`: Unique Gmail ID (prevents reprocessing)
- `subject`: Email subject line
- `sender`: Sender email address
- `received_at`: Original email timestamp
- `status`: Processing status (pending/processing/completed/failed)

**documents** - PDF attachments from emails
- `id`: UUID primary key
- `email_id`: Foreign key to emails table
- `filename`: Original PDF filename
- `markdown_content`: Converted markdown text
- `processing_status`: Conversion status

**investments** - Extracted investment data
- `id`: UUID primary key
- `document_id`: Foreign key to documents table
- 8 extracted fields (investment_name through target_net_returns)
- `raw_extraction_json`: Complete Gemini response for debugging
- `created_at`: Extraction timestamp

## Service Architecture

### Gmail Service (`services/gmail_service.py`)
Handles OAuth authentication and email fetching.

**Key responsibilities:**
- Load credentials from token.json
- Automatic token refresh (no browser needed after initial setup)
- Query emails by date filter
- Fetch message details and attachments

**OAuth Flow:**
1. Initial setup runs on host machine (not Docker)
2. Browser-based OAuth creates token.json
3. Token mounted into container as volume
4. Container handles automatic refresh

### Email Processor (`services/email_processor.py`)
Orchestrates email fetching and attachment saving.

**Flow:**
1. Query Gmail for new messages since last check
2. Skip already-processed message IDs (from DB)
3. Create email record in database
4. Download PDF attachments
5. Create document records
6. Update email status

### PDF Converter (`services/pdf_converter.py`)
Converts PDFs to markdown using OCR.

**Process:**
1. Open PDF with PyMuPDF
2. For each page, detect image blocks
3. Run Tesseract OCR on images
4. Overlay extracted text onto PDF
5. Convert entire PDF to markdown
6. Return markdown content

### Extraction Service (`services/extraction_service.py`)
Uses Gemini AI to extract structured data.

**Prompt template extracts:**
- Investment name
- Firm name
- Strategy description
- Leaders/PM/CEO
- Management fees
- Incentive fees
- Liquidity/lock terms
- Target net returns

**Output:** JSON object with 8 fields, stored in investments table.

### Scheduler (`services/scheduler.py`)
Manages periodic job execution with APScheduler.

**Configuration:**
- Runs email fetch every 6 hours
- Stores next run time for status endpoint
- Graceful shutdown handling

## API Design

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/investments` | List investments (paginated) |
| GET | `/api/v1/investments/{id}` | Get single investment |
| PUT | `/api/v1/investments/{id}` | Update investment |
| GET | `/api/v1/investments/export/csv` | Export all as CSV |
| GET | `/api/v1/emails` | List processed emails |
| GET | `/api/v1/documents/{id}/markdown` | View document markdown |
| POST | `/api/v1/trigger/fetch-emails` | Manual email fetch |
| GET | `/api/v1/status` | System health status |
| GET | `/api/v1/scheduler/status` | Scheduler info |
| GET | `/api/v1/oauth/status` | Gmail connection status |

### Query Parameters (Investments List)

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `search`: Full-text search across all fields
- `sort_by`: Column to sort (default: created_at)
- `sort_order`: asc/desc (default: desc)

## Adding New Extraction Fields

To add a new field to extract:

1. **Update schema** (`models/investment.py`):
   ```python
   new_field = Column(String(255))
   ```

2. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "Add new_field"
   alembic upgrade head
   ```

3. **Update extraction prompt** (`services/extraction_service.py`):
   ```python
   FIELDS_FORMATS = {
       ...
       "New Field": "Format instructions",
   }
   ```

4. **Update Pydantic schemas** (`schemas/investment.py`)

5. **Update frontend** (add column to table, detail view)

## Deployment Architecture

```
Ubuntu Mini PC
├── Docker Engine
│   ├── postgres (container)
│   │   └── Volume: postgres_data
│   ├── backend (container)
│   │   └── Volume: backend_data (emails, markdown, token.json)
│   └── frontend (container)
│       └── nginx serving static files
└── Host filesystem
    └── token.json (mounted into backend)
```

## Security Considerations

- OAuth tokens stored on host, mounted read-only into container
- Database credentials via environment variables
- Gemini API key via environment variable
- No external network access except Gmail API and Gemini API
- Frontend communicates only with backend API
