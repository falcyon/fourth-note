from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any, Dict


class InvestmentBase(BaseModel):
    investment_name: Optional[str] = None
    firm: Optional[str] = None
    strategy_description: Optional[str] = None
    leaders: Optional[str] = None
    management_fees: Optional[str] = None
    incentive_fees: Optional[str] = None
    liquidity_lock: Optional[str] = None
    target_net_returns: Optional[str] = None


class InvestmentCreate(InvestmentBase):
    document_id: UUID
    raw_extraction_json: Optional[Dict[str, Any]] = None


class InvestmentUpdate(BaseModel):
    investment_name: Optional[str] = None
    firm: Optional[str] = None
    strategy_description: Optional[str] = None
    leaders: Optional[str] = None
    management_fees: Optional[str] = None
    incentive_fees: Optional[str] = None
    liquidity_lock: Optional[str] = None
    target_net_returns: Optional[str] = None


class InvestmentResponse(InvestmentBase):
    id: UUID
    document_id: UUID
    raw_extraction_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    # Nested info for display
    source_filename: Optional[str] = None
    source_email_subject: Optional[str] = None

    class Config:
        from_attributes = True


class InvestmentListResponse(BaseModel):
    items: List[InvestmentResponse]
    total: int
    page: int
    per_page: int
    pages: int
