"""Canonical run result construction and resolution.

This module is application-owned: it builds and resolves deliverable result
artifacts from persisted ResearchRun state without giving framework harnesses
delivery authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from pathlib import PurePosixPath
from typing import Any

from agent.run_result import ExecutionOutcome


CANONICAL_RESULT_ARTIFACT_ID = "research-report.md"
CANONICAL_RESULT_PATH = PurePosixPath("/workspace/research-report.md")
MAX_RESULT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ResolvedRunResult:
    run_id: str
    execution_status: str
    delivery_status: str
    artifact: dict[str, str]


def build_generic_result_artifact(
    outcome: ExecutionOutcome,
    *,
    generated_at: datetime | None = None,
) -> dict[str, str]:
    """Build the immutable generic result artifact for one completed run."""
    candidate = outcome.report_candidate
    if (
        candidate is not None
        and getattr(candidate, "path", None) == CANONICAL_RESULT_PATH
        and _is_non_empty_bounded_text(getattr(candidate, "content", ""))
    ):
        return _artifact(
            kind="research_report_markdown",
            content=candidate.content,
        )

    return _artifact(
        kind="research_report_fallback_markdown",
        content=_fallback_report(outcome, generated_at=generated_at),
    )


def _artifact(*, kind: str, content: str) -> dict[str, str]:
    return {
        "artifact_id": CANONICAL_RESULT_ARTIFACT_ID,
        "kind": kind,
        "media_type": "text/markdown",
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def _is_non_empty_bounded_text(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    return len(value.encode("utf-8")) <= MAX_RESULT_BYTES


def _fallback_report(
    outcome: ExecutionOutcome,
    *,
    generated_at: datetime | None,
) -> str:
    timestamp = (generated_at or datetime.now(timezone.utc)).isoformat()
    bounded_text = _safe_excerpt(outcome.last_agent_text)
    if not bounded_text:
        bounded_text = "No canonical report was produced by the agent."
    lines = [
        "# Fallback Report",
        "",
        "A canonical `/workspace/research-report.md` artifact was not available.",
        "",
        f"- Run ID: {outcome.run_id or 'unknown'}",
        f"- Generated at: {timestamp}",
        "",
        "## Last Agent Text",
        "",
        bounded_text,
        "",
    ]
    return "\n".join(lines)


_ABSOLUTE_PATH_RE = re.compile(r"(?:(?:/[A-Za-z0-9._ -]+){2,})")


def _safe_excerpt(value: str, *, limit: int = 4000) -> str:
    if not value:
        return ""
    text = value.replace("Traceback", "[redacted]").replace(
        "traceback",
        "[redacted]",
    )
    text = _ABSOLUTE_PATH_RE.sub("[redacted-path]", text)
    text = text.strip()
    if len(text) > limit:
        text = f"{text[:limit]}…"
    return text
