"""Runtime limits for the Talent Hiring Signal profile."""
from __future__ import annotations

import os


DEFAULT_TALENT_RECURSION_LIMIT = 160


def talent_recursion_limit() -> int:
    configured = os.environ.get("DECISION_RESEARCH_AGENT_TALENT_RECURSION_LIMIT")
    if configured is None or not configured.strip():
        return DEFAULT_TALENT_RECURSION_LIMIT
    try:
        limit = int(configured)
    except ValueError:
        return DEFAULT_TALENT_RECURSION_LIMIT
    if limit < 1:
        return DEFAULT_TALENT_RECURSION_LIMIT
    return limit
