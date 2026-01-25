"""Document API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentMarkdownResponse

router = APIRouter()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a single document by ID.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/markdown", response_model=DocumentMarkdownResponse)
async def get_document_markdown(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get the markdown content for a document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentMarkdownResponse(
        id=document.id,
        filename=document.filename,
        markdown_content=document.markdown_content,
    )
