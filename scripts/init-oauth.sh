#!/bin/bash
# Gmail OAuth Setup Script
# Run this ONCE on the host machine before Docker deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/backend/data"
TOKEN_FILE="$DATA_DIR/token.json"
CREDENTIALS_FILE="$PROJECT_ROOT/credentials.json"

echo "=== Gmail OAuth Setup ==="
echo ""

# Check for credentials.json
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "ERROR: credentials.json not found at $CREDENTIALS_FILE"
    echo ""
    echo "To obtain credentials.json:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a new project or select existing"
    echo "3. Enable the Gmail API"
    echo "4. Go to Credentials > Create Credentials > OAuth client ID"
    echo "5. Select 'Desktop application'"
    echo "6. Download the JSON file and save as credentials.json"
    exit 1
fi

# Create data directory if needed
mkdir -p "$DATA_DIR"

# Check if token already exists
if [ -f "$TOKEN_FILE" ]; then
    echo "Token file already exists at $TOKEN_FILE"
    read -p "Do you want to regenerate it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing token."
        exit 0
    fi
    rm "$TOKEN_FILE"
fi

# Create temporary Python script for OAuth
OAUTH_SCRIPT=$(mktemp)
cat > "$OAUTH_SCRIPT" << 'PYTHON_SCRIPT'
import json
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    credentials_file = sys.argv[1]
    token_file = sys.argv[2]

    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save as JSON (not pickle) for better portability
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }

    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\nToken saved to {token_file}")
    print("OAuth setup complete!")

if __name__ == "__main__":
    main()
PYTHON_SCRIPT

echo "Starting OAuth flow..."
echo "A browser window will open. Please sign in and grant permissions."
echo ""

# Check if required Python packages are installed
python3 -c "from google_auth_oauthlib.flow import InstalledAppFlow" 2>/dev/null || {
    echo "Installing required Python packages..."
    pip3 install google-auth-oauthlib google-auth
}

# Run the OAuth script
python3 "$OAUTH_SCRIPT" "$CREDENTIALS_FILE" "$TOKEN_FILE"

# Cleanup
rm "$OAUTH_SCRIPT"

echo ""
echo "=== Setup Complete ==="
echo "Token saved to: $TOKEN_FILE"
echo "You can now run 'docker compose up -d' to start the application."
