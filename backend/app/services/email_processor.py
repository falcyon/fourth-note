"""Email processing service - fetches emails and saves attachments."""
import base64
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.email import Email, EmailStatus
from app.models.document import Document, DocumentStatus
from app.services.gmail_service import get_gmail_service
from app.services.progress import get_progress_tracker

settings = get_settings()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem storage."""
    # Keep only ASCII characters
    safe = filename.encode("ascii", errors="ignore").decode("ascii")
    # Replace problematic characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', safe)
    # Fallback if empty
    return safe if safe and safe != ".pdf" else "attachment.pdf"


class EmailProcessor:
    """Processes emails from Gmail and saves to database."""

    def __init__(self, db: Session):
        self.db = db
        self.gmail = get_gmail_service()
        self.data_dir = settings.data_path
        self.progress = get_progress_tracker()

    def _extract_header(self, headers: List[Dict], name: str) -> Optional[str]:
        """Extract a header value from message headers."""
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value")
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse email date header to datetime."""
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return None

    def _find_pdf_attachments(self, payload: Dict) -> List[Dict[str, str]]:
        """Find all PDF attachments in email payload."""
        attachments = []

        def scan_parts(parts: List[Dict]):
            for part in parts:
                filename = part.get("filename", "")
                body = part.get("body", {})

                if filename.lower().endswith(".pdf") and "attachmentId" in body:
                    attachments.append({
                        "filename": filename,
                        "attachment_id": body["attachmentId"],
                    })

                if "parts" in part:
                    scan_parts(part["parts"])

        if "parts" in payload:
            scan_parts(payload["parts"])

        return attachments

    def _save_attachment(
        self,
        message_id: str,
        attachment_id: str,
        filename: str,
        email_id: UUID,
    ) -> Path:
        """Download and save attachment to disk."""
        # Create directory for this email
        email_dir = self.data_dir / "emails" / str(email_id)
        email_dir.mkdir(parents=True, exist_ok=True)

        # Download and save
        data = self.gmail.get_attachment(message_id, attachment_id)
        safe_filename = sanitize_filename(filename)
        file_path = email_dir / safe_filename

        file_path.write_bytes(data)
        return file_path

    def is_message_processed(self, gmail_message_id: str) -> bool:
        """Check if a message has already been processed."""
        return self.db.query(Email).filter(
            Email.gmail_message_id == gmail_message_id
        ).first() is not None

    def process_message(self, message_id: str) -> Optional[Email]:
        """Process a single Gmail message."""
        if self.is_message_processed(message_id):
            return None

        msg = self.gmail.get_message(message_id)
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        # Find PDF attachments
        pdf_attachments = self._find_pdf_attachments(payload)
        if not pdf_attachments:
            return None  # Skip emails without PDFs

        # Extract metadata
        subject = self._extract_header(headers, "Subject")
        sender = self._extract_header(headers, "From")
        received_at = self._parse_date(self._extract_header(headers, "Date"))

        # Create email record
        email = Email(
            gmail_message_id=message_id,
            subject=subject,
            sender=sender,
            received_at=received_at,
            status=EmailStatus.PROCESSING.value,
        )
        self.db.add(email)
        self.db.flush()

        # Process each PDF attachment
        for attachment in pdf_attachments:
            file_path = self._save_attachment(
                message_id=message_id,
                attachment_id=attachment["attachment_id"],
                filename=attachment["filename"],
                email_id=email.id,
            )

            document = Document(
                email_id=email.id,
                filename=sanitize_filename(attachment["filename"]),
                file_path=str(file_path),
                processing_status=DocumentStatus.PENDING,
            )
            self.db.add(document)

        self.db.commit()
        return email

    def fetch_new_emails(self, since_timestamp: Optional[int] = None) -> List[Email]:
        """Fetch and process new emails from Gmail."""
        if since_timestamp is None:
            since_timestamp = settings.gmail_query_since

        self.progress.emit("gmail", "Connecting to Gmail API...")

        query = f"after:{since_timestamp}"
        messages = self.gmail.list_messages(query=query)

        self.progress.emit("gmail", f"Found {len(messages)} messages to check", {
            "total_messages": len(messages)
        })

        new_emails = []
        emails_with_pdfs = 0

        for i, msg_meta in enumerate(messages):
            self.progress.emit("fetch", f"Processing message {i+1}/{len(messages)}...", {
                "current": i + 1,
                "total": len(messages)
            })

            email = self.process_message(msg_meta["id"])
            if email:
                new_emails.append(email)
                emails_with_pdfs += 1
                pdf_count = len(email.documents)
                self.progress.emit("fetch", f"Found email with {pdf_count} PDF(s): {email.subject}", {
                    "subject": email.subject,
                    "pdf_count": pdf_count,
                    "emails_found": emails_with_pdfs
                })

        self.progress.emit("fetch", f"Email fetch complete: {emails_with_pdfs} emails with PDFs", {
            "emails_with_pdfs": emails_with_pdfs,
            "total_checked": len(messages)
        })

        return new_emails


def get_email_processor(db: Session) -> EmailProcessor:
    """Factory function for EmailProcessor."""
    return EmailProcessor(db)
