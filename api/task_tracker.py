"""异步任务错误处理和超时管理"""
import asyncio
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# 默认任务超时（秒）— 30 分钟
DEFAULT_TASK_TIMEOUT = int(os.getenv("AGENT_TASK_TIMEOUT_SECONDS", "1800"))

# 活跃任务字典: task_id -> (asyncio.Task, timeout_seconds, start_time)
active_tasks: Dict[str, tuple] = {}


def create_tracked_task(
    coroutine, task_id: str, timeout_seconds: int = DEFAULT_TASK_TIMEOUT
) -> asyncio.Task:
    """创建并跟踪异步任务，带超时保护。

    Args:
        coroutine: 要执行的协程
        task_id: 任务标识
        timeout_seconds: 超时时间（秒），默认从环境变量 AGENT_TASK_TIMEOUT_SECONDS 读取

    Returns:
        asyncio.Task: 创建的任务对象
    """
    task = asyncio.create_task(coroutine)
    start_time = asyncio.get_event_loop().time()
    active_tasks[task_id] = (task, timeout_seconds, start_time)
    task.add_done_callback(lambda t: _on_task_done(t, task_id))
    return task


def _on_task_done(task: asyncio.Task, task_id: str):
    """任务完成回调"""
    # 从活跃字典中移除
    active_tasks.pop(task_id, None)

    # 检查异常
    try:
        exc = task.exception()
        if exc:
            if isinstance(exc, asyncio.CancelledError):
                logger.info(f"Task {task_id} was cancelled (possibly due to timeout)")
            else:
                logger.error(f"Task {task_id} failed with exception: {exc}")
    except asyncio.CancelledError:
        logger.info(f"Task {task_id} was cancelled")
    except Exception:
        pass


def check_timeouts() -> list:
    """检查所有活跃任务是否超时，超时则取消。

    Returns:
        被取消的任务 ID 列表
    """
    cancelled = []
    now = asyncio.get_event_loop().time()
    timed_out_ids = []

    for task_id, (task, timeout_seconds, start_time) in active_tasks.items():
        elapsed = now - start_time
        if elapsed > timeout_seconds:
            timed_out_ids.append(task_id)

    for task_id in timed_out_ids:
        if task_id in active_tasks:
            task, timeout_seconds, _ = active_tasks[task_id]
            logger.warning(
                f"Task {task_id} timed out after {timeout_seconds}s, cancelling"
            )
            task.cancel()
            cancelled.append(task_id)

    return cancelled


def get_active_task(task_id: str) -> asyncio.Task | None:
    """获取指定任务"""
    entry = active_tasks.get(task_id)
    return entry[0] if entry else None


def clear_active_tasks():
    """清理所有活跃任务（测试用）"""
    active_tasks.clear()
