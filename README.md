# Fourth Note

**Live at:** [fourthnote.leff.in](https://fourthnote.leff.in)

A centralized brain for investors to track every investment. Fourth Note automatically aggregates investment data from multiple sources, extracts key metrics using AI, and provides a unified dashboard for portfolio oversight.

## Vision

Investors receive information about their investments from many sources: pitch decks, quarterly reports, meeting notes, web updates, and phone calls. Fourth Note aims to be the single source of truth that:

- **Aggregates** data from all sources automatically
- **Extracts** both static info (fund name, managers) and dynamic metrics (returns, fees)
- **Tracks** changes over time
- **Surfaces** relevant comparisons and competitor analysis

## Current Features (v1.0)

### Pitch Deck Processing
- **Gmail Integration** - Monitors inbox for emails with PDF attachments
- **OCR Processing** - Extracts text from scanned pitch decks
- **AI Extraction** - Uses Google Gemini to identify 8 key investment fields:
  - Investment Name, Firm, Strategy Description, Leaders
  - Management Fees, Incentive Fees, Liquidity/Lock, Target Returns
- **Searchable Database** - All extracted data stored in PostgreSQL
- **Web Dashboard** - View, search, edit, and export investment data

### Dashboard Capabilities
- Searchable, sortable investment table
- Detailed view with full extraction data
- Manual email fetch with real-time progress
- CSV export for spreadsheet analysis
- System health monitoring

## Roadmap

### v1.1 (In Progress)
- User authentication via Google Sign-In
- Multi-tenant data isolation
- Markdown file preservation for reference

### v2.0 (Planned)
- Meeting notes ingestion
- Manual data entry interface
- Web scraping for public fund data
- Quarterly call transcription
- Source attribution on hover

### Future
- Competitor/similar fund tracking
- Vector embeddings for semantic search
- Investment comparison tools

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Local development setup (Windows)
- Production deployment (Ubuntu/Docker)
- Cloudflare tunnel configuration

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Database:** PostgreSQL
- **AI:** Google Gemini
- **Infrastructure:** Docker, Nginx, Cloudflare Tunnel
