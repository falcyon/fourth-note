"""Markdown packet generator for investments.

Generates a markdown "packet" file for each investment containing all
stored information. This serves as a backup and human-readable record.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.investment import Investment
from app.models.field_value import FieldValue

settings = get_settings()


def sanitize_filename(name: str) -> str:
    """Create a safe filename from investment name."""
    if not name:
        return "unnamed"
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', name)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe.strip('_')
    return safe[:100] if safe else "unnamed"


class PacketService:
    """Service for generating markdown packet files for investments."""

    def __init__(self, db: Session):
        self.db = db
        self.packets_dir = settings.data_path / "packets"
        self.packets_dir.mkdir(parents=True, exist_ok=True)

    def generate_packet(self, investment_id: UUID) -> Optional[Path]:
        """Generate a markdown packet for an investment.

        Returns the path to the generated file, or None if investment not found.
        """
        investment = self.db.query(Investment).filter(
            Investment.id == investment_id
        ).first()

        if not investment:
            return None

        # Get all field values with history
        field_values = self.db.query(FieldValue).filter(
            FieldValue.investment_id == investment_id
        ).order_by(
            FieldValue.field_name,
            FieldValue.is_current.desc(),
            FieldValue.created_at.desc()
        ).all()

        # Group field values by field name
        fields_by_name = {}
        for fv in field_values:
            if fv.field_name not in fields_by_name:
                fields_by_name[fv.field_name] = []
            fields_by_name[fv.field_name].append(fv)

        # Generate markdown content
        content = self._generate_markdown(investment, fields_by_name)

        # Save to file
        filename = sanitize_filename(investment.investment_name or str(investment.id))
        file_path = self.packets_dir / f"{filename}.md"

        file_path.write_text(content, encoding="utf-8")
        return file_path

    def _generate_markdown(
        self,
        investment: Investment,
        fields_by_name: dict
    ) -> str:
        """Generate the markdown content for an investment packet."""
        lines = []

        # Header
        lines.append(f"# {investment.investment_name or 'Unnamed Investment'}")
        lines.append("")

        if investment.firm:
            lines.append(f"**Firm:** {investment.firm}")
            lines.append("")

        # Metadata
        lines.append("---")
        lines.append("")
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Investment ID:** `{investment.id}`")
        lines.append(f"- **Created:** {investment.created_at.strftime('%Y-%m-%d %H:%M:%S') if investment.created_at else 'Unknown'}")
        lines.append(f"- **Last Updated:** {investment.updated_at.strftime('%Y-%m-%d %H:%M:%S') if investment.updated_at else 'Unknown'}")
        lines.append(f"- **Source Documents:** {investment.source_count}")
        lines.append("")

        # Key Metrics
        lines.append("---")
        lines.append("")
        lines.append("## Key Metrics")
        lines.append("")

        metrics = [
            ("Management Fees", investment.management_fees),
            ("Incentive Fees", investment.incentive_fees),
            ("Liquidity/Lock", investment.liquidity_lock),
            ("Target Net Returns", investment.target_net_returns),
        ]

        for label, value in metrics:
            if value:
                lines.append(f"- **{label}:** {value}")

        lines.append("")

        # Leaders
        if investment.leaders:
            lines.append("---")
            lines.append("")
            lines.append("## Leadership")
            lines.append("")
            for leader in investment.leaders.split(","):
                leader = leader.strip()
                if leader:
                    lines.append(f"- {leader}")
            lines.append("")

        # Strategy
        if investment.strategy_description:
            lines.append("---")
            lines.append("")
            lines.append("## Strategy Description")
            lines.append("")
            lines.append(investment.strategy_description)
            lines.append("")

        # Notes
        if investment.notes:
            lines.append("---")
            lines.append("")
            lines.append("## Notes")
            lines.append("")
            lines.append(investment.notes)
            lines.append("")

        # Related Documents
        if investment.investment_documents:
            lines.append("---")
            lines.append("")
            lines.append("## Source Documents")
            lines.append("")
            for inv_doc in investment.investment_documents:
                doc = inv_doc.document
                if doc:
                    lines.append(f"- **{doc.filename}** ({inv_doc.relationship_type})")
                    if doc.email:
                        lines.append(f"  - From: {doc.email.sender}")
                        if doc.email.received_at:
                            lines.append(f"  - Received: {doc.email.received_at.strftime('%Y-%m-%d')}")
            lines.append("")

        # Field History (for data recovery)
        lines.append("---")
        lines.append("")
        lines.append("## Field Value History")
        lines.append("")
        lines.append("*This section contains the full history of all field values for data recovery purposes.*")
        lines.append("")

        for field_name, values in sorted(fields_by_name.items()):
            lines.append(f"### {field_name}")
            lines.append("")
            for fv in values:
                current_marker = " **(current)**" if fv.is_current else ""
                source_info = f"from {fv.source_name}" if fv.source_name else f"via {fv.source_type}"
                date_info = fv.created_at.strftime('%Y-%m-%d %H:%M') if fv.created_at else "Unknown date"
                lines.append(f"- `{fv.field_value}`{current_marker}")
                lines.append(f"  - Source: {source_info}")
                lines.append(f"  - Extracted: {date_info}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated by Fourth Note on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")

        return "\n".join(lines)

    def update_all_packets(self) -> int:
        """Regenerate packets for all investments. Returns count of packets generated."""
        investments = self.db.query(Investment).all()
        count = 0
        for inv in investments:
            if self.generate_packet(inv.id):
                count += 1
        return count


def get_packet_service(db: Session) -> PacketService:
    """Factory function for PacketService."""
    return PacketService(db)
