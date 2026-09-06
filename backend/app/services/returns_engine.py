from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.organization import Organization
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.financials import Return, Fee


class ReturnsEngine:
    """Calculates return rates, Courier RTO losses, and damaged stock write-offs for Indian sellers."""

    TWO_PLACES = Decimal("0.01")

    @classmethod
    def round_val(cls, val: Decimal) -> Decimal:
        return val.quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def get_returns_analytics(cls, db: Session, org_id: str, days: int = 30) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # 1. Total orders and units sold
        orders = db.query(Order).filter(Order.organization_id == org_id, Order.order_date >= since).all()
        order_ids = [o.id for o in orders]
        
        items = []
        if order_ids:
            items = db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all()
        
        units_by_sku: Dict[str, int] = {}
        for it in items:
            units_by_sku[it.sku] = units_by_sku.get(it.sku, 0) + it.quantity
        total_units_sold = sum(units_by_sku.values())

        # 2. Return records
        returns = []
        if order_ids:
            returns = db.query(Return).filter(Return.order_id.in_(order_ids)).all()
        else:
            returns = db.query(Return).join(Order, Return.order_id == Order.id).filter(
                Order.organization_id == org_id,
                Return.return_date >= since
            ).all()

        total_returns = len(returns)
        courier_rto_count = sum(1 for r in returns if "rto" in (r.return_type or "").lower())
        customer_return_count = total_returns - courier_rto_count

        overall_return_rate = (
            cls.round_val(Decimal(str(total_returns * 100)) / Decimal(str(total_units_sold)))
            if total_units_sold > 0 else Decimal("0.00")
        )
        courier_rto_rate = (
            cls.round_val(Decimal(str(courier_rto_count * 100)) / Decimal(str(total_units_sold)))
            if total_units_sold > 0 else Decimal("0.00")
        )

        total_shipping_loss = sum((r.shipping_loss for r in returns), Decimal("0.00"))
        total_packaging_loss = sum((r.packaging_loss for r in returns), Decimal("0.00"))
        total_damage_loss = sum((r.product_damage_loss for r in returns), Decimal("0.00"))
        total_financial_loss = sum((r.total_loss for r in returns), Decimal("0.00"))

        if total_financial_loss == Decimal("0.00") and total_returns > 0:
            # Fallback estimation for Indian market: ~₹120 avg shipping loss + ₹25 packaging
            total_shipping_loss = Decimal(str(total_returns * 120))
            total_packaging_loss = Decimal(str(total_returns * 25))
            total_damage_loss = Decimal(str(customer_return_count * 150))
            total_financial_loss = total_shipping_loss + total_packaging_loss + total_damage_loss

        # 3. Breakdown by reason
        reason_counts: Dict[str, int] = {}
        for r in returns:
            reason = r.return_reason or "Customer Refused at Doorstep (RTO)"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        reasons_list = [
            {"reason": k, "count": v, "percentage": round((v / total_returns * 100) if total_returns > 0 else 0, 1)}
            for k, v in reason_counts.items()
        ]
        reasons_list.sort(key=lambda x: x["count"], reverse=True)

        # 4. SKU-level return loss ranking
        products = db.query(Product).filter(Product.organization_id == org_id).all()
        prod_by_sku = {p.sku: p for p in products}

        sku_returns: Dict[str, List[Return]] = {}
        for r in returns:
            sku = r.sku or "GENERAL"
            if sku not in sku_returns:
                sku_returns[sku] = []
            sku_returns[sku].append(r)

        sku_ranking = []
        for sku, ret_list in sku_returns.items():
            sku_sold = units_by_sku.get(sku, len(ret_list))
            prod = prod_by_sku.get(sku)
            sku_rto = sum(1 for r in ret_list if "rto" in (r.return_type or "").lower())
            sku_cust = len(ret_list) - sku_rto
            sku_rate = round((len(ret_list) / sku_sold * 100) if sku_sold > 0 else 0, 1)

            sku_loss = sum((r.total_loss for r in ret_list), Decimal("0.00"))
            if sku_loss == Decimal("0.00"):
                # Estimate: ₹120 ship + ₹20 pkg + ₹100 damage if customer return
                c_cost = (prod.cost_price if prod else Decimal("300.00")) * Decimal("0.4")
                sku_loss = (Decimal(str(len(ret_list) * 140))) + (Decimal(str(sku_cust)) * c_cost)

            sku_ranking.append({
                "sku": sku,
                "title": prod.title if prod else sku,
                "units_sold": sku_sold,
                "returns_count": len(ret_list),
                "rto_count": sku_rto,
                "customer_return_count": sku_cust,
                "return_rate_percentage": sku_rate,
                "total_loss": str(cls.round_val(sku_loss)),
                "risk_level": "High" if sku_rate > 18 else ("Medium" if sku_rate > 10 else "Low"),
            })

        sku_ranking.sort(key=lambda x: float(x["total_loss"]), reverse=True)

        return {
            "period_days": days,
            "total_units_sold": total_units_sold,
            "total_returns": total_returns,
            "overall_return_rate_percentage": str(overall_return_rate),
            "courier_rto_count": courier_rto_count,
            "courier_rto_rate_percentage": str(courier_rto_rate),
            "customer_return_count": customer_return_count,
            "total_financial_loss": str(cls.round_val(total_financial_loss)),
            "shipping_loss": str(cls.round_val(total_shipping_loss)),
            "packaging_loss": str(cls.round_val(total_packaging_loss)),
            "damaged_product_loss": str(cls.round_val(total_damage_loss)),
            "reasons_breakdown": reasons_list,
            "sku_ranking": sku_ranking,
        }

