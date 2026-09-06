import pytest
from starlette.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_ppc_ad_audit_endpoint(client):
    res = client.get("/api/v1/ai/ppc-audit?days=30")
    assert res.status_code == 200
    data = res.json()
    assert "total_ad_spend" in data
    assert "blended_acos_percentage" in data
    assert isinstance(data["campaigns"], list)
    assert len(data["campaigns"]) > 0
    assert isinstance(data["negative_keyword_recommendations"], list)
    assert len(data["negative_keyword_recommendations"]) > 0
    assert isinstance(data["actionable_bid_optimizations"], list)


def test_pricing_recommendations_endpoint(client):
    res = client.get("/api/v1/ai/pricing-recommendations")
    assert res.status_code == 200
    data = res.json()
    assert data["total_skus_evaluated"] > 0
    assert isinstance(data["sku_recommendations"], list)
    assert len(data["sku_recommendations"]) > 0

    first_item = data["sku_recommendations"][0]
    assert "breakeven_floor_price" in first_item
    assert "recommended_optimal_price" in first_item
    assert first_item["action_verdict"] in (
        "Reduce to Hit Fee Breakpoint",
        "Healthy",
        "Increase to Protect Margin",
    )


def test_price_simulation_endpoint(client):
    # Profitable Test Case (₹999 Selling Price, ₹350 Cost)
    payload_prof = {
        "cost_price": 350.0,
        "packaging_cost": 25.0,
        "shipping_cost": 75.0,
        "target_selling_price": 999.0,
        "category": "Home & Kitchen",
        "marketplace": "amazon",
    }
    res_prof = client.post("/api/v1/ai/simulate-price", json=payload_prof)
    assert res_prof.status_code == 200
    d_prof = res_prof.json()
    assert d_prof["is_profitable"] is True
    assert float(d_prof["net_unit_profit"]) > 0
    assert float(d_prof["breakeven_price"]) < 999.0
    assert "Viable" in d_prof["verdict"] or "Excellent" in d_prof["verdict"]

    # Loss-Making Test Case (₹250 Selling Price, ₹350 Cost)
    payload_loss = {
        "cost_price": 350.0,
        "packaging_cost": 25.0,
        "shipping_cost": 75.0,
        "target_selling_price": 250.0,
        "category": "Home & Kitchen",
        "marketplace": "amazon",
    }
    res_loss = client.post("/api/v1/ai/simulate-price", json=payload_loss)
    assert res_loss.status_code == 200
    d_loss = res_loss.json()
    assert d_loss["is_profitable"] is False
    assert float(d_loss["net_unit_profit"]) < 0
    assert "Loss" in d_loss["verdict"]

