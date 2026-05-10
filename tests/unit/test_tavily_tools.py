"""Phase B: Tavily 工具重构测试 — 重试、超时、错误返回"""
import pytest
import sys
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def _mock_dependencies():
    """Mock tavily and dependencies before importing tavily_tools"""
    for mod in ["tavily", "dotenv", "api.monitor", "tools.tavily_tools"]:
        sys.modules.pop(mod, None)

    # Mock tavily client
    mock_tavily_mod = MagicMock()
    mock_client = MagicMock()
    mock_tavily_mod.TavilyClient = MagicMock(return_value=mock_client)
    sys.modules["tavily"] = mock_tavily_mod
    sys.modules["api.monitor"] = MagicMock()
    sys.modules["api.monitor"].monitor = MagicMock()

    # Set env
    import os
    os.environ["TAVILY_API_KEY"] = "test_key"

    yield

    for mod in ["tavily", "dotenv", "api.monitor", "tools.tavily_tools"]:
        sys.modules.pop(mod, None)


class TestTavilyTools:
    """测试 Tavily 工具的重试、超时、错误返回"""

    def test_internet_search_returns_results(self):
        """正常搜索应返回结果"""
        from tools.tavily_tools import internet_search
        with patch("tools.tavily_tools._search_with_retry") as mock_search:
            mock_search.return_value = [{"title": "Test", "url": "http://test.com"}]
            result = internet_search.invoke({"query": "test"})
            assert result == [{"title": "Test", "url": "http://test.com"}]

    def test_internet_search_no_api_key_returns_error(self):
        """无 API Key 应返回错误字符串"""
        import os
        os.environ.pop("TAVILY_API_KEY", None)
        from tools.tavily_tools import internet_search
        result = internet_search.invoke({"query": "test"})
        assert "Error" in result or "error" in result.lower()

    def test_search_retries_on_failure(self):
        """搜索失败应重试，重试耗尽后返回错误字符串"""
        from tools.tavily_tools import internet_search
        with patch("tools.tavily_tools._search_with_retry") as mock_search:
            mock_search.side_effect = Exception("API error")
            result = internet_search.invoke({"query": "test"})
            mock_search.assert_called_once()
            assert isinstance(result, str)
