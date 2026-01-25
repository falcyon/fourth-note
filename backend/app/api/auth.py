"""Authentication API endpoints."""
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user
from app.services.auth_service import get_auth_service
from app.services.gmail_service import SCOPES

settings = get_settings()
router = APIRouter()


class GoogleLoginRequest(BaseModel):
    """Request body for Google login."""
    id_token: str


class LoginResponse(BaseModel):
    """Response for successful login."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """Response for user info."""
    id: str
    email: str
    name: Optional[str]
    picture_url: Optional[str]
    has_gmail_connected: bool


class GmailTokenRequest(BaseModel):
    """Request body for connecting Gmail."""
    token_json: dict


class GmailAuthCodeRequest(BaseModel):
    """Request body for exchanging Gmail authorization code."""
    code: str
    redirect_uri: str


@router.post("/login", response_model=LoginResponse)
async def login_with_google(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    """Login with Google ID token.

    Verifies the Google ID token, creates or updates the user,
    and returns a JWT access token.
    """
    auth_service = get_auth_service(db)

    # Verify the Google token
    google_info = auth_service.verify_google_token(request.id_token)
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    # Get or create user
    user = auth_service.get_or_create_user(google_info)

    # Create JWT token
    access_token = auth_service.create_jwt_token(user)

    return LoginResponse(
        access_token=access_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "picture_url": user.picture_url,
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user's info."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        picture_url=current_user.picture_url,
        has_gmail_connected=current_user.gmail_token_json is not None,
    )


@router.post("/gmail/connect")
async def connect_gmail(
    request: GmailTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connect Gmail OAuth token to user account.

    This allows the user to fetch their own emails.
    """
    auth_service = get_auth_service(db)
    auth_service.update_gmail_token(current_user, request.token_json)

    return {"message": "Gmail connected successfully"}


@router.post("/gmail/exchange")
async def exchange_gmail_code(
    request: GmailAuthCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange an authorization code for Gmail OAuth tokens.

    The frontend initiates the OAuth flow and receives an authorization code.
    This endpoint exchanges that code for access and refresh tokens,
    then stores them in the user's account.
    """
    # Exchange the authorization code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": request.code,
        "redirect_uri": request.redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=token_data)

    if response.status_code != 200:
        error_detail = response.json().get("error_description", "Token exchange failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {error_detail}",
        )

    tokens = response.json()

    # Build token data in the format we use
    token_json = {
        "token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "scopes": SCOPES,
    }

    # Store in user's account
    auth_service = get_auth_service(db)
    auth_service.update_gmail_token(current_user, token_json)

    return {"message": "Gmail connected successfully"}


@router.delete("/gmail/disconnect")
async def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Gmail from user account."""
    auth_service = get_auth_service(db)
    auth_service.update_gmail_token(current_user, None)

    return {"message": "Gmail disconnected successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """Logout the current user.

    Note: Since we use JWTs, the actual invalidation happens client-side
    by removing the token. This endpoint exists for completeness and
    could be extended to implement token blacklisting if needed.
    """
    return {"message": "Logged out successfully"}
