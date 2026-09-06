from decimal import Decimal
from sqlalchemy import Column, String, ForeignKey, Numeric, Integer, DateTime, Date, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Fee(BaseModel):
    """Marketplace fee incurred on an order or order item."""
    __tablename__ = "fees"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(String(36), ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True, index=True)
    fee_type = Column(String(100), nullable=False, index=True)  # Commission, ClosingFee, ShippingFee, PickPack, TDS, TCS
    amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="fees")
    order_item = relationship("OrderItem", back_populates="fees")


class Settlement(BaseModel):
    """Bank settlement payout from marketplace."""
    __tablename__ = "settlements"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace_account_id = Column(String(36), ForeignKey("marketplace_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    settlement_id = Column(String(100), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)


class Refund(BaseModel):
    """Refund issued to buyer."""
    __tablename__ = "refunds"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    refund_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    refund_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="refunds")


class Return(BaseModel):
    """Product return or courier return (RTO)."""
    __tablename__ = "returns"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=True, index=True)
    return_date = Column(DateTime(timezone=True), nullable=False)
    return_reason = Column(String(255), nullable=True)
    return_type = Column(String(50), default="CustomerReturn", nullable=False)  # CustomerReturn, CourierReturn_RTO
    condition = Column(String(50), default="sellable", nullable=False)  # sellable, damaged, lost
    status = Column(String(50), default="Completed", nullable=False)  # Initiated, Received, Damaged
    restock_fee = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    # Detailed RTO Loss Breakdown
    shipping_loss = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    packaging_loss = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    product_damage_loss = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_loss = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    order = relationship("Order", back_populates="returns")


class Expense(BaseModel):
    """Operational business expenses outside of direct product costs."""
    __tablename__ = "expenses"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # Packaging, Rent, Staff, Software, Marketing, CA_Accountant, Utilities
    amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=True)
    vendor_name = Column(String(255), nullable=True)
    payment_method = Column(String(50), default="Bank Transfer", nullable=True)  # Bank Transfer, UPI, Credit Card, Cash
    is_recurring = Column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", back_populates="expenses")


class AdvertisingCost(BaseModel):
    """Daily or per-campaign advertising expenditure (Amazon Ads / Flipkart Ads)."""
    __tablename__ = "advertising_costs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace_account_id = Column(String(36), ForeignKey("marketplace_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, index=True)
    spend = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    sales = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    impressions = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)

    organization = relationship("Organization", back_populates="advertising_costs")
    marketplace_account = relationship("MarketplaceAccount", back_populates="advertising_costs")
