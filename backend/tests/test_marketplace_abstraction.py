from decimal import Decimal
import pytest
from app.integrations.marketplaces.base import (
    MarketplaceConnector,
    MockMarketplaceConnector,
    StandardOrder,
    StandardProduct,
)


@pytest.mark.asyncio
async def test_marketplace_connector_abstraction():
    connector: MarketplaceConnector = MockMarketplaceConnector(marketplace_type="amazon")

    products = await connector.get_products()
    assert len(products) > 0
    assert isinstance(products[0], StandardProduct)
    assert isinstance(products[0].current_listing_price, Decimal)

    orders = await connector.get_orders()
    assert len(orders) > 0
    assert isinstance(orders[0], StandardOrder)
    assert orders[0].marketplace_type == "amazon"
    assert isinstance(orders[0].total_amount, Decimal)

    # Check fee normalization
    assert len(orders[0].items[0].fees) > 0
    fee = orders[0].items[0].fees[0]
    assert isinstance(fee.amount, Decimal)
    assert fee.currency == "INR"
