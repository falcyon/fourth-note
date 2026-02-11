# Fourth Note

**Automated Investment Intelligence from All Your Sources**

---

## The Problem

Investment professionals spend too much time maintaining their data.

### The Pain Points

**1. Manual Data Entry Never Ends**
Every quarter, you receive dozens of emails from fund managers. Each contains critical data buried in PDF attachments, PowerPoint decks, and Word documents: NAV updates, fee structures, strategy pivots, leadership changes, capital calls, distribution notices.

You manually open each attachment, scan through pages of content, and copy numbers into your tracking spreadsheet. Repeat for every email, every fund, every quarter.

**2. Your Tracker Is Always Out of Date**
You may already have a single source of truth - maybe a master spreadsheet, maybe a CRM, maybe a shared drive. But keeping it current & updated is a full-time job. By the time you finish updating Q3 data, Q4 updates are already piling up in your inbox.

**3. Information Scattered Across Formats**
Investment insights live everywhere: email attachments, call transcripts, meeting notes, physical notebooks, Excel files, markdown docs. When you need to compare funds or recall a key detail, you're digging through multiple sources trying to piece together the full picture.

**4. Scanned Documents You Can't Search**
Many PDFs are scanned images, not searchable text. That one metric you need? It's in a document you can't even Ctrl+F.

**5. Analysis Takes a Backseat**
Hours spent on data maintenance are hours not spent on analysis, due diligence, manager relationships, or finding the next great investment. Your most valuable resource - attention - is consumed by administrative work.

---

## The Solution

**Fourth Note connects to your data sources and maintains your investment records automatically.**

We pull from your emails, investor calls, meeting transcriptions, and other communication channels. We extract attachments, convert them to searchable text (even scanned documents), and use AI to structure the data.

The result: a unified, always-current view of all your investments - maintained for you, not by you.


### The Process

1. **Connect Your Sources** - Email, call transcripts, meeting notes. One-click OAuth where available.

2. **Automatic Syncing** - New content is detected and processed automatically. No manual uploads.

3. **Smart Filtering** - Our AI identifies investment-related content and skips irrelevant material (signatures, disclaimers, marketing).

4. **Document Conversion** - Attachments are converted to searchable text. Scanned documents go through OCR. Nothing is lost.

5. **AI Extraction** - Our multi-agent system extracts structured data from unstructured content. Every field links back to its source for verification.

6. **Unified Dashboard** - All your investments in one place. Search, sort, filter, export.

### Your Data, Your Way

We don't lock you in. All extracted data is downloadable:
- **CSV export** for spreadsheet analysis
- **Markdown files** of every processed document

You can either integrate our process to your existing workflow, or choose to use our UI with all of its capabilities.
And if you ever want to leave, your data comes with you.

---

## What's Available Now (v1.2)

This release focuses on **email and attachments** - the highest-volume source for most investment professionals.

### Data We Extract

| Field | What It Captures | Example |
|-------|------------------|---------|
| **Investment Name** | Fund or vehicle name | "Sequoia Capital Fund XVI" |
| **Firm** | Management company | "Sequoia Capital" |
| **Strategy** | Investment approach and thesis | "Early-stage technology investments in consumer and enterprise software" |
| **Leadership** | Key people and roles | "Roelof Botha (Managing Partner), Alfred Lin (Partner)" |
| **Management Fees** | Annual management fee | "2.0% of committed capital" |
| **Incentive Fees** | Carried interest / performance fees | "20% over 8% preferred return" |
| **Liquidity Terms** | Lock-up and redemption terms | "10-year fund life, no interim redemptions" |
| **Target Returns** | Expected performance metrics | "3x net MOIC, 25% gross IRR" |

Every extracted value links back to its source document. Click any field to see where it came from.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Gmail Integration** | OAuth connection with automatic email fetching |
| **PDF Processing** | Automatic extraction with OCR for scanned documents |
| **Smart Document Filtering** | AI identifies investment-related content and skips irrelevant attachments |
| **Multi-Agent AI Pipeline** | Triage agent classifies emails, extraction agent pulls structured data |
| **Investment Dashboard** | Searchable list view with sorting, pagination, and source attribution |
| **Investment Detail View** | Complete view of extracted data with linked source documents |
| **Document Access** | Download original files or extracted markdown |
| **CSV Export** | One-click export of all investment data |

---

## What's Coming

### Additional Data Sources

| Source | Status |
|--------|--------|
| **Email + PDF attachments** | Available now |
| **PowerPoint (PPT/PPTX)** | In development |
| **Word (DOC/DOCX)** | In development |
| **Excel (XLS/XLSX)** | Planned |
| **Investor call transcripts** | Planned |
| **Meeting notes** | Planned |

### Intelligent Analysis

| Feature | Description |
|---------|-------------|
| **Fund Similarity** | Automatically identify funds with similar strategies, sectors, or structures - without digging through your notes |
| **Natural Language Search** | Natural language queries across all your data ("Which funds increased fees this year?", "Show me all healthcare-focused strategies") |