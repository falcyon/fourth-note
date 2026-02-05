from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any


class LeaderInfo(BaseModel):
    """Individual leader with optional LinkedIn profile."""
    name: str
    linkedin_url: Optional[str] = None


class InvestmentBase(BaseModel):
    investment_name: Optional[str] = None
    firm: Optional[str] = None
    strategy_description: Optional[str] = None
    leaders_json: Optional[List[LeaderInfo]] = None
    management_fees: Optional[str] = None
    incentive_fees: Optional[str] = None
    liquidity_lock: Optional[str] = None
    target_net_returns: Optional[str] = None


class InvestmentCreate(InvestmentBase):
    """For creating an investment manually (without a document)."""
    notes: Optional[str] = None


class InvestmentUpdate(BaseModel):
    """For updating investment fields."""
    investment_name: Optional[str] = None
    firm: Optional[str] = None
    strategy_description: Optional[str] = None
    leaders_json: Optional[List[LeaderInfo]] = None
    management_fees: Optional[str] = None
    incentive_fees: Optional[str] = None
    liquidity_lock: Optional[str] = None
    target_net_returns: Optional[str] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None


# Field attribution schemas
class FieldAttribution(BaseModel):
    """Attribution info for a single field value."""
    value: Optional[Any] = None  # Can be string or JSON (for leaders_json)
    source_type: str
    source_id: Optional[UUID] = None
    source_name: Optional[str] = None
    confidence: str = "medium"
    extracted_at: datetime

    class Config:
        from_attributes = True


class FieldWithHistory(FieldAttribution):
    """Field attribution with all historical values."""
    all_values: List[FieldAttribution] = []


# Document reference schemas
class InvestmentDocumentResponse(BaseModel):
    """Document linked to an investment."""
    id: UUID
    document_id: UUID
    filename: str
    relationship: str = "source"
    has_pdf: bool = False
    has_markdown: bool = False
    added_at: datetime

    class Config:
        from_attributes = True


# Main investment response schemas
class InvestmentResponse(InvestmentBase):
    """Basic investment response for list views."""
    id: UUID
    notes: Optional[str] = None
    is_archived: bool = False
    source_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvestmentDetailResponse(InvestmentResponse):
    """Detailed investment response with field attributions and documents."""
    field_attributions: Optional[Dict[str, FieldWithHistory]] = None
    documents: List[InvestmentDocumentResponse] = []

    class Config:
        from_attributes = True


class InvestmentListResponse(BaseModel):
    """Paginated list of investments."""
    items: List[InvestmentResponse]
    total: int
    page: int
    per_page: int
    pages: int
