from __future__ import annotations

from api.run_repository import _connect, _now, init_run_schema


REVIEW_MIGRATION_VERSION = "004_durable_review_feasibility"
REVIEW_MIGRATION_CHECKSUM = "durable-review-feasibility-v1"


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
