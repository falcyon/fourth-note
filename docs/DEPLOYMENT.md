# Fourth Note - Deployment Guide

**Version 1.0.0**

This guide covers two deployment scenarios:
- [Local Development (Windows 11)](#local-development-windows-11-without-docker) - For testing without Docker
- [Production (Ubuntu NUC)](#production-deployment-ubuntu-2404-with-docker) - Docker-based deployment

---

# Local Development (Windows 11 without Docker)

## Prerequisites

### Software Requirements
- **Python 3.11+**: Download from [python.org](https://www.python.org/downloads/)
- **Node.js 20+**: Download from [nodejs.org](https://nodejs.org/)
- **PostgreSQL 16**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- **Tesseract OCR**: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- **Git**: Download from [git-scm.com](https://git-scm.com/download/win)

### Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Gmail API**
4. Enable the **Generative Language API** (Gemini)
5. Create OAuth credentials (Desktop application) → Download as `credentials.json`
6. Create an API key for Gemini → Note the key

## Folder Structure (Windows)

```
C:\Projects\fourth-note\           # Git repo
├── backend\
│   ├── data\                      # Local data directory
│   │   ├── emails\                # Downloaded PDFs
│   │   └── token.json             # OAuth token
│   └── .env                       # Backend environment
├── frontend\
├── credentials.json               # Google OAuth credentials
└── .env.example
```

## Step-by-Step Setup

### 1. Clone Repository

```powershell
cd C:\Projects
git clone https://github.com/USERNAME/fourth-note.git
cd fourth-note
```

### 2. Install Tesseract OCR

1. Download installer from [UB Mannheim releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run installer (default path: `C:\Program Files\Tesseract-OCR`)
3. Add to PATH:
   - Open System Properties → Environment Variables
   - Add `C:\Program Files\Tesseract-OCR` to Path

Verify installation:
```powershell
tesseract --version
```

### 3. Setup PostgreSQL

1. Install PostgreSQL 16 with pgAdmin
2. During install, set a password for the `postgres` user
3. Open pgAdmin or psql and create database:

```sql
CREATE DATABASE pitchdeck;
CREATE USER pitchdeck WITH PASSWORD 'your_local_password';
GRANT ALL PRIVILEGES ON DATABASE pitchdeck TO pitchdeck;
ALTER DATABASE pitchdeck OWNER TO pitchdeck;
```

### 4. Setup Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir data\emails
mkdir data\markdown
```

Create `backend\.env`:
```env
# Database (local PostgreSQL)
DATABASE_URL=postgresql://pitchdeck:your_local_password@localhost:5432/pitchdeck

# Google APIs
GOOGLE_API_KEY=your_gemini_api_key

# Paths (Windows local)
DATA_DIR=./data
TOKEN_FILE=./data/token.json
CREDENTIALS_FILE=../credentials.json

# Gmail Configuration
GMAIL_QUERY_SINCE=1735689600

# Scheduler (set to 0 to disable for local dev)
SCHEDULER_INTERVAL_HOURS=0
```

### 5. Gmail OAuth Setup

Place `credentials.json` in project root, then:

```powershell
# From project root with backend venv activated
cd ..
python scripts/init-oauth.py
```

This opens a browser for Google sign-in. After authorization, `token.json` is saved to `backend\data\token.json`.

### 6. Run Database Migrations

```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

### 7. Setup Frontend

```powershell
cd ..\frontend

# Install dependencies
npm install
```

### 8. Start Development Servers

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

### 9. Access Application

- **Frontend**: http://localhost:5173 (Vite dev server with hot reload)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

The Vite dev server proxies `/api` requests to the backend automatically.

## Local Development Commands

| Action | Command |
|--------|---------|
| Start backend | `cd backend && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload` |
| Start frontend | `cd frontend && npm run dev` |
| Run migrations | `cd backend && alembic upgrade head` |
| Create migration | `cd backend && alembic revision --autogenerate -m "description"` |
| Refresh OAuth | `python scripts/init-oauth.py` |

---

# Production Deployment (Ubuntu 24.04 with Docker)

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
- Ubuntu 24.04 LTS
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
sudo mkdir -p /mnt/WD1/fourth-note/data/emails
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

**Important**: This step must be done on the NUC directly (not via SSH) as it requires a web browser.

```bash
# Ubuntu 24.04 requires a virtual environment for pip packages
python3 -m venv ~/oauth-venv
source ~/oauth-venv/bin/activate

# Install dependency and run OAuth setup
pip install google-auth-oauthlib
python scripts/init-oauth.py

# Deactivate venv when done
deactivate
```

This will:
1. Open a browser window
2. Prompt you to sign in to Google
3. Request permission to read Gmail
4. Save credentials to `backend/data/token.json`

Copy token to project root for Docker:
```bash
cp backend/data/token.json ./token.json
```

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

1. Open browser to `http://<NUC-IP>:4444/`
2. Dashboard should load
3. Click "Fetch Emails" to trigger initial sync
4. Check `http://<NUC-IP>:4444/api/v1/status` for health status
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

# Re-run OAuth setup (requires browser access)
source ~/oauth-venv/bin/activate
python scripts/init-oauth.py
deactivate

# Copy new token and restart
cp backend/data/token.json ./token.json
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

- System status: `http://<NUC-IP>:4444/api/v1/status`
- Scheduler status: `http://<NUC-IP>:4444/api/v1/scheduler/status`
- OAuth status: `http://<NUC-IP>:4444/api/v1/oauth/status`

---

## Exposing via Cloudflare Tunnel + Nginx

To access Fourth Note via a subdomain (e.g., `fourthwall.leff.in`), configure nginx as a reverse proxy and add the hostname to your Cloudflare tunnel.

### 1. Setup Nginx Site Config

Copy the provided nginx config:

```bash
sudo cp ~/fourth-note/deploy/fourthwall.leff.in /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/fourthwall.leff.in /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Or create manually at `/etc/nginx/sites-available/fourthwall.leff.in`:

```nginx
server {
    listen 80;
    server_name fourthwall.leff.in;

    # Security headers
    add_header X-Content-Type-Options "nosniff";
    add_header X-Frame-Options "SAMEORIGIN";

    # Main traffic - proxy to Fourth Note frontend
    location / {
        proxy_pass http://127.0.0.1:4444;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long-running API requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
    }
}
```

### 2. Create a New Cloudflare Tunnel

Create a dedicated tunnel for Fourth Note:

```bash
# Login to Cloudflare (if not already)
cloudflared tunnel login

# Create new tunnel
cloudflared tunnel create fourthwall-tunnel

# Note the tunnel ID from output (e.g., abc12345-6789-...)
```

### 3. Create Tunnel Config

Create `/etc/cloudflared/fourthwall-tunnel.yml`:

```yaml
tunnel: <your-new-tunnel-id>
credentials-file: /home/falcyon/.cloudflared/<your-new-tunnel-id>.json

ingress:
  - hostname: fourthwall.leff.in
    service: http://127.0.0.1:80
  - service: http_status:404
```

### 4. Create Systemd Service

Create `/etc/systemd/system/cloudflared-fourthwall.service`:

```ini
[Unit]
Description=Cloudflare Tunnel for Fourth Note
After=network.target

[Service]
Type=simple
User=falcyon
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/fourthwall-tunnel.yml run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared-fourthwall
sudo systemctl start cloudflared-fourthwall
```

### 5. Add DNS Record in Cloudflare

```bash
# Route DNS to tunnel
cloudflared tunnel route dns fourthwall-tunnel fourthwall.leff.in
```

Or manually in Cloudflare Dashboard → DNS:
- **Type:** CNAME
- **Name:** `fourthwall`
- **Target:** `<your-new-tunnel-id>.cfargotunnel.com`
- **Proxy status:** Proxied (orange cloud)

### 6. Verify

1. Check tunnel status: `sudo systemctl status cloudflared-fourthwall`
2. Visit `https://fourthwall.leff.in`
3. Dashboard should load with HTTPS (Cloudflare handles SSL)
