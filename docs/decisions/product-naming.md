# Product Naming

## Decision

- Public English product name: **Decision Research Agent**
- Canonical repository and technical identifier: `decision-research-agent`
- Compatibility service identifier: `deep-search-agent`

The repository and primary local directory were renamed on 2026-06-18 after
the Talent P1A value gate passed. New configuration, Tool Client usage, and
LangSmith examples use the canonical identity.

## Evidence Boundary

The name is supported by the implemented agent runtime, evidence lifecycle,
EvidenceLedger, ResearchRun identity model, deterministic DecisionBrief
contracts, and the completed Talent value gate. It does not claim that every
source is verified or that the service makes decisions for users.

Durable HITL, runtime Skills, Async Subagent, and other deferred capabilities
are not implied by the name.

## Compatibility Boundary

The following identifiers remain unchanged in this compatibility release:

- Exact health response: `{"status":"ok","service":"deep-search-agent"}`
- Legacy `DEEP_SEARCH_AGENT_*` environment aliases
- `tools/deep_search_agent_tool.py` compatibility shim
- Existing API paths, persisted identities, Docker resources, profile IDs,
  benchmark IDs, and historical evidence

Canonical presence always wins over a legacy alias, including an empty
canonical value. Legacy use emits a value-free `FutureWarning`.

Legacy removal is a future breaking change. It requires at least two tagged
releases after this migration, a separate approved plan, a first-party consumer
inventory, no active first-party legacy use outside compatibility surfaces, and
release-note migration instructions.
