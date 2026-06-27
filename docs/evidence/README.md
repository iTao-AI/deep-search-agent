# Release Evidence

This directory retains only bounded evidence used by current release gates.
Each artifact states its own scope and limits; presence in this directory does
not grant independent verification authority.

| Artifact | Boundary |
|---|---|
| [durable-hitl-gate-report.json](durable-hitl-gate-report.json) | Machine-readable result for the 13 controlled single-node SQLite durability and safety gates. |
| [real-source-proof.json](real-source-proof.json) | Machine-readable bounded real-source workflow proof and report hashes. |
| [real-source-proof.md](real-source-proof.md) | Human-readable proof procedure, verification/publication outcome, and explicit limitations. |

The durable HITL artifact proves only the documented feasibility boundary; its
feature flag remains disabled by default. The real-source artifact proves a
small declared workflow sample, not source archiving, automatic truth
verification, market coverage, or hiring outcomes.
