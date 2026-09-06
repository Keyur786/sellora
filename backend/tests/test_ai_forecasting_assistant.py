import pytest
from starlette.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_forecasting_endpoint_standard_and_diwali(client):
    # Standard season
    res_std = client.get("/api/v1/ai/forecasting?season=standard")
    assert res_std.status_code == 200
    d_std = res_std.json()
    assert d_std["total_skus_tracked"] > 0
    assert len(d_std["sku_forecasts"]) > 0
    assert "Standard" in d_std["season_mode"]

    first_item = d_std["sku_forecasts"][0]
    assert "days_of_inventory_remaining" in first_item
    assert first_item["seasonal_multiplier_applied"] == 1.0
    assert first_item["status"] in (
        "Critical Stockout Risk",
        "Reorder Soon",
        "Healthy",
        "Dead Stock / LTSF",
    )

    # Diwali 3x surge season
    res_diwali = client.get("/api/v1/ai/forecasting?season=diwali")
    assert res_diwali.status_code == 200
    d_diwali = res_diwali.json()
    assert "Diwali" in d_diwali["season_mode"]
    assert d_diwali["sku_forecasts"][0]["seasonal_multiplier_applied"] == 3.0
    # Working capital should be required under 3x rush
    assert float(d_diwali["total_working_capital_required"]) >= 0


def test_assistant_chat_endpoint_english_and_hinglish(client):
    # English Query
    res_en = client.post(
        "/api/v1/ai/chat",
        json={"message": "What is my total net profit this month?"}
    )
    assert res_en.status_code == 200
    d_en = res_en.json()
    assert "Net Profit" in d_en["reply"] or "₹" in d_en["reply"]
    assert len(d_en["suggested_followups"]) > 0

    # Hinglish Query
    res_hi = client.post(
        "/api/v1/ai/chat",
        json={"message": "Mera sabse bada loss making product kaunsa hai?"}
    )
    assert res_hi.status_code == 200
    d_hi = res_hi.json()
    assert "loss" in d_hi["reply"].lower() or "rto" in d_hi["reply"].lower()


def test_assistant_researched_multi_domain_queries(client):
    # 1. Catalog & Stock Lookup for specific product
    res_stock = client.post(
        "/api/v1/ai/chat",
        json={"message": "How much stock do I have left for the copper bottle?"}
    )
    assert res_stock.status_code == 200
    data_stock = res_stock.json()
    assert "stock" in data_stock["reply"].lower() or "cogs" in data_stock["reply"].lower()
    assert len(data_stock["suggested_followups"]) > 0

    # 2. Orders & Shipping Geography
    res_orders = client.post(
        "/api/v1/ai/chat",
        json={"message": "Where are my customer orders shipping to?"}
    )
    assert res_orders.status_code == 200
    data_orders = res_orders.json()
    assert "order" in data_orders["reply"].lower() or "delhi" in data_orders["reply"].lower() or "bengaluru" in data_orders["reply"].lower()

    # 3. Customer Returns & Complaints
    res_returns = client.post(
        "/api/v1/ai/chat",
        json={"message": "Why are customers returning products and what is my RTO?"}
    )
    assert res_returns.status_code == 200
    data_returns = res_returns.json()
    assert "return" in data_returns["reply"].lower() or "rto" in data_returns["reply"].lower()

    # 4. Multi-turn Conversation with conversation_history
    res_history = client.post(
        "/api/v1/ai/chat",
        json={
            "message": "And how can I reduce these returns?",
            "conversation_history": [
                {"role": "user", "content": "What is my return rate?"},
                {"role": "assistant", "content": "Your return rate is 8.5% with 14 returns."}
            ]
        }
    )
    assert res_history.status_code == 200
    assert len(res_history.json()["reply"]) > 10


def test_whatsapp_morning_digest_endpoint(client):
    res = client.get("/api/v1/ai/whatsapp-digest")
    assert res.status_code == 200
    data = res.json()
    assert "Rajesh" in data["recipient_name"]
    assert "Apex Retail" in data["store_name"]
    assert "Namaste" in data["message_text"]
    assert "https://api.whatsapp.com/send?text=" in data["whatsapp_direct_url"]

