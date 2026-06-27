from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def test_external_services_reference_matches_resilience_contract() -> None:
    text = (ROOT / "docs/reference/external-services.md").read_text(encoding="utf-8")

    required = [
        "OpenAI-compatible provider (default DeepSeek)",
        "15s",
        "60s",
        "10s",
        "30s",
        "120s",
        "3 total attempts",
        "terminal on timeout",
        "SELECT-only textual guard",
        "table whitelist",
        "least-privilege read-only account",
        "not an AST or parameter-binding authority",
    ]
    forbidden = [
        "~99%",
        "流式响应无超时",
        "SQL 注入: 由子 Agent prompt 约束",
        "无（待改进，Phase 7b）",
    ]

    for phrase in required:
        assert phrase in text
    for phrase in forbidden:
        assert phrase not in text


def test_current_public_surface_omits_internal_milestone_codes() -> None:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "*.md"],
        capture_output=True,
        check=True,
    )
    paths = [
        ROOT / raw.decode("utf-8")
        for raw in completed.stdout.split(b"\0")
        if raw
    ]
    paths.extend(
        [
            ROOT / ".env.example",
            ROOT / "api/review_api.py",
            ROOT / "scripts/evidence_verification_container_fixture.py",
        ]
    )
    pattern = re.compile(r"\b(?:P1A|P1B|P1C|P2A|Phase 7b)\b")
    violations = [
        path.relative_to(ROOT).as_posix()
        for path in paths
        if pattern.search(path.read_text(encoding="utf-8"))
    ]

    assert violations == []


def test_real_source_proof_uses_canonical_public_paths() -> None:
    assert (ROOT / "docs/evidence/real-source-proof.md").is_file()
    assert (ROOT / "docs/evidence/real-source-proof.json").is_file()
    assert not (ROOT / "docs/evidence/p2a-real-source-proof.md").exists()
    assert not (ROOT / "docs/evidence/p2a-real-source-proof.json").exists()

    completed = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "grep",
            "-n",
            "p2a-real-source-proof",
            "--",
            ":!tests/**",
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1, completed.stdout


def test_verification_docs_distinguish_runtime_from_operator_proof() -> None:
    paths = [
        ROOT / "docs/operations/evidence-verification-workflow.md",
        ROOT / "docs/decisions/evidence-verification-authority.md",
    ]

    assert (ROOT / "docs/operations/real-source-proof-workflow.md").is_file()
    for path in paths:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "adds no real-source proof" not in text
        assert "operator-driven real-source proof" in text
        assert "does not automatically retrieve sources" in text
        assert "not a runtime crawler" in text
        assert "not automatic truth verification" in text
        assert "not a production-readiness claim" in text


def test_cors_reference_is_canonical_and_deny_by_default() -> None:
    text = (ROOT / "docs/reference/api-contract.md").read_text(encoding="utf-8")

    assert "DECISION_RESEARCH_AGENT_CORS_ALLOWED_ORIGIN" in text
    assert "CORS is deny-by-default" in text
    assert "frontend-specific setting is not a compatibility alias" in text


def test_release_verification_uses_bounded_backend_readiness() -> None:
    paths = [
        ROOT / "docs/releases/v0.1.0.md",
        ROOT
        / "docs/superpowers/plans/2026-06-27-v0-1-0-release-presentation-cleanup.md",
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in [
            "for attempt in $(seq 1 60)",
            "--max-time 2",
            'if [ "$ready" -ne 1 ]',
            "docker compose logs --no-color backend mysql",
            "--max-time 5",
        ]:
            assert phrase in text, f"{phrase!r} missing from {path}"


def test_changelog_marks_v010_as_pending_release() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "## [0.1.0] - Pending release" in changelog
    assert not re.search(r"^## \[0\.1\.0\] - \d{4}-\d{2}-\d{2}$", changelog, re.MULTILINE)
