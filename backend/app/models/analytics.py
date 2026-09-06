from decimal import Decimal
from sqlalchemy import Column, String, ForeignKey, Numeric, Integer, DateTime, Date, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ProfitSnapshot(BaseModel):
    """Daily aggregated profit snapshot for fast dashboard analytics."""
    __tablename__ = "profit_snapshots"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    marketplace_type = Column(String(50), default="all", nullable=False, index=True)  # all, amazon, flipkart

    total_sales = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_orders = Column(Integer, default=0, nullable=False)
    units_sold = Column(Integer, default=0, nullable=False)

    # Cost breakdown
    product_costs = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    marketplace_fees = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_costs = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    advertising_costs = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    returns_costs = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    other_expenses = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    net_profit = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    profit_margin = Column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)  # Percentage, e.g. 24.92

    organization = relationship("Organization", back_populates="profit_snapshots")


class SyncJob(BaseModel):
    """Execution status for asynchronous background marketplace syncs."""
    __tablename__ = "sync_jobs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace_account_id = Column(String(36), ForeignKey("marketplace_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # orders, products, finances, advertising
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, running, completed, failed
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    records_processed = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    organization = relationship("Organization", back_populates="sync_jobs")
    marketplace_account = relationship("MarketplaceAccount", back_populates="sync_jobs")
