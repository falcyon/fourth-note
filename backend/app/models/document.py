"""Document model for storing PDF attachments."""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    CONVERTING = "converting"
    CONVERTED = "converted"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True)  # Now nullable for manual uploads
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000))
    markdown_content = Column(Text)
    markdown_file_path = Column(String(1000))  # Path to saved .md file
    # Store as string, use enum values (lowercase)
    processing_status = Column(String(50), default=DocumentStatus.PENDING.value, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    email = relationship("Email", back_populates="documents")
    investment_documents = relationship("InvestmentDocument", back_populates="document", cascade="all, delete-orphan")

    @property
    def investments(self):
        """Get all investments linked to this document."""
        return [id.investment for id in self.investment_documents]

    def __repr__(self):
        return f"<Document {self.filename}>"
