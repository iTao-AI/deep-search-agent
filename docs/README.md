# Deep Search Agent — 项目文档

## 文档索引

| 文档 | 说明 |
|------|------|
| [PRD](prd.md) | 产品需求文档 — 产品愿景、目标用户、核心功能、成功指标 |
| [决策记录](decisions/) | ADR（架构决策记录）— 记录为什么选择 A 而不是 B |

## 技术参考文档

技术参考文档位于项目根目录 `spec/` 下，包含：

| 文档 | 说明 |
|------|------|
| [architecture.md](../spec/architecture.md) | 系统架构、模块职责、数据流 |
| [api-contract.md](../spec/api-contract.md) | REST + WebSocket API 端点定义 |
| [data-models.md](../spec/data-models.md) | 数据模型、Session Workspace、子 Agent 输入输出 |
| [tool-registry.md](../spec/tool-registry.md) | 工具接口定义清单 |
| [state-machine.md](../spec/state-machine.md) | LangGraph 图结构、节点定义、状态流转 |
| [external-services.md](../spec/external-services.md) | 外部依赖清单、SLA、超时/降级策略 |

## 与 openspec/ 的区别

- **`docs/`** — 产品意图和架构决策（为什么）
- **`spec/`** — 系统当前技术状态的快照（现在是什么）
- **`openspec/`** — 变更过程管理（这次改了什么），由 OpenSpec 工具自动管理
