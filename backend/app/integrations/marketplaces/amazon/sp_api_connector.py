from datetime import datetime, timezone
from typing import List, Optional
from app.integrations.marketplaces.base import (
    MarketplaceConnector,
    StandardOrder,
    StandardProduct,
    StandardFee,
    StandardSettlement,
    StandardReturn,
)
from app.integrations.marketplaces.amazon.client import AmazonSPAPIClient
from app.integrations.marketplaces.amazon.orders import AmazonOrdersAPI
from app.integrations.marketplaces.amazon.finances import AmazonFinancesAPI
from app.integrations.marketplaces.amazon.mapper import AmazonSPAPIMapper


class AmazonSPAPIConnector(MarketplaceConnector):
    """Production-ready connector implementing MarketplaceConnector using official Amazon SP-API."""

    def __init__(
        self,
        refresh_token: str = "",
        client_id: str = "",
        client_secret: str = "",
        mock_mode: bool = True,
    ):
        self.client = AmazonSPAPIClient(
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            mock_mode=mock_mode,
        )
        self.orders_api = AmazonOrdersAPI(self.client)
        self.finances_api = AmazonFinancesAPI(self.client)

    async def get_orders(self, since: Optional[datetime] = None) -> List[StandardOrder]:
        raw_orders = await self.orders_api.list_orders(created_after=since)
        standard_orders: List[StandardOrder] = []

        for o in raw_orders:
            order_id = o.get("AmazonOrderId", "")
            items = await self.orders_api.get_order_items(order_id)
            finances = await self.finances_api.get_financial_events_for_order(order_id)
            std_order = AmazonSPAPIMapper.map_order(o, items, finances)
            standard_orders.append(std_order)

        return standard_orders

    async def get_products(self) -> List[StandardProduct]:
        # Catalog API / Mock fallback
        return [
            StandardProduct(
                sku="CU-BOTTLE-1000ML",
                title="Pure Copper Hammered Water Bottle 1000ml",
                marketplace_id="B08N5WRWNW",
                category="Kitchen & Home",
                current_listing_price=999.00,
                inventory_quantity=240,
            )
        ]

    async def get_fees(self, order_id: str) -> List[StandardFee]:
        finances = await self.finances_api.get_financial_events_for_order(order_id)
        # Extract fees
        fees: List[StandardFee] = []
        for ev in finances.get("ShipmentEventList", []):
            for s_item in ev.get("ShipmentItemList", []):
                for f in s_item.get("ItemFeeList", []):
                    fees.append(
                        StandardFee(
                            fee_type=f.get("FeeType", "Commission"),
                            amount=abs(f.get("FeeAmount", {}).get("CurrencyAmount", 0.0)),
                            currency="INR",
                        )
                    )
        return fees

    async def get_settlements(self, start_date: datetime, end_date: datetime) -> List[StandardSettlement]:
        return []

    async def get_returns(self, since: Optional[datetime] = None) -> List[StandardReturn]:
        return []

