# Design: Phase 7b 工具韧性增强

## 技术决策

### 重试装饰器：自实现 vs 外部库

**决策：自实现 `@retry` 装饰器**

理由：
- 需求简单：指数退避 + 最大重试次数 + 可配置异常类型
- 约 80 行代码即可覆盖全部功能
- 项目已有类似重试模式（Tavily 内置 `_search_with_retry`），风格一致
- 避免引入 tenacity 等重量级依赖（tenacity 本身 ~2000 行代码）

**关键设计**：
- 纯异步装饰器，兼容 `async def` 函数
- 使用 `asyncio.sleep()` 退避，非 `time.sleep()`
- 可重试异常通过参数配置，默认 `(TimeoutError, ConnectionError, OSError)`
- 重试间隔通过 monitor 报告，保持可观测性

### 超时机制：`asyncio.wait_for`

**决策：使用 Python 标准库 `asyncio.wait_for`**

理由：
- 标准库，无额外依赖
- 语义清晰，`asyncio.wait_for(coro, timeout=...)` 一目了然
- 超时抛出 `asyncio.TimeoutError`，可与重试装饰器协同工作
- 与现有 async 架构（FastAPI、LangGraph）兼容

**超时值配置**：
```python
TIMEOUTS = {
    "tavily": 15,      # HTTP search，通常 1-3s
    "ragflow": 60,     # 流式问答，可能需要较长
    "mysql_connect": 10,  # 数据库连接
    "mysql_query": 30,    # SQL 查询
    "llm": 120,        # Qwen-Max 生成
    "pdf_convert": 60, # weasyprint/word 转换
}
```

集中定义在 `tools/retry_utils.py`，便于统一调整。

### 优雅降级策略

**决策：工具层返回结构化错误字符串，sub-agent 层决定是否降级**

理由：
- 工具层职责是执行单一操作，返回成功或失败
- sub-agent 拥有更多上下文（哪些数据源可用、任务优先级）
- 结构化错误字符串格式：`"Error: {service_name} {failure_type} after {retries} retries"`
- 主 Agent 可通过解析错误字符串判断是否所有数据源都不可用

### API 层任务超时

**决策：在 `task_tracker.py` 中增加超时检测**

实现方式：
- `TrackedTask` 增加 `timeout_seconds` 字段
- `start()` 方法记录开始时间
- `check_timeout()` 方法检查是否超过超时上限
- 在 `TaskTracker` 的定期清理循环中调用 `check_timeout()`
- 超时任务调用 `task.cancel()` 并记录状态

**为什么不在 FastAPI middleware 层做**：
- FastAPI middleware 超时只会断开 HTTP 连接，不会 cancel 后台 task
- task_tracker 是任务生命周期的所有者，超时逻辑应在此处

## 架构影响

```
┌─────────────────────────────────────────────────────┐
│  API Layer (api/server.py, api/task_tracker.py)     │
│  + 任务级超时 (30min)                                 │
├─────────────────────────────────────────────────────┤
│  Agent Layer (agent/main_agent.py)                  │
│  + LLM 超时 (120s)                                    │
├─────────────────────────────────────────────────────┤
│  Sub-Agent Layer (agent/sub_agents/)                │
│  - 无变更（纯结构封装）                                 │
├─────────────────────────────────────────────────────┤
│  Tools Layer (tools/*.py)                           │
│  + @retry 装饰器                                      │
│  + asyncio.wait_for 超时包裹                         │
│  + 结构化错误字符串                                    │
├─────────────────────────────────────────────────────┤
│  Shared Utils (tools/retry_utils.py) [NEW]           │
│  - retry() 装饰器                                    │
│  - TIMEOUTS 配置字典                                  │
└─────────────────────────────────────────────────────┘
```

## 回归风险

| 变更 | 风险等级 | 缓解措施 |
|------|----------|----------|
| Tavily timeout 修复 | 低 | 仅修正参数传递，不改变行为 |
| RAGFlow 超时包裹 | 中 | 60s 超时足够覆盖正常请求 |
| MySQL 连接池超时 | 低 | 10s connect + 30s read 是合理默认值 |
| 重试装饰器 | 低 | 纯新增，未装饰的函数不受影响 |
| API 任务超时 | 中 | 30min 默认值足够长，正常任务不会触发 |
