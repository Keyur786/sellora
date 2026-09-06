from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.product import Product, Inventory
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve all products belonging strictly to current tenant organization."""
    products = (
        db.query(Product)
        .filter(Product.organization_id == org.id)
        .order_by(Product.created_at.desc())
        .all()
    )

    results = []
    for p in products:
        stock = p.inventory.available_quantity if p.inventory else 0
        resp = ProductResponse.model_validate(p)
        resp.available_stock = stock
        results.append(resp)
    return results


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Create a new product with unit cost configuration."""
    existing = (
        db.query(Product)
        .filter(Product.organization_id == org.id, Product.sku == data.sku)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{data.sku}' already exists in your organization",
        )

    product = Product(
        organization_id=org.id,
        sku=data.sku,
        title=data.title,
        asin_or_fsn=data.asin_or_fsn,
        category=data.category,
        image_url=data.image_url,
        cost_price=data.cost_price,
        packaging_cost=data.packaging_cost,
        other_cost=data.other_cost,
    )
    db.add(product)
    db.flush()

    # Create empty inventory
    inv = Inventory(product_id=product.id, available_quantity=0, reserved_quantity=0)
    db.add(inv)
    db.commit()
    db.refresh(product)

    resp = ProductResponse.model_validate(product)
    resp.available_stock = 0
    return resp


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product_cogs(
    product_id: str,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update product Cost of Goods Sold (COGS: product cost, packaging, other unit cost)."""
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.organization_id == org.id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if data.title is not None:
        product.title = data.title
    if data.category is not None:
        product.category = data.category
    if data.cost_price is not None:
        product.cost_price = data.cost_price
    if data.packaging_cost is not None:
        product.packaging_cost = data.packaging_cost
    if data.other_cost is not None:
        product.other_cost = data.other_cost
    if data.is_active is not None:
        product.is_active = data.is_active

    db.commit()
    db.refresh(product)

    stock = product.inventory.available_quantity if product.inventory else 0
    resp = ProductResponse.model_validate(product)
    resp.available_stock = stock
    return resp
