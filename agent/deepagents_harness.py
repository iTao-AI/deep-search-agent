"""DeepAgents-native generic research harness assembly."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    create_deep_agent,
    register_harness_profile,
)
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.middleware.filesystem import FilesystemPermission

from agent.profile_middleware import build_profile_middleware
from agent.profile_registry import profile_registry
from agent.research_agents import compile_generic_researchers
from agent.runtime_context import ResearchRuntimeContext

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_SKILLS_ROOT = _REPOSITORY_ROOT / "skills"
_REQUIRED_SKILLS = (
    "research-planning",
    "evidence-synthesis-and-reporting",
)

GENERIC_COORDINATOR_PROMPT = """
Coordinate bounded research using only the named researchers and server-owned
tools. Read the available Skills before planning. Keep working notes under
/workspace/. Record evidence gaps instead of inventing facts. When synthesis
is complete, write the canonical Markdown candidate exactly to
/workspace/research-report.md.
""".strip()


class HarnessConfigurationError(RuntimeError):
    """Stable fail-closed error for invalid harness release assets."""


@dataclass(frozen=True)
class DeepAgentsHarness:
    """Compiled generic graph plus its server-owned harness policy."""

    graph: Any
    backend: CompositeBackend
    permissions: tuple[FilesystemPermission, ...]
    skills: tuple[str, ...]

    def backend_contract(self) -> dict[str, Any]:
        skills_backend = self.backend.routes["/skills/"]
        return {
            "default": type(self.backend.default).__name__,
            "routes": {
                route: type(backend).__name__
                for route, backend in self.backend.routes.items()
            },
            "virtual_mode": skills_backend.virtual_mode,
        }

    def permission_for(
        self,
        operation: Literal["read", "write"],
        path: str,
    ) -> str:
        for rule in self.permissions:
            if operation not in rule.operations:
                continue
            if any(_matches_permission_path(path, pattern) for pattern in rule.paths):
                return rule.mode
        return "allow"


def _matches_permission_path(path: str, pattern: str) -> bool:
    if pattern == "/**":
        return path.startswith("/")
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")
    return path == pattern


def build_filesystem_permissions() -> list[FilesystemPermission]:
    """Build the security-critical first-match-wins permission list."""
    return [
        FilesystemPermission(
            operations=["write"],
            paths=["/skills/**"],
            mode="deny",
        ),
        FilesystemPermission(
            operations=["read"],
            paths=["/skills/**"],
            mode="allow",
        ),
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/workspace/**"],
            mode="allow",
        ),
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/**"],
            mode="deny",
        ),
    ]


def _read_required_skills(skills_root: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    try:
        for name in _REQUIRED_SKILLS:
            path = skills_root / name / "SKILL.md"
            content = path.read_text(encoding="utf-8")
            if (
                not content.startswith("---\n")
                or f"\nname: {name}\n" not in content
                or "\ndescription:" not in content
            ):
                raise ValueError(f"incomplete Skill: {name}")
            loaded[name] = content
    except (OSError, UnicodeError, ValueError) as exc:
        raise HarnessConfigurationError("harness_assets_missing") from exc
    return loaded


def load_skill_names(
    profile_id: str,
    *,
    skills_root: Path | None = None,
) -> set[str]:
    if profile_id == "talent-hiring-signal":
        return set()
    if profile_id != "generic":
        raise KeyError(f"unknown profile: {profile_id}")
    return set(_read_required_skills(skills_root or _DEFAULT_SKILLS_ROOT))


def _register_generic_harness_profile(model: Any) -> None:
    if isinstance(model, str):
        provider = model.split(":", 1)[0]
    else:
        get_ls_params = getattr(model, "_get_ls_params", None)
        params = get_ls_params() if callable(get_ls_params) else {}
        provider = params.get("ls_provider")
    if not isinstance(provider, str) or not provider:
        raise HarnessConfigurationError("harness_model_profile_unavailable")
    register_harness_profile(
        provider,
        HarnessProfile(
            general_purpose_subagent=GeneralPurposeSubagentProfile(
                enabled=False,
            ),
        ),
    )


def build_generic_harness(
    *,
    model: Any,
    skills_root: Path | None = None,
) -> DeepAgentsHarness:
    """Compile the generic coordinator from release-owned assets and policy."""
    root = (skills_root or _DEFAULT_SKILLS_ROOT).resolve()
    _read_required_skills(root)
    policy = profile_registry.policy_for("generic")
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/skills/": FilesystemBackend(
                root_dir=root,
                virtual_mode=True,
            ),
        },
    )
    permissions = tuple(build_filesystem_permissions())
    researchers = compile_generic_researchers(model=model)
    _register_generic_harness_profile(model)
    graph = create_deep_agent(
        model=model,
        tools=[],
        system_prompt=GENERIC_COORDINATOR_PROMPT,
        middleware=build_profile_middleware("generic", role="coordinator"),
        subagents=list(researchers.values()),
        skills=list(policy.skills),
        permissions=list(permissions),
        backend=backend,
        context_schema=ResearchRuntimeContext,
        name="generic-research-coordinator",
    )
    return DeepAgentsHarness(
        graph=graph,
        backend=backend,
        permissions=permissions,
        skills=policy.skills,
    )
