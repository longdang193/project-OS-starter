from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"
OVERLAY_ROOT = PATCH_ROOT / "overlays" / "9router-codex-relay" / "ce4460ef"


def test_9router_codex_relay_overlay_is_versioned_and_update_safe() -> None:
    script = (PATCH_ROOT / "Apply-9RouterCodexRelayOverlay.ps1").read_text(encoding="utf-8")
    manifest = (OVERLAY_ROOT / "manifest.json").read_text(encoding="utf-8")
    patch = (OVERLAY_ROOT / "9router-codex-relay.patch").read_text(encoding="utf-8")
    readme = (PATCH_ROOT / "README.md").read_text(encoding="utf-8")

    assert '"id": "9router-codex-opaque-relay"' in manifest
    assert '"version": "1.0.0"' in manifest
    assert '"baseCommit": "ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8"' in manifest
    assert '"patch": "9router-codex-relay.patch"' in manifest
    assert "src/app/api/v1/chatgpt-web/responses/route.js" in patch
    assert "tests/unit/chatgpt-web-responses-relay.test.js" in patch
    assert "MAX_RELAY_BODY_BYTES = 8 * 1024 * 1024" in patch
    assert 'import * as zlib from "node:zlib"' in patch
    assert 'content-encoding' in patch
    assert "zstdDecompressSync" in patch
    assert "zstdCompressSync" in patch
    assert "CODEX_RELAY_UPSTREAM_URL" in patch
    assert 'status: 426' in patch
    assert "x-codex-turn-metadata" in patch
    assert "redirect: \"manual\"" in patch
    assert "fetchMock" in patch
    assert "--3way" in script
    assert "--cached" in script
    assert "GIT_INDEX_FILE" in script
    assert "--reverse" in script
    assert "--ignore-whitespace" in script
    assert "VerifyOnly" in script
    assert "tracked changes" in script
    assert "Install-9RouterGlobal -TargetPath $targetPath" in script
    assert "AllowDowngrade" in script
    assert "Apply-9RouterCodexRelayOverlay.ps1" in readme
    assert "CODEX_RELAY_UPSTREAM_URL" in readme
    assert "/v1/chatgpt-web/responses" in readme
    assert "no model aliasing" in readme
    assert "no automatic replay" in readme
    assert "no relay `/v1/models` route" in readme


def test_9router_codex_relay_patch_contains_only_expected_files() -> None:
    patch = (OVERLAY_ROOT / "9router-codex-relay.patch").read_text(encoding="utf-8")
    paths = [
        line.removeprefix("+++ b/")
        for line in patch.splitlines()
        if line.startswith("+++ b/")
    ]
    assert paths == [
        "src/app/api/v1/chatgpt-web/responses/route.js",
        "tests/unit/chatgpt-web-responses-relay.test.js",
    ]
    assert "src/app/api/v1/responses/route.js" not in patch
    assert "dist/tokenpilot-codex-hook.cmd" not in patch
