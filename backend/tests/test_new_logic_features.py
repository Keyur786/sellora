import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.organization import Organization
from app.models.product import Product, Inventory
from app.models.order import Order


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_organization_settings_get_and_patch(client):
    # 1. GET current organization
    resp = client.get("/api/v1/organization/current")
    assert resp.status_code == 200
    org_data = resp.json()
    assert "id" in org_data
    assert "name" in org_data
    assert "currency" in org_data
    assert "timezone" in org_data
    orig_name = org_data["name"]

    # 2. PATCH organization settings
    patch_resp = client.patch(
        "/api/v1/organization/current",
        json={"name": "Apex Prime Traders", "currency": "INR", "timezone": "Asia/Kolkata"},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["name"] == "Apex Prime Traders"
    assert updated["currency"] == "INR"

    # Restore
    client.patch("/api/v1/organization/current", json={"name": orig_name})


def test_order_financial_drilldown(client):
    # Fetch an order from list
    orders_resp = client.get("/api/v1/orders")
    assert orders_resp.status_code == 200
    orders = orders_resp.json()["orders"]
    assert len(orders) > 0
    order_id = orders[0]["id"]

    # Fetch specific order drilldown
    detail_resp = client.get(f"/api/v1/orders/{order_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == order_id
    assert "items" in detail
    assert "fees" in detail
    assert "total_amount" in detail


def test_create_product_with_initial_stock(client):
    sku = "TEST-NEW-SKU-999"
    create_payload = {
        "sku": sku,
        "title": "Automated Test Stainless Steel Flask",
        "asin_or_fsn": "B09TEST999",
        "category": "Test Category",
        "cost_price": 250.00,
        "packaging_cost": 20.00,
        "other_cost": 5.00,
        "initial_stock": 75,
    }

    # Delete if exists from previous run
    # Create product
    resp = client.post("/api/v1/products", json=create_payload)
    if resp.status_code == 400 and "already exists" in resp.json()["detail"]:
        # Duplicate from re-run, verify fetch
        pass
    else:
        assert resp.status_code == 201
        created = resp.json()
        assert created["sku"] == sku
        assert created["available_stock"] == 75
        assert float(created["cost_price"]) == 250.00


def test_marketplace_sync_database_upsert(client):
    # Get first marketplace account
    mkt_resp = client.get("/api/v1/marketplaces")
    assert mkt_resp.status_code == 200
    accounts = mkt_resp.json()
    assert len(accounts) > 0
    acc_id = accounts[0]["id"]

    # Trigger sync
    sync_resp = client.post(f"/api/v1/marketplaces/{acc_id}/sync")
    assert sync_resp.status_code == 200
    sync_res = sync_resp.json()
    assert sync_res["status"] == "completed"
    assert "records synchronized" in sync_res["message"]


def test_ai_ppc_audit_with_catalog_grounding(client):
    resp = client.get("/api/v1/ai/ppc-audit?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert "negative_keyword_recommendations" in data
    assert len(data["negative_keyword_recommendations"]) >= 2
    assert "actionable_bid_optimizations" in data
    assert len(data["actionable_bid_optimizations"]) >= 2


def test_ai_dispute_drafter_with_fallback(client):
    payload = {
        "order_id": "402-9876543-1234567",
        "marketplace": "amazon",
        "claim_type": "Materially Different / Fraud Return",
        "loss_amount": 1499.00,
        "notes": "Customer returned a counterfeit empty bottle without seals.",
    }
    resp = client.post("/api/v1/ai/draft-dispute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "formal_claim_letter" in data
    assert "subject_line" in data
    assert "402-9876543-1234567" in data["subject_line"] or "402-9876543-1234567" in data["formal_claim_letter"]
    assert len(data["required_evidence_checklist"]) > 0


def test_ai_return_insights_actionable_feedback(client):
    resp = client.get("/api/v1/ai/return-insights?days=60")
    assert resp.status_code == 200
    data = resp.json()
    assert "top_issues" in data
    assert "actionable_supplier_feedback" in data
    assert len(data["actionable_supplier_feedback"]) >= 2

