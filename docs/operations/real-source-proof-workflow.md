# Real-Source Proof Workflow

This workflow proves a small sample path. It is not a crawler, benchmark, or
market-coverage claim.

## Prerequisites

- `DECISION_RESEARCH_AGENT_ENABLE_DURABLE_HITL=true`
- `DECISION_RESEARCH_AGENT_ENABLE_EVIDENCE_VERIFICATION=true`
- `API_SECRET` set for local operator auth
- backend running against a disposable local SQLite database

## Steps

1. Validate the manifest hash.
2. Seed the proof run.
3. Open each public source URL manually.
4. Use `python tools/decision_research_agent_tool.py evidence show ...`.
5. Use `evidence verify --confirm-source-match` or `evidence reject`.
6. Use `evidence finalize`.
7. Use `review show`, `review approve --wait`, and `review wait`.
8. Generate and check the proof report.

## Limits

- A verified record means the persisted observation matched the source at
  decision time.
- It does not prove role availability, market coverage, future truth, or hiring
  outcome.
