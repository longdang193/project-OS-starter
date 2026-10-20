from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "tools" / "local-patch-hub" / "Install-9RouterGlobal.ps1"


def test_global_installer_stops_launcher_and_tray_processes_before_replacement() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "9router\\.cmd" in script
    assert "tray\\.ps1" in script
    assert "Get-9RouterProcesses" in script
    assert "remainingProcesses" in script


def test_global_installer_rolls_back_when_replacement_or_verification_fails() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "$rollbackRoot" in script
    assert "Move-Item -LiteralPath $packageRoot" in script
    assert "Restore-9RouterGlobal" in script
    assert "versionOutput" in script


def test_combo_launcher_accepts_existing_shim_with_windows_path_separators() -> None:
    script = (ROOT / "tools" / "local-patch-hub" / "Start-9RouterCodexCombo.ps1").read_text(
        encoding="utf-8"
    )

    assert "cgw-codex-shim[\\\\/]+run\\.js" in script
    assert 'Join-Path "tools" "cgw-codex-shim\\run.js"' in script


def test_combo_launcher_authenticates_existing_shim_with_target_env_key() -> None:
    script = (ROOT / "tools" / "local-patch-hub" / "Start-9RouterCodexCombo.ps1").read_text(
        encoding="utf-8"
    )

    assert "Get-DotEnvValue" in script
    assert "Authorization" in script
    assert "rejected the target .env" in script
    assert "StatusCode -in @(200, 401)" in script


def test_combo_readme_does_not_recommend_downgrading_the_global_router() -> None:
    readme = (ROOT / "tools" / "local-patch-hub" / "README.md").read_text(encoding="utf-8")

    assert "-InstallGlobal -AllowDowngrade" not in readme
    assert "0.5.104" in readme
    assert "Do not use `-AllowDowngrade`" in readme


def test_combo_startup_registration_is_available_without_secrets() -> None:
    startup = (ROOT / "tools" / "local-patch-hub" / "Install-9RouterCodexComboStartup.ps1").read_text(
        encoding="utf-8"
    )
    launcher = (ROOT / "tools" / "local-patch-hub" / "Start-9RouterCodexCombo.ps1").read_text(
        encoding="utf-8"
    )

    assert "Register-ScheduledTask" in startup
    assert "AtLogOn" in startup
    assert "-LogonType Interactive" in startup
    assert "AllowStartIfOnBatteries" in startup
    assert "DontStopIfGoingOnBatteries" in startup
    assert "CGW_SHIM_API_KEY" not in startup
    assert "InstallStartup" in launcher


def test_combo_readme_explains_one_time_startup_registration() -> None:
    readme = (ROOT / "tools" / "local-patch-hub" / "README.md").read_text(encoding="utf-8")

    assert "Install-9RouterCodexComboStartup.ps1" in readme
    assert "once" in readme.lower()
    assert "Windows logon" in readme
