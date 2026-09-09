from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_ROOT = ROOT / "tools" / "local-patch-hub"


def test_open_design_overlay_uses_symbol_discovery_and_shared_markers() -> None:
    updater = (PATCH_ROOT / "Apply-OpenDesignPatch.ps1").read_text(encoding="utf-8")

    assert "server-*.mjs" in updater
    assert "function diffRunArtifacts" in updater
    assert "function validateRunDeliverable" in updater
    assert "mcp-bootstrap-*.mjs" in updater
    assert "function ensureMcpDaemonUrl" in updater
    assert "OD_MCP_BOOTSTRAP_IPC_PATH" in updater
    assert "package.json" in updater
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
    assert "function runPackagedHeadless(config, request" in updater
    assert "headless runtime namespace resolver (0.22.0)" in updater
    assert "headless runtime namespace fallback" in updater
    assert "function resolvePackagedSidecarIpcPath" in updater
    assert 'type: "sidecar:status"' in updater
    assert 'type: "sidecar:stop"' in updater
    assert 'type: "sidecar:invoke"' in updater
    assert "channel: activeConfig.channel" in updater
    assert "channel: options.channel" in updater
    assert "app: stamp.app" in updater
    assert "APP_KEYS,\n  SIDECAR_ENV\n} from \"./chunk-UZPD62PF.mjs\";" in updater
    assert 'if (-not $text.Contains("function resolvePackagedHeadlessRuntimeNamespace"))' in updater


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


def test_open_design_mcp_launcher_discovers_current_sidecar() -> None:
    launcher = (PATCH_ROOT / "Start-OpenDesignMcp.ps1").read_text(encoding="utf-8")

    assert "NamedPipeClientStream" in launcher
    assert '"sidecar:describe"' in launcher
    assert "ReadLineAsync" in launcher
    assert "ReadTimeout" not in launcher
    assert "result.stamp.app -eq \"daemon\"" in launcher
    assert "OD_SIDECAR_CLIENT_ENDPOINT = $runtime.Endpoint" in launcher
    assert "OD_DATA_DIR = $runtime.DataDir" in launcher
    assert "Start-Process -FilePath $exe -ArgumentList \"--headless\"" in launcher
    assert "open-design-sidecar-5329972e5f38dbd97ec28d825bccc6b9" not in launcher
    assert 'Name -like "open-design-*"' in launcher
    assert "System.Threading.Mutex" in launcher
    assert "OpenDesignMcpBootstrap" in launcher
    assert "WaitOne" in launcher
    assert "ReleaseMutex" in launcher
    assert "startupBudgetSeconds" in launcher
    assert "readinessBudgetSeconds" in launcher
    assert "Find-OpenDesignDaemon" in launcher


def test_installed_packaged_logger_uses_safe_writes() -> None:
    bundle = Path.home() / "AppData/Local/Programs/Open Design/resources/app/prebundled/packaged-main.mjs"
    if not bundle.exists():
        return
    source = bundle.read_text(encoding="utf-8")
    assert "const safeConsoleWrite" in source
    assert "resolvePackagedHeadlessRuntimeNamespace" in source
    assert 'let echo = process.env[DESKTOP_LOG_ECHO_ENV] === "1" && process.stdout.isTTY === true;' in source
    assert "function hasActivePackagedRun" in source
    assert "reason=active-run" in source
    assert "OD_SIDECAR_SUPERVISED_CONTEXT" in source
    assert "resolvePackagedSidecarIpcPath" in source
    assert 'type: "sidecar:status"' in source
    assert 'type: "sidecar:stop"' in source
    assert 'type: "sidecar:invoke"' in source
    assert "channel: options.channel" in source
    bootstrap = next(bundle.parent.joinpath("daemon", "chunks").glob("mcp-bootstrap-*.mjs"), None)
    assert bootstrap is not None
    bootstrap_source = bootstrap.read_text(encoding="utf-8")
    assert "APP_KEYS,\n  SIDECAR_ENV\n} from \"./chunk-UZPD62PF.mjs\";" in bootstrap_source
    context_start = source.index("const supervisedContext = JSON.stringify({")
    context_end = source.index("childEnv.OD_SIDECAR_SUPERVISED_CONTEXT", context_start)
    context = source[context_start:context_end]
    assert "stamp" in context
    assert "ipc" not in context
    assert "app: stamp.app" in context
    assert "source: stamp.source" in context
    logger = source[source.index("function createPackagedDesktopLogger") : source.index("function attachPackagedDesktopProcessLogging")]
    assert "safeConsoleWrite(originalConsole.error, args);" in logger
    server = next(bundle.parent.joinpath("daemon", "chunks").glob("server-*.mjs"), None)
    assert server is not None
    server_source = server.read_text(encoding="utf-8")
    assert "OD_MCP_BOOTSTRAP_IPC_PATH" in server_source
