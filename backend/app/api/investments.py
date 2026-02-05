"""Investment API routes."""
import csv
import io
from pathlib import Path
from typing import Optional, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import sqlalchemy as sa
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.investment import Investment
from app.models.investment_document import InvestmentDocument
from app.models.field_value import FieldValue
from app.models.user import User
from app.middleware.auth import get_current_user
from app.schemas.investment import (
    InvestmentResponse,
    InvestmentDetailResponse,
    InvestmentListResponse,
    InvestmentUpdate,
    FieldAttribution,
    FieldWithHistory,
    InvestmentDocumentResponse,
)

router = APIRouter()


def _build_field_attributions(investment: Investment, db: Session) -> Dict[str, FieldWithHistory]:
    """Build field attributions dict from field_values."""
    attributions = {}

    # Get all field values for this investment
    field_values = db.query(FieldValue).filter(
        FieldValue.investment_id == investment.id
    ).order_by(FieldValue.extracted_at.desc()).all()

    # Group by field_name
    field_groups: Dict[str, list] = {}
    for fv in field_values:
        if fv.field_name not in field_groups:
            field_groups[fv.field_name] = []
        field_groups[fv.field_name].append(fv)

    # Build response
    for field_name, values in field_groups.items():
        # Current value is the one with is_current=True, or the most recent
        current = next((v for v in values if v.is_current), values[0] if values else None)

        if current:
            all_values = [
                FieldAttribution(
                    value=v.field_value,
                    source_type=v.source_type,
                    source_id=v.source_id,
                    source_name=v.source_name,
                    confidence=v.confidence or "medium",
                    extracted_at=v.extracted_at,
                )
                for v in values
            ]

            attributions[field_name] = FieldWithHistory(
                value=current.field_value,
                source_type=current.source_type,
                source_id=current.source_id,
                source_name=current.source_name,
                confidence=current.confidence or "medium",
                extracted_at=current.extracted_at,
                all_values=all_values,
            )

    return attributions


def _build_documents_list(investment: Investment, db: Session) -> list:
    """Build list of linked documents."""
    documents = []

    inv_docs = db.query(InvestmentDocument).filter(
        InvestmentDocument.investment_id == investment.id
    ).options(joinedload(InvestmentDocument.document)).all()

    for inv_doc in inv_docs:
        doc = inv_doc.document
        if doc:
            has_pdf = bool(doc.file_path and Path(doc.file_path).exists())
            has_markdown = bool(doc.markdown_file_path and Path(doc.markdown_file_path).exists())

            documents.append(InvestmentDocumentResponse(
                id=inv_doc.id,
                document_id=doc.id,
                filename=doc.filename,
                relationship=inv_doc.relationship_type or "source",
                has_pdf=has_pdf,
                has_markdown=has_markdown,
                added_at=inv_doc.added_at,
            ))

    return documents


def _investment_to_response(inv: Investment) -> InvestmentResponse:
    """Convert Investment model to basic response schema."""
    return InvestmentResponse(
        id=inv.id,
        investment_name=inv.investment_name,
        firm=inv.firm,
        strategy_description=inv.strategy_description,
        leaders_json=inv.leaders_json,
        management_fees=inv.management_fees,
        incentive_fees=inv.incentive_fees,
        liquidity_lock=inv.liquidity_lock,
        target_net_returns=inv.target_net_returns,
        notes=inv.notes,
        is_archived=inv.is_archived or False,
        source_count=inv.source_count,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
    )


@router.get("", response_model=InvestmentListResponse)
async def list_investments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List investments with pagination, search, and sorting.
    Only returns investments belonging to the current user.
    """
    query = db.query(Investment).filter(Investment.user_id == current_user.id)

    # Filter out archived by default
    if not include_archived:
        query = query.filter(Investment.is_archived == False)

    # Search across multiple fields
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Investment.investment_name.ilike(search_term),
                Investment.firm.ilike(search_term),
                Investment.strategy_description.ilike(search_term),
                Investment.leaders_json.cast(sa.Text).ilike(search_term),
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
async def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export all investments as CSV.
    Only exports investments belonging to the current user.
    """
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id,
        Investment.is_archived == False
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
        "Sources",
        "Extracted At",
    ])

    # Data rows
    for inv in investments:
        # Format leaders from JSON: "Name (LinkedIn)" or just "Name"
        leaders_str = ""
        if inv.leaders_json:
            leader_parts = []
            for leader in inv.leaders_json:
                if leader.get("linkedin_url"):
                    leader_parts.append(f"{leader['name']} ({leader['linkedin_url']})")
                else:
                    leader_parts.append(leader.get("name", ""))
            leaders_str = " | ".join(leader_parts)

        writer.writerow([
            inv.investment_name or "",
            inv.firm or "",
            inv.strategy_description or "",
            leaders_str,
            inv.management_fees or "",
            inv.incentive_fees or "",
            inv.liquidity_lock or "",
            inv.target_net_returns or "",
            inv.source_count,
            inv.created_at.isoformat() if inv.created_at else "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=investments.csv"},
    )


@router.get("/{investment_id}", response_model=InvestmentDetailResponse)
async def get_investment(
    investment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single investment by ID with full details.
    Includes field attributions and linked documents.
    Only returns investments belonging to the current user.
    """
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()

    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    # Build field attributions and documents
    field_attributions = _build_field_attributions(investment, db)
    documents = _build_documents_list(investment, db)

    return InvestmentDetailResponse(
        id=investment.id,
        investment_name=investment.investment_name,
        firm=investment.firm,
        strategy_description=investment.strategy_description,
        leaders_json=investment.leaders_json,
        management_fees=investment.management_fees,
        incentive_fees=investment.incentive_fees,
        liquidity_lock=investment.liquidity_lock,
        target_net_returns=investment.target_net_returns,
        notes=investment.notes,
        is_archived=investment.is_archived or False,
        source_count=investment.source_count,
        created_at=investment.created_at,
        updated_at=investment.updated_at,
        field_attributions=field_attributions,
        documents=documents,
    )


@router.put("/{investment_id}", response_model=InvestmentDetailResponse)
async def update_investment(
    investment_id: UUID,
    update: InvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an investment (for manual corrections).
    Creates field_values with source_type='manual' for tracking.
    Only updates investments belonging to the current user.
    """
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == current_user.id
    ).first()

    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    # Update only provided fields
    update_data = update.model_dump(exclude_unset=True)

    # Fields that should create field_values
    tracked_fields = {
        "investment_name", "firm", "strategy_description", "leaders_json",
        "management_fees", "incentive_fees", "liquidity_lock", "target_net_returns"
    }

    for field, value in update_data.items():
        old_value = getattr(investment, field)

        # Only create field_value if it's a tracked field and value changed
        if field in tracked_fields and value != old_value:
            # Mark existing current values as not current
            db.query(FieldValue).filter(
                FieldValue.investment_id == investment.id,
                FieldValue.field_name == field,
                FieldValue.is_current == True
            ).update({"is_current": False})

            # Serialize JSON fields to string for storage
            import json
            stored_value = (
                json.dumps(value) if field == "leaders_json" and isinstance(value, list)
                else str(value) if value else None
            )

            # Create new field value with manual source
            fv = FieldValue(
                investment_id=investment.id,
                field_name=field,
                field_value=stored_value,
                source_type="manual",
                source_name="Manual Edit",
                is_current=True,
                confidence="verified",  # Manual edits are verified
            )
            db.add(fv)

        # Update denormalized field
        setattr(investment, field, value)

    db.commit()
    db.refresh(investment)

    # Build response with updated attributions
    field_attributions = _build_field_attributions(investment, db)
    documents = _build_documents_list(investment, db)

    return InvestmentDetailResponse(
        id=investment.id,
        investment_name=investment.investment_name,
        firm=investment.firm,
        strategy_description=investment.strategy_description,
        leaders_json=investment.leaders_json,
        management_fees=investment.management_fees,
        incentive_fees=investment.incentive_fees,
        liquidity_lock=investment.liquidity_lock,
        target_net_returns=investment.target_net_returns,
        notes=investment.notes,
        is_archived=investment.is_archived or False,
        source_count=investment.source_count,
        created_at=investment.created_at,
        updated_at=investment.updated_at,
        field_attributions=field_attributions,
        documents=documents,
    )
