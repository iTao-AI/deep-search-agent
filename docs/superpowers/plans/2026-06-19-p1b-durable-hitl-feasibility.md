# P1B Durable HITL Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that a feature-flagged, bundle-level Talent review can persist an `approve` or `reject` decision, survive process/container/forced-crash windows, and resolve exactly once without weakening evidence or delivery boundaries.

**Architecture:** Keep the application SQLite database authoritative for `ResearchRun`, immutable review decisions, workflow state, leases, resolutions, and artifacts. Use a separate SQLite LangGraph checkpointer for a pure no-model/no-tool review gate, with deterministic identities, `durability="sync"`, startup reconciliation, and fail-closed `manual_recovery` for ambiguous cross-database state.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLite WAL, LangGraph 1.2.5, `langgraph-checkpoint-sqlite` 3.1.0, pytest, Docker Compose.

---

## Source of Truth

- Design spec: `docs/superpowers/specs/2026-06-19-p1b-durable-hitl-feasibility-design.md`
- Current baseline: `python -m pytest -q` -> `534 passed, 5 warnings in 58.19s`
- Base commit: `0c8adee93607531625bd46e75cb6c46fa4ab9f65`
- Planning branch: `codex/p1b-durable-hitl-feasibility`

## Scope Lock

### Feasibility Boundary

This milestone proves durable review behavior for the repository's current
single-service, persistent-volume deployment shape. Official LangGraph guidance
positions `SqliteSaver` as a lightweight/small-project checkpointer and recommends
Postgres-backed savers for production workloads. Therefore:

- a thirteen-gate PASS proves P1B feasibility, not general production readiness;
- the feature remains disabled by default after PASS;
- multi-region, horizontally scaled, or high-throughput review execution is not
  claimed by this milestone;
- P1C must separately decide whether SQLite remains acceptable for the actual
  deployment envelope or whether a production checkpointer is required.

### Four-Day Execution Cutline

The four-day kill gate is evaluated incrementally, not only after all twelve tasks:

| Checkpoint | Required proof | Stop condition |
|---|---|---|
| Day 0 | constrained dependency install, reopen/resume compatibility, immutable contracts | any package or `durability="sync"` incompatibility |
| Day 1 | additive schema, atomic workflow seed, idempotent decision, pure gate reopen/resume | unresolved cross-database invariant or non-deterministic identity |
| Day 2 | bounded worker, lease/reclaim, strict API, lifecycle integration | duplicate resolution, unbounded retry, or auth fail-open |
| Day 3 | restart, exact crash-window convergence, Docker persistence, thirteen-gate report | any skip, ambiguous terminal state, or unexplained `manual_recovery` |

Do not continue polishing documentation or integration after a checkpoint has
already produced a P1B NO-GO. Record the failing evidence and stop the P1B
implementation.

### In Scope

- Bundle-level `approve` and `reject`.
- Feature-flagged authenticated HTTP decision path.
- Immutable decisions and resolutions.
- Persistent SQLite LangGraph checkpointer in a separate database.
- Pure review-gate graph.
- Lease/reclaim worker and startup reconciliation.
- Deterministic reviewed DecisionBrief artifacts for approval.
- Process restart, container restart, forced `SIGKILL`, idempotency, conflict,
  migration, backup, restore, and rollback verification.
- Machine-readable thirteen-gate report.

### Not in Scope

- Publicly enabling durable HITL.
- Claim-level editing, evidence changes, re-research, or automatic verification.
- UI, Tool Client review commands, ATS, email, or new delivery channels.
- Runtime Skills, Async Subagents, LLM reviewer, long-term memory, Agent Server,
  Postgres migration, multi-key reviewer identity, or RBAC.

## File Map

| File | Responsibility |
|---|---|
| `api/review_models.py` | Pydantic request/result contracts, enums, bounded values, deterministic identifiers |
| `api/review_repository.py` | Review schema, decision idempotency, leases, attempts, reconciliation reads, fenced resolution |
| `api/review_gate.py` | Persistent SQLite checkpointer adapter and pure interrupt/resume graph |
| `api/review_worker.py` | Bounded startup scan, lease claim, checkpoint creation/resume, recovery |
| `api/review_api.py` | Feature-flagged route, strict auth, sanitized error envelopes |
| `api/review_artifacts.py` | Deterministic reviewed DecisionBrief JSON/Markdown |
| `api/run_repository.py` | Add `blocked`, return sanitized review projection, atomically seed workflow |
| `api/run_migrations.py` | Verify and back up application/checkpoint schemas |
| `api/server.py` | Register router and start/stop worker only |
| `scripts/durable_hitl_gate_runner.py` | Execute and report the thirteen gates |
| `scripts/durable_hitl_crash_worker.py` | Subprocess fixture with injected stage hook for forced-crash tests |
| `tests/unit/test_review_*.py` | Contracts, repository, graph, artifacts, worker |
| `tests/integration/test_durable_review_*.py` | HTTP, restart, container, and crash windows |
| `docs/operations/durable-hitl-feasibility.md` | Operator commands, PASS/NO-GO interpretation, privacy boundary |

## Identity and Version Contract

Use these deterministic identities:

```python
def review_workflow_id(run_id: str, review_id: str, revision: int) -> str:
    value = f"{run_id}\n{review_id}\n{revision}"
    return f"rwf_{uuid.uuid5(uuid.NAMESPACE_URL, value).hex}"


def checkpoint_thread_id(workflow_id: str) -> str:
    return f"review_{workflow_id}"


def post_review_segment_id(run_id: str, review_id: str, revision: int) -> str:
    value = f"{run_id}\n{review_id}\n{revision}\npost_review"
    return f"{run_id}_seg_review_{uuid.uuid5(uuid.NAMESPACE_URL, value).hex[:16]}"


def review_resolution_id(decision_id: str) -> str:
    return f"resolution_{uuid.uuid5(uuid.NAMESPACE_URL, decision_id).hex}"
```

Expected run version sequence:

```text
0 pending
1 running
2 completed + review_required + workflow seeded
3 immutable decision accepted + resume_pending
4 resolved + ready|blocked
```

Workflow and lease housekeeping does not increment `ResearchRun.state_version`.

## Commit Strategy

Each task ends in a small local commit. Do not push or create a PR until all
thirteen gates and the final review pass.

---

### Task 1: Clean Dependency and Persistent Checkpointer Compatibility Gate

**Files:**
- Modify: `requirements.txt`
- Modify: `constraints.txt`
- Create: `tests/integration/test_review_checkpoint_compatibility.py`
- Create: `scripts/check_review_checkpoint_compatibility.py`

- [ ] **Step 1: Write the failing import and persistence test**

```python
# tests/integration/test_review_checkpoint_compatibility.py
from langgraph.types import Command

from scripts.check_review_checkpoint_compatibility import compile_graph


def test_sqlite_checkpoint_reopens_and_resumes_with_sync_durability(tmp_path):
    path = str(tmp_path / "checkpoints.db")
    config = {"configurable": {"thread_id": "review_rwf_test"}}

    graph, connection = compile_graph(path)
    first = graph.invoke({"decision_id": None}, config=config, durability="sync")
    assert first["__interrupt__"][0].value["workflow_id"] == "rwf_test"
    connection.close()

    reopened, reopened_connection = compile_graph(path)
    result = reopened.invoke(
        Command(resume="decision_001"),
        config=config,
        durability="sync",
    )
    assert result["decision_id"] == "decision_001"
    reopened_connection.close()
```

- [ ] **Step 2: Run the RED test in a disposable Python 3.11 environment**

Run:

```bash
python3.11 -m venv /tmp/decision-research-p1b-compat
/tmp/decision-research-p1b-compat/bin/python -m pip install -r requirements.txt -c constraints.txt
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_review_checkpoint_compatibility.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'langgraph.checkpoint.sqlite'`.

- [ ] **Step 3: Declare and pin the official SQLite checkpoint package**

Add:

```text
# requirements.txt, Database section
langgraph-checkpoint-sqlite>=3.1.0
```

Add:

```text
# constraints.txt
langgraph-checkpoint-sqlite==3.1.0
```

- [ ] **Step 4: Add a reusable compatibility script**

```python
# scripts/check_review_checkpoint_compatibility.py
from pathlib import Path
import sqlite3
import tempfile
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from langgraph.types import interrupt


class GateState(TypedDict):
    decision_id: str | None


def _gate(state: GateState):
    decision_id = interrupt(
        {
            "workflow_id": "rwf_test",
            "allowed": ["approve", "reject"],
        }
    )
    return {"decision_id": decision_id}


def compile_graph(path: str):
    connection = sqlite3.connect(path, check_same_thread=False)
    saver = SqliteSaver(connection)
    saver.setup()
    builder = StateGraph(GateState)
    builder.add_node("gate", _gate)
    builder.add_edge(START, "gate")
    builder.add_edge("gate", END)
    return builder.compile(checkpointer=saver), connection


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="review-checkpoint-") as tmp:
        path = str(Path(tmp) / "checkpoints.db")
        config = {"configurable": {"thread_id": "review_compatibility"}}
        graph, connection = compile_graph(path)
        first = graph.invoke(
            {"decision_id": None},
            config=config,
            durability="sync",
        )
        assert first["__interrupt__"]
        connection.close()

        graph, connection = compile_graph(path)
        result = graph.invoke(
            Command(resume="decision_compatibility"),
            config=config,
            durability="sync",
        )
        assert result["decision_id"] == "decision_compatibility"
        connection.close()
    print("persistent_review_checkpoint_compatibility=passed")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Recreate the disposable environment and run GREEN checks**

Run:

```bash
rm -rf /tmp/decision-research-p1b-compat
python3.11 -m venv /tmp/decision-research-p1b-compat
/tmp/decision-research-p1b-compat/bin/python -m pip install -r requirements.txt -c constraints.txt
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_review_checkpoint_compatibility.py -q
/tmp/decision-research-p1b-compat/bin/python scripts/check_review_checkpoint_compatibility.py
/tmp/decision-research-p1b-compat/bin/python - <<'PY'
import importlib.metadata as metadata
for package in (
    "deepagents",
    "langgraph",
    "langgraph-checkpoint",
    "langgraph-checkpoint-sqlite",
):
    print(package, metadata.version(package))
PY
```

Expected:

```text
1 passed
persistent_review_checkpoint_compatibility=passed
deepagents 0.6.10
langgraph 1.2.5
langgraph-checkpoint 4.1.1
langgraph-checkpoint-sqlite 3.1.0
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt constraints.txt \
  tests/integration/test_review_checkpoint_compatibility.py \
  scripts/check_review_checkpoint_compatibility.py
git commit -m "build(research): add persistent review checkpoint gate"
```

**Stop condition:** If the constrained environment cannot interrupt, close, reopen,
and resume with `durability="sync"`, record P1B NO-GO and do not continue.

---

### Task 2: Review Contracts, Feature Flag, and Deterministic Identities

**Files:**
- Create: `api/review_models.py`
- Create: `tests/unit/test_review_models.py`
- Modify: `.env.example`

- [ ] **Step 1: Write RED contract tests**

```python
# tests/unit/test_review_models.py
import pytest
from pydantic import ValidationError

from api.review_models import (
    ReviewDecisionRequest,
    durable_hitl_enabled,
    review_workflow_id,
    checkpoint_thread_id,
    post_review_segment_id,
)


def test_reject_requires_reason():
    with pytest.raises(ValidationError, match="reason"):
        ReviewDecisionRequest(
            decision_id="decision_001",
            review_revision=1,
            action="reject",
            expected_state_version=2,
        )


def test_approve_accepts_optional_reason():
    request = ReviewDecisionRequest(
        decision_id="decision_001",
        review_revision=1,
        action="approve",
        expected_state_version=2,
    )
    assert request.reason is None


def test_review_identities_are_stable_and_scoped():
    first = review_workflow_id("run_1", "review_1", 1)
    assert first == review_workflow_id("run_1", "review_1", 1)
    assert first != review_workflow_id("run_2", "review_1", 1)
    assert checkpoint_thread_id(first).startswith("review_rwf_")
    assert post_review_segment_id("run_1", "review_1", 1).startswith(
        "run_1_seg_review_"
    )


def test_durable_hitl_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        raising=False,
    )
    assert durable_hitl_enabled() is False
```

- [ ] **Step 2: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_models.py -q
```

Expected: FAIL because `api.review_models` does not exist.

- [ ] **Step 3: Implement bounded immutable contracts**

```python
# api/review_models.py
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from typing import Annotated, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


BoundedId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    ),
]
BoundedReason = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]
ReviewAction = Literal["approve", "reject"]
WorkflowStatus = Literal[
    "checkpoint_pending",
    "waiting_decision",
    "resume_pending",
    "resuming",
    "resolution_pending",
    "approved",
    "rejected",
    "manual_recovery",
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReviewDecisionRequest(FrozenModel):
    decision_id: BoundedId
    review_revision: int = Field(ge=1)
    action: ReviewAction
    reason: BoundedReason | None = None
    expected_state_version: int = Field(ge=0)

    @model_validator(mode="after")
    def require_reject_reason(self):
        if self.action == "reject" and self.reason is None:
            raise ValueError("reason is required for reject")
        return self


class ReviewDecisionRecord(FrozenModel):
    decision_id: BoundedId
    run_id: BoundedId
    review_id: BoundedId
    review_revision: int
    action: ReviewAction
    reason: str | None
    actor_fingerprint: str
    request_hash: str
    accepted_state_version: int
    created_at: datetime


def durable_hitl_enabled() -> bool:
    return os.getenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        "false",
    ).strip().lower() == "true"


def review_workflow_id(run_id: str, review_id: str, revision: int) -> str:
    value = f"{run_id}\n{review_id}\n{revision}"
    return f"rwf_{uuid.uuid5(uuid.NAMESPACE_URL, value).hex}"


def checkpoint_thread_id(workflow_id: str) -> str:
    return f"review_{workflow_id}"


def post_review_segment_id(run_id: str, review_id: str, revision: int) -> str:
    value = f"{run_id}\n{review_id}\n{revision}\npost_review"
    suffix = uuid.uuid5(uuid.NAMESPACE_URL, value).hex[:16]
    return f"{run_id}_seg_review_{suffix}"


def review_resolution_id(decision_id: str) -> str:
    return f"resolution_{uuid.uuid5(uuid.NAMESPACE_URL, decision_id).hex}"


def decision_request_hash(
    *,
    run_id: str,
    review_id: str,
    request: ReviewDecisionRequest,
) -> str:
    payload = {
        "run_id": run_id,
        "review_id": review_id,
        "decision_id": request.decision_id,
        "review_revision": request.review_revision,
        "action": request.action,
        "reason": request.reason,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
```

- [ ] **Step 4: Document the disabled default**

Add to `.env.example`:

```dotenv
# Experimental P1B path. Keep false until all durable HITL gates pass.
DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL=false
```

- [ ] **Step 5: Run GREEN**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_models.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add api/review_models.py tests/unit/test_review_models.py .env.example
git commit -m "feat(research): define durable review contracts"
```

---

### Task 3: Additive Review Schema, Verification, Backup, and Restore

**Files:**
- Create: `api/review_repository.py`
- Create: `tests/unit/test_review_migrations.py`
- Modify: `api/run_migrations.py`
- Modify: `scripts/run_identity_migration.py`

- [ ] **Step 1: Write RED migration tests**

```python
# tests/unit/test_review_migrations.py
import sqlite3

from api.persistence import init_db
from api.run_migrations import (
    backup_database,
    restore_database,
    verify_run_schema,
)
from api.review_repository import REVIEW_MIGRATION_VERSION, init_review_schema


REVIEW_TABLES = {
    "review_decisions_v2",
    "review_workflows_v2",
    "review_resume_attempts_v2",
    "review_resolutions_v2",
}


def _tables(path):
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


def test_review_migration_is_idempotent_and_verified(tmp_path):
    path = str(tmp_path / "tasks.db")
    init_db(path).close()
    init_review_schema(path)
    init_review_schema(path)
    result = verify_run_schema(db_path=path)
    assert REVIEW_TABLES <= _tables(path)
    assert REVIEW_MIGRATION_VERSION in result["migration_versions"]


def test_review_schema_backup_restore_removes_additive_tables(tmp_path):
    path = str(tmp_path / "tasks.db")
    backup = str(tmp_path / "tasks.pre-review.db")
    init_db(path).close()
    before = _tables(path)
    backup_database(db_path=path, backup_path=backup)
    init_review_schema(path)
    assert REVIEW_TABLES <= _tables(path)
    restore_database(backup_path=backup, db_path=path)
    assert _tables(path) == before
```

- [ ] **Step 2: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_migrations.py -q
```

Expected: FAIL because `api.review_repository` does not exist.

- [ ] **Step 3: Implement the additive schema**

Create `api/review_repository.py` with:

```python
from __future__ import annotations

from api.run_repository import _connect, init_run_schema, _now


REVIEW_MIGRATION_VERSION = "004_durable_review_feasibility"
REVIEW_MIGRATION_CHECKSUM = "durable-review-feasibility-v1"


def init_review_schema(db_path: str | None = None) -> None:
    init_run_schema(db_path)
    connection = _connect(db_path)
    try:
        with connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS review_decisions_v2 (
                    decision_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    review_id TEXT NOT NULL REFERENCES review_bundles_v2(review_id) ON DELETE CASCADE,
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
                    run_id TEXT NOT NULL UNIQUE REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    review_id TEXT NOT NULL REFERENCES review_bundles_v2(review_id) ON DELETE CASCADE,
                    review_revision INTEGER NOT NULL,
                    checkpoint_thread_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    decision_id TEXT REFERENCES review_decisions_v2(decision_id),
                    post_review_segment_id TEXT NOT NULL,
                    lease_owner TEXT,
                    lease_expires_at TEXT,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    last_error_code TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS review_resume_attempts_v2 (
                    workflow_id TEXT NOT NULL REFERENCES review_workflows_v2(workflow_id) ON DELETE CASCADE,
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
                    run_id TEXT NOT NULL UNIQUE REFERENCES research_runs_v2(run_id) ON DELETE CASCADE,
                    review_id TEXT NOT NULL REFERENCES review_bundles_v2(review_id) ON DELETE CASCADE,
                    decision_id TEXT NOT NULL UNIQUE REFERENCES review_decisions_v2(decision_id),
                    action TEXT NOT NULL,
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
                (REVIEW_MIGRATION_VERSION, _now(), REVIEW_MIGRATION_CHECKSUM),
            )
    finally:
        connection.close()
```

- [ ] **Step 4: Extend schema verification**

Update `api/run_migrations.py`:

```python
REQUIRED_TABLES |= {
    "review_decisions_v2",
    "review_workflows_v2",
    "review_resume_attempts_v2",
    "review_resolutions_v2",
}
REQUIRED_INDEXES |= {
    "idx_review_workflows_status_lease",
    "idx_review_decisions_run",
}


def verify_run_schema(*, db_path: str) -> dict:
    # Keep the existing table/index/foreign-key checks.
    migration_rows = conn.execute(
        "SELECT version, checksum FROM schema_migrations"
    ).fetchall()
    migrations = {row[0]: row[1] for row in migration_rows}
    expected = {
        MIGRATION_VERSION: "run-identity-backbone-v1",
        REVIEW_MIGRATION_VERSION: REVIEW_MIGRATION_CHECKSUM,
    }
    if any(migrations.get(version) != checksum for version, checksum in expected.items()):
        raise RuntimeError("run_schema_verification_failed:migration_checksum")
    return {
        "migration_versions": sorted(expected),
        "tables": sorted(REQUIRED_TABLES),
        "indexes": sorted(REQUIRED_INDEXES),
    }
```

Import `REVIEW_MIGRATION_VERSION`, `REVIEW_MIGRATION_CHECKSUM`, and
`init_review_schema`, and have `migrate_with_backup()` call
`init_review_schema(db_path)` instead of only `init_run_schema(db_path)`.

- [ ] **Step 5: Run GREEN and existing migration regression**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_migrations.py \
  tests/unit/test_run_migrations.py \
  tests/unit/test_run_repository.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add api/review_repository.py api/run_migrations.py \
  scripts/run_identity_migration.py tests/unit/test_review_migrations.py
git commit -m "feat(research): add durable review persistence schema"
```

---

### Task 4: Atomic Workflow Seed, Decision Idempotency, and Conflict Fencing

**Files:**
- Modify: `api/review_repository.py`
- Modify: `api/run_repository.py`
- Create: `tests/unit/test_review_repository.py`
- Modify: `tests/unit/test_run_repository.py`

- [ ] **Step 1: Write RED repository tests**

```python
# tests/unit/test_review_repository.py
import pytest

from api.review_models import ReviewDecisionRequest
from api.review_repository import (
    ReviewConflict,
    accept_review_decision,
    get_review_projection,
)


def test_same_decision_request_is_idempotent(required_review_run):
    request = ReviewDecisionRequest(
        decision_id="decision_001",
        review_revision=1,
        action="approve",
        expected_state_version=2,
    )
    first = accept_review_decision(
        db_path=required_review_run.db_path,
        run_id=required_review_run.run_id,
        review_id=required_review_run.review_id,
        request=request,
        actor_fingerprint="actor_hash",
    )
    second = accept_review_decision(
        db_path=required_review_run.db_path,
        run_id=required_review_run.run_id,
        review_id=required_review_run.review_id,
        request=request,
        actor_fingerprint="actor_hash",
    )
    assert first.decision == second.decision
    assert first.idempotent_replay is False
    assert second.idempotent_replay is True
    assert get_review_projection(
        db_path=required_review_run.db_path,
        run_id=required_review_run.run_id,
    )["workflow"]["status"] == "resume_pending"


def test_reused_decision_id_with_different_action_conflicts(required_review_run):
    approve = ReviewDecisionRequest(
        decision_id="decision_001",
        review_revision=1,
        action="approve",
        expected_state_version=2,
    )
    reject = approve.model_copy(update={"action": "reject", "reason": "Not accepted"})
    accept_review_decision(
        db_path=required_review_run.db_path,
        run_id=required_review_run.run_id,
        review_id=required_review_run.review_id,
        request=approve,
        actor_fingerprint="actor_hash",
    )
    with pytest.raises(ReviewConflict, match="decision_id_conflict"):
        accept_review_decision(
            db_path=required_review_run.db_path,
            run_id=required_review_run.run_id,
            review_id=required_review_run.review_id,
            request=reject,
            actor_fingerprint="actor_hash",
        )


def test_different_decision_for_same_review_conflicts(required_review_run):
    first = ReviewDecisionRequest(
        decision_id="decision_001",
        review_revision=1,
        action="approve",
        expected_state_version=2,
    )
    second = ReviewDecisionRequest(
        decision_id="decision_002",
        review_revision=1,
        action="reject",
        reason="Rejected",
        expected_state_version=2,
    )
    accept_review_decision(
        db_path=required_review_run.db_path,
        run_id=required_review_run.run_id,
        review_id=required_review_run.review_id,
        request=first,
        actor_fingerprint="actor_hash",
    )
    with pytest.raises(ReviewConflict, match="review_already_decided"):
        accept_review_decision(
            db_path=required_review_run.db_path,
            run_id=required_review_run.run_id,
            review_id=required_review_run.review_id,
            request=second,
            actor_fingerprint="actor_hash",
        )
```

The `required_review_run` fixture must create a Talent run, transition it to
running, persist a required bundle, seed the workflow in the same finalization
transaction, and assert run `state_version == 2`.

- [ ] **Step 2: Add workflow-seed assertions to run finalization**

```python
def test_required_review_finalization_seeds_workflow_atomically(
    required_review_run_factory,
):
    fixture = required_review_run_factory(seed_workflow=False)
    workflow_id = review_workflow_id(
        fixture.run_id,
        fixture.review.review_id,
        fixture.review.revision,
    )
    assert finalize_run_transaction(
        **fixture.finalization_kwargs,
        review_bundle=fixture.review,
        review_workflow={
            "workflow_id": workflow_id,
            "checkpoint_thread_id": checkpoint_thread_id(workflow_id),
            "post_review_segment_id": post_review_segment_id(
                fixture.run_id,
                fixture.review.review_id,
                fixture.review.revision,
            ),
        },
    )
    run = get_run(db_path=fixture.db_path, run_id=fixture.run_id)
    assert run["state_version"] == 2
    assert run["review_workflow"]["status"] == "checkpoint_pending"
```

`required_review_run_factory(seed_workflow=False)` must return a frozen fixture
with `db_path`, `run_id`, `review`, and `finalization_kwargs`. The kwargs contain
the existing run/segment/version/status/evidence/packet/artifact arguments but do
not include `review_bundle` or `review_workflow`.

- [ ] **Step 3: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_repository.py \
  tests/unit/test_run_repository.py -q
```

Expected: FAIL because workflow seeding and decision functions do not exist.

- [ ] **Step 4: Implement workflow seed in the existing finalization transaction**

Add this parameter after the existing `artifacts` parameter:

```python
review_workflow: dict[str, str] | None = None,
```

Insert this block after `review_bundle` is persisted and before artifacts are
inserted:

```python
if review_workflow is not None:
    if review_bundle is None or not review_bundle.required_before_delivery:
        raise ValueError("review_workflow requires a required review_bundle")
    conn.execute(
        """
        INSERT INTO review_workflows_v2 (
            workflow_id, run_id, review_id, review_revision,
            checkpoint_thread_id, status, post_review_segment_id,
            attempt_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'checkpoint_pending', ?, 0, ?, ?)
        """,
        (
            review_workflow["workflow_id"],
            run_id,
            review_bundle.review_id,
            review_bundle.revision,
            review_workflow["checkpoint_thread_id"],
            review_workflow["post_review_segment_id"],
            now,
            now,
        ),
    )
```

Call `init_review_schema()` before this transaction.

- [ ] **Step 5: Implement decision acceptance**

In `api/review_repository.py`, define:

```python
@dataclass(frozen=True)
class DecisionAcceptance:
    decision: ReviewDecisionRecord
    workflow_status: str
    idempotent_replay: bool


class ReviewConflict(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def accept_review_decision(
    *,
    run_id: str,
    review_id: str,
    request: ReviewDecisionRequest,
    actor_fingerprint: str,
    db_path: str | None = None,
) -> DecisionAcceptance:
    init_review_schema(db_path)
    request_hash = decision_request_hash(
        run_id=run_id,
        review_id=review_id,
        request=request,
    )
    connection = _connect(db_path)
    try:
        with connection:
            existing = connection.execute(
                "SELECT * FROM review_decisions_v2 WHERE decision_id = ?",
                (request.decision_id,),
            ).fetchone()
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise ReviewConflict("decision_id_conflict")
                return _decision_acceptance(existing, idempotent_replay=True)

            run = connection.execute(
                """
                SELECT execution_status, review_status, delivery_status, state_version,
                       profile_id
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
                    decision_id, run_id, review_id, review_revision, action, reason,
                    actor_fingerprint, request_hash, accepted_state_version, created_at
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
            connection.execute(
                """
                UPDATE review_workflows_v2
                SET decision_id = ?, status = 'resume_pending', updated_at = ?
                WHERE workflow_id = ? AND status = 'waiting_decision'
                """,
                (request.decision_id, now, workflow["workflow_id"]),
            )
            cursor = connection.execute(
                """
                UPDATE research_runs_v2
                SET state_version = state_version + 1, updated_at = ?
                WHERE run_id = ? AND state_version = ?
                """,
                (now, run_id, request.expected_state_version),
            )
            if cursor.rowcount != 1:
                raise ReviewConflict("stale_state_version")
            row = connection.execute(
                "SELECT * FROM review_decisions_v2 WHERE decision_id = ?",
                (request.decision_id,),
            ).fetchone()
            return _decision_acceptance(row, idempotent_replay=False)
    finally:
        connection.close()
```

Catch SQLite uniqueness errors and map same-review conflicts to
`ReviewConflict("review_already_decided")`.

- [ ] **Step 6: Add sanitized projections to `get_run()`**

Return:

```python
result["review_workflow"] = sanitized_workflow_or_none
result["review_decision"] = sanitized_decision_or_none
result["review_resolution"] = sanitized_resolution_or_none
```

Expose `reason_recorded` instead of decision reason text. Exclude
`actor_fingerprint`, `lease_owner`, checkpoint path, and raw error text.

- [ ] **Step 7: Run GREEN**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_repository.py \
  tests/unit/test_run_repository.py \
  tests/integration/test_run_api.py -q
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add api/review_repository.py api/run_repository.py \
  tests/unit/test_review_repository.py tests/unit/test_run_repository.py
git commit -m "feat(research): persist idempotent review decisions"
```

---

### Task 5: Deterministic Reviewed DecisionBrief Artifacts and Fenced Resolution

**Files:**
- Create: `api/review_artifacts.py`
- Modify: `api/review_repository.py`
- Modify: `api/run_repository.py`
- Create: `tests/unit/test_review_artifacts.py`
- Modify: `tests/unit/test_review_repository.py`

- [ ] **Step 1: Write RED artifact tests**

```python
# tests/unit/test_review_artifacts.py
from api.review_artifacts import build_reviewed_artifacts


def test_approval_builds_deterministic_reviewed_artifacts_without_verifying_evidence(
    required_review_run,
):
    first = build_reviewed_artifacts(
        original_brief_json=required_review_run.brief_json,
        decision=required_review_run.approve_decision,
    )
    second = build_reviewed_artifacts(
        original_brief_json=required_review_run.brief_json,
        decision=required_review_run.approve_decision,
    )
    assert first == second
    reviewed = first.brief
    assert reviewed.review_summary["status"] == "resolved"
    assert reviewed.review_summary["decision"]["action"] == "approve"
    assert reviewed.review_summary["decision"]["reviewer_kind"] == "service_credential"
    assert reviewed.review_summary["decision"]["reason_recorded"] is False
    assert "reason" not in reviewed.review_summary["decision"]
    assert all(
        item["verification_status"] == "unverified"
        for item in reviewed.evidence_summary
    )
    assert {item["artifact_id"] for item in first.artifacts} == {
        "decision-brief.reviewed.json",
        "decision-brief.reviewed.md",
    }


def test_rejection_creates_no_reviewed_delivery_artifacts(required_review_run):
    result = build_reviewed_artifacts(
        original_brief_json=required_review_run.brief_json,
        decision=required_review_run.reject_decision,
    )
    assert result.artifacts == []
```

- [ ] **Step 2: Write RED fenced-resolution tests**

```python
def test_approval_resolution_is_exactly_once(required_review_run):
    resolution = resolve_review(
        db_path=required_review_run.db_path,
        workflow_id=required_review_run.workflow_id,
        worker_id="worker_a",
        expected_run_state_version=3,
        result=required_review_run.approved_artifacts,
    )
    replay = resolve_review(
        db_path=required_review_run.db_path,
        workflow_id=required_review_run.workflow_id,
        worker_id="worker_a",
        expected_run_state_version=3,
        result=required_review_run.approved_artifacts,
    )
    assert replay == resolution
    run = get_run(db_path=required_review_run.db_path, run_id=required_review_run.run_id)
    assert run["review_status"] == "resolved"
    assert run["delivery_status"] == "ready"
    assert run["state_version"] == 4
    assert [item["artifact_id"] for item in run["artifacts"]].count(
        "decision-brief.reviewed.json"
    ) == 1


def test_stale_worker_cannot_resolve_after_another_worker(required_review_run):
    with pytest.raises(ReviewConflict, match="lease_not_owned"):
        resolve_review(
            db_path=required_review_run.db_path,
            workflow_id=required_review_run.workflow_id,
            worker_id="stale_worker",
            expected_run_state_version=3,
            result=required_review_run.approved_artifacts,
        )
```

- [ ] **Step 3: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_artifacts.py \
  tests/unit/test_review_repository.py -q
```

Expected: FAIL because artifact and resolution functions do not exist.

- [ ] **Step 4: Implement deterministic reviewed artifacts**

```python
# api/review_artifacts.py
from dataclasses import dataclass
import json

from agent.talent_contracts import DecisionBrief
from api.decision_brief import render_markdown, with_content_hash
from api.review_models import ReviewDecisionRecord


@dataclass(frozen=True)
class ReviewedArtifactResult:
    brief: DecisionBrief | None
    resolved_review: dict
    artifacts: list[dict]


def build_reviewed_artifacts(
    *,
    original_brief_json: str,
    decision: ReviewDecisionRecord,
) -> ReviewedArtifactResult:
    original = DecisionBrief.model_validate_json(original_brief_json)
    resolved_review = {
        **original.review_summary,
        "status": "resolved",
        "required_before_delivery": False,
        "decision": {
            "decision_id": decision.decision_id,
            "action": decision.action,
            "reason_recorded": decision.reason is not None,
            "reviewer_kind": "service_credential",
            "created_at": decision.created_at.isoformat(),
        },
    }
    if decision.action == "reject":
        return ReviewedArtifactResult(
            brief=None,
            resolved_review=resolved_review,
            artifacts=[],
        )

    brief = with_content_hash(
        original.model_copy(update={"review_summary": resolved_review})
    )
    artifacts = [
        {
            "artifact_id": "decision-brief.reviewed.json",
            "kind": "decision_brief_reviewed_json",
            "media_type": "application/json",
            "content": json.dumps(
                brief.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            "content_hash": brief.content_hash,
        },
        {
            "artifact_id": "decision-brief.reviewed.md",
            "kind": "decision_brief_reviewed_markdown",
            "media_type": "text/markdown",
            "content": render_markdown(brief),
            "content_hash": brief.content_hash,
        },
    ]
    return ReviewedArtifactResult(
        brief=brief,
        resolved_review=resolved_review,
        artifacts=artifacts,
    )
```

- [ ] **Step 5: Implement fenced resolution**

`resolve_review()` must:

1. return the existing resolution on exact replay;
2. require workflow `status='resuming'` and matching unexpired `lease_owner`;
3. require the decision's `accepted_state_version`;
4. insert resolution and approval artifacts in one application transaction;
5. update run to `review_status='resolved'`;
6. set delivery `ready` for approve or `blocked` for reject;
7. increment run version once;
8. update workflow to `approved` or `rejected`, clear lease;
9. complete the current attempt;
10. reject stale workers.

Add `"blocked"` to `DELIVERY_STATUSES`.

- [ ] **Step 6: Run GREEN**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_artifacts.py \
  tests/unit/test_review_repository.py \
  tests/unit/test_decision_brief.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add api/review_artifacts.py api/review_repository.py api/run_repository.py \
  tests/unit/test_review_artifacts.py tests/unit/test_review_repository.py
git commit -m "feat(research): resolve reviewed decision briefs"
```

---

### Task 6: Persistent Pure Review-Gate Graph

**Files:**
- Create: `api/review_gate.py`
- Create: `tests/unit/test_review_gate.py`
- Modify: `tests/integration/test_review_checkpoint_compatibility.py`

- [ ] **Step 1: Write RED graph tests**

```python
# tests/unit/test_review_gate.py
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
```

- [ ] **Step 2: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_gate.py -q
```

Expected: FAIL because `api.review_gate` does not exist.

- [ ] **Step 3: Implement the pure graph and checkpoint adapter**

```python
# api/review_gate.py
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable, Literal, NotRequired, TypedDict

from api.review_models import ReviewDecisionRecord
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ReviewGateState(TypedDict):
    workflow_id: str
    run_id: str
    review_id: str
    review_revision: int
    decision_id: NotRequired[str]
    action: NotRequired[str]


@dataclass(frozen=True)
class CheckpointInspection:
    status: Literal["absent", "interrupted", "completed"]
    decision_id: str | None
    action: str | None


class ReviewGateMismatch(RuntimeError):
    pass


class ReviewGate:
    def __init__(
        self,
        checkpoint_path: str,
        decision_loader: Callable[[str], ReviewDecisionRecord | None],
    ):
        self._checkpoint_path = checkpoint_path
        self._decision_loader = decision_loader

    def _compile(self):
        connection = sqlite3.connect(
            self._checkpoint_path,
            check_same_thread=False,
            timeout=5,
        )
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        saver = SqliteSaver(connection)
        saver.setup()

        def wait_for_decision(state: ReviewGateState):
            decision_id = interrupt(
                {
                    "workflow_id": state["workflow_id"],
                    "run_id": state["run_id"],
                    "review_id": state["review_id"],
                    "review_revision": state["review_revision"],
                    "allowed_actions": ["approve", "reject"],
                }
            )
            decision = self._decision_loader(decision_id)
            expected = (
                state["run_id"],
                state["review_id"],
                state["review_revision"],
            )
            actual = (
                decision.run_id if decision else None,
                decision.review_id if decision else None,
                decision.review_revision if decision else None,
            )
            if actual != expected:
                raise ReviewGateMismatch("checkpoint_decision_mismatch")
            return {
                "decision_id": decision_id,
                "action": decision.action,
            }

        builder = StateGraph(ReviewGateState)
        builder.add_node("wait_for_decision", wait_for_decision)
        builder.add_edge(START, "wait_for_decision")
        builder.add_edge("wait_for_decision", END)
        return builder.compile(checkpointer=saver), connection

    def ensure_waiting(
        self,
        *,
        workflow_id: str,
        checkpoint_thread_id: str,
        run_id: str,
        review_id: str,
        review_revision: int,
    ) -> dict:
        graph, connection = self._compile()
        try:
            result = graph.invoke(
                {
                    "workflow_id": workflow_id,
                    "run_id": run_id,
                    "review_id": review_id,
                    "review_revision": review_revision,
                },
                config={
                    "configurable": {
                        "thread_id": checkpoint_thread_id,
                    }
                },
                durability="sync",
            )
            return result["__interrupt__"][0].value
        finally:
            connection.close()

    def resume(self, *, checkpoint_thread_id: str, decision_id: str) -> dict:
        graph, connection = self._compile()
        try:
            return graph.invoke(
                Command(resume=decision_id),
                config={"configurable": {"thread_id": checkpoint_thread_id}},
                durability="sync",
            )
        finally:
            connection.close()

    def inspect(self, checkpoint_thread_id: str) -> CheckpointInspection:
        graph, connection = self._compile()
        try:
            snapshot = graph.get_state(
                {"configurable": {"thread_id": checkpoint_thread_id}}
            )
            values = dict(snapshot.values or {})
            if snapshot.next:
                return CheckpointInspection(
                    status="interrupted",
                    decision_id=values.get("decision_id"),
                    action=values.get("action"),
                )
            if values.get("decision_id"):
                return CheckpointInspection(
                    status="completed",
                    decision_id=values["decision_id"],
                    action=values.get("action"),
                )
            return CheckpointInspection(
                status="absent",
                decision_id=None,
                action=None,
            )
        finally:
            connection.close()
```

- [ ] **Step 4: Run GREEN**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_gate.py \
  tests/integration/test_review_checkpoint_compatibility.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add api/review_gate.py tests/unit/test_review_gate.py \
  tests/integration/test_review_checkpoint_compatibility.py
git commit -m "feat(research): add persistent review gate graph"
```

---

### Task 7: Lease, Reclaim, Worker, and Reconciliation

**Files:**
- Modify: `api/review_repository.py`
- Create: `api/review_worker.py`
- Create: `tests/unit/test_review_worker.py`
- Modify: `tests/unit/test_review_repository.py`

- [ ] **Step 1: Write RED lease tests**

```python
def test_expired_lease_is_reclaimed_without_new_segment(required_review_run, clock):
    first = claim_review_workflow(
        db_path=required_review_run.db_path,
        worker_id="worker_a",
        lease_seconds=10,
        now=clock.now(),
    )
    clock.advance(seconds=11)
    second = claim_review_workflow(
        db_path=required_review_run.db_path,
        worker_id="worker_b",
        lease_seconds=10,
        now=clock.now(),
    )
    assert second.workflow_id == first.workflow_id
    assert second.post_review_segment_id == first.post_review_segment_id
    assert second.attempt == first.attempt + 1


def test_stale_worker_cannot_complete_reclaimed_attempt(required_review_run, clock):
    first = claim_review_workflow(
        db_path=required_review_run.db_path,
        worker_id="worker_a",
        lease_seconds=10,
        now=clock.now(),
    )
    clock.advance(seconds=11)
    second = claim_review_workflow(
        db_path=required_review_run.db_path,
        worker_id="worker_b",
        lease_seconds=10,
        now=clock.now(),
    )
    assert second.attempt == first.attempt + 1
    with pytest.raises(ReviewConflict, match="lease_not_owned"):
        complete_checkpoint_creation(
            db_path=required_review_run.db_path,
            workflow_id=first.workflow_id,
            worker_id="worker_a",
        )
```

Import `pytest`, `complete_checkpoint_creation`, and `ReviewConflict`.

- [ ] **Step 2: Write RED worker tests**

```python
# tests/unit/test_review_worker.py
import pytest

from api.review_worker import ReviewWorker


@pytest.mark.asyncio
async def test_worker_creates_missing_checkpoint_and_marks_waiting(
    checkpoint_pending_run,
):
    worker = ReviewWorker(
        db_path=checkpoint_pending_run.db_path,
        checkpoint_path=checkpoint_pending_run.checkpoint_path,
        worker_id="worker_a",
    )
    assert await worker.run_once() is True
    projection = checkpoint_pending_run.projection()
    assert projection["workflow"]["status"] == "waiting_decision"


@pytest.mark.asyncio
async def test_worker_resumes_decision_and_resolves_approval(resume_pending_run):
    worker = ReviewWorker(
        db_path=resume_pending_run.db_path,
        checkpoint_path=resume_pending_run.checkpoint_path,
        worker_id="worker_a",
    )
    assert await worker.run_once() is True
    run = resume_pending_run.get_run()
    assert run["review_status"] == "resolved"
    assert run["delivery_status"] == "ready"


@pytest.mark.asyncio
async def test_worker_marks_manual_recovery_on_mismatched_checkpoint(
    mismatched_checkpoint_run,
):
    worker = ReviewWorker(
        db_path=mismatched_checkpoint_run.db_path,
        checkpoint_path=mismatched_checkpoint_run.checkpoint_path,
        worker_id="worker_a",
    )
    assert await worker.run_once() is True
    projection = mismatched_checkpoint_run.projection()
    assert projection["workflow"]["status"] == "manual_recovery"
    assert projection["workflow"]["last_error_code"] == (
        "checkpoint_decision_mismatch"
    )
```

- [ ] **Step 3: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_repository.py \
  tests/unit/test_review_worker.py -q
```

Expected: FAIL because lease and worker functions do not exist.

- [ ] **Step 4: Implement conditional lease claims**

`claim_review_workflow()` must use one `BEGIN IMMEDIATE` transaction and:

```sql
SELECT *
FROM review_workflows_v2
WHERE status IN (
    'checkpoint_pending',
    'resume_pending',
    'resuming',
    'resolution_pending'
)
  AND (
    lease_owner IS NULL
    OR lease_expires_at IS NULL
    OR lease_expires_at <= :now
  )
ORDER BY created_at, workflow_id
LIMIT 1;
```

Then update the selected row only if its current status and prior lease fields still
match. Set `status='resuming'` only for `resume_pending`/expired `resuming`; keep
`checkpoint_pending` unchanged while creating its initial interrupt and keep
`resolution_pending` unchanged while applying an already completed graph result.
Increment `attempt_count`, write the deterministic segment with:

```sql
INSERT OR IGNORE INTO run_segments (
    segment_id, run_id, kind, sequence, attempt, status, created_at, updated_at
) VALUES (?, ?, 'post_review', 1, 1, 'pending', ?, ?);
```

Append one `review_resume_attempts_v2` row per claim.

- [ ] **Step 5: Implement `ReviewWorker`**

```python
# api/review_worker.py
from __future__ import annotations

import asyncio
import logging
import uuid

from api.review_artifacts import build_reviewed_artifacts
from api.review_gate import ReviewGate, ReviewGateMismatch
from api.review_repository import (
    claim_review_workflow,
    complete_checkpoint_creation,
    get_decision,
    get_original_decision_brief,
    mark_manual_recovery,
    mark_resolution_pending,
    release_workflow_for_retry,
    resolve_review,
)


class ReviewWorker:
    def __init__(
        self,
        *,
        db_path: str | None,
        checkpoint_path: str,
        worker_id: str | None = None,
        lease_seconds: int = 30,
        poll_seconds: float = 1.0,
        stage_hook=None,
    ):
        self.db_path = db_path
        self.checkpoint_path = checkpoint_path
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex}"
        self.lease_seconds = lease_seconds
        self.poll_seconds = poll_seconds
        self.stage_hook = stage_hook or (lambda stage, workflow: None)
        self._stop = asyncio.Event()

    async def run_once(self) -> bool:
        claim = await asyncio.to_thread(
            claim_review_workflow,
            db_path=self.db_path,
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
        )
        if claim is None:
            return False
        if claim.original_status != "checkpoint_pending":
            self.stage_hook("lease_acquired", claim)
        gate = ReviewGate(
            self.checkpoint_path,
            lambda decision_id: get_decision(
                db_path=self.db_path,
                decision_id=decision_id,
            ),
        )
        try:
            if claim.original_status == "checkpoint_pending":
                await asyncio.to_thread(
                    gate.ensure_waiting,
                    workflow_id=claim.workflow_id,
                    checkpoint_thread_id=claim.checkpoint_thread_id,
                    run_id=claim.run_id,
                    review_id=claim.review_id,
                    review_revision=claim.review_revision,
                )
                self.stage_hook("checkpoint_interrupted", claim)
                await asyncio.to_thread(
                    complete_checkpoint_creation,
                    db_path=self.db_path,
                    workflow_id=claim.workflow_id,
                    worker_id=self.worker_id,
                )
                return True

            if claim.original_status != "resolution_pending":
                result = await asyncio.to_thread(
                    gate.resume,
                    checkpoint_thread_id=claim.checkpoint_thread_id,
                    decision_id=claim.decision_id,
                )
                self.stage_hook("graph_resumed", claim)
                await asyncio.to_thread(
                    mark_resolution_pending,
                    db_path=self.db_path,
                    workflow_id=claim.workflow_id,
                    worker_id=self.worker_id,
                    decision_id=result["decision_id"],
                )
            decision = await asyncio.to_thread(
                get_decision,
                db_path=self.db_path,
                decision_id=claim.decision_id,
            )
            artifacts = build_reviewed_artifacts(
                original_brief_json=await asyncio.to_thread(
                    get_original_decision_brief,
                    db_path=self.db_path,
                    run_id=claim.run_id,
                ),
                decision=decision,
            )
            await asyncio.to_thread(
                resolve_review,
                db_path=self.db_path,
                workflow_id=claim.workflow_id,
                worker_id=self.worker_id,
                expected_run_state_version=decision.accepted_state_version,
                result=artifacts,
            )
            return True
        except ReviewGateMismatch as exc:
            await asyncio.to_thread(
                mark_manual_recovery,
                db_path=self.db_path,
                workflow_id=claim.workflow_id,
                worker_id=self.worker_id,
                error_code=str(exc),
            )
            return True
        except Exception as exc:
            logging.exception("Durable review worker failed for %s", claim.workflow_id)
            await asyncio.to_thread(
                release_workflow_for_retry,
                db_path=self.db_path,
                workflow_id=claim.workflow_id,
                worker_id=self.worker_id,
                error_code=bounded_worker_error_code(exc),
                max_attempts=3,
            )
            return True

    async def run_forever(self) -> None:
        while not self._stop.is_set():
            if not await self.run_once():
                try:
                    await asyncio.wait_for(
                        self._stop.wait(),
                        timeout=self.poll_seconds,
                    )
                except asyncio.TimeoutError:
                    pass

    def stop(self) -> None:
        self._stop.set()
```

Use explicit bounded error codes; do not persist exception text.
Define `bounded_worker_error_code()` in `api/review_worker.py` as an allowlisted
exception-to-code mapper; unknown exceptions map to `review_worker_failed`.
`release_workflow_for_retry()` must return failed `resuming` work to
`resume_pending`, preserve `resolution_pending` as `resolution_pending`, and clear
the lease. It must never move a completed checkpoint back to `resume_pending`.
When `attempt_count >= max_attempts`, it must move the workflow to
`manual_recovery` with a stable bounded error code instead of creating an infinite
poison-work loop.

Add tests proving:

```python
@pytest.mark.asyncio
async def test_two_workers_do_not_resolve_the_same_workflow_twice(
    resume_pending_run,
):
    worker_a = resume_pending_run.worker(worker_id="worker_a")
    worker_b = resume_pending_run.worker(worker_id="worker_b")
    await asyncio.gather(worker_a.run_once(), worker_b.run_once())
    assert resume_pending_run.count_resolutions() == 1
    assert resume_pending_run.count_reviewed_json_artifacts() == 1


@pytest.mark.asyncio
async def test_permanent_failure_stops_after_three_attempts(
    permanently_failing_review_run,
):
    worker = permanently_failing_review_run.worker(worker_id="worker_a")
    for _ in range(3):
        await worker.run_once()
    projection = permanently_failing_review_run.projection()
    assert projection["workflow"]["status"] == "manual_recovery"
    assert projection["workflow"]["last_error_code"] == "checkpoint_unavailable"
```

- [ ] **Step 6: Run GREEN**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_repository.py \
  tests/unit/test_review_gate.py \
  tests/unit/test_review_worker.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add api/review_repository.py api/review_worker.py \
  tests/unit/test_review_repository.py tests/unit/test_review_worker.py
git commit -m "feat(research): recover durable reviews with leases"
```

---

### Task 8: Feature-Flagged Strict Review Decision API

**Files:**
- Create: `api/review_api.py`
- Create: `tests/integration/test_durable_review_api.py`
- Modify: `api/server.py`
- Modify: `tests/integration/test_run_api.py`

- [ ] **Step 1: Write RED disabled/auth tests**

```python
# tests/integration/test_durable_review_api.py
from fastapi.testclient import TestClient

from api.server import app


def _url(run_id, review_id):
    return f"/api/runs/{run_id}/reviews/{review_id}/decisions"


def test_decision_api_is_disabled_by_default(required_review_run, monkeypatch):
    monkeypatch.delenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        raising=False,
    )
    response = TestClient(app).post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=required_review_run.approve_request,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "durable_hitl_disabled"


def test_enabled_decision_api_fails_closed_without_api_secret(
    required_review_run,
    monkeypatch,
):
    monkeypatch.setenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        "true",
    )
    monkeypatch.delenv("API_SECRET", raising=False)
    response = TestClient(app).post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=required_review_run.approve_request,
    )
    assert response.status_code == 503
    assert response.json()["code"] == "review_auth_not_configured"


def test_wrong_key_is_rejected(required_review_run, monkeypatch):
    monkeypatch.setenv("DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL", "true")
    monkeypatch.setenv("API_SECRET", "correct")
    response = TestClient(app).post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=required_review_run.approve_request,
        headers={"X-API-Key": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_api_key"
```

- [ ] **Step 2: Write RED success/idempotency/conflict tests**

```python
def test_decision_api_accepts_and_replays_same_request(required_review_run, auth):
    client = TestClient(app)
    first = client.post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=required_review_run.approve_request,
        headers=auth,
    )
    second = client.post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=required_review_run.approve_request,
        headers=auth,
    )
    assert first.status_code == second.status_code == 202
    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True


def test_conflicting_decision_returns_actionable_409(required_review_run, auth):
    client = TestClient(app)
    first = client.post(
        _url(required_review_run.run_id, required_review_run.review_id),
        json=required_review_run.approve_request,
        headers=auth,
    )
    assert first.status_code == 202
    conflicting = {
        **required_review_run.approve_request,
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
    assert response.json() == {
        "code": "review_already_decided",
        "problem": "This review revision already has an accepted decision.",
        "cause": "A conflicting decision was submitted.",
        "fix": "Fetch the run and use the persisted decision result.",
        "retryable": False,
        "run_id": required_review_run.run_id,
        "request_id": response.json()["request_id"],
    }
```

- [ ] **Step 3: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_durable_review_api.py -q
```

Expected: FAIL because the route does not exist.

- [ ] **Step 4: Implement strict auth and router**

```python
# api/review_api.py
from __future__ import annotations

import hashlib
import hmac
import os
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.review_models import ReviewDecisionRequest, durable_hitl_enabled
from api.review_repository import ReviewConflict, accept_review_decision


router = APIRouter()


def _error(status: int, *, code: str, problem: str, cause: str, fix: str,
           retryable: bool, run_id: str | None = None) -> JSONResponse:
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


def _authenticate(request: Request):
    if not durable_hitl_enabled():
        return None, _error(
            404,
            code="durable_hitl_disabled",
            problem="Durable review decisions are disabled.",
            cause="The P1B feature flag is false.",
            fix="Use the existing non-interrupt review bundle.",
            retryable=False,
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
        )
    fingerprint = hashlib.sha256(
        f"decision-research-agent-review:{secret}".encode()
    ).hexdigest()
    return fingerprint, None


@router.post(
    "/api/runs/{run_id}/reviews/{review_id}/decisions",
    status_code=202,
    include_in_schema=True,
    deprecated=True,
)
async def submit_review_decision(
    run_id: str,
    review_id: str,
    body: ReviewDecisionRequest,
    request: Request,
):
    actor, error = _authenticate(request)
    if error is not None:
        return error
    try:
        result = await asyncio.to_thread(
            accept_review_decision,
            run_id=run_id,
            review_id=review_id,
            request=body,
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
```

Import `asyncio`. Map each stable conflict code to a fixed redacted envelope.

- [ ] **Step 5: Register only the router in `api/server.py`**

```python
from api.review_api import router as review_router

app.include_router(review_router)
```

- [ ] **Step 6: Run GREEN and auth regressions**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_durable_review_api.py \
  tests/unit/test_auth_middleware.py \
  tests/integration/test_run_api.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add api/review_api.py api/server.py \
  tests/integration/test_durable_review_api.py \
  tests/integration/test_run_api.py
git commit -m "feat(research): add disabled durable review API"
```

---

### Task 9: Seed Workflows from Talent Finalization and Manage Worker Lifecycle

**Files:**
- Modify: `api/server.py`
- Modify: `api/review_worker.py`
- Modify: `api/review_repository.py`
- Modify: `tests/integration/test_run_api.py`
- Create: `tests/integration/test_durable_review_lifecycle.py`

- [ ] **Step 1: Write RED disabled compatibility test**

```python
def test_talent_finalization_does_not_seed_workflow_when_flag_is_false(
    talent_result,
    monkeypatch,
):
    monkeypatch.setenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        "false",
    )
    run = finalize_talent_fixture(talent_result)
    assert run["review_status"] == "required"
    assert run["delivery_status"] == "review_required"
    assert run["review_workflow"] is None
```

- [ ] **Step 2: Write RED enabled workflow test**

```python
def test_talent_finalization_atomically_seeds_checkpoint_pending_workflow(
    talent_result,
    monkeypatch,
):
    monkeypatch.setenv(
        "DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL",
        "true",
    )
    run = finalize_talent_fixture(talent_result)
    assert run["state_version"] == 2
    assert run["review_workflow"]["status"] == "checkpoint_pending"
    assert run["review_workflow"]["review_id"] == run["review_bundle"]["review_id"]


def test_required_review_remains_not_deliverable_before_resolution(
    enabled_required_review_run,
):
    run = enabled_required_review_run.get_run()
    assert run["review_status"] == "required"
    assert run["delivery_status"] == "review_required"
    assert "decision-brief.reviewed.json" not in {
        item["artifact_id"] for item in run["artifacts"]
    }
```

- [ ] **Step 3: Write RED TestClient lifecycle test**

```python
def test_app_lifespan_starts_worker_only_when_enabled(monkeypatch):
    starts = []
    stops = []
    monkeypatch.setattr(server, "create_review_worker", lambda: FakeWorker(starts, stops))

    monkeypatch.setenv("DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL", "false")
    with TestClient(server.app):
        pass
    assert starts == []

    monkeypatch.setenv("DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL", "true")
    monkeypatch.setenv("API_SECRET", "configured")
    with TestClient(server.app):
        assert starts == ["started"]
    assert stops == ["stopped"]
```

- [ ] **Step 4: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_durable_review_lifecycle.py \
  tests/integration/test_run_api.py -q
```

Expected: FAIL because finalization does not seed workflows and no worker lifespan exists.

- [ ] **Step 5: Seed deterministic workflow data**

In `_run_v2_with_persistence()`:

```python
review_workflow = None
if (
    durable_hitl_enabled()
    and review_bundle is not None
    and review_bundle.required_before_delivery
):
    workflow_id = review_workflow_id(
        run_id,
        review_bundle.review_id,
        review_bundle.revision,
    )
    review_workflow = {
        "workflow_id": workflow_id,
        "checkpoint_thread_id": checkpoint_thread_id(workflow_id),
        "post_review_segment_id": post_review_segment_id(
            run_id,
            review_bundle.review_id,
            review_bundle.revision,
        ),
    }
```

Pass `review_workflow=review_workflow` into `finalize_run_transaction()`.

- [ ] **Step 6: Add bounded FastAPI lifespan**

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = None
    worker = None
    if durable_hitl_enabled():
        worker = create_review_worker()
        task = asyncio.create_task(worker.run_forever())
    try:
        yield
    finally:
        if worker is not None:
            worker.stop()
        if task is not None:
            await task


app = FastAPI(
    title="Decision Research Agent API",
    description="Source-backed research runs that produce decision-ready briefs.",
    lifespan=lifespan,
)
```

`create_review_worker()` resolves:

```python
checkpoint_path = os.getenv(
    "DECISION_RESEARCH_AGENT_CHECKPOINT_DB_PATH",
    str(project_root / "data" / "review_checkpoints.db"),
)
```

If HITL is enabled while `API_SECRET` is empty, startup must log a stable error and
not start the worker. The write route remains fail-closed.

- [ ] **Step 7: Run GREEN**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_durable_review_lifecycle.py \
  tests/integration/test_run_api.py \
  tests/unit/test_review_worker.py -q
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add api/server.py api/review_worker.py api/review_repository.py \
  tests/integration/test_durable_review_lifecycle.py \
  tests/integration/test_run_api.py
git commit -m "feat(research): start durable review workflows"
```

---

### Task 10: Process Restart, Corruption, and Forced-Crash Recovery Matrix

**Files:**
- Create: `scripts/durable_hitl_crash_worker.py`
- Create: `scripts/durable_hitl_fixture.py`
- Create: `tests/integration/test_durable_review_restart.py`
- Create: `tests/integration/test_durable_review_kill9.py`
- Modify: `api/review_worker.py`
- Modify: `api/review_repository.py`

- [ ] **Step 1: Write RED process-restart tests**

```python
# tests/integration/test_durable_review_restart.py
def test_restart_recovers_checkpoint_pending(tmp_path):
    fixture = seed_checkpoint_pending(tmp_path)
    run_worker_subprocess(fixture)
    assert load_projection(fixture)["workflow"]["status"] == "waiting_decision"


def test_restart_recovers_decision_committed_before_resume(tmp_path):
    fixture = seed_resume_pending(tmp_path, action="approve")
    run_worker_subprocess(fixture)
    run = load_run(fixture)
    assert run["delivery_status"] == "ready"
    assert run["review_resolution"]["action"] == "approve"


def test_corrupt_checkpoint_after_resume_attempt_is_manual_recovery(tmp_path):
    fixture = seed_resuming_with_corrupt_checkpoint(tmp_path)
    run_worker_subprocess(fixture)
    projection = load_projection(fixture)
    assert projection["workflow"]["status"] == "manual_recovery"
    assert projection["workflow"]["last_error_code"] == "checkpoint_corrupt"
```

- [ ] **Step 2: Write RED parameterized `SIGKILL` test**

```python
# tests/integration/test_durable_review_kill9.py
import os
import signal
import subprocess
import sys

import pytest


CRASH_STAGES = [
    "application_finalized",
    "checkpoint_interrupted",
    "decision_committed",
    "lease_acquired",
    "graph_resumed",
]

EXPECTED_OUTCOMES = {
    "application_finalized": {
        "workflow_status": "waiting_decision",
        "decision_count": 0,
        "resolution_count": 0,
        "reviewed_artifact_count": 0,
    },
    "checkpoint_interrupted": {
        "workflow_status": "waiting_decision",
        "decision_count": 0,
        "resolution_count": 0,
        "reviewed_artifact_count": 0,
    },
    "decision_committed": {
        "workflow_status": "approved",
        "decision_count": 1,
        "resolution_count": 1,
        "reviewed_artifact_count": 1,
    },
    "lease_acquired": {
        "workflow_status": "approved",
        "decision_count": 1,
        "resolution_count": 1,
        "reviewed_artifact_count": 1,
    },
    "graph_resumed": {
        "workflow_status": "approved",
        "decision_count": 1,
        "resolution_count": 1,
        "reviewed_artifact_count": 1,
    },
}


@pytest.mark.parametrize("stage", CRASH_STAGES)
def test_sigkill_window_converges_without_duplicate_state(tmp_path, stage):
    marker = tmp_path / f"{stage}.marker"
    command = [
        sys.executable,
        "scripts/durable_hitl_crash_worker.py",
        "--stage",
        stage,
        "--marker",
        str(marker),
        "--root",
        str(tmp_path),
    ]
    process = subprocess.Popen(command)
    wait_for_marker(marker, timeout=10)
    os.kill(process.pid, signal.SIGKILL)
    process.wait(timeout=10)

    run_recovery_worker(tmp_path)
    assert_converged_exactly_once(
        tmp_path,
        expected=EXPECTED_OUTCOMES[stage],
    )
```

`assert_converged_exactly_once()` must assert:

```python
assert count_post_review_segments(tmp_path) == 1
assert count_decisions(tmp_path) == expected["decision_count"]
assert count_resolutions(tmp_path) == expected["resolution_count"]
assert count_reviewed_json_artifacts(tmp_path) == expected["reviewed_artifact_count"]
assert workflow_status(tmp_path) == expected["workflow_status"]
```

`manual_recovery` is not an acceptable generic success result for these five
known crash windows. It is reserved for genuinely irreconcilable or corrupt state,
which has its own explicit gate.

- [ ] **Step 3: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_durable_review_restart.py \
  tests/integration/test_durable_review_kill9.py -q
```

Expected: FAIL because the subprocess harness and reconciliation behavior do not exist.

- [ ] **Step 4: Implement a test-injected stage hook**

Production worker already accepts `stage_hook`. Invoke it at:

```text
application_finalized
checkpoint_interrupted
decision_committed
lease_acquired
graph_resumed
```

The default is a no-op. Do not add production environment failpoints.

- [ ] **Step 5: Implement crash worker**

```python
# scripts/durable_hitl_crash_worker.py
from __future__ import annotations

import argparse
from pathlib import Path
import time

from api.review_worker import ReviewWorker
from scripts.durable_hitl_fixture import run_stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    def stage_hook(stage, workflow):
        if stage == args.stage:
            Path(args.marker).write_text(workflow.workflow_id, encoding="utf-8")
            while True:
                time.sleep(1)

    run_stage(Path(args.root), args.stage, stage_hook)


if __name__ == "__main__":
    main()
```

Create `scripts/durable_hitl_fixture.py` as shared deterministic fixture code. It
exports `create_required_review_fixture()` and `run_stage()` and contains no
pytest imports. Both crash and container scripts use it, so the backend image does
not need to copy the test tree.

Use this fixture contract:

```python
# scripts/durable_hitl_fixture.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent.talent_contracts import ResearchPacket
from api.review_models import (
    ReviewDecisionRequest,
    checkpoint_thread_id,
    post_review_segment_id,
    review_workflow_id,
)
from api.review_repository import accept_review_decision
from api.review_worker import ReviewWorker
from api.run_repository import (
    create_run,
    finalize_run_transaction,
    get_run,
    transition_run,
)
from api.talent_artifacts import build_talent_artifacts


@dataclass(frozen=True)
class DurableReviewFixture:
    db_path: str
    checkpoint_path: str
    run_id: str
    review_id: str
    workflow_id: str
    approve_request: ReviewDecisionRequest
    worker: ReviewWorker

    def get_run(self):
        return get_run(db_path=self.db_path, run_id=self.run_id)


def create_required_review_fixture(
    *,
    db_path: str,
    checkpoint_path: str,
    stage_hook=None,
) -> DurableReviewFixture:
    scope = {
        "target_roles": ["AI Agent Engineer"],
        "target_companies": [],
        "time_window": {"start": "2026-01-01", "end": "2026-06-19"},
        "declared_samples": [],
        "allowed_source_types": ["public_job_posting"],
        "research_questions": ["question-1"],
        "requested_outputs": ["decision_brief"],
    }
    created = create_run(
        db_path=db_path,
        thread_id="durable-review-fixture",
        query="fixture query",
        profile_id="talent-hiring-signal",
        scope=scope,
    )
    assert transition_run(
        db_path=db_path,
        run_id=created["run_id"],
        expected_state_version=0,
        allowed_previous_statuses={"pending"},
        execution_status="running",
    )
    packet = ResearchPacket.model_validate(
        {
            "packet_id": "packet-fixture",
            "scope_id": "scope-fixture",
            "findings": [
                {
                    "finding_id": "finding-1",
                    "research_question_id": "question-1",
                    "statement": "Fixture signal",
                    "evidence_refs": ["ev_missing"],
                    "sample_scope": "declared fixture",
                    "confidence": 0.8,
                }
            ],
            "candidate_claims": [
                {
                    "claim_id": "claim-1",
                    "text": "Fixture claim",
                    "claim_type": "signal",
                    "finding_refs": ["finding-1"],
                    "evidence_refs": ["ev_missing"],
                    "confidence": 0.8,
                    "citation_status": "cited",
                    "verification_status": "unverified",
                    "review_status": "required",
                    "conflict_status": "none",
                }
            ],
        }
    )
    review, _, artifacts = build_talent_artifacts(
        run_id=created["run_id"],
        scope=scope,
        packets=[packet],
        evidence_entries=[],
        generated_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )
    workflow_id = review_workflow_id(
        created["run_id"],
        review.review_id,
        review.revision,
    )
    assert finalize_run_transaction(
        db_path=db_path,
        run_id=created["run_id"],
        segment_id=created["segment_id"],
        expected_state_version=1,
        allowed_previous_statuses={"running"},
        execution_status="completed",
        review_status="required",
        delivery_status="review_required",
        evidence_entries=[],
        research_packets=[packet],
        review_bundle=review,
        artifacts=artifacts,
        review_workflow={
            "workflow_id": workflow_id,
            "checkpoint_thread_id": checkpoint_thread_id(workflow_id),
            "post_review_segment_id": post_review_segment_id(
                created["run_id"],
                review.review_id,
                review.revision,
            ),
        },
    )
    request = ReviewDecisionRequest(
        decision_id="decision_fixture_001",
        review_revision=review.revision,
        action="approve",
        expected_state_version=2,
    )
    return DurableReviewFixture(
        db_path=db_path,
        checkpoint_path=checkpoint_path,
        run_id=created["run_id"],
        review_id=review.review_id,
        workflow_id=workflow_id,
        approve_request=request,
        worker=ReviewWorker(
            db_path=db_path,
            checkpoint_path=checkpoint_path,
            worker_id="worker_fixture",
            stage_hook=stage_hook,
        ),
    )
```

`run_stage(root, stage, stage_hook)` uses this constructor and advances only the
operations required to hit the selected crash point:

```python
def run_stage(root: Path, stage: str, stage_hook) -> None:
    fixture = create_required_review_fixture(
        db_path=str(root / "tasks.db"),
        checkpoint_path=str(root / "review_checkpoints.db"),
        stage_hook=stage_hook,
    )
    if stage == "application_finalized":
        stage_hook(stage, fixture)
        return
    asyncio.run(fixture.worker.run_once())
    if stage == "checkpoint_interrupted":
        return
    accept_review_decision(
        db_path=fixture.db_path,
        run_id=fixture.run_id,
        review_id=fixture.review_id,
        request=fixture.approve_request,
        actor_fingerprint="fixture_actor",
    )
    if stage == "decision_committed":
        stage_hook(stage, fixture)
        return
    asyncio.run(fixture.worker.run_once())
```

`application_finalized` is emitted directly after construction;
`checkpoint_interrupted`, `lease_acquired`, and `graph_resumed` are emitted by
the worker; `decision_committed` is emitted immediately after
`accept_review_decision()` returns.

- [ ] **Step 6: Implement startup reconciliation**

Before claiming normal work:

```python
def reconcile_review_workflows(
    *,
    db_path: str | None,
    gate: ReviewGate,
    now: datetime,
) -> int:
    reconciled = 0
    for workflow in list_reconcilable_workflows(db_path=db_path, now=now):
        try:
            checkpoint = gate.inspect(workflow.checkpoint_thread_id)
        except Exception:
            mark_manual_recovery(
                db_path=db_path,
                workflow_id=workflow.workflow_id,
                worker_id=None,
                error_code="checkpoint_corrupt",
            )
            reconciled += 1
            continue

        if workflow.status == "checkpoint_pending":
            if checkpoint.status == "interrupted":
                mark_waiting_decision(
                    db_path=db_path,
                    workflow_id=workflow.workflow_id,
                )
                reconciled += 1
            continue

        if workflow.status == "resuming" and workflow.lease_expired(now):
            if (
                checkpoint.status == "completed"
                and checkpoint.decision_id == workflow.decision_id
            ):
                mark_resolution_pending(
                    db_path=db_path,
                    workflow_id=workflow.workflow_id,
                    worker_id=None,
                    decision_id=workflow.decision_id,
                )
            elif checkpoint.status == "interrupted":
                release_expired_lease(
                    db_path=db_path,
                    workflow_id=workflow.workflow_id,
                )
            else:
                mark_manual_recovery(
                    db_path=db_path,
                    workflow_id=workflow.workflow_id,
                    worker_id=None,
                    error_code="checkpoint_decision_mismatch",
                )
            reconciled += 1
    return reconciled
```

Use `ReviewGate.inspect()` rather than querying checkpoint tables.

- [ ] **Step 7: Run GREEN**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_durable_review_restart.py \
  tests/integration/test_durable_review_kill9.py -q
```

Expected: restart tests pass and all five crash windows converge.

- [ ] **Step 8: Commit**

```bash
git add api/review_worker.py api/review_repository.py \
  scripts/durable_hitl_crash_worker.py scripts/durable_hitl_fixture.py \
  tests/integration/test_durable_review_restart.py \
  tests/integration/test_durable_review_kill9.py
git commit -m "test(research): verify durable review crash recovery"
```

---

### Task 11: Container Persistence and Thirteen-Gate Runner

**Files:**
- Modify: `Dockerfile.backend`
- Modify: `docker-compose.yml`
- Create: `scripts/durable_hitl_gate_runner.py`
- Create: `scripts/durable_hitl_container_fixture.py`
- Create: `tests/integration/test_durable_review_container.py`
- Create: `tests/unit/test_durable_hitl_gate_runner.py`

- [ ] **Step 1: Write RED gate aggregation test**

```python
# tests/unit/test_durable_hitl_gate_runner.py
from scripts.durable_hitl_gate_runner import build_report


def test_gate_report_is_no_go_when_any_gate_fails():
    report = build_report(
        {f"gate_{number:02d}": number != 13 for number in range(1, 14)}
    )
    assert report["status"] == "NO_GO"
    assert report["passed"] == 12
    assert report["failed"] == ["gate_13"]


def test_gate_report_passes_only_all_thirteen():
    report = build_report(
        {f"gate_{number:02d}": True for number in range(1, 14)}
    )
    assert report["status"] == "PASS"
    assert report["passed"] == 13
    assert report["failed"] == []
```

- [ ] **Step 2: Write RED container persistence test**

```python
# tests/integration/test_durable_review_container.py
def test_backend_container_restart_preserves_review_state(docker_project):
    seeded = docker_project.exec_json(
        "python scripts/durable_hitl_container_fixture.py seed"
    )
    docker_project.restart("backend")
    recovered = docker_project.exec_json(
        "python scripts/durable_hitl_container_fixture.py "
        f"recover --run-id {seeded['run_id']} --timeout-seconds 20"
    )
    assert recovered["application_db_preserved"] is True
    assert recovered["checkpoint_db_preserved"] is True
    assert recovered["decision_preserved"] is True
    assert recovered["reviewed_artifact_preserved"] is True
```

Implement `docker_project` locally in
`tests/integration/test_durable_review_container.py`; do not add a pytest Docker
plugin. The fixture must:

1. allocate a unique Compose project name;
2. run `docker compose up -d --build backend` with process-local
   `DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL=true` and a non-production
   test-only `API_SECRET`;
3. expose `exec_json()` and `restart()` wrappers using argument arrays rather than
   `shell=True`;
4. always run `docker compose down -v` in `finally`;
5. fail, rather than skip, when
   `DECISION_RESEARCH_AGENT_REQUIRE_DOCKER_TESTS=true`.

Mark with `@pytest.mark.docker` and skip with an explicit reason when Docker is
unavailable. The final P1B gate command must run it on a Docker-capable host; a
skip does not count as a pass.

When `DECISION_RESEARCH_AGENT_REQUIRE_DOCKER_TESTS=true`, the fixture must call
`pytest.fail("docker_required_but_unavailable")` instead of `pytest.skip(...)`.
This prevents pytest's zero exit code for an all-skipped node from becoming a
false thirteen-gate PASS.

- [ ] **Step 3: Run RED**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_durable_hitl_gate_runner.py -q
```

Expected: FAIL because the gate runner does not exist.

- [ ] **Step 4: Include scripts and checkpoint path in the backend image**

Modify `Dockerfile.backend`:

```dockerfile
COPY scripts/ scripts/
```

Modify `docker-compose.yml` backend environment:

```yaml
environment:
  - MYSQL_HOST=mysql
  - MYSQL_PORT=3306
  - TASKS_DB_PATH=/app/data/tasks.db
  - DECISION_RESEARCH_AGENT_CHECKPOINT_DB_PATH=/app/data/review_checkpoints.db
  - DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL=${DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL:-false}
```

Do not set `API_SECRET` to a default value.

- [ ] **Step 5: Implement machine-readable gate report**

```python
# scripts/durable_hitl_gate_runner.py
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


GATE_TESTS = {
    "gate_01_restart_recovery":
        "tests/integration/test_durable_review_restart.py::"
        "test_restart_recovers_checkpoint_pending",
    "gate_02_container_persistence":
        "tests/integration/test_durable_review_container.py::"
        "test_backend_container_restart_preserves_review_state",
    "gate_03_duplicate_idempotency":
        "tests/integration/test_durable_review_api.py::"
        "test_decision_api_accepts_and_replays_same_request",
    "gate_04_decision_before_resume":
        "tests/integration/test_durable_review_restart.py::"
        "test_restart_recovers_decision_committed_before_resume",
    "gate_05_replay_safety":
        "tests/unit/test_review_repository.py::"
        "test_approval_resolution_is_exactly_once",
    "gate_06_conflicting_decision":
        "tests/integration/test_durable_review_api.py::"
        "test_conflicting_decision_returns_actionable_409",
    "gate_07_checkpoint_failure":
        "tests/integration/test_durable_review_restart.py::"
        "test_corrupt_checkpoint_after_resume_attempt_is_manual_recovery",
    "gate_08_migration_restore":
        "tests/unit/test_review_migrations.py::"
        "test_review_schema_backup_restore_removes_additive_tables",
    "gate_09_auth_fail_closed":
        "tests/integration/test_durable_review_api.py::"
        "test_enabled_decision_api_fails_closed_without_api_secret",
    "gate_10_unresolved_not_deliverable":
        "tests/integration/test_durable_review_lifecycle.py::"
        "test_required_review_remains_not_deliverable_before_resolution",
    "gate_11_lease_reclaim":
        "tests/unit/test_review_repository.py::"
        "test_expired_lease_is_reclaimed_without_new_segment",
    "gate_12_sync_durability":
        "tests/integration/test_review_checkpoint_compatibility.py::"
        "test_sqlite_checkpoint_reopens_and_resumes_with_sync_durability",
    "gate_13_sigkill_windows":
        "tests/integration/test_durable_review_kill9.py::"
        "test_sigkill_window_converges_without_duplicate_state",
}


def build_report(results: dict[str, bool]) -> dict:
    failed = [name for name, passed in sorted(results.items()) if not passed]
    return {
        "status": "PASS" if not failed and len(results) == 13 else "NO_GO",
        "expected": 13,
        "passed": sum(results.values()),
        "failed": failed,
        "results": results,
    }


def _pytest_gate_passed(completed: subprocess.CompletedProcess[str]) -> bool:
    output = f"{completed.stdout}\n{completed.stderr}"
    skipped = re.search(r"\b\d+\s+skipped\b", output, flags=re.IGNORECASE)
    return completed.returncode == 0 and skipped is None


def run_gate_tests() -> dict[str, bool]:
    results = {}
    for gate_name, node_id in GATE_TESTS.items():
        command = [sys.executable, "-m", "pytest", node_id, "-q"]
        env = os.environ.copy()
        if gate_name == "gate_02_container_persistence":
            env["DECISION_RESEARCH_AGENT_REQUIRE_DOCKER_TESTS"] = "true"
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        results[gate_name] = _pytest_gate_passed(completed)
        if not results[gate_name]:
            print(completed.stdout, file=sys.stderr)
            print(completed.stderr, file=sys.stderr)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = build_report(run_gate_tests())
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if report.get("status") != "NO_GO" else 1)


if __name__ == "__main__":
    main()
```

Add a unit test that stubs a Docker gate subprocess returning
zero with skipped output and verifies the runner still reports `NO_GO`; the
environment contract above is the primary enforcement, and the output check is
defense in depth.

Add `scripts/durable_hitl_container_fixture.py` with two commands:

```python
def seed() -> dict:
    fixture = create_required_review_fixture(
        db_path=os.environ["TASKS_DB_PATH"],
        checkpoint_path=os.environ[
            "DECISION_RESEARCH_AGENT_CHECKPOINT_DB_PATH"
        ],
    )
    asyncio.run(fixture.worker.run_once())
    acceptance = accept_review_decision(
        db_path=fixture.db_path,
        run_id=fixture.run_id,
        review_id=fixture.review_id,
        request=fixture.approve_request,
        actor_fingerprint="container_fixture",
    )
    return {
        "run_id": fixture.run_id,
        "decision_id": acceptance.decision.decision_id,
    }


def recover(*, run_id: str, timeout_seconds: float) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        run = get_run(run_id=run_id)
        if run and run["delivery_status"] == "ready":
            checkpoint = ReviewGate(
                os.environ["DECISION_RESEARCH_AGENT_CHECKPOINT_DB_PATH"],
                lambda decision_id: get_decision(decision_id=decision_id),
            ).inspect(run["review_workflow"]["checkpoint_thread_id"])
            artifact_ids = {item["artifact_id"] for item in run["artifacts"]}
            return {
                "application_db_preserved": True,
                "checkpoint_db_preserved": checkpoint.status == "completed",
                "decision_preserved": run["review_decision"] is not None,
                "reviewed_artifact_preserved":
                    "decision-brief.reviewed.json" in artifact_ids,
            }
        time.sleep(0.25)
    raise RuntimeError("container_review_recovery_timeout")
```

The script uses the same deterministic fixture builder as the crash harness,
accepts `seed` and `recover` subcommands through `argparse`, prints one JSON object,
and never prints decision reason or credential material.

- [ ] **Step 6: Run GREEN unit and Docker gates**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_durable_hitl_gate_runner.py -q
docker compose config --quiet
docker compose build backend
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/integration/test_durable_review_container.py -m docker -q
```

Expected: unit tests pass, Compose config passes, backend image builds, and
container persistence test passes without skip.

- [ ] **Step 7: Commit**

```bash
git add Dockerfile.backend docker-compose.yml \
  scripts/durable_hitl_gate_runner.py scripts/durable_hitl_container_fixture.py \
  tests/unit/test_durable_hitl_gate_runner.py \
  tests/integration/test_durable_review_container.py
git commit -m "test(research): add durable HITL gate runner"
```

---

### Task 12: Documentation, Gate Evidence, Full Verification, and NO-GO Discipline

**Files:**
- Create: `docs/operations/durable-hitl-feasibility.md`
- Create: `docs/evidence/durable-hitl-gate-report.json`
- Modify: `spec/api-contract.md`
- Modify: `spec/data-models.md`
- Modify: `README.md`
- Modify: `README_CN.md`
- Modify: `TODOS.md`

- [ ] **Step 1: Document the experimental boundary**

`docs/operations/durable-hitl-feasibility.md` must include:

````markdown
# Durable HITL Feasibility

## Status

The endpoint is experimental and disabled by default. A successful gate report
does not enable it automatically.

## Enable in a controlled environment

```dotenv
DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL=true
API_SECRET=<configured out of band>
TASKS_DB_PATH=/app/data/tasks.db
DECISION_RESEARCH_AGENT_CHECKPOINT_DB_PATH=/app/data/review_checkpoints.db
```

## Decision semantics

- `approve` permits delivery but does not verify evidence.
- `reject` blocks delivery and does not start new research.

## Gate command

```bash
python scripts/durable_hitl_gate_runner.py \
  --output docs/evidence/durable-hitl-gate-report.json
```

`PASS` requires thirteen passes. Any failure or Docker skip is `NO_GO`.
````

- [ ] **Step 2: Update API and data model references**

Document:

- the experimental POST route and fixed error envelope;
- sanitized additions to `GET /api/runs/{run_id}`;
- the four new tables;
- `blocked` delivery status;
- application DB vs checkpoint DB authority;
- decision reason, actor fingerprint, and checkpoint internals are never returned.

- [ ] **Step 3: Run focused verification**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest \
  tests/unit/test_review_models.py \
  tests/unit/test_review_migrations.py \
  tests/unit/test_review_repository.py \
  tests/unit/test_review_artifacts.py \
  tests/unit/test_review_gate.py \
  tests/unit/test_review_worker.py \
  tests/integration/test_review_checkpoint_compatibility.py \
  tests/integration/test_durable_review_api.py \
  tests/integration/test_durable_review_lifecycle.py \
  tests/integration/test_durable_review_restart.py \
  tests/integration/test_durable_review_kill9.py -q
```

Expected: all focused tests pass.

The focused set must include the two-worker lease race, poison-work retry cap,
Docker-required skip behavior, and per-stage exact crash oracle.

- [ ] **Step 4: Run the complete backend and frontend regression**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python -m pytest -q
cd frontend && npm ci && npm run build && cd ..
/tmp/decision-research-p1b-compat/bin/python -m compileall -q agent api tools scripts
docker compose config --quiet
git diff --check
```

Expected: all commands pass.

- [ ] **Step 5: Run all thirteen gates**

Run:

```bash
/tmp/decision-research-p1b-compat/bin/python \
  scripts/durable_hitl_gate_runner.py \
  --output docs/evidence/durable-hitl-gate-report.json
```

Expected:

```json
{
  "status": "PASS",
  "expected": 13,
  "passed": 13,
  "failed": []
}
```

If any gate fails, keep the generated report with `"status": "NO_GO"`, keep the
feature flag default false, do not claim P1B passed, and do not begin P1C.

- [ ] **Step 6: Inspect privacy and scope**

Run:

```bash
rg -n \
  'actor_fingerprint|lease_owner|checkpoint_path|decision reason|API_SECRET=' \
  README.md README_CN.md docs spec api tests scripts .env.example
git diff --stat origin/main...HEAD
git diff origin/main...HEAD -- . ':!docs/evidence/durable-hitl-gate-report.json'
```

Expected:

- no secret value;
- no actor fingerprint in public API projections or reviewed artifact;
- no raw checkpoint payload in API responses;
- no UI, Skills, Async Subagent, Agent Server, or Postgres expansion.

- [ ] **Step 7: Commit**

```bash
git add README.md README_CN.md TODOS.md spec/api-contract.md spec/data-models.md \
  docs/operations/durable-hitl-feasibility.md \
  docs/evidence/durable-hitl-gate-report.json
git commit -m "docs(research): record durable HITL feasibility"
```

---

## Final Review Sequence

After Task 12:

1. Run one authoritative `gstack-review`.
2. Address findings with `superpowers:receiving-code-review`.
3. Run targeted re-review only for changed findings.
4. Run `superpowers:verification-before-completion`.
5. Stop for user authorization before push or PR.

Do not run another `gstack-autoplan`; it reviews this implementation plan once
before implementation.

## Plan Self-Review

- Spec coverage: every goal, non-goal, status transition, API boundary, migration,
  recovery case, durable gate, and kill condition maps to a task above.
- Placeholder scan: no implementation placeholder remains; repository range
  notation such as `origin/main...HEAD` is intentional Git syntax.
- Type consistency: decisions are immutable `ReviewDecisionRecord` values;
  checkpoint state carries only opaque IDs; `resolution_pending` distinguishes a
  completed graph from a committed application resolution.
- Security correction: decision reason text is audit-only and is not projected
  through `GET /api/runs/{run_id}` or reviewed artifacts.
- Scope check: the plan remains one feasibility milestone with two internal lanes
  (P1B1 persistence/API and P1B2 checkpoint/recovery), one feature flag, and one
  final PASS/NO-GO report.

## Required Completion Report

Report:

- P1B status: `PASS` or `NO_GO`;
- branch and commit;
- exact focused/full/frontend/Docker commands and results;
- thirteen-gate table;
- whether the feature flag remains false;
- schema and migration result;
- documentation impact;
- any `manual_recovery` limitation;
- confirmation that P1C was not started.

---

## Autoplan Review Addendum

Reviewed on 2026-06-19 in **HOLD SCOPE** mode against the real repository at
commit `8f6dcc5`.

- Premise gate: passed by the user's explicit confirmation before `/autoplan`.
- UI scope: no. Design review skipped.
- Developer-facing scope: yes. The plan adds an experimental HTTP mutation,
  environment flags, migration commands, an operator gate runner, and runbook.
- Outside voices: Codex CLI authenticated but returned a usage-limit error before
  analysis; Claude subagents were unavailable under the active host policy.
  Consensus tables therefore use `N/A`, never fabricated agreement.

### Phase 1: CEO Review

#### 0A. Premise Challenge

| Premise | Assessment | Decision |
|---|---|---|
| P1A value has been proven strongly enough to justify P1B | Supported by the completed Talent value gate and merged renderer work | Keep |
| Durable HITL must be proven before public enablement | Correct; current non-interrupt bundle is safer until restart/idempotency gates pass | Keep |
| A pure review graph is safer than interrupting the expensive research graph | Correct because replay is isolated from model/tool side effects | Keep |
| Separate application and checkpoint SQLite databases are acceptable for a feasibility spike | Acceptable only with explicit reconciliation and `manual_recovery`; not a production scalability claim | Keep with boundary |
| All twelve tasks should run before the kill gate is evaluated | Wrong proxy; it risks spending the full window after feasibility has already failed | Replace with daily cutlines |

The user outcome is not "we used LangGraph interrupt." The outcome is: a required
Talent review can be decided once, recovered after a crash, and either release or
block delivery without changing evidence truth.

Doing nothing leaves the current non-interrupt review bundle intact. That is safe,
but it prevents externally usable review decisions. The pain is real but not urgent
enough to justify weakening the kill gate.

#### 0B. What Already Exists

| Sub-problem | Existing code | Reuse decision |
|---|---|---|
| Run identity and fenced transitions | `api/run_repository.py` `run_id`, `segment_id`, `state_version` | Extend; do not create a second run model |
| Atomic Talent finalization | `finalize_run_transaction()` | Seed workflow in the same transaction |
| Deterministic review content | `api/review_service.py`, `api/talent_artifacts.py` | Retain as review input |
| Canonical DecisionBrief rendering | `api/decision_brief.py` | Build reviewed artifacts from the original canonical artifact |
| Persistent application SQLite | `api/persistence.py`, `api/run_migrations.py` | Keep authoritative business ledger |
| FastAPI API-key middleware | `api/server.py` | Do not trust its fail-open dev behavior for decision mutation; add route-local fail-closed auth |
| Async task lifecycle | `api/task_tracker.py` | Reuse lifecycle style, not its process-local task registry |
| Persistent Docker volume | `docker-compose.yml` `backend_data:/app/data` | Store both SQLite files on the existing volume |
| Evidence/review privacy boundary | sanitized run/artifact APIs | Keep reason and actor audit-only |

#### 0C. Dream State Delta

```text
CURRENT
non-interrupt review bundle
delivery remains review_required
        |
        v
P1B FEASIBILITY
immutable decision ledger
pure persisted review gate
restart + crash recovery
feature flag remains false
        |
        v
12-MONTH IDEAL
deployment-appropriate durable checkpointer
real reviewer identity and authorization
operational SLOs and bounded recovery tooling
multiple reviewed delivery channels
```

P1B moves in the right direction but intentionally stops before reviewer UX,
role-based authorization, and production-scale checkpoint infrastructure.

#### 0C-bis. Implementation Alternatives

| Approach | Effort | Risk | Pros | Cons | Decision |
|---|---:|---:|---|---|---|
| A. Application ledger only, no LangGraph interrupt | S | Low | Smallest diff, proves decision idempotency | Does not prove the approved durable-gate requirement | Reject |
| B. Pure review graph plus application ledger | L | Medium | Isolates replay, proves the actual durability contract, reuses existing run model | Cross-database reconciliation is real complexity | **Selected** |
| C. Embed interrupt in Talent research graph | XL | High | One graph and one thread | Replays model/tool work, expands blast radius, couples review to research | Reject |

Approach B remains the best fit. It spends complexity only where the approved
requirement demands it.

#### 0D. Scope and Complexity

The plan touches more than eight files and introduces four service modules, so the
complexity smell is real. It is still justified because the scope contains four
separate responsibilities: immutable contracts, business persistence, checkpoint
execution, and HTTP/worker integration. Combining them into `api/server.py` would
reduce file count while increasing coupling and test cost.

The reduction applied inside scope is sequencing, not capability removal:

1. dependency/checkpoint compatibility;
2. ledger and deterministic identities;
3. pure graph and bounded worker;
4. API/lifecycle;
5. crash/container evidence;
6. documentation.

#### 0E. Temporal Interrogation

| Time | Decision needed before implementation |
|---|---|
| Hour 1 | Exact package compatibility and whether SQLite checkpoint reopen/resume works |
| Hours 2-3 | Transaction boundaries, deterministic IDs, status/version invariants |
| Hours 4-5 | Replay-safe graph behavior, lease ownership, retry cap, API auth |
| Hour 6+ | Exact crash oracles, Docker-required behavior, gate evidence and rollback |

#### 0F. Mode

**HOLD SCOPE**. No Skills, Async Subagent, UI, LLM reviewer, ATS integration,
Postgres migration, or public P1C activation was added.

#### CEO Architecture Review

```text
POST Talent run
      |
      v
api/server.py::_run_v2_with_persistence
      |
      +---- atomic transaction -------------------------------+
      |                                                       |
      v                                                       v
research_runs_v2 + review_bundles_v2                review_workflows_v2
      |                                                       |
      |                                                       v
      |                                              ReviewWorker lease
      |                                                       |
      |                                  +--------------------+------------------+
      |                                  |                                       |
      |                                  v                                       v
      |                         application SQLite                      checkpoint SQLite
      |                         decision authority                      graph position only
      |                                  |                                       |
      |                                  +--------------------+------------------+
      |                                                       v
      +---------------------------------------------- fenced resolution
                                                              |
                                      +-----------------------+------------------+
                                      v                                          v
                             approve: delivery ready                   reject: delivery blocked
```

Coupling is acceptable only if `api/review_gate.py` never writes business state and
`api/review_repository.py` never infers authority from raw checkpoint tables.

At 10x current load, SQLite write contention and polling are the first limits. At
100x, this architecture is outside its stated envelope. The plan now says so.

Rollback:

```text
incident
  |
  +--> set feature flag false
  |      new decisions return durable_hitl_disabled
  |      current review bundles remain review_required
  |
  +--> preserve both DB files for diagnosis
  |
  +--> restore application DB only from verified backup when migration itself failed
  |
  +--> do not delete checkpoint state while an accepted decision exists
```

#### Error and Rescue Registry

| Codepath | Failure | Exception/code | Rescue | Caller sees |
|---|---|---|---|---|
| dependency compatibility | package missing/incompatible | import/version failure | stop Day 0 | NO-GO report |
| `init_review_schema` | locked/corrupt DB | `sqlite3.OperationalError` / `DatabaseError` | restore verified backup for migration failure | migration failure |
| `accept_review_decision` | stale version | `stale_state_version` | no retry mutation | actionable 409 |
| `accept_review_decision` | duplicate conflicting request | `decision_id_conflict` / `review_already_decided` | return persisted authority | actionable 409 |
| `ReviewGate.ensure_waiting` | checkpoint locked | bounded SQLite error | release lease; retry up to cap | pending, logged |
| `ReviewGate.resume` | mismatched decision | `checkpoint_decision_mismatch` | `manual_recovery` | run projection shows recovery required |
| `ReviewGate.inspect` | corrupt checkpoint | `checkpoint_corrupt` | `manual_recovery` | run projection shows recovery required |
| `ReviewWorker.run_once` | transient unknown exception | allowlisted error code | release/retry up to 3 | no false success |
| `ReviewWorker.run_once` | poison work | max attempts reached | `manual_recovery` | bounded terminal diagnosis |
| review API auth | missing secret | `review_auth_not_configured` | reject before mutation | 503 with fix |
| review API auth | bad key | `invalid_api_key` | reject before mutation | 401 with fix |
| Docker gate | Docker absent | `docker_required_but_unavailable` | fail gate, never skip-pass | NO-GO |

No LLM call exists in this review path, so malformed/refusal model output is not a
new P1B failure mode.

#### Security Threat Model

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Decision mutation when global auth is fail-open | Medium | High | route-local fail-closed authentication |
| IDOR by changing `run_id`/`review_id` | Medium | High | transaction checks exact run/review/revision relationship |
| Duplicate/conflicting decision | High | High | unique constraints, request hash, state-version fence |
| Reason or credential leakage | Medium | Medium | audit-only fields, sanitized projections, no raw exception persistence |
| Checkpoint payload becomes business authority | Low | High | decision loader validates against application ledger |
| SQL injection | Low | High | parameterized SQL only |
| Path injection for checkpoint DB | Low | Medium | server-controlled environment path, no request-controlled path |

#### Data Flow and Shadow Paths

```text
DECISION REQUEST
  |
  +-- missing/invalid body ----------> 422, no write
  +-- feature flag false ------------> 404 durable_hitl_disabled
  +-- secret missing ----------------> 503 review_auth_not_configured
  +-- wrong key ---------------------> 401 invalid_api_key
  +-- stale/conflicting -------------> 409 stable conflict envelope
  |
  v
validate run + review + revision + version
  |
  v
atomic decision + resume_pending + state_version
  |
  +-- duplicate same hash -----------> idempotent 202
  +-- DB locked/transient -----------> no partial commit, bounded retry
  |
  v
worker lease -> checkpoint resume -> resolution_pending -> resolution commit
  |
  +-- completed graph, app crash ----> startup reconciliation
  +-- corrupt/mismatch --------------> manual_recovery
```

#### CEO Code Quality Review

- Keep review contracts in one module and persistence in one repository module.
- Remove the unused workflow `failed` state; `manual_recovery` is the explicit
  terminal state for operator intervention.
- Keep synchronous `SqliteSaver` calls off the FastAPI event loop with
  `asyncio.to_thread`.
- Add SQLite `busy_timeout` and WAL to make lock behavior bounded and observable.
- Keep fixture builders outside `tests/` only because Docker and subprocess
  harnesses need them in the backend image.

#### CEO Test Review

```text
NEW USER/API FLOW
submit approve/reject
  +-- disabled/auth/validation/conflict/idempotent tests
  +-- unresolved remains non-deliverable
  +-- approved becomes ready
  +-- rejected becomes blocked

NEW DATA FLOW
Talent finalization -> workflow seed -> checkpoint -> decision -> resolution
  +-- transaction rollback tests
  +-- reopen/resume compatibility test
  +-- decision and artifact exactly-once tests

NEW ASYNC WORK
lifespan worker -> claim -> lease -> resume -> resolve
  +-- two-worker race test
  +-- lease expiry/reclaim test
  +-- poison-work retry-cap test

NEW CRASH FLOW
five SIGKILL windows
  +-- exact per-stage oracle, not generic manual_recovery

NEW DEPLOYMENT FLOW
Compose persistent volume
  +-- restart test with Docker required
  +-- skipped Docker node forces NO-GO
```

#### CEO Performance Review

- No N+1 network calls are introduced.
- `get_run()` adds bounded point queries for one workflow, decision, and resolution.
- Worker polling must claim one row through the indexed
  `(status, lease_expires_at, updated_at)` path.
- SQLite lock wait is bounded to five seconds; retries stop after three attempts.
- No cache is needed because decision and checkpoint state must be strongly fresh.

#### CEO Observability Review

Required structured fields: `workflow_id`, `run_id`, `review_id`, `decision_id`
when present, `worker_id`, stage, attempt, error code, and elapsed time. Never log
reason text, API keys, actor fingerprints, evidence snippets, or checkpoint payloads.

The machine-readable gate report is the milestone dashboard. No new UI dashboard or
alerting system belongs in P1B.

#### CEO Deployment Review

Deploy order:

```text
install constrained dependency
  -> apply/verify additive application schema
  -> deploy code with feature flag false
  -> run focused + full + Docker gates
  -> record PASS or NO_GO
  -> keep feature flag false
```

Old code ignores additive tables. New code with the flag false preserves current
review-bundle behavior. Rollback does not require destructive schema deletion.

#### CEO Long-Term Review

Reversibility: **4/5**. Code and route are feature-flagged; schema is additive.
The path dependency is the dual-database reconciliation protocol. It remains
acceptable only while clearly scoped as a feasibility result.

#### CEO Failure Modes Registry

| Codepath | Failure mode | Rescued | Test | Visible | Logged |
|---|---|---:|---:|---:|---:|
| migration | checksum/table mismatch | yes | yes | yes | yes |
| decision API | missing auth | yes | yes | yes | yes |
| decision API | stale/conflict | yes | yes | yes | yes |
| checkpoint create | process killed | yes | yes | projection | yes |
| decision commit | process killed | yes | yes | recovered | yes |
| graph resume | process killed | yes | yes | recovered | yes |
| checkpoint corrupt | irreconcilable | manual | yes | yes | yes |
| lease held by dead worker | expiry/reclaim | yes | yes | delayed | yes |
| poison workflow | repeated failure | manual after 3 | yes | yes | yes |
| Docker unavailable | gate would skip | fail gate | yes | NO-GO | yes |

Critical gaps after plan corrections: **0**.

#### CEO Dual Voice Consensus

| Dimension | Claude subagent | Codex CLI | Consensus |
|---|---|---|---|
| Premises valid | N/A | unavailable: usage limit | primary review only |
| Right problem | N/A | unavailable | primary review: yes |
| Scope calibrated | N/A | unavailable | primary review: yes, with daily cutlines |
| Alternatives explored | N/A | unavailable | primary review: sufficient |
| Market risk covered | N/A | unavailable | not material to feasibility spike |
| Six-month trajectory | N/A | unavailable | acceptable with SQLite boundary |

#### CEO Completion Summary

| Item | Result |
|---|---|
| Mode | HOLD SCOPE |
| Architecture issues | 2 corrected: SQLite production claim, event-loop/lock boundary |
| Error paths mapped | 12 |
| Security issues | 1 corrected: route-local fail-closed auth retained as mandatory |
| Data/interaction gaps | 2 corrected: exact crash oracle, Docker skip |
| Code quality issues | 2 corrected: retry cap, unused state |
| Test gaps | 4 added |
| Performance issues | 1 bounded: SQLite lock wait |
| Observability gaps | 0 after stable-code requirements |
| Deployment risks | 1 corrected: daily kill cutlines |
| Design | skipped, no UI scope |
| Scope proposals | 0 |
| Unresolved CEO decisions | 0 |

**Phase 1 complete.** Outside voices were unavailable; no user challenge was
manufactured. The approved premise and HOLD SCOPE direction stand.

### Phase 2: Design Review

Skipped. The plan adds no screen, component, layout, form, or end-user UI flow.

### Phase 3: Engineering Review

#### Scope Challenge

The file count is high, but the architecture can be split into two sequential lanes
without reducing safety:

```text
Lane A: contracts -> schema -> decision repository -> artifacts
                                      |
                                      v
Lane B: checkpoint graph -> worker -> API/lifecycle -> crash/container gates
```

The lanes should not run as independent worktrees because both converge on
`api/review_repository.py`, `api/run_repository.py`, shared fixtures, and status
invariants. Sequential implementation is safer and faster than merge-conflict
coordination for this four-day spike.

#### Engineering Dependency Graph

```text
review_models
  +--> review_repository -----> run_repository
  |          |                       |
  |          +--> review_artifacts <-+
  |          |
  |          +--> review_gate <--> checkpoint SQLite
  |                    |
  |                    v
  +--------------> review_worker
                         |
                         +--> review_api
                         +--> FastAPI lifespan
                         +--> restart/SIGKILL/container harness
```

#### Engineering Findings

1. **[P1] (confidence 10/10)** The planned gate runner treated pytest return code
   zero as PASS, while the plan explicitly allowed Docker tests to skip. Pytest
   returns zero for skipped tests, so gate 2 could falsely pass. Fixed with a
   Docker-required environment contract plus skipped-output defense.
2. **[P1] (confidence 10/10)** The planned SIGKILL assertion accepted
   `manual_recovery` for every crash window and only checked counts `<= 1`. That
   proved absence of some duplicates, not correct recovery. Fixed with exact
   per-stage terminal states and exact counts.
3. **[P1] (confidence 9/10)** The worker catch-all released poison work forever.
   Fixed with a three-attempt cap and explicit `manual_recovery`.
4. **[P2] (confidence 9/10)** Synchronous checkpoint operations were called directly
   from an async worker. Fixed by moving them to `asyncio.to_thread`.
5. **[P2] (confidence 8/10)** SQLite lock handling had no explicit wait bound.
   Fixed with connection timeout, WAL, and `busy_timeout`.
6. **[P2] (confidence 8/10)** `docker_project` had no fixture contract and could
   accidentally introduce a plugin or shell injection. Fixed with a local,
   argument-array fixture contract and guaranteed teardown.

#### Engineering Test Diagram

| Codepath | Happy path | Failure/edge path | Test level |
|---|---|---|---|
| contract validation | approve/reject valid | missing reject reason, invalid IDs, extra fields | unit |
| schema migration | apply twice | checksum mismatch, restore | unit/integration |
| workflow seed | required review seeds atomically | artifact/evidence insert rollback | unit |
| decision acceptance | first accept | replay, conflicting ID, stale version, wrong profile | unit/integration |
| reviewed artifacts | approve/reject deterministic | reason/actor omitted, duplicate artifact fence | unit |
| gate | interrupt/reopen/resume | wrong review decision, corrupt checkpoint | unit/integration |
| worker | claim/resume/resolve | two-worker race, lease expiry, poison retry cap | async unit |
| API | authenticated 202 | disabled 404, no secret 503, wrong key 401, conflict 409 | integration |
| lifecycle | worker starts/stops | enabled without secret | integration |
| restart | pending and committed states recover | corruption becomes manual recovery | subprocess |
| SIGKILL | five exact windows converge | duplicate or wrong terminal state fails | subprocess chaos |
| container | restart preserves both DBs | Docker unavailable is NO-GO | Docker integration |
| gate report | all 13 pass | any failure or skip => NO-GO | unit/system |

The 2am confidence test is the thirteen-gate runner on a Docker-capable host. The
hostile-QA test is the exact five-window SIGKILL matrix plus concurrent workers.
The chaos test is killing the worker after checkpoint completion but before
application resolution.

#### Engineering Performance

The plan is low-throughput by design. The main risks are SQLite lock contention and
poll amplification. One indexed claim query per poll, one claimed row per worker,
five-second lock bounds, and one-second idle polling are acceptable for the spike.
No load test is required beyond a two-worker race because production throughput is
explicitly not claimed.

#### Engineering NOT in Scope

- Postgres or LangGraph Agent Server.
- Public enablement after PASS.
- Multiple review revisions per run.
- Reviewer accounts, RBAC, UI, or browser workflow.
- Re-research after rejection.
- Skills, Async Subagent, or LLM reviewer.
- Performance claims beyond the single-service SQLite envelope.

#### Engineering Completion Summary

| Item | Result |
|---|---|
| Scope | accepted with internal hardening |
| Architecture issues | 2 |
| Code quality issues | 2 |
| Test gaps | 4 |
| Performance issues | 1 |
| Failure-mode critical gaps | 0 after corrections |
| Parallelization | 2 conceptual lanes, sequential execution recommended |
| External voice | unavailable |
| Unresolved decisions | 0 |

**Phase 3 complete.** Six actionable findings were folded into the plan.

### Phase 3.5: DX Review

#### Developer Persona

| Field | Value |
|---|---|
| Who | Repository maintainer or backend engineer evaluating P1B |
| Context | Existing project environment; needs to prove or reject durability safely |
| Tolerance | One documented command for the final gate, explicit prerequisites |
| Expects | stable error codes, deterministic report, no hidden mutation, clean rollback |

#### Developer Perspective

I already know how to run the repository. I do not want a new platform tutorial; I
want to know whether durable review is enabled, what authority each SQLite file has,
and whether a failed gate can silently pass. I start from the operations doc, create
the constrained Python 3.11 environment, and run the compatibility gate before
touching persistence. During implementation, each task gives me one RED command and
one focused GREEN command. At the end I run one gate runner. If Docker is unavailable,
the command must say NO-GO rather than let me believe the feature is safe. If a crash
lands in `manual_recovery`, I need a stable error code and a runbook, not a traceback
or raw checkpoint JSON. The best moment is not a flashy output; it is seeing a
machine-readable report with exactly thirteen passes and knowing the feature still
did not enable itself.

#### Reference Benchmark

| Reference | Useful pattern | Applied here |
|---|---|---|
| LangGraph official HITL | persistent checkpointer, same `thread_id`, `Command(resume=...)` | explicit compatibility and reopen/resume gate |
| Mature workflow engines | immutable event/decision authority and replay-safe handlers | application ledger remains authoritative |
| Stripe-style mutation APIs | idempotency, stable structured errors, no implicit success | decision ID/hash and problem/cause/fix envelope |
| Current project | constrained dependencies, migration backup/restore, machine-readable benchmark | reused directly |

#### Magical Moment

Delivery vehicle: one CLI gate command producing
`docs/evidence/durable-hitl-gate-report.json`. It is deterministic, reviewable, and
fails non-zero on NO-GO. No playground or UI is justified for an internal disabled
feasibility path.

#### Developer Journey

| Stage | Developer does | Friction control | Status |
|---|---|---|---|
| Discover | reads P1B operations doc | experimental boundary first | covered |
| Evaluate | reads 13 gates and kill rules | PASS does not auto-enable | covered |
| Install | builds constrained Python 3.11 env | exact pinned package set | covered |
| Hello world | runs checkpoint compatibility script | one visible pass line | covered |
| Integrate | implements tasks in order | RED/GREEN per task | covered |
| Debug | reads stable error code and run projection | no raw secret/checkpoint data | covered |
| Verify | runs focused/full/frontend/Docker checks | exact commands | covered |
| Upgrade | applies additive migration with backup | checksum + restore | covered |
| Scale/migrate | stops at stated SQLite envelope | P1C decision, not hidden claim | covered |

Feature-specific time to first controlled proof: target **under 5 minutes after the
repository environment exists**. Fresh dependency installation is excluded from this
feature-specific measure and is recorded separately.

#### First-Time Maintainer Confusion Report

```text
T+0:00  Opens operations doc; sees disabled/experimental status.
T+0:30  Runs compatibility script; learns whether the checkpoint package works.
T+1:30  Reads authority table; application DB is ledger, checkpoint DB is position.
T+2:30  Runs gate runner.
T+3:00  Receives PASS or NO-GO. Docker absence cannot appear as PASS.
```

#### DX Scorecard

| Dimension | Before review | After review | Reason |
|---|---:|---:|---|
| Getting Started | 7 | 8 | daily cutlines and one final gate command |
| API design | 8 | 9 | strict auth, stable conflict envelope, idempotent mutation |
| Error messages | 7 | 9 | bounded codes and problem/cause/fix responses |
| Documentation | 7 | 8 | operations, API, data model, evidence report |
| Upgrade path | 8 | 9 | additive schema, backup, checksum, restore |
| Dev environment | 7 | 8 | constrained Python, Docker-required gate |
| Community/ecosystem | 7 | 7 | unchanged OSS surface; no P1B expansion needed |
| DX measurement | 8 | 9 | machine-readable 13-gate report |
| Overall | 7.4 | 8.6 | fit for an internal experimental path |

#### DX Implementation Checklist

- [ ] Compatibility command works in clean Python 3.11.
- [ ] Final gate is one command and exits non-zero on NO-GO.
- [ ] Docker absence cannot count as PASS.
- [ ] Every API error states problem, cause, fix, and retryability.
- [ ] Run projection omits reason text, actor fingerprint, lease owner, and checkpoint internals.
- [ ] Migration has backup, verification, and restore.
- [ ] Operations doc states PASS does not enable the feature.
- [ ] `manual_recovery` has stable codes and an operator response.
- [ ] P1C decision is not implied by P1B PASS.

#### DX Dual Voice Consensus

| Dimension | Claude subagent | Codex CLI | Consensus |
|---|---|---|---|
| Getting started | N/A | unavailable | primary review: sufficient |
| API naming | N/A | unavailable | primary review: consistent |
| Errors actionable | N/A | unavailable | primary review: strong after correction |
| Docs complete | N/A | unavailable | primary review: implementation requirement |
| Upgrade safe | N/A | unavailable | primary review: additive and reversible |
| Environment friction | N/A | unavailable | primary review: bounded |

**Phase 3.5 complete.** Overall DX target is 8.6/10 for the internal maintainer
persona; public end-user onboarding remains out of scope.

### Cross-Phase Themes

**Theme: false confidence is the main risk.** CEO, engineering, and DX analysis all
converged on the same requirement: no Docker skip, generic `manual_recovery`, or
SQLite PASS may be presented as production-ready success.

**Theme: bounded recovery beats more automation.** Retry caps, exact crash oracles,
and daily kill cutlines create more value than Skills, more agents, or UI.

### NOT in Scope

- Public HITL enablement or P1C implementation.
- Reviewer UI, RBAC, SSO, accounts, or multi-tenant authorization.
- Runtime Skills, Async Subagent, LLM reviewer, or long-term memory authority.
- Postgres migration, Agent Server, queue platform, or distributed scheduler.
- ATS, email, spreadsheet, dashboard, or webhook delivery.
- Re-running research after a rejection.
- Changing evidence verification status on approval.
- Repository/service/API rename work.

### Implementation Tasks

- [ ] **AP-T1 (P1, human: ~1h / Codex: ~15m)** — Gate runner — Make Docker skip an explicit NO-GO.
  - Files: `scripts/durable_hitl_gate_runner.py`, `tests/unit/test_durable_hitl_gate_runner.py`, `tests/integration/test_durable_review_container.py`
  - Verify: stubbed skip test and Docker-required integration gate.
- [ ] **AP-T2 (P1, human: ~2h / Codex: ~30m)** — Crash harness — Assert exact per-stage recovery state and counts.
  - Files: `tests/integration/test_durable_review_kill9.py`, `scripts/durable_hitl_fixture.py`
  - Verify: all five SIGKILL cases reach their specific oracle.
- [ ] **AP-T3 (P1, human: ~2h / Codex: ~30m)** — Worker — Bound poison retries and prove two-worker exactly-once behavior.
  - Files: `api/review_worker.py`, `api/review_repository.py`, `tests/unit/test_review_worker.py`
  - Verify: retry cap and concurrent worker tests.
- [ ] **AP-T4 (P2, human: ~1h / Codex: ~15m)** — Checkpoint adapter — Bound SQLite waits and keep sync I/O off the event loop.
  - Files: `api/review_gate.py`, `api/review_worker.py`, `tests/unit/test_review_gate.py`
  - Verify: timeout/lock test and async worker regression.
- [ ] **AP-T5 (P2, human: ~30m / Codex: ~10m)** — Documentation — State the lightweight SQLite feasibility boundary and daily kill cutlines.
  - Files: `docs/operations/durable-hitl-feasibility.md`, `README.md`, `README_CN.md`
  - Verify: privacy/scope grep and reviewer read-through.

### Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|---|---|---|---|---|---|
| 1 | CEO | Keep pure review graph separate from research graph | auto-decided | replay safety | isolates interrupt replay from model/tool side effects | interrupt Talent graph |
| 2 | CEO | Keep dual SQLite only as feasibility envelope | auto-decided | explicit boundaries | proves current deployment without claiming production scale | production-readiness claim |
| 3 | CEO | Evaluate kill gate daily | auto-decided | speed and focus | stops sunk-cost implementation after failed feasibility | end-only kill gate |
| 4 | Eng | Docker skip is NO-GO | auto-decided | evidence before assertion | pytest skip must never satisfy a durable gate | return-code-only pass |
| 5 | Eng | Use exact crash oracles | auto-decided | complete verification | generic terminal sets can hide broken recovery | `<= 1` and any terminal |
| 6 | Eng | Cap retries at three | auto-decided | bounded failure | poison work must stop visibly | infinite release/retry |
| 7 | Eng | Move sync checkpoint calls to threads | auto-decided | protect event loop | SQLite waits must not stall FastAPI | direct sync call |
| 8 | DX | One machine-readable gate command is the magical moment | auto-decided | simplest complete DX | internal maintainer needs certainty, not UI | playground/UI |

No taste decision or user challenge remains open.

## GSTACK REVIEW REPORT

### Runs

| Review | Runs | Status | Findings |
|---|---:|---|---|
| CEO Review | 1 | CLEAR | `HOLD_SCOPE`; 0 critical gaps |
| Codex Independent Review | 1 | UNAVAILABLE | CLI authentication succeeded, but the review call hit the current usage limit |
| Engineering Review | 1 | CLEAR | 6 findings folded into the plan; 0 unresolved critical gaps |
| Design Review | 0 | SKIPPED | No UI or visual interaction change in P1B |
| Developer Experience Review | 1 | CLEAR | Internal maintainer score improved from 7.4 to 8.6 |

### CODEX

Codex CLI was available and authenticated, but the independent review call could not
run because the account had reached its usage limit. This report does not fabricate
cross-model consensus; the primary CEO, engineering, and DX reviews remain the
decision basis.

### VERDICT

CEO, engineering, and developer-experience reviews are cleared. The plan is approved
for implementation of the bounded P1B durable HITL feasibility gate. Approval does
not enable the feature, establish production readiness, or authorize P1C.

NO UNRESOLVED DECISIONS
