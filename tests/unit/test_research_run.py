"""Tests for research run evidence and quality contracts."""
import json


class TestResearchEvidence:
    def test_mark_cited_evidence_matches_report_urls(self):
        from agent.research import EvidenceEntry, mark_cited_evidence

        entries = [
            EvidenceEntry(
                thread_id="thread-001",
                query_text="query",
                subagent_name="network_search",
                tool_name="tavily_search",
                source_url="https://example.com/source",
                snippet="source summary",
            )
        ]

        marked = mark_cited_evidence(
            entries,
            "Final report cites https://example.com/source for the claim.",
        )

        assert marked[0].citation_status == "cited"

    def test_quality_gate_fails_fallback_report(self, tmp_path):
        from agent.research import evaluate_report_quality

        fallback_report = tmp_path / "fallback_report.md"
        fallback_report.write_text("fallback", encoding="utf-8")

        quality = evaluate_report_quality(
            report_path=fallback_report,
            fallback_used=True,
            evidence_entries=[],
            token_usage={"total_tokens": 10},
            diagnostics=["tool:tavily_search"],
        )

        assert quality.status == "failed"
        assert any(issue["code"] == "fallback_report" for issue in quality.issues)


class TestResearchPersistence:
    def test_save_and_get_research_run_with_evidence(self, tmp_path):
        from api.persistence import (
            get_research_run_with_evidence,
            init_db,
            save_research_run,
            replace_evidence_entries,
        )
        from agent.research import EvidenceEntry

        db_path = str(tmp_path / "tasks.db")
        init_db(db_path)
        save_research_run(
            db_path=db_path,
            thread_id="thread-001",
            query="query",
            status="completed",
            started_at="2026-06-08T00:00:00+00:00",
            completed_at="2026-06-08T00:01:00+00:00",
            output_path="/tmp/report.md",
            fallback_used=False,
            assistant_calls=2,
            tool_starts=3,
            diagnostics_json=json.dumps(["tool:tavily_search"]),
            token_usage_json=json.dumps({"total_tokens": 123}),
            quality_report_json=json.dumps({"status": "passed", "issues": []}),
        )
        replace_evidence_entries(
            db_path,
            "thread-001",
            [
                EvidenceEntry(
                    thread_id="thread-001",
                    query_text="query",
                    subagent_name="network_search",
                    tool_name="tavily_search",
                    source_url="https://example.com/source",
                    snippet="source summary",
                    citation_status="cited",
                    verification_status="unverified",
                )
            ],
        )

        result = get_research_run_with_evidence(db_path, "thread-001")

        assert result["thread_id"] == "thread-001"
        assert result["quality_report"]["status"] == "passed"
        assert result["token_usage"]["total_tokens"] == 123
        assert result["evidence"][0]["source_url"] == "https://example.com/source"
        assert result["evidence"][0]["citation_status"] == "cited"
