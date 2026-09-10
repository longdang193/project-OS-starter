from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"
OVERLAY_ROOT = PATCH_ROOT / "overlays" / "9router-responses" / "e0be4111"
LATEST_OVERLAY_ROOT = PATCH_ROOT / "overlays" / "9router-responses" / "eb712ca8"


def test_9router_responses_overlay_is_versioned_and_update_safe() -> None:
    script = (PATCH_ROOT / "Apply-9RouterResponsesOverlay.ps1").read_text(encoding="utf-8")
    manifest = (OVERLAY_ROOT / "manifest.json").read_text(encoding="utf-8")
    patch = (OVERLAY_ROOT / "9router-responses-output.patch").read_text(encoding="utf-8")
    latest_manifest = (LATEST_OVERLAY_ROOT / "manifest.json").read_text(encoding="utf-8")
    latest_patch = (LATEST_OVERLAY_ROOT / "9router-responses-output.patch").read_text(encoding="utf-8")
    readme = (PATCH_ROOT / "README.md").read_text(encoding="utf-8")
    installer = (PATCH_ROOT / "Install-9RouterGlobal.ps1").read_text(encoding="utf-8")
    security_script = (PATCH_ROOT / "Apply-9RouterSecurityOverlay.ps1").read_text(encoding="utf-8")

    assert '"baseCommit": "e0be411184e67687171a1e13ae2e5686c14dd43a"' in manifest
    assert '"baseCommit": "eb712ca821f0ba6bc41043fbd14494c5af5daba5"' in latest_manifest
    assert "open-sse/transformer/responsesTransformer.js" in patch
    assert "tests/unit/responses-transformer-completed-output.test.js" in patch
    assert "responseOutput: []" in patch
    assert "output: state.responseOutput.filter(Boolean)" in patch
    assert "open-sse/transformer/responsesTransformer.js" in latest_patch
    assert "tests/unit/responses-transformer-completed-output.test.js" in latest_patch
    assert "open-sse/translator/index.js" in latest_patch
    assert "open-sse/translator/response/openai-responses.js" in latest_patch
    assert "open-sse/utils/stream.js" in latest_patch
    assert "tests/unit/openai-responses-completed-output.test.js" in latest_patch
    assert "tests/unit/openai-responses-completed-output-passthrough.test.js" in latest_patch
    assert "reconstructedOutput = state.responseOutput.filter(Boolean)" in latest_patch
    assert "translatorIndexPath" in script
    assert "streamPath" in script
    assert script.index("$nativeFix") < script.index("$records")
    assert "--3way" in script
    assert "--cached" in script
    assert "GIT_INDEX_FILE" in script
    assert "--reverse" in script
    assert "--ignore-whitespace" in script
    assert "VerifyOnly" in script
    assert "tracked changes" in script
    assert "Install-9RouterGlobal -TargetPath $targetPath" in script
    assert "Install-9RouterGlobal -TargetPath $targetPath" in security_script
    assert "AllowDowngrade" in script
    assert "AllowDowngrade" in security_script
    assert "Get-CimInstance Win32_Process" in installer
    assert "Push-Location" in installer
    assert "Refusing to downgrade" in installer
    assert "installedVersion" in installer
    assert "Stop-Process" in installer
    assert '"--force"' in installer
    assert "missing $entryPath" in installer
    assert "builtAppPath" in installer
    assert "installedAppPath" in installer
    assert "Get-9RouterProcesses" in installer
    assert "remainingProcesses" in installer
    assert "versionOutput" in installer
    assert "versionExitCode" in installer
    assert "9router.cmd" in installer
    assert "Apply-9RouterResponsesOverlay.ps1" in readme
