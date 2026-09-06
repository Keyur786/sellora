from typing import List, Optional
from pydantic import BaseModel


class ImportResultResponse(BaseModel):
    success: bool = True
    message: str
    rows_parsed: int
    orders_imported: int
    orders_updated: int = 0
    refunds_imported: int
    fees_extracted: int
    total_sales_value: str
    skus_identified: int


class COGSImportResponse(BaseModel):
    success: bool = True
    message: str
    rows_processed: int
    products_updated: int
    products_created: int
    updated_skus: List[str]
