"""Email model for storing processed emails."""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EmailStatus(str, enum.Enum):
    """Email processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Triaged out as not investment-related


class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    gmail_message_id = Column(String(255), unique=True, nullable=False, index=True)
    subject = Column(String(500))
    sender = Column(String(255))
    body_text = Column(String, nullable=True)  # Plain text email body for triage
    received_at = Column(DateTime)
    # Store as string, use enum values (lowercase)
    status = Column(String(50), default=EmailStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emails")
    documents = relationship("Document", back_populates="email", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Email {self.gmail_message_id}: {self.subject}>"
