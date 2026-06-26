import os

from fastapi.testclient import TestClient


def test_health_endpoint_bypasses_api_key_auth():
    os.environ["API_SECRET"] = "test-key"
    from api.server import app

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "decision-research-agent"}
