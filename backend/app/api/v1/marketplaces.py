import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.marketplace import MarketplaceAccount
from app.models.analytics import SyncJob
from app.models.product import Product, Inventory
from app.models.order import Order, OrderItem
from app.models.financials import Fee, Return, Settlement
from app.schemas.marketplace import (
    MarketplaceAccountCreate,
    MarketplaceAccountResponse,
    MarketplaceCredentialsUpdate,
    MarketplaceTestConnectionRequest,
    MarketplaceTestConnectionResponse,
    SyncTriggerResponse,
)
from app.integrations.marketplaces.base import MockMarketplaceConnector
from app.integrations.marketplaces.amazon.sp_api_connector import AmazonSPAPIConnector
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_account_credentials(account: MarketplaceAccount) -> dict:
    """Extract credentials from account record or fall back to system settings."""
    creds = {}
    if account.credentials_encrypted:
        try:
            creds = json.loads(account.credentials_encrypted)
        except Exception:
            pass

    if account.marketplace_type == "amazon":
        if not creds.get("client_id") and settings.SP_API_CLIENT_ID:
            creds["client_id"] = settings.SP_API_CLIENT_ID
        if not creds.get("client_secret") and settings.SP_API_CLIENT_SECRET:
            creds["client_secret"] = settings.SP_API_CLIENT_SECRET
        if not creds.get("refresh_token") and settings.SP_API_REFRESH_TOKEN:
            creds["refresh_token"] = settings.SP_API_REFRESH_TOKEN
        if not creds.get("seller_id") and settings.SP_API_SELLER_ID:
            creds["seller_id"] = settings.SP_API_SELLER_ID
        if not creds.get("marketplace_id"):
            creds["marketplace_id"] = settings.SP_API_MARKETPLACE_ID

    return creds


def _build_account_response(account: MarketplaceAccount) -> MarketplaceAccountResponse:
    creds = _get_account_credentials(account)
    has_creds = bool(creds.get("client_id") and creds.get("client_secret") and creds.get("refresh_token"))
    is_live = has_creds and not creds.get("refresh_token", "").startswith("mock_")
    mode = "live" if is_live else "sandbox"

    res = MarketplaceAccountResponse.model_validate(account)
    res.has_credentials = has_creds
    res.connection_mode = mode
    return res


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
    if not accounts:
        # Seed default Amazon India and Flipkart accounts for initial display
        amz = MarketplaceAccount(
            organization_id=org.id,
            marketplace_type="amazon",
            account_name="Amazon India",
            seller_id="A2QWR8429184",
            marketplace_id="A21TJRUUN4KGV",
            status="connected",
            last_synced_at=datetime.now(timezone.utc),
        )
        fk = MarketplaceAccount(
            organization_id=org.id,
            marketplace_type="flipkart",
            account_name="Flipkart Seller Hub",
            seller_id="FLIPKART_SELLER_881",
            marketplace_id="FLIPKART_IN",
            status="connected",
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(amz)
        db.add(fk)
        db.commit()
        accounts = [amz, fk]

    return [_build_account_response(a) for a in accounts]


@router.post("/connect", response_model=MarketplaceAccountResponse, status_code=status.HTTP_201_CREATED)
def connect_marketplace_account(
    data: MarketplaceAccountCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Register or connect a marketplace account with credentials."""
    existing = (
        db.query(MarketplaceAccount)
        .filter(
            MarketplaceAccount.organization_id == org.id,
            MarketplaceAccount.marketplace_type == data.marketplace_type.lower(),
        )
        .first()
    )

    creds_payload = {}
    if data.client_id or data.client_secret or data.refresh_token:
        creds_payload = {
            "client_id": data.client_id or "",
            "client_secret": data.client_secret or "",
            "refresh_token": data.refresh_token or "",
            "seller_id": data.seller_id,
            "marketplace_id": data.marketplace_id or "A21TJRUUN4KGV",
        }

    if existing:
        existing.account_name = data.account_name
        existing.seller_id = data.seller_id
        if data.marketplace_id:
            existing.marketplace_id = data.marketplace_id
        if creds_payload:
            existing.credentials_encrypted = json.dumps(creds_payload)
        existing.status = "connected"
        existing.last_synced_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return _build_account_response(existing)

    account = MarketplaceAccount(
        organization_id=org.id,
        marketplace_type=data.marketplace_type.lower(),
        account_name=data.account_name,
        seller_id=data.seller_id,
        marketplace_id=data.marketplace_id or "A21TJRUUN4KGV",
        credentials_encrypted=json.dumps(creds_payload) if creds_payload else None,
        status="connected",
        last_synced_at=datetime.now(timezone.utc),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return _build_account_response(account)


@router.put("/{account_id}/credentials", response_model=MarketplaceAccountResponse)
def update_marketplace_credentials(
    account_id: str,
    data: MarketplaceCredentialsUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update SP-API credentials for an existing marketplace account."""
    account = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.organization_id == org.id)
        .filter((MarketplaceAccount.id == account_id) | (MarketplaceAccount.marketplace_type == account_id.lower()))
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")

    creds = _get_account_credentials(account)
    if data.client_id is not None:
        creds["client_id"] = data.client_id
    if data.client_secret is not None:
        creds["client_secret"] = data.client_secret
    if data.refresh_token is not None:
        creds["refresh_token"] = data.refresh_token
    if data.seller_id is not None:
        account.seller_id = data.seller_id
        creds["seller_id"] = data.seller_id
    if data.marketplace_id is not None:
        account.marketplace_id = data.marketplace_id
        creds["marketplace_id"] = data.marketplace_id

    account.credentials_encrypted = json.dumps(creds)
    account.status = "connected"
    db.commit()
    db.refresh(account)
    return _build_account_response(account)


@router.post("/amazon/test-connection", response_model=MarketplaceTestConnectionResponse)
async def test_amazon_connection(
    data: MarketplaceTestConnectionRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Test Amazon SP-API credentials connectivity (Login with Amazon and live ping)."""
    # 1. Use provided credentials or lookup from tenant's connected Amazon account
    client_id = data.client_id
    client_secret = data.client_secret
    refresh_token = data.refresh_token

    if not (client_id and client_secret and refresh_token):
        account = (
            db.query(MarketplaceAccount)
            .filter(MarketplaceAccount.organization_id == org.id, MarketplaceAccount.marketplace_type == "amazon")
            .first()
        )
        if account:
            creds = _get_account_credentials(account)
            client_id = client_id or creds.get("client_id")
            client_secret = client_secret or creds.get("client_secret")
            refresh_token = refresh_token or creds.get("refresh_token")

    # 2. Fallback to settings
    client_id = client_id or settings.SP_API_CLIENT_ID
    client_secret = client_secret or settings.SP_API_CLIENT_SECRET
    refresh_token = refresh_token or settings.SP_API_REFRESH_TOKEN

    client = AmazonSPAPIClient(
        client_id=client_id or "",
        client_secret=client_secret or "",
        refresh_token=refresh_token or "",
    )

    res = await client.test_connection()
    return MarketplaceTestConnectionResponse(
        success=res.get("success", False),
        connection_mode=res.get("connection_mode", "sandbox"),
        message=res.get("message", "Test completed."),
        marketplace_name="Amazon India",
        seller_id=data.seller_id or settings.SP_API_SELLER_ID or "A2QWR8429184",
        checked_at=datetime.now(timezone.utc),
    )


@router.post("/{account_id}/sync", response_model=SyncTriggerResponse)
async def trigger_marketplace_sync(
    account_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Trigger synchronization for a marketplace account and persist records."""
    account = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.organization_id == org.id)
        .filter((MarketplaceAccount.id == account_id) | (MarketplaceAccount.marketplace_type == account_id.lower()))
        .first()
    )
    if not account:
        # Auto-provision if triggered via friendly name
        m_type = account_id.lower()
        if m_type in ("amazon", "flipkart"):
            account = MarketplaceAccount(
                organization_id=org.id,
                marketplace_type=m_type,
                account_name="Amazon India" if m_type == "amazon" else "Flipkart",
                seller_id="A2QWR8429184" if m_type == "amazon" else "FLIPKART_SELLER_881",
                marketplace_id="A21TJRUUN4KGV" if m_type == "amazon" else "FLIPKART_IN",
                status="connected",
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        else:
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

    # Initialize connector based on marketplace type and configured credentials
    try:
        creds = _get_account_credentials(account)
        is_live_amazon = (
            account.marketplace_type == "amazon"
            and bool(creds.get("client_id") and creds.get("client_secret") and creds.get("refresh_token"))
            and not creds.get("refresh_token", "").startswith("mock_")
        )

        if account.marketplace_type == "amazon":
            connector = AmazonSPAPIConnector(
                client_id=creds.get("client_id", ""),
                client_secret=creds.get("client_secret", ""),
                refresh_token=creds.get("refresh_token", ""),
                seller_id=account.seller_id,
                marketplace_id=account.marketplace_id or "A21TJRUUN4KGV",
                mock_mode=not is_live_amazon,
            )
        else:
            connector = MockMarketplaceConnector(marketplace_type=account.marketplace_type)

        records_count = 0
        product_cache = {}

        # 1. Sync Products & Live Inventory
        synced_products = await connector.get_products()
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

                inv = Inventory(
                    product_id=prod.id,
                    available_quantity=sp.inventory_quantity,
                    reserved_quantity=0,
                    last_updated_at=datetime.now(timezone.utc),
                )
                db.add(inv)
                records_count += 1
            else:
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

        # 2. Sync Orders, Order Items, and Itemized Fees
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

        # 3. Sync Customer Returns and Courier RTOs
        synced_returns = await connector.get_returns()
        for sr in synced_returns:
            existing_ret = (
                db.query(Return)
                .join(Order, Return.order_id == Order.id)
                .filter(Order.marketplace_order_id == sr.marketplace_order_id, Return.sku == sr.sku)
                .first()
            )
            if not existing_ret:
                parent_order = (
                    db.query(Order)
                    .filter(Order.marketplace_order_id == sr.marketplace_order_id)
                    .first()
                )
                if parent_order:
                    ret_obj = Return(
                        order_id=parent_order.id,
                        sku=sr.sku,
                        return_date=sr.return_date,
                        return_reason=sr.reason,
                        return_type=sr.return_type,
                        condition="damaged" if sr.status == "Damaged" else "sellable",
                        status=sr.status,
                        restock_fee=Decimal("0.00"),
                    )
                    db.add(ret_obj)
                    records_count += 1

        # 4. Sync Settlements
        now = datetime.now(timezone.utc)
        settlements = await connector.get_settlements(
            start_date=now - timezone.utc.utcoffset(now),
            end_date=now,
        )
        for st in settlements:
            existing_settle = (
                db.query(Settlement)
                .filter(
                    Settlement.organization_id == org.id,
                    Settlement.settlement_id == st.settlement_id,
                )
                .first()
            )
            if not existing_settle:
                s_record = Settlement(
                    organization_id=org.id,
                    marketplace_account_id=account.id,
                    settlement_id=st.settlement_id,
                    period_start=st.period_start,
                    period_end=st.period_end,
                    total_amount=st.total_amount,
                    currency=st.currency,
                )
                db.add(s_record)
                records_count += 1

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.records_processed = records_count
        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()

        mode_msg = "Live SP-API" if is_live_amazon else "Developer Sandbox"
        return SyncTriggerResponse(
            job_id=job.id,
            status=job.status,
            message=f"Sync completed successfully in {mode_msg} mode. {job.records_processed} records synchronized.",
        )
    except Exception as e:
        db.rollback()
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = str(e)
        db.add(job)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Marketplace synchronization failed: {str(e)}",
        )
