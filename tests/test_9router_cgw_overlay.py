from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"
OVERLAY_ROOT = PATCH_ROOT / "overlays" / "9router-cgw" / "87a74e1b"


def _assert_unified_patch_hunks_match_their_headers(patch: str) -> None:
    lines = patch.splitlines()
    for index, line in enumerate(lines):
        match = re.match(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",
            line,
        )
        if match is None:
            continue
        expected_old = int(match.group(2) or 1)
        expected_new = int(match.group(4) or 1)
        actual_old = 0
        actual_new = 0
        for hunk_line in lines[index + 1 :]:
            if hunk_line.startswith("@@ ") or hunk_line.startswith("diff --git "):
                break
            if hunk_line.startswith("+++") or hunk_line.startswith("---"):
                continue
            if hunk_line.startswith("+"):
                actual_new += 1
            elif hunk_line.startswith("-"):
                actual_old += 1
            elif hunk_line.startswith(" ") or hunk_line == "":
                actual_old += 1
                actual_new += 1
        assert (actual_old, actual_new) == (expected_old, expected_new), line


def test_9router_cgw_overlay_is_version_pinned_and_quota_safe() -> None:
    script = (PATCH_ROOT / "Apply-9RouterCgwOverlay.ps1").read_text(encoding="utf-8")
    manifest = (OVERLAY_ROOT / "manifest.json").read_text(encoding="utf-8")
    patch = (OVERLAY_ROOT / "9router-cgw.patch").read_text(encoding="utf-8")
    readme = (PATCH_ROOT / "README.md").read_text(encoding="utf-8")

    assert '"id": "9router-cgw-chat-runtime"' in manifest
    assert '"version": "1.1.2"' in manifest
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
    assert "CGW execution queue is full" in patch
    assert "DEFAULT_MAX_BODY_BYTES = 1024 * 1024" in patch
    assert "native-context-safe request body budget" in patch
    assert "accepts native sub-agent context above the legacy 64 KiB budget" in patch
    assert "open-sse/services/accountFallback.js" in patch
    assert "tests/unit/account-fallback-cgw-queue.test.js" in patch
    assert "x-9router-no-replay" in patch
    assert "stops combo fallback after CGW dispatch" in patch
    assert "failed after dispatch; replay disabled" in patch
    assert "--3way" in script
    assert "--cached" in script
    assert "GIT_INDEX_FILE" in script
    assert "VerifyOnly" in script
    assert "AllowDowngrade" in script
    assert "Install-9RouterGlobal -TargetPath $targetPath" in script
    assert "InstallReceiptJson" in script
    assert "Refusing to apply CGW overlay $($selected.Manifest.version) to 9router version" in script
    assert "Get-ChildItem" in script
    assert "Manifest.baseCommit" in script
    assert "if ($alreadyApplied.Count -eq 1)" in script
    assert "No 9router CGW overlay matches HEAD" in script
    assert 'overlays\\9router-cgw\\87a74e1b' not in script
    assert "Apply-9RouterCgwOverlay.ps1" in readme
    assert "CGW aliases must target `chatgpt-web/*`" in readme
    assert "optional `tools` and `tool_choice` metadata" in readme
    assert "/health` alone proves liveness" in readme
    assert "stops both account and combo fallback" in readme
    _assert_unified_patch_hunks_match_their_headers(patch)


def test_combo_launcher_rejects_stale_cgw_receipts() -> None:
    launcher = (PATCH_ROOT / "Start-9RouterCodexCombo.ps1").read_text(encoding="utf-8")

    assert "Get-ExpectedCgwOverlayVersion" in launcher
    assert "ExpectedOverlayVersion" in launcher
    assert "receipt.overlayVersion -eq $ExpectedOverlayVersion" in launcher
    assert "Refusing to start a stale 9router CGW runtime receipt" in launcher
