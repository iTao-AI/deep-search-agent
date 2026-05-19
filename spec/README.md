# 技术参考文档 (spec/)

本目录包含 Deep Search Agent 系统的技术参考文档。与 `openspec/specs/` 不同，这里是**系统当前状态的完整快照**，不随 OpenSpec 变更流程自动管理。

## 文档清单

| 文件 | 内容 | AI 注入时机 |
|------|------|------------|
| [architecture.md](architecture.md) | 架构图、模块职责、数据流 | 架构相关任务时 |
| [api-contract.md](api-contract.md) | REST + WebSocket 端点定义 | 修改 API 时 |
| [data-models.md](data-models.md) | 数据模型、Schema、输入输出格式 | 数据结构变更时 |
| [tool-registry.md](tool-registry.md) | 工具接口清单 | 新增/修改工具时 |
| [state-machine.md](state-machine.md) | LangGraph 图结构、状态流转 | Agent 流程修改时 |
| [external-services.md](external-services.md) | 外部依赖清单、SLA、超时 | 工具韧性/集成时 |

## 维护规则

- 这些文档由 AI 在实现变更时同步更新
- 每次变更对应一个 `docs/decisions/` 下的 ADR
- 新的 AI 会话开始时，读取相关文件注入上下文
