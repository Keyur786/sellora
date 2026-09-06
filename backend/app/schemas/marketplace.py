from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MarketplaceAccountCreate(BaseModel):
    marketplace_type: str  # amazon, flipkart
    account_name: str
    seller_id: str
    marketplace_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None


class MarketplaceCredentialsUpdate(BaseModel):
    seller_id: Optional[str] = None
    marketplace_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None


class MarketplaceAccountResponse(BaseModel):
    id: str
    organization_id: str
    marketplace_type: str
    account_name: str
    seller_id: str
    marketplace_id: Optional[str] = None
    status: str
    is_active: bool
    has_credentials: bool = False
    connection_mode: str = "sandbox"  # "live" or "sandbox"
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SyncTriggerResponse(BaseModel):
    job_id: str
    status: str
    message: str


class MarketplaceTestConnectionRequest(BaseModel):
    marketplace_type: str = "amazon"
    seller_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    marketplace_id: Optional[str] = "A21TJRUUN4KGV"


class MarketplaceTestConnectionResponse(BaseModel):
    success: bool
    connection_mode: str  # "live" or "sandbox"
    message: str
    marketplace_name: str = "Amazon India"
    seller_id: Optional[str] = None
    checked_at: datetime = datetime.now()
