# api-task-timeout Specification

## Purpose
TBD - created by archiving change phase-7b-tool-resilience. Update Purpose after archive.
## Requirements
### Requirement: 任务级超时

API 层的任务执行 MUST 设置超时上限（默认 30 分钟），超时后自动取消任务并返回错误响应。

#### Scenario: 任务在超时内完成
- **WHEN** 用户提交任务
- **WHEN** Agent 在 30 分钟内完成执行
- **THEN** 任务正常返回结果

#### Scenario: 任务超时被取消
- **WHEN** 用户提交任务
- **WHEN** Agent 执行超过 30 分钟未完成
- **THEN** 任务被自动取消（`task.cancel()`）
- **THEN** WebSocket 发送超时事件 `"Agent task timed out after 30 minutes"`
- **THEN** 任务状态标记为 `"timeout"`

#### Scenario: 可配置超时值
- **WHEN** 环境变量 `AGENT_TASK_TIMEOUT_SECONDS` 被设置
- **WHEN** 值为有效正整数（如 1800）
- **THEN** 使用该值作为任务超时上限
- **WHEN** 该环境变量未设置
- **THEN** 使用默认值 1800 秒（30 分钟）

