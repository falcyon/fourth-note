"""AI-powered extraction service using Google Gemini and OpenAI."""
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func
from google import genai
from openai import OpenAI

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
    "Leaders/PM/CEO": """Extract ALL information about each leader/executive mentioned in the document.
For each person, include as much detail as possible:
- Full name
- Current title/role at this firm
- Previous titles/roles and companies
- Education (universities, degrees)
- Years of experience
- Any other biographical details mentioned
Return as a JSON array of objects with these keys:
- 'name': Full name
- 'title': Current title/role
- 'company': Current company/firm
- 'previous_roles': Array of previous positions (e.g., ["CEO at XYZ Corp", "VP at ABC Inc"])
- 'education': Array of education (e.g., ["MBA Harvard", "BS MIT"])
- 'background': Any other relevant background info as a string
Example: [{"name": "John Smith", "title": "CEO", "company": "Acme Capital", "previous_roles": ["Partner at BigFund LP"], "education": ["MBA Wharton"], "background": "20 years in private equity"}]""",
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
    "Leaders/PM/CEO": "leaders_json",
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
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.pdf_converter = get_pdf_converter()
        self.progress = get_progress_tracker()

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from response text."""
        text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("No JSON object found in response")
        return json.loads(match.group(0))

    def _map_fields(self, raw_data: Dict[str, Any], leaders_with_linkedin: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Map extracted field names to database column names."""
        mapped = {}
        for api_field, db_field in FIELD_MAPPING.items():
            value = raw_data.get(api_field)
            if value is None:
                mapped[db_field] = None
            elif db_field == "leaders_json":
                # Use the leaders with LinkedIn URLs if provided (from second pass)
                if leaders_with_linkedin is not None:
                    mapped[db_field] = leaders_with_linkedin
                elif isinstance(value, list):
                    # First pass: just extract names for now
                    mapped[db_field] = [
                        {"name": item.get("name", ""), "linkedin_url": None}
                        for item in value if isinstance(item, dict) and item.get("name")
                    ]
                elif isinstance(value, str):
                    # Fallback: Gemini returned string, parse as pipe-separated
                    mapped[db_field] = [
                        {"name": name.strip(), "linkedin_url": None}
                        for name in value.split("|") if name.strip()
                    ]
                else:
                    mapped[db_field] = None
            else:
                mapped[db_field] = str(value)
        return mapped

    def _lookup_single_linkedin(self, leader: Dict[str, Any], firm_name: str = None) -> Dict[str, str]:
        """Look up LinkedIn profile for a single leader using OpenAI with web search."""
        name = leader.get("name", "Unknown")

        if not self.openai_client:
            print(f"[LinkedIn] {name}: OpenAI client not configured, skipping")
            return {"name": name, "linkedin_url": None}

        # Build context like the raw PDF text
        context_parts = [name]
        if leader.get("title"):
            context_parts.append(leader["title"])
        if leader.get("company") or firm_name:
            context_parts.append(f"at {leader.get('company') or firm_name}")
        if leader.get("previous_roles"):
            for role in leader["previous_roles"][:3]:
                context_parts.append(role)
        if leader.get("education"):
            for edu in leader["education"][:2]:
                context_parts.append(edu)
        if leader.get("background"):
            context_parts.append(leader["background"][:150])

        context = "\n".join(context_parts)
        print(f"[LinkedIn] Searching (OpenAI): {context[:100]}...")

        try:
            # Use gpt-5.2 with web search and simple ChatGPT-style prompt
            response = self.openai_client.responses.create(
                model="gpt-5.2",
                tools=[{"type": "web_search_preview"}],
                input=f"can you find this person's linkedin and give me the link?\n\n{context}"
            )

            # Get the response text
            text = response.output_text if hasattr(response, 'output_text') else str(response)
            print(f"[LinkedIn] {name}: response={text[:300] if text else 'None'}...")

            if not text:
                return {"name": name, "linkedin_url": None}

            # Extract LinkedIn URL from response
            url_match = re.search(r'https?://[^\s]*linkedin\.com/in/[^\s\)\"\'\]\>]+', text)
            if url_match:
                linkedin_url = url_match.group(0).rstrip('.,;:')
                print(f"[LinkedIn] {name}: FOUND {linkedin_url}")
                return {"name": name, "linkedin_url": linkedin_url}

            print(f"[LinkedIn] {name}: no LinkedIn URL in response")
            return {"name": name, "linkedin_url": None}

        except Exception as e:
            print(f"[LinkedIn] {name}: error - {e}")
            import traceback
            traceback.print_exc()

        return {"name": name, "linkedin_url": None}

    def _lookup_linkedin_profiles(self, leaders: List[Dict[str, Any]], firm_name: str = None) -> List[Dict[str, str]]:
        """Second pass: Use OpenAI with web search to find LinkedIn profiles for each leader."""
        if not leaders:
            return []

        print(f"[LinkedIn Lookup] Searching for {len(leaders)} people using OpenAI web search...")

        results = []
        for leader in leaders:
            result = self._lookup_single_linkedin(leader, firm_name)
            results.append(result)

        found_count = sum(1 for r in results if r.get("linkedin_url"))
        print(f"[LinkedIn Lookup] Found {found_count}/{len(leaders)} LinkedIn profiles")

        return results

    def extract_from_markdown(self, markdown_content: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Extract investment data from markdown content.

        Two-step process:
        1. Extract all investment fields including detailed leader info
        2. Use Google Search to find LinkedIn profiles for each leader
        """
        # Step 1: Extract all investment data (no search needed)
        print("[Extraction] Step 1: Extracting investment data...")
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=EXTRACTION_PROMPT + "\n\nDOCUMENT:\n" + markdown_content,
        )

        raw_data = self._extract_json(response.text)
        leaders_raw = raw_data.get("Leaders/PM/CEO", [])
        firm_name = raw_data.get("Firm")

        print(f"[Extraction] Found {len(leaders_raw) if isinstance(leaders_raw, list) else 0} leaders")

        # Log the raw leader data from step 1
        if isinstance(leaders_raw, list):
            print(f"[Extraction] Raw leader data from Gemini:")
            for i, leader in enumerate(leaders_raw[:5]):  # Limit to first 5 to avoid too much output
                print(f"  {i+1}. {leader}")

        # Step 2: Look up LinkedIn profiles for each leader
        leaders_with_linkedin = []
        if isinstance(leaders_raw, list) and leaders_raw:
            print("[Extraction] Step 2: Looking up LinkedIn profiles...")
            leaders_with_linkedin = self._lookup_linkedin_profiles(leaders_raw, firm_name)

        return self._map_fields(raw_data, leaders_with_linkedin), raw_data

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

            # Serialize JSON fields to string for storage
            stored_value = (
                json.dumps(field_value) if isinstance(field_value, (list, dict))
                else str(field_value)
            )

            # Create new field value
            fv = FieldValue(
                investment_id=investment.id,
                field_name=field_name,
                field_value=stored_value,
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
