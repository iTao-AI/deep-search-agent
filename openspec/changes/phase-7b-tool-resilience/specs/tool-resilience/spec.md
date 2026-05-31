## ADDED Requirements

### Requirement: 重试装饰器

系统必须提供可复用的异步重试装饰器 `@retry`，用于包裹可能失败的外部服务调用。装饰器 MUST 支持以下参数：
- `max_retries`：最大重试次数（默认 3）
- `backoff_factor`：指数退避因子（默认 2）
- `max_wait`：两次重试之间的最大等待秒数（默认 30）
- `retryable_exceptions`：可重试的异常类型元组（默认 `(TimeoutError, ConnectionError)`）
- `service_name`：服务名称，用于日志输出（默认 "unknown"）

每次重试 MUST 通过 monitor 记录重试事件。

#### Scenario: 首次调用成功，无需重试
- **WHEN** 被装饰的函数在第一次调用时成功返回
- **THEN** 直接返回结果，不进行任何重试
- **THEN** monitor 不记录任何重试事件

#### Scenario: 调用失败后重试成功
- **WHEN** 被装饰的函数首次调用抛出 `TimeoutError`
- **THEN** 等待退避时间（`min(2^0 * backoff_factor, max_wait)` 秒）后重试
- **WHEN** 第二次调用成功
- **THEN** 返回成功结果
- **THEN** monitor 记录 1 次重试事件

#### Scenario: 超过最大重试次数后失败
- **WHEN** 被装饰的函数连续 `max_retries` 次抛出 `TimeoutError`
- **THEN** 装饰器抛出最后一次异常
- **THEN** monitor 记录 `max_retries - 1` 次重试事件

#### Scenario: 不可重试的异常直接抛出
- **WHEN** 被装饰的函数抛出不在 `retryable_exceptions` 中的异常（如 `ValueError`）
- **THEN** 立即抛出该异常，不进行任何重试

#### Scenario: 自定义重试参数
- **WHEN** 装饰器配置为 `@retry(max_retries=5, backoff_factor=1, max_wait=10)`
- **WHEN** 函数连续失败 4 次，第 5 次成功
- **THEN** 返回成功结果
- **THEN** 每次重试等待时间为 `min(2^attempt, 10)` 秒

---

### Requirement: Tavily 超时和重试

Tavily 网络搜索工具 MUST 对 `_tavily_search()` 调用设置 15 秒超时，并使用重试装饰器包裹。`timeout` 参数 MUST 正确传递给 Tavily SDK 的 `client.search()` 调用。

#### Scenario: Tavily 正常响应
- **WHEN** 调用 Tavily 搜索 API
- **WHEN** API 在 15 秒内返回有效响应
- **THEN** 返回搜索结果，格式为原始 Tavily 响应

#### Scenario: Tavily 超时
- **WHEN** 调用 Tavily 搜索 API
- **WHEN** API 超过 15 秒未响应
- **THEN** 抛出 `TimeoutError`
- **THEN** 重试装饰器捕获并重试（最多 3 次）
- **WHEN** 所有重试均超时
- **THEN** 工具返回错误字符串 `"Error: internet search timed out after 3 retries"`

#### Scenario: Tavily API Key 缺失
- **WHEN** 环境变量 `TAVILY_API_KEY` 未设置
- **THEN** 工具直接返回错误字符串，不调用 Tavily SDK
- **THEN** 不触发重试机制

#### Scenario: Tavily timeout 参数正确传递
- **WHEN** `_search_with_retry()` 被调用，传入 `timeout=10`
- **THEN** Tavily SDK 的 `client.search()` 收到 `timeout=10` 参数

---

### Requirement: RAGFlow 超时和重试

RAGFlow 知识库工具 MUST 对所有 HTTP 调用（`rag.list_chats()`、`chat.create_session()`、`session.ask()`）设置 60 秒超时，并使用重试装饰器包裹。

#### Scenario: RAGFlow 正常响应
- **WHEN** 调用 RAGFlow 知识库查询
- **WHEN** 所有 HTTP 调用在 60 秒内完成
- **THEN** 返回查询结果

#### Scenario: RAGFlow session.ask 超时
- **WHEN** `session.ask()` 流式调用超过 60 秒未返回
- **THEN** 抛出 `TimeoutError`
- **THEN** 重试装饰器捕获并重试
- **WHEN** 所有重试均失败
- **THEN** 工具返回错误字符串 `"Error: knowledge base query timed out after retries"`
- **THEN** `finally` 块尝试清理临时 session

#### Scenario: RAGFlow 服务不可用
- **WHEN** RAGFlow API 返回连接错误（`ConnectionError`）
- **THEN** 重试装饰器捕获并重试（最多 3 次）
- **WHEN** 所有重试均失败
- **THEN** 工具返回错误字符串 `"Error: knowledge base service unavailable after retries"`

#### Scenario: RAGFlow API Key 缺失
- **WHEN** 环境变量 `RAGFLOW_API_KEY` 或 `RAGFLOW_API_URL` 未设置
- **THEN** 工具直接返回错误字符串，不调用 RAGFlow SDK
- **THEN** 不触发重试机制

---

### Requirement: MySQL 连接超时

MySQL 连接池 MUST 配置 `connect_timeout=10` 和 `read_timeout=30`，防止数据库无响应时无限阻塞。

#### Scenario: 正常获取连接
- **WHEN** 调用 `get_connection()`
- **WHEN** 数据库在 10 秒内响应
- **THEN** 返回有效连接对象

#### Scenario: 数据库连接超时
- **WHEN** 调用 `get_connection()`
- **WHEN** 数据库超过 10 秒未响应
- **THEN** 抛出 `TimeoutError` 或 `InterfaceError`
- **THEN** `get_connection()` 返回错误字符串 `"Error: database connection timed out"`

#### Scenario: SQL 查询读取超时
- **WHEN** 执行 SQL 查询
- **WHEN** 数据库超过 30 秒未返回结果
- **THEN** 抛出 `TimeoutError`
- **THEN** 工具返回错误字符串 `"Error: database query timed out"`
- **THEN** 连接被正确释放回连接池

---

### Requirement: 优雅降级

当外部服务不可用（重试耗尽后仍失败）时，工具 MUST 返回结构化的错误字符串，使 sub-agent 能够识别降级状态并调整后续行为。

#### Scenario: 单一数据源降级
- **WHEN** RAGFlow 服务完全不可用（所有重试失败）
- **WHEN** Tavily 和 MySQL 仍可用
- **THEN** 知识库工具返回 `"Error: knowledge base service unavailable"` 
- **THEN** sub-agent 可使用 Tavily 和 MySQL 继续执行

#### Scenario: 所有数据源降级
- **WHEN** Tavily、RAGFlow、MySQL 全部不可用
- **THEN** 各工具返回各自的错误字符串
- **THEN** 主 Agent 应检测到所有子 Agent 失败
- **THEN** 主 Agent 报告 "所有外部数据源不可用" 而非生成空报告

#### Scenario: 降级信息结构化
- **WHEN** 工具返回错误字符串
- **THEN** 错误字符串格式为 `"Error: {service_name} {failure_type} after {retries} retries"`
- **THEN** 包含服务名称、失败类型、重试次数信息

---

### Requirement: PDF 转换超时

PDF 转换工具（`convert_md_to_pdf`）MUST 设置 60 秒超时，防止 PDF 生成过程无限挂起。

#### Scenario: PDF 转换正常完成
- **WHEN** 调用 PDF 转换
- **WHEN** 转换在 60 秒内完成
- **THEN** 返回 PDF 文件路径

#### Scenario: PDF 转换超时
- **WHEN** PDF 转换超过 60 秒未完成
- **THEN** 工具返回错误字符串 `"Error: PDF conversion timed out after 60s"`
- **THEN** 临时文件被正确清理
