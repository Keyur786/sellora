from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ReturnReasonItem(BaseModel):
    reason: str
    count: int
    percentage: float


class SkuReturnItem(BaseModel):
    sku: str
    title: str
    units_sold: int
    returns_count: int
    rto_count: int
    customer_return_count: int
    return_rate_percentage: float
    total_loss: str
    risk_level: str


class ReturnsAnalyticsResponse(BaseModel):
    period_days: int
    total_units_sold: int
    total_returns: int
    overall_return_rate_percentage: str
    courier_rto_count: int
    courier_rto_rate_percentage: str
    customer_return_count: int
    total_financial_loss: str
    shipping_loss: str
    packaging_loss: str
    damaged_product_loss: str
    reasons_breakdown: List[ReturnReasonItem]
    sku_ranking: List[SkuReturnItem]


class ReturnResponse(BaseModel):
    id: str
    order_id: str
    sku: Optional[str] = None
    return_date: datetime
    return_reason: Optional[str] = None
    return_type: str
    condition: str
    status: str
    shipping_loss: Decimal
    packaging_loss: Decimal
    product_damage_loss: Decimal
    total_loss: Decimal
    model_config = ConfigDict(from_attributes=True)

