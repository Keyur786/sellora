import pytest
from decimal import Decimal
from app.integrations.marketplaces.amazon.auth import AmazonLWAAuth
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient
from app.integrations.marketplaces.amazon.sp_api_connector import AmazonSPAPIConnector
from app.integrations.marketplaces.base import StandardOrder


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


@pytest.mark.asyncio
async def test_amazon_sp_api_connector():
    connector = AmazonSPAPIConnector(mock_mode=True)
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
