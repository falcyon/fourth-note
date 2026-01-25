"""AI-powered extraction service using Google Gemini."""
import json
import re
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from google import genai

from app.config import get_settings
from app.models.document import Document, DocumentStatus
from app.models.investment import Investment
from app.services.pdf_converter import get_pdf_converter
from app.services.progress import get_progress_tracker

settings = get_settings()

# Field definitions with formatting instructions
FIELDS_FORMATS = {
    "Investment": "No specific format",
    "Firm": "No specific format",
    "Strategy Description": "No specific format",
    "Leaders/PM/CEO": "If multiple people, separate with commas",
    "Management Fees": "No specific format",
    "Incentive Fees": "Format as 'x% Pref and then x% incentive fee', e.g., '8% Pref and 20% incentive fee'",
    "Liquidity/Lock": "No specific format",
    "Target Net Returns": "Format as percentage or range, e.g., '10-12%'",
}

EXTRACTION_PROMPT = f"""
You are analyzing an investment pitch deck.

Extract the following fields from the document.
If a field is not present or unclear, return null.

Fields and formatting instructions:
{chr(10).join(f"- {field}: {fmt}" for field, fmt in FIELDS_FORMATS.items())}

Return valid JSON only. Do not include any other text or explanation.
"""

# Mapping from API field names to database column names
FIELD_MAPPING = {
    "Investment": "investment_name",
    "Firm": "firm",
    "Strategy Description": "strategy_description",
    "Leaders/PM/CEO": "leaders",
    "Management Fees": "management_fees",
    "Incentive Fees": "incentive_fees",
    "Liquidity/Lock": "liquidity_lock",
    "Target Net Returns": "target_net_returns",
}


class ExtractionService:
    """Service for extracting investment data from documents."""

    def __init__(self, db: Session):
        self.db = db
        self.client = genai.Client(api_key=settings.google_api_key)
        self.pdf_converter = get_pdf_converter()
        self.progress = get_progress_tracker()

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from response text."""
        text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("No JSON object found in response")
        return json.loads(match.group(0))

    def _map_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted field names to database column names."""
        return {
            db_field: str(raw_data.get(api_field)) if raw_data.get(api_field) else None
            for api_field, db_field in FIELD_MAPPING.items()
        }

    def extract_from_markdown(self, markdown_content: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Extract investment data from markdown content."""
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=EXTRACTION_PROMPT + "\n\nDOCUMENT:\n" + markdown_content,
        )
        raw_data = self._extract_json(response.text)
        return self._map_fields(raw_data), raw_data

    def process_document(self, document_id: UUID) -> Optional[Investment]:
        """Process a document: convert to markdown and extract investment data."""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None

        try:
            # Convert PDF to markdown
            self.progress.emit("processing", f"Converting PDF: {document.filename}", {
                "filename": document.filename,
                "stage": "converting"
            })

            document.processing_status = DocumentStatus.CONVERTING.value
            self.db.commit()

            if document.file_path and document.file_path.endswith('.pdf'):
                markdown = self.pdf_converter.convert_pdf(document.file_path)
            else:
                markdown = document.markdown_content or ""

            document.markdown_content = markdown
            document.processing_status = DocumentStatus.CONVERTED.value
            self.db.commit()

            # Extract investment data
            self.progress.emit("extraction", f"Sending to Gemini AI: {document.filename}", {
                "filename": document.filename,
                "stage": "extracting",
                "markdown_length": len(markdown)
            })

            document.processing_status = DocumentStatus.EXTRACTING.value
            self.db.commit()

            mapped_fields, raw_data = self.extract_from_markdown(markdown)

            # Create investment record
            investment = Investment(
                document_id=document.id,
                raw_extraction_json=raw_data,
                **mapped_fields,
            )
            self.db.add(investment)

            document.processing_status = DocumentStatus.COMPLETED.value
            self.db.commit()

            investment_name = mapped_fields.get("investment_name", "Unknown")
            firm = mapped_fields.get("firm", "Unknown")
            self.progress.emit("extraction", f"Extracted: {investment_name} ({firm})", {
                "filename": document.filename,
                "investment_name": investment_name,
                "firm": firm,
            })

            return investment

        except Exception as e:
            self.progress.emit("error", f"Failed: {document.filename}: {str(e)}", {
                "filename": document.filename,
                "error": str(e)
            })
            document.processing_status = DocumentStatus.FAILED.value
            document.error_message = str(e)
            self.db.commit()
            return None

    def process_pending_documents(self) -> List[Investment]:
        """Process all pending documents."""
        pending = self.db.query(Document).filter(
            Document.processing_status == DocumentStatus.PENDING.value
        ).all()

        if not pending:
            self.progress.emit("processing", "No pending documents to process")
            return []

        self.progress.emit("processing", f"Found {len(pending)} documents to process", {
            "total_documents": len(pending)
        })

        investments = []
        for i, document in enumerate(pending):
            self.progress.emit("processing", f"Processing {i+1}/{len(pending)}: {document.filename}", {
                "current": i + 1,
                "total": len(pending),
                "filename": document.filename
            })

            investment = self.process_document(document.id)
            if investment:
                investments.append(investment)

        return investments


def get_extraction_service(db: Session) -> ExtractionService:
    """Factory function for ExtractionService."""
    return ExtractionService(db)
