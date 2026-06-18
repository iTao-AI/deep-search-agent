from pathlib import Path
import subprocess
import sys

from tools import decision_research_agent_tool as canonical
from tools import deep_search_agent_tool as legacy


PROJECT_ROOT = Path(__file__).parents[2]
DESCRIPTION = "Decision Research Agent integration tool"


def test_legacy_module_reexports_canonical_public_contract():
    assert legacy.ToolClientError is canonical.ToolClientError
    assert legacy.ToolConfig is canonical.ToolConfig
    assert legacy.healthcheck is canonical.healthcheck
    assert legacy.main is canonical.main


def test_canonical_and_legacy_scripts_run_from_repository_root():
    for script_name in (
        "decision_research_agent_tool.py",
        "deep_search_agent_tool.py",
    ):
        result = subprocess.run(
            [sys.executable, f"tools/{script_name}", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert DESCRIPTION in result.stdout


def test_canonical_and_legacy_scripts_run_outside_repository(tmp_path):
    for script_name in (
        "decision_research_agent_tool.py",
        "deep_search_agent_tool.py",
    ):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "tools" / script_name),
                "--help",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert DESCRIPTION in result.stdout
