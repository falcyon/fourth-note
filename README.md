# Fourth Note

**Version 1.0.0**

An intelligent system that automatically extracts investment data from pitch deck PDFs received via email.

## What It Does

1. **Monitors Gmail** - Automatically checks for new emails with PDF attachments every 6 hours
2. **Processes PDFs** - Converts pitch deck PDFs to text using OCR technology
3. **Extracts Data** - Uses AI (Google Gemini) to identify and extract 8 key investment fields:
   - Investment Name
   - Firm
   - Strategy Description
   - Leaders/PM/CEO
   - Management Fees
   - Incentive Fees
   - Liquidity/Lock
   - Target Net Returns
4. **Stores Results** - Saves extracted data to a searchable PostgreSQL database
5. **Provides Dashboard** - Web interface to view, search, edit, and export data

## Accessing the Dashboard

Once deployed, access the dashboard at: `http://<server-ip>/`

### Dashboard Features

- **View All Investments** - Searchable, sortable table of all extracted investments
- **Investment Details** - Click any row to see full details and source document
- **Manual Fetch** - Click "Fetch Emails" button to trigger immediate email check with real-time progress
- **Export Data** - Download all data as CSV for use in spreadsheets
- **System Status** - View Gmail connection, scheduler status, and database stats

## Manual Email Fetch

If you don't want to wait for the scheduled 6-hour interval:

1. Open the dashboard
2. Click the "Fetch Emails" button
3. Watch real-time progress as it processes
4. New investments will appear in the table

## Exporting Data

1. Go to the Settings page
2. Click "Export to CSV"
3. Open in Excel or Google Sheets

## Deployment

See `docs/DEPLOYMENT.md` for full deployment instructions on Ubuntu/Docker.

## Support

For technical issues, check the [deployment guide](docs/DEPLOYMENT.md) for troubleshooting.
