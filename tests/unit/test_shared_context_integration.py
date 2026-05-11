"""Phase 3: SharedContext 集成回归测试"""
import pytest
import os
import sys
import subprocess


class TestSharedContextIntegration:
    """验证 SharedContext 集成不破坏现有功能"""

    def test_shared_context_in_main_agent(self):
        """main_agent.py 应该能导入并初始化 shared_context"""
        result = subprocess.run(
            [sys.executable, "-c", """
import os
os.environ["OPENAI_API_KEY"] = "test"
os.environ["OPENAI_BASE_URL"] = "http://test"
os.environ["LLM_QWEN_MAX"] = "test"
from unittest.mock import patch, MagicMock
with patch('agent.main_agent.create_deep_agent', return_value=MagicMock()):
    with patch('tavily.TavilyClient', return_value=MagicMock()):
        with patch('ragflow_sdk.RAGFlow', return_value=MagicMock()):
            from agent.main_agent import shared_context
            assert shared_context is not None
            from agent.shared_context import SharedContext
            assert isinstance(shared_context, SharedContext)
            print("OK")
"""],
            capture_output=True, text=True, cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"shared_context not accessible from main_agent:\n{result.stderr}"
        assert "OK" in result.stdout

    def test_shared_context_isolation_from_existing_context(self):
        """SharedContext 不应与现有的 api/context.py 冲突"""
        result = subprocess.run(
            [sys.executable, "-c", """
from agent.shared_context import SharedContext
from api.context import set_session_context, reset_session_context, get_session_context

ctx = SharedContext()
ctx.publish_fact("t1", "fact1", "s1", "t1")
token = set_session_context("/test/path")
assert get_session_context() == "/test/path"
reset_session_context(token)
print("OK")
"""],
            capture_output=True, text=True, cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"ContextVar conflict:\n{result.stderr}"
        assert "OK" in result.stdout
