"""Gmail API service with OAuth token management."""
import json
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

from app.config import get_settings

settings = get_settings()
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Type alias for token refresh callback
TokenSaveCallback = Callable[[Dict[str, Any]], None]


class GmailService:
    """Service for interacting with Gmail API."""

    def __init__(
        self,
        token_json: Optional[Dict[str, Any]] = None,
        on_token_refresh: Optional[TokenSaveCallback] = None,
    ):
        """Initialize Gmail service.

        Args:
            token_json: Optional per-user token data. If None, uses global token file.
            on_token_refresh: Optional callback to save refreshed tokens (for per-user tokens).
        """
        self._service: Optional[Resource] = None
        self._credentials: Optional[Credentials] = None
        self._token_json = token_json  # Per-user token data
        self._on_token_refresh = on_token_refresh  # Callback for saving refreshed tokens

    def _load_credentials(self) -> Optional[Credentials]:
        """Load credentials from per-user token or file."""
        # If per-user token provided, use it
        if self._token_json:
            token_data = self._token_json
        else:
            # Fall back to global token file
            token_path = settings.token_path
            if not token_path.exists():
                return None
            token_data = json.loads(token_path.read_text(encoding="utf-8"))

        return Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes", SCOPES),
        )

    def _save_credentials(self, creds: Credentials) -> None:
        """Save refreshed credentials back to storage.

        Uses the on_token_refresh callback if provided (for per-user tokens),
        otherwise saves to the global token file.
        """
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }

        # If we have a callback for per-user tokens, use it
        if self._on_token_refresh:
            self._on_token_refresh(token_data)
        else:
            # Fall back to global token file
            token_path = settings.token_path
            token_path.write_text(json.dumps(token_data, indent=2), encoding="utf-8")

    def get_service(self) -> Resource:
        """Get authenticated Gmail service, refreshing token if needed."""
        if self._service is not None and self._credentials and self._credentials.valid:
            return self._service

        self._credentials = self._load_credentials()

        if not self._credentials:
            raise RuntimeError(
                "No OAuth token found. Run 'python scripts/init-oauth.py' first."
            )

        if not self._credentials.valid:
            if self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
                self._save_credentials(self._credentials)
            else:
                raise RuntimeError(
                    "OAuth token is invalid and cannot be refreshed. "
                    "Run 'python scripts/init-oauth.py' again."
                )

        self._service = build("gmail", "v1", credentials=self._credentials)
        return self._service

    def is_authenticated(self) -> bool:
        """Check if Gmail service is properly authenticated."""
        try:
            service = self.get_service()
            service.users().getProfile(userId="me").execute()
            return True
        except Exception:
            return False

    def get_auth_status(self) -> Dict[str, Any]:
        """Get detailed authentication status."""
        token_path = settings.token_path
        token_exists = token_path.exists()

        if not token_exists:
            return {
                "authenticated": False,
                "token_exists": False,
                "message": "No token file found. Run 'python scripts/init-oauth.py' to authenticate.",
            }

        try:
            creds = self._load_credentials()
            if not creds:
                return {
                    "authenticated": False,
                    "token_exists": True,
                    "message": "Token file exists but could not load credentials.",
                }

            is_valid = self.is_authenticated()
            return {
                "authenticated": is_valid,
                "token_exists": True,
                "token_expired": creds.expired if creds else None,
                "message": "Connected to Gmail" if is_valid else "Token invalid or expired",
            }
        except Exception as e:
            return {
                "authenticated": False,
                "token_exists": True,
                "error": str(e),
                "message": f"Error checking authentication: {e}",
            }

    def list_messages(
        self,
        query: Optional[str] = None,
        max_results: int = 100,
    ) -> List[Dict[str, str]]:
        """List messages matching the query."""
        service = self.get_service()

        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()

        return results.get("messages", [])

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get full message details."""
        service = self.get_service()

        return service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()

    def get_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download an attachment."""
        import base64

        service = self.get_service()

        attachment = service.users().messages().attachments().get(
            userId="me",
            messageId=message_id,
            id=attachment_id,
        ).execute()

        return base64.urlsafe_b64decode(attachment["data"])


# Singleton instance for global token
_gmail_service: Optional[GmailService] = None


def get_gmail_service(
    token_json: Optional[Dict[str, Any]] = None,
    on_token_refresh: Optional[TokenSaveCallback] = None,
) -> GmailService:
    """Get Gmail service instance.

    Args:
        token_json: Optional per-user token. If provided, creates a new instance.
                   If None, returns singleton with global token file.
        on_token_refresh: Optional callback to save refreshed tokens. Only used
                         when token_json is provided (per-user mode).
    """
    global _gmail_service

    # If per-user token provided, return new instance (not cached)
    if token_json:
        return GmailService(token_json=token_json, on_token_refresh=on_token_refresh)

    # Otherwise use singleton for global token
    if _gmail_service is None:
        _gmail_service = GmailService()
    return _gmail_service
