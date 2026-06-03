# Phase 9 文档同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Phase 9 E2E 稳定性兜底实现后的架构变更、新增 API、测试数据同步到项目文档。

**Architecture:** 5 个纯文档文件更新，无代码变更。CLAUDE.md 补架构层描述，README 双版补端点 + 测试数，run-log.md 从 PLANNED 翻到 DONE，evidence README + technical-decisions.md 同步数字和决策。

**Tech Stack:** Markdown, git

**验证方式:** `pytest -q`（确认 282 passed）+ `npm run build`（确认前端基线）

---

## 文件变更概览

| 文件 | 操作 | 关键变更 |
|------|------|---------|
| `CLAUDE.md` | 修改 | API Endpoints、Core Layers、Design Patterns、Data Flow 四个区域追加 Phase 9 模块 |
| `README.md` | 修改 | 测试数 264→282、Evidence 表追加 Phase 9 行、项目结构补充 Phase 9 文件 |
| `README_CN.md` | 修改 | 同 README.md（中文版） |
| `docs/evidence/run-log.md` | 修改 | Phase 9 状态 PLANNED→DONE，追加实现摘要、模块列表、测试覆盖 |
| `docs/evidence/README.md` | 修改 | 测试数 264→282、补 Phase 9 产出描述 |
| `docs/evidence/technical-decisions.md` | 修改 | 追加 Phase 9 fallback 设计决策 |

---

### Task 1: 更新 CLAUDE.md（架构层 + API + Design Patterns + Data Flow）

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 更新 API Endpoints 区域**

在 `WebSocket /ws/{thread_id}` 行后追加新端点：

```markdown
- `GET /api/tasks/{thread_id}` — Query persisted task status and output path (Phase 8+)
- `GET /api/token-usage/{thread_id}` — Query token usage for a thread (Phase 7c)
```

定位：在 CLAUDE.md 第 37 行 `- \`WebSocket /ws/{thread_id}\` — Real-time reasoning stream` 之后插入以上两行。

- [ ] **Step 2: 更新 Core Layers 区域**

在 `api/context.py` 行后追加 Phase 9 新增模块：

```markdown
agent/run_result.py       — AgentRunAccumulator + AgentRunResult + stream chunk processor
api/persistence.py        — SQLite task state persistence (Phase 8)
api/task_finalizer.py     — Deterministic task finalization: completed/completed_with_fallback/failed (Phase 9)
```

定位：在 CLAUDE.md 第 52 行 `api/context.py` 之后插入。

- [ ] **Step 3: 更新 Key Design Patterns 区域**

追加 Pattern #5 和 #6：

```markdown
5. **Deterministic Task Finalization (Phase 9)**: `api/task_finalizer.py` guarantees every agent run reaches a definite terminal state — `completed` (report found), `completed_with_fallback` (fallback report generated), or `failed` (exception/timeout). No more "stream ended but no report" ambiguity. `AgentRunAccumulator` collects stream diagnostics during execution; `process_stream_chunk()` replaces the inline stream processing in server.py.

6. **Timeout Callback**: `api/server.py` registers `_mark_task_timeout()` as a callback when launching agent tasks via `run_with_timeout()`. On timeout, the callback persists `status="failed"` to SQLite and emits a `task_finalized` WebSocket event — before the task is cancelled. This prevents timeout tasks from silently disappearing.
```

定位：在 CLAUDE.md 第 63 行 Pattern #4 `Async Task Execution` 之后插入。

- [ ] **Step 4: 更新 Data Flow 区域**

将现有的步骤 4 和步骤 5 替换为 Phase 9 后的新流程：

```markdown
### Data Flow

1. User submits query → `POST /api/task` → `asyncio.create_task(_run_task_with_persistence())`
2. Task status set to `running` in SQLite via `update_task()`; timeout callback registered
3. `run_deep_agent()` creates session workspace, sets ContextVar, invokes LangGraph `main_agent.astream()`
4. Stream chunks collected by `process_stream_chunk()` into `AgentRunAccumulator`; events reported via WebSocket
5. On success: `finalize_task_run()` searches for a Markdown report → `completed` if found, or generates a fallback report → `completed_with_fallback`
6. On failure/timeout: `_mark_task_timeout()` or exception handler persists `failed` status + error message
7. All terminal states emit `task_finalized` WebSocket event with status, fallback flag, and output path
```

定位：替换 CLAUDE.md 第 65-71 行的现有 Data Flow 内容。

- [ ] **Step 5: 验证 CLAUDE.md 变更**

```bash
git diff CLAUDE.md
```

检查：
- API Endpoints 有 7 个端点（5 个原有 + 2 个新增）
- Core Layers 列出 `agent/run_result.py` 和 `api/task_finalizer.py`
- Design Patterns 有 6 个条目
- Data Flow 描述 7 步，包含 fallback 和 timeout 路径

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: CLAUDE.md 架构更新（Phase 9 确定性终态 + fallback + timeout callback）"
```

---

### Task 2: 更新 README.md（英文版）

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新测试数 264→282**

将 Evidence 表中：
```markdown
| Local pytest run | 264 passed, 0 failed | `pytest -q` |
```

替换为：
```markdown
| Local pytest run | 282 passed, 0 failed | `pytest -q` |
```

定位：READEME.md 第 64 行。

- [ ] **Step 2: 追加 Phase 9 Evidence 行**

在 Evidence 表末尾（CI/CD 行之后）追加：

```markdown
| Fallback reports | Implemented (Phase 9) | `api/task_finalizer.py`, deterministic terminal states |
| Task timeout handling | Implemented (Phase 9) | `api/server.py`, `_mark_task_timeout` callback |
```

定位：在 `| CI/CD | Configured (Phase 8) | ...` 行之后插入。

- [ ] **Step 3: 更新项目结构**

在项目结构树中追加 Phase 9 文件。在 `api/` 段中补充：

```markdown
│   ├── persistence.py              # SQLite task state persistence (Phase 8)
│   ├── task_finalizer.py           # Deterministic task finalization (Phase 9)
```

在 `agent/` 段中补充：

```markdown
│   ├── run_result.py               # AgentRunAccumulator + stream processing (Phase 9)
```

定位：在 `api/context.py` 行之后插入 `persistence.py` 和 `task_finalizer.py`；在 `agent/prompts.py` 行之后插入 `run_result.py`。

- [ ] **Step 4: 验证 README.md 变更**

```bash
git diff README.md
```

检查：
- 测试数为 282 passed
- Evidence 表有 13 行
- 项目结构包含 `run_result.py`、`persistence.py`、`task_finalizer.py`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: README.md 测试数 264→282，Evidence 表追加 Phase 9"
```

---

### Task 3: 更新 README_CN.md（中文版）

**Files:**
- Modify: `README_CN.md`

变更内容与 Task 2 完全对应（中文翻译），三个变更点：

- [ ] **Step 1: 更新测试数**

将第 62 行：
```markdown
| Local pytest run | 264 通过, 0 失败 | `pytest -q` |
```

替换为：
```markdown
| Local pytest run | 282 通过, 0 失败 | `pytest -q` |
```

- [ ] **Step 2: 追加 Phase 9 Evidence 行**

在 CI/CD 行之后追加：

```markdown
| 兜底报告 | 已实现（Phase 9） | `api/task_finalizer.py`，确定性终态 |
| 任务超时处理 | 已实现（Phase 9） | `api/server.py`，`_mark_task_timeout` 回调 |
```

- [ ] **Step 3: 更新项目结构**

在 `api/` 段追加：
```markdown
│   ├── persistence.py              # SQLite 任务状态持久化（Phase 8）
│   ├── task_finalizer.py           # 确定性任务终态处理（Phase 9）
```

在 `agent/` 段追加：
```markdown
│   ├── run_result.py               # AgentRunAccumulator + 流处理（Phase 9）
```

- [ ] **Step 4: 验证 README_CN.md 变更**

```bash
git diff README_CN.md
```

- [ ] **Step 5: Commit**

```bash
git add README_CN.md
git commit -m "docs: README_CN.md 测试数 264→282，Evidence 表追加 Phase 9"
```

---

### Task 4: 更新 run-log.md（Phase 9 状态翻牌）

**Files:**
- Modify: `docs/evidence/run-log.md`

- [ ] **Step 1: 替换 Phase 9 Plan 区域**

将第 44-50 行：
```markdown
## Phase 9 Plan

- **状态**: PLANNED
- **目标**: 将 Phase 8 的 E2E 不稳定报告生成问题收敛为确定性后端终态：`completed`、`completed_with_fallback` 或 `failed`。
- **验证策略**: 后端单元测试覆盖 persistence、timeout、agent run accumulator 和 task finalizer；集成测试覆盖 completed、fallback、exception、timeout；真实 E2E 使用 `scripts/e2e_runner.py` 手动记录。
- **非目标**: 本阶段不做 5 问 benchmark，不做 prompt 调优，不把真实 LLM E2E 放入 CI。
```

替换为：

```markdown
## Phase 9 Implementation

- **状态**: DONE（2026-06-03）
- **目标达成**: 将 E2E 不稳定报告生成问题收敛为确定性后端终态。
- **新增模块**:
  - `agent/run_result.py` — `AgentRunAccumulator`（流状态收集）+ `AgentRunResult`（不可变结果对象）+ `process_stream_chunk()`（替换 server.py 内联流处理）
  - `api/task_finalizer.py` — `TaskFinalization`（终态数据类）+ `finalize_task_run()`（报告搜索 / fallback 报告 / 持久化）
  - `api/server.py` — `_mark_task_timeout()` 回调 + `_run_task_with_persistence()` 封装；WebSocket 新增 `task_finalized` 事件
  - `api/monitor.py` — `report_task_finalized()` 方法（发射终态事件）
- **确定性终态**: `completed`（正式报告）| `completed_with_fallback`（兜底报告）| `failed`（异常/超时）
- **Fallback 报告内容**: 线程 ID、生成时间、原始查询、最后一个 agent 输出、诊断事件列表
- **测试覆盖**: 282 passed, 0 failed（含 `test_task_finalizer.py`、`test_persistence.py`、`test_monitor_sanitization.py` 中 Phase 9 相关用例）
- **非目标**: 本阶段未做 5 问 benchmark、prompt 调优、真实 LLM E2E 入 CI
```

- [ ] **Step 2: 更新文件顶部测试数引用**

将第 19 行：
```markdown
- Local pytest run: 264 passed, 0 failed（`python -m pytest -q`）
```

替换为：
```markdown
- Local pytest run: 282 passed, 0 failed（`python -m pytest -q`）
```

- [ ] **Step 3: 验证 run-log.md 变更**

```bash
git diff docs/evidence/run-log.md
```

检查：
- Phase 9 状态为 DONE
- 新增模块列表完整
- 确定性终态三个值都已列出
- 测试数 282

- [ ] **Step 4: Commit**

```bash
git add docs/evidence/run-log.md
git commit -m "docs: run-log.md Phase 9 PLANNED→DONE，追加实现摘要和模块列表"
```

---

### Task 5: 更新 docs/evidence/README.md

**Files:**
- Modify: `docs/evidence/README.md`

- [ ] **Step 1: 更新目录表**

将第 9 行：
```markdown
| [run-log.md](run-log.md) | E2E Run #1 数据（282s / 459K tokens / 2 子Agent）+ Phase 8 收口状态；benchmark 仍待后续稳定脚本补充 |
```

替换为：
```markdown
| [run-log.md](run-log.md) | E2E Run #1 数据（282s / 459K tokens / 2 子Agent）+ Phase 8 收口 + Phase 9 确定性终态实现；benchmark 待后续稳定脚本补充 |
```

- [ ] **Step 2: 追加 Phase 9 说明段**

在目录表之后（第 11 行之后）追加：

```markdown
## Phase 9 产出（2026-06-03）

- 确定性终态：`completed` / `completed_with_fallback` / `failed`
- Fallback 报告生成：当 agent 未产出正式报告时，系统自动生成含诊断信息的兜底报告
- Timeout 回调：超时任务在取消前持久化 `failed` 状态
- 测试：282 passed, 0 failed（含 `test_task_finalizer.py`、`test_persistence.py` 中 Phase 9 相关用例）
```

- [ ] **Step 3: 验证 docs/evidence/README.md 变更**

```bash
git diff docs/evidence/README.md
```

- [ ] **Step 4: Commit**

```bash
git add docs/evidence/README.md
git commit -m "docs: evidence/README.md 追加 Phase 9 产出描述，测试数 282"
```

---

### Task 6: 更新 docs/evidence/technical-decisions.md

**Files:**
- Modify: `docs/evidence/technical-decisions.md`

- [ ] **Step 1: 追加 Phase 9 Fallback 设计决策**

在文件末尾追加：

```markdown
## Phase 9 新增决策

### 为什么选「确定性终态」模型

Phase 8 收口时发现：同一 query 跑多次 E2E，有时生成报告、有时 agent 回答在 AIMessage 中但未写文件、有时 token 爆炸（459K → 3M）。根源是 DeepSeek 模型行为随机 + 报告生成依赖 agent 自主调用 write_file 工具。

«确定性终态»把「报告是否生成」从 agent 的不可靠决策中抽离出来，变成后端代码的确定性逻辑：

- 流的最后有 Markdown 文件 → `completed`
- 流正常结束但无 Markdown 文件 → 后端生成 fallback 报告 → `completed_with_fallback`
- 异常/超时 → `failed`

这样每次 E2E 都有明确终态，不会出现「stream ended but no report」的尴尬。面试/演示时即使 agent 没有生成正式报告，fallback 报告也包含完整诊断信息。

### Fallback 报告内容策略

Fallback 报告不是空的占位符，而是包含：

1. 线程 ID 和生成时间（可追溯性）
2. 原始查询（保留用户意图）
3. 最后一个 agent 文本输出（即使没写成文件，LLM 的思考也在这里）
4. 诊断事件列表（`tool:tavily`、`tool:ragflow` 等，证明 agent 确实在干活）

这样 fallback 报告本身就是问题排查的起点——面试官、审查者或 debug 者看到它就能判断是 query 太难、模型没调用工具、还是工具调用后没收到结果。

### TaskFinalization 接口设计

`TaskFinalization` 是不可变数据类，四个字段：

- `thread_id` — 对应原始请求
- `status` — `"completed" | "completed_with_fallback" | "failed"`
- `output_path` — 报告文件绝对路径（或 None）
- `fallback_used` — 布尔值，前端据此决定是否显示「兜底报告」标记
- `error_message` — 仅 `failed` 时有值

`finalize_task_run()` 是唯一入口，接收 `AgentRunResult`，返回 `TaskFinalization`。不抛异常——报告搜索失败时走 fallback 路径而非崩溃。
```

- [ ] **Step 2: 验证 technical-decisions.md 变更**

```bash
git diff docs/evidence/technical-decisions.md
```

- [ ] **Step 3: Commit**

```bash
git add docs/evidence/technical-decisions.md
git commit -m "docs: technical-decisions.md 追加 Phase 9 fallback 设计决策"
```

---

### Task 7: 全量验证

- [ ] **Step 1: 运行全量测试**

```bash
python -m pytest -q
```

预期：282 passed, 0 failed

- [ ] **Step 2: 运行前端构建**

```bash
cd frontend && npm run build
```

预期：构建成功

- [ ] **Step 3: 检查 git diff 完整性**

```bash
git diff --stat
```

预期：6 个文件变更，无意外文件。

- [ ] **Step 4: 检查所有文档中的数字一致性**

```bash
grep -rn '282\|264' README.md README_CN.md docs/evidence/run-log.md docs/evidence/README.md
```

预期：所有引用都是 282，无残留 264。

- [ ] **Step 5: 最终 commit（如有遗漏修正）**

```bash
git add -A
git commit -m "docs: Phase 9 文档同步最终验证"
```

---

## 自审清单

执行前自审：

1. **Spec 覆盖**: 原 plan 的 5 个 task 全部覆盖（加上全量验证 task）
2. **占位符检查**: 无 TBD / TODO / "等后续" —— 所有变更都有具体文本
3. **类型一致性**: 模块名、类名、方法名在所有文档中一致（核对过源码）
4. **数字一致性**: 282 passed（pytest -q 实际运行确认）
5. **安全边界**: 无 Career/面试动机泄露到公开文档（纯技术事实描述）
