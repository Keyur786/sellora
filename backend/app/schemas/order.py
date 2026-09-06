from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class FeeResponse(BaseModel):
    id: str
    fee_type: str
    amount: Decimal
    currency: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    id: str
    sku: str
    title: str
    quantity: int
    item_price: Decimal
    shipping_price: Decimal
    item_tax: Decimal
    shipping_tax: Decimal
    discount_amount: Decimal
    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: str
    marketplace_type: str
    marketplace_order_id: str
    order_date: datetime
    status: str
    fulfillment_channel: Optional[str] = None
    total_amount: Decimal
    currency: str
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None
    items: List[OrderItemResponse] = []
    fees: List[FeeResponse] = []
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total_count: int
    page: int
    page_size: int
