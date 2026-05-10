"""Phase B: NetworkSearchAgent 重构测试"""
import pytest
import sys
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def _mock_tavily_tools():
    """Mock tavily_tools before importing the agent, clean up after"""
    _mock_tavily = MagicMock()
    sys.modules["tools.tavily_tools"] = _mock_tavily
    yield
    sys.modules.pop("tools.tavily_tools", None)


class TestNetworkSearchAgent:
    """测试 NetworkSearchAgent 配置正确性和 to_dict 兼容性"""

    def test_create_agent(self):
        from agent.sub_agents.network_search_agent import NetworkSearchAgent
        from agent.sub_agents.base import BaseAgent

        agent = NetworkSearchAgent()
        assert isinstance(agent, BaseAgent)
        assert agent.config.name == "网络搜索助手"

    def test_to_dict_has_required_fields(self):
        from agent.sub_agents.network_search_agent import NetworkSearchAgent

        agent = NetworkSearchAgent()
        result = agent.to_dict()

        assert "name" in result
        assert "description" in result
        assert "system_prompt" in result
        assert "tools" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) > 0

    def test_to_dict_matches_original_format(self):
        from agent.prompts import sub_agents_config
        from agent.sub_agents.network_search_agent import NetworkSearchAgent

        expected_name = sub_agents_config["tavily"].get("name", "")
        expected_desc = sub_agents_config["tavily"].get("description", "")
        expected_prompt = sub_agents_config["tavily"].get("system_prompt", "")

        agent = NetworkSearchAgent()
        result = agent.to_dict()

        assert result["name"] == expected_name
        assert result["description"] == expected_desc
        assert result["system_prompt"] == expected_prompt
