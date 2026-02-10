# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Multi-agent architecture for email processing (TriageAgent, ExtractionAgent, LinkedInAgent)
- EmailOrchestrator to coordinate agent pipeline with graceful error handling
- Dark mode support for Settings page (consistency with other pages)
- Centralized localStorage constants in `frontend/src/constants.ts`
- ThemeContext for dark/light theme management

### Changed
- Email processing now uses agent-based architecture instead of monolithic service
- Emails are now processed one-by-one for cleaner fallback on errors

### Removed
- Deprecated `extraction_service.py` (replaced by ExtractionAgent)

## [1.1.2] - 2026-01-26

### Added
- Demo landing page with hero banner (only shown for demo users)
- User logout button in dropdown (for authenticated users only)
- "Demo" badge in user dropdown when viewing demo account

### Changed
- Dashboard shows "My Investments" for real users, "Demo Investments" for demo

### Fixed
- Sign in with Google button now correctly navigates to login page

## [1.1.1] - 2026-01-26

### Added
- Deploy script (`scripts/deploy.sh`) for quick Ubuntu deployment

### Changed
- Leaders column width increased from 140px to 200px
- Leaders content limited to 3 lines with truncation

## [1.1.0] - 2026-01-22

### Added
- Per-user Gmail OAuth connection
- Multi-tenant data isolation (user_id foreign keys)
- Dark theme with card-based layout
- Document management (PDF/markdown download)
- Gmail connection UI in Settings

### Changed
- Leaders separator from comma to pipe (`|`)
- Investment fields from VARCHAR(255) to TEXT
- Investment-centric database schema redesign

## [1.0.0] - 2026-01-15

### Added
- Initial release
- Gmail API integration with OAuth2
- PDF to markdown conversion (Tesseract OCR)
- Gemini AI data extraction
- Investment list with search/sort/pagination
- Investment detail view
- CSV export
- Background scheduler for auto-fetch
- Google Sign-In authentication
