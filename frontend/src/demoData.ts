export const demoRun = {
  service: "decision-research-agent",
  mode: "demo data",
  health: "unavailable",
  runId: "run_demo_talent_2026_06_29",
  threadId: "demo-thread-interview-console",
  segmentId: "run_demo_talent_2026_06_29_seg_final",
  stateVersion: 17,
  profileId: "talent-hiring-signal",
  lifecycle: [
    "created",
    "running",
    "evidence_frozen",
    "review_required",
    "approved",
    "published",
    "delivered"
  ],
  telemetry: [
    "session_created",
    "tool_start: talent_public_search",
    "assistant_call: researcher",
    "task_result",
    "result_ready"
  ],
  evidence: [
    {
      id: "ev_001",
      source: "declared_fixture: talent-hiring-signal-v1",
      fingerprint: "sha256:5f4c...c9e1",
      citedBy: ["claim_candidate_signal", "finding_market_signal"],
      verification: "verified"
    },
    {
      id: "ev_002",
      source: "public web aggregate",
      fingerprint: "sha256:b82a...1140",
      citedBy: ["claim_benchmark_fit"],
      verification: "unverified"
    }
  ],
  review: {
    status: "approved",
    decisionId: "decision_demo_approved_001",
    stateVersion: 17,
    idempotency: "accepted replay-safe decision"
  },
  verification: {
    snapshot: "verification_snapshot_rev_3",
    baselineOrigin: "declared_fixture",
    status: "verified",
    publicationFreshness: "current"
  },
  artifact: {
    id: "decision-brief.md",
    mediaType: "text/markdown",
    revision: "publication_rev_3",
    contentHash: "sha256:bb64e1d4f8d2a9c7",
    safety: "hash verified / unsafe content rejected"
  },
  resultMarkdown:
    "## Canonical Decision Brief\n\nRecommendation: proceed with a bounded interview demo using static data. Evidence refs: ev_001, ev_002.\n\nDelivery authority: GET /api/runs/{run_id}/result.",
  cliGoldenPath:
    'python tools/decision_research_agent_tool.py run \\\n  --query "Compare the evidence behind the proposed decision" \\\n  --wait \\\n  --result'
};

export const architectureNodes = [
  "OpenClaw / Codex / Tool Client / REST",
  "FastAPI",
  "ResearchExecutionService",
  "DeepAgentsHarness",
  "LangChain Agent Framework",
  "LangGraph Runtime",
  "Application DB Authority",
  "LangSmith Diagnostics"
];
