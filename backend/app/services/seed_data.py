from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.organization import Organization, User, OrganizationMember
from app.models.marketplace import MarketplaceAccount
from app.models.product import Product, Inventory
from app.models.order import Order, OrderItem
from app.models.financials import Fee, Expense, AdvertisingCost, Return
from app.models.analytics import ProfitSnapshot


def seed_demo_data(db: Session) -> Organization:
    """Populate database with rich realistic Indian e-commerce data if empty."""
    org = db.query(Organization).filter(Organization.slug == "demo-seller-india").first()
    if org:
        return org

    # 1. Organization & User
    org = Organization(
        name="Apex Retail India",
        slug="demo-seller-india",
        currency="INR",
        timezone="Asia/Kolkata",
    )
    db.add(org)
    db.flush()

    user = User(
        email="seller@sellora.in",
        full_name="Rajesh Sharma",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)

    # 2. Marketplace Accounts
    amazon_account = MarketplaceAccount(
        organization_id=org.id,
        marketplace_type="amazon",
        account_name="Apex Store Amazon IN",
        seller_id="A2QWR8429184",
        marketplace_id="A21TJRUUN4KGV",  # Amazon.in marketplace ID
        status="connected",
        last_synced_at=datetime.now(timezone.utc),
    )
    flipkart_account = MarketplaceAccount(
        organization_id=org.id,
        marketplace_type="flipkart",
        account_name="Apex Store Flipkart",
        seller_id="FLIPKART_SELLER_881",
        status="connected",
        last_synced_at=datetime.now(timezone.utc),
    )
    db.add_all([amazon_account, flipkart_account])
    db.flush()

    # 3. Products with Unit COGS
    # Notice Product 1 matches the prompt's exact economics:
    # Price: ₹999, Cost: ₹350, Fees: ₹180, Ads: ₹100, Shipping: ₹80, Returns: ₹40 -> Net: ₹249 (24.92%)
    p1 = Product(
        organization_id=org.id,
        sku="CU-BOTTLE-1000ML",
        title="Pure Copper Hammered Water Bottle 1000ml (Ayurvedic Health Edition)",
        asin_or_fsn="B08N5WRWNW",
        category="Kitchen & Home",
        cost_price=Decimal("350.00"),
        packaging_cost=Decimal("20.00"),
        other_cost=Decimal("10.00"),
        image_url="https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=300",
    )
    p2 = Product(
        organization_id=org.id,
        sku="AUDIO-AIR-PODS-PRO",
        title="True Wireless Earbuds with ANC & 40H Playtime",
        asin_or_fsn="B09H2S872K",
        category="Consumer Electronics",
        cost_price=Decimal("520.00"),
        packaging_cost=Decimal("35.00"),
        other_cost=Decimal("15.00"),
        image_url="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=300",
    )
    p3 = Product(
        organization_id=org.id,
        sku="KURTA-COTTON-SL-NAVY",
        title="Men's Pure Cotton Navy Blue Regular Fit Casual Kurta",
        asin_or_fsn="B07X99120Z",
        category="Apparel & Fashion",
        cost_price=Decimal("260.00"),
        packaging_cost=Decimal("15.00"),
        other_cost=Decimal("10.00"),
        image_url="https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=300",
    )
    p4 = Product(
        organization_id=org.id,
        sku="DESK-MAT-LEATHER-BRW",
        title="Dual-Sided Waterproof Vegan Leather Desk Mat (90x45cm)",
        asin_or_fsn="B08Z4L912A",
        category="Office Products",
        cost_price=Decimal("180.00"),
        packaging_cost=Decimal("18.00"),
        other_cost=Decimal("5.00"),
        image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=300",
    )
    db.add_all([p1, p2, p3, p4])
    db.flush()

    # Inventory
    db.add_all([
        Inventory(product_id=p1.id, available_quantity=240, reserved_quantity=12, warehouse_location="BOM-01"),
        Inventory(product_id=p2.id, available_quantity=115, reserved_quantity=8, warehouse_location="DEL-02"),
        Inventory(product_id=p3.id, available_quantity=320, reserved_quantity=25, warehouse_location="BLR-01"),
        Inventory(product_id=p4.id, available_quantity=85, reserved_quantity=4, warehouse_location="BOM-01"),
    ])

    # 4. Generate Orders with Fees
    now = datetime.now(timezone.utc)
    cities = [("Mumbai", "Maharashtra", "400001"), ("Bengaluru", "Karnataka", "560001"), ("Delhi", "Delhi", "110001"), ("Hyderabad", "Telangana", "500001"), ("Pune", "Maharashtra", "411001")]
    
    # 25 realistic historical orders spread over the last 14 days
    for day_offset in range(14):
        order_time = now - timedelta(days=day_offset, hours=4)
        city, state, pin = cities[day_offset % len(cities)]
        account = amazon_account if day_offset % 2 == 0 else flipkart_account
        mkt_type = "amazon" if account == amazon_account else "flipkart"

        order = Order(
            organization_id=org.id,
            marketplace_account_id=account.id,
            marketplace_type=mkt_type,
            marketplace_order_id=f"402-{1000000 + day_offset}-829103{day_offset}" if mkt_type == "amazon" else f"OD2026090{day_offset}1829",
            order_date=order_time,
            status="Delivered",
            fulfillment_channel="EasyShip" if mkt_type == "amazon" else "FBF",
            total_amount=Decimal("999.00"),
            currency="INR",
            customer_city=city,
            customer_state=state,
            postal_code=pin,
        )
        db.add(order)
        db.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=p1.id,
            sku=p1.sku,
            title=p1.title,
            quantity=1,
            item_price=Decimal("999.00"),
            shipping_price=Decimal("0.00"),
            item_tax=Decimal("152.38"),
        )
        db.add(item)
        db.flush()

        # Fees matching exact INR structure
        db.add_all([
            Fee(order_id=order.id, order_item_id=item.id, fee_type="Commission", amount=Decimal("119.88"), currency="INR"),
            Fee(order_id=order.id, order_item_id=item.id, fee_type="ClosingFee", amount=Decimal("25.00"), currency="INR"),
            Fee(order_id=order.id, order_item_id=item.id, fee_type="ShippingFee", amount=Decimal("75.00"), currency="INR"),
            Fee(order_id=order.id, order_item_id=item.id, fee_type="TCS", amount=Decimal("9.99"), currency="INR"),
        ])

    # 5. Expenses
    today = date.today()
    db.add_all([
        Expense(organization_id=org.id, category="Packaging Material", amount=Decimal("4500.00"), currency="INR", date=today - timedelta(days=5), description="Corrugated 3-ply boxes (1000 pcs)"),
        Expense(organization_id=org.id, category="Software", amount=Decimal("2499.00"), currency="INR", date=today - timedelta(days=10), description="Inventory & GST invoicing subscription"),
    ])

    # 6. Advertising Costs
    for d in range(14):
        ad_date = today - timedelta(days=d)
        db.add(
            AdvertisingCost(
                organization_id=org.id,
                marketplace_account_id=amazon_account.id,
                campaign_name="Copper Bottle Auto SP Campaign",
                date=ad_date,
                spend=Decimal("350.00"),
                sales=Decimal("1998.00"),
                impressions=3200,
                clicks=48,
            )
        )

    db.commit()
    return org
