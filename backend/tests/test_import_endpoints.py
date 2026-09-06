import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_upload_amazon_date_range_report_endpoint(client):
    unique_order_id = f"402-TEST-{uuid.uuid4().hex[:7]}"
    csv_data = (
        "Date/Time,Settlement id,type,Order ID,SKU,Description,Quantity,Marketplace,fulfillment,city,state,postal code,Product Sales,Product Sales Tax,Shipping Credits,Shipping Credits Tax,Gift wrap credits,Giftwrap credits tax,Regulatory Fee,Tax on Regulatory Fee,Promotional Rebates,Promotional Rebates Tax,Marketplace Withheld Tax,Selling fees,FBA fees,Other transaction fees,Other,Total\n"
        f"05-Sep-2026 14:22:10 IST,182910291,Order,{unique_order_id},SKU-BOTTLE-HTTP,Water Bottle,1,amazon.in,Seller,Pune,Maharashtra,411001,999.00,152.38,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,-9.99,-144.88,-75.00,0.00,0.00,769.13\n"
    )
    files = {"file": ("amazon_date_range.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/import/amazon/date-range-report", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["orders_imported"] >= 1
    assert data["fees_extracted"] >= 1


def test_upload_cogs_csv_endpoint(client):
    csv_data = (
        "sku,title,product_cost,packaging_cost,other_cost\n"
        "SKU-BOTTLE-HTTP,Water Bottle,350.00,20.00,10.00\n"
    )
    files = {"file": ("cogs.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/import/products/cogs-csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["rows_processed"] == 1


def test_download_sample_template(client):
    response = client.get("/api/v1/import/sample/amazon_date_range")
    assert response.status_code == 200
    assert "Date/Time" in response.text

    cogs_response = client.get("/api/v1/import/sample/seller_cogs")
    assert cogs_response.status_code == 200
    assert "product_cost" in cogs_response.text
