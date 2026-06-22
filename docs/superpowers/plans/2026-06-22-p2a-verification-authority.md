# P2A Verification Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to implement this plan task-by-task. Coding
> subagents are disabled by repository policy. Steps use checkbox (`- [ ]`)
> syntax for tracking.

**Goal:** Add an append-only, human-authoritative Evidence Verification Ledger
with deterministic local preflight, immutable baseline origin, effective
verification projection, and deterministic snapshot persistence without
changing current API, review, artifact, or delivery behavior.

**Architecture:** Keep `evidence_entries_v2` immutable and add only an immutable
`baseline_verification_origin` classification. Persist deterministic preflight
records, immutable human decision revisions, and immutable effective-state
snapshots in three additive tables. Internal repository functions may append
decisions and finalize snapshots, but PR1 exposes no API/CLI and performs no
artifact rebuild or publication transition.

**Tech Stack:** Python 3.11+, Pydantic v2, SQLite WAL with `BEGIN IMMEDIATE`,
FastAPI application persistence conventions, pytest.

---

## Delivery Boundary

This plan implements **P2A PR1 only**.

Included:

- immutable Evidence baseline origin;
- additive, idempotent, backup-verifiable migration;
- deterministic no-network preflight;
- append-only internal human decision ledger;
- effective verification projection;
- deterministic immutable snapshot persistence;
- P1A fixture-origin and P1C compatibility tests;
- ADR and current data-model documentation.

Explicitly excluded:

- REST endpoints, auth middleware changes, OpenAPI, and Tool Client commands;
- `DECISION_RESEARCH_AGENT_ENABLE_EVIDENCE_VERIFICATION` runtime wiring;
- review-table revision migration;
- `run_publications_v2`;
- artifact rebuild, current-publication pointers, or stale publication logic;
- operator workflow and real-source proof;
- LangSmith changes;
- Skills, Async Subagents, LLM reviewer, frontend, React, RBAC, Postgres, or
  multi-instance support.
- removal of `DEEP_SEARCH_AGENT_*`, the legacy Tool Client shim, the current
  health service ID, or updates to the personal website and other public UI.

PR2 owns controlled API/CLI, runtime enablement, revisioned publication, and
fresh review workflow. PR3 owns the bounded real-source proof.

Naming follows a gradual fade:

- PR1 introduces no new legacy identifiers and does not modify existing
  compatibility behavior.
- PR2 uses canonical names for every new environment variable, command,
  example, and contract; it does not expand legacy aliases to cover P2A.
- Active documentation touched for functional reasons should lead with the
  canonical identity and avoid repeating compatibility explanations.
- Do not create a dedicated PR, checklist item, feature headline, benchmark, or
  interview claim for the naming cleanup.
- Runtime alias, shim, and health-ID removal waits for the later
  UI/personal-portfolio maintenance batch and a fresh first-party consumer
  scan.
- Historical specs, plans, changelog entries, old LangSmith project names, and
  stable historical links remain unchanged.

## Guiding Constraints

1. `evidence_entries_v2` remains the immutable collection ledger.
2. `baseline_verification_origin` accepts only `none` or `declared_fixture`.
   Human authority is derived from immutable decision rows, never written back
   to Evidence.
3. Existing declared Talent fixtures remain compatible with the P1A benchmark
   but are never described as human-verified.
4. `verification_status=verified` alone must not infer fixture or human origin.
   Historical backfill is allowed only for aggregate-only Talent scopes; mixed
   source scopes remain `none` because per-row aggregate provenance was not
   persisted.
5. Preflight performs no DNS, HTTP, browser, filesystem source lookup, or LLM
   call.
6. The exact `(run_id, evidence_id, evidence_fingerprint)` tuple fences every
   decision.
7. A repeated decision ID with the same canonical request is idempotent; the
   same ID with different content conflicts.
8. Corrections append revision `N + 1`; prior decisions are never updated.
9. Snapshot identity excludes timestamps and is byte-stable for the same
   effective state.
10. Current run, artifact, P1A, P1C, and durable-review projections remain
    unchanged in PR1.

## File Map

### Create

- `api/evidence_verification_models.py`
  - frozen Pydantic contracts, stable enums, request validation, and canonical
    hashes/identities.
- `api/evidence_verification_service.py`
  - pure deterministic preflight and source-boundary evaluation.
- `api/evidence_verification_repository.py`
  - additive schema, legacy origin backfill, immutable append operations,
    effective projections, and snapshot persistence.
- `tests/unit/test_evidence_verification_models.py`
  - request and canonical identity contracts.
- `tests/unit/test_evidence_verification_service.py`
  - deterministic preflight and no-network boundary.
- `tests/unit/test_evidence_verification_repository.py`
  - append-only decisions, idempotency, fencing, corrections, projections, and
    snapshots.
- `tests/unit/test_evidence_verification_migrations.py`
  - idempotency, schema verification, legacy backfill, and backup/restore.
- `tests/integration/test_evidence_verification_compatibility.py`
  - existing Talent fixture and durable review compatibility.
- `docs/decisions/evidence-verification-authority.md`
  - long-lived authority and immutability decision.

### Modify

- `agent/research.py`
  - expose canonical fingerprint helpers and add immutable
    `baseline_verification_origin`.
- `agent/main_agent.py`
  - mark only controlled aggregate preload Evidence as `declared_fixture`.
- `api/run_repository.py`
  - persist the baseline origin while keeping current public run projection
    unchanged.
- `api/run_migrations.py`
  - optionally verify the PR1 schema and run the full additive migration through
    existing backup/restore.
- `tests/integration/test_evidence_lifecycle.py`
  - assert fixture origin without weakening existing `verified` compatibility.
- `spec/data-models.md`
  - document Verification Ledger authority and PR1 tables.
- `docs/README.md`
  - retain the planning-phase plan link and add the ADR.
- `docs/superpowers/specs/2026-06-21-p2a-evidence-verification-design.md`
  - retain the real-schema clarifications already made before this plan.

### Do Not Modify

- `api/review_api.py`
- `api/review_models.py`
- `api/review_worker.py`
- `api/review_artifacts.py`
- `tools/decision_research_agent_tool.py`
- `spec/api-contract.md`
- `frontend/`
- `docs/evidence/durable-hitl-gate-report.json`

The legacy identifier files may be read for compatibility verification but
must not be edited in PR1.

## Public And Internal Contracts

PR1 adds no public HTTP or CLI contract. The internal contracts below become
the implementation boundary consumed by PR2.

```python
def evaluate_evidence_preflight(
    *,
    run: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> EvidencePreflightResult: ...


def accept_verification_decision(
    *,
    db_path: str,
    run_id: str,
    evidence_id: str,
    request: VerificationDecisionRequest,
    actor_fingerprint: str,
) -> VerificationDecisionAcceptance: ...


def get_or_create_evidence_preflight(
    *,
    db_path: str,
    run_id: str,
    evidence_id: str,
) -> EvidencePreflightResult: ...


def get_effective_verification(
    *,
    db_path: str,
    run_id: str,
    evidence_id: str,
) -> EffectiveEvidenceVerification | None: ...


def list_effective_verifications(
    *,
    db_path: str,
    run_id: str,
) -> list[EffectiveEvidenceVerification]: ...


def finalize_verification_snapshot(
    *,
    db_path: str,
    run_id: str,
) -> VerificationSnapshotAcceptance: ...
```

Repository conflicts use stable internal codes:

```text
evidence_not_found
evidence_fingerprint_mismatch
evidence_preflight_blocked
verification_revision_conflict
verification_id_conflict
verification_persistence_conflict
```

Reject reason validation is owned by `VerificationDecisionRequest`. PR2 maps
that validation failure to the public `verification_reason_required` envelope.

## Task 1: Freeze Verification Contracts And Canonical Identities

**Files:**

- Create: `api/evidence_verification_models.py`
- Modify: `agent/research.py`
- Create: `tests/unit/test_evidence_verification_models.py`
- Test: `tests/unit/test_research_run.py`

- [ ] **Step 1: Write failing model and fingerprint tests**

Create `tests/unit/test_evidence_verification_models.py`:

```python
from pydantic import ValidationError
import pytest

from agent.research import (
    EvidenceEntry,
    evidence_fingerprint_for,
    source_identity_for,
)
from api.evidence_verification_models import (
    VerificationDecisionRequest,
    canonical_hash,
    preflight_id_for,
    verification_request_hash,
)


def test_verify_requires_explicit_bounded_confirmation():
    with pytest.raises(ValidationError, match="confirm_source_match"):
        VerificationDecisionRequest(
            verification_id="verification-1",
            evidence_fingerprint="a" * 64,
            expected_revision=0,
            action="verify",
        )


def test_reject_requires_reason_and_rejects_verify_only_fields():
    with pytest.raises(ValidationError, match="reason_code"):
        VerificationDecisionRequest(
            verification_id="verification-1",
            evidence_fingerprint="a" * 64,
            expected_revision=0,
            action="reject",
        )

    with pytest.raises(ValidationError, match="reason_code"):
        VerificationDecisionRequest(
            verification_id="verification-1",
            evidence_fingerprint="a" * 64,
            expected_revision=0,
            action="verify",
            confirm_source_match=True,
            reason_code="content_mismatch",
        )


def test_rejection_note_is_bounded():
    with pytest.raises(ValidationError, match="reason_note"):
        VerificationDecisionRequest(
            verification_id="verification-1",
            evidence_fingerprint="a" * 64,
            expected_revision=0,
            action="reject",
            reason_code="other",
            reason_note="x" * 1001,
        )


def test_canonical_identities_ignore_mapping_order():
    first = {"run_id": "run-1", "checks": [{"code": "a", "passed": True}]}
    second = {"checks": [{"passed": True, "code": "a"}], "run_id": "run-1"}

    assert canonical_hash(first) == canonical_hash(second)
    assert preflight_id_for(first) == preflight_id_for(second)


def test_request_hash_binds_run_evidence_and_request():
    request = VerificationDecisionRequest(
        verification_id="verification-1",
        evidence_fingerprint="a" * 64,
        expected_revision=0,
        action="verify",
        confirm_source_match=True,
    )

    assert verification_request_hash(
        run_id="run-1",
        evidence_id="ev-1",
        request=request,
    ) != verification_request_hash(
        run_id="run-2",
        evidence_id="ev-1",
        request=request,
    )


def test_evidence_entry_has_immutable_baseline_origin_and_stable_fingerprint():
    entry = EvidenceEntry(
        thread_id="thread-1",
        query_text="query",
        subagent_name="network_search",
        tool_name="internet_search",
        source_url="https://example.com/source.",
        snippet="  stable   snippet ",
        baseline_verification_origin="declared_fixture",
    )

    assert entry.source_identity == source_identity_for(
        "https://example.com/source."
    )
    assert entry.evidence_fingerprint == evidence_fingerprint_for(
        entry.source_identity,
        entry.snippet,
    )
    assert entry.baseline_verification_origin == "declared_fixture"


def test_evidence_entry_rejects_unknown_baseline_origin():
    with pytest.raises(ValueError, match="baseline_verification_origin"):
        EvidenceEntry(
            thread_id="thread-1",
            query_text="query",
            subagent_name="network_search",
            tool_name="internet_search",
            source_url="https://example.com/source",
            snippet="snippet",
            baseline_verification_origin="human",
        )
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_models.py \
  tests/unit/test_research_run.py -q
```

Expected: collection fails because `api.evidence_verification_models`,
`source_identity_for`, `evidence_fingerprint_for`, and
`baseline_verification_origin` do not exist.

- [ ] **Step 3: Add frozen Pydantic contracts and canonical helpers**

Create `api/evidence_verification_models.py` with these contracts:

```python
from __future__ import annotations

from typing import Any, Literal
import hashlib
import json
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator


VerificationAction = Literal["verify", "reject"]
VerificationOrigin = Literal["none", "declared_fixture", "human"]
VerificationState = Literal["unverified", "verified", "rejected"]
PreflightStatus = Literal["eligible", "blocked"]
RejectReasonCode = Literal[
    "source_unavailable",
    "content_mismatch",
    "source_out_of_scope",
    "ambiguous_source",
    "insufficient_context",
    "other",
]

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")


class VerificationContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PreflightCheck(VerificationContract):
    code: str = Field(min_length=1, max_length=100)
    passed: bool
    explanation: str = Field(min_length=1, max_length=300)


class EvidencePreflightResult(VerificationContract):
    preflight_id: str
    run_id: str
    evidence_id: str
    evidence_fingerprint: str
    preflight_version: str
    status: PreflightStatus
    checks: tuple[PreflightCheck, ...]
    preflight_hash: str


class VerificationDecisionRequest(VerificationContract):
    verification_id: str
    evidence_fingerprint: str
    expected_revision: int = Field(ge=0)
    action: VerificationAction
    confirm_source_match: bool = False
    reason_code: RejectReasonCode | None = None
    reason_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_action_fields(self):
        if not _ID_RE.fullmatch(self.verification_id):
            raise ValueError("verification_id has an invalid format")
        if not _FINGERPRINT_RE.fullmatch(self.evidence_fingerprint):
            raise ValueError("evidence_fingerprint must be lowercase sha256")
        if self.action == "verify":
            if not self.confirm_source_match:
                raise ValueError("confirm_source_match is required for verify")
            if self.reason_code is not None or self.reason_note is not None:
                raise ValueError("reason_code and reason_note are reject-only")
        elif self.reason_code is None:
            raise ValueError("reason_code is required for reject")
        return self


class VerificationDecisionRecord(VerificationContract):
    verification_id: str
    run_id: str
    evidence_id: str
    evidence_fingerprint: str
    revision: int = Field(ge=1)
    action: VerificationAction
    reason_code: RejectReasonCode | None = None
    reason_note: str | None = None
    preflight_id: str
    created_at: str


class EffectiveEvidenceVerification(VerificationContract):
    run_id: str
    evidence_id: str
    evidence_fingerprint: str
    verification_status: Literal["verified", "unverified"]
    verification_state: VerificationState
    verification_origin: VerificationOrigin
    verification_revision: int = Field(ge=0)
    decision_id: str | None = None


class VerificationSnapshotRecord(VerificationContract):
    snapshot_id: str
    run_id: str
    revision: int = Field(ge=1)
    snapshot: tuple[EffectiveEvidenceVerification, ...]
    snapshot_hash: str
    created_at: str


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def preflight_id_for(payload: dict[str, Any]) -> str:
    return f"vpf_{canonical_hash(payload)}"


def snapshot_id_for(*, run_id: str, snapshot_hash: str) -> str:
    return f"vsnap_{canonical_hash({'run_id': run_id, 'hash': snapshot_hash})}"


def verification_request_hash(
    *,
    run_id: str,
    evidence_id: str,
    request: VerificationDecisionRequest,
) -> str:
    return canonical_hash(
        {
            "run_id": run_id,
            "evidence_id": evidence_id,
            "request": request.model_dump(mode="json"),
        }
    )
```

In `agent/research.py`:

1. Rename the private canonical helpers to public functions:

```python
def source_identity_for(source_url: str | None) -> str:
    return _normalize_url(source_url.strip()) if source_url else "source:unknown"


def normalize_evidence_content(content: str) -> str:
    return " ".join(str(content).split())


def evidence_fingerprint_for(source_identity: str, content: str) -> str:
    payload = f"{source_identity}\n{normalize_evidence_content(content)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

2. Update `EvidenceEntry.__post_init__()` and `evidence_id_for()` to call those
   public helpers.
3. Add:

```python
baseline_verification_origin: str = "none"
```

4. Validate the frozen baseline value inside `__post_init__()`:

```python
if self.baseline_verification_origin not in {"none", "declared_fixture"}:
    raise ValueError("invalid baseline_verification_origin")
```

Do not accept `human` on an Evidence row.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_models.py \
  tests/unit/test_research_run.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit Task 1**

Stage only:

```bash
git add \
  agent/research.py \
  api/evidence_verification_models.py \
  tests/unit/test_evidence_verification_models.py
git commit -m "feat(research): define verification authority contracts"
```

## Task 2: Add The Recoverable Verification Schema

**Files:**

- Create: `api/evidence_verification_repository.py`
- Modify: `api/run_repository.py`
- Modify: `api/run_migrations.py`
- Create: `tests/unit/test_evidence_verification_migrations.py`
- Test: `tests/unit/test_run_migrations.py`
- Test: `tests/unit/test_review_migrations.py`

- [ ] **Step 1: Write failing migration and backfill tests**

Create `tests/unit/test_evidence_verification_migrations.py`:

```python
import json
import sqlite3

import pytest

from agent.research import EvidenceEntry
from api.evidence_verification_repository import (
    VERIFICATION_MIGRATION_VERSION,
    init_evidence_verification_schema,
)
from api.persistence import init_db
from api.run_migrations import (
    backup_database,
    restore_database,
    verify_run_schema,
)
from api.run_repository import create_run, finalize_run_transaction


VERIFICATION_TABLES = {
    "evidence_verification_preflights_v2",
    "evidence_verification_decisions_v2",
    "evidence_verification_snapshots_v2",
}


def _tables(path: str) -> set[str]:
    connection = sqlite3.connect(path)
    try:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        connection.close()


def test_verification_schema_is_idempotent_and_optionally_verified(tmp_path):
    path = str(tmp_path / "tasks.db")
    init_db(path).close()

    init_evidence_verification_schema(path)
    init_evidence_verification_schema(path)
    result = verify_run_schema(
        db_path=path,
        include_evidence_verification=True,
    )

    assert VERIFICATION_TABLES <= _tables(path)
    assert VERIFICATION_MIGRATION_VERSION in result["migration_versions"]
    connection = sqlite3.connect(path)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE version = ?",
            (VERIFICATION_MIGRATION_VERSION,),
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1


def test_verification_schema_backup_restore_removes_additive_state(tmp_path):
    path = str(tmp_path / "tasks.db")
    backup = str(tmp_path / "tasks.pre-verification.db")
    init_db(path).close()
    before = _tables(path)

    backup_database(db_path=path, backup_path=backup)
    init_evidence_verification_schema(path)
    assert VERIFICATION_TABLES <= _tables(path)

    restore_database(backup_path=backup, db_path=path)
    assert _tables(path) == before


def test_legacy_fixture_backfill_requires_aggregate_only_talent_scope_and_verified_status(
    tmp_path,
):
    path = str(tmp_path / "tasks.db")
    talent = create_run(
        db_path=path,
        thread_id="thread-talent",
        query="query",
        profile_id="talent-hiring-signal",
        scope={
            "target_roles": ["AI Agent Engineer"],
            "target_companies": [],
            "time_window": {"start": "2026-01-01", "end": "2026-06-12"},
            "declared_samples": [
                {
                    "sample_id": "aggregate-v1",
                    "source_type": "provided_aggregate",
                    "reference": "aggregate-v1",
                }
            ],
            "allowed_source_types": ["provided_aggregate"],
            "research_questions": ["question-1"],
            "requested_outputs": ["decision_brief"],
        },
    )
    ordinary = create_run(
        db_path=path,
        thread_id="thread-generic",
        query="query",
        profile_id="generic",
    )
    talent_entry = EvidenceEntry(
        thread_id="thread-talent",
        query_text="query",
        subagent_name="network_search",
        tool_name="internet_search",
        source_url="https://example.com/talent",
        snippet="talent",
        verification_status="verified",
    )
    ordinary_entry = EvidenceEntry(
        thread_id="thread-generic",
        query_text="query",
        subagent_name="network_search",
        tool_name="internet_search",
        source_url="https://example.com/generic",
        snippet="generic",
        verification_status="verified",
    )
    for created, entry in (
        (talent, talent_entry),
        (ordinary, ordinary_entry),
    ):
        assert finalize_run_transaction(
            db_path=path,
            run_id=created["run_id"],
            segment_id=created["segment_id"],
            expected_state_version=0,
            allowed_previous_statuses={"pending"},
            execution_status="completed",
            delivery_status="ready",
            evidence_entries=[entry],
        )

    init_evidence_verification_schema(path)

    connection = sqlite3.connect(path)
    try:
        rows = dict(
            connection.execute(
                """
                SELECT run_id, baseline_verification_origin
                FROM evidence_entries_v2
                """
            ).fetchall()
        )
    finally:
        connection.close()
    assert rows[talent["run_id"]] == "declared_fixture"
    assert rows[ordinary["run_id"]] == "none"


def test_mixed_source_talent_run_is_not_backfilled(tmp_path):
    path = str(tmp_path / "tasks.db")
    created = create_run(
        db_path=path,
        thread_id="thread-mixed",
        query="query",
        profile_id="talent-hiring-signal",
        scope={
            "target_roles": ["AI Agent Engineer"],
            "target_companies": [],
            "time_window": {"start": "2026-01-01", "end": "2026-06-12"},
            "declared_samples": [
                {
                    "sample_id": "aggregate-v1",
                    "source_type": "provided_aggregate",
                    "reference": "aggregate-v1",
                },
                {
                    "sample_id": "job-1",
                    "source_type": "public_job_posting",
                    "reference": "https://jobs.example.com/role",
                },
            ],
            "allowed_source_types": [
                "provided_aggregate",
                "public_job_posting",
            ],
            "research_questions": ["question-1"],
            "requested_outputs": ["decision_brief"],
        },
    )
    entry = EvidenceEntry(
        thread_id="thread-mixed",
        query_text="query",
        subagent_name="network_search",
        tool_name="internet_search",
        source_url="https://jobs.example.com/role",
        snippet="mixed source evidence",
        verification_status="verified",
    )
    assert finalize_run_transaction(
        db_path=path,
        run_id=created["run_id"],
        segment_id=created["segment_id"],
        expected_state_version=0,
        allowed_previous_statuses={"pending"},
        execution_status="completed",
        delivery_status="ready",
        evidence_entries=[entry],
    )

    init_evidence_verification_schema(path)

    connection = sqlite3.connect(path)
    try:
        origin = connection.execute(
            """
            SELECT baseline_verification_origin
            FROM evidence_entries_v2
            WHERE run_id = ?
            """,
            (created["run_id"],),
        ).fetchone()[0]
    finally:
        connection.close()
    assert origin == "none"


def test_legacy_unverified_talent_evidence_is_not_backfilled(tmp_path):
    path = str(tmp_path / "tasks.db")
    created = create_run(
        db_path=path,
        thread_id="thread-talent",
        query="query",
        profile_id="talent-hiring-signal",
        scope={
            "target_roles": ["AI Agent Engineer"],
            "target_companies": [],
            "time_window": {"start": "2026-01-01", "end": "2026-06-12"},
            "declared_samples": [
                {
                    "sample_id": "aggregate-v1",
                    "source_type": "provided_aggregate",
                    "reference": "aggregate-v1",
                }
            ],
            "allowed_source_types": ["provided_aggregate"],
            "research_questions": ["question-1"],
            "requested_outputs": ["decision_brief"],
        },
    )
    entry = EvidenceEntry(
        thread_id="thread-talent",
        query_text="query",
        subagent_name="network_search",
        tool_name="internet_search",
        source_url="https://example.com/source",
        snippet="source",
    )
    assert finalize_run_transaction(
        db_path=path,
        run_id=created["run_id"],
        segment_id=created["segment_id"],
        expected_state_version=0,
        allowed_previous_statuses={"pending"},
        execution_status="completed",
        delivery_status="ready",
        evidence_entries=[entry],
    )

    init_evidence_verification_schema(path)

    connection = sqlite3.connect(path)
    try:
        origin = connection.execute(
            """
            SELECT baseline_verification_origin
            FROM evidence_entries_v2
            WHERE run_id = ?
            """,
            (created["run_id"],),
        ).fetchone()[0]
    finally:
        connection.close()
    assert origin == "none"


@pytest.mark.parametrize(
    ("table", "column"),
    [
        ("evidence_entries_v2", "baseline_verification_origin"),
        ("evidence_verification_preflights_v2", "checks_json"),
        ("evidence_verification_decisions_v2", "actor_fingerprint"),
        ("evidence_verification_snapshots_v2", "snapshot_json"),
    ],
)
def test_verification_schema_checks_required_columns(
    tmp_path,
    table,
    column,
):
    path = str(tmp_path / f"{table}.db")
    init_evidence_verification_schema(path)
    connection = sqlite3.connect(path)
    try:
        connection.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(
        RuntimeError,
        match=rf"run_schema_verification_failed:.*{table}.*{column}",
    ):
        verify_run_schema(
            db_path=path,
            include_evidence_verification=True,
        )
```

- [ ] **Step 2: Run migration tests and confirm RED**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_migrations.py \
  tests/unit/test_run_migrations.py \
  tests/unit/test_review_migrations.py -q
```

Expected: collection fails because the verification repository and optional
schema verifier do not exist.

- [ ] **Step 3: Persist baseline origin on fresh runs**

In `api/run_repository.py`:

1. Add this column to the fresh `evidence_entries_v2` definition after
   `verification_status`:

```sql
baseline_verification_origin TEXT NOT NULL DEFAULT 'none'
    CHECK(baseline_verification_origin IN ('none', 'declared_fixture')),
```

2. Add an idempotent compatibility helper beside `init_run_schema()`:

```python
def _ensure_baseline_origin_column(
    connection: sqlite3.Connection,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(evidence_entries_v2)"
        ).fetchall()
    }
    if "baseline_verification_origin" not in columns:
        connection.execute(
            """
            ALTER TABLE evidence_entries_v2
            ADD COLUMN baseline_verification_origin TEXT NOT NULL DEFAULT 'none'
            CHECK(
                baseline_verification_origin
                IN ('none', 'declared_fixture')
            )
            """
        )
```

Call it inside the existing `with conn:` block in `init_run_schema()` after
`evidence_entries_v2` exists and before recording the run migration. This keeps
ordinary finalization compatible with databases created before PR1, even when
the P2A feature is not enabled.

3. Add the column to `finalize_run_transaction()` insert columns and values:

```python
entry.baseline_verification_origin,
```

4. Keep current run API shape unchanged. Replace the raw evidence conversion:

```python
result["evidence"] = [dict(entry) for entry in evidence]
```

with a compatibility helper:

```python
def _public_evidence_row(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    value.pop("baseline_verification_origin", None)
    return value
```

and:

```python
result["evidence"] = [_public_evidence_row(entry) for entry in evidence]
```

PR2 will expose effective origin through a deliberate API contract. PR1 must
not accidentally leak an internal migration field through `SELECT *`.

- [ ] **Step 4: Implement the additive schema and legacy backfill**

Create the schema portion of `api/evidence_verification_repository.py`:

```python
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
```

- [ ] **Step 5: Extend schema verification without breaking P1C**

In `api/run_migrations.py`:

1. Import the verification migration constants and initializer.
2. Define separate verification requirements:

```python
VERIFICATION_TABLES = {
    "evidence_verification_preflights_v2",
    "evidence_verification_decisions_v2",
    "evidence_verification_snapshots_v2",
}

VERIFICATION_INDEXES = {
    "idx_evidence_preflights_evidence",
    "idx_evidence_decisions_current",
}

VERIFICATION_COLUMNS = {
    "evidence_entries_v2": {"baseline_verification_origin"},
    "evidence_verification_preflights_v2": {
        "preflight_id",
        "run_id",
        "evidence_id",
        "evidence_fingerprint",
        "preflight_version",
        "status",
        "checks_json",
        "preflight_hash",
        "created_at",
    },
    "evidence_verification_decisions_v2": {
        "verification_id",
        "run_id",
        "evidence_id",
        "evidence_fingerprint",
        "revision",
        "action",
        "reason_code",
        "reason_note",
        "preflight_id",
        "actor_fingerprint",
        "request_hash",
        "created_at",
    },
    "evidence_verification_snapshots_v2": {
        "snapshot_id",
        "run_id",
        "revision",
        "snapshot_json",
        "snapshot_hash",
        "created_at",
    },
}
```

3. Change the signature:

```python
def verify_run_schema(
    *,
    db_path: str,
    include_evidence_verification: bool = False,
) -> dict:
```

Build local `required_tables`, `required_indexes`, `required_columns`, and
`expected_migrations` from the existing constants. Merge the verification
requirements only when `include_evidence_verification=True`.

4. Change `migrate_with_backup()` to:

```python
init_evidence_verification_schema(db_path)
return verify_run_schema(
    db_path=db_path,
    include_evidence_verification=True,
)
```

Do not change `check_review_readiness()` in PR1. Existing P1C startup continues
to call the default verifier and does not require P2A tables until PR2 enables
the new runtime.

- [ ] **Step 6: Update the existing restore regression for the new verifier argument**

In `tests/unit/test_run_migrations.py`, change the monkeypatched function in
`test_migration_verification_failure_restores_backup` to accept the optional
flag while preserving the intentional failure:

```python
def fail_verification(
    *,
    db_path,
    include_evidence_verification=False,
):
    raise RuntimeError("verification failed")
```

- [ ] **Step 7: Run migration tests and confirm GREEN**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_migrations.py \
  tests/unit/test_run_migrations.py \
  tests/unit/test_review_migrations.py \
  tests/unit/test_run_repository.py -q
```

Expected: all selected tests pass, including existing backup/restore and P1C
schema tests.

- [ ] **Step 8: Commit Task 2**

Stage only:

```bash
git add \
  api/evidence_verification_repository.py \
  api/run_repository.py \
  api/run_migrations.py \
  tests/unit/test_evidence_verification_migrations.py \
  tests/unit/test_run_migrations.py
git commit -m "feat(research): migrate verification authority ledger"
```

## Task 3: Implement Pure Deterministic Preflight

**Files:**

- Create: `api/evidence_verification_service.py`
- Create: `tests/unit/test_evidence_verification_service.py`
- Test: `tests/unit/test_talent_contracts.py`
- Test: `tests/unit/test_talent_search.py`

- [ ] **Step 1: Write failing preflight tests**

Create `tests/unit/test_evidence_verification_service.py`:

```python
import socket
import urllib.request

import pytest

from agent.research import evidence_fingerprint_for
from api.evidence_verification_service import evaluate_evidence_preflight


def _run(
    *,
    profile_id="talent-hiring-signal",
    declared_samples=None,
):
    return {
        "run_id": "run-1",
        "profile_id": profile_id,
        "scope": {
            "declared_samples": declared_samples
            if declared_samples is not None
            else [
                {
                    "sample_id": "sample-1",
                    "source_type": "public_job_posting",
                    "reference": "https://jobs.example.com/role",
                }
            ]
        },
    }


def _evidence(
    *,
    source_url="https://jobs.example.com/role",
    snippet="Evidence",
    fingerprint=None,
    baseline_origin="none",
):
    source_identity = source_url
    actual = evidence_fingerprint_for(source_identity, snippet)
    selected = actual if fingerprint is None else fingerprint
    return {
        "evidence_id": f"ev_run-1_{selected}",
        "run_id": "run-1",
        "source_url": source_url,
        "source_identity": source_identity,
        "snippet": snippet,
        "evidence_fingerprint": selected,
        "baseline_verification_origin": baseline_origin,
    }


def _failed_codes(result):
    return {check.code for check in result.checks if not check.passed}


def test_valid_declared_public_evidence_is_eligible_and_deterministic():
    first = evaluate_evidence_preflight(run=_run(), evidence=_evidence())
    second = evaluate_evidence_preflight(run=_run(), evidence=_evidence())

    assert first.status == "eligible"
    assert first == second
    assert [check.code for check in first.checks] == [
        "run_membership",
        "evidence_identity",
        "fingerprint_match",
        "url_scheme",
        "url_userinfo_absent",
        "url_hostname",
        "declared_source_boundary",
        "snippet_present",
        "snippet_within_bounds",
    ]


def test_fingerprint_mismatch_and_deterministic_id_mismatch_are_blocked():
    result = evaluate_evidence_preflight(
        run=_run(),
        evidence=_evidence(fingerprint="b" * 64),
    )

    assert result.status == "blocked"
    assert {"fingerprint_match"} <= _failed_codes(result)


@pytest.mark.parametrize(
    ("url", "expected_code"),
    [
        ("ftp://jobs.example.com/role", "url_scheme"),
        ("https://user:secret@jobs.example.com/role", "url_userinfo_absent"),
        ("https:///role", "url_hostname"),
        ("https://[invalid", "url_hostname"),
        ("https://other.example.com/role", "declared_source_boundary"),
    ],
)
def test_invalid_or_out_of_scope_urls_are_blocked(url, expected_code):
    result = evaluate_evidence_preflight(
        run=_run(),
        evidence=_evidence(source_url=url),
    )

    assert expected_code in _failed_codes(result)


def test_declared_fixture_origin_uses_declared_aggregate_boundary():
    result = evaluate_evidence_preflight(
        run=_run(
            declared_samples=[
                {
                    "sample_id": "aggregate-v1",
                    "source_type": "provided_aggregate",
                    "reference": "aggregate-v1",
                }
            ]
        ),
        evidence=_evidence(
            source_url="https://external.example.com/role",
            baseline_origin="declared_fixture",
        ),
    )

    assert result.status == "eligible"


def test_fixture_origin_without_declared_aggregate_is_blocked():
    result = evaluate_evidence_preflight(
        run=_run(declared_samples=[]),
        evidence=_evidence(baseline_origin="declared_fixture"),
    )

    assert "declared_source_boundary" in _failed_codes(result)


def test_generic_profile_has_no_declared_source_boundary():
    result = evaluate_evidence_preflight(
        run=_run(profile_id="generic", declared_samples=[]),
        evidence=_evidence(source_url="https://public.example.org/source"),
    )

    assert result.status == "eligible"


def test_preflight_performs_no_dns_or_http(monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)

    result = evaluate_evidence_preflight(run=_run(), evidence=_evidence())

    assert result.status == "eligible"
    assert calls == []


def test_empty_or_oversized_snippet_is_blocked():
    empty = evaluate_evidence_preflight(
        run=_run(),
        evidence=_evidence(snippet=""),
    )
    oversized = evaluate_evidence_preflight(
        run=_run(),
        evidence=_evidence(snippet="x" * 1001),
    )

    assert "snippet_present" in _failed_codes(empty)
    assert "snippet_within_bounds" in _failed_codes(oversized)
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_service.py -q
```

Expected: collection fails because
`api.evidence_verification_service.evaluate_evidence_preflight` does not exist.

- [ ] **Step 3: Implement stable check construction**

Create `api/evidence_verification_service.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse
import json
import re

from agent.research import (
    evidence_fingerprint_for,
    source_identity_for,
)
from api.evidence_verification_models import (
    EvidencePreflightResult,
    PreflightCheck,
    canonical_hash,
    preflight_id_for,
)


PREFLIGHT_VERSION = "1"
MAX_PERSISTED_SNIPPET_LENGTH = 1000
_HOST_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def _scope(run: Mapping[str, Any]) -> dict[str, Any]:
    value = run.get("scope")
    if isinstance(value, dict):
        return value
    raw = run.get("scope_json")
    if not isinstance(raw, str):
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _hostname_is_valid(hostname: str | None) -> bool:
    if not hostname:
        return False
    try:
        ascii_host = hostname.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return False
    if len(ascii_host) > 253:
        return False
    labels = ascii_host.rstrip(".").split(".")
    return bool(labels) and all(_HOST_LABEL_RE.fullmatch(label) for label in labels)


def _parsed_url(value: Any):
    try:
        parsed = urlparse(value if isinstance(value, str) else "")
        hostname = parsed.hostname
        username = parsed.username
        password = parsed.password
    except ValueError:
        parsed = urlparse("")
        hostname = None
        username = None
        password = None
    return parsed, hostname, username, password


def _declared_boundary_passes(
    *,
    run: Mapping[str, Any],
    evidence: Mapping[str, Any],
    hostname: str | None,
) -> bool:
    if run.get("profile_id") != "talent-hiring-signal":
        return True
    samples = _scope(run).get("declared_samples", [])
    samples = [item for item in samples if isinstance(item, dict)]
    if evidence.get("baseline_verification_origin") == "declared_fixture":
        return any(
            item.get("source_type") == "provided_aggregate"
            and isinstance(item.get("reference"), str)
            and bool(item["reference"])
            for item in samples
        )
    allowed_hosts = set()
    for item in samples:
        if item.get("source_type") != "public_job_posting":
            continue
        _, declared_host, _, _ = _parsed_url(item.get("reference"))
        if declared_host:
            allowed_hosts.add(declared_host.lower())
    return bool(hostname) and hostname.lower() in allowed_hosts


def _check(code: str, passed: bool, explanation: str) -> PreflightCheck:
    return PreflightCheck(
        code=code,
        passed=passed,
        explanation=explanation,
    )


def evaluate_evidence_preflight(
    *,
    run: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> EvidencePreflightResult:
    run_id = str(run.get("run_id") or "")
    evidence_id = str(evidence.get("evidence_id") or "")
    fingerprint = str(evidence.get("evidence_fingerprint") or "")
    source_url = evidence.get("source_url")
    parsed, hostname, username, password = _parsed_url(source_url)
    source_identity = str(evidence.get("source_identity") or "")
    snippet = str(evidence.get("snippet") or "")
    recomputed = evidence_fingerprint_for(
        source_identity_for(source_url),
        snippet,
    )
    expected_id = f"ev_{run_id}_{fingerprint}"
    checks = (
        _check(
            "run_membership",
            evidence.get("run_id") == run_id and bool(run_id),
            "Evidence belongs to the requested run.",
        ),
        _check(
            "evidence_identity",
            evidence_id == expected_id,
            "Evidence ID matches the run and immutable fingerprint.",
        ),
        _check(
            "fingerprint_match",
            source_identity == source_identity_for(source_url)
            and fingerprint == recomputed,
            "Persisted source identity and snippet reproduce the fingerprint.",
        ),
        _check(
            "url_scheme",
            parsed.scheme.lower() in {"http", "https"},
            "Source URL uses an allowed absolute scheme.",
        ),
        _check(
            "url_userinfo_absent",
            username is None and password is None,
            "Source URL contains no user information.",
        ),
        _check(
            "url_hostname",
            _hostname_is_valid(hostname),
            "Source URL has a syntactically valid hostname.",
        ),
        _check(
            "declared_source_boundary",
            _declared_boundary_passes(
                run=run,
                evidence=evidence,
                hostname=hostname,
            ),
            "Source stays within the persisted run boundary.",
        ),
        _check(
            "snippet_present",
            bool(snippet.strip()),
            "Persisted snippet is non-empty.",
        ),
        _check(
            "snippet_within_bounds",
            len(snippet) <= MAX_PERSISTED_SNIPPET_LENGTH,
            "Persisted snippet stays within the Evidence contract.",
        ),
    )
    status = "eligible" if all(item.passed for item in checks) else "blocked"
    payload = {
        "run_id": run_id,
        "evidence_id": evidence_id,
        "evidence_fingerprint": fingerprint,
        "preflight_version": PREFLIGHT_VERSION,
        "status": status,
        "checks": [item.model_dump(mode="json") for item in checks],
    }
    return EvidencePreflightResult(
        preflight_id=preflight_id_for(payload),
        preflight_hash=canonical_hash(payload),
        checks=checks,
        **{
            key: value
            for key, value in payload.items()
            if key != "checks"
        },
    )
```

Do not import `socket`, `requests`, `httpx`, Tavily, browser tooling, LangChain,
or any model client in this module.

- [ ] **Step 4: Run preflight and existing Talent boundary tests**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_service.py \
  tests/unit/test_talent_contracts.py \
  tests/unit/test_talent_search.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit Task 3**

Stage only:

```bash
git add \
  api/evidence_verification_service.py \
  tests/unit/test_evidence_verification_service.py
git commit -m "feat(research): evaluate evidence verification preflight"
```

## Task 4: Append Human Decisions And Derive Effective State

**Files:**

- Modify: `api/evidence_verification_repository.py`
- Create: `tests/unit/test_evidence_verification_repository.py`

- [ ] **Step 1: Write failing decision-ledger tests**

Create `tests/unit/test_evidence_verification_repository.py` with one reusable
run fixture and the decision tests below:

```python
from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from agent.research import EvidenceEntry
from api.evidence_verification_models import VerificationDecisionRequest
from api.evidence_verification_repository import (
    VerificationConflict,
    accept_verification_decision,
    get_or_create_evidence_preflight,
    get_effective_verification,
    init_evidence_verification_schema,
    list_effective_verifications,
)
from api.run_repository import create_run, finalize_run_transaction


def _persisted_evidence(
    tmp_path,
    *,
    suffix="ordinary",
    baseline_origin="none",
    source_url="https://jobs.example.com/role",
    declared_source_url=None,
):
    db_path = str(tmp_path / f"{suffix}.db")
    declared_source_url = declared_source_url or source_url
    declared_samples = (
        [
            {
                "sample_id": "aggregate-v1",
                "source_type": "provided_aggregate",
                "reference": "aggregate-v1",
            }
        ]
        if baseline_origin == "declared_fixture"
        else [
            {
                "sample_id": "job-1",
                "source_type": "public_job_posting",
                "reference": declared_source_url,
            }
        ]
    )
    created = create_run(
        db_path=db_path,
        thread_id=f"thread-{suffix}",
        query="query",
        profile_id="talent-hiring-signal",
        scope={
            "target_roles": ["AI Agent Engineer"],
            "target_companies": [],
            "time_window": {"start": "2026-01-01", "end": "2026-06-12"},
            "declared_samples": declared_samples,
            "allowed_source_types": [
                "provided_aggregate"
                if baseline_origin == "declared_fixture"
                else "public_job_posting"
            ],
            "research_questions": ["question-1"],
            "requested_outputs": ["decision_brief"],
        },
    )
    entry = EvidenceEntry(
        thread_id=f"thread-{suffix}",
        query_text="query",
        subagent_name="network_search",
        tool_name="internet_search",
        source_url=source_url,
        snippet="Persisted evidence",
        citation_status="cited",
        verification_status=(
            "verified"
            if baseline_origin == "declared_fixture"
            else "unverified"
        ),
        baseline_verification_origin=baseline_origin,
    )
    assert finalize_run_transaction(
        db_path=db_path,
        run_id=created["run_id"],
        segment_id=created["segment_id"],
        expected_state_version=0,
        allowed_previous_statuses={"pending"},
        execution_status="completed",
        delivery_status="ready",
        evidence_entries=[entry],
    )
    evidence_id = f"ev_{created['run_id']}_{entry.evidence_fingerprint}"
    return db_path, created["run_id"], evidence_id, entry.evidence_fingerprint


def _verify_request(
    *,
    verification_id="verification-1",
    fingerprint,
    expected_revision=0,
):
    return VerificationDecisionRequest(
        verification_id=verification_id,
        evidence_fingerprint=fingerprint,
        expected_revision=expected_revision,
        action="verify",
        confirm_source_match=True,
    )


def _reject_request(
    *,
    verification_id="verification-2",
    fingerprint,
    expected_revision,
):
    return VerificationDecisionRequest(
        verification_id=verification_id,
        evidence_fingerprint=fingerprint,
        expected_revision=expected_revision,
        action="reject",
        reason_code="content_mismatch",
        reason_note="The persisted snippet does not match the source.",
    )


def test_first_verify_appends_revision_one_and_derives_human_verified(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)

    accepted = accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=_verify_request(fingerprint=fingerprint),
        actor_fingerprint="actor-hash",
    )
    projection = get_effective_verification(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
    )

    assert accepted.idempotent_replay is False
    assert accepted.decision.revision == 1
    assert projection.verification_status == "verified"
    assert projection.verification_state == "verified"
    assert projection.verification_origin == "human"
    assert projection.verification_revision == 1
    assert projection.decision_id == "verification-1"


def test_preflight_persistence_is_deterministic_and_idempotent(tmp_path):
    db_path, run_id, evidence_id, _ = _persisted_evidence(tmp_path)

    first = get_or_create_evidence_preflight(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
    )
    second = get_or_create_evidence_preflight(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
    )

    assert first == second
    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM evidence_verification_preflights_v2
            WHERE preflight_id = ?
            """,
            (first.preflight_id,),
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1


def test_same_verification_id_and_request_is_idempotent(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)
    request = _verify_request(fingerprint=fingerprint)

    first = accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=request,
        actor_fingerprint="actor-hash",
    )
    second = accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=request,
        actor_fingerprint="actor-hash",
    )

    assert first.decision == second.decision
    assert second.idempotent_replay is True


def test_decision_rejects_missing_actor_fingerprint(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)

    with pytest.raises(
        VerificationConflict,
        match="verification_persistence_conflict",
    ):
        accept_verification_decision(
            db_path=db_path,
            run_id=run_id,
            evidence_id=evidence_id,
            request=_verify_request(fingerprint=fingerprint),
            actor_fingerprint="",
        )


def test_same_verification_id_with_different_request_conflicts(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)
    accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=_verify_request(fingerprint=fingerprint),
        actor_fingerprint="actor-hash",
    )

    with pytest.raises(VerificationConflict, match="verification_id_conflict"):
        accept_verification_decision(
            db_path=db_path,
            run_id=run_id,
            evidence_id=evidence_id,
            request=_reject_request(
                verification_id="verification-1",
                fingerprint=fingerprint,
                expected_revision=1,
            ),
            actor_fingerprint="actor-hash",
        )


def test_stale_fingerprint_fails_without_persistence(tmp_path):
    db_path, run_id, evidence_id, _ = _persisted_evidence(tmp_path)

    with pytest.raises(
        VerificationConflict,
        match="evidence_fingerprint_mismatch",
    ):
        accept_verification_decision(
            db_path=db_path,
            run_id=run_id,
            evidence_id=evidence_id,
            request=_verify_request(fingerprint="b" * 64),
            actor_fingerprint="actor-hash",
        )

    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM evidence_verification_decisions_v2"
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 0


def test_correction_appends_revision_two_and_keeps_revision_one(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)
    accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=_verify_request(fingerprint=fingerprint),
        actor_fingerprint="actor-hash",
    )

    corrected = accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=_reject_request(
            fingerprint=fingerprint,
            expected_revision=1,
        ),
        actor_fingerprint="actor-hash",
    )
    projection = get_effective_verification(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
    )

    assert corrected.decision.revision == 2
    assert projection.verification_status == "unverified"
    assert projection.verification_state == "rejected"
    assert projection.verification_origin == "human"
    connection = sqlite3.connect(db_path)
    try:
        revisions = [
            row[0]
            for row in connection.execute(
                """
                SELECT revision
                FROM evidence_verification_decisions_v2
                ORDER BY revision
                """
            )
        ]
    finally:
        connection.close()
    assert revisions == [1, 2]


def test_expected_revision_fences_concurrent_writers(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)
    init_evidence_verification_schema(db_path)

    def submit(index):
        return accept_verification_decision(
            db_path=db_path,
            run_id=run_id,
            evidence_id=evidence_id,
            request=_verify_request(
                verification_id=f"verification-{index}",
                fingerprint=fingerprint,
                expected_revision=0,
            ),
            actor_fingerprint=f"actor-{index}",
        )

    outcomes = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(submit, index) for index in (1, 2)]
        for future in futures:
            try:
                outcomes.append(future.result())
            except VerificationConflict as exc:
                outcomes.append(exc.code)

    assert sum(not isinstance(item, str) for item in outcomes) == 1
    assert outcomes.count("verification_revision_conflict") == 1


def test_blocked_preflight_cannot_verify_but_can_reject(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(
        tmp_path,
        source_url="https://other.example.com/role",
        declared_source_url="https://jobs.example.com/role",
    )

    with pytest.raises(
        VerificationConflict,
        match="evidence_preflight_blocked",
    ):
        accept_verification_decision(
            db_path=db_path,
            run_id=run_id,
            evidence_id=evidence_id,
            request=_verify_request(fingerprint=fingerprint),
            actor_fingerprint="actor-hash",
        )

    rejected = accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=_reject_request(
            fingerprint=fingerprint,
            expected_revision=0,
        ),
        actor_fingerprint="actor-hash",
    )
    assert rejected.decision.action == "reject"


def test_baseline_origin_is_not_human_and_legacy_status_alone_is_ignored(tmp_path):
    fixture = _persisted_evidence(
        tmp_path,
        suffix="fixture",
        baseline_origin="declared_fixture",
    )
    ordinary = _persisted_evidence(
        tmp_path,
        suffix="ordinary",
        baseline_origin="none",
    )

    fixture_projection = get_effective_verification(
        db_path=fixture[0],
        run_id=fixture[1],
        evidence_id=fixture[2],
    )
    ordinary_projection = get_effective_verification(
        db_path=ordinary[0],
        run_id=ordinary[1],
        evidence_id=ordinary[2],
    )

    assert fixture_projection.verification_origin == "declared_fixture"
    assert fixture_projection.verification_state == "verified"
    assert fixture_projection.verification_revision == 0
    assert ordinary_projection.verification_origin == "none"
    assert ordinary_projection.verification_state == "unverified"


def test_list_projection_is_stable_and_sorted_by_evidence_id(tmp_path):
    db_path, run_id, _, _ = _persisted_evidence(tmp_path)

    projections = list_effective_verifications(
        db_path=db_path,
        run_id=run_id,
    )

    assert projections == sorted(
        projections,
        key=lambda item: item.evidence_id,
    )
```

- [ ] **Step 2: Run decision tests and confirm RED**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_repository.py -q
```

Expected: imports fail because append and projection functions are not yet
implemented.

- [ ] **Step 3: Add repository records and stable conflicts**

At the top of `api/evidence_verification_repository.py`, add:

```python
from dataclasses import dataclass
from typing import Any

from api.evidence_verification_models import (
    EffectiveEvidenceVerification,
    EvidencePreflightResult,
    VerificationDecisionRecord,
    VerificationDecisionRequest,
    verification_request_hash,
)
from api.evidence_verification_service import evaluate_evidence_preflight


@dataclass(frozen=True)
class VerificationDecisionAcceptance:
    decision: VerificationDecisionRecord
    preflight: EvidencePreflightResult
    idempotent_replay: bool


class VerificationConflict(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
```

Add private conversion helpers:

```python
def _decision_record(row: sqlite3.Row) -> VerificationDecisionRecord:
    return VerificationDecisionRecord.model_validate(
        {
            "verification_id": row["verification_id"],
            "run_id": row["run_id"],
            "evidence_id": row["evidence_id"],
            "evidence_fingerprint": row["evidence_fingerprint"],
            "revision": row["revision"],
            "action": row["action"],
            "reason_code": row["reason_code"],
            "reason_note": row["reason_note"],
            "preflight_id": row["preflight_id"],
            "created_at": row["created_at"],
        }
    )


def _preflight_record(row: sqlite3.Row) -> EvidencePreflightResult:
    return EvidencePreflightResult.model_validate(
        {
            "preflight_id": row["preflight_id"],
            "run_id": row["run_id"],
            "evidence_id": row["evidence_id"],
            "evidence_fingerprint": row["evidence_fingerprint"],
            "preflight_version": row["preflight_version"],
            "status": row["status"],
            "checks": json.loads(row["checks_json"]),
            "preflight_hash": row["preflight_hash"],
        }
    )


def _target_rows(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    evidence_id: str,
) -> tuple[sqlite3.Row, sqlite3.Row]:
    run = connection.execute(
        """
        SELECT run_id, profile_id, scope_json
        FROM research_runs_v2
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()
    evidence = connection.execute(
        """
        SELECT *
        FROM evidence_entries_v2
        WHERE run_id = ? AND evidence_id = ?
        """,
        (run_id, evidence_id),
    ).fetchone()
    if run is None or evidence is None:
        raise VerificationConflict("evidence_not_found")
    return run, evidence
```

- [ ] **Step 4: Persist preflight inside the decision transaction**

Add:

```python
def _persist_preflight(
    connection: sqlite3.Connection,
    *,
    preflight: EvidencePreflightResult,
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO evidence_verification_preflights_v2 (
            preflight_id,
            run_id,
            evidence_id,
            evidence_fingerprint,
            preflight_version,
            status,
            checks_json,
            preflight_hash,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            preflight.preflight_id,
            preflight.run_id,
            preflight.evidence_id,
            preflight.evidence_fingerprint,
            preflight.preflight_version,
            preflight.status,
            json.dumps(
                [item.model_dump(mode="json") for item in preflight.checks],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            preflight.preflight_hash,
            _now(),
        ),
    )
    stored = connection.execute(
        """
        SELECT preflight_hash
        FROM evidence_verification_preflights_v2
        WHERE preflight_id = ?
        """,
        (preflight.preflight_id,),
    ).fetchone()
    if stored is None or stored["preflight_hash"] != preflight.preflight_hash:
        raise VerificationConflict("verification_persistence_conflict")
```

- [ ] **Step 5: Expose deterministic internal preflight persistence**

Add:

```python
def get_or_create_evidence_preflight(
    *,
    db_path: str,
    run_id: str,
    evidence_id: str,
) -> EvidencePreflightResult:
    init_evidence_verification_schema(db_path)
    connection = _connect(db_path)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            run, evidence = _target_rows(
                connection,
                run_id=run_id,
                evidence_id=evidence_id,
            )
            preflight = evaluate_evidence_preflight(
                run=dict(run),
                evidence=dict(evidence),
            )
            _persist_preflight(connection, preflight=preflight)
            row = connection.execute(
                """
                SELECT *
                FROM evidence_verification_preflights_v2
                WHERE preflight_id = ?
                """,
                (preflight.preflight_id,),
            ).fetchone()
            return _preflight_record(row)
    finally:
        connection.close()
```

This is an internal repository operation for PR2 queue construction. It is not
an HTTP mutation route.

- [ ] **Step 6: Implement fenced append and idempotent replay**

Add:

```python
def accept_verification_decision(
    *,
    db_path: str,
    run_id: str,
    evidence_id: str,
    request: VerificationDecisionRequest,
    actor_fingerprint: str,
) -> VerificationDecisionAcceptance:
    init_evidence_verification_schema(db_path)
    if not actor_fingerprint or len(actor_fingerprint) > 128:
        raise VerificationConflict("verification_persistence_conflict")
    request_hash = verification_request_hash(
        run_id=run_id,
        evidence_id=evidence_id,
        request=request,
    )
    connection = _connect(db_path)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT *
                FROM evidence_verification_decisions_v2
                WHERE verification_id = ?
                """,
                (request.verification_id,),
            ).fetchone()
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise VerificationConflict("verification_id_conflict")
                preflight_row = connection.execute(
                    """
                    SELECT *
                    FROM evidence_verification_preflights_v2
                    WHERE preflight_id = ?
                    """,
                    (existing["preflight_id"],),
                ).fetchone()
                if preflight_row is None:
                    raise VerificationConflict(
                        "verification_persistence_conflict"
                    )
                return VerificationDecisionAcceptance(
                    decision=_decision_record(existing),
                    preflight=_preflight_record(preflight_row),
                    idempotent_replay=True,
                )

            run, evidence = _target_rows(
                connection,
                run_id=run_id,
                evidence_id=evidence_id,
            )
            if (
                evidence["evidence_fingerprint"]
                != request.evidence_fingerprint
            ):
                raise VerificationConflict(
                    "evidence_fingerprint_mismatch"
                )
            preflight = evaluate_evidence_preflight(
                run=dict(run),
                evidence=dict(evidence),
            )
            _persist_preflight(connection, preflight=preflight)
            if request.action == "verify" and preflight.status != "eligible":
                raise VerificationConflict("evidence_preflight_blocked")

            current_revision = connection.execute(
                """
                SELECT COALESCE(MAX(revision), 0)
                FROM evidence_verification_decisions_v2
                WHERE run_id = ?
                  AND evidence_id = ?
                  AND evidence_fingerprint = ?
                """,
                (
                    run_id,
                    evidence_id,
                    request.evidence_fingerprint,
                ),
            ).fetchone()[0]
            if current_revision != request.expected_revision:
                raise VerificationConflict(
                    "verification_revision_conflict"
                )

            revision = current_revision + 1
            now = _now()
            connection.execute(
                """
                INSERT INTO evidence_verification_decisions_v2 (
                    verification_id,
                    run_id,
                    evidence_id,
                    evidence_fingerprint,
                    revision,
                    action,
                    reason_code,
                    reason_note,
                    preflight_id,
                    actor_fingerprint,
                    request_hash,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.verification_id,
                    run_id,
                    evidence_id,
                    request.evidence_fingerprint,
                    revision,
                    request.action,
                    request.reason_code,
                    request.reason_note,
                    preflight.preflight_id,
                    actor_fingerprint,
                    request_hash,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT *
                FROM evidence_verification_decisions_v2
                WHERE verification_id = ?
                """,
                (request.verification_id,),
            ).fetchone()
            return VerificationDecisionAcceptance(
                decision=_decision_record(row),
                preflight=preflight,
                idempotent_replay=False,
            )
    except sqlite3.IntegrityError as exc:
        message = str(exc)
        if "verification_id" in message:
            raise VerificationConflict("verification_id_conflict") from exc
        if "revision" in message:
            raise VerificationConflict(
                "verification_revision_conflict"
            ) from exc
        raise VerificationConflict(
            "verification_persistence_conflict"
        ) from exc
    finally:
        connection.close()
```

Pydantic validation owns missing reject reasons, so the repository does not
accept raw dictionaries.

- [ ] **Step 7: Implement effective state projection**

Add:

```python
def _effective_projection(
    *,
    evidence: sqlite3.Row,
    decision: sqlite3.Row | None,
) -> EffectiveEvidenceVerification:
    if decision is not None:
        verified = decision["action"] == "verify"
        return EffectiveEvidenceVerification(
            run_id=evidence["run_id"],
            evidence_id=evidence["evidence_id"],
            evidence_fingerprint=evidence["evidence_fingerprint"],
            verification_status="verified" if verified else "unverified",
            verification_state="verified" if verified else "rejected",
            verification_origin="human",
            verification_revision=decision["revision"],
            decision_id=decision["verification_id"],
        )
    if evidence["baseline_verification_origin"] == "declared_fixture":
        return EffectiveEvidenceVerification(
            run_id=evidence["run_id"],
            evidence_id=evidence["evidence_id"],
            evidence_fingerprint=evidence["evidence_fingerprint"],
            verification_status="verified",
            verification_state="verified",
            verification_origin="declared_fixture",
            verification_revision=0,
        )
    return EffectiveEvidenceVerification(
        run_id=evidence["run_id"],
        evidence_id=evidence["evidence_id"],
        evidence_fingerprint=evidence["evidence_fingerprint"],
        verification_status="unverified",
        verification_state="unverified",
        verification_origin="none",
        verification_revision=0,
    )


def get_effective_verification(
    *,
    db_path: str,
    run_id: str,
    evidence_id: str,
) -> EffectiveEvidenceVerification | None:
    init_evidence_verification_schema(db_path)
    connection = _connect(db_path)
    try:
        evidence = connection.execute(
            """
            SELECT *
            FROM evidence_entries_v2
            WHERE run_id = ? AND evidence_id = ?
            """,
            (run_id, evidence_id),
        ).fetchone()
        if evidence is None:
            return None
        decision = connection.execute(
            """
            SELECT *
            FROM evidence_verification_decisions_v2
            WHERE run_id = ?
              AND evidence_id = ?
              AND evidence_fingerprint = ?
            ORDER BY revision DESC
            LIMIT 1
            """,
            (
                run_id,
                evidence_id,
                evidence["evidence_fingerprint"],
            ),
        ).fetchone()
        return _effective_projection(
            evidence=evidence,
            decision=decision,
        )
    finally:
        connection.close()


def list_effective_verifications(
    *,
    db_path: str,
    run_id: str,
) -> list[EffectiveEvidenceVerification]:
    init_evidence_verification_schema(db_path)
    connection = _connect(db_path)
    try:
        evidence_rows = connection.execute(
            """
            SELECT *
            FROM evidence_entries_v2
            WHERE run_id = ?
            ORDER BY evidence_id
            """,
            (run_id,),
        ).fetchall()
        result = []
        for evidence in evidence_rows:
            decision = connection.execute(
                """
                SELECT *
                FROM evidence_verification_decisions_v2
                WHERE run_id = ?
                  AND evidence_id = ?
                  AND evidence_fingerprint = ?
                ORDER BY revision DESC
                LIMIT 1
                """,
                (
                    run_id,
                    evidence["evidence_id"],
                    evidence["evidence_fingerprint"],
                ),
            ).fetchone()
            result.append(
                _effective_projection(
                    evidence=evidence,
                    decision=decision,
                )
            )
        return result
    finally:
        connection.close()
```

Do not use `evidence_entries_v2.verification_status` to infer human authority.

- [ ] **Step 8: Run repository tests and confirm GREEN**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_repository.py \
  tests/unit/test_evidence_verification_service.py \
  tests/unit/test_evidence_verification_migrations.py -q
```

Expected: all selected tests pass.

- [ ] **Step 9: Commit Task 4**

Stage only:

```bash
git add \
  api/evidence_verification_repository.py \
  tests/unit/test_evidence_verification_repository.py
git commit -m "feat(research): append evidence verification decisions"
```

## Task 5: Finalize Deterministic Effective-State Snapshots

**Files:**

- Modify: `api/evidence_verification_repository.py`
- Modify: `tests/unit/test_evidence_verification_repository.py`

- [ ] **Step 1: Add failing snapshot tests**

Append to `tests/unit/test_evidence_verification_repository.py`:

```python
from api.evidence_verification_repository import finalize_verification_snapshot


def test_same_effective_state_reuses_snapshot_identity(tmp_path):
    db_path, run_id, _, _ = _persisted_evidence(tmp_path)

    first = finalize_verification_snapshot(
        db_path=db_path,
        run_id=run_id,
    )
    second = finalize_verification_snapshot(
        db_path=db_path,
        run_id=run_id,
    )

    assert first.idempotent_replay is False
    assert second.idempotent_replay is True
    assert first.snapshot == second.snapshot
    assert first.snapshot.revision == 1


def test_changed_effective_state_creates_next_snapshot_revision(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)
    initial = finalize_verification_snapshot(
        db_path=db_path,
        run_id=run_id,
    )
    accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=_verify_request(fingerprint=fingerprint),
        actor_fingerprint="actor-hash",
    )

    changed = finalize_verification_snapshot(
        db_path=db_path,
        run_id=run_id,
    )

    assert changed.idempotent_replay is False
    assert changed.snapshot.revision == 2
    assert changed.snapshot.snapshot_hash != initial.snapshot.snapshot_hash
    assert changed.snapshot.snapshot[0].verification_origin == "human"


def test_snapshot_json_is_sorted_and_omits_private_audit_fields(tmp_path):
    db_path, run_id, evidence_id, fingerprint = _persisted_evidence(tmp_path)
    accept_verification_decision(
        db_path=db_path,
        run_id=run_id,
        evidence_id=evidence_id,
        request=_reject_request(
            fingerprint=fingerprint,
            expected_revision=0,
        ),
        actor_fingerprint="private-actor",
    )

    accepted = finalize_verification_snapshot(
        db_path=db_path,
        run_id=run_id,
    )
    connection = sqlite3.connect(db_path)
    try:
        raw = connection.execute(
            """
            SELECT snapshot_json
            FROM evidence_verification_snapshots_v2
            WHERE snapshot_id = ?
            """,
            (accepted.snapshot.snapshot_id,),
        ).fetchone()[0]
    finally:
        connection.close()

    assert raw == json.dumps(
        [
            item.model_dump(mode="json")
            for item in accepted.snapshot.snapshot
        ],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert "private-actor" not in raw
    assert "request_hash" not in raw
    assert "reason_note" not in raw


def test_snapshot_rejects_unknown_run(tmp_path):
    with pytest.raises(VerificationConflict, match="evidence_not_found"):
        finalize_verification_snapshot(
            db_path=str(tmp_path / "missing.db"),
            run_id="run-missing",
        )
```

Also add `import json` to the test module.

- [ ] **Step 2: Run snapshot tests and confirm RED**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_repository.py \
  -k snapshot -q
```

Expected: collection or execution fails because
`finalize_verification_snapshot` does not exist.

- [ ] **Step 3: Add snapshot acceptance and row conversion**

In `api/evidence_verification_repository.py`, import:

```python
from api.evidence_verification_models import (
    VerificationSnapshotRecord,
    canonical_hash,
    snapshot_id_for,
)
```

Add:

```python
@dataclass(frozen=True)
class VerificationSnapshotAcceptance:
    snapshot: VerificationSnapshotRecord
    idempotent_replay: bool


def _snapshot_record(row: sqlite3.Row) -> VerificationSnapshotRecord:
    return VerificationSnapshotRecord.model_validate(
        {
            "snapshot_id": row["snapshot_id"],
            "run_id": row["run_id"],
            "revision": row["revision"],
            "snapshot": json.loads(row["snapshot_json"]),
            "snapshot_hash": row["snapshot_hash"],
            "created_at": row["created_at"],
        }
    )
```

- [ ] **Step 4: Implement one-transaction snapshot finalization**

Add:

```python
def finalize_verification_snapshot(
    *,
    db_path: str,
    run_id: str,
) -> VerificationSnapshotAcceptance:
    init_evidence_verification_schema(db_path)
    connection = _connect(db_path)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute(
                """
                SELECT run_id
                FROM research_runs_v2
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if run is None:
                raise VerificationConflict("evidence_not_found")

            evidence_rows = connection.execute(
                """
                SELECT *
                FROM evidence_entries_v2
                WHERE run_id = ?
                ORDER BY evidence_id
                """,
                (run_id,),
            ).fetchall()
            projections = []
            for evidence in evidence_rows:
                decision = connection.execute(
                    """
                    SELECT *
                    FROM evidence_verification_decisions_v2
                    WHERE run_id = ?
                      AND evidence_id = ?
                      AND evidence_fingerprint = ?
                    ORDER BY revision DESC
                    LIMIT 1
                    """,
                    (
                        run_id,
                        evidence["evidence_id"],
                        evidence["evidence_fingerprint"],
                    ),
                ).fetchone()
                projections.append(
                    _effective_projection(
                        evidence=evidence,
                        decision=decision,
                    )
                )

            snapshot_payload = [
                item.model_dump(mode="json")
                for item in projections
            ]
            snapshot_hash = canonical_hash(snapshot_payload)
            existing = connection.execute(
                """
                SELECT *
                FROM evidence_verification_snapshots_v2
                WHERE run_id = ? AND snapshot_hash = ?
                """,
                (run_id, snapshot_hash),
            ).fetchone()
            if existing is not None:
                return VerificationSnapshotAcceptance(
                    snapshot=_snapshot_record(existing),
                    idempotent_replay=True,
                )

            revision = connection.execute(
                """
                SELECT COALESCE(MAX(revision), 0) + 1
                FROM evidence_verification_snapshots_v2
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()[0]
            snapshot_id = snapshot_id_for(
                run_id=run_id,
                snapshot_hash=snapshot_hash,
            )
            now = _now()
            connection.execute(
                """
                INSERT INTO evidence_verification_snapshots_v2 (
                    snapshot_id,
                    run_id,
                    revision,
                    snapshot_json,
                    snapshot_hash,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    run_id,
                    revision,
                    json.dumps(
                        snapshot_payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    snapshot_hash,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT *
                FROM evidence_verification_snapshots_v2
                WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            ).fetchone()
            return VerificationSnapshotAcceptance(
                snapshot=_snapshot_record(row),
                idempotent_replay=False,
            )
    except sqlite3.IntegrityError as exc:
        raise VerificationConflict(
            "verification_persistence_conflict"
        ) from exc
    finally:
        connection.close()
```

The transaction reads decisions and writes the snapshot under the same
`BEGIN IMMEDIATE` fence. Do not call `list_effective_verifications()` here,
because that function opens a second connection and would break the snapshot
boundary.

- [ ] **Step 5: Run the complete repository test file**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_repository.py -q
```

Expected: all decision and snapshot tests pass.

- [ ] **Step 6: Commit Task 5**

Stage only:

```bash
git add \
  api/evidence_verification_repository.py \
  tests/unit/test_evidence_verification_repository.py
git commit -m "feat(research): finalize verification snapshots"
```

## Task 6: Preserve P1A Fixture And P1C Review Compatibility

**Files:**

- Modify: `agent/main_agent.py`
- Modify: `tests/integration/test_evidence_lifecycle.py`
- Create: `tests/integration/test_evidence_verification_compatibility.py`
- Test: `tests/unit/test_talent_artifacts.py`
- Test: `tests/integration/test_durable_review_lifecycle.py`
- Test: `tests/integration/test_durable_review_api.py`

- [ ] **Step 1: Extend the existing preload test and add a compatibility test**

In
`test_talent_run_prefetches_declared_aggregate_evidence_and_normalizes_refs`
inside `tests/integration/test_evidence_lifecycle.py`, preserve the current
assertion:

```python
assert all(
    entry.verification_status == "verified"
    for entry in outcome.evidence_entries
)
```

and add:

```python
assert all(
    entry.baseline_verification_origin == "declared_fixture"
    for entry in outcome.evidence_entries
)
```

Create `tests/integration/test_evidence_verification_compatibility.py`:

```python
from datetime import datetime, timezone

from agent.research import EvidenceEntry
from agent.talent_contracts import ResearchPacket
from api.evidence_verification_repository import get_effective_verification
from api.run_repository import (
    create_run,
    finalize_run_transaction,
    get_run,
)
from api.talent_artifacts import build_talent_artifacts


def test_declared_fixture_origin_preserves_p1a_artifact_contract(tmp_path):
    db_path = str(tmp_path / "tasks.db")
    scope = {
        "target_roles": ["AI Agent Engineer"],
        "target_companies": [],
        "time_window": {"start": "2026-01-01", "end": "2026-06-12"},
        "declared_samples": [
            {
                "sample_id": "aggregate-v1",
                "source_type": "provided_aggregate",
                "reference": "aggregate-v1",
            }
        ],
        "allowed_source_types": ["provided_aggregate"],
        "research_questions": ["question-1"],
        "requested_outputs": ["decision_brief"],
    }
    created = create_run(
        db_path=db_path,
        thread_id="thread-1",
        query="query",
        profile_id="talent-hiring-signal",
        scope=scope,
    )
    evidence = EvidenceEntry(
        thread_id="thread-1",
        query_text="query",
        subagent_name="network_search",
        tool_name="internet_search",
        source_url="https://jobs.example.com/role",
        snippet="Evaluation and observability are required.",
        citation_status="cited",
        verification_status="verified",
        baseline_verification_origin="declared_fixture",
    )
    evidence_id = (
        f"ev_{created['run_id']}_{evidence.evidence_fingerprint}"
    )
    packet = ResearchPacket.model_validate(
        {
            "packet_id": "packet-1",
            "scope_id": "aggregate-v1",
            "findings": [
                {
                    "finding_id": "finding-1",
                    "research_question_id": "question-1",
                    "statement": "Evaluation is present.",
                    "evidence_refs": [evidence_id],
                    "sample_scope": "declared aggregate",
                    "confidence": 0.8,
                }
            ],
            "candidate_claims": [
                {
                    "claim_id": "claim-1",
                    "text": "Evaluation is a hiring signal.",
                    "claim_type": "signal",
                    "finding_refs": ["finding-1"],
                    "evidence_refs": [evidence_id],
                    "confidence": 0.8,
                    "citation_status": "cited",
                    "verification_status": "unverified",
                    "review_status": "pending",
                    "conflict_status": "none",
                }
            ],
        }
    )
    review, brief, artifacts = build_talent_artifacts(
        run_id=created["run_id"],
        scope=scope,
        packets=[packet],
        evidence_entries=[evidence],
        generated_at=datetime(2026, 6, 12, tzinfo=timezone.utc),
    )

    assert finalize_run_transaction(
        db_path=db_path,
        run_id=created["run_id"],
        segment_id=created["segment_id"],
        expected_state_version=0,
        allowed_previous_statuses={"pending"},
        execution_status="completed",
        review_status=review.status,
        delivery_status="ready",
        evidence_entries=[evidence],
        research_packets=[packet],
        review_bundle=review,
        artifacts=artifacts,
    )

    stored = get_run(db_path=db_path, run_id=created["run_id"])
    projection = get_effective_verification(
        db_path=db_path,
        run_id=created["run_id"],
        evidence_id=evidence_id,
    )

    assert brief.evidence_summary[0]["verification_status"] == "verified"
    assert review.status == "not_required"
    assert stored["evidence"][0]["verification_status"] == "verified"
    assert "baseline_verification_origin" not in stored["evidence"][0]
    assert projection.verification_origin == "declared_fixture"
    assert projection.verification_state == "verified"
    assert projection.verification_revision == 0


def test_pr1_creates_no_publication_or_new_review_revision_tables(tmp_path):
    db_path = str(tmp_path / "tasks.db")
    created = create_run(
        db_path=db_path,
        thread_id="thread-1",
        query="query",
    )

    get_effective_verification(
        db_path=db_path,
        run_id=created["run_id"],
        evidence_id="missing",
    )

    import sqlite3

    connection = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        connection.close()
    assert "run_publications_v2" not in tables
```

- [ ] **Step 2: Run compatibility tests and confirm RED**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/integration/test_evidence_lifecycle.py::test_talent_run_prefetches_declared_aggregate_evidence_and_normalizes_refs \
  tests/integration/test_evidence_verification_compatibility.py \
  tests/unit/test_talent_artifacts.py -q
```

Expected: the preload assertion fails because aggregate Evidence still has
baseline origin `none`.

- [ ] **Step 3: Mark only controlled aggregate preload Evidence**

In `agent/main_agent.py`, extend the existing `replace()` call inside
`_freeze_execution_outcome()`:

```python
replace(
    entry,
    citation_status="cited",
    verification_status="verified",
    baseline_verification_origin="declared_fixture",
)
```

Do not infer this origin from `tool_name`, arbitrary model output, URL, or
`verification_status`. The mark remains gated by
`accumulator.verified_evidence_ids`, which is populated only by the controlled
server-bundled preload path.

- [ ] **Step 4: Run P1A and P1C focused compatibility**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/integration/test_evidence_lifecycle.py \
  tests/integration/test_evidence_verification_compatibility.py \
  tests/unit/test_talent_artifacts.py \
  tests/unit/test_talent_value_gate_runner.py \
  tests/integration/test_durable_review_lifecycle.py \
  tests/integration/test_durable_review_api.py -q
```

Expected: all selected tests pass. Existing review approval/rejection behavior
must not create or mutate Evidence Verification decisions.

- [ ] **Step 5: Commit Task 6**

Stage only:

```bash
git add \
  agent/main_agent.py \
  tests/integration/test_evidence_lifecycle.py \
  tests/integration/test_evidence_verification_compatibility.py
git commit -m "fix(research): preserve declared fixture verification origin"
```

## Task 7: Document Authority Boundaries And Close PR1

**Files:**

- Create: `docs/decisions/evidence-verification-authority.md`
- Modify: `spec/data-models.md`
- Modify: `docs/README.md`
- Test: all PR1 focused tests
- Test: full backend suite

- [ ] **Step 1: Add the architecture decision**

Create `docs/decisions/evidence-verification-authority.md`:

```markdown
# Evidence Verification Authority

## Decision

Decision Research Agent keeps collected Evidence immutable and stores human
verification as append-only decisions bound to one exact
`run_id + evidence_id + evidence_fingerprint` tuple.

Deterministic preflight establishes whether a persisted Evidence snapshot is
eligible for a human `verify` decision. Preflight does not fetch a URL, resolve
DNS, call an LLM, or judge truth. A human decision may append `verify` or
`reject`; corrections append a new revision and never update prior rows.

## Authority Boundary

- `evidence_entries_v2` owns what the run collected.
- `baseline_verification_origin=declared_fixture` records only the controlled
  server-bundled benchmark contract.
- `evidence_verification_preflights_v2` owns deterministic eligibility checks.
- `evidence_verification_decisions_v2` owns human decision history.
- `evidence_verification_snapshots_v2` owns one deterministic effective-state
  input for later artifact rebuilding.
- Review approval owns delivery permission and never grants Evidence
  verification.
- LangSmith remains diagnostic correlation and is not a business ledger.

`human_verified` means an authenticated reviewer confirmed that the persisted
snippet for the exact fingerprint was consistent with the identified source at
the recorded decision time. It is not a universal truth, claim approval, market
accuracy score, or guarantee that the source remains unchanged.

## Compatibility

Existing Talent benchmark fixtures remain effectively `verified` with origin
`declared_fixture`. They are not labeled `human`. Ordinary legacy
`verification_status=verified` rows do not gain fixture or human authority
unless the migration also proves the persisted Talent scope declared a
`provided_aggregate`.

PR1 adds no API, CLI, publication pointer, artifact revision, or new review
workflow. Those changes require the separately approved P2A PR2.

## Rejected Alternatives

- Mutating `evidence_entries_v2.verification_status`: rejected because it erases
  decision history and stale fingerprint boundaries.
- Automatic LLM verification: rejected because a model is not the human
  authority for this milestone.
- Server-side URL retrieval: deferred because it adds SSRF, redirect, DNS,
  payload, content-type, and source-drift risks not required for PR1.
```

- [ ] **Step 2: Update current data-model documentation**

Append a new `Evidence Verification Authority` section to
`spec/data-models.md` that includes:

```markdown
## Evidence Verification Authority

P2A PR1 keeps `evidence_entries_v2` immutable and adds:

| Storage | Authority |
|---|---|
| `baseline_verification_origin` | Immutable collection-time origin: `none` or `declared_fixture` |
| `evidence_verification_preflights_v2` | Versioned deterministic, no-network eligibility checks |
| `evidence_verification_decisions_v2` | Append-only human `verify` / `reject` revisions |
| `evidence_verification_snapshots_v2` | Deterministic effective-state snapshots |

Effective public semantics are derived:

| Origin | State | Compatibility status |
|---|---|---|
| `none` | `unverified` | `unverified` |
| `declared_fixture` | `verified` | `verified` |
| `human` + `verify` | `verified` | `verified` |
| `human` + `reject` | `rejected` | `unverified` |

The baseline origin column never stores `human`. Human state comes only from
the latest accepted decision for the exact Evidence fingerprint. Review
approval remains independent and does not write these tables.

PR1 exposes only internal repository operations. It adds no HTTP/CLI mutation
surface and does not rebuild artifacts.
```

Add a 2026-06-22 change-log row describing the PR1 schema and authority
boundary.

- [ ] **Step 3: Link the plan and ADR**

In `docs/README.md`:

1. Add the ADR under the current technical-decision documentation.
2. Verify the existing
   `superpowers/plans/2026-06-22-p2a-verification-authority.md` link remains
   present exactly once.

Do not add public claims that PR2 or PR3 is implemented.

- [ ] **Step 4: Run focused PR1 verification**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_models.py \
  tests/unit/test_evidence_verification_service.py \
  tests/unit/test_evidence_verification_migrations.py \
  tests/unit/test_evidence_verification_repository.py \
  tests/integration/test_evidence_verification_compatibility.py \
  tests/integration/test_evidence_lifecycle.py \
  tests/unit/test_run_repository.py \
  tests/unit/test_run_migrations.py \
  tests/unit/test_review_migrations.py \
  tests/unit/test_talent_artifacts.py \
  tests/unit/test_talent_value_gate_runner.py \
  tests/integration/test_durable_review_lifecycle.py \
  tests/integration/test_durable_review_api.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Run full backend verification**

Run:

```bash
../../.venv/bin/python -m pytest -q
```

Expected: the full suite passes. Record the actual count; do not reuse the
historical `682 passed` count.

The frontend build is not required because no frontend or public API contract
changes in PR1. The durable 13-gate runner is not required because review
workflow, checkpoint, resolution, and worker behavior are unchanged. Existing
durable review tests in Step 4 are still mandatory compatibility checks.

- [ ] **Step 6: Verify migration recovery and diff hygiene**

Run:

```bash
../../.venv/bin/python -m pytest \
  tests/unit/test_evidence_verification_migrations.py \
  tests/unit/test_run_migrations.py \
  tests/unit/test_review_migrations.py -q
git diff --check
git status --short
git diff --stat bcf2b9c...HEAD
git diff bcf2b9c...HEAD -- \
  agent \
  api \
  tests \
  docs \
  spec
```

Expected:

- migration tests prove idempotency, optional schema verification, and
  backup/restore;
- `git diff --check` emits no output;
- only the approved PR1 files are changed;
- no `.env`, secret, raw GStack artifact, private path, fixture, frontend, API,
  CLI, publication, or real-source proof change appears.
- no new active `DEEP_SEARCH_AGENT_*`, `deep_search_agent_tool.py`, or
  `service=deep-search-agent` reference is introduced outside unchanged
  compatibility and historical files.

- [ ] **Step 7: Commit documentation and final PR1 closure**

Stage only:

```bash
git add \
  docs/decisions/evidence-verification-authority.md \
  docs/README.md \
  spec/data-models.md \
  docs/superpowers/specs/2026-06-21-p2a-evidence-verification-design.md \
  docs/superpowers/plans/2026-06-22-p2a-verification-authority.md
git commit -m "docs(research): document verification authority"
```

Do not push or create a PR without explicit authorization.

## PR1 Acceptance Gate

PR1 is ready for independent review only when all are true:

- [ ] Migration is additive, idempotent, schema-verified, backed up, and
  recoverable.
- [ ] Fresh Evidence writes persist immutable baseline origin.
- [ ] Existing fixture rows are backfilled only with Talent profile,
  aggregate-only scope, and legacy verified status together; mixed-source runs
  are not inferred.
- [ ] No ordinary or legacy verified row is described as human-verified.
- [ ] Preflight has stable check order/codes and performs zero network I/O.
- [ ] `verify` requires eligible preflight and explicit confirmation.
- [ ] `reject` requires a bounded reason and may record a blocked preflight.
- [ ] Decision ID replay is idempotent; content mismatch conflicts.
- [ ] Expected revision fencing permits exactly one concurrent winner.
- [ ] Correction creates revision 2 and preserves revision 1.
- [ ] Effective state is reproducible from immutable Evidence plus decisions.
- [ ] Same effective state returns the same snapshot; changed state creates the
  next immutable revision.
- [ ] Snapshot content omits actor fingerprint, request hash, and reason note.
- [ ] Current run/API projection does not expose the internal baseline column.
- [ ] P1A fixture artifacts and P1C review behavior remain unchanged.
- [ ] No API, CLI, publication, artifact rebuild, frontend, or real-source work
  entered the diff.
- [ ] No new legacy identifier is introduced; existing runtime compatibility
  remains unchanged and unexpanded.
- [ ] Focused tests, full backend suite, and `git diff --check` pass.

## Execution Order

Execute Tasks 1 through 7 sequentially on branch
`codex/p2a-evidence-verification-design` in its existing isolated worktree.

To control context and quota, the execution window should load:

1. this file's header through `## Public And Internal Contracts`;
2. only the current `## Task N` section, bounded by the next task heading;
3. `## PR1 Acceptance Gate` before final verification.

Do not repeatedly load the complete plan after execution starts. The plan is a
reference source, not a prompt that must remain fully resident in every turn.

Use `superpowers:executing-plans` and
`superpowers:test-driven-development`. Do not use coding subagents. Stop and
return to planning if implementation requires:

- replacing `evidence_entries_v2`;
- changing review uniqueness or exactly-once resolution;
- adding a server URL fetcher;
- exposing a mutation endpoint in PR1;
- changing canonical P1A artifact bytes merely to carry origin metadata; or
- touching PR2/PR3 files to make PR1 tests pass.
