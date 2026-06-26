# Run Identity Boundaries

The P0B audit found 276 source references to `thread_id` across runtime, API, tools,
and scripts. These references must not be mechanically renamed.

## Keep as `thread_id`

- LangGraph `configurable.thread_id` and future checkpoint resume cursor.
- Caller conversation/session grouping.
- Caller conversation/session grouping for canonical run APIs.

## Use `run_id`

- Workspace directory and runtime context for `/api/runs`.
- Search de-duplication cache key.
- Token collection key.
- New ResearchRun, segment, and evidence persistence.
- New task tracking and result polling identity.

## Carry both

- LangSmith metadata and future monitor/telemetry events.
- Logs and diagnostics needed to correlate caller sessions with executions.
- Migration responses and operational diagnostics.

`POST /api/runs` permits same-thread concurrency after telemetry, WebSocket routing,
token collection, workspace, harness context, and search cache passed run-isolation tests.
