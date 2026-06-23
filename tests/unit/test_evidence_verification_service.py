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
