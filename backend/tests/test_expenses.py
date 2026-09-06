import uuid
from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_expense_crud_and_summary():
    with TestClient(app) as c:
        # Create an expense
        payload = {
            "category": "Warehouse Rent",
            "amount": 15000.00,
            "currency": "INR",
            "date": str(date.today()),
            "description": "Monthly warehouse space rental",
            "vendor_name": "Shree Ram Warehousing",
            "payment_method": "Bank Transfer",
            "is_recurring": True,
        }
        res = c.post("/api/v1/expenses", json=payload)
        assert res.status_code == 201
        created = res.json()
        assert created["category"] == "Warehouse Rent"
        assert float(created["amount"]) == 15000.00
        expense_id = created["id"]

        # List expenses
        list_res = c.get("/api/v1/expenses?category=Warehouse")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) >= 1
        assert any(e["id"] == expense_id for e in items)

        # Get summary
        summary_res = c.get("/api/v1/expenses/summary")
        assert summary_res.status_code == 200
        summary = summary_res.json()
        assert float(summary["total_expenses"]) >= 15000.00
        assert len(summary["categories"]) >= 1

        # Delete expense
        del_res = c.delete(f"/api/v1/expenses/{expense_id}")
        assert del_res.status_code == 204

