# Implementation Tasks: Phase 4 — 可观测性升级

**Change ID:** `phase-4-observability`

---

## Phase A: Telemetry 核心数据结构

- [x] A.1 创建 `agent/telemetry.py`：TelemetryRecord dataclass（thread_id、agent_name、tool_name、duration_ms、status、error、timestamp）
- [x] A.2 创建 `TelemetryCollector` 类：record() / get_by_thread() / clear_thread() / 容量控制（500/session）
- [x] A.3 编写 `tests/unit/test_telemetry.py`：覆盖 record、query、容量淘汰、线程隔离、清理
- [x] A.4 全局单例 `collector` 导出

**Self-Check:**
- [x] `pytest tests/unit/test_telemetry.py` 全部通过（10 passed in 0.01s）
- [x] 容量淘汰测试：插入 501 条，验证只有 500 条且最旧的被移除

---

## Phase B: ToolMonitor 参数脱敏 + Telemetry 集成

- [x] B.1 在 `api/monitor.py` 中新增 `sanitize_args()` 函数：敏感字段名黑名单匹配 + 长值截断
- [x] B.2 修改 `report_tool()` / `report_assistant()` / `report_task_result()`：输出 args 前调用 sanitize_args
- [x] B.3 修改 `ToolMonitor`：report_start 记录开始时间，report_end 自动计算 duration 并生成 TelemetryRecord
- [x] B.4 编写 `tests/unit/test_monitor_sanitization.py`：覆盖敏感字段脱敏、长值截断、非字符串不截断

**Self-Check:**
- [x] `pytest tests/unit/test_monitor_sanitization.py` 全部通过（16 passed in 0.13s）
- [x] 验证 report_tool 输出的事件 data 中 args 已脱敏

---

## Phase C: API 端点 + 集成

- [x] C.1 在 `api/server.py` 中新增 `GET /api/telemetry/{thread_id}` 端点
- [x] C.2 编写 `tests/unit/test_telemetry_api.py`：覆盖存在/不存在 thread_id 的查询
- [x] C.3 编写 `tests/unit/test_telemetry_integration.py`：集成测试验证 ToolMonitor → TelemetryCollector → API 全链路
- [x] C.4 运行全量测试套件，确保无回归

**Self-Check:**
- [x] `pytest tests/` 全部通过（133 passed in 2.70s）
- [x] `python api/server.py` 能正常启动
- [x] 手动验证 `/api/telemetry/` 端点返回正确格式

---

## Completion Checklist

- [x] All phases complete
- [x] All quality gates passed
- [ ] Documentation synced
- [ ] Ready for `/openspec-archive-change`
