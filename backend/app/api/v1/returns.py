from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.order import Order
from app.models.financials import Return
from app.services.returns_engine import ReturnsEngine
from app.schemas.returns import ReturnsAnalyticsResponse, ReturnResponse

router = APIRouter()


@router.get("/analytics", response_model=ReturnsAnalyticsResponse)
def get_returns_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve SKU return rates, Courier RTO financial loss, and reason breakdowns."""
    data = ReturnsEngine.get_returns_analytics(db=db, org_id=org.id, days=days)
    return ReturnsAnalyticsResponse(**data)


@router.get("", response_model=List[ReturnResponse])
def list_returns(
    return_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List detailed return and RTO ledger entries for the tenant."""
    query = (
        db.query(Return)
        .join(Order, Return.order_id == Order.id)
        .filter(Order.organization_id == org.id)
        .order_by(Return.return_date.desc())
    )
    if return_type:
        query = query.filter(Return.return_type.ilike(f"%{return_type}%"))

    returns = query.limit(limit).all()
    return [ReturnResponse.model_validate(r) for r in returns]

