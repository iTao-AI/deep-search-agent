import pytest
from fastapi.testclient import TestClient

from api.server import app
from tests.unit.test_review_repository import _required_review_run


def _url(run_id, review_id):
    return f"/api/runs/{run_id}/reviews/{review_id}/decisions"


@pytest.fixture
def required_review_run(tmp_path, monkeypatch):
    fixture = _required_review_run(tmp_path, suffix="api")
    monkeypatch.setenv("TASKS_DB_PATH", fixture.db_path)
    return fixture


@pytest.fixture
def approve_request():
    return {
        "decision_id": "decision_approve",
        "review_revision": 1,
        "action": "approve",
        "expected_state_version": 2,
    }


@pytest.fixture
def auth(monkeypatch):
    monkeypatch.setenv("DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL", "true")
    monkeypatch.setenv("API_SECRET", "correct")
    return {"X-API-Key": "correct"}


def test_decision_api_is_disabled_by_default(
    required_review_run,
    approve_request,
    monkeypatch,
):
    monkeypatch.delenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        raising=False,
    )
    monkeypatch.delenv("API_SECRET", raising=False)

    response = TestClient(app).post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=approve_request,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "durable_hitl_disabled"


def test_enabled_decision_api_fails_closed_without_api_secret(
    required_review_run,
    approve_request,
    monkeypatch,
):
    monkeypatch.setenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        "true",
    )
    monkeypatch.delenv("API_SECRET", raising=False)

    response = TestClient(app).post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=approve_request,
    )

    assert response.status_code == 503
    assert response.json()["code"] == "review_auth_not_configured"


def test_flag_and_auth_are_checked_before_body_validation(
    required_review_run,
    monkeypatch,
):
    url = _url(required_review_run.run_id, required_review_run.review_id)
    monkeypatch.delenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        raising=False,
    )
    monkeypatch.delenv("API_SECRET", raising=False)

    disabled = TestClient(app).post(url, json={})
    assert disabled.status_code == 404
    assert disabled.json()["code"] == "durable_hitl_disabled"

    monkeypatch.setenv("DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL", "true")
    unconfigured = TestClient(app).post(url, json={})
    assert unconfigured.status_code == 503
    assert unconfigured.json()["code"] == "review_auth_not_configured"


def test_wrong_key_is_rejected(
    required_review_run,
    approve_request,
    monkeypatch,
):
    monkeypatch.setenv("DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL", "true")
    monkeypatch.setenv("API_SECRET", "correct")

    response = TestClient(app).post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=approve_request,
        headers={"X-API-Key": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_api_key"


def test_authenticated_invalid_body_returns_bounded_contract_error(
    required_review_run,
    auth,
):
    response = TestClient(app).post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json={},
        headers=auth,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_review_decision"
    assert "errors" not in response.json()


def test_decision_api_accepts_and_replays_same_request(
    required_review_run,
    approve_request,
    auth,
):
    client = TestClient(app)
    first = client.post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=approve_request,
        headers=auth,
    )
    second = client.post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=approve_request,
        headers=auth,
    )

    assert first.status_code == second.status_code == 202
    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True


def test_conflicting_decision_returns_actionable_409(
    required_review_run,
    approve_request,
    auth,
):
    client = TestClient(app)
    first = client.post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=approve_request,
        headers=auth,
    )
    assert first.status_code == 202
    conflicting = {
        **approve_request,
        "decision_id": "decision_conflicting",
        "action": "reject",
        "reason": "Evidence boundary was not accepted.",
    }

    response = client.post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=conflicting,
        headers=auth,
    )

    assert response.status_code == 409
    body = response.json()
    request_id = body.pop("request_id")
    assert request_id.startswith("request_")
    assert body == {
        "code": "review_already_decided",
        "problem": "This review revision already has an accepted decision.",
        "cause": "A conflicting decision was submitted.",
        "fix": "Fetch the run and use the persisted decision result.",
        "retryable": False,
        "run_id": required_review_run.run_id,
    }
