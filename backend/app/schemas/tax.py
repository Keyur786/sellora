from typing import List
from pydantic import BaseModel


class MonthlyTaxItem(BaseModel):
    month: str
    orders_count: int
    gross_sales: str
    output_gst: str
    marketplace_fees: str
    claimable_itc: str
    tcs_gst: str
    tds_194o: str


class TaxReconciliationResponse(BaseModel):
    currency: str = "INR"
    period_days: int
    gross_marketplace_sales: str
    output_gst_collected: str
    total_marketplace_fees: str
    claimable_itc_gst: str
    tcs_gst_withheld: str
    tds_income_tax_194o: str
    estimated_net_gst_payable: str
    monthly_breakdown: List[MonthlyTaxItem]

