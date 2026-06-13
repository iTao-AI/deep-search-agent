# Talent Hiring Signal Benchmark v1

This benchmark uses five declared public-job-posting snapshots captured on
2026-06-09. It is intentionally bounded and must not be interpreted as a
market-wide hiring analysis.

## Run Boundary

- Set `DEEP_SEARCH_AGENT_ENABLE_BENCHMARK_FIXTURES=true`.
- Submit `research-scope.json` with `profile_id=talent-hiring-signal`.
- The `provided_aggregate` tool can resolve only the aggregate ID declared in
  that validated scope.
- The fixture provider is disabled by default and never accepts file paths.

## Limitations

- The source URLs may expire or redirect to access-verification pages.
- The bundled fixture preserves a concise source-backed snapshot for repeatable
  comparison; it does not claim the jobs remain open.
- Five selected postings do not represent overall demand, salary trends, or
  hiring volume.
