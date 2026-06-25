# P2A Real-Source Proof Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to implement this plan task-by-task. Coding
> subagents are intentionally not required. Steps use checkbox (`- [ ]`) syntax
> for tracking.

**Goal:** Prove, with a small public-source sample, that real observations can
move through Evidence verification, deterministic publication rebuild, fresh
controlled review, and current delivery without adding new runtime capability.

**Architecture:** Add a bounded offline proof harness around existing
repositories, APIs, and CLI contracts. The harness validates a committed
manifest, seeds ordinary Talent Evidence, records human-operated verification
and review results, and emits redacted proof reports; it does not fetch web
pages, change schemas, change APIs, or make decisions automatically.

**Tech Stack:** Python 3.11+, Pydantic 2.13, SQLite WAL, FastAPI TestClient,
existing Decision Research Agent CLI, pytest, Docker Compose.

---

## Delivery Boundary

This plan implements P2A PR3 as one external PR with five to six focused
commits.

Included:

- one fixed real-source proof manifest with 5-8 bounded observations;
- manifest validation, canonical hash, and redaction checks;
- deterministic offline seeding of ordinary Talent Evidence with origin
  `none`;
- repository/API-level proof that human verification changes effective
  authority and forces a fresh publication review;
- operator workflow docs for the existing CLI commands;
- committed JSON and Markdown proof report after the real operator run.

Excluded:

- automatic web fetching, crawling, screenshots, browser automation, or source
  archiving;
- new public API, schema, DB table, CLI command in the canonical tool, or
  production ingestion path;
- new Agent tool, profile, Skill, subagent, or LLM reviewer;
- frontend/UI, RBAC, multi-instance, Postgres, deployment, or benchmark scoring;
- removal or renaming of existing legacy compatibility surfaces.

## File Map

### Create

- `benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json`
  - versioned bounded manifest; no raw page bodies.
- `scripts/real_source_proof.py`
  - proof-only manifest validator, seed helper, report builder, and report
    checker.
- `tests/unit/test_real_source_proof.py`
  - manifest/hash/redaction/unit contract tests.
- `tests/integration/test_real_source_proof.py`
  - seed, verification, publication, review, idempotency integration tests.
- `docs/evidence/p2a-real-source-proof.json`
  - generated machine-readable proof report from the real operator run.
- `docs/evidence/p2a-real-source-proof.md`
  - concise human-readable proof summary.
- `docs/operations/real-source-proof-workflow.md`
  - operator workflow using existing service flags and CLI commands.

### Modify

- `docs/README.md`
  - add this implementation plan and final proof report to the docs index.
- `docs/evidence/README.md`
  - add the proof report entry and limitation statement.
- `docs/decisions/evidence-verification-authority.md`
  - add one paragraph clarifying the real-source proof boundary.

### Do Not Modify

- `agent/`
- `api/` schemas, routes, migrations, and repositories, except tests importing
  existing helpers
- `tools/decision_research_agent_tool.py`
- `frontend/`
- LangSmith configuration
- runtime Skills or subagent configuration
- compatibility shims and health compatibility behavior

If implementation appears to require any file in the Do Not Modify list, stop
and return to design review.

## Task 1: Add Manifest Contract and Sample

**Files:**

- Create: `benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json`
- Create: `scripts/real_source_proof.py`
- Create: `tests/unit/test_real_source_proof.py`

- [ ] **Step 1: Write failing manifest validation tests**

Add these tests:

```python
from pathlib import Path
import json

import pytest

from scripts.real_source_proof import (
    RealSourceManifest,
    canonical_manifest_hash,
    load_manifest,
)


def _write_manifest(tmp_path: Path, records: list[dict]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "manifest_id": "talent-agent-hiring-signals-v1",
                "manifest_version": 1,
                "question": "What hiring signals appear in AI Agent roles?",
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _record(sample_id: str, url: str = "https://example.com/careers/agent"):
    return {
        "sample_id": sample_id,
        "source_url": url,
        "source_title": "Agent infrastructure role",
        "organization": "Example",
        "observed_at": "2026-06-23T00:00:00Z",
        "observation": "The role asks for agent infrastructure reliability work.",
        "source_type": "public_job_posting",
    }


def test_manifest_requires_five_to_eight_records(tmp_path):
    path = _write_manifest(tmp_path, [_record("real_source_001")])

    with pytest.raises(ValueError, match="manifest_record_count"):
        load_manifest(path)


def test_manifest_rejects_duplicate_sample_id_and_url(tmp_path):
    path = _write_manifest(
        tmp_path,
        [
            _record("real_source_001"),
            _record("real_source_001", "https://example.com/careers/other"),
            _record("real_source_003"),
            _record("real_source_004"),
            _record("real_source_005"),
        ],
    )

    with pytest.raises(ValueError, match="duplicate_sample_id"):
        load_manifest(path)


def test_manifest_hash_is_ordered_and_stable(tmp_path):
    records = [_record(f"real_source_00{i}") for i in range(1, 6)]
    path = _write_manifest(tmp_path, records)

    manifest = load_manifest(path)

    assert isinstance(manifest, RealSourceManifest)
    assert canonical_manifest_hash(manifest) == canonical_manifest_hash(manifest)
```

- [ ] **Step 2: Run RED**

Run:

```bash
python -m pytest tests/unit/test_real_source_proof.py -q
```

Expected: collection fails because `scripts.real_source_proof` does not exist.

- [ ] **Step 3: Implement minimal manifest models**

Create `scripts/real_source_proof.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class RealSourceRecord:
    sample_id: str
    source_url: str
    source_title: str
    organization: str
    observed_at: str
    observation: str
    source_type: str


@dataclass(frozen=True)
class RealSourceManifest:
    manifest_id: str
    manifest_version: int
    question: str
    records: tuple[RealSourceRecord, ...]


def _require_text(value: object, *, field: str, max_length: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_required")
    normalized = " ".join(value.split())
    if len(normalized) > max_length:
        raise ValueError(f"{field}_too_long")
    return normalized


def _validate_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("source_url_https_required")
    return value


def load_manifest(path: Path) -> RealSourceManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list) or not 5 <= len(records) <= 8:
        raise ValueError("manifest_record_count")
    sample_ids: set[str] = set()
    urls: set[str] = set()
    parsed_records: list[RealSourceRecord] = []
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("manifest_record_invalid")
        sample_id = _require_text(item.get("sample_id"), field="sample_id", max_length=128)
        source_url = _validate_url(_require_text(item.get("source_url"), field="source_url", max_length=500))
        if sample_id in sample_ids:
            raise ValueError("duplicate_sample_id")
        if source_url in urls:
            raise ValueError("duplicate_source_url")
        sample_ids.add(sample_id)
        urls.add(source_url)
        parsed_records.append(
            RealSourceRecord(
                sample_id=sample_id,
                source_url=source_url,
                source_title=_require_text(item.get("source_title"), field="source_title", max_length=200),
                organization=_require_text(item.get("organization"), field="organization", max_length=100),
                observed_at=_require_text(item.get("observed_at"), field="observed_at", max_length=40),
                observation=_require_text(item.get("observation"), field="observation", max_length=500),
                source_type=_require_text(item.get("source_type"), field="source_type", max_length=80),
            )
        )
    organizations = {record.organization for record in parsed_records}
    if len(organizations) < 3:
        raise ValueError("manifest_organization_count")
    return RealSourceManifest(
        manifest_id=_require_text(payload.get("manifest_id"), field="manifest_id", max_length=128),
        manifest_version=int(payload.get("manifest_version")),
        question=_require_text(payload.get("question"), field="question", max_length=300),
        records=tuple(parsed_records),
    )


def canonical_manifest_json(manifest: RealSourceManifest) -> str:
    return json.dumps(
        {
            "manifest_id": manifest.manifest_id,
            "manifest_version": manifest.manifest_version,
            "question": manifest.question,
            "records": [record.__dict__ for record in manifest.records],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_manifest_hash(manifest: RealSourceManifest) -> str:
    return hashlib.sha256(canonical_manifest_json(manifest).encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Add the real manifest**

Create `benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json` with
5-8 records from official public career or ATS pages. Use bounded operator
summaries only. Do not copy long page text.

Acceptable source examples at design time:

- OpenAI official career pages for Agent Infrastructure or Codex Core Agent
- Google official career page for Agentic AI engineering
- LangChain official Ashby career page for Applied AI or related roles

Every record must use `source_type: "public_job_posting"`.

- [ ] **Step 5: Run GREEN**

Run:

```bash
python -m pytest tests/unit/test_real_source_proof.py -q
```

Expected: `3 passed`.

- [ ] **Step 6: Commit**

```bash
git add benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json \
  scripts/real_source_proof.py tests/unit/test_real_source_proof.py
git commit -m "feat(research): add real-source proof manifest"
```

## Task 2: Seed Ordinary Talent Evidence Deterministically

**Files:**

- Modify: `scripts/real_source_proof.py`
- Modify: `tests/unit/test_real_source_proof.py`
- Create: `tests/integration/test_real_source_proof.py`

- [ ] **Step 1: Write RED seed tests**

Add unit tests:

```python
from agent.research import evidence_id_for
from scripts.real_source_proof import (
    build_research_packet_for_manifest,
    evidence_entries_for_manifest,
)


def test_manifest_evidence_starts_as_ordinary_unverified(tmp_path):
    manifest = load_manifest(_write_manifest(tmp_path, [_record(f"real_source_00{i}", f"https://example.com/careers/{i}") for i in range(1, 6)]))

    entries = evidence_entries_for_manifest(
        manifest,
        thread_id="thread-real-proof",
        query_text=manifest.question,
    )

    assert len(entries) == 5
    assert {entry.baseline_verification_origin for entry in entries} == {"none"}
    assert {entry.verification_status for entry in entries} == {"unverified"}
    assert all(entry.tool_name == "real_source_manifest" for entry in entries)


def test_research_packet_references_real_evidence_ids(tmp_path):
    manifest = load_manifest(_write_manifest(tmp_path, [_record(f"real_source_00{i}", f"https://example.com/careers/{i}") for i in range(1, 6)]))
    run_id = "run_real_source"
    entries = evidence_entries_for_manifest(
        manifest,
        thread_id="thread-real-proof",
        query_text=manifest.question,
    )

    packet = build_research_packet_for_manifest(
        manifest=manifest,
        run_id=run_id,
        evidence_entries=entries,
    )

    expected_ids = {
        evidence_id_for(entry.source_url, entry.snippet, run_id=run_id)
        for entry in entries
    }
    actual_ids = {
        evidence_ref
        for finding in packet.findings
        for evidence_ref in finding.evidence_refs
    }
    assert actual_ids == expected_ids
```

- [ ] **Step 2: Run RED**

Run:

```bash
python -m pytest tests/unit/test_real_source_proof.py -q
```

Expected: import failures for the new helper functions.

- [ ] **Step 3: Implement Evidence and packet builders**

Add these functions to `scripts/real_source_proof.py`:

```python
from datetime import datetime, timezone

from agent.research import EvidenceEntry, evidence_id_for
from agent.talent_contracts import ResearchPacket


def evidence_entries_for_manifest(
    manifest: RealSourceManifest,
    *,
    thread_id: str,
    query_text: str,
) -> tuple[EvidenceEntry, ...]:
    created_at = datetime.now(timezone.utc).isoformat()
    return tuple(
        EvidenceEntry(
            thread_id=thread_id,
            query_text=query_text,
            subagent_name="operator_manifest",
            tool_name="real_source_manifest",
            source_url=record.source_url,
            source_identity=record.source_url,
            snippet=record.observation,
            citation_status="cited",
            verification_status="unverified",
            baseline_verification_origin="none",
            created_at=created_at,
        )
        for record in manifest.records
    )


def build_research_packet_for_manifest(
    *,
    manifest: RealSourceManifest,
    run_id: str,
    evidence_entries: tuple[EvidenceEntry, ...],
) -> ResearchPacket:
    findings = []
    claims = []
    for index, (record, entry) in enumerate(zip(manifest.records, evidence_entries), start=1):
        evidence_id = evidence_id_for(entry.source_url, entry.snippet, run_id=run_id)
        finding_id = f"finding-{index}"
        findings.append(
            {
                "finding_id": finding_id,
                "research_question_id": "real_source_question",
                "statement": record.observation,
                "evidence_refs": [evidence_id],
                "sample_scope": "real_source_manifest",
                "confidence": 0.8,
            }
        )
        claims.append(
            {
                "claim_id": f"claim-{index}",
                "text": record.observation,
                "claim_type": "signal",
                "finding_refs": [finding_id],
                "evidence_refs": [evidence_id],
                "confidence": 0.8,
                "citation_status": "cited",
                "verification_status": "unverified",
                "review_status": "pending",
                "conflict_status": "none",
            }
        )
    return ResearchPacket.model_validate(
        {
            "packet_id": "real-source-proof-packet",
            "scope_id": manifest.manifest_id,
            "findings": findings,
            "candidate_claims": claims,
        }
    )
```

- [ ] **Step 4: Write RED integration seed test**

Add:

```python
from api.run_repository import get_run
from scripts.real_source_proof import seed_real_source_run


def test_seed_real_source_run_persists_origin_none(tmp_path):
    manifest_path = _write_manifest(tmp_path, [_record(f"real_source_00{i}", f"https://example.com/careers/{i}") for i in range(1, 6)])

    result = seed_real_source_run(
        manifest_path=manifest_path,
        db_path=str(tmp_path / "tasks.db"),
    )

    run = get_run(db_path=str(tmp_path / "tasks.db"), run_id=result["run_id"])
    assert run["profile_id"] == "talent-hiring-signal"
    assert len(run["evidence"]) == 5
    assert {item["baseline_verification_origin"] for item in run["evidence"]} == {"none"}
    assert run["review_status"] == "required"
    assert run["delivery_status"] == "review_required"
```

- [ ] **Step 5: Implement `seed_real_source_run`**

Use existing repository functions only:

```python
from api.run_repository import create_run, finalize_run_transaction
from api.talent_artifacts import build_talent_artifacts
from api.review_models import checkpoint_thread_id, post_review_segment_id, review_workflow_id


def manifest_scope(manifest: RealSourceManifest) -> dict:
    return {
        "target_roles": ["AI Agent Engineer", "Applied AI Engineer"],
        "target_companies": sorted({record.organization for record in manifest.records}),
        "time_window": {"start": "2026-06-01", "end": "2026-06-23"},
        "declared_samples": [
            {
                "sample_id": record.sample_id,
                "source_type": record.source_type,
                "reference": record.source_url,
            }
            for record in manifest.records
        ],
        "allowed_source_types": ["public_job_posting"],
        "research_questions": ["real_source_question"],
        "requested_outputs": ["decision_brief"],
    }


def seed_real_source_run(*, manifest_path: Path, db_path: str | None = None) -> dict:
    manifest = load_manifest(manifest_path)
    created = create_run(
        db_path=db_path,
        thread_id=f"thread-{manifest.manifest_id}",
        query=manifest.question,
        profile_id="talent-hiring-signal",
        profile_version="1",
        scope=manifest_scope(manifest),
    )
    entries = evidence_entries_for_manifest(
        manifest,
        thread_id=created["thread_id"],
        query_text=manifest.question,
    )
    packet = build_research_packet_for_manifest(
        manifest=manifest,
        run_id=created["run_id"],
        evidence_entries=entries,
    )
    review, _brief, artifacts = build_talent_artifacts(
        run_id=created["run_id"],
        scope=manifest_scope(manifest),
        packets=[packet],
        evidence_entries=list(entries),
        generated_at=datetime.now(timezone.utc),
    )
    workflow_id = review_workflow_id(created["run_id"], review.review_id, review.revision)
    accepted = finalize_run_transaction(
        db_path=db_path,
        run_id=created["run_id"],
        segment_id=created["segment_id"],
        expected_state_version=0,
        allowed_previous_statuses={"pending"},
        execution_status="completed",
        review_status="required",
        delivery_status="review_required",
        evidence_entries=list(entries),
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
    if not accepted:
        raise RuntimeError("seed_run_finalization_failed")
    return {
        "manifest_id": manifest.manifest_id,
        "manifest_hash": canonical_manifest_hash(manifest),
        "run_id": created["run_id"],
        "segment_id": created["segment_id"],
        "review_id": review.review_id,
        "evidence_count": len(entries),
    }
```

- [ ] **Step 6: Run GREEN**

Run:

```bash
python -m pytest \
  tests/unit/test_real_source_proof.py \
  tests/integration/test_real_source_proof.py -q
```

Expected: all new tests pass.

- [ ] **Step 7: Commit**

```bash
git add scripts/real_source_proof.py tests/unit/test_real_source_proof.py \
  tests/integration/test_real_source_proof.py
git commit -m "feat(research): seed real-source proof evidence"
```

## Task 3: Prove Verification, Publication, Review, and Idempotency

**Files:**

- Modify: `scripts/real_source_proof.py`
- Modify: `tests/integration/test_real_source_proof.py`

- [ ] **Step 1: Write integration RED for full lifecycle**

Add:

```python
from api.evidence_verification_models import VerificationDecisionRequest
from api.evidence_verification_repository import accept_verification_decision
from api.publication_repository import finalize_verification_publication, get_current_publication
from api.review_models import ReviewDecisionRequest
from api.review_repository import accept_review_decision, get_review_detail, resolve_review


def test_real_source_lifecycle_requires_human_verification_and_fresh_review(tmp_path):
    manifest_path = _write_manifest(tmp_path, [_record(f"real_source_00{i}", f"https://example.com/careers/{i}") for i in range(1, 6)])
    db_path = str(tmp_path / "tasks.db")
    seeded = seed_real_source_run(manifest_path=manifest_path, db_path=db_path)
    run = get_run(db_path=db_path, run_id=seeded["run_id"])

    for index, evidence in enumerate(run["evidence"], start=1):
        accept_verification_decision(
            db_path=db_path,
            run_id=seeded["run_id"],
            evidence_id=evidence["evidence_id"],
            request=VerificationDecisionRequest(
                verification_id=f"verification-real-{index}",
                evidence_fingerprint=evidence["evidence_fingerprint"],
                expected_revision=0,
                action="verify",
                confirm_source_match=True,
            ),
            actor_fingerprint="operator",
        )

    first = finalize_verification_publication(
        db_path=db_path,
        run_id=seeded["run_id"],
        expected_state_version=get_run(db_path=db_path, run_id=seeded["run_id"])["state_version"],
    )
    second = finalize_verification_publication(
        db_path=db_path,
        run_id=seeded["run_id"],
        expected_state_version=get_run(db_path=db_path, run_id=seeded["run_id"])["state_version"],
    )
    assert second.idempotent_replay is True
    assert second.publication.publication_id == first.publication.publication_id

    detail = get_review_detail(
        db_path=db_path,
        run_id=seeded["run_id"],
        review_id=first.publication.review_id,
    )
    decision = accept_review_decision(
        db_path=db_path,
        run_id=seeded["run_id"],
        review_id=first.publication.review_id,
        request=ReviewDecisionRequest(
            decision_id="decision-real-proof",
            review_revision=detail["review_revision"],
            action="approve",
            expected_state_version=detail["state_version"],
        ),
        actor_fingerprint="operator",
    )
    resolve_review(db_path=db_path, workflow_id=detail["workflow"]["workflow_id"])

    current = get_current_publication(db_path=db_path, run_id=seeded["run_id"])
    assert current is not None
    assert current.status == "ready"
    assert current.is_current is True
```

- [ ] **Step 2: Run RED**

Run:

```bash
python -m pytest tests/integration/test_real_source_proof.py -q
```

Expected: failures until helper return payload and import paths are complete.

- [ ] **Step 3: Add proof completeness checks**

Add to `scripts/real_source_proof.py`:

```python
def assert_complete_proof_report(report: dict) -> None:
    required = {
        "manifest_id",
        "manifest_hash",
        "run_id",
        "source_count",
        "decision_mode",
        "verification_summary",
        "publication",
        "review",
        "artifact_hashes",
        "limits",
    }
    missing = required - set(report)
    if missing:
        raise ValueError(f"proof_report_missing:{','.join(sorted(missing))}")
    if report["decision_mode"] != "human_operator":
        raise ValueError("proof_decision_mode_not_human")
    if report["verification_summary"].get("unresolved_count") != 0:
        raise ValueError("proof_unresolved_verifications")
    if report["publication"].get("status") != "ready":
        raise ValueError("proof_publication_not_ready")
    encoded = json.dumps(report, ensure_ascii=False)
    disallowed = ("API_SECRET", "actor_fingerprint", "request_hash", "/Users/")
    for token in disallowed:
        if token in encoded:
            raise ValueError(f"proof_report_leaks:{token}")
```

- [ ] **Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/integration/test_real_source_proof.py -q
```

Expected: integration lifecycle tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/real_source_proof.py tests/integration/test_real_source_proof.py
git commit -m "test(research): prove real-source verification lifecycle"
```

## Task 4: Add Report Generation and CLI Entry Points

**Files:**

- Modify: `scripts/real_source_proof.py`
- Modify: `tests/unit/test_real_source_proof.py`

- [ ] **Step 1: Write RED for report command behavior**

Add:

```python
def test_report_writer_rejects_private_fields(tmp_path):
    from scripts.real_source_proof import write_atomic_report

    with pytest.raises(ValueError, match="proof_report_leaks"):
        write_atomic_report(
            tmp_path / "proof.json",
            {
                "manifest_id": "x",
                "manifest_hash": "h",
                "run_id": "run",
                "source_count": 5,
                "decision_mode": "human_operator",
                "verification_summary": {"unresolved_count": 0},
                "publication": {"status": "ready"},
                "review": {"status": "approved"},
                "artifact_hashes": {},
                "limits": ["sample only"],
                "actor_fingerprint": "secret",
            },
        )


def test_main_manifest_hash_outputs_bounded_json(tmp_path, capsys):
    manifest_path = _write_manifest(tmp_path, [_record(f"real_source_00{i}", f"https://example.com/careers/{i}") for i in range(1, 6)])
    from scripts.real_source_proof import main

    assert main(["manifest-hash", "--manifest", str(manifest_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["manifest_id"] == "talent-agent-hiring-signals-v1"
    assert re.fullmatch(r"[0-9a-f]{64}", payload["manifest_hash"])
```

- [ ] **Step 2: Run RED**

Run:

```bash
python -m pytest tests/unit/test_real_source_proof.py -q
```

Expected: missing `write_atomic_report` or `main`.

- [ ] **Step 3: Implement bounded entry points**

Add an `argparse` `main()` with these subcommands only:

```text
manifest-hash --manifest PATH
seed --manifest PATH --db-path PATH
build-report --manifest PATH --db-path PATH --run-id ID --output PATH
check-report --report PATH
```

Rules:

- print JSON only;
- return non-zero on validation failure;
- do not read env vars;
- do not call HTTP;
- generate reports deterministically from the manifest and application DB;
- compute UTF-8 byte SHA-256 separately from logical DecisionBrief hashes;
- verify idempotent finalization replay and rebuilt artifact byte stability;
- atomically write reports through `path.with_suffix(path.suffix + ".tmp")`
  then `Path.replace()`.

- [ ] **Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/unit/test_real_source_proof.py -q
```

Expected: unit tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/real_source_proof.py tests/unit/test_real_source_proof.py
git commit -m "feat(research): emit bounded real-source proof reports"
```

## Task 5: Document Operator Workflow and Evidence Boundary

**Files:**

- Create: `docs/operations/real-source-proof-workflow.md`
- Modify: `docs/evidence/README.md`
- Modify: `docs/decisions/evidence-verification-authority.md`
- Modify: `docs/README.md`

- [ ] **Step 1: Write workflow doc**

Create `docs/operations/real-source-proof-workflow.md` with these sections:

```markdown
# Real-Source Proof Workflow

This workflow proves a small sample path. It is not a crawler, benchmark, or
market-coverage claim.

## Prerequisites

- `DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL=true`
- `DECISION_RESEARCH_AGENT_ENABLE_EVIDENCE_VERIFICATION=true`
- `API_SECRET` set for local operator auth
- backend running against a disposable local SQLite database

## Steps

1. Validate the manifest hash.
2. Seed the proof run.
3. Open each public source URL manually.
4. Use `python tools/decision_research_agent_tool.py evidence show ...`.
5. Use `evidence verify --confirm-source-match` or `evidence reject`.
6. Use `evidence finalize`.
7. Use `review show`, `review approve --wait`, and `review wait`.
8. Generate and check the proof report.

## Limits

- A verified record means the persisted observation matched the source at
  decision time.
- It does not prove role availability, market coverage, future truth, or hiring
  outcome.
```

- [ ] **Step 2: Update docs indexes**

Add entries for:

- `docs/operations/real-source-proof-workflow.md`
- `docs/evidence/p2a-real-source-proof.json`
- `docs/evidence/p2a-real-source-proof.md`
- this plan file

- [ ] **Step 3: Update authority ADR**

Add one paragraph:

```markdown
P2A PR3 adds a bounded real-source proof. It uses ordinary Evidence with
baseline origin `none`, then relies on the existing append-only human decision
ledger and immutable snapshot projection to establish `human` authority. The
proof report is evidence of workflow execution for a small public sample, not a
source archive or market coverage claim.
```

- [ ] **Step 4: Commit**

```bash
git add docs/operations/real-source-proof-workflow.md docs/evidence/README.md \
  docs/decisions/evidence-verification-authority.md docs/README.md
git commit -m "docs(research): document real-source proof workflow"
```

## Task 6: Run Real Operator Proof and Commit Reports

**Files:**

- Create: `docs/evidence/p2a-real-source-proof.json`
- Create: `docs/evidence/p2a-real-source-proof.md`
- Modify: `docs/evidence/README.md`

- [ ] **Step 1: Start local controlled runtime**

Use a disposable DB and canonical env vars:

```bash
export DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL=true
export DECISION_RESEARCH_AGENT_ENABLE_EVIDENCE_VERIFICATION=true
export API_SECRET="<local secret>"
export TASKS_DB_PATH="$(pwd)/.tmp/real-source-proof/tasks.db"
export DECISION_RESEARCH_AGENT_CHECKPOINT_DB_PATH="$(pwd)/.tmp/real-source-proof/checkpoints.db"
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: Validate manifest and seed run**

In a second shell:

```bash
python scripts/real_source_proof.py manifest-hash \
  --manifest benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json

python scripts/real_source_proof.py seed \
  --manifest benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json \
  --db-path .tmp/real-source-proof/tasks.db
```

Expected: JSON output with `manifest_hash`, `run_id`, and `evidence_count`.

- [ ] **Step 3: Manually inspect and decide every Evidence record**

For each record:

```bash
python tools/decision_research_agent_tool.py evidence show \
  --run-id "$RUN_ID" \
  --evidence-id "$EVIDENCE_ID"
```

Then either:

```bash
python tools/decision_research_agent_tool.py evidence verify \
  --run-id "$RUN_ID" \
  --evidence-id "$EVIDENCE_ID" \
  --confirm-source-match
```

or:

```bash
printf '%s\n' "source unavailable during proof" | \
python tools/decision_research_agent_tool.py evidence reject \
  --run-id "$RUN_ID" \
  --evidence-id "$EVIDENCE_ID" \
  --reason-code source_unavailable \
  --reason-stdin
```

- [ ] **Step 4: Finalize and approve fresh review**

```bash
python tools/decision_research_agent_tool.py evidence finalize --run-id "$RUN_ID"
python tools/decision_research_agent_tool.py review show --run-id "$RUN_ID"
python tools/decision_research_agent_tool.py review approve --run-id "$RUN_ID" --wait
python tools/decision_research_agent_tool.py review wait --run-id "$RUN_ID"
```

Expected: final review status is `approved` and current publication is `ready`.

- [ ] **Step 5: Generate reports**

Use the implemented proof-only command to write:

```text
docs/evidence/p2a-real-source-proof.json
docs/evidence/p2a-real-source-proof.md
```

```bash
python scripts/real_source_proof.py build-report \
  --manifest benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json \
  --db-path .tmp/real-source-proof/tasks.db \
  --run-id "$RUN_ID" \
  --output docs/evidence/p2a-real-source-proof.json
```

The JSON report must pass:

```bash
python scripts/real_source_proof.py check-report \
  --report docs/evidence/p2a-real-source-proof.json
```

- [ ] **Step 6: Run final validation**

Run:

```bash
python -m pytest \
  tests/unit/test_real_source_proof.py \
  tests/integration/test_real_source_proof.py -q

python -m pytest -q

python scripts/run_durable_hitl_gate.py

python -m pytest tests/integration/test_evidence_verification_container.py -q

git diff --check
```

Expected:

- focused proof tests pass;
- full backend suite passes;
- durable HITL gate reports `PASS`, `13/13`;
- controlled Docker compatibility test passes;
- diff check passes.

- [ ] **Step 7: Commit**

```bash
git add docs/evidence/p2a-real-source-proof.json \
  docs/evidence/p2a-real-source-proof.md docs/evidence/README.md
git commit -m "docs(research): publish bounded real-source proof"
```

## Final Pre-PR Checklist

- [ ] `git status --short` is empty.
- [ ] `git log --oneline --decorate -6` shows focused commits only.
- [ ] No committed report contains secrets, local absolute paths, actor
  fingerprints, request hashes, traceback text, SQLite file contents, or raw
  source-page bodies.
- [ ] New commands, docs, and reports use canonical project identity only.
- [ ] Feature flags remain disabled by default.
- [ ] No code change touches existing compatibility shims or health
  compatibility behavior.
- [ ] PR body says this is a bounded proof and not a crawler, source archive,
  market benchmark, or production verification system.
