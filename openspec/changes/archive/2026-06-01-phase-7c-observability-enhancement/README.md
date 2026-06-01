# Phase 7c: 可观测性增强（Token 追踪 + 工具缓存）

**Status:** Merged to main
**PR:** https://github.com/iTao-AI/deep-search-agent/pull/11
**Commits:**
- feat(phase-7c): add TokenUsageData, TokenUsageCollector, TokenTrackingCallbackHandler
- feat(phase-7c): add TTLCache + @cached_tool decorator
- feat(phase-7c): integrate token tracking + tavily cache
- feat(phase-7c): add token-usage REST endpoint + fix tavily test import
- chore(phase-7c): add openspec proposal, design, and specs
- fix(phase-7c): add report_cache_hit to monitor + resolve forward ref
- fix(phase-7c): P1 - read token usage from real LLMResult shape; P2 - fix Tavily cache TTL to 300s

## Summary
- **Token 追踪**: TokenUsageData + TokenUsageCollector + TokenTrackingCallbackHandler + /api/token-usage 端点
- **工具缓存**: TTLCache + @cached_tool 装饰器，已应用到 Tavily（5 分钟 TTL）
- **26 个单元测试**: 15 token_tracking + 11 cache
- **回归**: 208 passed, 0 failures
