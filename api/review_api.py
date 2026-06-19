from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
from typing import Any
import uuid

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.review_models import ReviewDecisionRequest, durable_hitl_enabled
from api.review_repository import ReviewConflict, accept_review_decision


router = APIRouter()


def _error(
    status: int,
    *,
    code: str,
    problem: str,
    cause: str,
    fix: str,
    retryable: bool,
    run_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "code": code,
            "problem": problem,
            "cause": cause,
            "fix": fix,
            "retryable": retryable,
            "run_id": run_id,
            "request_id": f"request_{uuid.uuid4().hex}",
        },
    )


def _authenticate(request: Request, *, run_id: str):
    if not durable_hitl_enabled():
        return None, _error(
            404,
            code="durable_hitl_disabled",
            problem="Durable review decisions are disabled.",
            cause="The P1B feature flag is false.",
            fix="Use the existing non-interrupt review bundle.",
            retryable=False,
            run_id=run_id,
        )
    secret = os.getenv("API_SECRET", "")
    if not secret:
        return None, _error(
            503,
            code="review_auth_not_configured",
            problem="Durable review authentication is not configured.",
            cause="API_SECRET is empty.",
            fix="Configure API_SECRET before enabling durable HITL.",
            retryable=False,
            run_id=run_id,
        )
    supplied = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(supplied, secret):
        return None, _error(
            401,
            code="invalid_api_key",
            problem="The review credential is invalid.",
            cause="X-API-Key did not match the configured service credential.",
            fix="Provide the configured X-API-Key.",
            retryable=False,
            run_id=run_id,
        )
    fingerprint = hashlib.sha256(
        f"decision-research-agent-review:{secret}".encode()
    ).hexdigest()
    return fingerprint, None


def _conflict_response(code: str, *, run_id: str) -> JSONResponse:
    if code == "review_already_decided":
        return _error(
            409,
            code=code,
            problem="This review revision already has an accepted decision.",
            cause="A conflicting decision was submitted.",
            fix="Fetch the run and use the persisted decision result.",
            retryable=False,
            run_id=run_id,
        )
    if code == "decision_id_conflict":
        return _error(
            409,
            code=code,
            problem="This decision ID is already bound to another request.",
            cause="The decision ID was reused with different content.",
            fix="Use the original request or submit a new decision ID.",
            retryable=False,
            run_id=run_id,
        )
    if code == "stale_state_version":
        return _error(
            409,
            code=code,
            problem="The run changed before this decision was accepted.",
            cause="expected_state_version is stale.",
            fix="Fetch the run and retry against its current state version.",
            retryable=True,
            run_id=run_id,
        )
    if code == "review_not_found":
        return _error(
            404,
            code=code,
            problem="The requested review workflow was not found.",
            cause="The run, review, or revision does not match.",
            fix="Fetch the run and use its current review identity.",
            retryable=False,
            run_id=run_id,
        )
    if code == "review_not_waiting":
        return _error(
            409,
            code=code,
            problem="The review is not accepting a decision.",
            cause="The workflow is not in waiting_decision state.",
            fix="Fetch the run and inspect the current review status.",
            retryable=False,
            run_id=run_id,
        )
    if code == "unsupported_review_profile":
        return _error(
            409,
            code=code,
            problem="This run profile does not support durable review.",
            cause="P1B is limited to the Talent Hiring Signal profile.",
            fix="Use the existing delivery path for this profile.",
            retryable=False,
            run_id=run_id,
        )
    return _error(
        409,
        code=code,
        problem="The review decision could not be accepted.",
        cause="The durable review ledger rejected the transition.",
        fix="Fetch the run and inspect its current review status.",
        retryable=False,
        run_id=run_id,
    )


@router.post(
    "/api/runs/{run_id}/reviews/{review_id}/decisions",
    status_code=202,
    include_in_schema=True,
    deprecated=True,
)
async def submit_review_decision(
    run_id: str,
    review_id: str,
    request: Request,
    body: Any = Body(...),
):
    actor, error = _authenticate(request, run_id=run_id)
    if error is not None:
        return error
    try:
        validated = ReviewDecisionRequest.model_validate(body)
    except ValidationError:
        return _error(
            422,
            code="invalid_review_decision",
            problem="The review decision request is invalid.",
            cause="The request body failed the bounded decision contract.",
            fix="Provide a valid decision ID, revision, action, and state version.",
            retryable=False,
            run_id=run_id,
        )
    try:
        result = await asyncio.to_thread(
            accept_review_decision,
            run_id=run_id,
            review_id=review_id,
            request=validated,
            actor_fingerprint=actor,
        )
    except ReviewConflict as exc:
        return _conflict_response(exc.code, run_id=run_id)
    return {
        "status": result.workflow_status,
        "run_id": run_id,
        "review_id": review_id,
        "decision_id": result.decision.decision_id,
        "idempotent_replay": result.idempotent_replay,
    }
