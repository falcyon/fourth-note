# Fourth Note - Deployment Guide

**Version 1.0.0**

## Folder Structure

**Ubuntu NUC layout:**
```
~/fourth-note/                    # Git repo (code + config)
├── docker-compose.yml
├── .env                          # Secrets (not in git)
├── token.json                    # OAuth token (not in git)
├── credentials.json              # Google Cloud credentials (not in git)
├── backend/
└── frontend/

/mnt/WD1/fourth-note/             # Data on external drive
├── postgres/                     # Database files
└── data/
    └── emails/                   # Downloaded PDFs
```

## Prerequisites

### System Requirements
- Ubuntu 22.04 LTS or newer
- Minimum 4GB RAM
- External drive mounted at `/mnt/WD1`
- Internet access for Gmail API and Gemini API

### Software Requirements
- Docker Engine 24.0+
- Docker Compose v2.0+
- Git
- Python 3 (for OAuth setup)

## Initial Setup (One-Time)

### 1. Install Docker

```bash
# Update package index
sudo apt update

# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone Repository

```bash
cd ~
git clone https://github.com/USERNAME/fourth-note.git
cd fourth-note
```

### 3. Create Data Directories on External Drive

```bash
sudo mkdir -p /mnt/WD1/fourth-note/postgres
sudo mkdir -p /mnt/WD1/fourth-note/data
sudo chown -R $USER:$USER /mnt/WD1/fourth-note
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

Required environment variables:
- `GOOGLE_API_KEY`: Your Gemini API key
- `POSTGRES_PASSWORD`: Strong password for database

### 5. Setup Google Cloud Credentials

1. Download `credentials.json` from Google Cloud Console
2. Place in `~/fourth-note/credentials.json`

### 6. Gmail OAuth Setup

**Important**: This step must be done on the mini PC directly (not via SSH) as it requires a web browser.

```bash
python3 scripts/init-oauth.py
```

This will:
1. Open a browser window
2. Prompt you to sign in to Google
3. Request permission to read Gmail
4. Save credentials to `token.json` in the current directory

### 7. Start Services

```bash
# Build and start all containers
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 8. Verify Installation

1. Open browser to `http://<NUC-IP>/`
2. Dashboard should load
3. Click "Fetch Emails" to trigger initial sync
4. Check `http://<NUC-IP>/api/v1/status` for health status
5. Verify PDFs are saved to `/mnt/WD1/fourth-note/data/emails/`

## Updating Code

```bash
cd ~/fourth-note
git pull
docker compose build
docker compose up -d
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `pitchdeck` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `POSTGRES_DB` | Database name | `pitchdeck` |
| `GOOGLE_API_KEY` | Gemini API key | `AIza...` |
| `GMAIL_QUERY_SINCE` | Unix timestamp to fetch emails from | `1704067200` |
| `SCHEDULER_INTERVAL_HOURS` | Hours between email checks | `6` |

## Backup Procedures

### Database Backup

```bash
# Create backup
docker compose exec postgres pg_dump -U pitchdeck pitchdeck > backup_$(date +%Y%m%d).sql

# Restore backup
docker compose exec -T postgres psql -U pitchdeck pitchdeck < backup_20240101.sql
```

### Full Data Backup

```bash
# Stop services
docker compose down

# Backup external drive data
sudo tar -czvf fourth_note_backup_$(date +%Y%m%d).tar.gz /mnt/WD1/fourth-note

# Restart services
docker compose up -d
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs backend
docker compose logs postgres

# Common issues:
# - Missing .env file
# - Invalid GOOGLE_API_KEY
# - Port already in use
# - Missing credentials.json or token.json
```

### OAuth Token Expired

If you see "Token has been revoked" errors:

```bash
# Remove old token
rm token.json

# Re-run OAuth setup
python3 scripts/init-oauth.py

# Restart backend
docker compose restart backend
```

### Database Connection Failed

```bash
# Check if postgres is running
docker compose ps postgres

# Check postgres logs
docker compose logs postgres

# Verify environment variables
docker compose config | grep POSTGRES
```

### Email Fetch Not Working

1. Check OAuth status: `curl http://localhost:8000/api/v1/oauth/status`
2. Verify token.json exists: `ls -la token.json`
3. Check Gmail API quotas in Google Cloud Console
4. Review backend logs: `docker compose logs backend | grep -i gmail`

### OCR Quality Issues

If extracted text is poor quality:

1. Ensure Tesseract is installed in container
2. Check PDF quality (scanned vs native)
3. Consider adding language packs for non-English documents

## Quick Reference

| Action | Commands |
|--------|----------|
| Deploy changes | `git pull && docker compose build && docker compose up -d` |
| View logs | `docker compose logs -f` |
| Restart services | `docker compose restart` |
| Stop everything | `docker compose down` |
| Full rebuild | `docker compose down && docker compose build --no-cache && docker compose up -d` |

### Database Migrations

If your update includes database schema changes:

```bash
# After pulling and rebuilding
docker compose exec backend alembic upgrade head
```

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

### Check Resource Usage

```bash
docker stats
```

### Health Endpoints

- System status: `http://<NUC-IP>/api/v1/status`
- Scheduler status: `http://<NUC-IP>/api/v1/scheduler/status`
- OAuth status: `http://<NUC-IP>/api/v1/oauth/status`
