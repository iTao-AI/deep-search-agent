"""Phase C: RAGFlow 工具重构测试 — session 清理"""
import pytest
import sys
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def _mock_dependencies():
    """Mock ragflow SDK and dependencies"""
    for mod in ["ragflow_sdk", "dotenv", "api.monitor", "tools.ragflow_tools"]:
        sys.modules.pop(mod, None)

    mock_ragflow_mod = MagicMock()
    mock_ragflow_sdk = MagicMock()
    mock_ragflow_mod.RAGFlow = mock_ragflow_sdk
    sys.modules["ragflow_sdk"] = mock_ragflow_mod
    sys.modules["api.monitor"] = MagicMock()
    sys.modules["api.monitor"].monitor = MagicMock()

    import os
    os.environ["RAGFLOW_API_KEY"] = "test_key"
    os.environ["RAGFLOW_API_URL"] = "http://localhost:8080"

    yield

    for mod in ["ragflow_sdk", "dotenv", "api.monitor", "tools.ragflow_tools"]:
        sys.modules.pop(mod, None)


class TestRAGFlowTools:
    """测试 RAGFlow 工具的 session 清理和错误返回"""

    def test_get_assistant_list_returns_string(self):
        """正常应返回格式化的字符串"""
        mock_rag = MagicMock()
        mock_chat = MagicMock()
        mock_chat.name = "TestBot"
        mock_chat.description = "Test Desc"
        mock_chat.datasets = []
        mock_rag.list_chats.return_value = [mock_chat]

        with patch("tools.ragflow_tools.RAGFlow", return_value=mock_rag):
            from tools.ragflow_tools import get_assistant_list
            result = get_assistant_list.invoke({"dummy_arg": ""})
            assert "TestBot" in result

    def test_get_assistant_list_missing_config(self):
        """配置缺失应返回错误字符串"""
        import os
        os.environ.pop("RAGFLOW_API_KEY", None)

        from tools.ragflow_tools import get_assistant_list
        result = get_assistant_list.invoke({"dummy_arg": ""})
        assert "错误" in result

    def test_create_ask_delete_session_cleanup_on_success(self):
        """正常流程应删除 session"""
        mock_rag = MagicMock()
        mock_chat = MagicMock()
        mock_chat.name = "TestBot"
        mock_session = MagicMock()
        mock_session.id = "session_123"
        mock_chat.create_session.return_value = mock_session

        # Mock streaming response
        mock_response = MagicMock()
        mock_response.content = "Test answer"
        mock_session.ask.return_value = [mock_response]

        mock_rag.list_chats.return_value = [mock_chat]

        with patch("tools.ragflow_tools.RAGFlow", return_value=mock_rag):
            from tools.ragflow_tools import create_ask_delete
            result = create_ask_delete.invoke({
                "assistant_name": "TestBot",
                "question": "Hello",
            })

            mock_chat.delete_sessions.assert_called_once_with(ids=["session_123"])
            assert "Test answer" in result

    def test_create_ask_delete_session_cleanup_on_exception(self):
        """异常流程也应删除 session"""
        mock_rag = MagicMock()
        mock_chat = MagicMock()
        mock_chat.name = "TestBot"
        mock_session = MagicMock()
        mock_session.id = "session_456"
        mock_chat.create_session.return_value = mock_session
        mock_session.ask.side_effect = Exception("Network error")
        mock_rag.list_chats.return_value = [mock_chat]

        with patch("tools.ragflow_tools.RAGFlow", return_value=mock_rag):
            from tools.ragflow_tools import create_ask_delete
            result = create_ask_delete.invoke({
                "assistant_name": "TestBot",
                "question": "Hello",
            })

            mock_chat.delete_sessions.assert_called_once_with(ids=["session_456"])
            assert "失败" in result
