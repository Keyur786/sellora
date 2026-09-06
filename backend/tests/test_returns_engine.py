import uuid
from decimal import Decimal
import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.organization import Organization
from app.models.marketplace import MarketplaceAccount
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.financials import Return
from app.services.returns_engine import ReturnsEngine
from datetime import datetime, timezone


def test_returns_engine_rto_calculation():
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        org = Organization(name=f"Return Org {suffix}", slug=f"return-org-{suffix}", currency="INR")
        db.add(org)
        db.flush()

        account = MarketplaceAccount(
            organization_id=org.id,
            marketplace_type="amazon",
            account_name="Test Amazon",
            seller_id=f"SELLER_{suffix}",
            status="connected",
        )
        db.add(account)
        db.flush()

        p1 = Product(organization_id=org.id, sku="RTO-SKU-1", title="Product 1", cost_price=Decimal("200.00"))
        p2 = Product(organization_id=org.id, sku="RTO-SKU-2", title="Product 2", cost_price=Decimal("400.00"))
        db.add_all([p1, p2])
        db.flush()

        # Create 10 orders for p1 and 5 orders for p2
        now = datetime.now(timezone.utc)
        orders = []
        for i in range(10):
            o = Order(
                organization_id=org.id,
                marketplace_account_id=account.id,
                marketplace_type="amazon",
                marketplace_order_id=f"402-RET-{suffix}-{i}",
                order_date=now,
                status="Delivered",
                total_amount=Decimal("999.00"),
                currency="INR",
            )
            db.add(o)
            db.flush()
            orders.append(o)
            it = OrderItem(order_id=o.id, product_id=p1.id, sku=p1.sku, title=p1.title, quantity=1, item_price=Decimal("999.00"))
            db.add(it)

        # Attach 2 Courier RTO returns to p1
        db.add(Return(
            order_id=orders[0].id,
            sku=p1.sku,
            return_date=now,
            return_reason="Customer refused COD",
            return_type="CourierReturn_RTO",
            condition="sellable",
            status="Completed",
            shipping_loss=Decimal("120.00"),
            packaging_loss=Decimal("25.00"),
            product_damage_loss=Decimal("0.00"),
            total_loss=Decimal("145.00"),
        ))
        db.add(Return(
            order_id=orders[1].id,
            sku=p1.sku,
            return_date=now,
            return_reason="Pincode unserviceable",
            return_type="CourierReturn_RTO",
            condition="sellable",
            status="Completed",
            shipping_loss=Decimal("120.00"),
            packaging_loss=Decimal("25.00"),
            product_damage_loss=Decimal("0.00"),
            total_loss=Decimal("145.00"),
        ))
        db.commit()

        # Run analytical engine
        res = ReturnsEngine.get_returns_analytics(db=db, org_id=org.id, days=30)
        
        assert res["total_units_sold"] == 10
        assert res["total_returns"] == 2
        assert res["courier_rto_count"] == 2
        assert float(res["overall_return_rate_percentage"]) == 20.0
        assert float(res["courier_rto_rate_percentage"]) == 20.0
        assert float(res["total_financial_loss"]) == 290.00
        assert len(res["sku_ranking"]) == 1
        assert res["sku_ranking"][0]["sku"] == "RTO-SKU-1"

    finally:
        db.close()

