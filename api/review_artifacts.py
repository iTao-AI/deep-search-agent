from __future__ import annotations

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
    """Resolve review metadata without changing evidence verification state."""
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
