"""Gmail OAuth Setup Script for Windows
Run this to generate a fresh token.json
"""
import json
import os
import sys

# Add backend to path for dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    credentials_file = os.path.join(project_root, "credentials.json")
    token_file = os.path.join(project_root, "backend", "data", "token.json")

    # Ensure data directory exists
    os.makedirs(os.path.dirname(token_file), exist_ok=True)

    if not os.path.exists(credentials_file):
        print(f"ERROR: credentials.json not found at {credentials_file}")
        print("\nTo obtain credentials.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable the Gmail API")
        print("4. Go to Credentials > Create Credentials > OAuth client ID")
        print("5. Select 'Desktop application'")
        print("6. Download the JSON file and save as credentials.json")
        sys.exit(1)

    print("=== Gmail OAuth Setup ===\n")
    print("A browser window will open. Please sign in and grant permissions.\n")

    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save as JSON
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }

    with open(token_file, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)

    print(f"\nToken saved to {token_file}")
    print("OAuth setup complete!")
    print("\nYou can now use the application.")

if __name__ == "__main__":
    main()
