from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "manage_switchyard_runtime.py"
SPEC = importlib.util.spec_from_file_location("manage_switchyard_runtime", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MANAGER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MANAGER
SPEC.loader.exec_module(MANAGER)


def write_role(
    root: Path,
    name: str,
    model: str,
    provider: str = "9router",
    rank: int | None = None,
) -> None:
    if rank is None:
        rank = {"low": 10, "normal": 20, "high": 30, "xhigh": 40}.get(name, 20)
    agents = root / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    (agents / f"{name}.toml").write_text(
        f'name = "{name}"\n'
        f'model_provider = "{provider}"\n'
        f'model = "{model}"\n'
        f"rank = {rank}\n"
        'description = "role"\n'
        'developer_instructions = "instructions"\n',
        encoding="utf-8",
    )


def write_manifest(
    root: Path,
    *,
    efficient: str = "normal",
    capable: str = "high",
    route_id: str = "auto",
) -> Path:
    path = root / "repo_config" / "switchyard-routing.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "policy_version = 1\n"
        f'efficient_profile = "{efficient}"\n'
        f'capable_profile = "{capable}"\n'
        f'route_id = "{route_id}"\n'
        'high_control_route_id = "switchyard/high-control"\n'
        'picker = "capable_first"\n'
        "confidence_threshold = 0.5\n"
        "recent_turn_window = 3\n",
        encoding="utf-8",
    )
    return path


def codex_config(provider: str = "9router", base_url: str = "http://127.0.0.1:17667/v1") -> dict:
    return {
        "model_provider": provider,
        "model": "combo-high",
        "model_providers": {
            provider: {"name": "provider", "base_url": base_url, "wire_api": "responses"}
        },
    }


def contract(tmp_path: Path):
    write_role(tmp_path, "normal", "combo-normal", rank=20)
    write_role(tmp_path, "high", "combo-high", rank=30)
    write_role(tmp_path, "low", "combo-low")
    policy = MANAGER.load_routing_policy(write_manifest(tmp_path))
    profiles = MANAGER.load_agent_profiles(tmp_path / "agents")
    return MANAGER.resolve_routing_contract(policy, profiles, codex_config())


def test_resolves_normal_high_and_excludes_low(tmp_path: Path) -> None:
    resolved = contract(tmp_path)

    assert resolved.efficient.model == "combo-normal"
    assert resolved.capable.model == "combo-high"
    assert resolved.efficient.name != "low"
    assert resolved.upstream_base_url == "http://127.0.0.1:17667/v1"


def test_rejects_low_as_automatic_endpoint(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", "combo-normal")
    write_role(tmp_path, "high", "combo-high")
    write_role(tmp_path, "low", "combo-low")
    with pytest.raises(ValueError, match="low"):
        MANAGER.load_routing_policy(write_manifest(tmp_path, efficient="low"))


def test_rejects_non_v1_automatic_band(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", "combo-normal")
    write_role(tmp_path, "high", "combo-high")
    write_role(tmp_path, "xhigh", "combo-xhigh")

    with pytest.raises(ValueError, match="normal.*high"):
        MANAGER.load_routing_policy(write_manifest(tmp_path, capable="xhigh"))


def test_rejects_non_auto_route_id(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", "combo-normal")
    write_role(tmp_path, "high", "combo-high")

    with pytest.raises(ValueError, match="auto"):
        MANAGER.load_routing_policy(write_manifest(tmp_path, route_id="manual"))


def test_rejects_inverted_rank_order(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", "combo-normal", rank=30)
    write_role(tmp_path, "high", "combo-high", rank=20)
    policy = MANAGER.load_routing_policy(write_manifest(tmp_path))
    profiles = MANAGER.load_agent_profiles(tmp_path / "agents")

    with pytest.raises(ValueError, match="rank"):
        MANAGER.validate_static_contract(policy, profiles)


def test_static_validation_does_not_require_user_local_codex_config(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", "combo-normal")
    write_role(tmp_path, "high", "combo-high")
    write_role(tmp_path, "low", "combo-low")
    manifest = write_manifest(tmp_path)

    assert MANAGER.main(["validate", "--manifest", str(manifest)]) == 0


def test_static_validation_rejects_profile_provider_mismatch(tmp_path: Path) -> None:
    write_role(tmp_path, "normal", "combo-normal")
    write_role(tmp_path, "high", "combo-high", provider="other")
    write_role(tmp_path, "low", "combo-low")
    policy = MANAGER.load_routing_policy(write_manifest(tmp_path))
    profiles = MANAGER.load_agent_profiles(tmp_path / "agents")

    with pytest.raises(ValueError, match="same model provider"):
        MANAGER.validate_static_contract(policy, profiles)


def test_render_is_deterministic_and_contains_no_secret(tmp_path: Path) -> None:
    resolved = contract(tmp_path)

    first = MANAGER.render_switchyard_routes(resolved)
    second = MANAGER.render_switchyard_routes(resolved)
    assert first == second
    assert "combo-normal" in first
    assert "combo-high" in first
    assert 'env_key = "SWITCHYARD_API_KEY"' in MANAGER.render_codex_auto()
    assert 'api_key_env = "SWITCHYARD_API_KEY"' in first
    assert "api_key = " not in first.lower()
    assert "secret" not in first.lower()
    assert "http://127.0.0.1:17667/v1" in first


def test_deploy_refuses_drift_then_allows_explicit_replacement(tmp_path: Path) -> None:
    resolved = contract(tmp_path)
    codex_home = tmp_path / "codex"
    switchyard_home = tmp_path / "switchyard"
    outputs = MANAGER._outputs(resolved, codex_home, switchyard_home)
    MANAGER.deploy_outputs(outputs)
    original = (codex_home / "auto.config.toml").read_text(encoding="utf-8")
    (codex_home / "auto.config.toml").write_text(
        original.replace('model = "auto"', 'model = "old"'),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Refusing"):
        MANAGER.deploy_outputs(outputs)
    MANAGER.deploy_outputs(outputs, replace_existing=True)
    assert (codex_home / "auto.config.toml").read_text(encoding="utf-8") == original


def test_check_reports_drift_and_preserves_unrelated_file(tmp_path: Path) -> None:
    resolved = contract(tmp_path)
    codex_home = tmp_path / "codex"
    switchyard_home = tmp_path / "switchyard"
    unrelated = switchyard_home / "notes.txt"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("keep", encoding="utf-8")
    outputs = MANAGER._outputs(resolved, codex_home, switchyard_home)

    assert MANAGER.check_outputs(outputs)
    MANAGER.deploy_outputs(outputs)
    assert MANAGER.check_outputs(outputs) == []
    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_read_and_validate_switchyard_row(tmp_path: Path) -> None:
    path = tmp_path / "routing.jsonl"
    path.write_text(
        '{"route":"auto","decision_source":"dimensions","decision_score":0.7,'
        '"decision_threshold":0.5,"model":"combo-high","tier":"strong",'
        '"prompt_tokens":10,"completion_tokens":2,"total_tokens":12}\n',
        encoding="utf-8",
    )
    row = MANAGER.read_switchyard_row(path, 0, timeout_seconds=0.1)
    MANAGER.validate_smoke_row(row)
    assert row["model"] == "combo-high"


def test_validate_smoke_row_rejects_missing_decision_evidence() -> None:
    row = {
        "route": "auto",
        "model": "combo-normal",
        "tier": "",
        "prompt_tokens": 1,
        "completion_tokens": 1,
        "total_tokens": 2,
    }
    with pytest.raises(ValueError, match="decision_source"):
        MANAGER.validate_smoke_row(row)


def test_read_switchyard_row_times_out_without_new_row(tmp_path: Path) -> None:
    path = tmp_path / "routing.jsonl"
    path.write_text("{\"old\":true}\n", encoding="utf-8")
    with pytest.raises(TimeoutError, match="No complete"):
        MANAGER.read_switchyard_row(path, path.stat().st_size, timeout_seconds=0.01)
