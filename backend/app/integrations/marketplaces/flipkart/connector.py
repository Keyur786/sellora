from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from app.integrations.marketplaces.base import (
    MarketplaceConnector,
    StandardOrder,
    StandardOrderItem,
    StandardProduct,
    StandardFee,
    StandardSettlement,
    StandardReturn,
)


class FlipkartConnector(MarketplaceConnector):
    """Flipkart Seller Hub connector implementing the standard MarketplaceConnector contract."""

    def __init__(self, app_id: str = "", app_secret: str = ""):
        self.app_id = app_id
        self.app_secret = app_secret

    async def get_products(self) -> List[StandardProduct]:
        return [
            StandardProduct(
                sku="CU-BOTTLE-1000ML",
                title="Pure Copper Hammered Water Bottle 1000ml",
                marketplace_id="FSNBOTTL7282",
                category="Home & Kitchen",
                current_listing_price=Decimal("999.00"),
                inventory_quantity=180,
            ),
            StandardProduct(
                sku="AUDIO-AIR-PODS-PRO",
                title="True Wireless Earbuds with ANC",
                marketplace_id="FSNEARBD9102",
                category="Audio",
                current_listing_price=Decimal("1499.00"),
                inventory_quantity=95,
            ),
        ]

    async def get_orders(self, since: Optional[datetime] = None) -> List[StandardOrder]:
        now = datetime.now(timezone.utc)
        return [
            StandardOrder(
                marketplace_order_id="OD33221100998811",
                marketplace_type="flipkart",
                order_date=now,
                status="Delivered",
                fulfillment_channel="FBF",  # Fulfillment by Flipkart
                total_amount=Decimal("999.00"),
                currency="INR",
                customer_city="Bengaluru",
                customer_state="Karnataka",
                postal_code="560001",
                items=[
                    StandardOrderItem(
                        marketplace_item_id="FP-ITEM-01",
                        sku="CU-BOTTLE-1000ML",
                        title="Pure Copper Hammered Water Bottle 1000ml",
                        quantity=1,
                        item_price=Decimal("999.00"),
                        fees=[
                            StandardFee(fee_type="Marketplace Commission", amount=Decimal("119.88"), currency="INR"),
                            StandardFee(fee_type="Fixed Fee", amount=Decimal("30.00"), currency="INR"),
                            StandardFee(fee_type="Collection Fee", amount=Decimal("19.98"), currency="INR"),
                            StandardFee(fee_type="Shipping Fee", amount=Decimal("65.00"), currency="INR"),
                            StandardFee(fee_type="TCS GST", amount=Decimal("9.99"), currency="INR"),
                        ],
                    )
                ],
            )
        ]

    async def get_fees(self, order_id: str) -> List[StandardFee]:
        return [
            StandardFee(fee_type="Marketplace Commission", amount=Decimal("119.88"), currency="INR"),
            StandardFee(fee_type="Fixed Fee", amount=Decimal("30.00"), currency="INR"),
            StandardFee(fee_type="Collection Fee", amount=Decimal("19.98"), currency="INR"),
            StandardFee(fee_type="Shipping Fee", amount=Decimal("65.00"), currency="INR"),
            StandardFee(fee_type="TCS GST", amount=Decimal("9.99"), currency="INR"),
        ]

    async def get_settlements(self, start_date: datetime, end_date: datetime) -> List[StandardSettlement]:
        return [
            StandardSettlement(
                settlement_id="FP-SETTLE-2026-09-01",
                period_start=start_date,
                period_end=end_date,
                total_amount=Decimal("32400.00"),
                currency="INR",
            )
        ]

    async def get_returns(self, since: Optional[datetime] = None) -> List[StandardReturn]:
        return [
            StandardReturn(
                marketplace_order_id="OD33221100998811",
                sku="CU-BOTTLE-1000ML",
                return_date=datetime.now(timezone.utc),
                reason="Customer Return - Defective piece",
                return_type="CustomerReturn",
                status="Completed",
            )
        ]

