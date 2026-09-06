from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional


@dataclass
class StandardFee:
    """Standardized representation of a marketplace fee."""
    fee_type: str  # Commission, ClosingFee, PickPackFee, ShippingFee, TCS, TDS
    amount: Decimal
    currency: str = "INR"
    description: Optional[str] = None


@dataclass
class StandardOrderItem:
    """Standardized representation of a marketplace order line item."""
    marketplace_item_id: str
    sku: str
    title: str
    quantity: int
    item_price: Decimal
    shipping_price: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    fees: List[StandardFee] = field(default_factory=list)


@dataclass
class StandardOrder:
    """Standardized representation of a marketplace order."""
    marketplace_order_id: str
    marketplace_type: str  # amazon, flipkart
    order_date: datetime
    status: str  # Shipped, Delivered, Cancelled, Returned
    fulfillment_channel: str  # FBA, EasyShip, SelfShip, FBF
    total_amount: Decimal
    currency: str = "INR"
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None
    postal_code: Optional[str] = None
    items: List[StandardOrderItem] = field(default_factory=list)


@dataclass
class StandardProduct:
    """Standardized representation of a marketplace catalog listing."""
    sku: str
    title: str
    marketplace_id: str  # ASIN or FSN
    category: Optional[str] = None
    current_listing_price: Decimal = Decimal("0.00")
    inventory_quantity: int = 0
    image_url: Optional[str] = None


@dataclass
class StandardSettlement:
    """Standardized representation of a marketplace bank payout."""
    settlement_id: str
    period_start: datetime
    period_end: datetime
    total_amount: Decimal
    currency: str = "INR"


@dataclass
class StandardReturn:
    """Standardized representation of a customer return or courier RTO."""
    marketplace_order_id: str
    sku: str
    return_date: datetime
    reason: str
    return_type: str  # CustomerReturn, CourierReturn_RTO
    status: str  # Completed, Damaged


class MarketplaceConnector(ABC):
    """Abstract base class contract for all marketplace connectors."""

    @abstractmethod
    async def get_orders(self, since: Optional[datetime] = None) -> List[StandardOrder]:
        """Fetch and convert marketplace orders into standardized internal format."""
        raise NotImplementedError

    @abstractmethod
    async def get_products(self) -> List[StandardProduct]:
        """Fetch and convert marketplace listings into standardized internal format."""
        raise NotImplementedError

    @abstractmethod
    async def get_fees(self, order_id: str) -> List[StandardFee]:
        """Fetch detailed fee breakdown for a specific order."""
        raise NotImplementedError

    @abstractmethod
    async def get_settlements(self, start_date: datetime, end_date: datetime) -> List[StandardSettlement]:
        """Fetch bank settlement payout reports."""
        raise NotImplementedError

    @abstractmethod
    async def get_returns(self, since: Optional[datetime] = None) -> List[StandardReturn]:
        """Fetch product returns and RTO records."""
        raise NotImplementedError


class MockMarketplaceConnector(MarketplaceConnector):
    """Mock connector providing realistic Indian e-commerce data for testing and local development."""

    def __init__(self, marketplace_type: str = "amazon"):
        self.marketplace_type = marketplace_type

    async def get_products(self) -> List[StandardProduct]:
        return [
            StandardProduct(
                sku="CU-BOTTLE-1000ML",
                title="Pure Copper Hammered Water Bottle 1000ml Ayurvedic Health Benefits",
                marketplace_id="B08N5WRWNW" if self.marketplace_type == "amazon" else "FSNBOTTL7282",
                category="Kitchen & Home",
                current_listing_price=Decimal("999.00"),
                inventory_quantity=240,
                image_url="https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=300",
            ),
            StandardProduct(
                sku="AUDIO-AIR-PODS-PRO",
                title="True Wireless Earbuds with ENC Noise Cancellation, 40H Playtime",
                marketplace_id="B09H2S872K" if self.marketplace_type == "amazon" else "FSNEARBD9102",
                category="Consumer Electronics",
                current_listing_price=Decimal("1499.00"),
                inventory_quantity=115,
                image_url="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=300",
            ),
            StandardProduct(
                sku="KURTA-COTTON-SL-NAVY",
                title="Men's Pure Cotton Navy Blue Regular Fit Casual Kurta",
                marketplace_id="B07X99120Z" if self.marketplace_type == "amazon" else "FSNKURTA3481",
                category="Apparel & Fashion",
                current_listing_price=Decimal("799.00"),
                inventory_quantity=320,
                image_url="https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=300",
            ),
            StandardProduct(
                sku="DESK-MAT-LEATHER-BRW",
                title="Dual-Sided Waterproof Vegan Leather Desk Mat (90x45cm)",
                marketplace_id="B08Z4L912A" if self.marketplace_type == "amazon" else "FSNDESKM1092",
                category="Office Products",
                current_listing_price=Decimal("599.00"),
                inventory_quantity=85,
                image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=300",
            ),
        ]

    async def get_orders(self, since: Optional[datetime] = None) -> List[StandardOrder]:
        now = datetime.now(timezone.utc)
        return [
            StandardOrder(
                marketplace_order_id=f"402-{i:07d}-928312{i}" if self.marketplace_type == "amazon" else f"OD{i:010d}",
                marketplace_type=self.marketplace_type,
                order_date=now,
                status="Delivered",
                fulfillment_channel="EasyShip" if self.marketplace_type == "amazon" else "FBF",
                total_amount=Decimal("999.00"),
                currency="INR",
                customer_city="Bengaluru",
                customer_state="Karnataka",
                postal_code="560001",
                items=[
                    StandardOrderItem(
                        marketplace_item_id=f"ITEM-{i}",
                        sku="CU-BOTTLE-1000ML",
                        title="Pure Copper Hammered Water Bottle 1000ml",
                        quantity=1,
                        item_price=Decimal("999.00"),
                        fees=[
                            StandardFee(fee_type="Commission", amount=Decimal("119.88")),
                            StandardFee(fee_type="ClosingFee", amount=Decimal("25.00")),
                            StandardFee(fee_type="ShippingFee", amount=Decimal("75.00")),
                            StandardFee(fee_type="TCS", amount=Decimal("9.99")),
                        ],
                    )
                ],
            )
            for i in range(1, 6)
        ]

    async def get_fees(self, order_id: str) -> List[StandardFee]:
        return [
            StandardFee(fee_type="Commission", amount=Decimal("119.88")),
            StandardFee(fee_type="ClosingFee", amount=Decimal("25.00")),
            StandardFee(fee_type="ShippingFee", amount=Decimal("75.00")),
            StandardFee(fee_type="TCS", amount=Decimal("9.99")),
        ]

    async def get_settlements(self, start_date: datetime, end_date: datetime) -> List[StandardSettlement]:
        return [
            StandardSettlement(
                settlement_id="SETTLE-2026-09-01",
                period_start=start_date,
                period_end=end_date,
                total_amount=Decimal("48520.00"),
                currency="INR",
            )
        ]

    async def get_returns(self, since: Optional[datetime] = None) -> List[StandardReturn]:
        now = datetime.now(timezone.utc)
        return [
            StandardReturn(
                marketplace_order_id="402-0000001-9283121",
                sku="KURTA-COTTON-SL-NAVY",
                return_date=now,
                reason="Size too large",
                return_type="CustomerReturn",
                status="Completed",
            )
        ]
