from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "setup_deepagents_runtime.ps1"


def test_setup_script_exposes_explicit_reinstall_and_migration_controls() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "[switch]$ForceReinstall" in text
    assert "[switch]$MigrateConfig" in text


def test_setup_script_uses_managed_runtime_without_path_fallback() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "$managedDcodePath" in text
    assert "Get-Command dcode" not in text
    assert "if (-not $SkipInstall -and $installRequired)" in text


def test_setup_script_parses_with_windows_powershell() -> None:
    command = (
        "$text = Get-Content -LiteralPath '"
        + str(SCRIPT).replace("'", "''")
        + "' -Raw; [scriptblock]::Create($text) | Out-Null"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
