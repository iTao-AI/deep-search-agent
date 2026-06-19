from datetime import datetime, timezone

import pytest

from api.review_gate import ReviewGate, ReviewGateMismatch
from api.review_models import ReviewDecisionRecord


def _decision(*, review_id: str) -> ReviewDecisionRecord:
    return ReviewDecisionRecord(
        decision_id="decision_1",
        run_id="run_1",
        review_id=review_id,
        review_revision=1,
        action="approve",
        reason=None,
        actor_fingerprint="actor_hash",
        request_hash="request_hash",
        accepted_state_version=3,
        created_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )


def test_gate_interrupt_payload_contains_only_opaque_ids(tmp_path):
    gate = ReviewGate(
        checkpoint_path=str(tmp_path / "checkpoints.db"),
        decision_loader=lambda decision_id: None,
    )

    interrupt_value = gate.ensure_waiting(
        workflow_id="rwf_1",
        checkpoint_thread_id="review_rwf_1",
        run_id="run_1",
        review_id="review_1",
        review_revision=1,
    )

    assert interrupt_value == {
        "workflow_id": "rwf_1",
        "run_id": "run_1",
        "review_id": "review_1",
        "review_revision": 1,
        "allowed_actions": ["approve", "reject"],
    }
    assert "evidence" not in str(interrupt_value).lower()
    assert "query" not in str(interrupt_value).lower()


def test_gate_reopens_and_resumes_authoritative_decision(tmp_path):
    path = str(tmp_path / "checkpoints.db")
    decisions = {"decision_1": _decision(review_id="review_1")}
    first = ReviewGate(path, decisions.get)
    first.ensure_waiting(
        workflow_id="rwf_1",
        checkpoint_thread_id="review_rwf_1",
        run_id="run_1",
        review_id="review_1",
        review_revision=1,
    )

    reopened = ReviewGate(path, decisions.get)
    result = reopened.resume(
        checkpoint_thread_id="review_rwf_1",
        decision_id="decision_1",
    )

    assert result["decision_id"] == "decision_1"
    assert result["action"] == "approve"


def test_gate_rejects_cross_review_decision(tmp_path):
    path = str(tmp_path / "checkpoints.db")
    decisions = {"decision_1": _decision(review_id="review_other")}
    gate = ReviewGate(path, decisions.get)
    gate.ensure_waiting(
        workflow_id="rwf_1",
        checkpoint_thread_id="review_rwf_1",
        run_id="run_1",
        review_id="review_1",
        review_revision=1,
    )

    with pytest.raises(
        ReviewGateMismatch,
        match="checkpoint_decision_mismatch",
    ):
        gate.resume(
            checkpoint_thread_id="review_rwf_1",
            decision_id="decision_1",
        )


def test_gate_inspection_distinguishes_absent_interrupted_and_completed(tmp_path):
    path = str(tmp_path / "checkpoints.db")
    decisions = {"decision_1": _decision(review_id="review_1")}
    gate = ReviewGate(path, decisions.get)

    assert gate.inspect("review_missing").status == "absent"
    gate.ensure_waiting(
        workflow_id="rwf_1",
        checkpoint_thread_id="review_rwf_1",
        run_id="run_1",
        review_id="review_1",
        review_revision=1,
    )
    assert gate.inspect("review_rwf_1").status == "interrupted"

    gate.resume(
        checkpoint_thread_id="review_rwf_1",
        decision_id="decision_1",
    )
    completed = gate.inspect("review_rwf_1")
    assert completed.status == "completed"
    assert completed.decision_id == "decision_1"
    assert completed.action == "approve"
