from pathlib import Path


def test_host_core_deploy_uses_locked_uv_runtime_and_proves_runtime() -> None:
    script = (Path(__file__).resolve().parent.parent / "scripts" / "deploy_harness_core_to_host.ps1").read_text(encoding="utf-8")

    assert "uv pip install --python $hostPython --no-deps --editable $corePath" not in script
    assert '$uvRuntime = @("run", "--locked", "--project", $hostPath)' in script
    assert "& uv @uvRuntime python" in script
    assert "from harness_core.api import runtime_identity" in script
    assert "Host runtime did not load locked harness-core" in script
    assert "& uv @uvRuntime codex-harness-host capabilities" in script
    assert "& uv @uvRuntime codex-harness-host preflight" in script
