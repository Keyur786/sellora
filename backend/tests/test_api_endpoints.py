import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_dashboard_endpoint(client):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "organization" in data
    assert "top_products" in data
    assert "recent_orders" in data
    assert data["summary"]["currency"] == "INR"


def test_products_endpoint(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0
    first = products[0]
    assert "sku" in first
    assert "cost_price" in first
    assert "packaging_cost" in first


def test_product_cogs_update(client):
    # Fetch first product
    products = client.get("/api/v1/products").json()
    first_id = products[0]["id"]

    # Update COGS
    patch_resp = client.patch(
        f"/api/v1/products/{first_id}",
        json={"cost_price": 375.50, "packaging_cost": 25.00, "other_cost": 15.00},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert float(updated["cost_price"]) == 375.50
    assert float(updated["packaging_cost"]) == 25.00
    assert float(updated["other_cost"]) == 15.00


def test_orders_endpoint(client):
    response = client.get("/api/v1/orders")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert data["total_count"] > 0
    first_order = data["orders"][0]
    assert "marketplace_type" in first_order
    assert "total_amount" in first_order


def test_marketplaces_endpoint_and_sync(client):
    # List marketplaces
    response = client.get("/api/v1/marketplaces")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) >= 2
    first_account = accounts[0]

    # Trigger sync
    sync_resp = client.post(f"/api/v1/marketplaces/{first_account['id']}/sync")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["status"] == "completed"
    assert "records synchronized" in sync_data["message"]
