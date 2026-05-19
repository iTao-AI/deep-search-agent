# 工具注册表

## 工具清单

所有工具使用 LangChain `@tool` 装饰器，通过 LangGraph 图节点注册为可调用的 action。

### Tavily 搜索工具

- **文件**: `tools/tavily_tools.py`
- **用途**: 网络搜索，获取实时网页信息
- **输入**: 搜索查询字符串
- **输出**: 搜索结果列表（标题、URL、摘要、评分）
- **外部依赖**: Tavily API Key
- **重试**: 内置 3 次重试
- **超时**: 无（待改进，Phase 7b）

### MySQL 工具

- **文件**: `tools/mysql_tools.py`
- **用途**: 数据库查询操作
- **输入**: 自然语言查询描述或 SQL 语句
- **输出**: 查询结果集（行列表）
- **外部依赖**: MySQL 连接池
- **连接管理**: 使用连接池，无瞬断重试（待改进，Phase 7b）
- **安全**: SQL 注入防护由子 Agent prompt 约束

### RAGFlow 工具

- **文件**: `tools/ragflow_tools.py`
- **用途**: 企业知识库检索
- **输入**: 自然语言查询
- **输出**: 知识片段列表（内容、来源、评分）
- **外部依赖**: RAGFlow API
- **流式**: 支持流式响应
- **超时**: 无（待改进，Phase 7b）
- **重试**: 无（待改进，Phase 7b）

### Markdown 工具

- **文件**: `tools/markdown_tools.py`
- **用途**: 将结构化报告数据转换为 Markdown 格式
- **输入**: 报告章节数据
- **输出**: Markdown 字符串
- **外部依赖**: 无

### PDF 工具

- **文件**: `tools/pdf_tools.py`
- **用途**: 将 Markdown 转换为 PDF
- **输入**: Markdown 文件路径
- **输出**: PDF 文件路径
- **外部依赖**: pywin32/Word（当前，仅 Windows）
- **待改进**: Phase 6A 替换为 pandoc 跨平台方案

### 文件读写工具

- **文件**: `tools/upload_file_read_tool.py`
- **用途**: Session 工作空间内的文件读取，支持多种格式
- **工具函数**: `read_file_content(filename, instruction)`
- **支持格式**: `.md`, `.txt`, `.docx`, `.pdf`, `.xlsx`, `.xls`
- **输入**: 文件名（相对于 workspace）+ 提取指令
- **输出**: 文件内容字符串
- **安全**: 路径遍历防护，通过 `resolve_path()` 限制在 workspace 内

### SharedContext 工具

- **文件**: `tools/shared_context_tools.py`
- **用途**: 子 Agent 间的事实发布和查询（Phase 3 引入）
- **工具函数**:
  - `publish_fact(fact, source, topic, thread_id)` — 发布事实到共享上下文
  - `query_facts(topic, source_filter, thread_id)` — 按主题查询已发布事实
- **隔离**: 按 thread_id 隔离，防止跨 session 事实泄漏
- **自动解析**: thread_id 为空时自动从 `api.context` 获取当前会话

## 工具接口约定

所有工具遵循以下约定：

1. **装饰器**: 使用 `@tool` 装饰
2. **错误处理**: 返回错误字符串，不抛出异常
3. **监控**: 调用时通过 `monitor.report_*()` 上报进度
4. **会话隔离**: 通过 `ContextVar` 获取当前 workspace

## 新增工具指南

添加新工具时：

1. 在 `tools/` 下创建新文件
2. 使用 `@tool` 装饰工具函数
3. 在对应子 Agent 中注册工具
4. 更新 `prompt/prompts.yml` 中的工具描述
5. 更新本文档

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-05-19 | 初始工具注册表 |
