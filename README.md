[English](./README.md) | [中文](./README_zh.md)

# Deep Search Agent

An autonomous planning agent built on LangGraph. Users ask open-ended questions in natural language; the main agent autonomously plans, delegates to specialized sub-agents (network search, database query, knowledge base retrieval), synthesizes results, and generates reports in Markdown/PDF format.

## Architecture

```
User Question
    │
    ▼
┌──────────────────────────────────┐
│         Main Agent (Planner)     │
│  - Task decomposition            │
│  - Sub-agent delegation          │
│  - File system context mgmt      │
│  - Report generation             │
├──────────┬──────────┬────────────┤
│ Network  │ Database │ Knowledge  │
│ Search   │ Query    │ Base (RAG) │
│ Agent    │ Agent    │ Agent      │
│ (Tavily) │ (MySQL)  │ (RAGFlow)  │
└──────────┴──────────┴────────────┘
    │           │           │
    ▼           ▼           ▼
  Internet    Business   Enterprise
  Search      Data       Knowledge
```

**Data flow:**
1. User submits a question via REST API or WebSocket
2. Main Agent (LangGraph) analyzes the question and creates a task plan
3. Sub-agents are dispatched via the `task` tool with isolated contexts
4. Results are synthesized and written as Markdown/PDF reports
5. Progress is streamed to the frontend via WebSocket in real time

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | DeepAgents SDK (LangGraph ecosystem) |
| LLM | Qwen-Max (DashScope, OpenAI-compatible API) |
| Network Search | Tavily Search API |
| Database | MySQL (mysql.connector) |
| Knowledge Base | RAGFlow (enterprise RAG engine) |
| Web API | FastAPI + Uvicorn |
| Real-Time Comm | WebSocket |
| Frontend | Vue 3 + Vite |

## Features

- **Autonomous Task Planning**: Agent decides what to search, how many times, and when to stop
- **Hierarchical Sub-Agent Delegation**: Three specialized sub-agents for different information sources
- **File System Context Management**: Automatic workspace isolation per session via ContextVar, prevents concurrent request interference
- **Real-Time Reasoning Stream**: WebSocket-based live progress tracking of agent's thinking process
- **Report Generation**: Auto-generates Markdown/PDF reports from gathered information
- **File Upload & Analysis**: Users can upload documents (PDF, Word, Excel) for the agent to analyze

## Quick Start

### Prerequisites

- Python >= 3.11
- Node.js >= 18
- Tavily API key (https://app.tavily.com/)
- DashScope API key (https://bailian.console.aliyun.com/)

### 1. Install Backend Dependencies

```bash
cd deep-search-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
vim .env
```

Fill in your API keys.

### 3. Run

```bash
# Start the backend
python api/server.py

# In another terminal, start the frontend
cd frontend
npm install && npm run dev
```

The API provides:
- **POST /api/task** — Start an agent task
- **POST /api/upload** — Upload files for analysis
- **GET /api/files** — List generated files
- **GET /api/download** — Download generated files
- **WebSocket /ws/{thread_id}** — Real-time reasoning stream

## API Reference

### POST /api/task

Start an agent task. The agent runs asynchronously; progress is pushed via WebSocket.

```json
{
  "query": "调研 AI 行业趋势并生成 PDF 报告",
  "thread_id": "optional-uuid"
}
```

Response:
```json
{
  "status": "started",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### WebSocket /ws/{thread_id}

Connect with the `thread_id` returned from `/api/task`. Events include:
- `session_created` — Workspace directory ready
- `tool_start` — A tool is being executed
- `assistant_call` — A sub-agent is being dispatched
- `task_result` — Final answer available
- `error` — Execution failed

## Project Structure

```
deep-search-agent/
├── agent/
│   ├── main_agent.py        # Main agent orchestration + runtime
│   ├── llm.py               # LLM initialization
│   ├── prompts.py           # Prompt config loader
│   └── sub_agents/
│       ├── network_search_agent.py      # Tavily search sub-agent
│       ├── database_query_agent.py      # MySQL query sub-agent
│       └── knowledge_base_agent.py      # RAGFlow sub-agent
├── tools/
│   ├── tavily_tools.py      # Network search tool
│   ├── mysql_tools.py       # Database query tools (list tables, preview, SQL)
│   ├── ragflow_tools.py     # Knowledge base tools (assistant list, ask)
│   ├── markdown_tools.py    # Markdown report generation
│   ├── pdf_tools.py         # Markdown to PDF conversion
│   └── upload_file_read_tool.py  # File reading (PDF, Word, Excel, text)
├── api/
│   ├── server.py            # FastAPI server (REST + WebSocket)
│   ├── monitor.py           # Real-time progress monitor (singleton)
│   └── context.py           # ContextVar session isolation
├── utils/
│   ├── path_utils.py        # Path resolution & virtual path cleaning
│   └── word_converter.py    # Markdown to PDF via Word COM
├── prompt/
│   └── prompts.yml          # Agent system prompts (YAML config)
└── frontend/                # Vue 3 frontend (WebSocket real-time display)
```

## License

MIT
