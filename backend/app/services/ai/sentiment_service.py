from datetime import date, timedelta
from typing import List, Dict, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.financials import Return
from app.models.product import Product
from app.schemas.ai import SentimentInsightResponse, ReturnSentimentItem


class SentimentService:
    """Customer Return & Review Sentiment Miner identifying physical defects and packaging vulnerabilities."""

    @classmethod
    def get_return_insights(cls, db: Session, org_id: str, days: int = 60) -> SentimentInsightResponse:
        since_date = date.today() - timedelta(days=days)
        returns = (
            db.query(Return)
            .join(Order, Return.order_id == Order.id)
            .filter(Order.organization_id == org_id, Return.return_date >= since_date)
            .all()
        )

        total_returns = len(returns)
        if total_returns == 0:
            return SentimentInsightResponse(
                period_days=days,
                total_analyzed_returns=0,
                top_issues=[],
                actionable_supplier_feedback=[
                    "No return records logged for this period. Keep monitoring customer feedback."
                ],
            )

        # Categorize by root cause
        categories: Dict[str, List[Return]] = defaultdict(list)
        for r in returns:
            reason = (r.return_reason or "").lower()
            if r.return_type == "courier_rto" or "refused" in reason or "doorstep" in reason or "undelivered" in reason:
                categories["COD Doorstep Delivery Rejection"].append(r)
            elif "damage" in reason or "broken" in reason or "cracked" in reason or r.condition == "damaged":
                categories["Courier Transit & Handling Damage"].append(r)
            elif "size" in reason or "fit" in reason or "tight" in reason or "loose" in reason:
                categories["Sizing & Measurement Discrepancy"].append(r)
            elif "different" in reason or "wrong" in reason or "color" in reason or "picture" in reason:
                categories["Listing Photo & Color Expectation Mismatch"].append(r)
            else:
                categories["Product Performance & Quality Defect"].append(r)

        top_issues = []
        for cat_name, items in categories.items():
            pct = round((len(items) / total_returns) * 100, 1)
            skus = list(set([r.order.items[0].sku for r in items if r.order and r.order.items]))[:4]

            if cat_name == "COD Doorstep Delivery Rejection":
                summary = "Buyers changing mind upon courier arrival or unavailable during delivery attempt."
                remedy = "Implement automated pre-dispatch WhatsApp address verification and offer ₹50 discount for prepaid UPI conversion."
            elif cat_name == "Courier Transit & Handling Damage":
                summary = "Rough handling during inter-state hub transit causing internal packaging rupture."
                remedy = "Upgrade outer shipper to 5-ply corrugated carton with 15mm corner foam buffers to withstand conveyor sorting."
            elif cat_name == "Sizing & Measurement Discrepancy":
                summary = "Customers finding the dimensions or fit smaller than standard Indian expectations."
                remedy = "Update primary listing image with an annotated dimensional ruler diagram and recommend ordering one size up."
            elif cat_name == "Listing Photo & Color Expectation Mismatch":
                summary = "Studio lighting in product images causing customer dissatisfaction with actual product color tone."
                remedy = "Add unedited natural-daylight lifestyle photos and a 15-second unboxing video to the listing media gallery."
            else:
                summary = "Minor finish or mechanical inconsistencies reported after unpacking."
                remedy = "Mandate a 5-point QA checklist at packing station before sealing courier security tape."

            top_issues.append(
                ReturnSentimentItem(
                    root_cause=cat_name,
                    percentage=pct,
                    affected_skus=skus,
                    summary=summary,
                    remedy=remedy,
                )
            )

        top_issues.sort(key=lambda x: x.percentage, reverse=True)

        feedback = cls._generate_actionable_feedback(
            sample_reasons=[r.return_reason for r in returns if r.return_reason][:12],
            top_categories=list(categories.keys()),
        )

        return SentimentInsightResponse(
            period_days=days,
            total_analyzed_returns=total_returns,
            top_issues=top_issues,
            actionable_supplier_feedback=feedback,
        )

    @classmethod
    def _generate_actionable_feedback(cls, sample_reasons: List[str], top_categories: List[str]) -> List[str]:
        """Synthesize tailored supplier and packaging feedback using Gemini with fallback."""
        from app.services.ai.gemini_client import GeminiClient
        import json
        import re

        if GeminiClient.is_configured() and sample_reasons:
            reasons_text = "\n".join(f"- {r}" for r in sample_reasons[:8])
            cats_text = ", ".join(top_categories[:4])
            prompt = (
                "You are an Indian e-commerce packaging and supplier quality engineer.\n"
                "Analyze these actual customer return complaints and categories to provide 4 specific, actionable remedies for the seller.\n\n"
                f"Return Categories: {cats_text}\n\n"
                f"Customer Return Reasons:\n{reasons_text}\n\n"
                "Return a strict JSON object with this exact structure:\n"
                "{\n"
                '  "actionable_supplier_feedback": [\n'
                '    "Actionable bullet 1 with concrete packaging or vendor spec",\n'
                '    "Actionable bullet 2 with concrete packaging or vendor spec",\n'
                '    "Actionable bullet 3 with concrete packaging or vendor spec",\n'
                '    "Actionable bullet 4 with concrete packaging or vendor spec"\n'
                '  ]\n'
                "}\n"
                "Return ONLY the JSON object."
            )
            raw_ai = GeminiClient.generate_text(
                prompt=prompt,
                system_instruction="You are a quality control specialist diagnosing e-commerce returns for Indian merchants.",
            )
            if raw_ai:
                try:
                    clean_json = re.sub(r"^```(?:json)?\n?", "", raw_ai.strip(), flags=re.MULTILINE)
                    clean_json = re.sub(r"\n?```$", "", clean_json.strip(), flags=re.MULTILINE)
                    parsed = json.loads(clean_json)
                    items = parsed.get("actionable_supplier_feedback", [])
                    if len(items) >= 2:
                        return [str(i) for i in items[:4]]
                except Exception:
                    pass

        return [
            "Packaging Audit: Replace 3-ply boxes with 5-ply 150GSM boxes for any SKU shipping over 500km.",
            "Visual Clarity: Ensure primary listing images depict actual product without heavy saturation or studio filters.",
            "Pre-Dispatch Protocol: Enforce WhatsApp OTP verification for all Cash-on-Delivery shipments exceeding ₹1,000.",
            "Factory Quality Check: Reject incoming vendor batches showing > 2% finish defect rate.",
        ]

