from pathlib import Path


def test_host_core_deploy_uses_locked_uv_runtime_and_proves_runtime() -> None:
    script = (Path(__file__).resolve().parent.parent / "scripts" / "deploy_harness_core_to_host.ps1").read_text(encoding="utf-8")

    assert "uv run --locked codex-harness-host" not in script
    assert "& harness-core-launcher upgrade --host-root $hostPath" in script
    assert "& harness-core-launcher doctor" in script
    assert "& harness-core-launcher preflight" in script
