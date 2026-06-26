"""Tests for task finalization and fallback reports."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import pytest

from agent.run_result import AgentRunResult
from agent.harness_contracts import ReportCandidate
from agent.research import EvidenceEntry


@pytest.fixture
def task_db(tmp_path, monkeypatch):
    db_path = tmp_path / "tasks.db"
    monkeypatch.setenv("TASKS_DB_PATH", str(db_path))
    return str(db_path)


def _save_task(thread_id: str, query: str):
    from api.persistence import save_task

    save_task(thread_id=thread_id, query=query, status="running")


class TestTaskFinalizer:
    def test_finalizer_module_does_not_read_shared_context(self):
        import inspect
        import api.task_finalizer as task_finalizer

        source = inspect.getsource(task_finalizer)

        assert "_collect_shared_context_evidence" not in source
        assert "shared_context_tools" not in source

    def test_finalizer_uses_report_candidate_without_scanning_session_dir(
        self,
        tmp_path,
        task_db,
        monkeypatch,
    ):
        from api.task_finalizer import finalize_task_run

        thread_id = "finalizer-report-candidate"
        _save_task(thread_id, "query")
        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=tmp_path / f"session_{thread_id}",
            report_candidate=ReportCandidate(
                path=PurePosixPath("/workspace/research-report.md"),
                content="# Report\n",
            ),
        )

        monkeypatch.setattr(
            Path,
            "glob",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("session_dir scan")
            ),
        )
        monkeypatch.setattr(
            Path,
            "iterdir",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("session_dir scan")
            ),
        )
        monkeypatch.setattr(
            os,
            "scandir",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("session_dir scan")
            ),
        )

        finalized = finalize_task_run(result)

        assert finalized.status == "completed"
        assert Path(finalized.output_path).read_text(encoding="utf-8") == "# Report\n"

    def test_ignores_existing_host_markdown_without_report_candidate(
        self,
        tmp_path,
        task_db,
    ):
        from api.persistence import get_task
        from api.task_finalizer import finalize_task_run

        thread_id = "finalizer-existing"
        session_dir = tmp_path / f"session_{thread_id}"
        session_dir.mkdir()
        old_report = session_dir / "old.md"
        new_report = session_dir / "new.md"
        fallback = session_dir / "fallback_report.md"
        old_report.write_text("old", encoding="utf-8")
        new_report.write_text("new", encoding="utf-8")
        fallback.write_text("fallback must be ignored", encoding="utf-8")
        old_time = 1_700_000_000
        new_time = 1_700_000_100
        old_report.touch()
        new_report.touch()
        fallback.touch()
        import os
        os.utime(old_report, (old_time, old_time))
        os.utime(new_report, (new_time, new_time))
        os.utime(fallback, (new_time + 100, new_time + 100))
        _save_task(thread_id, "query")

        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=session_dir,
            last_agent_text="agent text",
        )
        finalization = finalize_task_run(result)

        task = get_task(thread_id=thread_id)
        assert finalization.status == "completed_with_fallback"
        assert finalization.fallback_used is True
        assert finalization.output_path.endswith("fallback_report.md")
        assert task["status"] == "completed_with_fallback"
        assert task["output_path"].endswith("fallback_report.md")
        assert json.loads(task["token_usage_json"])["total_tokens"] == 0

    def test_writes_fallback_report_when_no_markdown_exists(self, tmp_path, task_db):
        from api.persistence import get_task
        from api.task_finalizer import finalize_task_run

        thread_id = "finalizer-fallback"
        session_dir = tmp_path / f"session_{thread_id}"
        session_dir.mkdir()
        _save_task(thread_id, "query")

        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=session_dir,
            last_agent_text="last visible agent text",
            assistant_calls=2,
            tool_starts=1,
            diagnostics=["tool:tavily_search"],
        )
        finalization = finalize_task_run(result)

        fallback_path = session_dir / "fallback_report.md"
        task = get_task(thread_id=thread_id)
        content = fallback_path.read_text(encoding="utf-8")
        assert finalization.status == "completed_with_fallback"
        assert finalization.fallback_used is True
        assert finalization.output_path == str(fallback_path)
        assert task["status"] == "completed_with_fallback"
        assert task["output_path"] == str(fallback_path)
        assert "# Fallback Report" in content
        assert "query" in content
        assert "last visible agent text" in content
        assert "tool:tavily_search" in content

    def test_ignores_empty_markdown_report(self, tmp_path, task_db):
        from api.task_finalizer import finalize_task_run

        thread_id = "finalizer-empty"
        session_dir = tmp_path / f"session_{thread_id}"
        session_dir.mkdir()
        (session_dir / "empty.md").write_text("", encoding="utf-8")
        _save_task(thread_id, "query")

        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=session_dir,
            last_agent_text="agent text",
        )
        finalization = finalize_task_run(result)

        assert finalization.status == "completed_with_fallback"
        assert finalization.output_path.endswith("fallback_report.md")

    def test_ignores_markdown_older_than_run_start(self, tmp_path, task_db):
        from api.task_finalizer import finalize_task_run

        thread_id = "finalizer-stale"
        session_dir = tmp_path / f"session_{thread_id}"
        session_dir.mkdir()
        stale_report = session_dir / "uploaded_input.md"
        stale_report.write_text("old uploaded markdown", encoding="utf-8")
        _save_task(thread_id, "query")

        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=session_dir,
            started_at=datetime.now(timezone.utc),
            last_agent_text="agent text",
        )
        finalization = finalize_task_run(result)

        assert finalization.status == "completed_with_fallback"
        assert finalization.output_path.endswith("fallback_report.md")
        assert finalization.output_path != str(stale_report)

    def test_fallback_task_result_is_string_payload(self, tmp_path, task_db, monkeypatch):
        import api.task_finalizer as task_finalizer

        thread_id = "finalizer-string-payload"
        session_dir = tmp_path / f"session_{thread_id}"
        session_dir.mkdir()
        _save_task(thread_id, "query")
        captured_results = []

        monkeypatch.setattr(
            task_finalizer.monitor,
            "report_task_result",
            captured_results.append,
        )

        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=session_dir,
            started_at=datetime.now(timezone.utc),
            last_agent_text="agent text",
        )
        task_finalizer.finalize_task_run(result)

        assert captured_results
        assert isinstance(captured_results[0], str)

    def test_persists_research_run_and_marks_cited_evidence(self, tmp_path, task_db):
        from api.persistence import get_research_run_with_evidence
        from api.task_finalizer import finalize_task_run

        thread_id = "finalizer-research-run"
        session_dir = tmp_path / f"session_{thread_id}"
        session_dir.mkdir()
        report = session_dir / "report.md"
        report.write_text(
            "The report cites https://example.com/source as evidence.",
            encoding="utf-8",
        )
        _save_task(thread_id, "query")

        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=session_dir,
            last_agent_text="agent text",
            assistant_calls=1,
            tool_starts=1,
            diagnostics=["tool:tavily_search"],
            report_candidate=ReportCandidate(
                path=PurePosixPath("/workspace/research-report.md"),
                content=(
                    "The report cites https://example.com/source as evidence."
                ),
            ),
            evidence_entries=[
                EvidenceEntry(
                    thread_id=thread_id,
                    query_text="query",
                    subagent_name="network_search",
                    tool_name="tavily_search",
                    source_url="https://example.com/source",
                    snippet="source summary",
                )
            ],
        )

        finalize_task_run(result)
        research_run = get_research_run_with_evidence(thread_id=thread_id)

        assert research_run["thread_id"] == thread_id
        assert research_run["status"] == "completed"
        assert research_run["quality_report"]["status"] == "passed"
        assert research_run["assistant_calls"] == 1
        assert research_run["tool_starts"] == 1
        assert research_run["evidence"][0]["citation_status"] == "cited"

    def test_finalize_does_not_mark_task_completed_when_research_persistence_fails(
        self, tmp_path, task_db, monkeypatch
    ):
        from api.persistence import get_task
        import api.task_finalizer as task_finalizer

        thread_id = "finalizer-persistence-failure"
        session_dir = tmp_path / f"session_{thread_id}"
        session_dir.mkdir()
        report = session_dir / "report.md"
        report.write_text("report", encoding="utf-8")
        _save_task(thread_id, "query")

        def fail_persist(*args, **kwargs):
            raise RuntimeError("research persistence failed")

        monkeypatch.setattr(task_finalizer, "persist_research_run", fail_persist)

        result = AgentRunResult(
            thread_id=thread_id,
            query="query",
            session_dir=session_dir,
            last_agent_text="agent text",
            report_candidate=ReportCandidate(
                path=PurePosixPath("/workspace/research-report.md"),
                content="report",
            ),
        )

        with pytest.raises(RuntimeError, match="research persistence failed"):
            task_finalizer.finalize_task_run(result)

        task = get_task(thread_id=thread_id)
        assert task["status"] == "running"
        assert task["output_path"] is None
