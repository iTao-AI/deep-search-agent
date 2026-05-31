## Why

当前项目对外部服务（RAGFlow、Tavily、MySQL、LLM）的调用缺乏统一的超时和重试机制。RAGFlow 的流式 `session.ask()` 可能无限挂起，Tavily 的 timeout 参数是死代码，MySQL 连接池无超时配置。任何外部服务的网络抖动或宕机都会导致 Agent 永久挂起或返回无意义的原始错误，严重影响系统可靠性。

## What Changes

- **新增** `tools/retry_utils.py`：统一的可复用异步重试装饰器（指数退避 + 最大重试 + 可配置异常类型）
- **新增** 各工具调用的超时包裹（`asyncio.wait_for`），超时值集中配置
- **修复** Tavily timeout 参数死代码 — 正确传递给 SDK
- **修复** RAGFlow 所有 HTTP 调用增加超时和重试
- **修复** MySQL 连接池增加 `connect_timeout` 和 `read_timeout`
- **新增** 优雅降级模式 — 外部服务不可用时返回有意义的降级结果
- **新增** API 层任务级超时（默认 30 分钟），超时自动 cancel  runaway task
- **新增** `tools/retry_utils.py` 的单元测试

## Capabilities

### New Capabilities
- `tool-resilience`: 工具层韧性能力，包括超时控制、重试机制、优雅降级
- `api-task-timeout`: API 层任务超时管理，防止 runaway task 消耗资源

### Modified Capabilities
- （无 — 不修改现有 spec 的需求定义，仅增强底层韧性实现）

## Impact

**受影响文件**：
- `tools/retry_utils.py` — 新建
- `tools/tavily_tools.py` — 修复 timeout 传递，使用统一重试装饰器
- `tools/ragflow_tools.py` — 增加超时和重试
- `tools/mysql_tools.py` — 连接池增加超时参数
- `tools/db_connection.py` — 连接池配置超时
- `api/task_tracker.py` — 增加任务级超时
- `api/server.py` — 无需修改（超时由 task_tracker 处理）
- `tests/unit/test_retry_utils.py` — 新建

**回归风险**：
- Tavily timeout 修复 — 低风险，仅修正参数传递路径
- 超时包裹 — 需确认超时值不切正常请求（Tavily 15s / RAGFlow 60s / MySQL 30s / LLM 120s）
- 重试装饰器 — 纯新增，不影响未装饰的函数

**技术选型**：
- 自实现异步重试装饰器 vs tenacity：选择自实现，因为需求简单（指数退避 + 最大重试），约 100 行代码即可覆盖，减少外部依赖和维护成本
- `asyncio.wait_for` 超时 vs 自定义超时机制：选择 `asyncio.wait_for`，因为 Python 标准库，语义清晰，与现有 async 架构兼容

## Out-of-Scope

- 熔断器模式（Circuit Breaker）— 留到后续迭代
- 缓存层 — 属于 Phase 7c（可观测性增强）
- WebSocket 前端重连机制
- Agent 级别重试编排（由 deepagents SDK 控制）
