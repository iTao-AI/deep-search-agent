from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_active_surface_uses_canonical_identity():
    from scripts.check_canonical_identity import find_forbidden_terms

    assert find_forbidden_terms(ROOT) == []


def test_health_service_uses_canonical_identifier():
    from fastapi.testclient import TestClient
    from api.server import app

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "decision-research-agent",
    }
