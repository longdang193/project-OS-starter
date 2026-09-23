from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

import pytest


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
    assert "function Write-TextIfChanged" in text
    assert "Set-Content" not in text
    assert 'Installed managed dcode at $managedDcodePath' in text


def test_write_if_changed_preserves_unchanged_files() -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell is required for helper behavior validation")
    text = SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n")
    start = text.index("function Write-TextIfChanged {")
    end = text.index("\n}\n\n$configPath", start) + 2
    helper = text[start:end]
    command = f"""
{helper}
$path = Join-Path $env:TEMP 'project-os-write-if-changed.txt'
[IO.File]::WriteAllText($path, 'same', [Text.UTF8Encoding]::new($false))
$before = [Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
Write-TextIfChanged -Path $path -Content 'same' -Encoding ([Text.UTF8Encoding]::new($false))
$after = [Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
if ($before -cne $after) {{ exit 1 }}
Write-TextIfChanged -Path $path -Content 'changed' -Encoding ([Text.UTF8Encoding]::new($false))
if ([IO.File]::ReadAllText($path) -cne 'changed') {{ exit 2 }}
Remove-Item -LiteralPath $path -Force
"""
    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_setup_script_parses_with_windows_powershell() -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell is required for parser validation")
    command = (
        "$text = Get-Content -LiteralPath '"
        + str(SCRIPT).replace("'", "''")
        + "' -Raw; [scriptblock]::Create($text) | Out-Null"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
