from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "tools" / "local-patch-hub"


def test_9router_overlay_is_versioned_and_rebases() -> None:
    script = (OVERLAY / "Apply-9RouterSecurityOverlay.ps1").read_text(encoding="utf-8")
    manifest = (OVERLAY / "overlays/9router-security/eb712ca8/manifest.json").read_text(encoding="utf-8")

    assert "--3way" in script
    assert "--reverse" in script
    assert "VerifyOnly" in script
    assert "eb712ca821f0ba6bc41043fbd14494c5af5daba5" in manifest
    assert (OVERLAY / "overlays/9router-security/eb712ca8/9router-security.patch").is_file()
