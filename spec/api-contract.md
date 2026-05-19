# API 规范文档

## REST API

### POST /api/task

启动一个异步 Agent 任务。

**请求体：**
```json
{
  "query": "用户的研究问题（自然语言）",
  "upload_files": ["可选：上传的文件路径数组"]
}
```

**响应：**
```json
{
  "thread_id": "唯一的会话线程ID",
  "status": "started"
}
```

### POST /api/upload

上传文件用于分析。

**请求：**
- Content-Type: `multipart/form-data`
- 字段：`file`（文件对象）

**响应：**
```json
{
  "file_path": "上传后的文件路径",
  "status": "success"
}
```

### GET /api/files

列出输出目录下的文件。

**查询参数：**
- `path`（可选）：子目录路径

**响应：**
```json
{
  "files": [
    {
      "name": "filename.md",
      "path": "/path/to/file",
      "size": 1024,
      "modified": "2026-05-19T10:00:00Z"
    }
  ]
}
```

### GET /api/download

下载生成的文件。

**查询参数：**
- `path`：文件路径（相对于输出目录）

**响应：**
- Content-Type: 根据文件类型
- Body: 文件二进制流

### GET /api/telemetry/{thread_id}

获取指定线程的遥测记录。

**路径参数：**
- `thread_id`：POST /api/task 返回的线程 ID

**响应：**
```json
{
  "telemetry": [
    {
      "timestamp": "ISO 8601 时间戳",
      "type": "事件类型",
      "data": { ... }
    }
  ]
}
```

## WebSocket

### WebSocket /ws/{thread_id}

实时接收 Agent 推理流事件。

**连接参数：**
- `thread_id`：POST /api/task 返回的线程 ID

**消息格式（服务端 → 客户端）：**
```json
{
  "type": "tool_start | tool_running | tool_end | error | complete",
  "thread_id": "线程ID",
  "tool_name": "工具名称",
  "message": "事件描述",
  "data": { ... },
  "timestamp": "ISO 8601 时间戳"
}
```

**事件类型说明：**

| type | 含义 |
|------|------|
| `tool_start` | 工具开始执行 |
| `tool_running` | 工具执行中（进度更新） |
| `tool_end` | 工具执行完成 |
| `error` | 发生错误 |
| `complete` | 整个任务完成 |

## 认证

当前无认证。生产环境应添加 API Key 或 JWT 认证。

## 错误响应

```json
{
  "error": "错误描述",
  "detail": "详细错误信息（开发环境）"
}
```

**HTTP 状态码：**
- `200`：成功
- `400`：请求参数错误
- `404`：资源未找到
- `500`：服务器内部错误

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-05-19 | 初始 API 规范 |
