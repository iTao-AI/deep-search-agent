import asyncio
from pathlib import Path
import json
import sqlite3

from api.evidence_verification_models import VerificationDecisionRequest
from api.evidence_verification_repository import accept_verification_decision
from api.publication_repository import (
    finalize_verification_publication,
    get_current_publication,
    migrate_publication_with_backup,
)
from api.review_models import ReviewDecisionRequest
from api.review_repository import (
    accept_review_decision,
    get_review_detail,
)
from api.review_worker import ReviewWorker
from api.run_repository import get_run
from scripts.real_source_proof import (
    assert_complete_proof_report,
    build_proof_report,
    main,
    seed_real_source_run,
)


def _write_manifest(tmp_path: Path, records: list[dict]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "manifest_id": "talent-agent-hiring-signals-v1",
                "manifest_version": 1,
                "question": "What hiring signals appear in AI Agent roles?",
                "allowed_hosts": [
                    "jobs.ashbyhq.com",
                    "openai.com",
                    "www.google.com",
                ],
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _record(
    sample_id: str,
    url: str = "https://openai.com/careers/agent",
    organization: str = "OpenAI",
):
    return {
        "sample_id": sample_id,
        "source_url": url,
        "source_title": "Agent infrastructure role",
        "organization": organization,
        "observed_at": "2026-06-23T00:00:00Z",
        "observation": "The role asks for agent infrastructure reliability work.",
        "source_type": "public_job_posting",
    }


def _records(count: int = 5) -> list[dict]:
    sources = (
        ("OpenAI", "https://openai.com/careers"),
        ("LangChain", "https://jobs.ashbyhq.com/langchain"),
        ("Google", "https://www.google.com/about/careers"),
    )
    return [
        _record(
            f"real_source_{index:03d}",
            f"{sources[(index - 1) % len(sources)][1]}/{index}",
            sources[(index - 1) % len(sources)][0],
        )
        for index in range(1, count + 1)
    ]


def _baseline_origins(db_path: str, run_id: str) -> set[str]:
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT baseline_verification_origin
            FROM evidence_entries_v2
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        connection.close()


def test_seed_real_source_run_persists_origin_none(tmp_path):
    manifest_path = _write_manifest(tmp_path, _records())
    db_path = str(tmp_path / "tasks.db")

    result = seed_real_source_run(
        manifest_path=manifest_path,
        db_path=db_path,
    )

    run = get_run(db_path=db_path, run_id=result["run_id"])
    assert run["profile_id"] == "talent-hiring-signal"
    assert len(run["evidence"]) == 5
    assert _baseline_origins(db_path, result["run_id"]) == {"none"}
    assert run["review_status"] == "required"
    assert run["delivery_status"] == "review_required"


async def _complete_lifecycle(tmp_path, *, reject_first: bool = False):
    manifest_path = _write_manifest(tmp_path, _records())
    db_path = str(tmp_path / "tasks.db")
    seeded = seed_real_source_run(manifest_path=manifest_path, db_path=db_path)
    migrate_publication_with_backup(
        db_path=db_path,
        backup_path=str(tmp_path / "backup.db"),
    )
    worker = ReviewWorker(
        db_path=db_path,
        checkpoint_path=str(tmp_path / "checkpoints.db"),
        worker_id="real-source-proof-worker",
    )
    assert await worker.run_once() is True
    run = get_run(db_path=db_path, run_id=seeded["run_id"])

    for index, evidence in enumerate(run["evidence"], start=1):
        action = "reject" if reject_first and index == 1 else "verify"
        accept_verification_decision(
            db_path=db_path,
            run_id=seeded["run_id"],
            evidence_id=evidence["evidence_id"],
            request=VerificationDecisionRequest(
                verification_id=f"verification-real-{index}",
                evidence_fingerprint=evidence["evidence_fingerprint"],
                expected_revision=0,
                action=action,
                confirm_source_match=action == "verify",
                reason_code=(
                    "content_mismatch" if action == "reject" else None
                ),
                reason_note=(
                    "Synthetic rejection for lifecycle coverage."
                    if action == "reject"
                    else None
                ),
            ),
            actor_fingerprint="operator",
        )

    first = finalize_verification_publication(
        db_path=db_path,
        run_id=seeded["run_id"],
        expected_state_version=get_run(db_path=db_path, run_id=seeded["run_id"])[
            "state_version"
        ],
    )
    second = finalize_verification_publication(
        db_path=db_path,
        run_id=seeded["run_id"],
        expected_state_version=get_run(db_path=db_path, run_id=seeded["run_id"])[
            "state_version"
        ],
    )
    assert second.idempotent_replay is True
    assert second.publication.publication_id == first.publication.publication_id

    assert await worker.run_once() is True
    detail = get_review_detail(
        db_path=db_path,
        run_id=seeded["run_id"],
        review_id=first.publication.review_id,
    )
    accepted = accept_review_decision(
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
    assert accepted.idempotent_replay is False
    assert await worker.run_once() is True

    current = get_current_publication(db_path=db_path, run_id=seeded["run_id"])
    assert current is not None
    assert current.status == "ready"
    assert current.is_current is True
    return manifest_path, db_path, seeded


def test_real_source_lifecycle_requires_human_verification_and_fresh_review(tmp_path):
    manifest_path, db_path, seeded = asyncio.run(_complete_lifecycle(tmp_path))

    report = build_proof_report(
        manifest_path=manifest_path,
        db_path=db_path,
        run_id=seeded["run_id"],
    )
    assert_complete_proof_report(report)
    assert report["idempotency"]["finalize_replay"] is True
    assert report["byte_stability"]["stable"] is True
    assert {
        artifact["media_type"] for artifact in report["artifact_hashes"].values()
    } == {"application/json", "text/markdown"}
    assert len(
        {
            artifact["byte_sha256"]
            for artifact in report["artifact_hashes"].values()
        }
    ) == 2


def test_real_source_report_preserves_explicit_rejection(tmp_path):
    manifest_path, db_path, seeded = asyncio.run(
        _complete_lifecycle(tmp_path, reject_first=True)
    )

    report = build_proof_report(
        manifest_path=manifest_path,
        db_path=db_path,
        run_id=seeded["run_id"],
    )

    assert_complete_proof_report(report)
    rejected = [
        decision
        for decision in report["source_decisions"]
        if decision["action"] == "reject"
    ]
    assert len(rejected) == 1
    assert rejected[0]["verification_state"] == "rejected"
    assert rejected[0]["reason_code"] == "content_mismatch"
    assert report["verification_summary"]["state_counts"] == {
        "rejected": 1,
        "verified": 4,
    }


def test_build_report_command_writes_checked_report(tmp_path, capsys):
    manifest_path, db_path, seeded = asyncio.run(_complete_lifecycle(tmp_path))
    output_path = tmp_path / "proof.json"

    assert (
        main(
            [
                "build-report",
                "--manifest",
                str(manifest_path),
                "--db-path",
                db_path,
                "--run-id",
                seeded["run_id"],
                "--output",
                str(output_path),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "written"
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert_complete_proof_report(report)
