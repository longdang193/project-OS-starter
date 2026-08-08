from pathlib import Path


def test_host_core_deploy_uses_editable_source_and_proves_runtime() -> None:
    script = (Path(__file__).resolve().parent.parent / "scripts" / "deploy_harness_core_to_host.ps1").read_text(encoding="utf-8")

    assert "uv pip install --python $hostPython --no-deps --editable $corePath" in script
    assert "from harness_core.api import runtime_identity" in script
    assert "Host did not import editable harness-core source" in script
    assert "& $hostCommand capabilities" in script
    assert "& $hostCommand preflight" in script
