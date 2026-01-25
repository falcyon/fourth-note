"""Application configuration."""
import os
import sys
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

# Force UTF-8 encoding on Windows (do this once, early)
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://pitchdeck:pitchdeck@localhost:5432/pitchdeck"

    # Google APIs
    google_api_key: str = ""

    # Gmail Configuration
    gmail_query_since: int = 1735689600  # Jan 1, 2025 UTC

    # Scheduler
    scheduler_interval_hours: int = 6

    # Paths - defaults for Docker, override via env for local dev
    data_dir: str = "/app/data"
    token_file: str = "/app/data/token.json"
    credentials_file: str = "/app/credentials.json"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def data_path(self) -> Path:
        """Get absolute data directory path."""
        return Path(self.data_dir).resolve()

    @property
    def token_path(self) -> Path:
        """Get absolute token file path."""
        return Path(self.token_file).resolve()

    @property
    def credentials_path(self) -> Path:
        """Get absolute credentials file path."""
        return Path(self.credentials_file).resolve()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
