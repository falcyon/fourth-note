"""Investment model - central entity for tracking investments."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Investment(Base):
    """Central entity for tracking investments.

    Investments are now independent of documents. Documents are linked
    via the investment_documents junction table, and field values are
    stored in the field_values table with source attribution.

    The columns below (investment_name, firm, etc.) are denormalized
    copies of the "current" values from field_values for fast display.
    """
    __tablename__ = "investments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Denormalized current values (from field_values where is_current=True)
    investment_name = Column(String(500))
    firm = Column(String(500))
    strategy_description = Column(Text)
    leaders_json = Column(JSONB, default=list)  # Leaders with LinkedIn URLs: [{"name": "...", "linkedin_url": "..."}]
    management_fees = Column(Text)
    incentive_fees = Column(Text)
    liquidity_lock = Column(Text)
    target_net_returns = Column(Text)

    # User notes (not from extraction)
    notes = Column(Text)

    # Status
    is_archived = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="investments")
    investment_documents = relationship("InvestmentDocument", back_populates="investment", cascade="all, delete-orphan")
    field_values = relationship("FieldValue", back_populates="investment", cascade="all, delete-orphan")

    @property
    def documents(self):
        """Get all linked documents."""
        return [id.document for id in self.investment_documents]

    @property
    def source_count(self):
        """Count of linked documents."""
        return len(self.investment_documents)

    def __repr__(self):
        return f"<Investment {self.investment_name or 'Unnamed'}>"
