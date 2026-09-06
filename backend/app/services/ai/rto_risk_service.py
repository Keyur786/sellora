from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.order import Order
from app.schemas.ai import RTORiskResponse, OrdersRTOSummaryResponse


HIGH_RTO_STATES = {
    "bihar", "uttar pradesh", "jharkhand", "assam", "odisha", 
    "west bengal", "madhya pradesh", "rajasthan"
}

METRO_TIER1_CITIES = {
    "mumbai", "delhi", "bengaluru", "bangalore", "hyderabad", 
    "pune", "chennai", "kolkata", "ahmedabad"
}


class RTORiskService:
    """Predictive COD RTO Risk Engine assessing probability of doorstep rejection."""

    @classmethod
    def evaluate_order(cls, order: Order) -> RTORiskResponse:
        total = Decimal(str(order.total_amount or 0))
        # Look for payment clues or default to COD if not explicitly marked prepaid
        city = (order.customer_city or "").strip()
        state = (order.customer_state or "").strip()
        
        # Check if prepaid or COD from marketplace order attributes
        # Most Amazon India/Flipkart orders without explicit prepaid tag default to COD
        is_cod = True
        if order.status.lower() in ("shipped", "delivered") and "prepaid" in (order.fulfillment_channel or "").lower():
            is_cod = False

        score = 15  # Base baseline
        reasons = []

        if is_cod:
            score += 25
            reasons.append("Cash-on-Delivery (COD) payment selected by customer.")
            
            # High ticket COD has severe buyer hesitation
            if total > Decimal("2000.00"):
                score += 30
                reasons.append(f"High order value (₹{total:,.2f}) on COD significantly increases doorstep buyer refusal risk.")
            elif total > Decimal("1000.00"):
                score += 15
                reasons.append("Moderate order value (> ₹1,000) on COD increases courier rejection probability.")
            
            # Geographic checks
            if state.lower() in HIGH_RTO_STATES:
                score += 20
                reasons.append(f"Destination state ({state}) has higher courier non-delivery and RTO rates on EasyShip/Ekart.")
            elif city.lower() in METRO_TIER1_CITIES:
                score -= 10
                reasons.append(f"Delivery to Tier-1 Metro hub ({city}) improves courier delivery success rate.")
        else:
            reasons.append("Prepaid transaction (Zero doorstep payment refusal risk).")
            score = 10

        # Clamp score between 5 and 95
        final_score = max(5, min(95, score))

        if final_score >= 60:
            level = "High"
            mitigation = "Send automated WhatsApp confirmation with an instant ₹50 discount coupon to convert order to UPI prepaid before dispatch."
        elif final_score >= 35:
            level = "Medium"
            mitigation = "Trigger automated WhatsApp OTP or SMS confirmation to verify address and phone validity prior to printing shipping label."
        else:
            level = "Low"
            mitigation = "Standard dispatch recommended. Low risk of courier delivery failure."

        return RTORiskResponse(
            order_id=order.id,
            marketplace_order_id=order.marketplace_order_id,
            payment_method="COD" if is_cod else "Prepaid",
            total_amount=f"{total:.2f}",
            customer_city=city or None,
            customer_state=state or None,
            risk_score=final_score,
            risk_level=level,
            risk_reasons=reasons,
            recommended_mitigation=mitigation,
        )

    @classmethod
    def get_orders_summary(cls, db: Session, org_id: str, limit: int = 50) -> OrdersRTOSummaryResponse:
        orders = (
            db.query(Order)
            .filter(Order.organization_id == org_id)
            .order_by(Order.order_date.desc())
            .limit(limit)
            .all()
        )

        evaluated = [cls.evaluate_order(o) for o in orders]
        high_cnt = sum(1 for e in evaluated if e.risk_level == "High")
        med_cnt = sum(1 for e in evaluated if e.risk_level == "Medium")
        low_cnt = sum(1 for e in evaluated if e.risk_level == "Low")

        # Potential loss: estimated ~₹140 freight loss per high-risk COD rejection
        loss_at_risk = Decimal(str(high_cnt)) * Decimal("140.00")

        return OrdersRTOSummaryResponse(
            total_orders_evaluated=len(evaluated),
            high_risk_count=high_cnt,
            medium_risk_count=med_cnt,
            low_risk_count=low_cnt,
            potential_rto_loss_at_risk=f"{loss_at_risk:.2f}",
            orders=evaluated,
        )

