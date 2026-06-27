# Tool Registry

Decision Research Agent exposes tools through the DeepAgents/LangChain harness.
The service layer decides which profile may use which tools; tools remain
untrusted inputs to the application ledger until validated and persisted by the
service-owned contracts.

## Runtime Tool Surfaces

| Surface | Files | Used by | Notes |
|---|---|---|---|
| Public web search | `tools/tavily_tools.py`, `tools/talent_search.py` | Generic profile, bounded Talent profile | Talent search applies declared scope allowlists and post-filtering before evidence publication. |
| Provided aggregate fixture | `tools/provided_aggregate.py` | Talent benchmark/profile only when explicitly enabled | Default disabled; requires canonical fixture flag and declared aggregate allowlist. |
| MySQL query helper | `tools/mysql_tools.py`, `tools/db_connection.py` | Generic profile | Uses configured MySQL pool; not a business ledger. |
| RAGFlow retrieval helper | `tools/ragflow_tools.py` | Generic profile | Optional external knowledge retrieval helper. |
| Retry/cache helpers | `tools/retry_utils.py`, `tools/cache.py` | Tool implementation support | Internal helpers, not agent-facing tools. |
| Integration Tool Client | `tools/decision_research_agent_tool.py` | Operators and first-party automation | Calls the public HTTP API; it is not registered as an agent tool. |

## Skills

The generic profile loads read-only DeepAgents skills from:

- `skills/research-planning/SKILL.md`
- `skills/evidence-synthesis-and-reporting/SKILL.md`

The Talent profile intentionally does not load runtime skills or arbitrary
filesystem tools. Talent findings and claims must bind to current-run evidence
IDs validated by the application service.

Generic virtual workspace and Skills are DeepAgents harness capabilities, not
application database authority. Anything intended for delivery must still pass
the service-owned outcome, artifact, and safety contracts.

## Registration Rules

1. Register tools through profile-specific harness policy, not global hidden
   imports.
2. Keep Talent tools fail-closed: missing fixture gate, undeclared aggregate,
   invalid source type, invented evidence reference, or out-of-scope URL must
   block readiness.
3. Do not let tools write directly to authoritative run, review, verification,
   or publication tables. Persist only through service/repository contracts.
4. Treat tool output as untrusted text until schema, evidence reference, and
   safety checks pass.
5. Update this registry, affected profile tests, and API/operator docs whenever
   a public tool surface changes.

## Removed Surfaces

v0.1.0 runtime cleanup removed the old thread/task runtime, upload-file shared
workspace tools, in-agent report-generation tooling, and old shared-context
tool contracts from the active product surface. Historical documents may
mention them, but active contracts must use canonical run/result delivery.

## Change Log

| Date | Change |
|---|---|
| 2026-05-19 | Initial tool registry |
| 2026-06-26 | Replaced removed workspace/report tools with current DeepAgents-native tool surfaces |
