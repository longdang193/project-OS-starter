[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA "Programs\Open Design"),
    [string]$BackupRoot = (Join-Path $env:LOCALAPPDATA "OpenDesign-patch-backups"),
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
$PatchVersion = "2026-09-04.5"

function Read-Utf8([string]$Path) {
    return [IO.File]::ReadAllText($Path, [Text.UTF8Encoding]::new($false))
}

function Write-Utf8([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Replace-Once([string]$Text, [string]$Name, [string]$Old, [string]$New, [string]$Marker) {
    if ($Text.Contains($Marker)) {
        Write-Verbose "$Name already patched"
        return $Text
    }
    $count = ([regex]::Matches($Text, [regex]::Escape($Old))).Count
    if ($count -ne 1) {
        throw "$Name anchor mismatch: expected 1 match, got $count"
    }
    return $Text.Replace($Old, $New)
}

function Find-Bundle([string]$Directory, [string]$Pattern, [string[]]$Anchors) {
    $matches = @(
        Get-ChildItem -LiteralPath $Directory -Filter $Pattern -File |
            Where-Object {
                $text = Read-Utf8 $_.FullName
                ($Anchors | ForEach-Object { $text.Contains($_) }) -notcontains $false
            }
    )
    if ($matches.Count -ne 1) {
        throw "Expected one $Pattern bundle with required anchors; found $($matches.Count)"
    }
    return $matches[0]
}

function Backup-Once([string]$Path, [string]$Directory) {
    New-Item -ItemType Directory -Force -Path $Directory | Out-Null
    $backup = Join-Path $Directory ([IO.Path]::GetFileName($Path) + ".original")
    if (-not (Test-Path -LiteralPath $backup -PathType Leaf)) {
        Copy-Item -LiteralPath $Path -Destination $backup
    }
    return $backup
}

function Patch-Server([string]$Path) {
    $text = (Read-Utf8 $Path).Replace("`r`n", "`n").Replace("`r", "`n")
    $text = Replace-Once $text "manifest markdown classifier" @'
function isArtifactPath(path106) {
  const lower = path106.toLowerCase();
  const dot = lower.lastIndexOf(".");
  if (dot < 0)
    return false;
  return ARTIFACT_EXTENSIONS.has(lower.slice(dot));
}
'@ @'
function isArtifactPath(path106) {
  const lower = path106.toLowerCase();
  const dot = lower.lastIndexOf(".");
  if (dot < 0)
    return false;
  return ARTIFACT_EXTENSIONS.has(lower.slice(dot));
}
function isManifestBackedMarkdownPath(filePath2) {
  const lower = filePath2.toLowerCase();
  if (!lower.endsWith(".md"))
    return false;
  try {
    const manifest = JSON.parse(fs23.readFileSync(`${filePath2}.artifact.json`, "utf8"));
    return manifest?.version === 1 && manifest?.kind === "markdown-document" && manifest?.renderer === "markdown" && manifest?.status === "complete";
  } catch {
    return false;
  }
}
'@ "function isManifestBackedMarkdownPath"

    $text = Replace-Once $text "tracked file classifier" @'
function isTrackedRunFile(name) {
  return isArtifactPath(name) || isDesignSystemFile(name) || isRenderDependencyPath(name);
}
'@ @'
function isTrackedRunFile(name, fullPath = name) {
  return isArtifactPath(name) || isManifestBackedMarkdownPath(fullPath) || isDesignSystemFile(name) || isRenderDependencyPath(name);
}
'@ "function isTrackedRunFile(name, fullPath = name)"

    $text = Replace-Once $text "sync snapshot path" @'
      } else if (entry.isFile()) {
        const tracked = isTrackedRunFile(entry.name);
        if (tracked ? trackedCount >= MAX_FILES : otherCount >= MAX_OTHER_FILES)
          continue;
        const full = path41.join(dir, entry.name);
'@ @'
      } else if (entry.isFile()) {
        const full = path41.join(dir, entry.name);
        const tracked = isTrackedRunFile(entry.name, full);
        if (tracked ? trackedCount >= MAX_FILES : otherCount >= MAX_OTHER_FILES)
          continue;
'@ "isTrackedRunFile(entry.name, full)"

    $text = Replace-Once $text "async snapshot path" @'
      } else if (entry.isFile()) {
        const tracked = isTrackedRunFile(entry.name);
        if (tracked ? trackedCount >= MAX_FILES : otherCount >= MAX_OTHER_FILES)
          continue;
        files.push({ full: path41.join(dir, entry.name), tracked });
'@ @'
      } else if (entry.isFile()) {
        const full = path41.join(dir, entry.name);
        const tracked = isTrackedRunFile(entry.name, full);
        if (tracked ? trackedCount >= MAX_FILES : otherCount >= MAX_OTHER_FILES)
          continue;
        files.push({ full, tracked });
'@ "files.push({ full, tracked })"

    $text = Replace-Once $text "diff markdown classification" '    if (isArtifactPath(classifyPath)) {' '    if (isArtifactPath(classifyPath) || isManifestBackedMarkdownPath(classifyPath)) {' 'isManifestBackedMarkdownPath(classifyPath)'
    $text = Replace-Once $text "event markdown classification" '  return collectWrittenPathsMatching(events, isArtifactPath).size;' '  return collectWrittenPathsMatching(events, (filePath2) => isArtifactPath(filePath2) || isManifestBackedMarkdownPath(filePath2)).size;' 'isManifestBackedMarkdownPath(filePath2)'
    $text = Replace-Once $text "ledger markdown classification" '    if (isArtifactPath(path106))' '    if (isArtifactPath(path106) || isManifestBackedMarkdownPath(path106))' 'isManifestBackedMarkdownPath(path106)'

    $text = Replace-Once $text "deliverable selector" @'
function matchesAcceptedKinds(acceptedKinds, fileKind) {
  return !acceptedKinds || acceptedKinds.has(fileKind);
}
'@ @'
function matchesAcceptedKinds(acceptedKinds, fileKind) {
  return !acceptedKinds || acceptedKinds.has(fileKind);
}
function selectRunDeliverableEntry(files, declared, touchedPaths, metadata) {
  const declaredEntry = declared ? files.find((file) => filePath(file) === declared) ?? null : null;
  const touched = touchedPaths instanceof Set ? touchedPaths : new Set(touchedPaths ?? []);
  const allowManifestEntryOverride = projectKind(metadata) !== "prototype";
  if (allowManifestEntryOverride) {
    const touchedArtifact = files.find((file) => {
      const entry = filePath(file);
      const manifest = file.artifactManifest;
      return touched.has(entry) && manifest?.entry === entry && manifest?.status === "complete";
    });
    if (touchedArtifact)
      return touchedArtifact;
  }
  return declaredEntry ?? inferredEntry(files, acceptedDeliverableKinds(metadata));
}
'@ "function selectRunDeliverableEntry"

    $text = Replace-Once $text "deliverable selector call" '  const selected = declared ? files.find((file) => filePath(file) === declared) ?? null : inferredEntry(files, acceptedKinds);' '  const selected = selectRunDeliverableEntry(files, declared, touched, input2.projectMetadata);' 'selectRunDeliverableEntry(files, declared, touched, input2.projectMetadata)'
    $text = Replace-Once $text "deliverable touched set" @'
  const selected = selectRunDeliverableEntry(files, declared, touched, input2.projectMetadata);
'@ @'
  const touched = input2.touchedPaths ? new Set(input2.touchedPaths.flatMap((candidate) => {
    if (typeof candidate !== "string" || !candidate)
      return [];
    const absolute = path42.isAbsolute(candidate) ? path42.resolve(candidate) : path42.resolve(projectRoot, candidate);
    const relative3 = path42.relative(projectRoot, absolute);
    if (!relative3 || relative3.startsWith("..") || path42.isAbsolute(relative3)) {
      return [];
    }
    return [relative3.replaceAll(path42.sep, "/")];
  })) : null;
  const selected = selectRunDeliverableEntry(files, declared, touched, input2.projectMetadata);
'@ 'const touched = input2.touchedPaths'
    $text = Replace-Once $text "manifest artifact facts" @'
  const facts = {
    entryFile,
    artifactKind: selected.kind
  };
'@ @'
  const selectedArtifactManifest = selected.artifactManifest;
  const facts = {
    entryFile,
    artifactKind: selectedArtifactManifest?.kind ?? selected.artifactKind ?? selected.kind
  };
'@ "const selectedArtifactManifest"
    $text = Replace-Once $text "shared touched validation" @'
  if (input2.touchedPaths) {
    const touched = new Set(input2.touchedPaths.flatMap((candidate) => {
      if (typeof candidate !== "string" || !candidate)
        return [];
      const absolute = path42.isAbsolute(candidate) ? path42.resolve(candidate) : path42.resolve(projectRoot, candidate);
      const relative3 = path42.relative(projectRoot, absolute);
      if (!relative3 || relative3.startsWith("..") || path42.isAbsolute(relative3)) {
        return [];
      }
      return [relative3.replaceAll(path42.sep, "/")];
    }));
    if (!touched.has(entryFile)) {
'@ @'
  if (touched) {
    if (!touched.has(entryFile)) {
'@ "if (touched)"

    if ($text.Contains('  ".md",`n')) {
        $text = $text.Replace('  ".md",`n', '')
    }
    return $text
}

function Patch-PackagedMain([string]$Path) {
    $text = (Read-Utf8 $Path).Replace("`r`n", "`n").Replace("`r", "`n")
    if ($text.Contains("const safeConsoleWrite")) {
        Write-Verbose "packaged logger EPIPE guard already patched"
        return $text.Replace('let echo = process.env[DESKTOP_LOG_ECHO_ENV] !== "0";', 'let echo = process.env[DESKTOP_LOG_ECHO_ENV] === "1" && process.stdout.isTTY === true;')
    }
    if (-not $text.Contains("const handleConsoleStreamError")) {
        $text = Replace-Once $text "packaged logger EPIPE guard" @'
function createPackagedDesktopLogger(paths) {
  const echo = process.env[DESKTOP_LOG_ECHO_ENV] !== "0";
'@ @'
function createPackagedDesktopLogger(paths) {
  let echo = process.env[DESKTOP_LOG_ECHO_ENV] === "1" && process.stdout.isTTY === true;
  const isBrokenPipeError = (error) => error?.code === "EPIPE" || error?.errno === -4047;
  const handleConsoleStreamError = (error) => {
    if (isBrokenPipeError(error)) {
      echo = false;
      return;
    }
    throw error;
  };
  const safeConsoleWrite = (method, args) => {
    if (!echo)
      return;
    try {
      method(...args);
    } catch (error) {
      if (isBrokenPipeError(error)) {
        echo = false;
        return;
      }
      throw error;
    }
  };
  process.stdout.on("error", handleConsoleStreamError);
  process.stderr.on("error", handleConsoleStreamError);
'@ "const handleConsoleStreamError"
    }
    if (-not $text.Contains("const safeConsoleWrite")) {
        $text = Replace-Once $text "packaged logger safe writer" @'
  let echo = process.env[DESKTOP_LOG_ECHO_ENV] === "1" && process.stdout.isTTY === true;
  const handleConsoleStreamError = (error) => {
    if (error?.code === "EPIPE") {
      echo = false;
      return;
    }
    throw error;
  };
  process.stdout.on("error", handleConsoleStreamError);
  process.stderr.on("error", handleConsoleStreamError);
'@ @'
  let echo = process.env[DESKTOP_LOG_ECHO_ENV] !== "0";
  const isBrokenPipeError = (error) => error?.code === "EPIPE" || error?.errno === -4047;
  const handleConsoleStreamError = (error) => {
    if (isBrokenPipeError(error)) {
      echo = false;
      return;
    }
    throw error;
  };
  const safeConsoleWrite = (method, args) => {
    if (!echo)
      return;
    try {
      method(...args);
    } catch (error) {
      if (isBrokenPipeError(error)) {
        echo = false;
        return;
      }
      throw error;
    }
  };
  process.stdout.on("error", handleConsoleStreamError);
  process.stderr.on("error", handleConsoleStreamError);
'@ "const safeConsoleWrite"
    }
    $text = Replace-Once $text "packaged logger safe console writes" @'
  console.log = (...args) => {
    logger.info("console.log", { args });
    if (echo) originalConsole.log(...args);
  };
  console.info = (...args) => {
    logger.info("console.info", { args });
    if (echo) originalConsole.info(...args);
  };
  console.warn = (...args) => {
    logger.warn("console.warn", { args });
    if (echo) originalConsole.warn(...args);
  };
  console.error = (...args) => {
    logger.error("console.error", { args });
    if (echo) originalConsole.error(...args);
  };
'@ @'
  console.log = (...args) => {
    logger.info("console.log", { args });
    safeConsoleWrite(originalConsole.log, args);
  };
  console.info = (...args) => {
    logger.info("console.info", { args });
    safeConsoleWrite(originalConsole.info, args);
  };
  console.warn = (...args) => {
    logger.warn("console.warn", { args });
    safeConsoleWrite(originalConsole.warn, args);
  };
  console.error = (...args) => {
    logger.error("console.error", { args });
    safeConsoleWrite(originalConsole.error, args);
  };
'@ "safeConsoleWrite(originalConsole.error, args)"
    return $text
}

function Patch-Bootstrap([string]$Path) {
    $text = (Read-Utf8 $Path).Replace("`r`n", "`n").Replace("`r", "`n")
    if (-not $text.Contains("function withMcpBootstrapLock")) {
        $text = Replace-Once $text "bootstrap imports" 'import { createRequire as __odCreateRequire } from "node:module"; const require = __odCreateRequire(import.meta.url);' @'
import { createRequire as __odCreateRequire } from "node:module"; const require = __odCreateRequire(import.meta.url);
import { createHash } from "node:crypto";
import { open, rm, stat } from "node:fs/promises";
'@ "import { createHash } from \"node:crypto\";"
        $text = Replace-Once $text "bootstrap path imports" 'import { isAbsolute } from "node:path";' @'
import { isAbsolute, join } from "node:path";
import { tmpdir } from "node:os";
'@ 'import { tmpdir } from "node:os";'
        $text = Replace-Once $text "bootstrap lock" @'
var DEFAULT_BOOTSTRAP_POLL_MS = 250;
'@ @'
var DEFAULT_BOOTSTRAP_POLL_MS = 250;
function mcpBootstrapLockPath(env) {
  const identity = env[SIDECAR_ENV.IPC_PATH] ?? env.OD_DAEMON_URL ?? "default";
  const digest = createHash("sha256").update(identity, "utf8").digest("hex").slice(0, 16);
  return join(tmpdir(), `open-design-mcp-bootstrap-${digest}.lock`);
}
async function withMcpBootstrapLock(env, action, timeoutMs) {
  const lockPath = mcpBootstrapLockPath(env);
  const deadline = Date.now() + timeoutMs;
  while (true) {
    try {
      const handle = await open(lockPath, "wx");
      try {
        return await action();
      } finally {
        await handle.close();
        await rm(lockPath, { force: true });
      }
    } catch (error) {
      if (error?.code !== "EEXIST") throw error;
      try {
        const lock = await stat(lockPath);
        if (Date.now() - lock.mtimeMs > timeoutMs * 2)
          await rm(lockPath, { force: true });
      } catch {
      }
      if (Date.now() >= deadline)
        throw new Error(`Timed out waiting for OpenDesign MCP bootstrap lock: ${lockPath}`);
      await delay(DEFAULT_BOOTSTRAP_POLL_MS);
    }
  }
}
'@ "function withMcpBootstrapLock"
        $text = Replace-Once $text "bootstrap critical section" @'
  await spawnBootstrap(plan);
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    await sleep(DEFAULT_BOOTSTRAP_POLL_MS);
    daemonUrl = registeredBootstrapTarget ? await discoverTargetDaemonUrl(env, 300) : await resolveDaemonUrl2({
      env,
      flagUrl: null,
      timeoutMs: 300
    });
    if (daemonUrl != null && await probeDaemon(daemonUrl))
      return daemonUrl;
  }
  throw new Error(`OpenDesign was launched headlessly but its daemon did not become ready within ${timeoutMs}ms.`);
'@ @'
  return await withMcpBootstrapLock(env, async () => {
    daemonUrl = registeredBootstrapTarget ? await discoverTargetDaemonUrl(env, 800) : await resolveDaemonUrl2({
      env,
      flagUrl: null,
      timeoutMs: 800
    });
    if (daemonUrl != null && (registeredBootstrapTarget || await probeDaemon(daemonUrl)))
      return daemonUrl;
    const currentPlan = planMcpDaemonBootstrap({
      daemonReachable: daemonUrl != null && await probeDaemon(daemonUrl),
      env,
      explicitDaemonUrl
    });
    if (currentPlan.action === "none") {
      if (daemonUrl != null)
        return daemonUrl;
      throw new Error(`The registered OpenDesign runtime is unavailable and cannot be launched (${currentPlan.reason}).`);
    }
    await spawnBootstrap(currentPlan);
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      await sleep(DEFAULT_BOOTSTRAP_POLL_MS);
      daemonUrl = registeredBootstrapTarget ? await discoverTargetDaemonUrl(env, 300) : await resolveDaemonUrl2({
        env,
        flagUrl: null,
        timeoutMs: 300
      });
      if (daemonUrl != null && await probeDaemon(daemonUrl))
        return daemonUrl;
    }
    throw new Error(`OpenDesign was launched headlessly but its daemon did not become ready within ${timeoutMs}ms.`);
  }, timeoutMs);
'@ "return await withMcpBootstrapLock"
    }
    return $text
}

function Get-Sha256([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '')
    } finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

function Invoke-NodeCheck([string]$Path) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($null -eq $node) {
        throw "Node.js is required for OpenDesign bundle validation."
    }
    & $node.Source --check $Path
    if ($LASTEXITCODE -ne 0) {
        throw "Node syntax check failed: $Path"
    }
}

$exe = Join-Path $InstallRoot "Open Design.exe"
$prebundled = Join-Path $InstallRoot "resources\app\prebundled"
$chunks = Join-Path $prebundled "daemon\chunks"
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "OpenDesign executable not found: $exe" }
if (-not (Test-Path -LiteralPath $prebundled -PathType Container)) { throw "OpenDesign prebundled resources not found: $prebundled" }
if (-not (Test-Path -LiteralPath $chunks -PathType Container)) { throw "OpenDesign daemon chunks not found: $chunks" }

$packagedMain = Find-Bundle $prebundled "packaged-main.mjs" @("function createPackagedDesktopLogger")
$server = Find-Bundle $chunks "server-*.mjs" @("function diffRunArtifacts", "function validateRunDeliverable")
$bootstrap = Find-Bundle $chunks "mcp-bootstrap-*.mjs" @("function ensureMcpDaemonUrl")
$version = (Get-Item -LiteralPath $exe).VersionInfo.ProductVersion
if (-not $version) { $version = "unknown" }
$backupDir = Join-Path $BackupRoot $version

$packagedMainBefore = Read-Utf8 $packagedMain.FullName
$serverBefore = Read-Utf8 $server.FullName
$bootstrapBefore = Read-Utf8 $bootstrap.FullName
$packagedMainBackup = Backup-Once $packagedMain.FullName $backupDir
$serverBackup = Backup-Once $server.FullName $backupDir
$bootstrapBackup = Backup-Once $bootstrap.FullName $backupDir

$packagedMainAfter = Patch-PackagedMain $packagedMain.FullName
$serverAfter = Patch-Server $server.FullName
$bootstrapAfter = Patch-Bootstrap $bootstrap.FullName
$packagedMainPatched = $packagedMainAfter -ne ($packagedMainBefore.Replace("`r
", "
").Replace("`r", "
"))
$serverPatched = $serverAfter -ne ($serverBefore.Replace("`r
", "
").Replace("`r", "
"))
$bootstrapPatched = $bootstrapAfter -ne ($bootstrapBefore.Replace("`r`n", "`n").Replace("`r", "`n"))

if ($VerifyOnly) {
    if (-not $packagedMainAfter.Contains("const safeConsoleWrite") -or -not $serverAfter.Contains("function isManifestBackedMarkdownPath") -or -not $serverAfter.Contains("allowManifestEntryOverride") -or -not $bootstrapAfter.Contains("function withMcpBootstrapLock")) {
        throw "OpenDesign local patch is not applied."
    }
    Write-Output "OpenDesign local patch verified: $version"
    exit 0
}

if ($packagedMainPatched) { Write-Utf8 $packagedMain.FullName $packagedMainAfter }
if ($serverPatched) { Write-Utf8 $server.FullName $serverAfter }
if ($bootstrapPatched) { Write-Utf8 $bootstrap.FullName $bootstrapAfter }
Invoke-NodeCheck $packagedMain.FullName
Invoke-NodeCheck $server.FullName
Invoke-NodeCheck $bootstrap.FullName

$marker = [ordered]@{
    patchVersion = $PatchVersion
    appliedAt = (Get-Date).ToUniversalTime().ToString("o")
    openDesignVersion = $version
    serverBundle = $server.FullName
    bootstrapBundle = $bootstrap.FullName
    packagedMainBundle = $packagedMain.FullName
    packagedMainOriginal = Get-Sha256 $packagedMainBackup
    packagedMainPatched = Get-Sha256 $packagedMain.FullName
    serverOriginal = Get-Sha256 $serverBackup
    serverPatched = Get-Sha256 $server.FullName
    bootstrapOriginal = Get-Sha256 $bootstrapBackup
    bootstrapPatched = Get-Sha256 $bootstrap.FullName
}
Write-Utf8 (Join-Path $backupDir "patch-manifest.json") ($marker | ConvertTo-Json)
Write-Output "OpenDesign local patch ready: $version"
Write-Output "Packaged main: $($packagedMain.Name)"
Write-Output "Server: $($server.Name)"
Write-Output "Bootstrap: $($bootstrap.Name)"
