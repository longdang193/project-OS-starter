from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "open-design-local-patch"


def test_open_design_overlay_uses_symbol_discovery_and_shared_markers() -> None:
    updater = (PATCH_ROOT / "Apply-OpenDesignPatch.ps1").read_text(encoding="utf-8")

    assert "server-*.mjs" in updater
    assert "function diffRunArtifacts" in updater
    assert "function validateRunDeliverable" in updater
    assert "mcp-bootstrap-*.mjs" in updater
    assert "function ensureMcpDaemonUrl" in updater
    assert "OD_MCP_BOOTSTRAP_IPC_PATH" in updater
    assert "OD_PACKAGED_RUNTIME_NAMESPACE" in updater
    assert "resolvePackagedHeadlessRuntimeNamespace" in updater
    assert "mcpBootstrapRuntimeNamespace" in updater
    assert "postSpawnIpcPath" in updater
    assert "-headless-daemon" in updater
    assert "const postSpawnIpcPath" in updater
    assert "bootstrap isolated post-spawn polling upgrade" in updater
    assert '$normalizedOld = $Old.Replace("`r`n", "`n").Replace("`r", "`n")' in updater
    assert "OpenDesign-patch-backups" in updater
    assert "function Get-Sha256" in updater
    assert "Get-FileHash" not in updater
    assert 'import { isAbsolute, join } from "node:path";`n' not in updater
    assert "'var DEFAULT_BOOTSTRAP_POLL_MS = 250;`n'" not in updater
    assert "VerifyOnly" in updater
    assert "already patched" in updater.lower()
    assert "fail" in updater.lower()
    assert "packaged-main.mjs" in updater
    assert "function createPackagedDesktopLogger" in updater
    assert "EPIPE" in updater
    assert 'let echo = process.env[DESKTOP_LOG_ECHO_ENV] !== "0";' in updater
    assert 'let echo = process.env[DESKTOP_LOG_ECHO_ENV] === "1" && process.stdout.isTTY === true;' in updater
    assert 'process.stdout.on("error", handleConsoleStreamError);' in updater
    assert 'process.stderr.on("error", handleConsoleStreamError);' in updater
    assert 'const handleConsoleStreamError' in updater
    assert 'const safeConsoleWrite' in updater
    assert 'safeConsoleWrite(originalConsole.error, args);' in updater
    assert "function hasActivePackagedRun" in updater
    assert "readdir" in updater
    assert "reason=active-run" in updater


def test_open_design_launcher_patches_before_starting_app() -> None:
    launcher = (PATCH_ROOT / "Start-OpenDesignPatched.ps1").read_text(encoding="utf-8")

    assert "Apply-OpenDesignPatch.ps1" in launcher
    assert "Start-Process" in launcher
    assert "OpenDesignArgs.Count -gt 0" in launcher
    assert "Open Design.exe" in launcher
    assert 'OD_DESKTOP_LOG_ECHO' in launcher
    assert '$env:OD_DESKTOP_LOG_ECHO = "0"' in launcher
    assert "Get-Process -Name 'Open Design'" not in launcher
    assert "Stop-Process -Force" not in launcher


def test_installed_packaged_logger_uses_safe_writes() -> None:
    bundle = Path.home() / "AppData/Local/Programs/Open Design/resources/app/prebundled/packaged-main.mjs"
    if not bundle.exists():
        return
    source = bundle.read_text(encoding="utf-8")
    assert "const safeConsoleWrite" in source
    assert "resolvePackagedHeadlessRuntimeNamespace" in source
    assert "OD_MCP_BOOTSTRAP_IPC_PATH" in source
    assert 'let echo = process.env[DESKTOP_LOG_ECHO_ENV] === "1" && process.stdout.isTTY === true;' in source
    assert "function hasActivePackagedRun" in source
    assert "reason=active-run" in source
    logger = source[source.index("function createPackagedDesktopLogger") : source.index("function attachPackagedDesktopProcessLogging")]
    assert "safeConsoleWrite(originalConsole.error, args);" in logger
