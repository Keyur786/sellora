from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint responds with 200 and healthy database."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["project"] == "Sellora"
    assert data["database"] == "healthy"


def test_root():
    """Verify root endpoint provides API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Sellora" in data["message"]
