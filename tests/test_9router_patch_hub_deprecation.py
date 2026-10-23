import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"

PRESERVED_FILES = {
    "Apply-LightMem2CodexOverlay.ps1": "794bd8278e59fcdc04eea3906a00064f2a22f380ba208c88be4ef7c5eb7e47bc",
    "Apply-OpenDesignPatch.ps1": "8e731ad98cc0e153b81a810edf8363038bcfcc0684b30bf5b6c0c15f5385b453",
    "Start-OpenDesignMcp.ps1": "495088e13b6d2e2f6374b143805b6f1102d401c35e0a9ec004e604f04fe1f097",
    "Start-OpenDesignPatched.cmd": "b30ef013a8fb6f017b2a3c30d29b60ad110211706a80b3069d7e9f57c8d35c32",
    "Start-OpenDesignPatched.ps1": "4beaac4ba1be7c39944faa32f96459bbdccbe73d7ce3b4e240e087c3b3e7cb01",
    "overlays/lightrsi-codex-hook-portable/c05cafe5/lightrsi-codex-compaction-compatibility.patch": "fc3ea525c0b3eaef00fe10e8e0ad50336d3f69c6aaee5295ae953976aaea391b",
    "overlays/lightrsi-codex-hook-portable/c05cafe5/manifest.json": "7cdac31e146e5ab6a8e8b9231e2dba4d85c7b978f534fe6b602595d95064df7a",
    "overlays/lightrsi-codex-hook-portable/c0d86ae/lightrsi-codex-hook-portable.patch": "94a618676eb096b3e907d8f0c944c8ae1bf0e1302f96002aecd5718f30300940",
    "overlays/lightrsi-codex-hook-portable/c0d86ae/manifest.json": "1390b737d87ac9f762ae5188e0d75c542740fe2a890d995c8bb7a6d4ed756320",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_9router_patch_hub_surfaces_are_removed() -> None:
    removed_names = {
        "Apply-9RouterAttributionOverlay.ps1",
        "Apply-9RouterCodexRelayOverlay.ps1",
        "Apply-9RouterResponsesOverlay.ps1",
        "Apply-9RouterSecurityOverlay.ps1",
        "Install-9RouterGlobal.ps1",
        "Start-9RouterCodexCombo.ps1",
    }
    assert not any((PATCH_ROOT / name).exists() for name in removed_names)
    for directory in (
        "9router-attribution",
        "9router-codex-relay",
        "9router-responses",
        "9router-security",
    ):
        assert not (PATCH_ROOT / "overlays" / directory).exists()


def test_direct_fork_procedure_is_the_only_9router_guidance() -> None:
    readme = (PATCH_ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/longdang193/9router" in readme
    assert "docs/UPSTREAM-SYNC.md" in readme
    assert "Apply-9Router" not in readme
    assert "Start-9Router" not in readme
    assert "overlays/9router-" not in readme


def test_opendesign_and_lightmem2_surfaces_are_byte_for_byte_preserved() -> None:
    for relative_path, expected_hash in PRESERVED_FILES.items():
        path = PATCH_ROOT / relative_path
        assert path.exists(), relative_path
        assert sha256(path) == expected_hash, relative_path
