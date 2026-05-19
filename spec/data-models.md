# 数据模型文档

## Session Workspace 结构

每次任务执行时，系统创建一个独立的 session workspace 目录。

```
workspace/
├── session-<uuid>/
│   ├── task_input.md          # 用户输入的原始问题
│   ├── research_notes.md      # Agent 研究笔记
│   ├── draft_report.md        # 草稿报告
│   ├── final_report.md        # 最终 Markdown 报告
│   ├── final_report.pdf       # 最终 PDF 报告
│   └── uploads/               # 上传的文件
│       └── <filename>
```

## 子 Agent 输入输出

### Network Search Agent

**输入：**
```json
{
  "query": "搜索查询（自然语言）",
  "max_results": 5
}
```

**输出：**
```json
{
  "results": [
    {
      "title": "网页标题",
      "url": "https://...",
      "content": "摘要内容",
      "score": 0.95
    }
  ],
  "summary": "搜索结果的简要总结"
}
```

### Database Query Agent

**输入：**
```json
{
  "query": "自然语言查询描述",
  "tables": ["可选：指定查询的表名"]
}
```

**输出：**
```json
{
  "sql": "生成的 SQL 语句",
  "results": [
    { "column1": "value1", "column2": "value2" }
  ],
  "summary": "查询结果的简要总结"
}
```

### Knowledge Base Agent (RAGFlow)

**输入：**
```json
{
  "query": "检索查询（自然语言）",
  "top_k": 5
}
```

**输出：**
```json
{
  "results": [
    {
      "content": "检索到的知识片段",
      "source": "知识库来源",
      "score": 0.88
    }
  ],
  "summary": "检索结果的简要总结"
}
```

## 报告 Markdown Schema

生成的报告遵循以下结构：

```markdown
# [报告标题]

## 概述
[任务概述 + 核心发现摘要]

## 任务详情

### 子任务 1：[任务名称]
- **目标**：[子任务目标]
- **过程**：[执行过程]
- **结果**：[子任务结果]

### 子任务 2：[任务名称]
...

## 综合结论
[跨子任务综合分析]

## 参考文献
1. [标题](URL)
2. ...
```

## Telemetry 数据结构

```json
{
  "thread_id": "string",
  "model": "qwen-max",
  "total_tokens": 12345,
  "prompt_tokens": 8000,
  "completion_tokens": 4345,
  "tool_calls": [
    {
      "tool": "tavily_search",
      "duration_ms": 1500,
      "tokens_used": 500,
      "status": "success"
    }
  ],
  "started_at": "2026-05-19T10:00:00Z",
  "completed_at": "2026-05-19T10:05:00Z"
}
```

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-05-19 | 初始数据模型文档 |
