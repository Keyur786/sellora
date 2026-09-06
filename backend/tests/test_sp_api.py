import pytest
from decimal import Decimal
from starlette.testclient import TestClient
from app.main import app
from app.integrations.marketplaces.amazon.auth import AmazonLWAAuth
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient
from app.integrations.marketplaces.amazon.sp_api_connector import AmazonSPAPIConnector
from app.integrations.marketplaces.amazon.catalog import AmazonCatalogAPI
from app.integrations.marketplaces.amazon.inventory import AmazonFBAInventoryAPI
from app.integrations.marketplaces.amazon.reports import AmazonReportsAPI
from app.integrations.marketplaces.base import StandardOrder, StandardProduct, StandardSettlement, StandardReturn


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_amazon_lwa_auth():
    auth = AmazonLWAAuth(client_id="mock_client_123", client_secret="mock_secret_456")
    url = auth.get_authorization_url(app_id="amzn_app_789", state="state_random_123")
    assert "sellercentral.amazon.in" in url
    assert "application_id=amzn_app_789" in url

    # Mock exchange
    tokens = await auth.exchange_code_for_tokens("test_code_123")
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Validate credentials
    val = await auth.validate_credentials("mock_refresh_token_123")
    assert val["valid"] is True
    assert val["mode"] == "sandbox"


@pytest.mark.asyncio
async def test_amazon_sp_api_connector():
    connector = AmazonSPAPIConnector(mock_mode=True)
    
    # 1. Orders
    orders = await connector.get_orders()
    assert len(orders) > 0
    first = orders[0]
    assert isinstance(first, StandardOrder)
    assert first.marketplace_type == "amazon"
    assert first.total_amount > Decimal("0.00")
    assert len(first.items) > 0
    assert first.items[0].sku == "CU-BOTTLE-1000ML"

    # Verify fees extracted from financialEvents
    fees = first.items[0].fees
    assert len(fees) > 0
    fee_types = [f.fee_type for f in fees]
    assert "Commission" in fee_types
    assert "FixedClosingFee" in fee_types
    assert "WeightHandlingFee" in fee_types

    # 2. Products and live inventory
    products = await connector.get_products()
    assert len(products) > 0
    assert isinstance(products[0], StandardProduct)
    assert products[0].inventory_quantity > 0

    # 3. Fees for order
    order_fees = await connector.get_fees(first.marketplace_order_id)
    assert len(order_fees) > 0

    # 4. Settlements
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    settlements = await connector.get_settlements(now - timedelta(days=30), now)
    assert len(settlements) > 0
    assert isinstance(settlements[0], StandardSettlement)
    assert settlements[0].total_amount > Decimal("0.00")

    # 5. Returns
    returns = await connector.get_returns()
    assert len(returns) > 0
    assert isinstance(returns[0], StandardReturn)
    assert returns[0].sku in ("CU-BOTTLE-1000ML", "AUDIO-AIR-PODS-PRO")


@pytest.mark.asyncio
async def test_amazon_sub_apis():
    sp_client = AmazonSPAPIClient(mock_mode=True)

    # Catalog API
    cat_api = AmazonCatalogAPI(sp_client)
    item = await cat_api.get_catalog_item("B08N5WRWNW")
    assert "items" in item or "summaries" in item

    # Inventory API
    inv_api = AmazonFBAInventoryAPI(sp_client)
    inv = await inv_api.get_inventory_summaries()
    assert len(inv) > 0
    assert inv[0]["sellerSku"] == "CU-BOTTLE-1000ML"

    # Reports API
    rep_api = AmazonReportsAPI(sp_client)
    data = await rep_api.download_report_data("mock-report")
    assert len(data) > 0
    assert "order-id" in data[0]


def test_marketplace_api_endpoints(client):
    # 1. List accounts
    res_list = client.get("/api/v1/marketplaces")
    assert res_list.status_code == 200
    accounts = res_list.json()
    assert len(accounts) >= 2

    # 2. Test connection endpoint
    res_test = client.post(
        "/api/v1/marketplaces/amazon/test-connection",
        json={
            "marketplace_type": "amazon",
            "client_id": "mock_client",
            "client_secret": "mock_secret",
            "refresh_token": "mock_token",
            "seller_id": "A2QWR8429184",
        },
    )
    assert res_test.status_code == 200
    test_data = res_test.json()
    assert test_data["success"] is True
    assert test_data["connection_mode"] == "sandbox"

    # 3. Update credentials endpoint
    res_update = client.put(
        "/api/v1/marketplaces/amazon/credentials",
        json={
            "seller_id": "A2QWR8429184",
            "client_id": "mock_cid",
            "client_secret": "mock_csec",
            "refresh_token": "mock_rtoken",
        },
    )
    assert res_update.status_code == 200
    up_data = res_update.json()
    assert up_data["has_credentials"] is True

    # 4. Trigger sync
    res_sync = client.post("/api/v1/marketplaces/amazon/sync")
    assert res_sync.status_code == 200
    sync_data = res_sync.json()
    assert sync_data["status"] == "completed"
    assert "synchronized" in sync_data["message"].lower()
