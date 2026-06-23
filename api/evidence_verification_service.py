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
