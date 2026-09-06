from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.schemas.organization import OrganizationResponse, OrganizationUpdate

router = APIRouter()


@router.get("/current", response_model=OrganizationResponse)
def get_current_org_details(
    org: Organization = Depends(get_current_organization),
):
    """Retrieve details and configuration for the current authenticated organization."""
    return org


@router.patch("/current", response_model=OrganizationResponse)
def update_current_org_details(
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update profile settings (name, currency, timezone) for the current organization."""
    if data.name is not None:
        name_str = data.name.strip()
        if not name_str:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization name cannot be blank",
            )
        org.name = name_str

    if data.currency is not None:
        curr_str = data.currency.strip().upper()
        if len(curr_str) != 3:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Currency must be a 3-letter ISO code (e.g. INR, USD)",
            )
        org.currency = curr_str

    if data.timezone is not None:
        tz_str = data.timezone.strip()
        if not tz_str:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Timezone cannot be blank",
            )
        org.timezone = tz_str

    db.add(org)
    db.commit()
    db.refresh(org)
    return org

