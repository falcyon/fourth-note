"""Investment API routes."""
import csv
import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.investment import Investment
from app.models.document import Document
from app.models.email import Email
from app.schemas.investment import (
    InvestmentResponse,
    InvestmentListResponse,
    InvestmentUpdate,
)

router = APIRouter()


def _investment_to_response(inv: Investment) -> InvestmentResponse:
    """Convert Investment model to response schema with nested info."""
    response = InvestmentResponse.model_validate(inv)
    if inv.document:
        response.source_filename = inv.document.filename
        if inv.document.email:
            response.source_email_subject = inv.document.email.subject
    return response


@router.get("", response_model=InvestmentListResponse)
async def list_investments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
):
    """
    List investments with pagination, search, and sorting.
    """
    query = db.query(Investment).options(
        joinedload(Investment.document).joinedload(Document.email)
    )

    # Search across multiple fields
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Investment.investment_name.ilike(search_term),
                Investment.firm.ilike(search_term),
                Investment.strategy_description.ilike(search_term),
                Investment.leaders.ilike(search_term),
            )
        )

    # Get total count
    total = query.count()

    # Sorting
    sort_column = getattr(Investment, sort_by, Investment.created_at)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    # Pagination
    offset = (page - 1) * per_page
    investments = query.offset(offset).limit(per_page).all()

    return InvestmentListResponse(
        items=[_investment_to_response(inv) for inv in investments],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/export/csv")
async def export_csv(db: Session = Depends(get_db)):
    """
    Export all investments as CSV.
    """
    investments = db.query(Investment).options(
        joinedload(Investment.document).joinedload(Document.email)
    ).order_by(Investment.created_at.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Investment Name",
        "Firm",
        "Strategy Description",
        "Leaders/PM/CEO",
        "Management Fees",
        "Incentive Fees",
        "Liquidity/Lock",
        "Target Net Returns",
        "Source File",
        "Email Subject",
        "Extracted At",
    ])

    # Data rows
    for inv in investments:
        writer.writerow([
            inv.investment_name or "",
            inv.firm or "",
            inv.strategy_description or "",
            inv.leaders or "",
            inv.management_fees or "",
            inv.incentive_fees or "",
            inv.liquidity_lock or "",
            inv.target_net_returns or "",
            inv.document.filename if inv.document else "",
            inv.document.email.subject if inv.document and inv.document.email else "",
            inv.created_at.isoformat() if inv.created_at else "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=investments.csv"},
    )


@router.get("/{investment_id}", response_model=InvestmentResponse)
async def get_investment(
    investment_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a single investment by ID.
    """
    investment = db.query(Investment).options(
        joinedload(Investment.document).joinedload(Document.email)
    ).filter(Investment.id == investment_id).first()

    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    return _investment_to_response(investment)


@router.put("/{investment_id}", response_model=InvestmentResponse)
async def update_investment(
    investment_id: UUID,
    update: InvestmentUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an investment (for manual corrections).
    """
    investment = db.query(Investment).options(
        joinedload(Investment.document).joinedload(Document.email)
    ).filter(Investment.id == investment_id).first()

    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    # Update only provided fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(investment, field, value)

    db.commit()
    db.refresh(investment)

    return _investment_to_response(investment)
