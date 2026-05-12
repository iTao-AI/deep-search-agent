# Proposal: Phase 4 — 可观测性升级

**Change ID:** `phase-4-observability`
**Created:** 2026-05-12
**Status:** Draft

---

## Problem Statement

当前系统只能看到"工具开始/结束"的原始事件，存在以下问题：

1. **无性能指标**：无法知道某个工具调用耗时多久、是否有性能瓶颈
2. **无 Token 消耗**：LLM 调用的 token 用量完全不可见
3. **日志泄露风险**：`ToolMonitor.report_tool()` 把工具参数原样输出到 WebSocket 和日志，如果参数包含 API Key、密码等敏感信息，会直接暴露
4. **无可观测性 API**：前端无法查询历史遥测数据，用户只能看实时 WebSocket 流

## Proposed Solution

引入 `AgentTelemetry` 收集 + 日志参数脱敏两层能力：

### 层 1：AgentTelemetry 收集器

```python
@dataclass
class TelemetryRecord:
    thread_id: str
    agent_name: str          # "main" / "network_search" / "database_query"
    tool_name: str           # "publish_fact" / "tavily_search" / "mysql_query"
    duration_ms: float
    input_tokens: int
    output_tokens: int
    status: str              # "success" | "error" | "timeout"
    error: str | None
    timestamp: datetime
```

- 基于 `api/context.py` 的 `ContextVar` 实现 thread_id 隔离
- 内存存储，按 thread_id 分组，每 session 最多保留 500 条记录（超过淘汰最旧）
- `api/server.py` 新增 `/api/telemetry/{thread_id}` 端点返回 JSON

### 层 2：ToolMonitor 参数脱敏

- `report_tool()` 不再直接输出 `args` 原文
- 新增 `sanitize_args()` 方法，对已知敏感字段（key、password、token、secret、api_key 等）做掩码处理
- 对未知参数的值做长度截断（超过 200 字符截断并追加 `...`），防止日志膨胀

### 层 3：Telemetry 与 Monitor 集成

- 在 `ToolMonitor` 的 `report_start` / `report_end` 中自动记录时间戳
- 工具执行结束后自动生成 `TelemetryRecord`
- 前端通过 WebSocket 可以实时收到 telemetry 事件

## Scope

### In Scope
- `agent/telemetry.py` — 新增 TelemetryCollector + TelemetryRecord
- `api/monitor.py` — 改造：集成 telemetry 自动记录 + 参数脱敏
- `api/server.py` — 新增 `/api/telemetry/{thread_id}` 端点
- 子 Agent 调用 telemetry（通过 ToolMonitor 自动触发，不侵入业务代码）

### Out of Scope
- 第三方 APM 集成（Prometheus、Datadog 等）
- 持久化存储（遥测数据仅内存存储，session 结束即丢弃）
- 前端 telemetry 可视化（仅后端 API + WebSocket 事件）
- LLM 级别的 token 统计（需要 LangChain/LangGraph 回调支持，后续 Phase 可选）

## Impact Analysis

| Component | Change Required | Details |
|-----------|-----------------|---------|
| `agent/telemetry.py` | 新增 | TelemetryCollector 类 + TelemetryRecord dataclass |
| `api/monitor.py` | 修改 | report_start/end 集成 telemetry + sanitize_args 脱敏 |
| `api/server.py` | 修改 | 新增 /api/telemetry 端点 |
| Agent 业务代码 | 无侵入 | 通过 ToolMonitor 自动触发，不改 sub_agents 代码 |

## Architecture Considerations

1. **无侵入设计**：Telemetry 通过 ToolMonitor 的 report_start/report_end 自动记录，不需要每个 Agent 手动埋点。这符合"横切关注点应该横切实现"的原则。

2. **脱敏策略**：基于字段名黑名单匹配（key/password/token/secret/api_key），而非值内容判断。这比基于内容的检测更可靠——字段名是 API 契约的一部分，不会变化。

3. **容量控制**：每 thread_id 最多 500 条记录，防止内存泄漏。对于长时间运行的 session 来说，旧数据会被淘汰。

## Success Criteria

- [ ] `/api/telemetry/{thread_id}` 返回该 session 的工具调用记录（tool_name、duration_ms、status）
- [ ] ToolMonitor 不再输出原始 API Key / password 等敏感参数到日志
- [ ] 新增的 telemetry 代码不影响现有 Agent 执行（无侵入验证）
- [ ] 并发请求场景下 telemetry 数据不交叉（thread_id 隔离）

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Telemetry 记录影响性能 | Low | Medium | 异步写入，不阻塞主流程 |
| 脱敏规则遗漏新的敏感字段 | Medium | High | 基于字段名模式匹配（包含 key/secret/token 等关键词），覆盖大多数情况 |
| 内存占用增长 | Low | Medium | 每 session 500 条上限 + session 结束时清理 |
