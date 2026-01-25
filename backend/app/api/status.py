"""Status and health API routes."""
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.email import Email
from app.models.document import Document, DocumentStatus
from app.models.investment import Investment
from app.services.gmail_service import get_gmail_service
from app.services.scheduler import get_scheduler_status

router = APIRouter()


class SystemStatus(BaseModel):
    status: str
    database: str
    gmail: str
    timestamp: str


class SchedulerStatus(BaseModel):
    running: bool
    interval_hours: int
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    last_result: Optional[Dict[str, Any]] = None


class OAuthStatus(BaseModel):
    authenticated: bool
    token_exists: bool
    token_expired: Optional[bool] = None
    message: str
    error: Optional[str] = None


class DatabaseStats(BaseModel):
    total_emails: int
    total_documents: int
    total_investments: int
    pending_documents: int
    failed_documents: int


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """Get overall system health status."""
    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    # Check Gmail
    gmail = get_gmail_service()
    gmail_auth = gmail.get_auth_status()
    gmail_status = "connected" if gmail_auth["authenticated"] else gmail_auth.get("message", "disconnected")

    overall = "healthy" if db_status == "connected" and gmail_auth["authenticated"] else "degraded"

    return SystemStatus(
        status=overall,
        database=db_status,
        gmail=gmail_status,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/scheduler/status", response_model=SchedulerStatus)
async def get_scheduler_info():
    """Get scheduler status and next run time."""
    status = get_scheduler_status()
    return SchedulerStatus(**status)


@router.get("/oauth/status", response_model=OAuthStatus)
async def get_oauth_status():
    """Get Gmail OAuth connection status."""
    gmail = get_gmail_service()
    status = gmail.get_auth_status()
    return OAuthStatus(**status)


@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics."""
    return DatabaseStats(
        total_emails=db.query(func.count(Email.id)).scalar() or 0,
        total_documents=db.query(func.count(Document.id)).scalar() or 0,
        total_investments=db.query(func.count(Investment.id)).scalar() or 0,
        pending_documents=db.query(func.count(Document.id)).filter(
            Document.processing_status == DocumentStatus.PENDING.value
        ).scalar() or 0,
        failed_documents=db.query(func.count(Document.id)).filter(
            Document.processing_status == DocumentStatus.FAILED.value
        ).scalar() or 0,
    )
