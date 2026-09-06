from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MarketplaceAccountCreate(BaseModel):
    marketplace_type: str  # amazon, flipkart
    account_name: str
    seller_id: str
    marketplace_id: Optional[str] = None


class MarketplaceAccountResponse(BaseModel):
    id: str
    organization_id: str
    marketplace_type: str
    account_name: str
    seller_id: str
    marketplace_id: Optional[str] = None
    status: str
    is_active: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SyncTriggerResponse(BaseModel):
    job_id: str
    status: str
    message: str
