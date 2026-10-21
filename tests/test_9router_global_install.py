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


def test_global_installer_bootstraps_build_dependencies_only_when_missing() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert 'node_modules\\next\\package.json' in script
    assert 'cli\\node_modules\\esbuild\\package.json' in script
    assert '"install", "--no-audit", "--no-fund", "--ignore-scripts"' in script
    assert "Ensure-NpmDependencies" in script
    assert script.index("Ensure-NpmDependencies -WorkingDirectory $TargetPath") < script.index('$cliPath = Join-Path $TargetPath "cli"')


def test_global_installer_writes_requested_receipt_atomically_after_verification() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "$InstallReceiptJson" in script
    assert "9router-cgw-overlay.json" in script
    assert "Move-Item -LiteralPath $receiptStage" in script
    assert "Restore-9RouterGlobal" in script


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


def test_combo_launcher_applies_the_manifest_selected_cgw_overlay_before_install() -> None:
    script = (ROOT / "tools" / "local-patch-hub" / "Start-9RouterCodexCombo.ps1").read_text(
        encoding="utf-8"
    )

    assert "Apply-9RouterCgwOverlay.ps1" in script
    assert "Refusing to start a stale 9router CGW runtime receipt" in script
    assert "targetPackage.version" not in script


def test_combo_launcher_applies_overlay_before_require_shim_entrypoint() -> None:
    script = (ROOT / "tools" / "local-patch-hub" / "Start-9RouterCodexCombo.ps1").read_text(
        encoding="utf-8"
    )

    assert script.index("if ($InstallGlobal)") < script.index("CGW Chat shim is missing")


def test_combo_launcher_requires_the_durable_cgw_install_receipt() -> None:
    script = (ROOT / "tools" / "local-patch-hub" / "Start-9RouterCodexCombo.ps1").read_text(
        encoding="utf-8"
    )

    assert "9router-cgw-overlay.json" in script
    assert "overlayId" in script
    assert "Test-InstalledCgwRuntime" not in script
    assert "PackageVersion" in script
    assert 'overlayVersion -eq "1.0.0"' not in script


def test_combo_launcher_can_repair_a_missing_global_command() -> None:
    script = (ROOT / "tools" / "local-patch-hub" / "Start-9RouterCodexCombo.ps1").read_text(
        encoding="utf-8"
    )

    assert script.index("if ($InstallGlobal)") < script.index("Global 9router command is missing")


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

def test_global_installer_short_circuits_an_exact_existing_receipt_before_stopping_processes() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "9router-cgw-overlay.json" in script
    assert "InstallReceiptJson" in script
    assert "already matches" in script
    assert script.index("already matches") < script.index("Get-9RouterProcesses")
