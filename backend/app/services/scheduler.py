"""APScheduler integration for periodic email processing."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import SessionLocal
from app.models.email import Email, EmailStatus
from app.services.progress import get_progress_tracker

settings = get_settings()
logger = logging.getLogger(__name__)

# Global state
_scheduler: Optional[BackgroundScheduler] = None
_last_run: Optional[datetime] = None
_last_result: Optional[Dict[str, Any]] = None


def run_email_processing():
    """Job function: fetch new emails and process documents."""
    global _last_run, _last_result

    logger.info("Starting scheduled email processing...")
    _last_run = datetime.utcnow()
    progress = get_progress_tracker()

    db = SessionLocal()
    try:
        from app.services.email_processor import get_email_processor
        from app.services.extraction_service import get_extraction_service

        # Fetch new emails
        processor = get_email_processor(db)
        new_emails = processor.fetch_new_emails()
        logger.info(f"Fetched {len(new_emails)} new emails with PDF attachments")

        # Process pending documents
        extractor = get_extraction_service(db)
        investments = extractor.process_pending_documents()
        logger.info(f"Extracted {len(investments)} new investments")

        # Update email statuses
        progress.emit("status", "Updating email statuses...")
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

        _last_result = {
            "emails_fetched": len(new_emails),
            "investments_extracted": len(investments),
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


def trigger_immediate_run() -> Dict[str, Any]:
    """Trigger immediate email processing."""
    if _scheduler is None:
        return {"error": "Scheduler not running"}

    run_email_processing()
    return _last_result or {"status": "completed"}
