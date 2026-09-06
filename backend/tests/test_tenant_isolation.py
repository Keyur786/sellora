import uuid
from decimal import Decimal
import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.organization import Organization
from app.models.product import Product


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_strict_tenant_isolation():
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        # Create Org A
        org_a = Organization(name=f"Tenant Alpha {suffix}", slug=f"tenant-alpha-{suffix}", currency="INR")
        db.add(org_a)
        db.flush()

        # Create Org B
        org_b = Organization(name=f"Tenant Beta {suffix}", slug=f"tenant-beta-{suffix}", currency="INR")
        db.add(org_b)
        db.flush()

        # Create product in Org A
        prod_a = Product(
            organization_id=org_a.id,
            sku=f"SKU-ALPHA-{suffix}",
            title="Alpha Premium Bottle",
            cost_price=Decimal("200.00"),
        )
        db.add(prod_a)

        # Create product in Org B
        prod_b = Product(
            organization_id=org_b.id,
            sku=f"SKU-BETA-{suffix}",
            title="Beta Premium Pillow",
            cost_price=Decimal("450.00"),
        )
        db.add(prod_b)
        db.commit()

        # Query Org A products: must ONLY return prod_a
        org_a_products = db.query(Product).filter(Product.organization_id == org_a.id).all()
        org_a_skus = [p.sku for p in org_a_products]
        assert f"SKU-ALPHA-{suffix}" in org_a_skus
        assert f"SKU-BETA-{suffix}" not in org_a_skus

        # Query Org B products: must ONLY return prod_b
        org_b_products = db.query(Product).filter(Product.organization_id == org_b.id).all()
        org_b_skus = [p.sku for p in org_b_products]
        assert f"SKU-BETA-{suffix}" in org_b_skus
        assert f"SKU-ALPHA-{suffix}" not in org_b_skus

    finally:
        db.close()
