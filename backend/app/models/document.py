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
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000))
    markdown_content = Column(Text)
    # Store as string, use enum values (lowercase)
    processing_status = Column(String(50), default=DocumentStatus.PENDING.value, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    email = relationship("Email", back_populates="documents")
    investments = relationship("Investment", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document {self.filename}>"
