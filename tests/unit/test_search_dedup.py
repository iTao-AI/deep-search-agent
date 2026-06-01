"""Test search query deduplication within a single task."""
import pytest
from unittest.mock import MagicMock


class TestSearchDedup:
    """Test that identical queries are not re-executed within same task."""

    def test_dedup_same_query_uses_cache(self):
        """Same query within a task returns cached result without calling again."""
        from tools.tavily_tools import search_with_dedup, clear_search_cache

        clear_search_cache()
        mock_fn = MagicMock(return_value={"results": "data"})

        results_1 = search_with_dedup("AI trends", search_fn=mock_fn, thread_id="test-dedup")
        results_2 = search_with_dedup("AI trends", search_fn=mock_fn, thread_id="test-dedup")

        assert results_1 == results_2
        # mock_fn should only have been called once (second call hit cache)
        assert mock_fn.call_count == 1
        clear_search_cache("test-dedup")

    def test_different_query_not_deduped(self):
        """Different queries should NOT be deduped."""
        from tools.tavily_tools import search_with_dedup, clear_search_cache

        clear_search_cache()
        mock_fn = MagicMock(side_effect=lambda q, **kw: {"results": q})

        results_1 = search_with_dedup("AI trends", search_fn=mock_fn, thread_id="test-dedup-2")
        results_2 = search_with_dedup("quantum computing", search_fn=mock_fn, thread_id="test-dedup-2")

        assert results_1 != results_2
        assert mock_fn.call_count == 2
        clear_search_cache("test-dedup-2")

    def test_dedup_scoped_per_thread(self):
        """Dedup cache is isolated per thread_id."""
        from tools.tavily_tools import search_with_dedup, clear_search_cache

        clear_search_cache()
        mock_fn = MagicMock(return_value={"results": "data"})

        results_a = search_with_dedup("AI trends", search_fn=mock_fn, thread_id="thread-a")
        results_b = search_with_dedup("AI trends", search_fn=mock_fn, thread_id="thread-b")

        # Different threads should have separate caches — two calls
        assert mock_fn.call_count == 2
        clear_search_cache("thread-a")
        clear_search_cache("thread-b")
