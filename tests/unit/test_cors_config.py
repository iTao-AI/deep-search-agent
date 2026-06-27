"""CORS configuration contract tests."""

from api.cors_config import get_allowed_origins, validate_cors_origin


CANONICAL_ENV = "DECISION_RESEARCH_AGENT_CORS_ALLOWED_ORIGIN"


def test_cors_denies_browser_origins_by_default(monkeypatch) -> None:
    monkeypatch.delenv(CANONICAL_ENV, raising=False)
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)

    assert get_allowed_origins() == []
    assert validate_cors_origin("http://localhost:5173") is False


def test_cors_allows_one_canonical_configured_origin(monkeypatch) -> None:
    monkeypatch.setenv(CANONICAL_ENV, "https://example.com")

    assert get_allowed_origins() == ["https://example.com"]
    assert validate_cors_origin("https://example.com") is True
    assert validate_cors_origin("https://other.example.com") is False


def test_cors_does_not_accept_retired_frontend_origin_alias(monkeypatch) -> None:
    monkeypatch.delenv(CANONICAL_ENV, raising=False)
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:5173")

    assert get_allowed_origins() == []
