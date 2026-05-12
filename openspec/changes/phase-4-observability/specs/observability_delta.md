# Delta: Observability (Telemetry + Log Sanitization)

**Change ID:** `phase-4-observability`
**Affects:** `agent/telemetry.py`, `api/monitor.py`, `api/server.py`

---

## ADDED

### Requirement: TelemetryRecord 数据结构

系统提供 `TelemetryRecord` 数据类，描述单次工具调用的遥测记录。

#### Scenario: 创建成功状态的记录
- GIVEN 一个工具调用完成
- WHEN 创建 `TelemetryRecord(thread_id="abc", tool_name="search", duration_ms=150.0, status="success")`
- THEN 记录包含 thread_id、agent_name、tool_name、duration_ms、status、timestamp 字段

#### Scenario: 创建错误状态的记录
- GIVEN 一个工具调用抛出异常
- WHEN 创建 `TelemetryRecord(..., status="error", error="Connection timeout")`
- THEN 记录的 error 字段包含错误信息

### Requirement: TelemetryCollector 收集器

系统提供 `TelemetryCollector` 类，管理遥测记录的存储和查询。

#### Scenario: 记录工具调用
- GIVEN 一个 TelemetryCollector 实例
- WHEN 调用 `record(record: TelemetryRecord)`
- THEN 该记录追加到对应 thread_id 的列表中

#### Scenario: 按 thread_id 查询
- GIVEN 某 thread_id 下已记录多条 telemetry
- WHEN 调用 `get_by_thread(thread_id="abc")`
- THEN 返回该 thread_id 下的所有记录列表

#### Scenario: 容量控制
- GIVEN 某 thread_id 下已记录 500 条 telemetry
- WHEN 调用 `record()` 添加第 501 条
- THEN 自动淘汰最早的一条记录，保持总量不超过 500

#### Scenario: 清理线程数据
- GIVEN 某 thread_id 下已记录多条 telemetry
- WHEN 调用 `clear_thread(thread_id="abc")`
- THEN 该 thread_id 下的所有记录被清除，不影响其他 thread_id

#### Scenario: 全局实例
- GIVEN 模块被导入
- THEN `collector` 全局单例可用，无需手动初始化

### Requirement: 参数脱敏

ToolMonitor 在输出工具参数前必须进行脱敏处理。

#### Scenario: 已知敏感字段脱敏
- GIVEN 工具参数包含 `{"api_key": "sk-12345", "query": "hello"}`
- WHEN 调用 `sanitize_args(args)`
- THEN 返回 `{"api_key": "***REDACTED***", "query": "hello"}`

#### Scenario: 敏感字段模式匹配
- GIVEN 工具参数包含 `{"password": "pass123", "token": "tok_abc", "secret": "s3cr3t"}`
- WHEN 调用 `sanitize_args(args)`
- THEN 所有包含 "key"、"password"、"token"、"secret" 的字段名对应的值均被替换为 `"***REDACTED***"`

#### Scenario: 长值截断
- GIVEN 工具参数包含 `{"data": "A" * 500}`（500 字符的字符串值）
- WHEN 调用 `sanitize_args(args)`
- THEN 该值被截断为前 200 字符 + `"... (truncated, 500 chars total)"`

#### Scenario: 非字符串值不截断
- GIVEN 工具参数包含 `{"limit": 100, "enabled": true}`
- WHEN 调用 `sanitize_args(args)`
- THEN 数字和布尔值保持原样，不做截断

### Requirement: ToolMonitor 集成 Telemetry

ToolMonitor 的 report_start / report_end 自动触发 telemetry 记录。

#### Scenario: report_start 记录开始时间
- GIVEN 调用 `monitor.report_start("search", {...})`
- THEN 内部为该工具调用记录开始时间戳

#### Scenario: report_end 生成 TelemetryRecord
- GIVEN 之前调用了 report_start("search", ...)
- WHEN 调用 `monitor.report_end("search", result)`
- THEN 自动计算 duration_ms，生成 TelemetryRecord 并存入 collector

#### Scenario: report_end 标记错误状态
- GIVEN 之前调用了 report_start("search", ...)
- WHEN 调用 `monitor.report_end("search", result, error="Connection failed")`
- THEN 生成的 TelemetryRecord 中 status="error"，error="Connection failed"

#### Scenario: report_end 参数已脱敏
- GIVEN 调用 `monitor.report_end("search", result)`
- THEN 向 WebSocket 推送的事件中 args 已脱敏，不暴露原始敏感值

### Requirement: /api/telemetry 端点

FastAPI 提供 REST 端点查询指定 session 的遥测数据。

#### Scenario: 查询存在的 thread_id
- GIVEN 某 thread_id 下已记录多条 telemetry
- WHEN `GET /api/telemetry/{thread_id}`
- THEN 返回 JSON 数组，包含 tool_name、duration_ms、status、timestamp 等字段

#### Scenario: 查询不存在的 thread_id
- WHEN `GET /api/telemetry/nonexistent`
- THEN 返回空数组 `[]`，不抛出异常

---

## MODIFIED

### Requirement: ToolMonitor report_tool 方法

`report_tool()` 方法输出参数前必须经过脱敏处理。

#### Scenario: 输出参数已脱敏
- GIVEN 调用 `monitor.report_tool("tavily_search", args={"api_key": "sk-secret", "query": "test"})`
- THEN `_emit` 事件的 data 中 args 为 `{"api_key": "***REDACTED***", "query": "test"}`

---

## REMOVED

(None)
