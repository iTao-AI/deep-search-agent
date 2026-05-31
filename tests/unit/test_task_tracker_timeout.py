"""任务超时管理单元测试 — Phase 7b"""
import asyncio
import os
import sys

import pytest


class TestTaskTrackerTimeout:
    """测试任务超时功能"""

    @pytest.mark.asyncio
    async def test_task_tracked_with_timeout(self):
        """创建的任务应被跟踪，完成后自动移除"""
        from api.task_tracker import (
            clear_active_tasks,
            create_tracked_task,
            get_active_task,
        )

        clear_active_tasks()

        async def dummy():
            await asyncio.sleep(0.1)
            return "done"

        task = create_tracked_task(dummy(), "timeout-test-1", timeout_seconds=1800)
        assert get_active_task("timeout-test-1") is not None

        await asyncio.sleep(0.2)
        assert get_active_task("timeout-test-1") is None

    @pytest.mark.asyncio
    async def test_check_timeouts_cancels_long_running_task(self):
        """超时任务应被取消"""
        from api.task_tracker import (
            check_timeouts,
            clear_active_tasks,
            create_tracked_task,
        )

        clear_active_tasks()

        async def slow():
            await asyncio.sleep(100)
            return "done"

        # 创建超时为 0.1 秒的任务
        task = create_tracked_task(slow(), "timeout-test-2", timeout_seconds=1)

        # 等待超时
        await asyncio.sleep(1.5)

        cancelled = check_timeouts()
        assert "timeout-test-2" in cancelled
        # Give the event loop a chance to process the cancellation
        await asyncio.sleep(0)
        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_default_timeout_from_env(self):
        """默认超时应从环境变量读取"""
        # 清除已缓存的模块
        sys.modules.pop("api.task_tracker", None)
        sys.modules.pop("api", None)

        old_val = os.environ.get("AGENT_TASK_TIMEOUT_SECONDS")
        os.environ["AGENT_TASK_TIMEOUT_SECONDS"] = "600"

        from api import task_tracker
        import importlib

        importlib.reload(task_tracker)

        assert task_tracker.DEFAULT_TASK_TIMEOUT == 600

        if old_val is None:
            os.environ.pop("AGENT_TASK_TIMEOUT_SECONDS", None)
        else:
            os.environ["AGENT_TASK_TIMEOUT_SECONDS"] = old_val
