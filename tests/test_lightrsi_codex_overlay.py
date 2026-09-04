from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "open-design-local-patch"
OVERLAY_ROOT = PATCH_ROOT / "overlays" / "lightrsi-codex-hook-portable" / "c0d86ae"


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
    assert "No LightMem2 Codex overlay matches target HEAD" in reconciler
    assert "ProjectOS-LightMem2-Codex-Overlay.cmd" in reconciler
