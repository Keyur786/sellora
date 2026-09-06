from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str
    title: str
    asin_or_fsn: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    packaging_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    other_cost: Decimal = Field(default=Decimal("0.00"), ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    packaging_cost: Optional[Decimal] = Field(default=None, ge=0)
    other_cost: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: str
    organization_id: str
    is_active: bool
    created_at: datetime
    available_stock: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
