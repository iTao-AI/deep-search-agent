# Run Log

本文件记录端到端任务执行的实际数据。当前尚未运行专项基准测试，以下指标待后续填充。

**计划测量项：**

- 平均耗时与 P95 耗时：使用 5-10 个固定任务样例，记录完成时间分布。
- Token 消耗：通过已有 `token_tracking.py` 和 `GET /api/token-usage/{thread_id}` 记录 input/output/total token。
- 子 Agent 调用次数：记录单次任务中主 Agent 派发子 Agent 的次数。
- 缓存命中率：对比 Tavily 搜索在短时间重复查询时的缓存命中情况。

**前端构建：**

- `cd frontend && npm install`：成功
- `cd frontend && npm run build`：成功，输出 "built in 357ms"

**已有数据：**

- Local pytest run: 247 passed, 0 failed（`python -m pytest -q`）
- Docker 部署: 本机验证通过（见 [QA 报告摘要](assets/qa-report-summary.md)）

## E2E Run #1

- **日期**: 2026-06-01
- **环境**: 本机 (macOS, Python 3.13, DeepSeek API)
- **输入问题**: "2024年AI发展趋势"
- **命令**: POST /api/task + WebSocket /ws/evidence-run-002
- **总耗时**: 4 分 42 秒 (281.97s)
- **子 Agent 调用**: 网络搜索助手 (2 次，分别搜索技术突破和行业动态)
- **工具调用**: 网络搜索工具 (Tavily，多次搜索查询)
- **WebSocket 事件**: 50 个 monitor_event (session_created → assistant_call → tool_start → task_result)
- **Token 用量**: input: 446,542 / output: 12,723 / total: 459,265 / cost: $19.39 / calls: 21
- **生成产物**: `output/session_evidence-run-002/2024年AI发展趋势报告.md` (12,142 bytes)
- **备注**: WebSocket 180s 超时后断开，但报告文件已完整生成；未生成 PDF（需 WeasyPrint 系统依赖）
