from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.product import Product, Inventory
from app.models.order import Order, OrderItem
from app.schemas.ai import ForecastingSKUItem, WorkingCapitalForecastResponse


class ForecastingService:
    """Demand & Working Capital Forecasting Engine accounting for Indian festive surges."""

    TWO_PLACES = Decimal("0.01")

    @classmethod
    def get_forecast(cls, db: Session, org_id: str, season: str = "standard") -> WorkingCapitalForecastResponse:
        season_lower = season.lower()
        if "diwali" in season_lower or "mega" in season_lower:
            multiplier = 3.0
            season_mode_label = "Diwali & Great Indian Festival (3.0x Surge)"
        elif "festive" in season_lower or "rakhi" in season_lower:
            multiplier = 2.0
            season_mode_label = "Festive Season / Rakhi (2.0x Surge)"
        else:
            multiplier = 1.0
            season_mode_label = "Standard Run-Rate (1.0x)"

        # Fetch catalog and stock
        products = db.query(Product).filter(Product.organization_id == org_id).all()
        since_30d = date.today() - timedelta(days=30)
        recent_orders = (
            db.query(Order)
            .filter(Order.organization_id == org_id, Order.order_date >= since_30d)
            .all()
        )

        # Calculate sales velocity per SKU
        sku_sales_30d: Dict[str, int] = {}
        for o in recent_orders:
            for it in o.items:
                sku_sales_30d[it.sku] = sku_sales_30d.get(it.sku, 0) + it.quantity

        sku_forecasts: List[ForecastingSKUItem] = []
        imminent_stockout_cnt = 0
        dead_stock_cnt = 0
        total_working_capital = Decimal("0.00")
        total_doir = 0.0

        today = date.today()

        for p in products:
            inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
            avail = inv.available_quantity if inv else 120
            reserved = inv.reserved_quantity if inv else 10
            cogs = Decimal(str(p.cost_price or 300))

            raw_sold = sku_sales_30d.get(p.sku, 24)
            # Base velocity units/day * festive multiplier
            daily_vel = max(0.4, (raw_sold / 30.0)) * multiplier
            doir = float(avail / daily_vel) if daily_vel > 0 else 999.0
            total_doir += doir

            if doir <= 14.0:
                status = "Critical Stockout Risk"
                imminent_stockout_cnt += 1
                lead_days = max(1, int(doir - 2))
                deadline = (today + timedelta(days=lead_days)).isoformat()
                reorder_units = max(100, int(daily_vel * 45 - avail))
                capital = (Decimal(str(reorder_units)) * cogs).quantize(cls.TWO_PLACES)
                total_working_capital += capital
                notes = f"High stockout risk! Supplier lead time is ~14 days. Place PO immediately to avoid losing Amazon Buy Box rank."
            elif doir <= 28.0:
                status = "Reorder Soon"
                deadline = (today + timedelta(days=int(doir - 14))).isoformat()
                reorder_units = max(50, int(daily_vel * 35 - avail))
                capital = (Decimal(str(reorder_units)) * cogs).quantize(cls.TWO_PLACES)
                total_working_capital += capital
                notes = f"Stock adequate for {int(doir)} days. Queue vendor PO to sustain buffer through peak demand."
            elif doir > 90.0:
                status = "Dead Stock / LTSF"
                dead_stock_cnt += 1
                deadline = "N/A"
                reorder_units = 0
                notes = f"Excess inventory ({int(doir)} days supply). Danger of Amazon FBA Long-Term Storage Fees (LTSF). Consider running a 15% discount deal."
            else:
                status = "Healthy"
                deadline = (today + timedelta(days=int(doir - 20))).isoformat()
                reorder_units = 0
                notes = f"Optimal inventory run-rate. Stock covers next {int(doir)} days."

            sku_forecasts.append(
                ForecastingSKUItem(
                    sku=p.sku,
                    title=p.title,
                    category=p.category or "General",
                    current_stock=avail,
                    reserved_stock=reserved,
                    daily_velocity_units=round(daily_vel, 1),
                    days_of_inventory_remaining=round(doir, 1),
                    seasonal_multiplier_applied=multiplier,
                    status=status,
                    recommended_reorder_units=reorder_units,
                    reorder_deadline_date=deadline,
                    working_capital_required=f"{capital:.2f}" if reorder_units > 0 else "0.00",
                    action_notes=notes,
                )
            )

        sku_forecasts.sort(key=lambda x: x.days_of_inventory_remaining)
        avg_doir = round(total_doir / len(products), 1) if products else 0.0

        return WorkingCapitalForecastResponse(
            currency="INR",
            season_mode=season_mode_label,
            total_skus_tracked=len(products),
            imminent_stockout_count=imminent_stockout_cnt,
            dead_stock_count=dead_stock_cnt,
            total_working_capital_required=f"{total_working_capital:.2f}",
            average_catalog_doir_days=avg_doir,
            forecast_horizon_days=30,
            sku_forecasts=sku_forecasts,
        )

