# Deep Search Agent

An autonomous planning agent built on DeepAgents SDK (LangChain ecosystem). Users ask open-ended questions in natural language, the agent autonomously plans, delegates to specialized sub-agents (network search, database query, knowledge base retrieval), synthesizes results, and generates reports in Markdown/PDF format.

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

## Features

- **Autonomous Task Planning**: Agent decides what to search, how many times, and when to stop
- **Hierarchical Sub-Agent Delegation**: Three specialized sub-agents for different information sources
- **File System Context Management**: Automatic workspace isolation per session, prevents context overflow
- **Real-Time Reasoning Stream**: WebSocket-based live progress tracking of agent's thinking process
- **Report Generation**: Auto-generates Markdown/PDF reports from gathered information

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | DeepAgents SDK (LangChain ecosystem) |
| LLM | Qwen-Max (DashScope, OpenAI-compatible API) |
| Network Search | Tavily Search API |
| Database | MySQL (mysql.connector) |
| Knowledge Base | RAGFlow (enterprise RAG engine) |
| Web API | FastAPI + Uvicorn |
| Real-Time Comm | WebSocket |
| Frontend | Vue 3 + Vite |

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
│   └── word_converter.py    # Markdown to PDF via Word COM (Windows)
├── prompt/
│   └── prompts.yml          # Agent system prompts (YAML config)
├── frontend/                # Vue 3 frontend (WebSocket real-time display)
├── ragflow-deploy/          # RAGFlow Docker deployment guide + DB schema
├── docs/                    # Architecture, API docs, interview notes
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites

- Python >= 3.11
- Node.js >= 18
- Tavily API key (https://app.tavily.com/)
- DashScope API key (https://bailian.console.aliyun.com/)
- MySQL database (optional, for database query agent)
- RAGFlow instance (optional, for knowledge base agent)

### 1. Install Backend Dependencies

```bash
cd deep-search-agent
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Configure

```bash
cp .env.example .env
vim .env
```

Fill in your API keys.

### 4. Deploy RAGFlow (Optional)

See `ragflow-deploy/01_RAGFlow安装可视化.md` for step-by-step Docker deployment guide.

### 5. Initialize Database (Optional)

```bash
mysql -u root -p < ragflow-deploy/database-schema.sql
```

### 6. Run

```bash
# Start the backend server
python api/server.py

# In another terminal, start the frontend
cd frontend
npm run dev
```

The API provides:
- **POST /api/task** — Start an agent task
- **POST /api/upload** — Upload files for analysis
- **GET /api/files** — List generated files
- **GET /api/download** — Download generated files
- **WebSocket /ws/{thread_id}** — Real-time reasoning stream

## Documentation

- **Architecture**: `docs/architecture.md` — Full project architecture and workflow
- **API Reference**: `docs/api-docs.md` — API endpoint documentation
- **Interview Notes**: `docs/interview-notes.txt` — How to present this project
- **RAGFlow Deploy**: `ragflow-deploy/` — Docker deployment guide and assets
- **DB Schema**: `ragflow-deploy/database-schema.sql` — MySQL initialization script

## How It Works

### 1. Task Reception

User submits a natural language question. The system creates a unique `thread_id` and an isolated workspace directory.

### 2. Autonomous Planning

The Main Agent analyzes the question, creates a todo-list, and decides which sub-agents to invoke. It can:
- Search the internet (Tavily) for public knowledge
- Query MySQL for business data
- Query RAGFlow for enterprise internal knowledge

### 3. Sub-Agent Delegation

Each sub-agent has its own system prompt and tools. The Main Agent delegates via the `task` tool, which creates an isolated context for the sub-agent — keeping the Main Agent's context clean.

### 4. Report Generation

After gathering information, the Main Agent generates a Markdown report and optionally converts it to PDF.

### 5. Real-Time Streaming

Every step (tool call, sub-agent delegation, final answer) is streamed to the frontend via WebSocket, so users can watch the agent's thinking process in real time.

## License

MIT
