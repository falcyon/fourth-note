from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.email import EmailStatus


class EmailBase(BaseModel):
    gmail_message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    received_at: Optional[datetime] = None


class EmailCreate(EmailBase):
    pass


class EmailResponse(EmailBase):
    id: UUID
    status: EmailStatus
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    items: List[EmailResponse]
    total: int
    page: int
    per_page: int
    pages: int
