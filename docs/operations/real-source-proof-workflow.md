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
8. Generate the report from the manifest and application database:

   ```bash
   python scripts/real_source_proof.py build-report \
     --manifest benchmarks/real-source-proof/talent-agent-hiring-signals-v1.json \
     --db-path "$DECISION_RESEARCH_AGENT_DB_PATH" \
     --run-id "$RUN_ID" \
     --output docs/evidence/real-source-proof.json
   ```

9. Check the complete report schema:

   ```bash
   python scripts/real_source_proof.py check-report \
     --report docs/evidence/real-source-proof.json
   ```

`build-report` verifies an idempotent finalization replay, rebuilds reviewed
artifacts from the immutable verification snapshot and accepted review
decision, and compares their UTF-8 bytes with the stored JSON and Markdown
artifacts.

## Limits

- A verified record means the persisted observation matched the source at
  decision time.
- It does not prove role availability, market coverage, future truth, or hiring
  outcome.
