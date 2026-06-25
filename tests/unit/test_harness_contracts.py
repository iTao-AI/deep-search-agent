from dataclasses import FrozenInstanceError
from pathlib import PurePosixPath

import pytest

from agent.harness_contracts import HarnessRequest, ReportCandidate


def test_harness_request_is_immutable():
    request = HarnessRequest(
        query="research agent hiring signals",
        thread_id="thread_1",
        run_id="run_1",
        segment_id="segment_1",
        profile_id="generic",
        scope={},
        trace_metadata={"research_run_id": "run_1"},
    )

    with pytest.raises(FrozenInstanceError):
        request.run_id = "other"


def test_report_candidate_accepts_only_virtual_workspace_path():
    candidate = ReportCandidate(
        path=PurePosixPath("/workspace/research-report.md"),
        content="# Report",
    )

    assert candidate.path.as_posix() == "/workspace/research-report.md"
