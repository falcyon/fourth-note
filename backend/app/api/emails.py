"""Email API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.email import Email
from app.models.document import Document
from app.schemas.email import EmailResponse, EmailListResponse

router = APIRouter()


@router.get("", response_model=EmailListResponse)
async def list_emails(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List processed emails with pagination.
    """
    query = db.query(Email)

    if status:
        query = query.filter(Email.status == status)

    # Get total count
    total = query.count()

    # Order by received date, newest first
    query = query.order_by(Email.received_at.desc().nullslast())

    # Pagination
    offset = (page - 1) * per_page
    emails = query.offset(offset).limit(per_page).all()

    # Add document counts
    items = []
    for email in emails:
        doc_count = db.query(func.count(Document.id)).filter(
            Document.email_id == email.id
        ).scalar()

        response = EmailResponse.model_validate(email)
        response.document_count = doc_count
        items.append(response)

    return EmailListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a single email by ID.
    """
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    doc_count = db.query(func.count(Document.id)).filter(
        Document.email_id == email.id
    ).scalar()

    response = EmailResponse.model_validate(email)
    response.document_count = doc_count
    return response
