"""Investment-Document junction table for many-to-many relationship."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class InvestmentDocument(Base):
    """Links investments to their source documents."""
    __tablename__ = "investment_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_id = Column(UUID(as_uuid=True), ForeignKey("investments.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Type of relationship
    relationship_type = Column("relationship", String(50), default="source")  # 'source', 'reference', 'supplement'

    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    investment = relationship("Investment", back_populates="investment_documents")
    document = relationship("Document", back_populates="investment_documents")

    __table_args__ = (
        UniqueConstraint('investment_id', 'document_id', name='uq_investment_documents'),
    )

    def __repr__(self):
        return f"<InvestmentDocument investment={self.investment_id} doc={self.document_id}>"
