"""Canonical loader for repository agent profiles."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import random
import tomllib


FORBIDDEN_KEYS = {
    "model_reasoning_effort",
    "base_url",
    "api_key",
    "model_providers",
}
REQUIRED_KEYS = {
    "name",
    "model_provider",
    "model",
    "description",
    "developer_instructions",
}
ALLOWED_KEYS = REQUIRED_KEYS | {"rank"}


@dataclass(frozen=True)
class AgentProfile:
    source: Path
    name: str
    model_provider: str
    model: str
    rank: int | None
    description: str
    developer_instructions: str


def _required_string(payload: dict[str, object], key: str, source: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Agent profile {source} `{key}` must be a non-empty string.")
    return value.strip()


def load_agent_profiles(
    agents_root: Path,
    runtime_provider: str | None = None,
    pattern: str = "*.toml",
) -> dict[str, AgentProfile]:
    profiles: dict[str, AgentProfile] = {}
    ranks: set[int] = set()
    for source in sorted(agents_root.glob(pattern)):
        try:
            payload = tomllib.loads(source.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(f"Cannot read agent profile {source}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid agent profile {source}: TOML root must be a table.")
        forbidden = sorted(FORBIDDEN_KEYS & payload.keys())
        if forbidden:
            raise ValueError(
                f"Invalid agent profile {source}: runtime-owned keys: {', '.join(forbidden)}"
            )
        unexpected = sorted(set(payload) - ALLOWED_KEYS)
        if unexpected:
            raise ValueError(
                f"Invalid agent profile {source}: unsupported keys: {', '.join(unexpected)}"
            )

        name = _required_string(payload, "name", source)
        if source.stem != name:
            raise ValueError(f"Agent profile filename must match name: {source}")
        model_provider = _required_string(payload, "model_provider", source)
        if runtime_provider is not None and model_provider != runtime_provider:
            raise ValueError(
                f"Agent profile provider `{model_provider}` does not match runtime provider "
                f"`{runtime_provider}`: {source}"
            )
        rank = payload.get("rank")
        if rank is not None and (isinstance(rank, bool) or not isinstance(rank, int) or rank <= 0):
            raise ValueError(f"Agent profile `{source}` `rank` must be a positive integer.")
        if rank is not None and rank in ranks:
            raise ValueError(f"Agent profile ranks must be unique: {source}")
        if rank is not None:
            ranks.add(rank)
        if name in profiles:
            raise ValueError(f"Duplicate agent profile: {name}")
        profiles[name] = AgentProfile(
            source=source,
            name=name,
            model_provider=model_provider,
            model=_required_string(payload, "model", source),
            rank=rank,
            description=_required_string(payload, "description", source),
            developer_instructions=_required_string(payload, "developer_instructions", source),
        )
    if not profiles:
        raise ValueError(f"No agent profiles found under: {agents_root}")
    return profiles


def select_review_profiles(
    profiles: Mapping[str, AgentProfile],
    count: int = 1,
    *,
    sample: Callable[[Sequence[str], int], Sequence[str]] | None = None,
) -> tuple[str, ...]:
    if count not in {1, 2}:
        raise ValueError("review count must be 1 or 2")
    candidates = tuple(
        sorted(
            name
            for name, profile in profiles.items()
            if name.startswith("review-") and profile.rank is None
        )
    )
    if len(candidates) < count:
        raise ValueError(f"at least {count} unranked review profiles are required")
    selected = tuple((sample or random.SystemRandom().sample)(candidates, count))
    if len(selected) != count or len(set(selected)) != count or not set(selected) <= set(candidates):
        raise ValueError("review selector returned invalid profiles")
    return selected
