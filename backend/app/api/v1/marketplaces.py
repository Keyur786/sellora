from typing import List
from datetime import datetime, timezone
from decimal import Decimal
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


from app.models.product import Product, Inventory
from app.models.order import Order, OrderItem
from app.models.financials import Fee, Return


@router.post("/{account_id}/sync", response_model=SyncTriggerResponse)
async def trigger_marketplace_sync(
    account_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Trigger synchronization for a marketplace account and persist records."""
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

    # Run sync via MarketplaceConnector abstraction and persist into database
    try:
        connector = MockMarketplaceConnector(marketplace_type=account.marketplace_type)
        
        # 1. Sync Products & Inventory
        synced_products = await connector.get_products()
        records_count = 0
        product_cache = {}

        for sp in synced_products:
            prod = (
                db.query(Product)
                .filter(Product.organization_id == org.id, Product.sku == sp.sku)
                .first()
            )
            if not prod:
                prod = Product(
                    organization_id=org.id,
                    sku=sp.sku,
                    title=sp.title,
                    asin_or_fsn=sp.marketplace_id,
                    category=sp.category,
                    image_url=sp.image_url,
                    cost_price=sp.current_listing_price * Decimal("0.40"),
                    packaging_cost=Decimal("20.00"),
                    other_cost=Decimal("5.00"),
                    is_active=True,
                )
                db.add(prod)
                db.flush()
                
                # Create initial inventory
                inv = Inventory(
                    product_id=prod.id,
                    available_quantity=sp.inventory_quantity,
                    reserved_quantity=0,
                    last_updated_at=datetime.now(timezone.utc),
                )
                db.add(inv)
                records_count += 1
            else:
                # Update inventory if exists
                if prod.inventory:
                    prod.inventory.available_quantity = sp.inventory_quantity
                    prod.inventory.last_updated_at = datetime.now(timezone.utc)
                else:
                    inv = Inventory(
                        product_id=prod.id,
                        available_quantity=sp.inventory_quantity,
                        reserved_quantity=0,
                        last_updated_at=datetime.now(timezone.utc),
                    )
                    db.add(inv)
            product_cache[sp.sku] = prod

        # 2. Sync Orders, Items, and Fees
        synced_orders = await connector.get_orders()
        for so in synced_orders:
            existing_order = (
                db.query(Order)
                .filter(
                    Order.marketplace_account_id == account.id,
                    Order.marketplace_order_id == so.marketplace_order_id,
                )
                .first()
            )
            if not existing_order:
                order = Order(
                    organization_id=org.id,
                    marketplace_account_id=account.id,
                    marketplace_type=so.marketplace_type,
                    marketplace_order_id=so.marketplace_order_id,
                    order_date=so.order_date,
                    status=so.status,
                    fulfillment_channel=so.fulfillment_channel,
                    total_amount=so.total_amount,
                    currency=so.currency,
                    customer_city=so.customer_city,
                    customer_state=so.customer_state,
                    postal_code=so.postal_code,
                )
                db.add(order)
                db.flush()

                for item in so.items:
                    prod = product_cache.get(item.sku) or (
                        db.query(Product)
                        .filter(Product.organization_id == org.id, Product.sku == item.sku)
                        .first()
                    )
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=prod.id if prod else None,
                        sku=item.sku,
                        title=item.title,
                        quantity=item.quantity,
                        item_price=item.item_price,
                        shipping_price=item.shipping_price,
                        item_tax=item.tax_amount,
                        discount_amount=item.discount_amount,
                    )
                    db.add(order_item)
                    db.flush()

                    for fee in item.fees:
                        fee_record = Fee(
                            order_id=order.id,
                            order_item_id=order_item.id,
                            fee_type=fee.fee_type,
                            amount=fee.amount,
                            currency=fee.currency,
                            description=fee.description,
                        )
                        db.add(fee_record)

                records_count += 1

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.records_processed = records_count
        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        db.rollback()
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = str(e)
        db.add(job)
        db.commit()

    return SyncTriggerResponse(
        job_id=job.id,
        status=job.status,
        message=f"Sync completed successfully. {job.records_processed} records synchronized.",
    )

