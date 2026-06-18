# Decision Research Agent Technical Identifier Migration Design

## Status

- Public product name: `Decision Research Agent`
- Canonical repository slug: `iTao-AI/decision-research-agent`
- Canonical local directory: `/Users/mac/Developer/Projects/Active/decision-research-agent`
- Migration strategy: staged compatibility

The GitHub repository and primary local directory were renamed on 2026-06-18 after the Talent P1A value gate passed. This design covers the remaining runtime, client, observability, documentation, and compatibility identifiers.

## Goal

Make `decision-research-agent` the canonical technical identity for new integrations without breaking existing clients that use `deep-search-agent`, `DEEP_SEARCH_AGENT_*`, the current health response, or historical links.

## Non-Goals

- Do not change existing `/api/*` or `/ws/*` routes.
- Do not rename SQLite tables, persisted IDs, benchmark IDs, profile IDs, or database defaults.
- Do not rewrite historical plans, archived OpenSpec changes, merged PR links, benchmark artifacts, or evidence records.
- Do not combine output-template optimization, P1B durable HITL, Skills, Async Subagent, or UI work with this migration.
- Do not change the health `service` value in this compatibility release.

## Options Considered

### Option A: Big-Bang Rename

Replace every old identifier, health value, environment variable, file name, path, and historical reference in one release.

Rejected because it breaks existing Tool Client deployments, invalidates historical evidence paths, and makes rollback ambiguous.

### Option B: Presentation-Only Rename

Keep all technical identifiers on `deep-search-agent` indefinitely and change only README titles.

Rejected because the repository has already moved and new integrations should not continue accumulating the obsolete prefix.

### Option C: Staged Compatibility Migration

Adopt new canonical identifiers for all new configuration and tooling, preserve bounded legacy aliases, and leave historical records unchanged.

Selected because it moves the product identity forward while keeping current clients operational and making every compatibility boundary testable.

## Canonical And Legacy Contracts

### Repository And Directory

Canonical values:

- GitHub: `https://github.com/iTao-AI/decision-research-agent`
- Local directory: `/Users/mac/Developer/Projects/Active/decision-research-agent`
- Git remote: `git@github.com:iTao-AI/decision-research-agent.git`

GitHub's old repository URL may redirect, but current documentation must use the canonical URL. Historical PR and evidence links remain unchanged because they resolve through GitHub redirects and preserve provenance.

### Environment Variables

New canonical variables:

| Canonical | Legacy alias |
|---|---|
| `DECISION_RESEARCH_AGENT_URL` | `DEEP_SEARCH_AGENT_URL` |
| `DECISION_RESEARCH_AGENT_API_KEY` | `DEEP_SEARCH_AGENT_API_KEY` |
| `DECISION_RESEARCH_AGENT_TIMEOUT_SECONDS` | `DEEP_SEARCH_AGENT_TIMEOUT_SECONDS` |
| `DECISION_RESEARCH_AGENT_ENABLE_BENCHMARK_FIXTURES` | `DEEP_SEARCH_AGENT_ENABLE_BENCHMARK_FIXTURES` |
| `DECISION_RESEARCH_AGENT_TALENT_RECURSION_LIMIT` | `DEEP_SEARCH_AGENT_TALENT_RECURSION_LIMIT` |

Resolution rules:

1. If the canonical variable exists, use it, including an explicitly empty value.
2. Otherwise, if the legacy alias exists, use it and emit a value-free
   `FutureWarning` once per resolver boundary and legacy key.
3. Otherwise, use the existing default.
4. Never log variable values, especially API keys.
5. Warning filters such as `PYTHONWARNINGS=error` must not turn legacy
   configuration into a startup failure.

Empty and invalid canonical values never fall through to legacy aliases:

| Setting | Empty canonical value | Invalid canonical value |
|---|---|---|
| API key | Explicit tombstone; no auth header | N/A |
| URL | Use the Tool Client default | Whitespace uses the default |
| Timeout | Use the Tool Client default | Non-numeric or non-positive uses the default |
| Benchmark fixture flag | Disabled | Any value except `true` is disabled |
| Talent recursion limit | Use the safe default | Non-numeric or non-positive uses the safe default |

The benchmark runner must set and restore the canonical fixture variable without leaking process state. Unit tests must retain explicit coverage for legacy fallback and canonical precedence.

### Health Contract

This release keeps the existing compatibility contract:

```json
{
  "status": "ok",
  "service": "deep-search-agent"
}
```

The complete payload remains unchanged because current integrations may compare
the object exactly. Canonical product discovery uses the repository, API title,
Tool Client, and current documentation. A future breaking release may switch
`service` only after consumer inventory and an explicit deprecation window.

### Tool Client

- Canonical entrypoint: `tools/decision_research_agent_tool.py`
- Legacy entrypoint: `tools/deep_search_agent_tool.py`

The implementation moves to the canonical module. The legacy file becomes a thin CLI/import compatibility shim and must not duplicate client logic. Documentation uses the canonical path and canonical environment variables.

### LangSmith

- New default project: `decision-research-agent-dev`
- Existing project: `deep-search-agent-dev`

Newly configured local runs use the new project through `.env.example` and observability documentation. Existing untracked `.env` files are not edited automatically; operators must opt in by changing `LANGSMITH_PROJECT`. Historical traces remain in the old project and are not copied, deleted, or treated as the business audit ledger. Privacy defaults remain `LANGSMITH_HIDE_INPUTS=true` and `LANGSMITH_HIDE_OUTPUTS=true`.

### API, Persistence, And Deployment

- REST and WebSocket paths remain unchanged.
- Docker Compose service names `backend`, `frontend`, and `mysql` remain unchanged.
- Existing Docker volume names and database defaults remain unchanged to avoid creating empty replacement stores.
- ResearchRun, EvidenceLedger, thread/run/segment identities, fixture IDs, and profile IDs remain unchanged.

## Runtime Design

Create `agent/runtime_env.py` as the server-side compatibility resolver. Agent runtime modules use it for benchmark fixture and Talent recursion settings. The standalone Tool Client keeps a small local resolver because direct execution with `python tools/decision_research_agent_tool.py` must not depend on repository-root import behavior.

The resolver emits no value data. It uses `FutureWarning` so operators can see
the migration requirement without enabling developer-only warnings. Warning
deduplication is lock-protected and local to each resolver boundary: the server
resolver and standalone Tool Client do not promise cross-module
deduplication. Canonical precedence is deterministic even when both names are
set.

## Documentation Policy

Update current entrypoints:

- `README.md`
- `README_CN.md`
- `.env.example`
- `CHANGELOG.md`
- `docs/README.md`
- `docs/AGENT_INTEGRATION.md`
- `docs/observability.md`
- `docs/decisions/product-naming.md`
- `docs/superpowers/specs/2026-06-18-technical-identifier-migration-design.md`
- `spec/api-contract.md`

Do not bulk-edit:

- `docs/superpowers/plans/` and earlier specs
- `docs/evidence/`
- `openspec/changes/archive/`
- merged PR URLs
- benchmark snapshots and historical execution paths

Historical documents describe the identity that existed when evidence was produced. Current index pages may add a migration note linking old and new names.

The existing README and architecture diagrams still describe valid generic-profile modules and data flows. This migration updates product labels and the project-root tree name, but does not redraw those diagrams or imply that the Talent direct structured path replaced the generic architecture.

## File-Level Scope

| File | Change |
|---|---|
| `agent/runtime_env.py` | Add canonical-first legacy env resolution and warning deduplication. |
| `agent/main_agent.py` | Resolve the canonical benchmark fixture flag through the shared helper. |
| `agent/talent_runtime.py` | Resolve the canonical recursion limit through the shared helper. |
| `tools/provided_aggregate.py` | Resolve the canonical benchmark fixture flag through the shared helper. |
| `scripts/talent_value_gate_runner.py` | Set and restore the canonical fixture flag for benchmark runs. |
| `tools/decision_research_agent_tool.py` | Become the canonical Tool Client implementation and env contract. |
| `tools/deep_search_agent_tool.py` | Remain as a compatibility shim. |
| `.env.example` | Publish canonical fixture and LangSmith defaults. |
| `README.md`, `README_CN.md` | Replace stale current-product and repository labels without rewriting architecture narrative. |
| `docs/README.md`, `docs/AGENT_INTEGRATION.md`, `docs/observability.md` | Make the migration discoverable and document canonical client, env, health, and LangSmith usage. |
| `docs/decisions/product-naming.md` | Record the completed repository rename and the remaining compatibility boundary. |
| `spec/api-contract.md` | Update the exact health/client configuration contract. |
| `CHANGELOG.md` | Add an Unreleased compatibility-migration entry without rewriting historical releases. |
| focused tests | Lock canonical precedence, legacy fallback, warning behavior, health compatibility, Tool Client shim, and benchmark env restoration. |

## Error And Rollback Behavior

- Invalid canonical numeric values follow the existing safe default behavior; they do not fall back to a conflicting legacy value.
- An explicitly empty canonical API key disables the key instead of exposing a legacy secret.
- Existing deployments should retain matching legacy keys during the rollback
  window. A fresh canonical-only installation must restore legacy keys before
  rolling back to pre-migration code.
- If the code migration is reverted, the GitHub repository can keep the new slug because old GitHub URLs redirect and runtime compatibility remains on the old identifiers.

Legacy aliases remain for at least two tagged releases after this migration.
Removal requires a separate approved breaking-change plan, a first-party
consumer inventory, no active first-party legacy use outside shims, tests, and
compatibility documentation, plus release-note migration instructions. The
repository currently has no tags, so this release does not start a fabricated
date-based countdown.

## Test Matrix

| Area | Required verification |
|---|---|
| Canonical env only | New key drives client URL, API key, timeout, fixture flag, and Talent recursion limit. |
| Legacy env only | Old key still works and emits a value-free deprecation warning. |
| Both env names | Canonical value wins deterministically. |
| Empty canonical secret | Legacy secret is not read. |
| Benchmark runner | Canonical fixture flag is restored after success and failure. |
| Health | The complete payload remains `{"status":"ok","service":"deep-search-agent"}`. |
| Tool paths | Canonical CLI works; legacy CLI produces the same behavior. |
| API routes | Existing REST and WebSocket route tests remain unchanged and pass. |
| Backend regression | Full `python -m pytest -q` passes. |
| Frontend regression | `npm run build` passes. |
| Docs | Current entrypoints use canonical names; historical sources are untouched. |

## Acceptance Criteria

1. The repository, local directory, and origin use `decision-research-agent`.
2. New documentation and examples use canonical environment variables and Tool Client path.
3. Existing legacy environment configurations continue to work without exposing values.
4. Health consumers that require `service=deep-search-agent` remain compatible.
5. Canonical identity discovery uses the repository, API title, Tool Client,
   and documentation rather than a health payload change.
6. New LangSmith runs default to `decision-research-agent-dev`; old traces remain untouched.
7. API paths, persisted data, benchmark identity, and historical evidence remain unchanged.
8. Upgrade and rollback documentation covers canonical-only, dual-key, and
   legacy-only configurations.
9. Focused tests, full backend tests, frontend build, and diff checks pass before the PR is presented for review.

## Delivery Boundary

The migration is delivered as one compatibility-focused PR with no behavioral feature work. The PR is not merged until user review is complete. Repository rename has already been performed and is independently reversible from the code PR.
