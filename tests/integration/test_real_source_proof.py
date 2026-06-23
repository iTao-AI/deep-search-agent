from pathlib import Path
import json
import sqlite3

from api.run_repository import get_run
from scripts.real_source_proof import seed_real_source_run


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
    manifest_path = _write_manifest(
        tmp_path,
        [
            _record(f"real_source_00{i}", f"https://example.com/careers/{i}")
            for i in range(1, 6)
        ],
    )
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
