"""Document API routes."""
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.middleware.auth import get_current_user
from app.schemas.document import DocumentResponse, DocumentMarkdownResponse

router = APIRouter()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single document by ID.
    Only returns documents belonging to the current user.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if files exist on disk
    has_pdf = bool(document.file_path and Path(document.file_path).exists())
    has_markdown = bool(document.markdown_file_path and Path(document.markdown_file_path).exists())

    response = DocumentResponse.model_validate(document)
    response.has_pdf = has_pdf
    response.has_markdown = has_markdown
    return response


@router.get("/{document_id}/markdown", response_model=DocumentMarkdownResponse)
async def get_document_markdown(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the markdown content for a document.
    Only returns documents belonging to the current user.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentMarkdownResponse(
        id=document.id,
        filename=document.filename,
        markdown_content=document.markdown_content,
    )


@router.get("/{document_id}/download/pdf")
async def download_document_pdf(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download the original PDF file for a document.
    Only allows download of documents belonging to the current user.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.file_path:
        raise HTTPException(status_code=404, detail="PDF file not found")

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=document.filename,
        media_type="application/pdf",
    )


@router.get("/{document_id}/download/markdown")
async def download_document_markdown(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download the markdown file for a document.
    Only allows download of documents belonging to the current user.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.markdown_file_path:
        raise HTTPException(status_code=404, detail="Markdown file not found")

    file_path = Path(document.markdown_file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Markdown file not found on disk")

    # Use original filename with .md extension
    md_filename = Path(document.filename).stem + ".md"

    return FileResponse(
        path=str(file_path),
        filename=md_filename,
        media_type="text/markdown",
    )
