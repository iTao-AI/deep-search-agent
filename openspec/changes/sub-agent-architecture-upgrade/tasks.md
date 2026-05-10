# Implementation Tasks: Phase 1 — 子 Agent 架构升级

**Change ID:** `sub-agent-architecture-upgrade`

---

## Phase A: 基础层（AgentContext + AgentConfig + BaseAgent）

- [ ] A.1 创建 `agent/sub_agents/base.py`，定义 `AgentContext` dataclass（thread_id、workspace_dir、memory、metadata）
- [ ] A.2 定义 `AgentConfig` TypedDict/dataclass（name、description、system_prompt、tools）
- [ ] A.3 定义 `BaseAgent` 基类，提供 `to_dict()` 方法输出 deepagents 兼容格式
- [ ] A.4 编写 `tests/unit/test_agent_context.py` — 测试 AgentContext 创建、状态读写、metadata 追踪
- [ ] A.5 编写 `tests/unit/test_agent_config.py` — 测试 AgentConfig 创建和 to_dict 输出

**Quality Gate:**
- [ ] pytest tests/unit/test_agent_context.py tests/unit/test_agent_config.py 通过
- [ ] 类型检查通过（mypy 或 pyright）

---

## Phase B: 子 Agent 重构（NetworkSearchAgent）

- [ ] B.1 创建 `agent/sub_agents/network_search_agent.py` — NetworkSearchAgent 类，继承 BaseAgent
- [ ] B.2 验证 `to_dict()` 输出与原始 dict 一致（字段、值、tools 列表）
- [ ] B.3 编写 `tests/unit/test_network_search_agent.py` — 测试配置正确性和 to_dict 兼容性

**Quality Gate:**
- [ ] 所有测试通过
- [ ] NetworkSearchAgent 功能与原始 dict 一致

---

## Phase C: 子 Agent 重构（DatabaseQueryAgent）

- [ ] C.1 创建 `agent/sub_agents/database_query_agent.py` — DatabaseQueryAgent 类，继承 BaseAgent
- [ ] C.2 验证 `to_dict()` 输出与原始 dict 一致
- [ ] C.3 编写 `tests/unit/test_database_query_agent.py`

**Quality Gate:**
- [ ] 所有测试通过
- [ ] DatabaseQueryAgent 功能与原始 dict 一致

---

## Phase D: 子 Agent 重构（KnowledgeBaseAgent）

- [ ] D.1 创建 `agent/sub_agents/knowledge_base_agent.py` — KnowledgeBaseAgent 类，继承 BaseAgent
- [ ] D.2 验证 `to_dict()` 输出与原始 dict 一致
- [ ] D.3 编写 `tests/unit/test_knowledge_base_agent.py`

**Quality Gate:**
- [ ] 所有测试通过
- [ ] KnowledgeBaseAgent 功能与原始 dict 一致

---

## Phase E: main_agent.py 适配层 + 回归测试

- [ ] E.1 修改 `agent/main_agent.py` — 使用 Agent 实例替代 dict，通过适配层输出 dict 列表
- [ ] E.2 编写 `tests/unit/test_main_agent_adapter.py` — 验证 subagents_list 输出格式兼容 deepagents
- [ ] E.3 全量回归测试 — 验证 3 个 Agent 升级后 main_agent 行为不变

**Quality Gate:**
- [ ] 全量测试通过
- [ ] main_agent 导入无报错

---

## Completion Checklist

- [ ] 所有 Phase 完成
- [ ] 所有质量门通过
- [ ] 文档/注释更新
- [ ] 准备 `/openspec-archive sub-agent-architecture-upgrade`
