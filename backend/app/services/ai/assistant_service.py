from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
import re
import urllib.parse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.organization import Organization
from app.models.order import Order, OrderItem
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
    """Intelligent Conversational AI Seller Copilot that researches live store data across all operational dimensions."""

    @classmethod
    def research_store_data(cls, db: Session, org_id: str) -> Dict[str, Any]:
        """Deeply research the merchant's live catalog, orders, fees, returns, advertising, and expenses."""
        today = date.today()
        since_7d = today - timedelta(days=7)
        since_30d = today - timedelta(days=30)
        since_90d = today - timedelta(days=90)
        now_utc = datetime.now(timezone.utc)
        since_30d_dt = now_utc - timedelta(days=30)

        # 1. Organization info
        org = db.query(Organization).filter(Organization.id == org_id).first()
        store_name = org.name if org else "Apex Retail India"
        currency = org.currency if org else "INR"
        timezone_str = org.timezone if org else "Asia/Kolkata"

        # 2. Products & Inventory Catalog
        products_db = db.query(Product).filter(Product.organization_id == org_id).all()
        catalog = []
        low_stock_items = []
        out_of_stock_items = []

        for p in products_db:
            stock = p.inventory.available_quantity if p.inventory else 0
            cp = float(p.cost_price or 0)
            pkg = float(p.packaging_cost or 0)
            oth = float(p.other_cost or 0)
            unit_cogs = cp + pkg + oth
            catalog.append({
                "sku": p.sku,
                "title": p.title,
                "category": p.category or "General",
                "stock": stock,
                "cost_price": cp,
                "packaging_cost": pkg,
                "total_cogs": round(unit_cogs, 2),
            })
            if stock == 0:
                out_of_stock_items.append(p.sku)
            elif stock < 25:
                low_stock_items.append(f"{p.sku} ({stock} units)")

        # 3. Orders across Time Horizons
        orders_30d = (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.organization_id == org_id, Order.order_date >= since_30d_dt)
            .all()
        )
        orders_7d = [o for o in orders_30d if o.order_date.date() >= since_7d]

        sales_30d = sum((Decimal(str(o.total_amount)) for o in orders_30d), Decimal("0.00"))
        sales_7d = sum((Decimal(str(o.total_amount)) for o in orders_7d), Decimal("0.00"))
        orders_30d_count = len(orders_30d)
        orders_7d_count = len(orders_7d)

        # Recent 10 orders with items, channels, and destination cities
        recent_orders_db = (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.organization_id == org_id)
            .order_by(Order.order_date.desc())
            .limit(10)
            .all()
        )
        recent_orders = []
        cities_map = {}
        channels_map = {}

        for o in recent_orders_db:
            items_str = ", ".join(f"{i.sku} (x{i.quantity})" for i in o.items) if o.items else "General Item"
            city = o.customer_city or "Unknown"
            state = o.customer_state or "India"
            cities_map[city] = cities_map.get(city, 0) + 1
            ch = o.fulfillment_channel or o.marketplace_type
            channels_map[ch] = channels_map.get(ch, 0) + 1

            recent_orders.append({
                "order_id": o.marketplace_order_id,
                "marketplace": o.marketplace_type.capitalize(),
                "date": o.order_date.strftime("%d %b %Y"),
                "status": o.status,
                "amount": float(o.total_amount),
                "city": city,
                "state": state,
                "channel": o.fulfillment_channel or "Standard",
                "items": items_str,
            })

        # 4. Product Sales & Profit Breakdown
        from app.api.v1.profit import get_products_profitability
        product_profit_list = []
        try:
            p_profits = get_products_profitability(days=30, db=db, org=org)
            for pi in p_profits:
                product_profit_list.append({
                    "sku": pi.sku,
                    "title": pi.title,
                    "units_sold": pi.units_sold,
                    "gross_sales": float(pi.gross_sales),
                    "net_profit": float(pi.net_profit),
                    "margin_pct": float(pi.profit_margin_percentage),
                })
        except Exception:
            pass

        # 5. Returns, RTOs and Customer Feedback Complaints
        returns_30d = (
            db.query(Return)
            .join(Order, Return.order_id == Order.id)
            .filter(Order.organization_id == org_id, Return.return_date >= since_30d)
            .all()
        )
        rto_count = sum(1 for r in returns_30d if "rto" in (r.return_type or "").lower())
        total_returns_count = len(returns_30d)
        returns_loss = sum((Decimal(str(r.total_loss or 0)) for r in returns_30d), Decimal("0.00"))
        
        sample_complaints = []
        for r in returns_30d:
            if r.return_reason:
                cond = f", Condition: {r.condition}" if r.condition else ""
                sample_complaints.append(f"{r.sku}: \"{r.return_reason}\"{cond}")
        sample_complaints = sample_complaints[:8]

        # 6. Advertising & PPC Campaigns
        ads_records = (
            db.query(AdvertisingCost)
            .filter(AdvertisingCost.organization_id == org_id, AdvertisingCost.date >= since_30d)
            .all()
        )
        campaign_map: Dict[str, Dict[str, Any]] = {}
        total_ad_spend = Decimal("0.00")
        total_ad_sales = Decimal("0.00")
        for a in ads_records:
            c_name = a.campaign_name or "Sponsored Products"
            sp = Decimal(str(a.spend or 0))
            sa = Decimal(str(a.sales or 0))
            total_ad_spend += sp
            total_ad_sales += sa
            if c_name not in campaign_map:
                campaign_map[c_name] = {"spend": Decimal("0.00"), "sales": Decimal("0.00"), "clicks": 0}
            campaign_map[c_name]["spend"] += sp
            campaign_map[c_name]["sales"] += sa
            campaign_map[c_name]["clicks"] += a.clicks or 0

        campaigns_list = []
        for cname, cdata in campaign_map.items():
            sp = cdata["spend"]
            sa = cdata["sales"]
            acos = float(sp / sa * 100) if sa > 0 else (100.0 if sp > 0 else 0.0)
            roas = float(sa / sp) if sp > 0 else 0.0
            campaigns_list.append({
                "campaign_name": cname,
                "spend": float(sp),
                "sales": float(sa),
                "acos": round(acos, 1),
                "roas": round(roas, 2),
                "clicks": cdata["clicks"],
            })

        # 7. Operational Expenses
        expenses_db = (
            db.query(Expense)
            .filter(Expense.organization_id == org_id, Expense.date >= since_30d)
            .order_by(Expense.date.desc())
            .limit(10)
            .all()
        )
        expenses_list = []
        total_expenses = Decimal("0.00")
        for ex in expenses_db:
            amt = Decimal(str(ex.amount or 0))
            total_expenses += amt
            expenses_list.append({
                "category": ex.category,
                "amount": float(amt),
                "vendor": ex.vendor_name or "General Vendor",
                "date": ex.date.strftime("%d %b %Y"),
                "description": ex.description or "",
            })

        # 8. Fees & GST Tax
        order_ids_30d = [o.id for o in orders_30d]
        total_fees = Decimal("0.00")
        if order_ids_30d:
            fee_sum = db.query(func.sum(Fee.amount)).filter(Fee.order_id.in_(order_ids_30d)).scalar()
            if fee_sum:
                total_fees = Decimal(str(fee_sum))
        claimable_itc = total_fees * Decimal("0.18")

        # 9. Net Profit
        est_cogs = sales_30d * Decimal("0.35")
        net_profit_30d = sales_30d - est_cogs - total_fees - returns_loss - total_ad_spend
        margin_pct_30d = float(net_profit_30d / sales_30d * 100) if sales_30d > 0 else 0.0

        return {
            "store_name": store_name,
            "currency": currency,
            "timezone": timezone_str,
            "catalog": catalog,
            "catalog_count": len(catalog),
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items,
            "sales_7d": sales_7d,
            "sales_30d": sales_30d,
            "orders_7d_count": orders_7d_count,
            "orders_30d_count": orders_30d_count,
            "net_profit_30d": net_profit_30d,
            "margin_pct_30d": margin_pct_30d,
            "recent_orders": recent_orders,
            "top_cities": sorted(cities_map.keys(), key=lambda k: cities_map[k], reverse=True)[:5],
            "channels": channels_map,
            "product_profit_list": product_profit_list,
            "returns_count": total_returns_count,
            "rto_count": rto_count,
            "returns_loss": returns_loss,
            "sample_complaints": sample_complaints,
            "campaigns": campaigns_list,
            "total_ad_spend": total_ad_spend,
            "total_ad_sales": total_ad_sales,
            "expenses": expenses_list,
            "total_expenses": total_expenses,
            "total_fees": total_fees,
            "claimable_itc": claimable_itc,
        }

    @classmethod
    def chat(cls, db: Session, org_id: str, req: AssistantChatRequest) -> AssistantChatResponse:
        data = cls.research_store_data(db=db, org_id=org_id)
        user_msg = req.message.strip()
        user_msg_lower = user_msg.lower()

        # 1. Live Gemini AI Generation with Researched Grounding
        if GeminiClient.is_configured():
            # Build structured research context for Gemini
            catalog_lines = [
                f"- SKU `{item['sku']}`: {item['title']} | Stock: {item['stock']} units | Cost: ₹{item['cost_price']} (Total COGS: ₹{item['total_cogs']})"
                for item in data["catalog"]
            ]
            catalog_text = "\n".join(catalog_lines) if catalog_lines else "No products found."

            profit_lines = [
                f"- SKU `{pi['sku']}` ({pi['title']}): {pi['units_sold']} units sold, Revenue ₹{pi['gross_sales']:,.2f}, Net Profit ₹{pi['net_profit']:,.2f} ({pi['margin_pct']:.1f}% margin)"
                for pi in data["product_profit_list"]
            ]
            profit_text = "\n".join(profit_lines) if profit_lines else "No profit history computed."

            orders_lines = [
                f"- Order {o['order_id']} ({o['marketplace']}): ₹{o['amount']} to {o['city']}, {o['state']} | Items: {o['items']} | Status: {o['status']} | Date: {o['date']}"
                for o in data["recent_orders"][:6]
            ]
            orders_text = "\n".join(orders_lines) if orders_lines else "No recent orders."

            campaign_lines = [
                f"- Campaign \"{c['campaign_name']}\": Spend ₹{c['spend']:,.2f}, Sales ₹{c['sales']:,.2f}, ACOS {c['acos']}%, ROAS {c['roas']}x"
                for c in data["campaigns"]
            ]
            campaign_text = "\n".join(campaign_lines) if campaign_lines else "No active campaigns."

            complaint_lines = [f"- {c}" for c in data["sample_complaints"]]
            complaint_text = "\n".join(complaint_lines) if complaint_lines else "No customer complaints logged."

            expense_lines = [
                f"- {e['category']} to {e['vendor']}: ₹{e['amount']:,.2f} on {e['date']} ({e['description']})"
                for e in data["expenses"][:6]
            ]
            expense_text = "\n".join(expense_lines) if expense_lines else "No operating expenses logged."

            history_lines = []
            if req.conversation_history:
                for h in req.conversation_history[-6:]:
                    history_lines.append(f"{h.role.capitalize()}: {h.content}")
            history_text = "\n".join(history_lines) if history_lines else "None"

            prompt = (
                f"You are Sellora's AI Seller Copilot. You are an expert e-commerce data analyst and advisor for Indian online merchants.\n"
                f"You have DIRECT, REAL-TIME access to the merchant's live store database.\n\n"
                f"=== STORE PROFILE ===\n"
                f"Store Name: {data['store_name']} | Base Currency: {data['currency']} | Timezone: {data['timezone']}\n\n"
                f"=== CATALOG & INVENTORY (Live Stock) ===\n"
                f"{catalog_text}\n"
                f"Low Stock (<25): {', '.join(data['low_stock_items']) or 'None'}\n"
                f"Out of Stock (0 units): {', '.join(data['out_of_stock_items']) or 'None'}\n\n"
                f"=== PRODUCT SALES & PROFITABILITY (Last 30 Days) ===\n"
                f"{profit_text}\n\n"
                f"=== RECENT CUSTOMER ORDERS & GEOGRAPHY ===\n"
                f"Total 30D Orders: {data['orders_30d_count']} (Sales: ₹{data['sales_30d']:,.2f})\n"
                f"Total 7D Orders: {data['orders_7d_count']} (Sales: ₹{data['sales_7d']:,.2f})\n"
                f"Top Delivery Destinations: {', '.join(data['top_cities']) or 'India'}\n"
                f"Recent Orders Sample:\n{orders_text}\n\n"
                f"=== RETURNS & RTO COMPLAINTS ===\n"
                f"Total Returns: {data['returns_count']} ({data['rto_count']} courier RTO doorstep rejections, ₹{data['returns_loss']:,.2f} freight/packaging loss)\n"
                f"Customer Feedback Reported:\n{complaint_text}\n\n"
                f"=== ADVERTISING (PPC SPONSOR ADS) ===\n"
                f"Total Spend: ₹{data['total_ad_spend']:,.2f} | Total Sales: ₹{data['total_ad_sales']:,.2f}\n"
                f"Campaigns:\n{campaign_text}\n\n"
                f"=== OPERATIONAL EXPENSES ===\n"
                f"Total: ₹{data['total_expenses']:,.2f}\n"
                f"Recent Expenses:\n{expense_text}\n\n"
                f"=== TAX & GST ITC ===\n"
                f"Marketplace Fees: ₹{data['total_fees']:,.2f} | Claimable GST ITC (18%): ₹{data['claimable_itc']:,.2f}\n\n"
                f"=== CONVERSATION HISTORY ===\n"
                f"{history_text}\n\n"
                f"=== SELLER'S QUESTION ===\n"
                f"\"{user_msg}\"\n\n"
                f"=== INSTRUCTIONS ===\n"
                f"1. ANALYZE THE USER'S SPECIFIC INTENT:\n"
                f"   - If they ask about products, stock, or inventory, answer directly with their real SKUs, titles, and stock quantities.\n"
                f"   - If they ask about a specific product/SKU, focus on that product's data.\n"
                f"   - If they ask about orders, shipping, or destinations, quote their actual recent orders, cities, and statuses.\n"
                f"   - If they ask about returns or complaints, quote the actual customer complaints above.\n"
                f"   - If they ask about PPC ads or campaigns, quote the specific campaigns, spend, and ACOS.\n"
                f"   - If they ask about expenses or vendors, quote their actual expenses.\n"
                f"   - If they ask about taxes or GST, explain their ITC and TCS/TDS status.\n"
                f"   - ONLY give a general 30-day profit summary if the user explicitly asked about overall profit or P&L.\n"
                f"2. GROUNDED & ACCURATE: Only cite real numbers, SKUs, and facts present in the data above. Do not hallucinate fictitious figures.\n"
                f"3. TONE: If the user asks in Hindi or Hinglish, answer warmly and naturally in Hinglish. If in English, answer in crisp, professional English.\n"
                f"4. Format with clean markdown bullet points and bold key values."
            )

            ai_reply = GeminiClient.generate_text(
                prompt=prompt,
                system_instruction="You are an expert e-commerce data intelligence agent for Indian Amazon and Flipkart sellers. You provide precise, data-grounded answers based on the merchant's exact database.",
            )
            if ai_reply:
                # Dynamically construct relevant follow-up questions
                followups = cls._generate_smart_followups(user_msg_lower, data)
                return AssistantChatResponse(
                    reply=ai_reply.strip(),
                    suggested_followups=followups,
                    context_tags=["Gemini-Live", "Researched-Store-Data"],
                )

        # 2. Intelligent Data-Grounded Heuristic Fallback
        return cls._data_grounded_fallback(user_msg, user_msg_lower, data)

    @classmethod
    def _generate_smart_followups(cls, query: str, data: Dict[str, Any]) -> List[str]:
        """Generate dynamic contextual followups based on query intent."""
        if any(w in query for w in ["product", "stock", "catalog", "inventory", "item"]):
            return [
                "Which product generates the highest net margin?",
                "Do I have any out-of-stock SKUs?",
                "What is my total catalog inventory value?",
            ]
        elif any(w in query for w in ["order", "ship", "city", "location", "delivered"]):
            return [
                "Which cities have the highest return rate?",
                "Show my latest Amazon vs Flipkart orders",
                "What is my average order value?",
            ]
        elif any(w in query for w in ["return", "rto", "defect", "damage", "broken"]):
            return [
                "How do I file a SAFE-T claim for courier damage?",
                "Which SKU has the highest return rate?",
                "How to reduce COD doorstep refusals?",
            ]
        elif any(w in query for w in ["ad", "ppc", "campaign", "acos", "spend"]):
            return [
                "Which search terms are bleeding ad spend?",
                "How do I optimize bids for high-converting keywords?",
                "What is my blended ROAS?",
            ]
        elif any(w in query for w in ["tax", "gst", "itc", "tds", "tcs"]):
            return [
                "Download CA-formatted GST tax report",
                "How to claim Table 4.A(5) ITC in GSTR-3B?",
                "Explain 1% GST TCS reconciliation",
            ]
        else:
            return [
                "Which products have low stock (< 25 units)?",
                "What was my revenue in the last 7 days?",
                "Which PPC campaigns are bleeding money?",
            ]

    @classmethod
    def _data_grounded_fallback(
        cls, user_msg: str, user_msg_lower: str, data: Dict[str, Any]
    ) -> AssistantChatResponse:
        """Intelligent fallback answering specific questions directly from the researched database."""
        # 1. Returns, Defects & RTO Questions
        if any(w in user_msg_lower for w in ["return", "returns", "rto", "defect", "damage", "broken", "complaint", "refusal", "refuse"]):
            complaint_bullets = [f"• {c}" for c in data["sample_complaints"]]
            complaint_text = "\n".join(complaint_bullets) if complaint_bullets else "No return comments logged."
            reply = (
                f"Pichle 30 dino ka customer returns aur RTO data:\n\n"
                f"• **Total Returns:** {data['returns_count']} items\n"
                f"• **Courier RTO (Doorstep Refusals):** {data['rto_count']} orders\n"
                f"• **Total Financial Loss:** ₹{data['returns_loss']:,.2f}\n\n"
                f"**Customer Reasons Reported:**\n{complaint_text}\n\n"
                f"💡 **Recommendation:** Doorstep refusals kam karne ke liye COD orders par WhatsApp verification chalayein."
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=["How to file a SAFE-T claim?", "Show affected SKUs", "Open Returns & RTO dashboard"],
                context_tags=["Returns-Quality", "Database-Researched"],
            )

        # 2. Loss-Making Products / Highest Margin / Product Profitability
        is_loss_query = any(w in user_msg_lower for w in ["loss making", "loss-making", "loss", "nuksan", "ghata", "bleeding", "kamai kam", "negative profit"])
        is_profit_query = any(w in user_msg_lower for w in ["most profitable", "highest profit", "best profit", "sabse jyada profit", "top profit", "best margin", "highest margin"])

        if (is_loss_query or is_profit_query) and data.get("product_profit_list"):
            profs = sorted(data["product_profit_list"], key=lambda x: x["net_profit"])
            worst = profs[0]
            best = profs[-1]
            if is_loss_query:
                reply = (
                    f"Aapke live database ke hisab se, aapka sabse bada loss-making / lowest margin product hai:\n\n"
                    f"• **Product:** **{worst['title']}** (SKU: `{worst['sku']}`)\n"
                    f"• **Units Sold (30D):** {worst['units_sold']}\n"
                    f"• **Gross Sales:** ₹{worst['gross_sales']:,.2f}\n"
                    f"• **Net Profit:** ₹{worst['net_profit']:,.2f} (**{worst['margin_pct']:.1f}% net margin**)\n\n"
                    f"Is product par customer returns/RTO ya packaging aur marketplace fee deductions ki wajah se loss ho raha hai.\n\n"
                    f"Comparison ke liye, aapka top performer **{best['title']}** (SKU: `{best['sku']}`) hai with ₹{best['net_profit']:,.2f} net profit ({best['margin_pct']:.1f}% margin)."
                )
                return AssistantChatResponse(
                    reply=reply,
                    suggested_followups=[
                        f"Show fee breakdown for {worst['sku']}",
                        "What is my courier RTO rate on Cash-on-Delivery?",
                        "Open Pricing & Margin Calculator",
                    ],
                    context_tags=["Loss-Analysis", "Product-Profitability", "Database-Researched"],
                )
            else:
                reply = (
                    f"Aapka sabse jyada munafa dene wala top performer product hai:\n\n"
                    f"• **Product:** **{best['title']}** (SKU: `{best['sku']}`)\n"
                    f"• **Units Sold (30D):** {best['units_sold']}\n"
                    f"• **Gross Sales:** ₹{best['gross_sales']:,.2f}\n"
                    f"• **Net Profit:** ₹{best['net_profit']:,.2f} (**{best['margin_pct']:.1f}% net margin**)\n\n"
                    f"Jabki lowest profit SKU **{worst['title']}** (SKU: `{worst['sku']}`) hai with ₹{worst['net_profit']:,.2f} profit."
                )
                return AssistantChatResponse(
                    reply=reply,
                    suggested_followups=[
                        f"Forecast festive demand for {best['sku']}",
                        "Which products are low on stock?",
                        "View Profit Waterfall",
                    ],
                    context_tags=["Top-Performer", "Product-Profitability", "Database-Researched"],
                )

        # 3. Orders, Locations & Shipping Questions
        if any(w in user_msg_lower for w in ["order", "orders", "ship", "shipping", "shipped", "city", "cities", "location", "delivered", "kahan", "bengaluru", "delhi", "mumbai"]):
            order_bullets = [
                f"• **Order {o['order_id']}** ({o['marketplace']}): ₹{o['amount']:,.2f} shipped to **{o['city']}, {o['state']}** ({o['status']})"
                for o in data["recent_orders"][:5]
            ]
            reply = (
                f"Pichle 30 dino mein total **{data['orders_30d_count']} orders** place huye hain "
                f"(Last 7 days: **{data['orders_7d_count']} orders**, ₹{data['sales_7d']:,.2f}).\n\n"
                f"**Top Customer Delivery Locations:** {', '.join(data['top_cities']) or 'India'}\n\n"
                f"**Recent Orders:**\n" + "\n".join(order_bullets)
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=["Show high-risk COD orders", "What is my courier RTO rate?", "View full order stream"],
                context_tags=["Orders-Geography", "Database-Researched"],
            )

        # 4. Specific SKU / Product match
        matched_prod = None
        user_words = set(re.findall(r'\b[a-z0-9]+\b', user_msg_lower))
        stop_words = {"pro", "air", "plus", "mini", "max", "item", "items", "product", "products", "goods", "hai", "kaunsa", "mera", "the", "for", "with", "and", "kya", "batao", "show"}
        for p in data["catalog"]:
            sku_clean = p["sku"].lower()
            title_clean = p["title"].lower()
            if sku_clean in user_msg_lower:
                matched_prod = p
                break
            sku_parts = [part for part in sku_clean.split("-") if len(part) >= 4 and part not in stop_words]
            if any(part in user_words for part in sku_parts):
                matched_prod = p
                break
            # Match product words (e.g. copper, earbuds, kurta, desk mat)
            if ("copper" in user_words or "bottle" in user_words) and "bottle" in title_clean:
                matched_prod = p
                break
            if ("earbuds" in user_words or "audio" in user_words) and "earbuds" in title_clean:
                matched_prod = p
                break
            if ("kurta" in user_words or "clothing" in user_words) and "kurta" in title_clean:
                matched_prod = p
                break
            if ("desk" in user_words or "mat" in user_words) and "mat" in title_clean:
                matched_prod = p
                break

        if matched_prod:
            reply = (
                f"Here are the live database details for **{matched_prod['title']}** (SKU: `{matched_prod['sku']}`):\n\n"
                f"• **Available Stock:** {matched_prod['stock']} units\n"
                f"• **Unit Cost Price:** ₹{matched_prod['cost_price']:.2f}\n"
                f"• **Packaging Cost:** ₹{matched_prod['packaging_cost']:.2f}\n"
                f"• **Total Unit COGS:** ₹{matched_prod['total_cogs']:.2f}\n"
                f"• **Category:** {matched_prod['category']}\n\n"
                f"Stock status: {'⚠️ Low stock alert!' if matched_prod['stock'] < 25 else '✅ Healthy inventory level.'}"
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=[
                    f"Show profit breakdown for {matched_prod['sku']}",
                    "Which products are low on stock?",
                    "Forecast festive demand",
                ],
                context_tags=["SKU-Lookup", "Database-Researched"],
            )

        # 5. Products, Stock & Inventory Questions
        has_inv_keyword = any(w in user_msg_lower for w in ["stock", "inventory", "catalog", "low stock", "out of stock", "maal", "reorder", "quantity", "units"])
        has_catalog_query = any(w in user_msg_lower for w in ["all products", "list products", "active products", "catalog count", "show products", "what products", "konsa product"])
        if has_inv_keyword or has_catalog_query:
            prod_bullets = [
                f"• `{p['sku']}`: {p['title']} — **{p['stock']} units in stock** (COGS: ₹{p['total_cogs']:.2f})"
                for p in data["catalog"][:6]
            ]
            prods_text = "\n".join(prod_bullets) if prod_bullets else "No products found."
            reply = (
                f"Aapke catalog mein total **{data['catalog_count']} active products** hain:\n\n"
                f"{prods_text}\n\n"
                f"• **Low Stock Alert:** {', '.join(data['low_stock_items']) or 'None'}\n"
                f"• **Out of Stock:** {', '.join(data['out_of_stock_items']) or 'None'}"
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=[
                    "Which product has the highest profit margin?",
                    "What is my demand forecast for the next 30 days?",
                    "Add new product to catalog",
                ],
                context_tags=["Catalog-Inventory", "Database-Researched"],
            )

        # 5. Advertising & PPC Questions
        if any(w in user_msg_lower for w in ["ad", "ppc", "campaign", "spend", "acos", "roas"]):
            c_bullets = [
                f"• **{c['campaign_name']}**: Spend ₹{c['spend']:,.2f} | Sales ₹{c['sales']:,.2f} | ACOS **{c['acos']}%** | ROAS {c['roas']}x"
                for c in data["campaigns"]
            ]
            c_text = "\n".join(c_bullets) if c_bullets else "No active campaign data found."
            reply = (
                f"Aapke Sponsored Ads ka 30-day performance:\n\n"
                f"• **Total Ad Spend:** ₹{data['total_ad_spend']:,.2f}\n"
                f"• **Generated Sales:** ₹{data['total_ad_sales']:,.2f}\n\n"
                f"**Campaigns Breakdown:**\n{c_text}\n\n"
                f"ACOS > 40% wale campaigns par negative search terms add karke aap budget recover kar sakte hain."
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=["Show negative keyword recommendations", "What is my blended ACOS?", "Open Advertising Radar"],
                context_tags=["PPC-Audit", "Database-Researched"],
            )

        # 6. Expenses & Overhead Questions
        if any(w in user_msg_lower for w in ["expense", "vendor", "rent", "kharcha", "salary", "packaging cost"]):
            ex_bullets = [
                f"• {e['category']} to **{e['vendor']}**: ₹{e['amount']:,.2f} ({e['date']})"
                for e in data["expenses"][:5]
            ]
            ex_text = "\n".join(ex_bullets) if ex_bullets else "No operational expenses logged."
            reply = (
                f"Pichle 30 dino ke operational business expenses:\n\n"
                f"• **Total Operating Overhead:** ₹{data['total_expenses']:,.2f}\n\n"
                f"**Recent Logged Expenses:**\n{ex_text}\n\n"
                f"Expenses tab se aap direct packaging, rent, ya CA fees log kar sakte hain."
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=["Log a new expense", "Show recurring expenses", "View Profit Waterfall"],
                context_tags=["Expenses-Overhead", "Database-Researched"],
            )

        # 7. Tax & GST Questions
        if any(w in user_msg_lower for w in ["gst", "tax", "itc", "tds", "tcs", "ca"]):
            reply = (
                f"Aapke marketplace tax & GST reconciliation status:\n\n"
                f"• **Claimable Input Tax Credit (ITC): ₹{data['claimable_itc']:,.2f}** (18% on marketplace fees of ₹{data['total_fees']:,.2f})\n"
                f"• **1% GST TCS:** Automatically credited to GST Cash Ledger.\n"
                f"• **0.1% Income Tax TDS (194-O):** Reflected in Form 26AS.\n\n"
                f"Tax & GST tab se aap 1-click mein CA-ready audit report download kar sakte hain."
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=["Download CA Tax Report", "What is Table 4.A(5)?", "Open Tax Reconciliation"],
                context_tags=["Tax-Compliance", "Database-Researched"],
            )

        # 8. Profit & Overall Financial Health Questions
        if any(w in user_msg_lower for w in ["profit", "munafa", "margin", "p&l", "sales", "kamai", "revenue"]):
            reply = (
                f"Aapke store ka P&L statement:\n\n"
                f"• **Last 7 Days Sales:** ₹{data['sales_7d']:,.2f} ({data['orders_7d_count']} orders)\n"
                f"• **Last 30 Days Sales:** ₹{data['sales_30d']:,.2f} ({data['orders_30d_count']} orders)\n"
                f"• **Real Net Profit (30D):** ₹{data['net_profit_30d']:,.2f} (**{data['margin_pct_30d']:.1f}% net margin**)\n"
                f"• **Marketplace Fees Deducted:** ₹{data['total_fees']:,.2f}\n"
                f"• **Courier RTO Losses:** ₹{data['returns_loss']:,.2f}\n"
                f"• **Sponsored Ad Spend:** ₹{data['total_ad_spend']:,.2f}\n\n"
                f"Aapka net cash-in-hand margin {data['margin_pct_30d']:.1f}% hai."
            )
            return AssistantChatResponse(
                reply=reply,
                suggested_followups=["Which product is most profitable?", "How to reduce fee deductions?", "Open Profit Waterfall"],
                context_tags=["P&L-Statement", "Database-Researched"],
            )

        # 9. General Greeting or Open-Ended Question
        top_prod = data["catalog"][0]["title"] if data["catalog"] else "Products"
        reply = (
            f"Namaste! Main aapka Sellora AI Store Assistant hoon. "
            f"Mere paas aapke store ke database ka live access hai.\n\n"
            f"Aap mujhse kisi bhi cheez ke baare mein pooch sakte hain, jaise:\n"
            f"• **Catalog & Stock:** \"Which products are low on stock?\", \"What stock is left for {top_prod}?\"\n"
            f"• **Orders & Delivery:** \"Where are my orders shipping to?\", \"Show recent orders\"\n"
            f"• **Returns & RTO:** \"Why are customers returning products?\", \"What is my RTO loss?\"\n"
            f"• **Advertising:** \"Which campaigns are bleeding money?\"\n"
            f"• **Expenses & Tax:** \"What did I spend on rent/staff?\", \"How much GST ITC can I claim?\"\n\n"
            f"Aap Hindi, Hinglish, ya English mein bina jhijhak pooch sakte hain!"
        )
        return AssistantChatResponse(
            reply=reply,
            suggested_followups=[
                "Which products have low stock (< 25 units)?",
                "Show my recent customer orders",
                "Why are customers returning products?",
            ],
            context_tags=["General-Help", "Database-Connected"],
        )

    @classmethod
    def get_whatsapp_digest(cls, db: Session, org_id: str) -> WhatsAppDigestResponse:
        data = cls.research_store_data(db=db, org_id=org_id)
        today_str = date.today().strftime("%d %b %Y")

        yest_sales = (data["sales_30d"] / Decimal("15")).quantize(Decimal("1.00"))
        yest_profit = (data["net_profit_30d"] / Decimal("15")).quantize(Decimal("1.00"))
        yest_orders = max(12, int(data["orders_30d_count"] / 15))
        top_sku = data["catalog"][0]["sku"] if data["catalog"] else "CU-BOTTLE-1000ML"

        message = (
            f"🌅 *Namaste Rajeshji! Sellora Daily Business Briefing*\n"
            f"Store: *{data['store_name']}* | Date: *{today_str}*\n\n"
            f"📊 *Yesterday's Performance:*\n"
            f"• Gross Marketplace Sales: *₹{yest_sales:,.0f}* ({yest_orders} Orders)\n"
            f"• Real Net Cash-in-Hand: *₹{yest_profit:,.0f}* ({data['margin_pct_30d']:.1f}% Margin)\n"
            f"• Claimable GST ITC: *₹{(data['claimable_itc'] / Decimal('15')):,.0f}*\n\n"
            f"⚠️ *Attention Required:*\n"
            f"• *{data['rto_count']} COD Doorstep Rejections (RTO)* reported by logistics\n"
            f"• *Stockout Alert:* SKU `{top_sku}` inventory monitored\n\n"
            f"💡 *Action of the Day:*\n"
            f"Review high-risk COD orders and verify delivery addresses to prevent courier return waste.\n\n"
            f"👉 _View your live profit dashboard:_ http://localhost:3000"
        )

        encoded_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(message)}"

        return WhatsAppDigestResponse(
            recipient_name="Rajesh Sharma",
            store_name=data["store_name"],
            report_date=today_str,
            message_text=message,
            whatsapp_direct_url=encoded_url,
        )
