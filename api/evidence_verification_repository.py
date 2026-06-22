from __future__ import annotations

import json
import sqlite3

from api.review_repository import init_review_schema
from api.run_repository import _connect, _now


VERIFICATION_MIGRATION_VERSION = "005_evidence_verification_authority"
VERIFICATION_MIGRATION_CHECKSUM = "evidence-verification-authority-v1"


def _is_aggregate_only_scope(scope_json: str) -> bool:
    try:
        scope = json.loads(scope_json)
    except (TypeError, ValueError):
        return False
    allowed = scope.get("allowed_source_types")
    samples = scope.get("declared_samples", [])
    return (
        allowed == ["provided_aggregate"]
        and bool(samples)
        and all(
            isinstance(sample, dict)
            and sample.get("source_type") == "provided_aggregate"
            and isinstance(sample.get("reference"), str)
            and bool(sample["reference"])
            for sample in samples
        )
    )


def _backfill_declared_fixture_origin(
    connection: sqlite3.Connection,
) -> None:
    runs = connection.execute(
        """
        SELECT run_id, scope_json
        FROM research_runs_v2
        WHERE profile_id = 'talent-hiring-signal'
        """
    ).fetchall()
    fixture_run_ids = [
        row["run_id"]
        for row in runs
        if _is_aggregate_only_scope(row["scope_json"])
    ]
    connection.executemany(
        """
        UPDATE evidence_entries_v2
        SET baseline_verification_origin = 'declared_fixture'
        WHERE run_id = ?
          AND verification_status = 'verified'
          AND baseline_verification_origin = 'none'
        """,
        [(run_id,) for run_id in fixture_run_ids],
    )


def init_evidence_verification_schema(
    db_path: str | None = None,
) -> None:
    init_review_schema(db_path)
    connection = _connect(db_path)
    try:
        with connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS
                evidence_verification_preflights_v2 (
                    preflight_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL
                        REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    evidence_id TEXT NOT NULL
                        REFERENCES evidence_entries_v2(evidence_id)
                        ON DELETE CASCADE,
                    evidence_fingerprint TEXT NOT NULL,
                    preflight_version TEXT NOT NULL,
                    status TEXT NOT NULL
                        CHECK(status IN ('eligible', 'blocked')),
                    checks_json TEXT NOT NULL,
                    preflight_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(
                        run_id,
                        evidence_id,
                        evidence_fingerprint,
                        preflight_version,
                        preflight_hash
                    )
                );

                CREATE TABLE IF NOT EXISTS
                evidence_verification_decisions_v2 (
                    verification_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL
                        REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    evidence_id TEXT NOT NULL
                        REFERENCES evidence_entries_v2(evidence_id)
                        ON DELETE CASCADE,
                    evidence_fingerprint TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision >= 1),
                    action TEXT NOT NULL
                        CHECK(action IN ('verify', 'reject')),
                    reason_code TEXT,
                    reason_note TEXT,
                    preflight_id TEXT NOT NULL
                        REFERENCES evidence_verification_preflights_v2(
                            preflight_id
                        ),
                    actor_fingerprint TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(
                        run_id,
                        evidence_id,
                        evidence_fingerprint,
                        revision
                    )
                );

                CREATE TABLE IF NOT EXISTS
                evidence_verification_snapshots_v2 (
                    snapshot_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL
                        REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    revision INTEGER NOT NULL CHECK(revision >= 1),
                    snapshot_json TEXT NOT NULL,
                    snapshot_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(run_id, revision),
                    UNIQUE(run_id, snapshot_hash)
                );

                CREATE INDEX IF NOT EXISTS
                idx_evidence_preflights_evidence
                ON evidence_verification_preflights_v2(
                    run_id,
                    evidence_id,
                    created_at
                );

                CREATE INDEX IF NOT EXISTS
                idx_evidence_decisions_current
                ON evidence_verification_decisions_v2(
                    run_id,
                    evidence_id,
                    evidence_fingerprint,
                    revision DESC
                );
                """
            )
            _backfill_declared_fixture_origin(connection)
            connection.execute(
                """
                INSERT OR IGNORE INTO schema_migrations(
                    version,
                    applied_at,
                    checksum
                ) VALUES (?, ?, ?)
                """,
                (
                    VERIFICATION_MIGRATION_VERSION,
                    _now(),
                    VERIFICATION_MIGRATION_CHECKSUM,
                ),
            )
    finally:
        connection.close()
