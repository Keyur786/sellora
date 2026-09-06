from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Organization(BaseModel):
    """Tenant organization entity."""
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    marketplace_accounts = relationship("MarketplaceAccount", back_populates="organization", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="organization", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="organization", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="organization", cascade="all, delete-orphan")
    advertising_costs = relationship("AdvertisingCost", back_populates="organization", cascade="all, delete-orphan")
    profit_snapshots = relationship("ProfitSnapshot", back_populates="organization", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="organization", cascade="all, delete-orphan")


class User(BaseModel):
    """System user account."""
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    auth_provider_id = Column(String(255), index=True, nullable=True)  # Supabase/Clerk UID
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Memberships
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")


class OrganizationMember(BaseModel):
    """Association between User and Organization with role."""
    __tablename__ = "organization_members"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="owner", nullable=False)  # owner, admin, viewer

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )
