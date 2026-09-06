from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.order import Order
from app.api.v1.profit import get_profit_summary, get_products_profitability
from app.schemas.order import OrderResponse

router = APIRouter()


@router.get("")
def get_dashboard_data(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
) -> Dict[str, Any]:
    """Aggregate top-level KPI metrics, top products, and recent orders for the dashboard."""
    # 1. Summary
    summary = get_profit_summary(days=days, db=db, org=org)

    # 2. Top Profitable Products
    products_profit = get_products_profitability(days=days, db=db, org=org)
    top_products = products_profit[:5]

    # 3. Recent 5 Orders
    recent_orders_db = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.fees))
        .filter(Order.organization_id == org.id)
        .order_by(Order.order_date.desc())
        .limit(5)
        .all()
    )
    recent_orders = [OrderResponse.model_validate(o) for o in recent_orders_db]

    return {
        "organization": {
            "id": org.id,
            "name": org.name,
            "currency": org.currency,
        },
        "summary": summary,
        "top_products": top_products,
        "recent_orders": recent_orders,
    }
