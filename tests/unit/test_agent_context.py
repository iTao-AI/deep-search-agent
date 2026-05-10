"""Phase A: AgentContext + AgentConfig + BaseAgent tests"""
import pytest
from pathlib import Path


class TestAgentContext:
    """Test AgentContext creation and state management"""

    def test_create_context_with_thread_id(self):
        """Creating AgentContext should accept thread_id and workspace_dir"""
        from agent.sub_agents.base import AgentContext

        ctx = AgentContext(thread_id="test-123", workspace_dir=Path("/tmp/test"))

        assert ctx.thread_id == "test-123"
        assert ctx.workspace_dir == Path("/tmp/test")
        assert ctx.memory == {}
        assert ctx.metadata == {}

    def test_memory_read_write(self):
        """AgentContext should support cross-tool-call memory sharing"""
        from agent.sub_agents.base import AgentContext

        ctx = AgentContext(thread_id="test-1", workspace_dir=Path("/tmp/test"))

        ctx.memory["search_results"] = ["result1", "result2"]
        assert ctx.memory["search_results"] == ["result1", "result2"]

    def test_metadata_tracking(self):
        """AgentContext should track metadata"""
        from agent.sub_agents.base import AgentContext

        ctx = AgentContext(thread_id="test-1", workspace_dir=Path("/tmp/test"))

        ctx.metadata["call_count"] = 3
        ctx.metadata["execution_time"] = 1.5

        assert ctx.metadata["call_count"] == 3
        assert ctx.metadata["execution_time"] == 1.5


class TestAgentConfig:
    """Test AgentConfig creation and to_dict compatibility"""

    def test_create_config(self):
        """AgentConfig should accept name, description, system_prompt, tools"""
        from agent.sub_agents.base import AgentConfig

        def dummy_tool():
            pass

        config = AgentConfig(
            name="test_agent",
            description="A test agent",
            system_prompt="You are a test agent",
            tools=[dummy_tool]
        )

        assert config.name == "test_agent"
        assert config.description == "A test agent"
        assert config.system_prompt == "You are a test agent"
        assert dummy_tool in config.tools

    def test_to_dict_output(self):
        """AgentConfig.to_dict() should output deepagents compatible format"""
        from agent.sub_agents.base import AgentConfig

        def dummy_tool():
            pass

        config = AgentConfig(
            name="test_agent",
            description="A test agent",
            system_prompt="You are a test agent",
            tools=[dummy_tool]
        )

        result = config.to_dict()

        assert result["name"] == "test_agent"
        assert result["description"] == "A test agent"
        assert result["system_prompt"] == "You are a test agent"
        assert dummy_tool in result["tools"]
