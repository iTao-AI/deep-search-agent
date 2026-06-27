"""CORS allowlist configuration."""
import os


_ALLOWED_ORIGIN_ENV = "DECISION_RESEARCH_AGENT_CORS_ALLOWED_ORIGIN"


def get_allowed_origins() -> list[str]:
    """Return the single configured browser origin, or deny by default."""
    allowed_origin = os.getenv(_ALLOWED_ORIGIN_ENV)
    return [allowed_origin] if allowed_origin else []


def validate_cors_origin(origin: str) -> bool:
    """Return whether an Origin header is explicitly allowed."""
    return origin in get_allowed_origins()
