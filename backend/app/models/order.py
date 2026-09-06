from decimal import Decimal
from sqlalchemy import Column, String, ForeignKey, Numeric, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Order(BaseModel):
    """Standardized internal order model."""
    __tablename__ = "orders"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace_account_id = Column(String(36), ForeignKey("marketplace_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace_type = Column(String(50), nullable=False, index=True)  # "amazon", "flipkart"
    marketplace_order_id = Column(String(100), nullable=False, index=True)

    order_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # Shipped, Delivered, Cancelled, Returned
    fulfillment_channel = Column(String(50), nullable=True)  # FBA, EasyShip, MerchantFulfillment, FBF

    total_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)

    customer_city = Column(String(100), nullable=True)
    customer_state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="orders")
    marketplace_account = relationship("MarketplaceAccount", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    fees = relationship("Fee", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
    returns = relationship("Return", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("marketplace_account_id", "marketplace_order_id", name="uq_account_order_id"),
    )


class OrderItem(BaseModel):
    """Line item in an order."""
    __tablename__ = "order_items"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    sku = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    item_price = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_price = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    item_tax = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_tax = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    fees = relationship("Fee", back_populates="order_item", cascade="all, delete-orphan")
