from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"
OVERLAY_ROOT = PATCH_ROOT / "overlays" / "lightrsi-codex-hook-portable" / "c0d86ae"
COMPACTION_OVERLAY_ROOT = PATCH_ROOT / "overlays" / "lightrsi-codex-hook-portable" / "c05cafe5"


def test_lightmem2_overlay_is_centralized_and_exact_base_bound() -> None:
    manifest = (OVERLAY_ROOT / "manifest.json").read_text(encoding="utf-8")
    patch = (OVERLAY_ROOT / "lightrsi-codex-hook-portable.patch").read_text(encoding="utf-8")
    reconciler = (PATCH_ROOT / "Apply-LightMem2CodexOverlay.ps1").read_text(encoding="utf-8")

    assert '"baseCommit": "c0d86ae519d0eb4f1c3e3fefdd22b696a9e70c33"' in manifest
    assert "components/adapters/codex/src/install.ts" in patch
    assert "components/adapters/codex/tests/install.test.ts" in patch
    assert "rev-parse HEAD" in reconciler
    assert "appliedRecords" in reconciler
    assert "--reverse" in reconciler
    assert "SkipInstall" in reconciler
    assert "No LightMem2 Codex overlay matches target HEAD" in reconciler
    assert "ProjectOS-LightMem2-Codex-Overlay.cmd" in reconciler


def test_lightrsi_compaction_overlay_is_exact_base_bound() -> None:
    manifest = (COMPACTION_OVERLAY_ROOT / "manifest.json").read_text(encoding="utf-8")
    patch = (COMPACTION_OVERLAY_ROOT / "lightrsi-codex-compaction-compatibility.patch").read_text(encoding="utf-8")
    readme = (PATCH_ROOT / "README.md").read_text(encoding="utf-8")

    assert '"id": "lightrsi-codex-compaction-compatibility"' in manifest
    assert '"version": "1.2.0"' in manifest
    assert '"baseCommit": "c05cafe502fb474ab28e29e9e184adba8446a6a1"' in manifest
    assert "components/adapters/codex/src/proxy-runtime.ts" in patch
    assert "components/adapters/codex/src/upstream.ts" in patch
    assert "components/packages/foundation/host-adapter/src/gateway/runtime-server.ts" in patch
    assert "components/adapters/codex/tests/compaction-route.test.ts" in patch
    assert 'pathname === "/v1/responses/compact"' in patch
    assert "stripHistoricalWebSearchCalls" in patch
    assert "projectUpstreamPayload" in patch
    assert 'endpointPath: compactRequest ? "/responses/compact" : undefined' in patch
    assert "falls back to `/responses` on upstream `404`" in readme
    assert "-SkipInstall" in readme
