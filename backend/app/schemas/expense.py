from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExpenseBase(BaseModel):
    category: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "INR"
    date: date
    description: Optional[str] = None
    vendor_name: Optional[str] = None
    payment_method: Optional[str] = "Bank Transfer"
    is_recurring: bool = False


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    date: Optional[date] = None
    description: Optional[str] = None
    vendor_name: Optional[str] = None
    payment_method: Optional[str] = None
    is_recurring: Optional[bool] = None


class ExpenseResponse(ExpenseBase):
    id: str
    organization_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ExpenseCategorySummary(BaseModel):
    category: str
    total_amount: Decimal
    percentage: float
    count: int


class ExpenseSummaryResponse(BaseModel):
    currency: str = "INR"
    total_expenses: Decimal
    period_days: int
    categories: List[ExpenseCategorySummary]

