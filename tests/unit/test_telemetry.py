import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest


class TestTelemetryRecord:
    def test_create_success_record(self):
        from agent.telemetry import TelemetryRecord

        record = TelemetryRecord(
            thread_id="thread-1",
            agent_name="main_agent",
            tool_name="tavily_search",
            duration_ms=120.5,
            status="success",
        )

        assert record.thread_id == "thread-1"
        assert record.agent_name == "main_agent"
        assert record.tool_name == "tavily_search"
        assert record.duration_ms == 120.5
        assert record.status == "success"
        assert record.error is None
        assert isinstance(record.timestamp, datetime)

    def test_create_error_record(self):
        from agent.telemetry import TelemetryRecord

        record = TelemetryRecord(
            thread_id="thread-2",
            agent_name="db_agent",
            tool_name="mysql_query",
            duration_ms=5000.0,
            status="error",
            error="Connection timeout after 5s",
        )

        assert record.thread_id == "thread-2"
        assert record.status == "error"
        assert record.error == "Connection timeout after 5s"


class TestTelemetryCollector:
    def _get_collector(self):
        from agent.telemetry import TelemetryCollector
        return TelemetryCollector()

    def test_record_and_query(self):
        collector = self._get_collector()
        from agent.telemetry import TelemetryRecord

        collector.record(TelemetryRecord(
            thread_id="t1", agent_name="a1", tool_name="tool_a",
            duration_ms=10.0, status="success",
        ))
        collector.record(TelemetryRecord(
            thread_id="t1", agent_name="a1", tool_name="tool_b",
            duration_ms=20.0, status="success",
        ))

        results = collector.get_by_thread("t1")
        assert len(results) == 2
        assert results[0].tool_name == "tool_a"
        assert results[1].tool_name == "tool_b"

    def test_query_nonexistent_thread(self):
        collector = self._get_collector()
        results = collector.get_by_thread("nonexistent")
        assert results == []

    def test_clear_thread(self):
        collector = self._get_collector()
        from agent.telemetry import TelemetryRecord

        collector.record(TelemetryRecord(
            thread_id="t1", agent_name="a1", tool_name="tool_x",
            duration_ms=5.0, status="success",
        ))
        assert len(collector.get_by_thread("t1")) == 1

        collector.clear_thread("t1")
        assert collector.get_by_thread("t1") == []

    def test_clear_nonexistent_thread(self):
        collector = self._get_collector()
        # Should not raise
        collector.clear_thread("does-not-exist")
        assert collector.get_by_thread("does-not-exist") == []

    def test_clear_doesnt_affect_other_threads(self):
        collector = self._get_collector()
        from agent.telemetry import TelemetryRecord

        collector.record(TelemetryRecord(
            thread_id="t1", agent_name="a1", tool_name="tool_1",
            duration_ms=1.0, status="success",
        ))
        collector.record(TelemetryRecord(
            thread_id="t2", agent_name="a2", tool_name="tool_2",
            duration_ms=2.0, status="success",
        ))

        collector.clear_thread("t1")

        assert collector.get_by_thread("t1") == []
        assert len(collector.get_by_thread("t2")) == 1
        assert collector.get_by_thread("t2")[0].tool_name == "tool_2"


class TestCapacityControl:
    def test_eviction_at_500_limit(self):
        from agent.telemetry import TelemetryCollector, TelemetryRecord

        collector = TelemetryCollector()

        # Insert 501 records with distinct tool names
        for i in range(501):
            collector.record(TelemetryRecord(
                thread_id="cap-test",
                agent_name="a1",
                tool_name=f"tool_{i}",
                duration_ms=float(i),
                status="success",
            ))
            # Sleep 1ms every 100 inserts to ensure different timestamps
            if (i + 1) % 100 == 0:
                time.sleep(0.001)

        results = collector.get_by_thread("cap-test")
        assert len(results) == 500

        # Oldest (tool_0) should be evicted
        tool_names = [r.tool_name for r in results]
        assert "tool_0" not in tool_names
        # Newest (tool_500) should be present
        assert "tool_500" in tool_names


class TestGlobalCollector:
    def test_global_collector_exists(self):
        from agent.telemetry import collector
        assert collector is not None

    def test_global_collector_has_methods(self):
        from agent.telemetry import collector
        assert hasattr(collector, "record")
        assert hasattr(collector, "get_by_thread")
