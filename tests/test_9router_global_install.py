from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"
INSTALLER = PATCH_ROOT / "Install-9RouterGlobal.ps1"
LAUNCHER = PATCH_ROOT / "Start-9RouterCodexCombo.ps1"


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


def test_global_installer_writes_generic_verified_receipt_after_install() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "9router-install.json" in script
    assert "schemaVersion = 1" in script
    assert "packageVersion" in script
    assert "sourceCommit" in script
    assert "packageContentDigest" in script
    assert "Get-PackageContentDigest" in script
    assert "Move-Item -LiteralPath $receiptStage" in script
    assert "9router-cgw-overlay.json" not in script
    assert "InstallReceiptJson" not in script


def test_global_installer_preserves_downgrade_protection_and_exact_receipt_short_circuit() -> None:
    script = INSTALLER.read_text(encoding="utf-8")

    assert "Refusing to downgrade global 9router" in script
    assert "already matches version" in script
    assert script.index("already matches") < script.index("Get-9RouterProcesses")
    assert "ExpectedSourceCommit" in script


def test_combo_launcher_manages_only_the_native_9router_listener() -> None:
    script = LAUNCHER.read_text(encoding="utf-8")

    assert "Install-9RouterGlobal.ps1" in script
    assert "20128" in script
    assert "/api/health" in script
    assert "9router-install.json" in script
    assert "20129" not in script
    assert "cgw" not in script.lower()
    assert "chatgpt-web" not in script.lower()
    assert "InstallStartup" not in script


def test_combo_launcher_validates_source_commit_and_install_receipt() -> None:
    script = LAUNCHER.read_text(encoding="utf-8")

    assert "rev-parse HEAD" in script
    assert "schemaVersion" in script
    assert "packageVersion" in script
    assert "sourceCommit" in script
    assert "packageContentDigest" in script
    assert "stale or invalid 9router install receipt" in script


def test_cgw_owned_patch_hub_artifacts_are_removed() -> None:
    assert not (PATCH_ROOT / "Apply-9RouterCgwOverlay.ps1").exists()
    assert not (PATCH_ROOT / "Install-9RouterCodexComboStartup.ps1").exists()
    assert not (PATCH_ROOT / "overlays" / "9router-cgw").exists()
