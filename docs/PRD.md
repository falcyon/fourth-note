# Fourth Note - Product Requirements Document

This document tracks all features, their requirements, and the versions they were introduced in. It serves as a combined Confluence/Jira-style tracker for the project.

---

## 1. Agentic Engine (completed in v1.0)

The AI-powered extraction engine that processes documents and extracts structured investment data. Currently uses a single Gemini API call, with plans to evolve into a multi-agent architecture.

### 1.1 AI-Powered Data Extraction (completed in v1.0)

Send markdown content to Google Gemini API to extract structured investment data. Returns JSON with key investment fields.

#### 1.1.1 Extracted Fields

- Investment Name
- Firm
- Strategy Description
- Leaders
- Management Fees
- Incentive Fees
- Liquidity/Lock
- Target Returns

#### 1.1.2 Leaders Separator Update (v1.1)

Changed from comma to pipe (`|`) for multi-value support.

#### 1.1.3 VARCHAR to TEXT Migration (v1.1)

Changed investment fields from VARCHAR(255) to TEXT to handle longer extracted values.

### 1.2 Multi-Agent Architecture (planned for v2.0)

Multiple specialized AI agents for different processing tasks instead of a single extraction prompt.

#### 1.2.1 Relevance Agent

Filters irrelevant documents before processing.

#### 1.2.2 Extraction Agent

Structured data extraction from documents.

#### 1.2.3 Validation Agent

Quality checks on extracted data.

---

## 2. Email-based Document Ingestion (completed in v1.0)

The core pipeline that fetches emails from Gmail, extracts PDF attachments, and processes them for investment data extraction.

### 2.1 Gmail API Integration (completed in v1.0)

Connect to Gmail via OAuth2 to fetch emails containing investment-related attachments.

#### 2.1.1 OAuth2 Authentication

Uses `gmail.readonly` scope with automatic token refresh.

#### 2.1.2 Date Filter

Configurable via `GMAIL_QUERY_SINCE` environment variable (Unix timestamp).

#### 2.1.3 Attachment Detection

Identifies and downloads PDF attachments from emails.

### 2.2 PDF to Markdown Conversion (completed in v1.0)

Convert PDF documents to markdown text for AI processing.

#### 2.2.1 Tesseract OCR

Extract text from scanned/image-based PDFs using Tesseract.

#### 2.2.2 Direct Text Extraction

Extract text directly from digital PDFs without OCR.

#### 2.2.3 Page-by-Page Processing

Convert each page to image, then OCR, for reliable extraction.

#### 2.2.4 Markdown File Preservation (v1.1)

Save markdown files alongside PDFs for reference.

### 2.3 Database Storage (completed in v1.0)

Store extracted data in PostgreSQL with full CRUD support.

#### 2.3.1 Email Metadata Table

Stores fetched email information (subject, sender, date).

#### 2.3.2 Documents Table

Stores PDF documents and processing status.

#### 2.3.3 Investments Table

Stores extracted investment data with field attribution.

#### 2.3.4 Users Table (v1.1)

Added for multi-tenant support with Gmail OAuth tokens.

#### 2.3.5 User ID Foreign Keys (v1.1)

All tables have `user_id` column for data isolation.

#### 2.3.6 Investment-Centric Redesign (v1.1)

Redesigned schema with field attribution tracking.

### 2.4 Manual Email Fetch (completed in v1.0)

UI button to trigger email processing on demand.

#### 2.4.1 SSE Progress Streaming

Real-time progress tracking via Server-Sent Events.

#### 2.4.2 Step-by-Step Updates

Shows each step: fetching emails, downloading attachments, OCR progress, AI extraction.

### 2.5 Background Scheduler (completed in v1.0)

APScheduler-based background job for automatic email fetching.

#### 2.5.1 Configurable Interval

Set via `SCHEDULER_INTERVAL_HOURS` (default: 6 hours prod, 0 dev).

#### 2.5.2 Graceful Shutdown

Proper cleanup on application shutdown.

### 2.6 Smart Document Filtering (planned for v2.0)

Automatically filter out irrelevant PDF attachments before processing.

#### 2.6.1 Metadata Check

Check attachment filename and email body/subject for relevance signals.

#### 2.6.2 Content Scan

Scan PDF content if metadata is unclear.

#### 2.6.3 Skip Irrelevant

Automatically skip non-investment PDFs.

### 2.7 Multi-Format Support (planned for v2.0)

Support additional document formats beyond PDF.

#### 2.7.1 PowerPoint Support

Process PPT/PPTX files using markitdown library.

#### 2.7.2 Word Document Support

Process DOC/DOCX files using markitdown library.

---

## 3. Web Dashboard (completed in v1.0)

React-based frontend for viewing and managing investment data.

### 3.1 Investment List View (completed in v1.0)

Main dashboard showing all investments in a sortable, searchable table.

#### 3.1.1 Full-Text Search

Search across all investment fields.

#### 3.1.2 Column Sorting

Click column headers to sort ascending/descending.

#### 3.1.3 Pagination

Navigate large datasets with page controls.

#### 3.1.4 Dark Theme (v1.1)

Modern dark color scheme with card-based layout.

#### 3.1.5 Dashboard Table Improvements (planned for v1.2)

Display all extracted JSON attributes in the table and remove source/extracted date columns.

### 3.2 Investment Detail View (completed in v1.0)

Detailed view of a single investment showing all extracted fields.

#### 3.2.1 Field Display

Shows all extracted investment fields with values.

#### 3.2.2 Field Attribution (v1.1)

Shows source for each extracted value.

### 3.3 Document Management (completed in v1.1)

View and download documents associated with investments.

#### 3.3.1 Document List

Investment detail page shows associated documents with relationship type.

#### 3.3.2 PDF Download

Download original PDF files.

#### 3.3.3 Markdown Download

Download extracted markdown files.

#### 3.3.4 In-Browser Markdown Preview (planned for v2.0)

View markdown content in browser modal.

#### 3.3.5 In-Browser PDF Viewer (planned for v2.0)

View PDFs directly in browser.

### 3.4 Source Attribution (planned for v2.0)

Show where each extracted value came from in the source document.

#### 3.4.1 Hover Context Window

On hover over any field, show surrounding text from source document.

### 3.5 CSV Export (completed in v1.0)

Export all investments to CSV file for spreadsheet analysis.

### 3.6 Settings Page (completed in v1.0)

System status, scheduler info, and configuration display.

#### 3.6.1 System Status

Shows database and Gmail connection status.

#### 3.6.2 Scheduler Status

Shows next run time and last run result.

#### 3.6.3 Database Stats

Shows counts of emails, documents, investments.

#### 3.6.4 Gmail Connection UI (v1.1)

Connect/disconnect buttons for Gmail OAuth.

### 3.7 Progress Panel (completed in v1.0)

Dashboard panel displaying processing status during email fetch.

#### 3.7.1 Status Indicators

Success/error indicators for each processing step.

#### 3.7.2 Auto-Scroll (planned for v1.2)

Automatically scroll to show latest entry.

#### 3.7.3 Compact OCR Logs (planned for v1.2)

Show "(4/40)" instead of multiple log lines per page.

### 3.8 UI Redesign from Figma (planned for v2.0)

Replace current Claude Code-generated UI with professional design from Figma mockups. Current UI is functional with readability improvements but lacks polished visual design.

---

## 4. User Authentication & Multi-Tenancy (completed in v1.1)

Secure user authentication via Google OAuth2 Sign-In with JWT session management and per-user data isolation.

### 4.1 Google Sign-In (completed in v1.1)

Frontend Google Sign-In button that returns ID token.

#### 4.1.1 ID Token Verification

Backend verifies Google ID token authenticity.

#### 4.1.2 User Creation

Creates user record on first login.

### 4.2 JWT Session Tokens (completed in v1.1)

Backend issues JWT tokens for authenticated sessions.

#### 4.2.1 Token Generation

JWT created with user ID and expiration.

#### 4.2.2 LocalStorage Persistence

Tokens stored in browser localStorage.

### 4.3 Protected Routes (completed in v1.1)

Frontend route guards for authenticated pages.

#### 4.3.1 Redirect to Login

Unauthenticated users redirected to login page.

#### 4.3.2 Auto-Logout on 401

API client clears auth and redirects on 401 responses.

### 4.4 Multi-Tenant Data Isolation (completed in v1.1)

Each user can only access their own data.

#### 4.4.1 Query Filtering

All API queries filter by authenticated user's ID.

#### 4.4.2 Data Ownership

All records linked to creating user.

### 4.5 Per-User Gmail Connection (completed in v1.1)

Each user connects their own Gmail account.

#### 4.5.1 Gmail OAuth Flow

Settings page initiates OAuth with `gmail.readonly` scope.

#### 4.5.2 Token Storage

Gmail tokens stored per-user in database.

#### 4.5.3 Token Auto-Refresh

Expired tokens automatically refreshed.

#### 4.5.4 Connect/Disconnect UI

Settings page shows status with action buttons.

### 4.6 Demo Mode (completed in v1.1)

Automatic login for demo/showcase purposes.

#### 4.6.1 Auto-Login Attempt

App attempts login as `fourthnotetest@gmail.com` on load.

#### 4.6.2 Fallback to Google Sign-In

Shows Google Sign-In button if demo user doesn't exist.

#### 4.6.3 Demo Landing Page (v1.1.2)

Hero banner with app description only shows for demo users, hidden for authenticated users.

#### 4.6.4 Separate Dashboard View (v1.1.2)

Dashboard shows "Demo Investments" for demo users, "My Investments" for authenticated users.

#### 4.6.5 User Logout (v1.1.2)

Logout button in user dropdown (only for authenticated users). Returns to demo landing page.

---

## Future Features

- **Competitor/Fund Tracking** - Track similar or competing funds using vector embeddings
- **Semantic Search** - pgvector-based semantic search across all documents
- **Email Notifications** - Alerts on extraction errors or new investments
- **Bulk Re-extraction** - Re-process all documents with updated prompts
