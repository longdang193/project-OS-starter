"""Regression guard for the installed Open Design artifact tracker hotfix."""

from pathlib import Path

import pytest


def test_manifest_backed_markdown_is_tracked_by_run_diff() -> None:
    bundle_dir = Path.home() / "AppData/Local/Programs/Open Design/resources/app/prebundled/daemon/chunks"
    bundles = [
        path
        for path in bundle_dir.glob("server-*.mjs")
        if "function diffRunArtifacts" in path.read_text(encoding="utf-8")
    ]
    if not bundles:
        pytest.skip("Open Design packaged daemon is not installed")
    source = max(bundles, key=lambda path: path.stat().st_mtime_ns).read_text(encoding="utf-8")

    assert "function isManifestBackedMarkdownPath" in source
    assert '`${filePath2}.artifact.json`' in source
    assert "isManifestBackedMarkdownPath(classifyPath)" in source


@pytest.mark.skipif(
    not (Path.home() / "AppData/Local/Programs/Open Design/resources/app/prebundled/daemon/chunks").exists(),
    reason="Open Design packaged daemon is not installed",
)
def test_external_export_can_select_touched_manifest_entry() -> None:
    bundle_dir = Path.home() / "AppData/Local/Programs/Open Design/resources/app/prebundled/daemon/chunks"
    bundle = max(
        (path for path in bundle_dir.glob("server-*.mjs") if "function validateRunDeliverable" in path.read_text(encoding="utf-8")),
        key=lambda path: path.stat().st_mtime_ns,
    )
    source = bundle.read_text(encoding="utf-8")

    assert "allowManifestEntryOverride" in source
    assert "artifactManifest" in source[source.index("function validateRunDeliverable") : source.index("// ../daemon/dist/run-retry-policy.js")]
    assert "selected.artifactManifest" in source
