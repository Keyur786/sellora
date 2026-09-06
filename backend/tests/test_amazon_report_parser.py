import uuid
from decimal import Decimal
import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.organization import Organization
from app.models.product import Product
from app.models.order import Order
from app.models.financials import Fee
from app.integrations.marketplaces.amazon.report_parser import AmazonReportSynchronizer
from app.services.cogs_importer import COGSImporter
from app.services.profit_engine import ProfitEngine, UnitProfitInput


SAMPLE_AMAZON_CSV = """Date Range Report
Report generated for: Apex Retail India

Date/Time,Settlement id,type,Order ID,SKU,Description,Quantity,Marketplace,fulfillment,city,state,postal code,Product Sales,Product Sales Tax,Shipping Credits,Shipping Credits Tax,Gift wrap credits,Giftwrap credits tax,Regulatory Fee,Tax on Regulatory Fee,Promotional Rebates,Promotional Rebates Tax,Marketplace Withheld Tax,Selling fees,FBA fees,Other transaction fees,Other,Total
02-Sep-2026 14:22:10 IST,182910291,Order,402-9988271-1029381,TEST-COPPER-BOTTLE,Pure Copper Hammered Water Bottle 1000ml,1,amazon.in,Seller,Mumbai,Maharashtra,400001,999.00,152.38,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,-9.99,-144.88,-75.00,0.00,0.00,769.13
03-Sep-2026 18:05:42 IST,182910291,Order,402-1102938-5928371,TEST-AUDIO-EARBUDS,True Wireless Earbuds with ANC,1,amazon.in,Amazon,Bengaluru,Karnataka,560001,1499.00,228.66,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,-14.99,-215.85,-95.00,0.00,0.00,1173.16
"""

SAMPLE_COGS_CSV = """sku,product_cost,packaging_cost,other_cost
TEST-COPPER-BOTTLE,350.00,20.00,10.00
TEST-AUDIO-EARBUDS,520.00,35.00,15.00
"""


def test_amazon_report_sync_and_idempotency():
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        org = Organization(name=f"Org {suffix}", slug=f"org-{suffix}", currency="INR")
        db.add(org)
        db.commit()

        # 1. First Import
        res1 = AmazonReportSynchronizer.sync_date_range_report(
            db=db,
            org=org,
            raw_csv_content=SAMPLE_AMAZON_CSV,
        )
        assert res1["orders_imported"] == 2
        assert res1["fees_extracted"] > 0

        # Verify orders in DB
        orders = db.query(Order).filter(Order.organization_id == org.id).all()
        assert len(orders) == 2
        first_order = orders[0]
        assert first_order.marketplace_type == "amazon"
        assert first_order.total_amount > Decimal("0.00")

        # Verify fees extracted
        fees = db.query(Fee).filter(Fee.order_id == first_order.id).all()
        assert len(fees) > 0
        fee_types = [f.fee_type for f in fees]
        assert "Commission & Closing Fee" in fee_types
        assert "Shipping & Fulfillment Fee" in fee_types
        assert "TCS & TDS Withheld" in fee_types

        # 2. Second Import with SAME file (Idempotency test)
        res2 = AmazonReportSynchronizer.sync_date_range_report(
            db=db,
            org=org,
            raw_csv_content=SAMPLE_AMAZON_CSV,
        )
        # Should not create duplicate orders
        assert res2["orders_imported"] == 0
        orders_after = db.query(Order).filter(Order.organization_id == org.id).all()
        assert len(orders_after) == 2

    finally:
        db.close()


def test_cogs_csv_importer():
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        org = Organization(name=f"COGS Org {suffix}", slug=f"cogs-org-{suffix}", currency="INR")
        db.add(org)
        db.commit()

        res = COGSImporter.import_cogs_csv(
            db=db,
            org=org,
            csv_content=SAMPLE_COGS_CSV,
        )
        assert res["rows_processed"] == 2
        assert res["products_created"] == 2

        # Verify values stored
        p1 = db.query(Product).filter(Product.organization_id == org.id, Product.sku == "TEST-COPPER-BOTTLE").first()
        assert p1 is not None
        assert p1.cost_price == Decimal("350.00")
        assert p1.packaging_cost == Decimal("20.00")
        assert p1.other_cost == Decimal("10.00")

        # Re-import with updated cost
        updated_csv = "sku,product_cost,packaging_cost,other_cost\nTEST-COPPER-BOTTLE,365.00,22.00,12.00\n"
        res2 = COGSImporter.import_cogs_csv(db=db, org=org, csv_content=updated_csv)
        assert res2["products_updated"] == 1
        db.refresh(p1)
        assert p1.cost_price == Decimal("365.00")

    finally:
        db.close()

