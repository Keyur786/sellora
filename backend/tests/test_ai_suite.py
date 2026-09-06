import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.organization import Organization
from app.models.order import Order


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_cfo_insights_endpoint(client):
    response = client.get("/api/v1/ai/cfo-insights?days=30")
    assert response.status_code == 200
    data = response.json()
    assert data["period_days"] == 30
    assert "current_profit" in data
    assert "headline" in data
    assert isinstance(data["diagnoses"], list)
    assert len(data["diagnoses"]) > 0
    assert isinstance(data["recommended_actions"], list)
    assert len(data["recommended_actions"]) > 0


def test_listing_generator_amazon_and_flipkart(client):
    # Test Amazon
    payload_amz = {
        "title": "Pure Copper Water Bottle 1000ml Hammered",
        "category": "Home & Kitchen",
        "marketplace": "amazon",
        "material_or_specs": "99.6% Pure Copper, 1000ml Capacity",
        "key_features": "Leak proof silicone seal, Ayurvedic health benefits, handcrafted hammered texture",
        "target_audience": "Health-conscious individuals, office professionals",
        "selling_price": 799.00
    }
    res_amz = client.post("/api/v1/ai/generate-listing", json=payload_amz)
    assert res_amz.status_code == 200
    d_amz = res_amz.json()
    assert d_amz["marketplace"] == "amazon"
    assert len(d_amz["optimized_title"]) > 10
    assert len(d_amz["bullet_points"]) == 5
    assert len(d_amz["backend_search_terms"]) > 0
    assert len(d_amz["vernacular_keywords"]) > 0
    assert "product_description" in d_amz

    # Test Flipkart
    payload_fk = {
        "title": "Floral Cotton Kurti for Women",
        "category": "Clothing",
        "marketplace": "flipkart",
        "material_or_specs": "100% Breathable Jaipuri Cotton",
        "key_features": "Calf length, round neck, machine washable",
        "target_audience": "College and office wear",
        "selling_price": 549.00
    }
    res_fk = client.post("/api/v1/ai/generate-listing", json=payload_fk)
    assert res_fk.status_code == 200
    d_fk = res_fk.json()
    assert d_fk["marketplace"] == "flipkart"
    assert len(d_fk["bullet_points"]) == 5


def test_orders_rto_risk_summary_and_single_order(client):
    # Test Summary
    res_sum = client.get("/api/v1/ai/orders-risk-summary?limit=20")
    assert res_sum.status_code == 200
    d_sum = res_sum.json()
    assert d_sum["total_orders_evaluated"] > 0
    assert "high_risk_count" in d_sum
    assert len(d_sum["orders"]) > 0

    first_order = d_sum["orders"][0]
    assert "risk_score" in first_order
    assert first_order["risk_level"] in ("Low", "Medium", "High")
    assert len(first_order["risk_reasons"]) > 0
    assert len(first_order["recommended_mitigation"]) > 0

    # Test Single Order Endpoint
    order_id = first_order["order_id"]
    res_single = client.get(f"/api/v1/ai/order-rto-risk/{order_id}")
    assert res_single.status_code == 200
    d_single = res_single.json()
    assert d_single["order_id"] == order_id


def test_return_insights_sentiment(client):
    res = client.get("/api/v1/ai/return-insights?days=60")
    assert res.status_code == 200
    data = res.json()
    assert data["period_days"] == 60
    assert "top_issues" in data
    assert isinstance(data["actionable_supplier_feedback"], list)
    assert len(data["actionable_supplier_feedback"]) > 0


def test_dispute_drafter_safe_t_and_damage(client):
    payload = {
        "order_id": "408-9876543-1234567",
        "claim_type": "wrong_item_received",
        "marketplace": "amazon",
        "loss_amount": 1299.00,
        "notes": "Customer returned used bar of soap instead of brand new copper jug."
    }
    res = client.post("/api/v1/ai/draft-dispute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["marketplace"] == "amazon"
    assert "SAFE-T" in data["subject_line"]
    assert "408-9876543-1234567" in data["formal_claim_letter"]
    assert len(data["required_evidence_checklist"]) >= 3
    assert "SAFE-T Policy" in data["policy_citation"]

