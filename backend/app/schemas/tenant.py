from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserResponse(UserBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OrganizationBase(BaseModel):
    name: str
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"


class OrganizationResponse(OrganizationBase):
    id: str
    slug: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
