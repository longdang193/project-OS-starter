"""Canonical loader for repository agent profiles."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import json
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
ALLOWED_KEYS = REQUIRED_KEYS | {"rank", "herdr_only"}
_RETIREMENT_POLICY_PATHS = (
    Path(__file__).resolve().parents[1] / "repo_config" / "retired-model-policy.json",
    Path(__file__).resolve().with_name("retired-model-policy.json"),
)


def _load_retirement_policy() -> dict[str, object]:
    policy_path = next(
        (candidate for candidate in _RETIREMENT_POLICY_PATHS if candidate.is_file()),
        _RETIREMENT_POLICY_PATHS[0],
    )
    try:
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read retirement policy {policy_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Retirement policy {policy_path} must be a JSON object.")
    for key in ("retiredModelNames", "retiredModelPrefixes", "retiredProviderIds"):
        values = payload.get(key)
        if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
            raise RuntimeError(f"Retirement policy {policy_path} `{key}` must be a non-empty string list.")
    aliases = payload.get("providerAliases")
    if not isinstance(aliases, dict) or not aliases or not all(
        isinstance(alias, str)
        and alias
        and isinstance(provider, str)
        and provider
        for alias, provider in aliases.items()
    ):
        raise RuntimeError(
            f"Retirement policy {policy_path} `providerAliases` must be a non-empty string mapping."
        )
    return payload


_RETIREMENT_POLICY: dict[str, object] | None = None


def _retirement_policy() -> dict[str, object]:
    global _RETIREMENT_POLICY
    if _RETIREMENT_POLICY is None:
        _RETIREMENT_POLICY = _load_retirement_policy()
    return _RETIREMENT_POLICY


@dataclass(frozen=True)
class AgentProfile:
    source: Path
    name: str
    model_provider: str
    model: str
    rank: int | None
    description: str
    developer_instructions: str
    herdr_only: bool = False


def _required_string(payload: dict[str, object], key: str, source: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Agent profile {source} `{key}` must be a non-empty string.")
    return value.strip()


def validate_model_reference(
    model: str,
    source: Path | str,
    provider: str | None = None,
) -> None:
    policy = _retirement_policy()
    retired_names = frozenset(policy["retiredModelNames"])
    retired_prefixes = tuple(policy["retiredModelPrefixes"])
    retired_providers = frozenset(policy["retiredProviderIds"])
    provider_aliases = policy["providerAliases"]
    normalized_provider = provider_aliases.get(provider, provider) if isinstance(provider, str) else None
    if normalized_provider in retired_providers:
        raise ValueError(
            f"Agent profile {source} uses retired provider `{provider}`; "
            f"normalized provider `{normalized_provider}` is unsupported."
        )
    if model in retired_names or model.startswith(retired_prefixes):
        raise ValueError(
            f"Agent profile {source} uses retired model `{model}`; "
            "retired CGW/web-combo aliases are unsupported."
        )


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
        herdr_only = payload.get("herdr_only", False)
        if not isinstance(herdr_only, bool):
            raise ValueError(f"Agent profile `{source}` `herdr_only` must be a boolean.")
        if name in profiles:
            raise ValueError(f"Duplicate agent profile: {name}")
        model = _required_string(payload, "model", source)
        validate_model_reference(model, source, model_provider)
        profiles[name] = AgentProfile(
            source=source,
            name=name,
            model_provider=model_provider,
            model=model,
            rank=rank,
            description=_required_string(payload, "description", source),
            developer_instructions=_required_string(payload, "developer_instructions", source),
            herdr_only=herdr_only,
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
