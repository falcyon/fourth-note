"""Email orchestrator that coordinates the agentic pipeline."""

import asyncio
import json
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base import AgentResult
from app.agents.triage_agent import TriageAgent, TriageInput, TriageClassification
from app.agents.extraction_agent import ExtractionAgent
from app.agents.linkedin_agent import LinkedInAgent, LinkedInInput
from app.models.email import Email, EmailStatus
from app.models.document import Document, DocumentStatus
from app.models.investment import Investment
from app.models.investment_document import InvestmentDocument
from app.models.field_value import FieldValue
from app.models.user import User
from app.services.pdf_converter import get_pdf_converter
from app.services.progress import get_progress_tracker
from app.services.packet_service import get_packet_service


class EmailOrchestrator:
    """Coordinates agent execution for processing investment emails.

    Pipeline:
    1. Triage: Classify email as investment-related (YES/NO/UNSURE)
    2. For each PDF document (if not NO):
       a. Convert PDF to markdown
       b. Extract investment data with ExtractionAgent
       c. Look up LinkedIn profiles in parallel with LinkedInAgents
    3. Save to database (Investment, FieldValues, etc.)
    """

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.user_id = user.id
        self.triage_agent = TriageAgent()
        self.extraction_agent = ExtractionAgent()
        self.pdf_converter = get_pdf_converter()
        self.progress = get_progress_tracker()

    def log(self, message: str) -> None:
        """Log with orchestrator prefix."""
        print(f"[Orchestrator] {message}")

    async def process_email(self, email: Email, documents: List[Document]) -> List[Investment]:
        """Process a single email through the agentic pipeline.

        Args:
            email: The Email record
            documents: List of Document records (PDF attachments)

        Returns:
            List of Investment records created/updated
        """
        self.log(f"Processing email: {email.subject}")

        # Step 1: Triage - should we process this email?
        triage_input = TriageInput(
            subject=email.subject or "",
            sender=email.sender or "",
            attachment_names=[d.filename for d in documents],
            body_text=email.body_text or "",
        )

        triage_result = await self.triage_agent.run(triage_input)

        if not triage_result.success:
            self.log(f"Triage failed: {triage_result.error}")
            # Continue anyway with UNSURE
            classification = TriageClassification.UNSURE
        else:
            classification = triage_result.data["classification"]
            reason = triage_result.data.get("reason", "")
            self.log(f"Triage result: {classification.value} - {reason}")

        # If NO, skip this email
        if classification == TriageClassification.NO:
            self.progress.emit("triage", f"Skipped: {email.subject} (not investment-related)", {
                "email_id": str(email.id),
                "classification": "NO",
                "reason": triage_result.data.get("reason", ""),
            })
            email.status = EmailStatus.SKIPPED.value
            self.db.commit()
            return []

        # Step 2: Process each document
        investments = []
        for doc in documents:
            try:
                investment = await self._process_document(doc)
                if investment:
                    investments.append(investment)
            except Exception as e:
                self.log(f"Document processing failed: {doc.filename} - {e}")
                doc.processing_status = DocumentStatus.FAILED.value
                doc.error_message = str(e)
                self.db.commit()

        return investments

    async def _process_document(self, document: Document) -> Optional[Investment]:
        """Process a single document through extraction and LinkedIn lookup."""

        # Step 2a: Convert PDF to markdown
        self.progress.emit("processing", f"Converting PDF: {document.filename}", {
            "filename": document.filename,
            "stage": "converting",
        })

        document.processing_status = DocumentStatus.CONVERTING.value
        self.db.commit()

        if document.file_path and document.file_path.endswith(".pdf"):
            pdf_path = Path(document.file_path)
            md_path = pdf_path.with_suffix(".md")
            markdown = self.pdf_converter.convert_pdf(document.file_path, output_md_path=str(md_path))
            document.markdown_file_path = str(md_path)
        else:
            markdown = document.markdown_content or ""

        document.markdown_content = markdown
        document.processing_status = DocumentStatus.CONVERTED.value
        self.db.commit()

        # Step 2b: Extract investment data
        self.progress.emit("extraction", f"Extracting data: {document.filename}", {
            "filename": document.filename,
            "stage": "extracting",
            "markdown_length": len(markdown),
        })

        document.processing_status = DocumentStatus.EXTRACTING.value
        self.db.commit()

        extraction_result = await self.extraction_agent.run(markdown)

        if not extraction_result.success:
            raise Exception(f"Extraction failed: {extraction_result.error}")

        mapped_fields = extraction_result.data["mapped_fields"]
        leaders_raw = extraction_result.data["leaders_raw"]
        firm_name = extraction_result.data["firm_name"]

        # Step 2c: Store leaders (LinkedIn lookup disabled - unreliable results)
        if leaders_raw:
            # Just store leaders with null LinkedIn URLs
            mapped_fields["leaders_json"] = [
                {"name": leader.get("name", "Unknown"), "linkedin_url": None}
                for leader in leaders_raw
            ]
        else:
            mapped_fields["leaders_json"] = []

        # Step 3: Save to database
        investment = self._save_investment(document, mapped_fields)

        document.processing_status = DocumentStatus.COMPLETED.value
        self.db.commit()

        # Generate markdown packet
        packet_service = get_packet_service(self.db)
        packet_service.generate_packet(investment.id)

        return investment

    async def _lookup_linkedin_parallel(
        self, leaders: List[dict], firm_name: str = None
    ) -> List[dict]:
        """Look up LinkedIn profiles for all leaders in parallel."""

        self.log(f"Looking up {len(leaders)} LinkedIn profiles in parallel...")

        # Create tasks for all leaders
        tasks = []
        for leader in leaders:
            linkedin_input = LinkedInInput.from_leader_dict(leader, firm_name)
            agent = LinkedInAgent()
            tasks.append(agent.run(linkedin_input))

        # Run all lookups in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        leaders_with_linkedin = []
        found_count = 0

        for i, result in enumerate(results):
            name = leaders[i].get("name", "Unknown")

            if isinstance(result, Exception):
                self.log(f"LinkedIn lookup failed for {name}: {result}")
                leaders_with_linkedin.append({"name": name, "linkedin_url": None})
            elif isinstance(result, AgentResult) and result.success:
                data = result.data
                if data.get("linkedin_url"):
                    found_count += 1
                leaders_with_linkedin.append(data)
            else:
                leaders_with_linkedin.append({"name": name, "linkedin_url": None})

        self.log(f"Found {found_count}/{len(leaders)} LinkedIn profiles")
        return leaders_with_linkedin

    def _save_investment(self, document: Document, mapped_fields: dict) -> Investment:
        """Save or update investment in database."""

        # Check if investment already exists
        investment = self._find_matching_investment(
            mapped_fields.get("investment_name"),
            mapped_fields.get("firm"),
            document.user_id,
        )

        is_new = investment is None
        if is_new:
            investment = Investment(user_id=document.user_id)
            self.db.add(investment)
            self.db.flush()

        # Link document to investment
        existing_link = self.db.query(InvestmentDocument).filter(
            InvestmentDocument.investment_id == investment.id,
            InvestmentDocument.document_id == document.id,
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

        # Update denormalized fields
        self._update_denormalized_fields(investment, mapped_fields)

        self.db.commit()

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

    def _find_matching_investment(
        self, name: Optional[str], firm: Optional[str], user_id: UUID
    ) -> Optional[Investment]:
        """Try to find an existing investment by name and firm."""
        if not name and not firm:
            return None

        query = self.db.query(Investment).filter(Investment.user_id == user_id)

        # Try exact match on name and firm
        if name and firm:
            existing = query.filter(
                func.lower(Investment.investment_name) == func.lower(name),
                func.lower(Investment.firm) == func.lower(firm),
            ).first()
            if existing:
                return existing

        # Try match on just firm if name is similar or missing
        if firm:
            existing = query.filter(
                func.lower(Investment.firm) == func.lower(firm)
            ).first()
            if existing and (
                not name
                or not existing.investment_name
                or name.lower() in existing.investment_name.lower()
                or existing.investment_name.lower() in name.lower()
            ):
                return existing

        return None

    def _create_field_values(
        self, investment: Investment, mapped_fields: dict, document: Document
    ) -> None:
        """Create FieldValue records for each extracted field."""
        for field_name, field_value in mapped_fields.items():
            if field_value is None:
                continue

            # Mark existing current values as not current
            self.db.query(FieldValue).filter(
                FieldValue.investment_id == investment.id,
                FieldValue.field_name == field_name,
                FieldValue.is_current == True,
            ).update({"is_current": False})

            # Serialize JSON fields
            stored_value = (
                json.dumps(field_value)
                if isinstance(field_value, (list, dict))
                else str(field_value)
            )

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

    def _update_denormalized_fields(
        self, investment: Investment, mapped_fields: dict
    ) -> None:
        """Update denormalized field columns on Investment."""
        for field_name, field_value in mapped_fields.items():
            if field_value is not None:
                setattr(investment, field_name, field_value)


def get_orchestrator(db: Session, user: User) -> EmailOrchestrator:
    """Factory function for EmailOrchestrator."""
    return EmailOrchestrator(db, user)
