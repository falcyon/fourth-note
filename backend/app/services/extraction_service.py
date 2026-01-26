"""AI-powered extraction service using Google Gemini."""
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func
from google import genai

from app.config import get_settings
from app.models.document import Document, DocumentStatus
from app.models.investment import Investment
from app.models.investment_document import InvestmentDocument
from app.models.field_value import FieldValue
from app.models.user import User
from app.services.pdf_converter import get_pdf_converter
from app.services.progress import get_progress_tracker
from app.services.packet_service import get_packet_service

settings = get_settings()

# Field definitions with formatting instructions
FIELDS_FORMATS = {
    "Investment": "No specific format",
    "Firm": "No specific format",
    "Strategy Description": "No specific format",
    "Leaders/PM/CEO": "If multiple people, separate with pipe character |",
    "Management Fees": "No specific format",
    "Incentive Fees": "Format as 'x% Pref | x% incentive fee', e.g., '8% Pref | 20% incentive fee'",
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

    def __init__(self, db: Session, user: Optional[User] = None):
        self.db = db
        self.user = user
        self.user_id = user.id if user else None
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

    def _find_matching_investment(self, name: Optional[str], firm: Optional[str], user_id: UUID) -> Optional[Investment]:
        """Try to find an existing investment by name and firm."""
        if not name and not firm:
            return None

        query = self.db.query(Investment).filter(Investment.user_id == user_id)

        # Try exact match on name and firm
        if name and firm:
            existing = query.filter(
                func.lower(Investment.investment_name) == func.lower(name),
                func.lower(Investment.firm) == func.lower(firm)
            ).first()
            if existing:
                return existing

        # Try match on just firm if name is similar or missing
        if firm:
            existing = query.filter(
                func.lower(Investment.firm) == func.lower(firm)
            ).first()
            if existing and (not name or not existing.investment_name or
                           name.lower() in existing.investment_name.lower() or
                           existing.investment_name.lower() in name.lower()):
                return existing

        return None

    def _create_field_values(
        self,
        investment: Investment,
        mapped_fields: Dict[str, Any],
        document: Document
    ) -> List[FieldValue]:
        """Create FieldValue records for each extracted field."""
        field_values = []

        for field_name, field_value in mapped_fields.items():
            if field_value is None:
                continue

            # Mark any existing current values for this field as not current
            self.db.query(FieldValue).filter(
                FieldValue.investment_id == investment.id,
                FieldValue.field_name == field_name,
                FieldValue.is_current == True
            ).update({"is_current": False})

            # Create new field value
            fv = FieldValue(
                investment_id=investment.id,
                field_name=field_name,
                field_value=field_value,
                source_type="document",
                source_id=document.id,
                source_name=document.filename,
                is_current=True,
                confidence="medium",
            )
            self.db.add(fv)
            field_values.append(fv)

        return field_values

    def _update_denormalized_fields(self, investment: Investment, mapped_fields: Dict[str, Any]) -> None:
        """Update the denormalized field columns on Investment."""
        for field_name, field_value in mapped_fields.items():
            if field_value is not None:
                setattr(investment, field_name, field_value)

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
                # Save markdown file alongside PDF
                pdf_path = Path(document.file_path)
                md_path = pdf_path.with_suffix('.md')
                markdown = self.pdf_converter.convert_pdf(document.file_path, output_md_path=str(md_path))
                document.markdown_file_path = str(md_path)
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

            # Check if investment already exists
            investment = self._find_matching_investment(
                mapped_fields.get("investment_name"),
                mapped_fields.get("firm"),
                document.user_id
            )

            is_new = investment is None
            if is_new:
                # Create new investment
                investment = Investment(
                    user_id=document.user_id,
                )
                self.db.add(investment)
                self.db.flush()  # Get the ID

            # Link document to investment
            existing_link = self.db.query(InvestmentDocument).filter(
                InvestmentDocument.investment_id == investment.id,
                InvestmentDocument.document_id == document.id
            ).first()

            if not existing_link:
                link = InvestmentDocument(
                    investment_id=investment.id,
                    document_id=document.id,
                    relationship_type="source",
                )
                self.db.add(link)

            # Create field values with source attribution
            self._create_field_values(investment, mapped_fields, document)

            # Update denormalized fields on Investment
            self._update_denormalized_fields(investment, mapped_fields)

            document.processing_status = DocumentStatus.COMPLETED.value
            self.db.commit()

            # Generate/update the markdown packet for this investment
            packet_service = get_packet_service(self.db)
            packet_service.generate_packet(investment.id)

            investment_name = mapped_fields.get("investment_name", "Unknown")
            firm = mapped_fields.get("firm", "Unknown")
            action = "Created" if is_new else "Updated"
            self.progress.emit("extraction", f"{action}: {investment_name} ({firm})", {
                "filename": document.filename,
                "investment_name": investment_name,
                "firm": firm,
                "is_new": is_new,
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
        """Process all pending documents for the current user."""
        query = self.db.query(Document).filter(
            Document.processing_status == DocumentStatus.PENDING.value
        )
        if self.user_id:
            query = query.filter(Document.user_id == self.user_id)
        pending = query.all()

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


def get_extraction_service(db: Session, user: Optional[User] = None) -> ExtractionService:
    """Factory function for ExtractionService."""
    return ExtractionService(db, user)
