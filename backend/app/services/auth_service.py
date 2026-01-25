"""Authentication service for Google OAuth and JWT management."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User

settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def verify_google_token(self, token: str) -> Optional[dict]:
        """Verify a Google ID token and return user info.

        Returns dict with: google_id, email, name, picture_url
        Or None if verification fails.
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.google_client_id
            )

            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return None

            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name'),
                'picture_url': idinfo.get('picture'),
            }
        except Exception:
            return None

    def get_or_create_user(self, google_info: dict) -> User:
        """Get existing user or create new one from Google info."""
        user = self.db.query(User).filter(
            User.google_id == google_info['google_id']
        ).first()

        if user:
            # Update user info in case it changed
            user.email = google_info['email']
            user.name = google_info.get('name')
            user.picture_url = google_info.get('picture_url')
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                google_id=google_info['google_id'],
                email=google_info['email'],
                name=google_info.get('name'),
                picture_url=google_info.get('picture_url'),
            )
            self.db.add(user)

        self.db.commit()
        self.db.refresh(user)
        return user

    def create_jwt_token(self, user: User) -> str:
        """Create a JWT token for the user."""
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
        payload = {
            'sub': str(user.id),
            'email': user.email,
            'exp': expire,
            'iat': datetime.utcnow(),
        }
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

    def verify_jwt_token(self, token: str) -> Optional[dict]:
        """Verify a JWT token and return the payload.

        Returns dict with: sub (user_id), email
        Or None if verification fails.
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by their ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email."""
        return self.db.query(User).filter(User.email == email).first()

    def update_gmail_token(self, user: User, token_json: dict) -> User:
        """Update the Gmail OAuth token for a user."""
        user.gmail_token_json = token_json
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user


def get_auth_service(db: Session) -> AuthService:
    """Factory function for AuthService."""
    return AuthService(db)
