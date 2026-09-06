from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class ProfitSummaryResponse(BaseModel):
    currency: str = "INR"
    total_sales: Decimal
    total_orders: int
    units_sold: int
    net_profit: Decimal
    profit_margin_percentage: Decimal
    product_costs: Decimal
    packaging_costs: Decimal
    marketplace_fees: Decimal
    shipping_costs: Decimal
    advertising_costs: Decimal
    returns_costs: Decimal
    other_expenses: Decimal


class ProductProfitItem(BaseModel):
    product_id: str
    sku: str
    title: str
    image_url: Optional[str] = None
    units_sold: int
    gross_sales: Decimal
    product_cost: Decimal
    packaging_cost: Decimal
    marketplace_fees: Decimal
    shipping_cost: Decimal
    advertising_cost: Decimal
    returns_cost: Decimal
    net_profit: Decimal
    profit_margin_percentage: Decimal


class ProfitTrendPoint(BaseModel):
    date: str
    sales: Decimal
    net_profit: Decimal
    marketplace_fees: Decimal
    advertising: Decimal
