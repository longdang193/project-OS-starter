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
    current_manifest = (OVERLAY / "overlays/9router-security/ce4460ef/manifest.json").read_text(encoding="utf-8")
    assert "ce4460ef79382bfddb4aa5fc0ff9f3cb0d5f95a8" in current_manifest
    assert (OVERLAY / "overlays/9router-security/ce4460ef/9router-security.patch").is_file()


def test_9router_security_overlay_preserves_error_response_arguments() -> None:
    patch = (OVERLAY / "overlays/9router-security/ce4460ef/9router-security.patch").read_text(encoding="utf-8")

    assert "+export function errorResponse(statusCode, message, extraHeaders = null, diagnostics = {})" in patch
    assert "+export function createErrorResult(statusCode, message, resetsAtMs, extraHeaders = null, diagnostics = {})" in patch
    assert "+    return createErrorResult(statusCode, errMsg, resetsAtMs, upstreamResponseHeaders(providerResponse.headers), diagnostics);" in patch
    assert "+    response: errorResponse(statusCode, message, extraHeaders, diagnostics)" in patch
