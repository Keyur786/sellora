from decimal import Decimal
from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Product(BaseModel):
    """Internal standardized product representation with COGS."""
    __tablename__ = "products"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    asin_or_fsn = Column(String(100), nullable=True, index=True)
    category = Column(String(150), nullable=True)
    image_url = Column(String(1000), nullable=True)

    # Unit Cost Structure (Critical for accurate profit calculation)
    # Using Decimal / Numeric(12, 2)
    cost_price = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    packaging_cost = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    other_cost = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_org_product_sku"),
    )


class ProductVariant(BaseModel):
    """Product variant (e.g. specific sizes, colors)."""
    __tablename__ = "product_variants"

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_sku = Column(String(100), nullable=False, index=True)
    variant_name = Column(String(255), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    product = relationship("Product", back_populates="variants")


class Inventory(BaseModel):
    """Product stock and inventory tracking."""
    __tablename__ = "inventory"

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    available_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    warehouse_location = Column(String(255), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), nullable=True)

    product = relationship("Product", back_populates="inventory")
