# DeepAgents 项目 API 接口文档

本文档详细描述了 **DeepAgents 多智能体系统** 的后端服务接口。该系统基于 FastAPI 构建，提供 RESTful API 和 WebSocket 实时通讯能力，支持任务提交、文件上传下载、文件管理以及实时状态监控。

---

## 1. 基础信息

- **Base URL**: `http://<host>:8000`
- **WebSocket URL**: `ws://<host>:8000`
- **静态资源前缀**: (已移除)

---

## 2. 核心业务接口

### 2.1 智能体任务启动接口 (Run Agent Task)
启动一个新的智能体任务。任务将在后台异步执行，实时进度通过 WebSocket 推送。

- **URL**: `/api/task`
- **Method**: `POST`
- **Content-Type**: `application/json`

**请求体 (Request Body)**

| 参数名 | 类型 | 必选 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `query` | string | 是 | - | 用户输入的自然语言任务指令 |
| `thread_id` | string | 否 | `null` | 任务唯一标识 ID。若不提供，后端会自动生成一个 UUID |

**请求示例**

```json
{
    "query": "从网络查询小米汽车的信息，并保存到md文档中",
    "thread_id": "custom-session-id-123" 
}
```

**响应参数**

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `status` | string | 任务状态，固定为 "started" |
| `thread_id` | string | 任务唯一标识 ID (复用请求中的或新生成的) |

**响应示例**

```json
{
    "status": "started",
    "thread_id": "custom-session-id-123"
}
```

---

### 2.2 文件上传接口 (File Upload)
上传文件到指定会话的上下文目录 (`updated/session_{thread_id}`)，供 Agent 读取和分析。

- **URL**: `/api/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

**请求参数 (Form Data)**

| 参数名 | 类型 | 必选 | 描述 |
| :--- | :--- | :--- | :--- |
| `files` | file[] | 是 | 一个或多个文件对象 |
| `thread_id` | string | 是 | 关联的任务 ID (必须与任务提交时的 ID 一致) |

**响应参数**

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `status` | string | 上传状态，固定为 "uploaded" |
| `files` | string[] | 成功保存的文件名列表 |

**响应示例**

```json
{
    "status": "uploaded",
    "files": ["需求文档.docx", "数据表.xlsx"]
}
```

---

## 3. 文件管理接口

### 3.1 文件下载接口 (File Download)
根据绝对路径下载文件，包含严格的安全检查。

- **URL**: `/api/download`
- **Method**: `GET`

**请求参数 (Query Params)**

| 参数名 | 类型 | 必选 | 描述 |
| :--- | :--- | :--- | :--- |
| `path` | string | 是 | 文件的绝对路径 (通常从 `/api/files` 接口获取) |

**响应**
- 成功：返回文件流 (Binary Stream)，浏览器会自动触发下载。
- 失败：返回 JSON 错误信息。

**错误示例**

```json
{
    "error": "拒绝访问: 只能下载输出目录下的文件"
}

# 获取返回文件流
FileResponse(abs_path, filename=abs_path.name)
```

---

### 3.2 文件列表查询接口 (File Explorer)
列出指定目录下的所有生成文件信息，支持递归遍历。

- **URL**: `/api/files`
- **Method**: `GET`

**请求参数 (Query Params)**

| 参数名 | 类型 | 必选 | 描述 |
| :--- | :--- | :--- | :--- |
| `path` | string | 是 | 目标目录的绝对路径 (必须在 `output` 目录下) |

**响应参数**

| 参数名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `files` | object[] | 文件信息列表，按修改时间倒序排列 |

**`files` 数组元素结构**

| 字段 | 类型 | 描述 |
| :--- | :--- | :--- |
| `name` | string | 文件名 |
| `type` | string | 类型，固定为 "file" |
| `path` | string | 文件的绝对路径 (可用于 `/api/download`) |
| `size` | integer | 文件大小 (字节) |
| `mtime` | float | 最后修改时间戳 |

**响应示例**

```json
{
    "files": [
        {
            "name": "report.pdf",
            "type": "file",
            "path": "C:\\Projects\\DeepAgents\\output\\session_123\\report.pdf",
            "size": 10240,
            "mtime": 1706245600.123
        }
    ]
}
```

---

## 4. WebSocket 实时通讯

用于前端实时接收智能体执行过程中的状态反馈、工具调用详情及最终结果。

- **URL**: `/ws/{thread_id}`
- **协议**: `ws://<host>:8000/ws/{thread_id}`
- **说明**: 建立连接时必须在 URL 路径中携带 `thread_id`，以便服务端定向推送消息。

### 4.1 消息结构 (Server -> Client)

所有服务端推送的消息均为 JSON 格式：

```json
{
    "type": "monitor_event",
    "event": "事件类型枚举",
    "message": "人类可读的提示信息",
    "data": { ... },     // 事件附加数据
    "timestamp": "ISO-8601 时间字符串"
}
```

### 4.2 事件类型定义 (`event`)

前端应根据 `event` 字段的值进行不同的 UI 渲染：

| 事件类型 (`event`) | 触发时机 | `data` 结构示例 | 前端建议动作 |
| :--- | :--- | :--- | :--- |
| `session_created` | 工作目录创建成功 | `{"path": "C:/.../output/session_123"}` | 记录路径，用于后续调用 `/api/files` 接口展示文件列表 |
| `tool_start` | Agent 开始调用工具 | `{"tool_name": "search", "args": {...}}` | 展示“正在执行搜索...”及参数详情 |
| `assistant_call` | 委派给子 Agent | `{"assistant_name": "Researcher", "args": {...}}` | 展示“正在咨询研究员...” |
| `task_result` | 任务完成 | `{"result": "这是最终的回答..."}` | 将结果追加到对话框作为 AI 回复 |
| `error` | 发生异常 | `{}` | 弹窗或气泡提示错误信息 |

### 4.3 心跳保活 (Client -> Server)
客户端发送任意文本，服务端回显 pong。

- **发送**: `ping`
- **接收**: `{"type": "pong", "message": "服务端已收到: ping"}`
