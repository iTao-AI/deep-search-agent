# P2A Real-Source Proof

Executed on 2026-06-25 against the fixed
`talent-agent-hiring-signals-v1` manifest.

## Result

- Manifest hash:
  `56dfe83dcc206d5517f94011b628744075d9676a0aaeceb4863efe30d4241dee`
- Run: `run_2638ec8f89ee49c8b7ff2b7f506d3615`
- Sources inspected: 6
- Human verification: 6 verified, 0 rejected, 0 unresolved
- Publication: revision 2, current, `ready`
- Fresh review: revision 2, `approved`
- Delivery: `ready`
- Finalization replay: idempotent
- Rebuilt artifact bytes: stable

Both reviewed artifacts resolve to logical DecisionBrief content hash
`b79376ffaa0dbefebae28122b44e4da8f7f7de434dc6349f4a97418b62bc526a`.
Their serialized UTF-8 bytes are intentionally distinct:

- JSON SHA-256:
  `c72dbcb53b63dd968799226c8ccb59194809505d23f2528206ae7d095d5b8f7c`
- Markdown SHA-256:
  `3c850d255697a83097e1c02c3e0926eeb25266e35cb3b58f269bfcfeeed23354`

## Sources

| Sample | Source | Decision |
|---|---|---|
| `real_source_001` | [OpenAI: Software Engineer, Agent Infrastructure](https://openai.com/careers/software-engineer-agent-infrastructure-san-francisco/) | `verify` |
| `real_source_002` | [OpenAI: Applied AI Engineer, Codex Core Agent](https://openai.com/careers/applied-ai-engineer-codex-core-agent-san-francisco/) | `verify` |
| `real_source_003` | [OpenAI: Software Engineer, Cloud Agents](https://openai.com/careers/software-engineer-cloud-agents-san-francisco/) | `verify` |
| `real_source_004` | [LangChain: Fullstack Software Engineer, Applied AI](https://jobs.ashbyhq.com/langchain/c75915ba-a32b-4e17-873d-19b47564170d) | `verify` |
| `real_source_005` | [Google: Software Engineer, Agentic AI Systems, Cloud Security](https://www.google.com/about/careers/applications/jobs/results/138036920247558854-software-engineer-aiml-agentic-ai-systems-cloud-security) | `verify` |
| `real_source_006` | [Google: Senior Software Engineer, Agentic AI Systems, Cloud Security](https://www.google.com/about/careers/applications/jobs/results/106025468234212038-senior-software-engineer-agentic-ai-systems-cloud-security) | `verify` |

Each decision was made after comparing the persisted observation with the
identified public source. The LangChain page is JavaScript-rendered; its
listing was also checked through the official Ashby job-board posting API.

## Boundary

This report proves one fixed six-record workflow through ordinary Evidence,
human verification, immutable publication, and fresh durable review. It is not
a crawler, source archive, market-coverage benchmark, role-availability
guarantee, hiring-outcome claim, or production-readiness claim.

The machine-readable result is
[p2a-real-source-proof.json](p2a-real-source-proof.json).
