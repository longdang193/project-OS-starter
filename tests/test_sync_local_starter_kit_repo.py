from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "sync_local_starter_kit_repo.ps1"


def test_local_sync_rebuilds_and_validates_before_replacing_target() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    build = script.index("scripts/build_starter_kit.py")
    validate_source = script.index("--kit-root $sourcePath")
    validate_staging = script.index("--kit-root $sourceFullPath --compare-kit-root $stagingPath")
    replace_target = script.index("Remove-Item -Recurse -Force")

    assert build < validate_source < validate_staging < replace_target
    assert "--kit-root $sourceFullPath --compare-kit-root $targetFullPath" in script
