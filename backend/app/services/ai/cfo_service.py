from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, List
import json
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.order import Order, OrderItem
from app.models.financials import Fee, Return, Expense
from app.services.profit_engine import ProfitEngine
from app.services.ai.gemini_client import GeminiClient
from app.schemas.ai import CFOInsightResponse


class CFOService:
    """Virtual CFO service providing period-over-period variance analysis and root-cause diagnostics."""

    @classmethod
    def get_cfo_insights(cls, db: Session, org_id: str, days: int = 30) -> CFOInsightResponse:
        today = date.today()
        current_start = today - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        # 1. Fetch Current Period Metrics
        current_orders = db.query(Order).filter(Order.organization_id == org_id, Order.order_date >= current_start).all()
        current_order_ids = [o.id for o in current_orders]
        current_sales = sum((Decimal(str(o.total_amount)) for o in current_orders), Decimal("0.00"))
        
        current_fees = Decimal("0.00")
        if current_order_ids:
            fee_sum = db.query(func.sum(Fee.amount)).filter(Fee.order_id.in_(current_order_ids)).scalar()
            if fee_sum:
                current_fees = Decimal(str(fee_sum))

        current_returns = []
        if current_order_ids:
            current_returns = db.query(Return).filter(Return.order_id.in_(current_order_ids)).all()
        current_return_loss = sum((Decimal(str(r.total_loss or 0)) for r in current_returns), Decimal("0.00"))
        current_rto_count = sum(1 for r in current_returns if "rto" in (r.return_type or "").lower())

        current_expenses = db.query(Expense).filter(Expense.organization_id == org_id, Expense.date >= current_start).all()
        current_opex = sum((Decimal(str(e.amount)) for e in current_expenses), Decimal("0.00"))

        # Compute current net profit
        # Estimated product costs = ~35% of sales if not itemized
        current_cogs = Decimal("0.00")
        for order in current_orders:
            for item in order.items:
                if item.product and item.product.cost_price:
                    c = Decimal(str(item.product.cost_price)) + Decimal(str(item.product.packaging_cost or 0)) + Decimal(str(item.product.other_cost or 0))
                    current_cogs += c * item.quantity
                else:
                    current_cogs += Decimal(str(item.item_price)) * Decimal("0.35") * item.quantity

        current_net_profit = current_sales - current_cogs - current_fees - current_return_loss - current_opex

        # 2. Fetch Previous Period Metrics for Baseline
        prev_orders = db.query(Order).filter(Order.organization_id == org_id, Order.order_date >= previous_start, Order.order_date < current_start).all()
        prev_order_ids = [o.id for o in prev_orders]
        prev_sales = sum((Decimal(str(o.total_amount)) for o in prev_orders), Decimal("0.00"))

        prev_fees = Decimal("0.00")
        if prev_order_ids:
            p_fee_sum = db.query(func.sum(Fee.amount)).filter(Fee.order_id.in_(prev_order_ids)).scalar()
            if p_fee_sum:
                prev_fees = Decimal(str(p_fee_sum))

        prev_returns = []
        if prev_order_ids:
            prev_returns = db.query(Return).filter(Return.order_id.in_(prev_order_ids)).all()
        prev_return_loss = sum((Decimal(str(r.total_loss or 0)) for r in prev_returns), Decimal("0.00"))

        prev_expenses = db.query(Expense).filter(Expense.organization_id == org_id, Expense.date >= previous_start, Expense.date < current_start).all()
        prev_opex = sum((Decimal(str(e.amount)) for e in prev_expenses), Decimal("0.00"))

        prev_cogs = prev_sales * Decimal("0.35")
        prev_net_profit = prev_sales - prev_cogs - prev_fees - prev_return_loss - prev_opex

        # Calculate Variance
        variance = current_net_profit - prev_net_profit
        variance_pct = (variance / abs(prev_net_profit) * Decimal("100")) if prev_net_profit != Decimal("0.00") else Decimal("0.00")

        # 3. Formulate Prompt for Gemini AI
        prompt_data = {
            "period_days": days,
            "current_sales": f"₹{current_sales:,.2f}",
            "previous_sales": f"₹{prev_sales:,.2f}",
            "current_net_profit": f"₹{current_net_profit:,.2f}",
            "previous_net_profit": f"₹{prev_net_profit:,.2f}",
            "profit_variance": f"₹{variance:,.2f}",
            "profit_variance_pct": f"{variance_pct:.1f}%",
            "current_marketplace_fees": f"₹{current_fees:,.2f}",
            "current_return_loss": f"₹{current_return_loss:,.2f}",
            "current_rto_rejections": current_rto_count,
            "current_opex_expenses": f"₹{current_opex:,.2f}",
        }

        # Try Gemini Generation
        ai_response_text = None
        if GeminiClient.is_configured():
            prompt = (
                f"Analyze this Indian marketplace store performance:\n{json.dumps(prompt_data, indent=2)}\n"
                f"Output valid JSON with keys: headline, diagnoses (array of 3 strings), critical_alerts (array of 2 strings), recommended_actions (array of 3 strings)."
            )
            ai_response_text = GeminiClient.generate_text(
                prompt=prompt,
                system_instruction="You are a senior Virtual CFO for Indian Amazon and Flipkart sellers. Be concise, mathematically accurate, and action-oriented."
            )

        if ai_response_text:
            try:
                # Strip code fences if present
                clean_text = ai_response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                parsed = json.loads(clean_text)
                return CFOInsightResponse(
                    period_days=days,
                    current_profit=f"{current_net_profit:.2f}",
                    previous_profit=f"{prev_net_profit:.2f}",
                    profit_variance=f"{variance:.2f}",
                    profit_variance_pct=f"{variance_pct:.1f}",
                    headline=parsed.get("headline", f"Net Profit {'increased' if variance >= 0 else 'declined'} by {abs(variance_pct):.1f}% over the last {days} days"),
                    diagnoses=parsed.get("diagnoses", []),
                    critical_alerts=parsed.get("critical_alerts", []),
                    recommended_actions=parsed.get("recommended_actions", []),
                )
            except Exception:
                pass

        # Deterministic Domain-Expert Fallback
        diagnoses = []
        alerts = []
        actions = []

        if variance >= 0:
            headline = f"Strong performance: Net profit expanded by {variance_pct:.1f}% (+₹{abs(variance):,.2f})"
            diagnoses.append(f"Gross marketplace sales reached ₹{current_sales:,.2f} with healthy order velocity.")
            diagnoses.append(f"Marketplace commission and logistics overhead remained stable at {float(current_fees/current_sales*100):.1f}% of gross sales." if current_sales > 0 else "Fee rates remained controlled.")
            diagnoses.append(f"Courier RTO rejections remained within normal operational thresholds ({current_rto_count} units).")
            actions.append("Scale ad spend on your top 2 profit-margin SKUs to capture additional Buy Box volume.")
            actions.append("Reinvest positive cash flow into bulk packaging materials to negotiate 8-10% supplier discounts.")
            actions.append("Verify GSTR-3B Input Tax Credit (ITC) claim to reduce upcoming monthly outward GST liability.")
        else:
            headline = f"Profit alert: Net margin contracted by {abs(variance_pct):.1f}% (-₹{abs(variance):,.2f})"
            if current_return_loss > Decimal("1000.00"):
                diagnoses.append(f"Returns & Courier RTO drained ₹{current_return_loss:,.2f} directly from your bottom line ({current_rto_count} doorstep rejections).")
                alerts.append(f"High COD doorstep rejections ({current_rto_count} RTOs) are destroying unit profit margins.")
                actions.append("Enable WhatsApp pre-dispatch verification for Cash-on-Delivery orders over ₹1,000 to slash RTO.")
            else:
                diagnoses.append(f"Off-marketplace OPEX overhead of ₹{current_opex:,.2f} accounted for significant margin compression.")
            
            if current_fees > Decimal("2000.00"):
                diagnoses.append(f"Amazon & Flipkart fees (commission, weight handling, closing fees) totaled ₹{current_fees:,.2f}.")
                actions.append("Review selling prices around ₹999/₹499 thresholds to prevent dropping into higher commission fee slabs.")

            diagnoses.append("Fixed business operating overheads (rent, staff, software) absorbed a larger proportion of gross margin.")
            alerts.append("Net cash-in-hand is trailing reported marketplace sales due to itemized courier deductions.")
            actions.append("Conduct an audit of unsellable customer returns to submit SAFE-T claims for courier transit damage.")

        return CFOInsightResponse(
            period_days=days,
            current_profit=f"{current_net_profit:.2f}",
            previous_profit=f"{prev_net_profit:.2f}",
            profit_variance=f"{variance:.2f}",
            profit_variance_pct=f"{variance_pct:.1f}",
            headline=headline,
            diagnoses=diagnoses[:3],
            critical_alerts=alerts[:2] if alerts else ["Monitor Amazon EasyShip weight handling fee updates."],
            recommended_actions=actions[:3],
        )
