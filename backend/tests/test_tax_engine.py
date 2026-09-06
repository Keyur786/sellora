from fastapi.testclient import TestClient
from app.main import app


def test_tax_reconciliation_endpoint():
    with TestClient(app) as c:
        res = c.get("/api/v1/tax/reconciliation")
        assert res.status_code == 200
        data = res.json()
        assert "gross_marketplace_sales" in data
        assert "claimable_itc_gst" in data
        assert "tcs_gst_withheld" in data
        assert "tds_income_tax_194o" in data
        assert float(data["claimable_itc_gst"]) >= 0.0
        assert len(data["monthly_breakdown"]) >= 1


def test_tax_export_csv_endpoint():
    with TestClient(app) as c:
        res = c.get("/api/v1/tax/export")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/csv")
        assert "SELLORA - INDIAN MARKETPLACE GST & TAX RECONCILIATION REPORT" in res.text
        assert "Claimable Input Tax Credit (ITC on Fees @ 18%)" in res.text

