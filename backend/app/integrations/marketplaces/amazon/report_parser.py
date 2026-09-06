import csv
import io
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.marketplace import MarketplaceAccount
from app.models.product import Product, Inventory
from app.models.order import Order, OrderItem
from app.models.financials import Fee, Refund, Return


def clean_currency_str(val: Any) -> str:
    """Strip currency symbols, commas, and handle parentheses for negative amounts."""
    if val is None:
        return "0.00"
    s = str(val).strip()
    if not s or s == "--" or s == "-":
        return "0.00"
    # Remove currency symbols (₹, INR, $, etc.) and spaces
    s = re.sub(r"[₹\$\s]|INR", "", s)
    # Remove thousand commas
    s = s.replace(",", "")
    # Check for parentheses denoting negative numbers: (123.45) -> -123.45
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    return s.strip()


def parse_decimal(val: Any, default: str = "0.00") -> Decimal:
    """Safely convert any currency string into Decimal."""
    cleaned = clean_currency_str(val)
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def parse_amazon_date(date_str: str) -> datetime:
    """
    Parse date from various Amazon India date formats.
    e.g. '01-Sep-2026 14:22:10 IST', 'Sep 1, 2026 2:22:10 PM IST', '2026-09-01T14:22:10+05:30', '01.09.2026'
    """
    if not date_str or not str(date_str).strip():
        return datetime.now(timezone.utc)

    s = str(date_str).strip()
    # Remove 'IST' or timezone abbreviations for strptime
    s_clean = re.sub(r"\s+(IST|UTC|GMT)$", "", s).strip()

    formats = [
        "%d-%b-%Y %H:%M:%S",
        "%d-%b-%Y %I:%M:%S %p",
        "%b %d, %Y %I:%M:%S %p",
        "%b %d, %Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%d-%b-%Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(s_clean, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return datetime.now(timezone.utc)


class AmazonDateRangeReportParser:
    """Parser for Amazon India Date Range Payments Transaction Reports (CSV)."""

    @classmethod
    def parse_csv(cls, content: str) -> List[Dict[str, Any]]:
        """
        Parses the raw CSV string of an Amazon India Date Range Report.
        Skips preamble/metadata rows until the table header is found.
        """
        lines = content.splitlines()
        header_index = -1

        for i, line in enumerate(lines[:30]):
            lowered = line.lower()
            if ("date/time" in lowered or "date" in lowered) and ("order id" in lowered or "type" in lowered or "settlement id" in lowered):
                header_index = i
                break

        if header_index == -1:
            # Try reading from first line
            header_index = 0

        csv_reader = csv.DictReader(lines[header_index:])
        parsed_rows = []

        for row in csv_reader:
            # Normalize row keys by lowercasing and trimming
            normalized = {k.strip().lower() if k else "": v.strip() if v else "" for k, v in row.items()}
            
            # Skip empty rows
            order_id = normalized.get("order id") or normalized.get("order-id") or ""
            row_type = normalized.get("type") or ""
            if not order_id and not row_type:
                continue

            parsed_rows.append(normalized)

        return parsed_rows


class AmazonReportSynchronizer:
    """Idempotently synchronizes parsed Amazon records into the database for a tenant."""

    @classmethod
    def sync_date_range_report(
        cls,
        db: Session,
        org: Organization,
        raw_csv_content: str,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Imports orders, line items, and itemized fees from Amazon Date Range Transaction CSV.
        Guarantees idempotency: re-running does not duplicate records.
        """
        # 1. Resolve or create MarketplaceAccount
        account = None
        if account_id:
            account = db.query(MarketplaceAccount).filter(MarketplaceAccount.id == account_id, MarketplaceAccount.organization_id == org.id).first()

        if not account:
            account = db.query(MarketplaceAccount).filter(
                MarketplaceAccount.organization_id == org.id,
                MarketplaceAccount.marketplace_type == "amazon"
            ).first()

        if not account:
            account = MarketplaceAccount(
                organization_id=org.id,
                marketplace_type="amazon",
                account_name="Amazon India Store",
                seller_id="AMAZON_IN_SELLER",
                marketplace_id="A21TJRUUN4KGV",
                status="connected",
                last_synced_at=datetime.now(timezone.utc),
            )
            db.add(account)
            db.flush()

        rows = AmazonDateRangeReportParser.parse_csv(raw_csv_content)
        
        orders_new = 0
        orders_updated = 0
        refunds_processed = 0
        fees_recorded = 0
        total_sales_value = Decimal("0.00")
        products_seen = set()

        for r in rows:
            order_id_raw = r.get("order id") or r.get("order-id") or ""
            row_type = r.get("type", "Order")
            sku = r.get("sku") or "UNKNOWN-SKU"
            description = r.get("description") or f"Product {sku}"
            date_str = r.get("date/time") or r.get("date") or ""
            tx_date = parse_amazon_date(date_str)

            # Quantities
            qty_raw = r.get("quantity") or "1"
            try:
                quantity = max(1, int(float(qty_raw)))
            except ValueError:
                quantity = 1

            # Financial columns
            product_sales = parse_decimal(r.get("product sales") or r.get("sales"))
            product_sales_tax = parse_decimal(r.get("product sales tax") or r.get("sales tax"))
            shipping_credits = parse_decimal(r.get("shipping credits"))
            promotional_rebates = parse_decimal(r.get("promotional rebates"))
            withheld_tax = parse_decimal(r.get("marketplace withheld tax"))
            selling_fees = parse_decimal(r.get("selling fees"))
            fba_fees = parse_decimal(r.get("fba fees") or r.get("shipping fees"))
            other_fees = parse_decimal(r.get("other transaction fees"))
            total_net = parse_decimal(r.get("total"))

            fulfillment = r.get("fulfillment") or "Amazon"
            channel = "FBA" if "amazon" in fulfillment.lower() else "EasyShip"
            city = r.get("city") or r.get("order city") or ""
            state = r.get("state") or r.get("order state") or ""
            postal_code = r.get("postal code") or r.get("order postal code") or ""

            # Ensure product exists
            if sku != "UNKNOWN-SKU" and sku not in products_seen:
                products_seen.add(sku)
                prod = db.query(Product).filter(Product.organization_id == org.id, Product.sku == sku).first()
                if not prod:
                    prod = Product(
                        organization_id=org.id,
                        sku=sku,
                        title=description[:500],
                        cost_price=Decimal("0.00"),
                        packaging_cost=Decimal("0.00"),
                        other_cost=Decimal("0.00"),
                    )
                    db.add(prod)
                    db.flush()
                    db.add(Inventory(product_id=prod.id, available_quantity=100))

            if row_type.lower() == "order" and order_id_raw:
                # Idempotent Order find/create
                order = db.query(Order).filter(
                    Order.marketplace_account_id == account.id,
                    Order.marketplace_order_id == order_id_raw
                ).first()

                if not order:
                    order = Order(
                        organization_id=org.id,
                        marketplace_account_id=account.id,
                        marketplace_type="amazon",
                        marketplace_order_id=order_id_raw,
                        order_date=tx_date,
                        status="Delivered",
                        fulfillment_channel=channel,
                        total_amount=product_sales if product_sales > 0 else total_net,
                        currency="INR",
                        customer_city=city,
                        customer_state=state,
                        postal_code=postal_code,
                    )
                    db.add(order)
                    db.flush()
                    orders_new += 1
                    total_sales_value += order.total_amount
                else:
                    # Update details
                    order.status = "Delivered"
                    if city: order.customer_city = city
                    if state: order.customer_state = state
                    orders_updated += 1
                    total_sales_value += order.total_amount

                # Idempotent OrderItem find/create
                item = db.query(OrderItem).filter(OrderItem.order_id == order.id, OrderItem.sku == sku).first()
                if not item:
                    item = OrderItem(
                        order_id=order.id,
                        sku=sku,
                        title=description[:500],
                        quantity=quantity,
                        item_price=product_sales,
                        shipping_price=shipping_credits,
                        item_tax=product_sales_tax,
                        discount_amount=abs(promotional_rebates),
                    )
                    db.add(item)
                    db.flush()

                # Clean existing fees for this order to make import re-entrant (idempotent)
                db.query(Fee).filter(Fee.order_id == order.id).delete()

                # Insert extracted real fees (stored as positive deductions)
                fee_records = []
                if selling_fees != Decimal("0.00"):
                    fee_records.append(Fee(
                        order_id=order.id,
                        order_item_id=item.id,
                        fee_type="Commission & Closing Fee",
                        amount=abs(selling_fees),
                        currency="INR",
                        description="Amazon Referral Commission & Closing Fee",
                    ))
                if fba_fees != Decimal("0.00"):
                    fee_records.append(Fee(
                        order_id=order.id,
                        order_item_id=item.id,
                        fee_type="Shipping & Fulfillment Fee",
                        amount=abs(fba_fees),
                        currency="INR",
                        description="EasyShip / FBA Weight Handling Fee",
                    ))
                if other_fees != Decimal("0.00"):
                    fee_records.append(Fee(
                        order_id=order.id,
                        order_item_id=item.id,
                        fee_type="Pick & Pack Fee",
                        amount=abs(other_fees),
                        currency="INR",
                        description="Fulfillment Service Fee",
                    ))
                if withheld_tax != Decimal("0.00"):
                    fee_records.append(Fee(
                        order_id=order.id,
                        order_item_id=item.id,
                        fee_type="TCS & TDS Withheld",
                        amount=abs(withheld_tax),
                        currency="INR",
                        description="GST TCS & Section 194-O Income Tax Withheld",
                    ))

                if fee_records:
                    db.add_all(fee_records)
                    fees_recorded += len(fee_records)

            elif row_type.lower() == "refund" and order_id_raw:
                order = db.query(Order).filter(
                    Order.marketplace_account_id == account.id,
                    Order.marketplace_order_id == order_id_raw
                ).first()
                if order:
                    order.status = "Returned"
                    refund = Refund(
                        order_id=order.id,
                        refund_amount=abs(total_net),
                        refund_date=tx_date,
                        reason="Customer Refund",
                    )
                    db.add(refund)
                    refunds_processed += 1

        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "rows_parsed": len(rows),
            "orders_imported": orders_new,
            "orders_updated": orders_updated,
            "refunds_imported": refunds_processed,
            "fees_extracted": fees_recorded,
            "total_sales_value": str(total_sales_value),
            "skus_identified": len(products_seen),
        }
