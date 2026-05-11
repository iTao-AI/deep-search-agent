# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Deep Search Agent is an autonomous planning agent built on LangGraph. Users ask open-ended questions in natural language; the main agent autonomously plans, delegates to specialized sub-agents (network search, database query, knowledge base retrieval), synthesizes results, and generates reports in Markdown/PDF format.

## Commands

### Backend (Python 3.11+)

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the backend server (FastAPI + Uvicorn on port 8000)
python api/server.py
```

### Frontend (Node.js 18+)

```bash
cd frontend
npm install
npm run dev          # Start Vite dev server
npm run build        # Type-check + production build
```

### API Endpoints

- `POST /api/task` — Start an async agent task (returns thread_id)
- `POST /api/upload` — Upload files for analysis
- `GET /api/files?path=...` — List files in output directory
- `GET /api/download?path=...` — Download a generated file
- `WebSocket /ws/{thread_id}` — Real-time reasoning stream

## Architecture

### Core Layers

```
agent/main_agent.py        — LangGraph agent creation + async entry point (run_deep_agent)
agent/llm.py               — LLM initialization (Qwen-Max via DashScope)
agent/prompts.py           — YAML prompt config loader (prompt/prompts.yml)
agent/sub_agents/          — Three sub-agents: network_search, database_query, knowledge_base

tools/                     — All agent tools: tavily, mysql, ragflow, markdown, pdf, file_read
api/server.py              — FastAPI server (REST + WebSocket)
api/monitor.py             — ToolMonitor singleton + ConnectionManager for WebSocket events
api/context.py             — ContextVar-based session isolation (async-safe)
```

### Key Design Patterns

1. **ContextVar Session Isolation**: `api/context.py` uses `ContextVar` to isolate per-request workspace directories. Prevents data races when multiple requests run concurrently in the same event loop. Always set context before agent execution and reset in `finally`.

2. **Singleton ToolMonitor**: `api/monitor.py` provides a global `monitor` singleton. Tools report progress via `monitor.report_start()`, `monitor.report_running()`, `monitor.report_end()`. Events are emitted via WebSocket (if connected) or fallback to console.

3. **YAML Prompt Config**: Agent system prompts live in `prompt/prompts.yml`, not hardcoded. Loaded by `agent/prompts.py` into `main_agent_config` and `sub_agents_config`.

4. **Async Task Execution**: Agent tasks are launched via `asyncio.create_task()` in `api/server.py`. Progress is pushed through WebSocket using `monitor` events.

### Data Flow

1. User submits query → `POST /api/task` → `asyncio.create_task(run_deep_agent())`
2. `run_deep_agent()` creates session workspace, sets ContextVar, invokes LangGraph `main_agent.astream()`
3. Main agent decomposes tasks → delegates to sub-agents via `task` tool
4. Stream chunks processed by `_process_stream_chunk()` → events reported to frontend via WebSocket
5. Results written as Markdown/PDF in session workspace

## Environment Variables

Required in `.env` (copy from `.env.example`):

- `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `LLM_QWEN_MAX` — DashScope LLM config
- `TAVILY_API_KEY` — Network search
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_PORT` — Database
- `RAGFLOW_API_URL`, `RAGFLOW_API_KEY` — Knowledge base

## Frontend

Vue 3 + TypeScript + Vite. Entry: `frontend/src/main.ts` → `frontend/src/App.vue`. Connects to backend via WebSocket for real-time agent reasoning display and REST for file management.

## OpenSpec 工作流规则

本项目使用 OpenSpec SDD 工作流管理迭代。所有变更通过 `proposal → spec → tasks → apply → archive` 流程推进。

### 核心纪律

1. **先读后做**：执行任何 OpenSpec 命令前，先读取：
   - `openspec/config.yaml`（项目约束）
   - `openspec/specs/` 目录下相关域的规范（当前系统行为）
   - `openspec/changes/` 当前活跃的变更（如果存在）

2. **不要猜测需求**：如果 spec 中没有明确定义某个行为，问用户，不要自行补充。

3. **out-of-scope 是红线**：proposal.md 中标注为 out-of-scope 的功能，严禁实现。

### Apply 阶段规则

1. 每完成一个 tasks.md 中的 Phase，停下来。
2. 总结当前阶段的代码变更（改了什么文件、为什么这么改）。
3. 等待用户 review 并确认后，再继续下一 Phase。
4. 严禁一次性实现所有任务。

### Phase 4 强制门控（CRITICAL）

- **进入 Phase 4 后，必须先调用 `Skill("openspec-apply")`，再调用 `Skill("test-driven-development")`**
- **严禁跳过 skill 直接写代码或测试**
- 如果 skill 无法调用，必须向用户报告并等待手动触发指令
