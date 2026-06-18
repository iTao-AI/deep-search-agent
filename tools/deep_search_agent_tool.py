"""Deprecated compatibility entrypoint for Decision Research Agent tooling."""
from __future__ import annotations

try:
    from tools.decision_research_agent_tool import (
        ToolClientError,
        ToolConfig,
        _build_parser,
        config_from_env,
        doctor,
        get_run,
        get_task,
        healthcheck,
        main,
        profile_manifest,
        research_run,
        research_runs,
        start_run,
        start_task,
        token_usage,
        wait_for_run,
    )
except ModuleNotFoundError as exc:
    if exc.name not in {"tools", "tools.decision_research_agent_tool"}:
        raise
    from decision_research_agent_tool import (
        ToolClientError,
        ToolConfig,
        _build_parser,
        config_from_env,
        doctor,
        get_run,
        get_task,
        healthcheck,
        main,
        profile_manifest,
        research_run,
        research_runs,
        start_run,
        start_task,
        token_usage,
        wait_for_run,
    )


__all__ = [
    "ToolClientError",
    "ToolConfig",
    "config_from_env",
    "doctor",
    "get_run",
    "get_task",
    "healthcheck",
    "main",
    "profile_manifest",
    "research_run",
    "research_runs",
    "start_run",
    "start_task",
    "token_usage",
    "wait_for_run",
]


if __name__ == "__main__":
    raise SystemExit(main())
