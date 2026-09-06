from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.order import Order
from app.schemas.order import OrderListResponse, OrderResponse

router = APIRouter()


@router.get("", response_model=OrderListResponse)
def get_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    marketplace_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve tenant's orders with full marketplace fee and item details."""
    query = (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.fees),
        )
        .filter(Order.organization_id == org.id)
    )

    if marketplace_type:
        query = query.filter(Order.marketplace_type == marketplace_type.lower())
    if status:
        query = query.filter(Order.status == status)

    total_count = query.count()
    offset = (page - 1) * page_size
    orders = query.order_date.desc() if hasattr(query, 'order_date') else query.order_by(Order.order_date.desc()).offset(offset).limit(page_size).all()

    return OrderListResponse(
        orders=[OrderResponse.model_validate(o) for o in orders],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve complete financial drill-down and itemized fees for a specific order."""
    order = (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.fees),
        )
        .filter(Order.id == order_id, Order.organization_id == org.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return OrderResponse.model_validate(order)

