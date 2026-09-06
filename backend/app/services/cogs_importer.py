import csv
import io
from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.product import Product, Inventory
from app.integrations.marketplaces.amazon.report_parser import parse_decimal


class COGSImporter:
    """Service to parse and apply seller product cost CSVs."""

    @classmethod
    def import_cogs_csv(
        cls,
        db: Session,
        org: Organization,
        csv_content: str,
    ) -> Dict[str, Any]:
        """
        Parses seller unit economics CSV.
        Expected columns (case-insensitive, flexible naming):
          - sku / product_sku
          - product_cost / cost_price / purchase_price
          - packaging_cost / packaging
          - other_cost / other_unit_cost / freight_cost
          - title / product_name (optional)
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        products_updated = 0
        products_created = 0
        updated_skus = []

        for row in reader:
            # Normalize keys
            normalized = {k.strip().lower() if k else "": v.strip() if v else "" for k, v in row.items()}
            
            sku = (
                normalized.get("sku")
                or normalized.get("product_sku")
                or normalized.get("seller_sku")
                or ""
            )
            if not sku:
                continue

            product_cost = parse_decimal(
                normalized.get("product_cost")
                or normalized.get("cost_price")
                or normalized.get("purchase_price")
                or normalized.get("unit_cost")
            )
            packaging_cost = parse_decimal(
                normalized.get("packaging_cost")
                or normalized.get("packaging")
                or normalized.get("box_cost")
            )
            other_cost = parse_decimal(
                normalized.get("other_cost")
                or normalized.get("other_unit_cost")
                or normalized.get("freight_cost")
                or normalized.get("misc_cost")
            )
            title = normalized.get("title") or normalized.get("product_name") or f"Product {sku}"

            # Check if product exists
            product = db.query(Product).filter(
                Product.organization_id == org.id,
                Product.sku == sku,
            ).first()

            if product:
                product.cost_price = product_cost
                product.packaging_cost = packaging_cost
                product.other_cost = other_cost
                if title and product.title.startswith("Product "):
                    product.title = title[:500]
                products_updated += 1
            else:
                product = Product(
                    organization_id=org.id,
                    sku=sku,
                    title=title[:500],
                    cost_price=product_cost,
                    packaging_cost=packaging_cost,
                    other_cost=other_cost,
                )
                db.add(product)
                db.flush()
                # Create empty inventory
                db.add(Inventory(product_id=product.id, available_quantity=0))
                products_created += 1

            updated_skus.append(sku)

        db.commit()

        return {
            "rows_processed": len(updated_skus),
            "products_updated": products_updated,
            "products_created": products_created,
            "updated_skus": updated_skus,
        }
