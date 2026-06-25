from agent.runtime_context import ResearchRuntimeContext


def test_runtime_context_normalizes_policy_to_tuples():
    context = ResearchRuntimeContext(
        thread_id="thread_1",
        run_id="run_1",
        segment_id="segment_1",
        profile_id="generic",
        allowed_source_domains=["example.com"],
        allowed_source_types=["public_web"],
        allowed_aggregate_ids=[],
    )

    assert context.allowed_source_domains == ("example.com",)
