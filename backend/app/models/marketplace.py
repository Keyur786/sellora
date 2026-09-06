from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class MarketplaceAccount(BaseModel):
    """Connected marketplace credentials and status."""
    __tablename__ = "marketplace_accounts"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace_type = Column(String(50), nullable=False)  # "amazon", "flipkart"
    account_name = Column(String(255), nullable=False)
    seller_id = Column(String(255), nullable=False, index=True)
    marketplace_id = Column(String(100), nullable=True)  # e.g., Amazon India = A21TJRUUN4KGV
    credentials_encrypted = Column(Text, nullable=True)  # Encrypted OAuth tokens/refresh token
    status = Column(String(50), default="connected", nullable=False)  # connected, error, expired, syncing
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="marketplace_accounts")
    orders = relationship("Order", back_populates="marketplace_account", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="marketplace_account", cascade="all, delete-orphan")
    advertising_costs = relationship("AdvertisingCost", back_populates="marketplace_account", cascade="all, delete-orphan")
