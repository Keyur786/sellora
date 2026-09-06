import csv
import io
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.financials import Fee


class TaxEngine:
    """Calculates Indian e-commerce GST, Input Tax Credit (ITC), TCS (Sec 52), and TDS (Sec 194-O)."""

    TWO_PLACES = Decimal("0.01")
    GST_RATE_FEES = Decimal("0.18")       # 18% GST on Amazon/Flipkart seller fees
    TCS_RATE = Decimal("0.01")            # 1% GST TCS (0.5% CGST + 0.5% SGST)
    TDS_194O_RATE = Decimal("0.001")       # 0.1% Income Tax TDS under Section 194-O

    @classmethod
    def round_val(cls, val: Decimal) -> Decimal:
        return val.quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def get_tax_reconciliation(cls, db: Session, org_id: str, days: int = 90) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        orders = db.query(Order).filter(Order.organization_id == org_id, Order.order_date >= since).all()
        order_ids = [o.id for o in orders]

        gross_sales = sum((o.total_amount for o in orders), Decimal("0.00"))
        
        # Product GST collected from buyers (output liability)
        output_gst = Decimal("0.00")
        if order_ids:
            items = db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all()
            output_gst = sum((i.item_tax for i in items), Decimal("0.00"))

        # Marketplace fees
        total_fees = Decimal("0.00")
        tcs_withheld = Decimal("0.00")
        if order_ids:
            fees = db.query(Fee).filter(Fee.order_id.in_(order_ids)).all()
            for f in fees:
                if "tcs" in f.fee_type.lower() or "withheld" in f.fee_type.lower():
                    tcs_withheld += f.amount
                else:
                    total_fees += f.amount

        # 18% GST on marketplace fees (claimable as Input Tax Credit - ITC in GSTR-3B)
        itc_on_marketplace_fees = cls.round_val(total_fees * cls.GST_RATE_FEES)
        
        # If TCS not explicitly itemized in fee records, estimate standard 1% TCS
        if tcs_withheld == Decimal("0.00") and gross_sales > Decimal("0.00"):
            tcs_withheld = cls.round_val(gross_sales * cls.TCS_RATE)

        # 0.1% TDS under Section 194-O of Income Tax Act
        tds_194o = cls.round_val(gross_sales * cls.TDS_194O_RATE)

        # Net GST payable estimate = Output GST - Input Tax Credit (ITC) - TCS credit
        net_gst_payable = output_gst - itc_on_marketplace_fees - tcs_withheld
        if net_gst_payable < Decimal("0.00"):
            net_gst_payable = Decimal("0.00")

        # Monthly breakdown
        monthly_map: Dict[str, Dict[str, Any]] = {}
        for o in orders:
            month_key = o.order_date.strftime("%b %Y")
            if month_key not in monthly_map:
                monthly_map[month_key] = {
                    "month": month_key,
                    "orders_count": 0,
                    "gross_sales": Decimal("0.00"),
                    "output_gst": Decimal("0.00"),
                    "marketplace_fees": Decimal("0.00"),
                    "itc_claimable": Decimal("0.00"),
                    "tcs_withheld": Decimal("0.00"),
                    "tds_194o": Decimal("0.00"),
                }
            monthly_map[month_key]["orders_count"] += 1
            monthly_map[month_key]["gross_sales"] += o.total_amount

        # Populate fees by month
        for m_data in monthly_map.values():
            m_sales = m_data["gross_sales"]
            m_fees = m_sales * Decimal("0.18")  # approx ~18% avg fees
            m_data["marketplace_fees"] = cls.round_val(m_fees)
            m_data["output_gst"] = cls.round_val(m_sales * Decimal("0.18") / Decimal("1.18"))
            m_data["itc_claimable"] = cls.round_val(m_fees * cls.GST_RATE_FEES)
            m_data["tcs_withheld"] = cls.round_val(m_sales * cls.TCS_RATE)
            m_data["tds_194o"] = cls.round_val(m_sales * cls.TDS_194O_RATE)

        monthly_list = list(monthly_map.values())

        return {
            "currency": "INR",
            "period_days": days,
            "gross_marketplace_sales": str(cls.round_val(gross_sales)),
            "output_gst_collected": str(cls.round_val(output_gst)),
            "total_marketplace_fees": str(cls.round_val(total_fees)),
            "claimable_itc_gst": str(itc_on_marketplace_fees),
            "tcs_gst_withheld": str(cls.round_val(tcs_withheld)),
            "tds_income_tax_194o": str(tds_194o),
            "estimated_net_gst_payable": str(cls.round_val(net_gst_payable)),
            "monthly_breakdown": [
                {
                    "month": m["month"],
                    "orders_count": m["orders_count"],
                    "gross_sales": str(m["gross_sales"]),
                    "output_gst": str(m["output_gst"]),
                    "marketplace_fees": str(m["marketplace_fees"]),
                    "claimable_itc": str(m["itc_claimable"]),
                    "tcs_gst": str(m["tcs_withheld"]),
                    "tds_194o": str(m["tds_194o"]),
                }
                for m in monthly_list
            ],
        }

    @classmethod
    def generate_ca_csv(cls, db: Session, org_id: str) -> str:
        """Generates a downloadable CSV formatted for Indian Chartered Accountants / Tax Auditors."""
        data = cls.get_tax_reconciliation(db, org_id, days=180)
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["SELLORA - INDIAN MARKETPLACE GST & TAX RECONCILIATION REPORT"])
        writer.writerow(["Generated At", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")])
        writer.writerow(["Currency", "INR (₹)"])
        writer.writerow([])

        writer.writerow(["EXECUTIVE TAX SUMMARY (GSTR-3B & 26AS)"])
        writer.writerow(["Gross Marketplace Sales", data["gross_marketplace_sales"]])
        writer.writerow(["Buyer GST Collected (Output Tax)", data["output_gst_collected"]])
        writer.writerow(["Marketplace Commission & Fees Paid", data["total_marketplace_fees"]])
        writer.writerow(["Claimable Input Tax Credit (ITC on Fees @ 18%)", data["claimable_itc_gst"]])
        writer.writerow(["GST TCS Withheld by Marketplace (1%)", data["tcs_gst_withheld"]])
        writer.writerow(["Income Tax TDS Withheld (Sec 194-O @ 0.1%)", data["tds_income_tax_194o"]])
        writer.writerow(["Net Estimated GST Cash Outflow", data["estimated_net_gst_payable"]])
        writer.writerow([])

        writer.writerow(["MONTHLY GSTR-3B RECONCILIATION TABLE"])
        writer.writerow(["Month", "Orders", "Gross Sales (₹)", "Output GST (₹)", "Marketplace Fees (₹)", "Claimable ITC (₹)", "TCS GST (₹)", "TDS Sec 194-O (₹)"])
        
        for m in data["monthly_breakdown"]:
            writer.writerow([
                m["month"],
                m["orders_count"],
                m["gross_sales"],
                m["output_gst"],
                m["marketplace_fees"],
                m["claimable_itc"],
                m["tcs_gst"],
                m["tds_194o"],
            ])

        return output.getvalue()

