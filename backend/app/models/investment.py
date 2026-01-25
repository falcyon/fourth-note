import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Investment(Base):
    __tablename__ = "investments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    # Extracted fields (the 8 key fields)
    investment_name = Column(String(500))
    firm = Column(String(500))
    strategy_description = Column(Text)
    leaders = Column(Text)  # Leaders/PM/CEO
    management_fees = Column(String(255))
    incentive_fees = Column(String(255))
    liquidity_lock = Column(String(255))
    target_net_returns = Column(String(255))

    # Store raw extraction for debugging/audit
    raw_extraction_json = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="investments")

    def __repr__(self):
        return f"<Investment {self.investment_name or 'Unnamed'}>"
