# Fourth Note - Product Requirements Document

This document describes the features of Fourth Note, an investment tracking application. It serves as the planning document for what we want to build.

For version history and what actually shipped, see [CHANGELOG.md](../CHANGELOG.md).

---

## 1. Agentic Engine

The AI-powered extraction engine processes documents and extracts structured investment data. It receives markdown content from converted PDFs and uses Google Gemini to identify and extract key investment metrics.

### 1.1 AI-Powered Data Extraction (v1.0)

The extraction service sends markdown content to the Gemini API with a structured prompt requesting JSON output. It extracts the following fields: Investment Name, Firm, Strategy Description, Leaders (pipe-separated for multiple people), Management Fees, Incentive Fees, Liquidity/Lock terms, and Target Returns.

In v1.1, the leaders field separator was changed from comma to pipe (`|`) to support names containing commas, and all investment fields were migrated from VARCHAR(255) to TEXT to handle longer extracted values.

### 1.2 Multi-Agent Architecture (planned for v2.0)

The current single-prompt approach will evolve into a multi-agent system with specialized agents: a Relevance Agent to filter irrelevant documents before processing, an Extraction Agent for structured data extraction, and a Validation Agent for quality checks on extracted data.

---

## 2. Email-based Document Ingestion

The core pipeline fetches emails from Gmail, extracts PDF attachments, converts them to text, and processes them through the AI extraction engine.

### 2.1 Gmail API Integration (v1.0)

The application connects to Gmail via OAuth2 using the `gmail.readonly` scope. It fetches emails based on a configurable date filter (`GMAIL_QUERY_SINCE` environment variable as Unix timestamp), identifies PDF attachments, and downloads them for processing. Tokens are automatically refreshed when expired.

In v1.1, Gmail connection became per-user, with each user connecting their own Gmail account through the Settings page. OAuth tokens are stored per-user in the database with automatic refresh handling.

### 2.2 PDF to Markdown Conversion (v1.0)

PDFs are converted to markdown text for AI processing. The system uses Tesseract OCR to extract text from scanned or image-based PDFs, processing page-by-page by converting each page to an image first. Digital PDFs can have text extracted directly without OCR. In v1.1, markdown files are saved alongside PDFs for reference and debugging.

### 2.3 Database Storage (v1.0)

All data is stored in PostgreSQL with full CRUD support. The schema includes tables for email metadata (subject, sender, date), documents (PDF files and processing status), and investments (extracted data with field attribution).

In v1.1, the schema was redesigned to be investment-centric with field attribution tracking. A users table was added for multi-tenant support, and all tables received a `user_id` foreign key for data isolation.

### 2.4 Email Fetch Triggers (v1.0)

Users can trigger email processing on demand via a dashboard button. Progress is streamed in real-time using Server-Sent Events, showing each step: fetching emails, downloading attachments, OCR progress, and AI extraction results.

A background scheduler (APScheduler) automatically fetches emails at a configurable interval (`SCHEDULER_INTERVAL_HOURS`, default 6 hours in production, disabled in development). The scheduler gracefully shuts down with the application.

### 2.5 Smart Document Filtering (planned for v2.0)

Automatically filter out irrelevant PDF attachments before processing. The system will check attachment filenames and email body/subject for relevance signals, scan PDF content if metadata is unclear, and automatically skip non-investment documents.

### 2.6 Multi-Format Support (planned for v2.0)

Support additional document formats beyond PDF, including PowerPoint (PPT/PPTX) and Word documents (DOC/DOCX), using the markitdown library for conversion.

---

## 3. Web Dashboard

A React-based frontend for viewing and managing investment data, built with TypeScript, Vite, and Tailwind CSS.

### 3.1 Investment List View (v1.0)

The main dashboard displays all investments in a sortable, searchable interface. Users can search across all investment fields with full-text search, sort by clicking column headers, and navigate large datasets with pagination controls.

In v1.1, the UI was updated with a modern dark theme and card-based layout for better readability.

**Planned for v1.2:** Display all extracted JSON attributes in the table and remove source/extracted date columns.

### 3.2 Investment Detail View (v1.0)

A detailed view showing all extracted fields for a single investment. In v1.1, field attribution was added to show the source document for each extracted value.

### 3.3 Document Management (v1.1)

The investment detail page shows associated documents with their relationship type. Users can download original PDF files and extracted markdown files.

**Planned for v2.0:** In-browser markdown preview and PDF viewer to view documents without downloading.

### 3.4 Source Attribution (planned for v2.0)

Show where each extracted value came from in the source document. On hover over any field, display a context window with surrounding text from the source.

### 3.5 CSV Export (v1.0)

Export all investments to a CSV file for spreadsheet analysis and external reporting.

### 3.6 Settings Page (v1.0)

Displays system status including database and Gmail connection status, scheduler information (next run time, last run result), and database statistics (counts of emails, documents, investments).

In v1.1, Gmail connection UI was added with connect/disconnect buttons for OAuth management.

### 3.7 Progress Panel (v1.0)

A dashboard panel displaying real-time processing status during email fetch operations, with success/error indicators for each processing step.

**Planned for v1.2:** Auto-scroll to show latest entry, and compact OCR logs showing "(4/40)" instead of multiple log lines per page.

### 3.8 UI Redesign from Figma (planned for v2.0)

Replace the current Claude Code-generated UI with professional design from Figma mockups. The current UI is functional with readability improvements but lacks polished visual design.

---

## 4. User Authentication & Multi-Tenancy

Secure user authentication via Google OAuth2 Sign-In with JWT session management and per-user data isolation.

### 4.1 Google Sign-In (v1.1)

Users authenticate via a Google Sign-In button that returns an ID token. The backend verifies the token's authenticity with Google and creates a user record on first login. JWT session tokens are issued for authenticated sessions, stored in browser localStorage.

### 4.2 Protected Routes (v1.1)

Frontend route guards redirect unauthenticated users to the login page. The API client automatically clears authentication and redirects to login on 401 responses.

### 4.3 Multi-Tenant Data Isolation (v1.1)

Each user can only access their own data. All API queries filter by the authenticated user's ID, and all records are linked to the creating user.

### 4.4 Demo Mode (v1.1)

The application supports a demo mode for showcase purposes. On load, the app attempts to auto-login as a demo user (`fourthnotetest@gmail.com`). If the demo user doesn't exist, Google Sign-In is shown.

Demo users see a hero banner with the app description and a "Sign in with Google" button. Authenticated users see a clean dashboard without the banner, with "My Investments" instead of "Demo Investments" as the header. The logout button (only shown for authenticated users) returns to the demo landing page.

---

## Future Features

These features are under consideration for future versions:

- **Competitor/Fund Tracking** - Track similar or competing funds using vector embeddings for similarity matching
- **Semantic Search** - pgvector-based semantic search across all documents for natural language queries
- **Email Notifications** - Alerts on extraction errors or when new investments are detected
- **Bulk Re-extraction** - Re-process all existing documents with updated prompts when the extraction logic improves
