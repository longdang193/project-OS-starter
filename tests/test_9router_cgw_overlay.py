from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"
OVERLAY_ROOT = PATCH_ROOT / "overlays" / "9router-cgw" / "87a74e1b"


def test_9router_cgw_overlay_is_version_pinned_and_quota_safe() -> None:
    script = (PATCH_ROOT / "Apply-9RouterCgwOverlay.ps1").read_text(encoding="utf-8")
    manifest = (OVERLAY_ROOT / "manifest.json").read_text(encoding="utf-8")
    patch = (OVERLAY_ROOT / "9router-cgw.patch").read_text(encoding="utf-8")
    readme = (PATCH_ROOT / "README.md").read_text(encoding="utf-8")

    assert '"id": "9router-cgw-chat-runtime"' in manifest
    assert '"version": "1.0.0"' in manifest
    assert '"baseCommit": "87a74e1bda3677193c6f71a7e2100c90311f0689"' in manifest
    assert '"targetVersion": "0.5.104"' in manifest
    assert "src/app/api/models/test/ping.js" in patch
    assert "src/sse/services/model.js" in patch
    assert "tools/cgw-codex-shim/cgwResponses.js" in patch
    assert "chatgpt-web/" in patch
    assert "reasoning_effort" in patch
    assert "isExpectedCgwModel" in patch
    assert "CGW response body too large" in patch
    assert "CGW model mismatch" in patch
    assert "--3way" in script
    assert "--cached" in script
    assert "GIT_INDEX_FILE" in script
    assert "VerifyOnly" in script
    assert "AllowDowngrade" in script
    assert "Install-9RouterGlobal -TargetPath $targetPath" in script
    assert "InstallReceiptJson" in script
    assert "Refusing to apply CGW overlay to 9router version" in script
    assert "Apply-9RouterCgwOverlay.ps1" in readme
    assert "CGW aliases must target `chatgpt-web/*`" in readme
