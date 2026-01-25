"""Manual trigger API routes."""
import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import json

from app.database import get_db, SessionLocal
from app.services.scheduler import trigger_immediate_run
from app.services.progress import get_progress_tracker, ProgressEvent

router = APIRouter()


class TriggerResponse(BaseModel):
    message: str
    status: str
    emails_fetched: Optional[int] = None
    investments_extracted: Optional[int] = None
    error: Optional[str] = None


def run_processing_with_progress():
    """Run the email processing and return result."""
    progress = get_progress_tracker()
    progress.clear()
    progress.emit("start", "Starting email processing...")

    result = trigger_immediate_run()

    if result.get("status") == "error":
        progress.error(f"Processing failed: {result.get('error')}", result)
    else:
        progress.complete("Processing complete!", {
            "emails_fetched": result.get("emails_fetched", 0),
            "investments_extracted": result.get("investments_extracted", 0),
        })

    return result


async def progress_stream() -> AsyncGenerator[str, None]:
    """Generate SSE stream of progress events."""
    progress = get_progress_tracker()
    queue = progress.subscribe()

    # Start processing in a thread
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, run_processing_with_progress)

    try:
        while True:
            try:
                # Wait for events with timeout
                event = await asyncio.wait_for(queue.get(), timeout=0.5)
                yield event.to_sse()

                # If complete or error, we're done
                if event.step in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                # Check if processing is done
                if task.done():
                    break
                # Send heartbeat to keep connection alive
                yield ": heartbeat\n\n"
    finally:
        progress.unsubscribe(queue)
        # Ensure task completes
        await task


@router.get("/fetch-emails/stream")
async def trigger_fetch_emails_stream():
    """
    Stream progress of email fetch and processing via Server-Sent Events.
    """
    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/fetch-emails", response_model=TriggerResponse)
async def trigger_fetch_emails():
    """
    Manually trigger email fetch and processing.

    This runs synchronously and returns the result.
    """
    result = trigger_immediate_run()

    if result.get("status") == "error":
        return TriggerResponse(
            message="Email processing failed",
            status="error",
            error=result.get("error"),
        )

    return TriggerResponse(
        message="Email processing completed",
        status="success",
        emails_fetched=result.get("emails_fetched", 0),
        investments_extracted=result.get("investments_extracted", 0),
    )
