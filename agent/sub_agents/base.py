"""子 Agent 架构基类：AgentContext + AgentConfig + BaseAgent"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentContext:
    """Agent 执行上下文，支持跨工具调用的状态共享"""
    thread_id: str
    workspace_dir: Path
    memory: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """带类型注解的 Agent 配置对象，替代 dict 字面量"""
    name: str
    description: str
    system_prompt: str
    tools: list

    def to_dict(self) -> dict:
        """输出 deepagents 兼容格式"""
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
        }


class BaseAgent:
    """子 Agent 基类，封装 AgentConfig + AgentContext + to_dict() 方法"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.context: AgentContext | None = None

    def to_dict(self) -> dict:
        """输出 deepagents 兼容格式"""
        return self.config.to_dict()

    def create_context(self, thread_id: str, workspace_dir: Path) -> AgentContext:
        """创建 Agent 执行上下文"""
        self.context = AgentContext(
            thread_id=thread_id,
            workspace_dir=workspace_dir,
        )
        return self.context
