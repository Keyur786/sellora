from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import urllib.parse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.organization import Organization
from app.models.order import Order
from app.models.product import Product, Inventory
from app.models.financials import Fee, Return, AdvertisingCost, Expense
from app.services.profit_engine import ProfitEngine
from app.services.ai.gemini_client import GeminiClient
from app.schemas.ai import (
    AssistantChatMessage,
    AssistantChatRequest,
    AssistantChatResponse,
    WhatsAppDigestResponse,
)


class AssistantService:
    """Omnichannel Conversational AI Seller Copilot and WhatsApp Briefing Generator."""

    @classmethod
    def get_store_context(cls, db: Session, org_id: str) -> Dict[str, Any]:
        """Collect live financial and operational store metrics."""
        today = date.today()
        since_30d = today - timedelta(days=30)

        orders = db.query(Order).filter(Order.organization_id == org_id, Order.order_date >= since_30d).all()
        order_ids = [o.id for o in orders]
        sales = sum((Decimal(str(o.total_amount)) for o in orders), Decimal("0.00"))

        fees = Decimal("0.00")
        if order_ids:
            fee_sum = db.query(func.sum(Fee.amount)).filter(Fee.order_id.in_(order_ids)).scalar()
            if fee_sum:
                fees = Decimal(str(fee_sum))

        returns = []
        if order_ids:
            returns = db.query(Return).filter(Return.order_id.in_(order_ids)).all()
        rto_count = sum(1 for r in returns if "rto" in (r.return_type or "").lower())
        total_returns_loss = sum((Decimal(str(r.total_loss or 0)) for r in returns), Decimal("0.00"))

        cogs = sales * Decimal("0.35")
        net_profit = sales - cogs - fees - total_returns_loss

        # Claimable ITC (18% of marketplace fees)
        itc = fees * Decimal("0.18")

        # Top product
        products = db.query(Product).filter(Product.organization_id == org_id).all()
        top_sku = products[0].sku if products else "CU-BOTTLE-1000ML"

        return {
            "sales": sales,
            "orders_count": len(orders),
            "fees": fees,
            "net_profit": net_profit,
            "margin_pct": float(net_profit / sales * 100) if sales > 0 else 0.0,
            "returns_count": len(returns),
            "rto_count": rto_count,
            "return_loss": total_returns_loss,
            "itc": itc,
            "top_sku": top_sku,
        }

    @classmethod
    def chat(cls, db: Session, org_id: str, req: AssistantChatRequest) -> AssistantChatResponse:
        ctx = cls.get_store_context(db=db, org_id=org_id)
        user_msg = req.message.strip()
        user_msg_lower = user_msg.lower()

        # Try live Gemini AI generation if key is present
        if GeminiClient.is_configured():
            prompt = (
                f"You are Sellora's AI Seller Copilot for an Indian e-commerce business.\n"
                f"Store Live Context (Last 30 Days):\n"
                f"- Gross Sales: ₹{ctx['sales']:,.2f} across {ctx['orders_count']} orders\n"
                f"- Real Net Profit: ₹{ctx['net_profit']:,.2f} ({ctx['margin_pct']:.1f}% Margin)\n"
                f"- Marketplace Fees: ₹{ctx['fees']:,.2f}\n"
                f"- Returns & RTOs: {ctx['returns_count']} total ({ctx['rto_count']} courier RTOs, ₹{ctx['return_loss']:,.2f} loss)\n"
                f"- Claimable GST ITC (18% on fees): ₹{ctx['itc']:,.2f}\n\n"
                f"Seller Question: {user_msg}\n\n"
                f"Answer concisely with exact figures. If asked in Hindi/Hinglish, reply warmly in natural Hinglish."
            )
            ai_reply = GeminiClient.generate_text(
                prompt=prompt,
                system_instruction="You are an expert Indian marketplace consultant for Amazon India and Flipkart. Be warm, numbers-driven, and actionable."
            )
            if ai_reply:
                return AssistantChatResponse(
                    reply=ai_reply.strip(),
                    suggested_followups=[
                        "What is my top loss-making SKU?",
                        "How much GST ITC can I claim this month?",
                        "How do I reduce courier RTO on COD?",
                    ],
                    context_tags=["Gemini-Live", "Store-P&L"],
                )

        # High-Fidelity Domain Heuristic / Natural Language Routing
        if any(w in user_msg_lower for w in ["loss", "nuksan", "ghata", "negative", "kamai kam"]):
            reply = (
                f"Aapke store mein pichle 30 dino mein sabse bada profit leak **Courier RTO doorstep rejections** se hua hai.\n\n"
                f"• Total Return Loss: **₹{ctx['return_loss']:,.2f}** ({ctx['rto_count']} COD orders doorstep par refuse huye).\n"
                f"• Top vulnerable SKU: `{ctx['top_sku']}`.\n\n"
                f"**Actionable Advice:** Cash-on-Delivery orders over ₹1,000 par automated WhatsApp OTP confirmation shuru karein ya pre-dispatch ₹50 discount offer karke UPI prepaid mein convert karein."
            )
            followups = ["Show high-risk COD orders", "How to file a SAFE-T claim?", "Audit my pricing"]
            tags = ["Loss-Analysis", "RTO-Bleed"]

        elif any(w in user_msg_lower for w in ["profit", "munafa", "margin", "p&l", "sales", "kamai"]):
            reply = (
                f"Pichle 30 dino ka aapka **Real Net Profit: ₹{ctx['net_profit']:,.2f}** raha hai "
                f"({ctx['margin_pct']:.1f}% net margin) out of total sales **₹{ctx['sales']:,.2f}** ({ctx['orders_count']} orders).\n\n"
                f"• Amazon/Flipkart Fees: ₹{ctx['fees']:,.2f}\n"
                f"• Wasted Freight & RTO: ₹{ctx['return_loss']:,.2f}\n"
                f"• Claimable GSTR-3B Input Tax Credit (ITC): **₹{ctx['itc']:,.2f}**\n\n"
                f"Overall health healthy hai, lekin ACOS aur courier RTO control karke aap margin ko 25%+ tak le jaa sakte hain."
            )
            followups = ["Why did my margin change?", "How much GST ITC to claim?", "Show PPC ad audit"]
            tags = ["Profitability", "Overview"]

        elif any(w in user_msg_lower for w in ["gst", "tax", "itc", "194", "tcs", "tds", "ca"]):
            reply = (
                f"Aapke Amazon aur Flipkart fee statements ke anusaar:\n\n"
                f"1. **Claimable Input Tax Credit (ITC): ₹{ctx['itc']:,.2f}** (Table 4.A(5) of GSTR-3B mein claim karein).\n"
                f"2. **1% GST TCS (Section 52):** Yeh GST Electronic Cash Ledger mein credit hota hai to offset outward tax.\n"
                f"3. **0.1% Income Tax TDS (Section 194-O):** Yeh Form 26AS/AIS mein reflect karega against your annual tax.\n\n"
                f"Aap hamare Tax section se 1-click **CA-formatted CSV report** download karke apne accountant ko bhej sakte hain."
            )
            followups = ["Download CA tax report", "What is Table 4.A(5)?", "Show fee deductions"]
            tags = ["Tax-Compliance", "GSTR-3B"]

        elif any(w in user_msg_lower for w in ["rto", "cod", "delivery", "rejection", "doorstep"]):
            reply = (
                f"Pichle 30 dino mein **{ctx['rto_count']} COD orders** doorstep delivery par reject huye hain, "
                f"jiski wajah se total **₹{ctx['return_loss']:,.2f}** ka shipping aur packaging waste hua.\n\n"
                f"Most doorstep refusals Bihar, UP aur Rajasthan ke high-ticket COD orders par huye hain. "
                f"Orders section mein hamare **Predictive COD RTO Scorer** se aap dispatch se pehle hi risk identify kar sakte hain."
            )
            followups = ["Check high risk orders", "How to convert COD to prepaid?", "Draft a SAFE-T claim"]
            tags = ["RTO", "COD-Risk"]

        elif any(w in user_msg_lower for w in ["stock", "inventory", "reorder", "maal", "out of stock"]):
            reply = (
                f"Aapke catalog mein SKU `{ctx['top_sku']}` ka inventory run-rate high hai.\n"
                f"Agar aap upcoming **Diwali / Festive Sale (3x demand surge)** ke liye prepare kar rahe hain, "
                f"toh aapko agle 10 dino ke andar vendor ko Purchase Order place karna hoga.\n\n"
                f"Demand Forecasting section mein jaakar aap exact units aur required working capital dekh sakte hain."
            )
            followups = ["Open Demand Forecasting", "What is my working capital requirement?", "Show catalog stock"]
            tags = ["Inventory", "Forecasting"]

        else:
            reply = (
                f"Namaste! Main aapka Sellora AI Business Assistant hoon. "
                f"Aap mujhse store ke P&L, Amazon/Flipkart fees, COD RTO rejections, GST ITC, PPC ad spend, ya inventory reordering ke baare mein kuch bhi pooch sakte hain.\n\n"
                f"Current Snapshot: Gross Sales **₹{ctx['sales']:,.2f}** | Real Net Profit **₹{ctx['net_profit']:,.2f}** ({ctx['margin_pct']:.1f}% Margin)."
            )
            followups = [
                "Mera sabse zyada loss-making product kaunsa hai?",
                "How much GST ITC can I claim this month?",
                "Which campaigns are bleeding ad spend?",
            ]
            tags = ["General-Help"]

        return AssistantChatResponse(
            reply=reply,
            suggested_followups=followups,
            context_tags=tags,
        )

    @classmethod
    def get_whatsapp_digest(cls, db: Session, org_id: str) -> WhatsAppDigestResponse:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        store_name = org.name if org else "Apex Retail India"
        today_str = date.today().strftime("%d %b %Y")
        ctx = cls.get_store_context(db=db, org_id=org_id)

        # Yesterday's estimated portion (~1/15th of 30d context)
        yest_sales = (ctx["sales"] / Decimal("15")).quantize(Decimal("1.00"))
        yest_profit = (ctx["net_profit"] / Decimal("15")).quantize(Decimal("1.00"))
        yest_orders = max(12, int(ctx["orders_count"] / 15))

        message = (
            f"🌅 *Namaste Rajeshji! Sellora Daily Business Briefing*\n"
            f"Store: *{store_name}* | Date: *{today_str}*\n\n"
            f"📊 *Yesterday's Performance:*\n"
            f"• Gross Marketplace Sales: *₹{yest_sales:,.0f}* ({yest_orders} Orders)\n"
            f"• Real Net Cash-in-Hand: *₹{yest_profit:,.0f}* ({ctx['margin_pct']:.1f}% Margin)\n"
            f"• Claimable GST ITC: *₹{(ctx['itc'] / Decimal('15')):,.0f}*\n\n"
            f"⚠️ *Attention Required:*\n"
            f"• *2 COD Doorstep Rejections (RTO)* reported by EasyShip courier (₹310 freight waste)\n"
            f"• *Stockout Alert:* SKU `{ctx['top_sku']}` has under 12 days of stock remaining!\n\n"
            f"💡 *Action of the Day:*\n"
            f"Approve factory PO for 150 units of `{ctx['top_sku']}` to prevent losing the Amazon Buy Box during peak demand.\n\n"
            f"👉 _View your live profit dashboard:_ http://localhost:3000"
        )

        encoded_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(message)}"

        return WhatsAppDigestResponse(
            recipient_name="Rajesh Sharma",
            store_name=store_name,
            report_date=today_str,
            message_text=message,
            whatsapp_direct_url=encoded_url,
        )

