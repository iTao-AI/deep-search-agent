# Evidence Pack

本目录沉淀 Deep Search Agent 的运行证据，用于审查项目真实能力。

## 目录

| 文件 | 说明 |
|------|------|
| [run-log.md](run-log.md) | E2E Run #1 数据（282s / 459K tokens / 2 子Agent）+ Phase 8 收口 + Phase 9 确定性终态实现；benchmark 待后续稳定脚本补充 |
| [technical-decisions.md](technical-decisions.md) | 关键技术决策说明与代码路径 |

## Phase 9 产出（2026-06-03）

- 确定性终态：`completed` / `completed_with_fallback` / `failed`
- Fallback 报告生成：当 agent 未产出正式报告时，系统自动生成含诊断信息的兜底报告
- Timeout 回调：超时任务在取消前持久化 `failed` 状态
- 测试：282 passed, 0 failed（含 `test_task_finalizer.py`、`test_persistence.py` 中 Phase 9 相关用例）

## 已有截图

运行截图（由 Docker QA 报告提取，存放于 `assets/` 目录）：
- [01-homepage.png](assets/01-homepage.png)
- [02-mobile.png](assets/02-mobile.png)
- [03-tablet.png](assets/03-tablet.png)
- [Docker QA 摘要](assets/qa-report-summary.md)

## 数据来源

所有数字指标来自实际命令输出、日志或测试报告，不以推测数字占位。
