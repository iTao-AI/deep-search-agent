from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from typing import Any

from api.review_artifacts import ReviewedArtifactResult
from api.review_models import (
    ReviewDecisionRecord,
    ReviewDecisionRequest,
    decision_request_hash,
    review_resolution_id,
)
from api.run_repository import _connect, _now, init_run_schema


REVIEW_MIGRATION_VERSION = "004_durable_review_feasibility"
REVIEW_MIGRATION_CHECKSUM = "durable-review-feasibility-v1"


@dataclass(frozen=True)
class DecisionAcceptance:
    decision: ReviewDecisionRecord
    workflow_status: str
    idempotent_replay: bool


@dataclass(frozen=True)
class ReviewResolution:
    resolution_id: str
    run_id: str
    review_id: str
    decision_id: str
    action: str
    artifact_ids: tuple[str, ...]
    created_at: str


class ReviewConflict(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def init_review_schema(db_path: str | None = None) -> None:
    """Apply the additive durable review schema idempotently."""
    init_run_schema(db_path)
    connection = _connect(db_path)
    try:
        with connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS review_decisions_v2 (
                    decision_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL
                        REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    review_id TEXT NOT NULL
                        REFERENCES review_bundles_v2(review_id) ON DELETE CASCADE,
                    review_revision INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('approve', 'reject')),
                    reason TEXT,
                    actor_fingerprint TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    accepted_state_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(review_id, review_revision)
                );

                CREATE TABLE IF NOT EXISTS review_workflows_v2 (
                    workflow_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL UNIQUE
                        REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    review_id TEXT NOT NULL
                        REFERENCES review_bundles_v2(review_id) ON DELETE CASCADE,
                    review_revision INTEGER NOT NULL,
                    checkpoint_thread_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    decision_id TEXT
                        REFERENCES review_decisions_v2(decision_id),
                    post_review_segment_id TEXT NOT NULL,
                    lease_owner TEXT,
                    lease_expires_at TEXT,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    last_error_code TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS review_resume_attempts_v2 (
                    workflow_id TEXT NOT NULL
                        REFERENCES review_workflows_v2(workflow_id)
                        ON DELETE CASCADE,
                    attempt INTEGER NOT NULL,
                    worker_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    outcome TEXT,
                    error_code TEXT,
                    PRIMARY KEY(workflow_id, attempt)
                );

                CREATE TABLE IF NOT EXISTS review_resolutions_v2 (
                    resolution_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL UNIQUE
                        REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    review_id TEXT NOT NULL
                        REFERENCES review_bundles_v2(review_id) ON DELETE CASCADE,
                    decision_id TEXT NOT NULL UNIQUE
                        REFERENCES review_decisions_v2(decision_id),
                    action TEXT NOT NULL CHECK(action IN ('approve', 'reject')),
                    resolved_review_json TEXT NOT NULL,
                    artifact_ids_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_review_workflows_status_lease
                ON review_workflows_v2(status, lease_expires_at, updated_at);

                CREATE INDEX IF NOT EXISTS idx_review_decisions_run
                ON review_decisions_v2(run_id, created_at);
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO schema_migrations(version, applied_at, checksum)
                VALUES (?, ?, ?)
                """,
                (
                    REVIEW_MIGRATION_VERSION,
                    _now(),
                    REVIEW_MIGRATION_CHECKSUM,
                ),
            )
    finally:
        connection.close()


def _decision_record(row: sqlite3.Row) -> ReviewDecisionRecord:
    return ReviewDecisionRecord.model_validate(dict(row))


def _decision_acceptance(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    idempotent_replay: bool,
) -> DecisionAcceptance:
    workflow = connection.execute(
        """
        SELECT status FROM review_workflows_v2
        WHERE run_id = ? AND review_id = ? AND review_revision = ?
        """,
        (row["run_id"], row["review_id"], row["review_revision"]),
    ).fetchone()
    if workflow is None:
        raise ReviewConflict("review_not_found")
    return DecisionAcceptance(
        decision=_decision_record(row),
        workflow_status=workflow["status"],
        idempotent_replay=idempotent_replay,
    )


def accept_review_decision(
    *,
    run_id: str,
    review_id: str,
    request: ReviewDecisionRequest,
    actor_fingerprint: str,
    db_path: str | None = None,
) -> DecisionAcceptance:
    """Atomically accept one immutable review decision with fenced idempotency."""
    init_review_schema(db_path)
    request_hash = decision_request_hash(
        run_id=run_id,
        review_id=review_id,
        request=request,
    )
    connection = _connect(db_path)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM review_decisions_v2 WHERE decision_id = ?",
                (request.decision_id,),
            ).fetchone()
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise ReviewConflict("decision_id_conflict")
                return _decision_acceptance(
                    connection,
                    existing,
                    idempotent_replay=True,
                )

            prior_review_decision = connection.execute(
                """
                SELECT decision_id FROM review_decisions_v2
                WHERE review_id = ? AND review_revision = ?
                """,
                (review_id, request.review_revision),
            ).fetchone()
            if prior_review_decision is not None:
                raise ReviewConflict("review_already_decided")

            run = connection.execute(
                """
                SELECT execution_status, review_status, delivery_status,
                       state_version, profile_id
                FROM research_runs_v2 WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
            workflow = connection.execute(
                """
                SELECT * FROM review_workflows_v2
                WHERE run_id = ? AND review_id = ? AND review_revision = ?
                """,
                (run_id, review_id, request.review_revision),
            ).fetchone()
            if run is None or workflow is None:
                raise ReviewConflict("review_not_found")
            if run["profile_id"] != "talent-hiring-signal":
                raise ReviewConflict("unsupported_review_profile")
            if (
                run["execution_status"] != "completed"
                or run["review_status"] != "required"
                or run["delivery_status"] != "review_required"
                or workflow["status"] != "waiting_decision"
            ):
                raise ReviewConflict("review_not_waiting")
            if run["state_version"] != request.expected_state_version:
                raise ReviewConflict("stale_state_version")

            accepted_version = run["state_version"] + 1
            now = _now()
            connection.execute(
                """
                INSERT INTO review_decisions_v2 (
                    decision_id, run_id, review_id, review_revision, action,
                    reason, actor_fingerprint, request_hash,
                    accepted_state_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.decision_id,
                    run_id,
                    review_id,
                    request.review_revision,
                    request.action,
                    request.reason,
                    actor_fingerprint,
                    request_hash,
                    accepted_version,
                    now,
                ),
            )
            workflow_cursor = connection.execute(
                """
                UPDATE review_workflows_v2
                SET decision_id = ?, status = 'resume_pending', updated_at = ?
                WHERE workflow_id = ? AND status = 'waiting_decision'
                """,
                (request.decision_id, now, workflow["workflow_id"]),
            )
            if workflow_cursor.rowcount != 1:
                raise ReviewConflict("review_not_waiting")
            run_cursor = connection.execute(
                """
                UPDATE research_runs_v2
                SET state_version = state_version + 1, updated_at = ?
                WHERE run_id = ? AND state_version = ?
                """,
                (now, run_id, request.expected_state_version),
            )
            if run_cursor.rowcount != 1:
                raise ReviewConflict("stale_state_version")
            row = connection.execute(
                "SELECT * FROM review_decisions_v2 WHERE decision_id = ?",
                (request.decision_id,),
            ).fetchone()
            return _decision_acceptance(
                connection,
                row,
                idempotent_replay=False,
            )
    except sqlite3.IntegrityError as exc:
        message = str(exc)
        if (
            "review_decisions_v2.review_id, "
            "review_decisions_v2.review_revision"
        ) in message:
            raise ReviewConflict("review_already_decided") from exc
        if "review_decisions_v2.decision_id" in message:
            raise ReviewConflict("decision_id_conflict") from exc
        raise ReviewConflict("review_persistence_conflict") from exc
    finally:
        connection.close()


def _workflow_projection(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "workflow_id": row["workflow_id"],
        "run_id": row["run_id"],
        "review_id": row["review_id"],
        "review_revision": row["review_revision"],
        "status": row["status"],
        "decision_id": row["decision_id"],
        "post_review_segment_id": row["post_review_segment_id"],
        "attempt_count": row["attempt_count"],
        "last_error_code": row["last_error_code"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _decision_projection(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "decision_id": row["decision_id"],
        "run_id": row["run_id"],
        "review_id": row["review_id"],
        "review_revision": row["review_revision"],
        "action": row["action"],
        "reason_recorded": row["reason"] is not None,
        "accepted_state_version": row["accepted_state_version"],
        "created_at": row["created_at"],
    }


def _resolution_projection(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "resolution_id": row["resolution_id"],
        "run_id": row["run_id"],
        "review_id": row["review_id"],
        "decision_id": row["decision_id"],
        "action": row["action"],
        "artifact_ids": json.loads(row["artifact_ids_json"]),
        "created_at": row["created_at"],
    }


def get_review_projection(
    *,
    run_id: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Return bounded review state without audit-only or checkpoint internals."""
    init_review_schema(db_path)
    connection = _connect(db_path)
    try:
        workflow = connection.execute(
            "SELECT * FROM review_workflows_v2 WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        decision = connection.execute(
            """
            SELECT * FROM review_decisions_v2
            WHERE run_id = ? ORDER BY created_at DESC LIMIT 1
            """,
            (run_id,),
        ).fetchone()
        resolution = connection.execute(
            "SELECT * FROM review_resolutions_v2 WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        return {
            "workflow": _workflow_projection(workflow),
            "decision": _decision_projection(decision),
            "resolution": _resolution_projection(resolution),
        }
    finally:
        connection.close()


def _resolution_record(row: sqlite3.Row) -> ReviewResolution:
    return ReviewResolution(
        resolution_id=row["resolution_id"],
        run_id=row["run_id"],
        review_id=row["review_id"],
        decision_id=row["decision_id"],
        action=row["action"],
        artifact_ids=tuple(json.loads(row["artifact_ids_json"])),
        created_at=row["created_at"],
    )


def _lease_is_active(value: str | None) -> bool:
    if value is None:
        return False
    try:
        expires_at = datetime.fromisoformat(value)
    except ValueError:
        return False
    if expires_at.tzinfo is None:
        return False
    return expires_at > datetime.now(timezone.utc)


def resolve_review(
    *,
    workflow_id: str,
    worker_id: str,
    expected_run_state_version: int,
    result: ReviewedArtifactResult,
    db_path: str | None = None,
) -> ReviewResolution:
    """Persist one reviewed outcome exactly once under an active worker lease."""
    init_review_schema(db_path)
    connection = _connect(db_path)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            workflow = connection.execute(
                "SELECT * FROM review_workflows_v2 WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()
            if workflow is None:
                raise ReviewConflict("review_not_found")

            existing = connection.execute(
                "SELECT * FROM review_resolutions_v2 WHERE run_id = ?",
                (workflow["run_id"],),
            ).fetchone()
            if existing is not None:
                return _resolution_record(existing)

            if (
                workflow["status"] != "resuming"
                or workflow["lease_owner"] != worker_id
                or not _lease_is_active(workflow["lease_expires_at"])
            ):
                raise ReviewConflict("lease_not_owned")
            if workflow["decision_id"] is None:
                raise ReviewConflict("review_decision_missing")

            decision = connection.execute(
                "SELECT * FROM review_decisions_v2 WHERE decision_id = ?",
                (workflow["decision_id"],),
            ).fetchone()
            run = connection.execute(
                "SELECT state_version FROM research_runs_v2 WHERE run_id = ?",
                (workflow["run_id"],),
            ).fetchone()
            if decision is None or run is None:
                raise ReviewConflict("review_not_found")
            if (
                decision["accepted_state_version"]
                != expected_run_state_version
                or run["state_version"] != expected_run_state_version
            ):
                raise ReviewConflict("stale_state_version")

            result_decision = result.resolved_review.get("decision", {})
            if (
                result_decision.get("decision_id") != decision["decision_id"]
                or result_decision.get("action") != decision["action"]
            ):
                raise ReviewConflict("resolution_result_mismatch")
            if decision["action"] == "reject" and result.artifacts:
                raise ReviewConflict("resolution_result_mismatch")

            now = _now()
            artifact_ids = tuple(
                sorted(artifact["artifact_id"] for artifact in result.artifacts)
            )
            resolution = ReviewResolution(
                resolution_id=review_resolution_id(decision["decision_id"]),
                run_id=workflow["run_id"],
                review_id=workflow["review_id"],
                decision_id=decision["decision_id"],
                action=decision["action"],
                artifact_ids=artifact_ids,
                created_at=now,
            )
            connection.executemany(
                """
                INSERT INTO run_artifacts_v2 (
                    artifact_id, run_id, kind, media_type, content,
                    content_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        artifact["artifact_id"],
                        workflow["run_id"],
                        artifact["kind"],
                        artifact["media_type"],
                        artifact["content"],
                        artifact["content_hash"],
                        now,
                    )
                    for artifact in result.artifacts
                ],
            )
            connection.execute(
                """
                INSERT INTO review_resolutions_v2 (
                    resolution_id, run_id, review_id, decision_id, action,
                    resolved_review_json, artifact_ids_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resolution.resolution_id,
                    resolution.run_id,
                    resolution.review_id,
                    resolution.decision_id,
                    resolution.action,
                    json.dumps(
                        result.resolved_review,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    json.dumps(artifact_ids, separators=(",", ":")),
                    now,
                ),
            )
            delivery_status = (
                "ready" if decision["action"] == "approve" else "blocked"
            )
            run_cursor = connection.execute(
                """
                UPDATE research_runs_v2
                SET review_status = 'resolved',
                    delivery_status = ?,
                    state_version = state_version + 1,
                    updated_at = ?
                WHERE run_id = ? AND state_version = ?
                """,
                (
                    delivery_status,
                    now,
                    workflow["run_id"],
                    expected_run_state_version,
                ),
            )
            if run_cursor.rowcount != 1:
                raise ReviewConflict("stale_state_version")
            terminal_status = (
                "approved" if decision["action"] == "approve" else "rejected"
            )
            workflow_cursor = connection.execute(
                """
                UPDATE review_workflows_v2
                SET status = ?, lease_owner = NULL, lease_expires_at = NULL,
                    updated_at = ?
                WHERE workflow_id = ? AND status = 'resuming'
                  AND lease_owner = ?
                """,
                (terminal_status, now, workflow_id, worker_id),
            )
            if workflow_cursor.rowcount != 1:
                raise ReviewConflict("lease_not_owned")
            attempt_cursor = connection.execute(
                """
                UPDATE review_resume_attempts_v2
                SET completed_at = ?, outcome = ?, error_code = NULL
                WHERE workflow_id = ? AND attempt = ? AND worker_id = ?
                  AND completed_at IS NULL
                """,
                (
                    now,
                    terminal_status,
                    workflow_id,
                    workflow["attempt_count"],
                    worker_id,
                ),
            )
            if attempt_cursor.rowcount != 1:
                raise ReviewConflict("resume_attempt_not_found")
            return resolution
    except sqlite3.IntegrityError as exc:
        raise ReviewConflict("review_resolution_conflict") from exc
    finally:
        connection.close()
