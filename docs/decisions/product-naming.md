# Product Naming

## Decision

- Public English product name: **Decision Research Agent**
- Canonical repository and technical identifier: `decision-research-agent`
- Health service identifier: `decision-research-agent`

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

## Technical Boundary

The active runtime, Tool Client, environment variables, Docker defaults, and
health response use the canonical identifier. Historical evidence, archived
plans, and archived OpenSpec records may keep their original wording as
immutable project history.
