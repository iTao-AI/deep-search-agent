"""Test API Key authentication middleware."""
import os
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient


class TestAuthMiddleware:
    """Test X-API-Key middleware behavior."""

    def test_no_key_returns_401(self):
        """Request without X-API-Key header returns 401."""
        os.environ["API_SECRET"] = "test-key"
        from api.server import app
        client = TestClient(app)
        response = client.get("/api/runs/nonexistent")
        assert response.status_code == 401
        body = response.json()
        assert "API_SECRET" in body.get("detail", "")

    def test_wrong_key_returns_401(self):
        """Wrong API key returns 401."""
        os.environ["API_SECRET"] = "test-key"
        from api.server import app
        client = TestClient(app)
        response = client.get(
            "/api/runs/nonexistent",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    def test_correct_key_passes(self):
        """Correct API key passes through to endpoint logic."""
        os.environ["API_SECRET"] = "test-key"
        from api.server import app
        client = TestClient(app)
        response = client.get(
            "/api/runs/nonexistent",
            headers={"X-API-Key": "test-key"},
        )
        # 404 not found (directory doesn't exist) — NOT 401
        assert response.status_code != 401

    def test_cors_preflight_bypasses_api_key_auth(self):
        """Browser preflight has no X-API-Key and must reach CORS middleware."""
        env = os.environ.copy()
        env.update(
            {
                "API_SECRET": "test-key",
                "DECISION_RESEARCH_AGENT_CORS_ALLOWED_ORIGIN": "http://localhost:5173",
                "OPENAI_API_KEY": "test-cors-subprocess-only",
                "OPENAI_BASE_URL": "http://test",
                "LANGSMITH_TRACING": "false",
            }
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                """
from fastapi.testclient import TestClient
from api.server import app

response = TestClient(app).options(
    "/api/runs",
    headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-api-key,content-type",
    },
)
assert response.status_code == 200, response.text
assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
""",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert completed.returncode == 0, completed.stderr

    def test_api_secret_not_set_warns_and_passes(self):
        """If API_SECRET is not in env, log warning and skip auth."""
        if "API_SECRET" in os.environ:
            del os.environ["API_SECRET"]
        from api.server import app
        client = TestClient(app)
        response = client.get("/api/runs/nonexistent")
        # Should not be 401 when auth is disabled
        assert response.status_code != 401

    def test_websocket_protected(self):
        """WebSocket connection without proper key is rejected."""
        os.environ["API_SECRET"] = "test-key"
        from api.server import app
        client = TestClient(app)
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect("/ws/runs/test-run"):
                pass
        # Connection should be refused (auth failure)
