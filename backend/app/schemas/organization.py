from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    name: str
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    id: str
    slug: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

