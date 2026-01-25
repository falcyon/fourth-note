"""APScheduler integration for periodic email processing."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import SessionLocal
from app.models.email import Email, EmailStatus
from app.models.user import User
from app.services.progress import get_progress_tracker

settings = get_settings()
logger = logging.getLogger(__name__)

# Global state
_scheduler: Optional[BackgroundScheduler] = None
_last_run: Optional[datetime] = None
_last_result: Optional[Dict[str, Any]] = None


def _process_user_emails(db, user: User, progress) -> Dict[str, Any]:
    """Process emails for a single user.

    Returns dict with emails_fetched and investments_extracted counts.
    """
    from app.services.email_processor import get_email_processor, GmailNotConnectedError
    from app.services.extraction_service import get_extraction_service

    # Fetch new emails
    processor = get_email_processor(db, user)
    new_emails = processor.fetch_new_emails()
    logger.info(f"Fetched {len(new_emails)} new emails for user {user.email}")

    # Process pending documents
    extractor = get_extraction_service(db, user)
    investments = extractor.process_pending_documents()
    logger.info(f"Extracted {len(investments)} new investments for user {user.email}")

    # Update email statuses
    for email in new_emails:
        all_completed = all(
            doc.processing_status in ("completed", "failed")
            for doc in email.documents
        )
        if all_completed:
            has_failures = any(
                doc.processing_status == "failed"
                for doc in email.documents
            )
            email.status = EmailStatus.FAILED.value if has_failures else EmailStatus.COMPLETED.value
            db.commit()

    return {
        "emails_fetched": len(new_emails),
        "investments_extracted": len(investments),
    }


def run_email_processing(user_id: Optional[UUID] = None):
    """Job function: fetch new emails and process documents.

    If user_id is provided, processes emails only for that user.
    Otherwise, processes emails for all users with Gmail tokens.
    """
    global _last_run, _last_result

    logger.info("Starting scheduled email processing...")
    _last_run = datetime.utcnow()
    progress = get_progress_tracker()

    db = SessionLocal()
    try:
        from app.services.email_processor import GmailNotConnectedError

        total_emails = 0
        total_investments = 0

        if user_id:
            # Process specific user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User not found: {user_id}")

            if not user.gmail_token_json:
                raise GmailNotConnectedError(
                    "Gmail account not connected. Please connect your Gmail in Settings."
                )

            result = _process_user_emails(db, user, progress)
            total_emails = result["emails_fetched"]
            total_investments = result["investments_extracted"]
        else:
            # Scheduled job: process all users with Gmail tokens
            users = db.query(User).filter(User.gmail_token_json.isnot(None)).all()
            logger.info(f"Processing emails for {len(users)} users with Gmail connected")

            for user in users:
                try:
                    result = _process_user_emails(db, user, progress)
                    total_emails += result["emails_fetched"]
                    total_investments += result["investments_extracted"]
                except Exception as e:
                    logger.error(f"Failed to process emails for user {user.email}: {e}")
                    # Continue with other users

        progress.emit("status", "Email processing complete")

        _last_result = {
            "emails_fetched": total_emails,
            "investments_extracted": total_investments,
            "status": "success",
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Email processing failed: {e}\n{error_details}")
        progress.emit("error", f"Error: {str(e)}")
        _last_result = {
            "status": "error",
            "error": str(e),
        }
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler."""
    global _scheduler

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        run_email_processing,
        trigger=IntervalTrigger(hours=settings.scheduler_interval_hours),
        id="email_processing",
        name="Fetch and process emails",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(f"Scheduler started. Email processing every {settings.scheduler_interval_hours} hours.")


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped.")


def get_scheduler_status() -> Dict[str, Any]:
    """Get current scheduler status."""
    if _scheduler is None:
        return {
            "running": False,
            "message": "Scheduler not initialized",
        }

    job = _scheduler.get_job("email_processing")

    return {
        "running": _scheduler.running,
        "interval_hours": settings.scheduler_interval_hours,
        "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "last_run": _last_run.isoformat() if _last_run else None,
        "last_result": _last_result,
    }


def trigger_immediate_run(user_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Trigger immediate email processing for a specific user."""
    if _scheduler is None:
        return {"error": "Scheduler not running"}

    run_email_processing(user_id)
    return _last_result or {"status": "completed"}
