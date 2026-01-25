from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.document import DocumentStatus


class DocumentBase(BaseModel):
    filename: str
    file_path: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: UUID
    email_id: UUID
    processing_status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentMarkdownResponse(BaseModel):
    id: UUID
    filename: str
    markdown_content: Optional[str] = None
