# Delta: 共享事实上下文 (shared_context)

**Change ID:** `agent-inter-agent-communication`
**Affects:** agent/shared_context.py, agent/main_agent.py, agent/sub_agents/

---

## ADDED

### Requirement: SharedContext 事实发布

系统提供 `SharedContext` 类，允许 Agent 节点向 LangGraph state 写入结构化事实。

#### Scenario: 发布单条事实
- GIVEN 一个 LangGraph state 包含 `shared_facts` 列表
- WHEN 调用 `publish_fact(state, fact="某公司2024年营收100亿", source="network_search", topic="company_revenue")`
- THEN `shared_facts` 中新增一条记录，包含 fact、source、topic、timestamp 字段

#### Scenario: 发布事实自动附加元数据
- GIVEN 调用 `publish_fact`
- WHEN 未提供 topic 参数
- THEN 自动从 source 派生 topic，使用 source 名称作为默认 topic

#### Scenario: 重复事实去重
- GIVEN 某 topic 下已存在完全相同的 fact（fact 文本 + source 均相同）
- WHEN 再次调用 `publish_fact` 发布相同内容
- THEN 不重复写入，返回已存在的记录

---

### Requirement: SharedContext 事实查询

系统允许 Agent 节点按 topic 查询已发布的事实。

#### Scenario: 按主题查询事实
- GIVEN state 中已发布多条事实，涉及不同 topic
- WHEN 调用 `query_facts(state, topic="company_revenue")`
- THEN 返回所有匹配该 topic 的事实列表

#### Scenario: 查询不存在的 topic
- GIVEN state 中 `shared_facts` 为空或不包含指定 topic
- WHEN 调用 `query_facts(state, topic="unknown_topic")`
- THEN 返回空列表 `[]`，不抛出异常

#### Scenario: 按来源过滤事实
- GIVEN state 中已发布多条事实，来自不同 source
- WHEN 调用 `query_facts(state, topic="company_revenue", source_filter="network_search")`
- THEN 仅返回匹配 topic 且 source 为 network_search 的事实

---

### Requirement: SharedContext 容量控制与清理

系统必须防止无限制内存增长，并提供 session 级别的清理能力。

#### Scenario: 事实数量上限
- GIVEN 某 thread_id 下已发布 100 条事实
- WHEN 调用 `publish_fact` 发布第 101 条
- THEN 自动淘汰最早发布的一条事实，保持总量不超过 100 条

#### Scenario: 按线程清理事实
- GIVEN 某 thread_id 下已发布多条事实
- WHEN 调用 `clear_facts(thread_id="xxx")`
- THEN 该 thread_id 下的所有事实被清除，不影响其他 thread_id 的事实

#### Scenario: 清理不存在的 thread_id
- GIVEN 调用 `clear_facts(thread_id="nonexistent")`
- THEN 不抛出异常，静默返回

---

### Requirement: StateGraph 集成 shared_facts

`main_agent.py` 的 StateGraph 必须包含 `shared_facts` 字段。

#### Scenario: 初始化 shared_facts
- GIVEN 创建新的 agent 会话
- WHEN 初始化 StateGraph state
- THEN `shared_facts` 字段为空列表 `[]`

#### Scenario: 跨节点共享
- GIVEN 节点 A 在 state 中发布事实
- WHEN 节点 B 读取 state
- THEN 节点 B 可以读取节点 A 发布的事实

---

### Requirement: 子 Agent 事实发布

子 Agent 在执行完核心操作后，应将关键结果发布到 shared_context。

#### Scenario: 网络搜索发布搜索结果摘要
- GIVEN network_search_agent 完成一次搜索
- WHEN 搜索结果包含有效数据
- THEN 发布一条 topic 为 "search_result" 的事实，包含 query、top_urls、key_findings

#### Scenario: 数据库查询发布结果摘要
- GIVEN database_query_agent 完成一次查询
- WHEN 查询结果包含有效数据
- THEN 发布一条 topic 为 "db_query_result" 的事实，包含 table、row_count、columns

---

## MODIFIED

### Requirement: main_agent.py 增加 shared_facts 消费

主 Agent 在完成所有子 Agent 后，应消费 shared_facts 中的信息用于最终报告生成。

#### Scenario: 汇总事实
- GIVEN 所有子 Agent 已完成执行
- WHEN 主 Agent 生成最终报告
- THEN 从 shared_facts 中提取关键信息，整合到报告中

---

## REMOVED

(None)
