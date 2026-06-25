"""Immutable framework runtime context derived from server-owned policy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ResearchRuntimeContext:
    thread_id: str
    run_id: str
    segment_id: str
    profile_id: str
    allowed_source_domains: tuple[str, ...] | Iterable[str] = ()
    allowed_source_types: tuple[str, ...] | Iterable[str] = ()
    allowed_aggregate_ids: tuple[str, ...] | Iterable[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "allowed_source_domains",
            tuple(self.allowed_source_domains),
        )
        object.__setattr__(
            self,
            "allowed_source_types",
            tuple(self.allowed_source_types),
        )
        object.__setattr__(
            self,
            "allowed_aggregate_ids",
            tuple(self.allowed_aggregate_ids),
        )
