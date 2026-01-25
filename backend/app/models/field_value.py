"""FieldValue model for field-level source attribution."""
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class FieldValue(Base):
    """Stores field values with source attribution.

    Each field value tracks:
    - Which investment it belongs to
    - What field it is (investment_name, firm, etc.)
    - The actual value
    - Where it came from (source_type, source_id, source_name)
    - Location within the source (for future hover-to-see-context)
    - Effective date (for time-series data like quarterly revenue, leadership changes)
    - Whether it's the current/active value
    """
    __tablename__ = "field_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_id = Column(UUID(as_uuid=True), ForeignKey("investments.id", ondelete="CASCADE"), nullable=False, index=True)

    # What field this is
    field_name = Column(String(100), nullable=False)  # 'investment_name', 'firm', 'q4_2024_revenue', etc.
    field_value = Column(Text)

    # Source attribution
    source_type = Column(String(50), nullable=False)  # 'document', 'manual', 'web', 'api'
    source_id = Column(UUID(as_uuid=True))  # References document_id, email_id, etc.
    source_name = Column(String(500))  # Display name: "Q4 Pitch Deck.pdf"

    # Location within source (for future "hover to see context" feature)
    source_location_start = Column(Integer)  # Markdown line/char offset
    source_location_end = Column(Integer)
    source_context = Column(Text)  # Text snippet from source

    # For time-series data (quarterly revenue, leadership changes, etc.)
    effective_date = Column(Date)  # When this value was true
    period_type = Column(String(20))  # 'quarterly', 'annual', 'point_in_time', null

    # Status
    is_current = Column(Boolean, default=True)  # Is this the active value?
    confidence = Column(String(20), default="medium")  # 'low', 'medium', 'high', 'verified'

    # Timestamps
    extracted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    investment = relationship("Investment", back_populates="field_values")

    def __repr__(self):
        return f"<FieldValue {self.field_name}={self.field_value[:20] if self.field_value else 'None'}...>"
