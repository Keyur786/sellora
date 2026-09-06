from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.marketplace import MarketplaceAccount
from app.models.analytics import SyncJob
from app.schemas.marketplace import MarketplaceAccountCreate, MarketplaceAccountResponse, SyncTriggerResponse
from app.integrations.marketplaces.base import MockMarketplaceConnector

router = APIRouter()


@router.get("", response_model=List[MarketplaceAccountResponse])
def get_marketplace_accounts(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List all marketplace connections for the tenant."""
    accounts = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.organization_id == org.id)
        .all()
    )
    return [MarketplaceAccountResponse.model_validate(a) for a in accounts]


@router.post("/connect", response_model=MarketplaceAccountResponse, status_code=status.HTTP_201_CREATED)
def connect_marketplace_account(
    data: MarketplaceAccountCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Register or connect a marketplace account (Amazon India / Flipkart)."""
    account = MarketplaceAccount(
        organization_id=org.id,
        marketplace_type=data.marketplace_type.lower(),
        account_name=data.account_name,
        seller_id=data.seller_id,
        marketplace_id=data.marketplace_id,
        status="connected",
        last_synced_at=datetime.now(timezone.utc),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return MarketplaceAccountResponse.model_validate(account)


@router.post("/{account_id}/sync", response_model=SyncTriggerResponse)
async def trigger_marketplace_sync(
    account_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Trigger background synchronization for a marketplace account."""
    account = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.id == account_id, MarketplaceAccount.organization_id == org.id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marketplace account not found",
        )

    # Create SyncJob record
    job = SyncJob(
        organization_id=org.id,
        marketplace_account_id=account.id,
        job_type="all",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Run sync via MarketplaceConnector abstraction
    try:
        connector = MockMarketplaceConnector(marketplace_type=account.marketplace_type)
        orders = await connector.get_orders()
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.records_processed = len(orders)
        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = str(e)
        db.commit()

    return SyncTriggerResponse(
        job_id=job.id,
        status=job.status,
        message=f"Sync completed successfully. {job.records_processed} records synchronized.",
    )
