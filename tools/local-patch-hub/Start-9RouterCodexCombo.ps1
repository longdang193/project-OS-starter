[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$TargetRoot,
  [switch]$InstallGlobal,
  [switch]$AllowDowngrade
)

$ErrorActionPreference = "Stop"

function Get-ResolvedPath {
  param([string]$Path)
  return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
}

function Get-ListeningOwner {
  param([int]$Port)
  $connection = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($connection.Count -eq 0) { return $null }
  $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection[0].OwningProcess)" -ErrorAction SilentlyContinue
  return [pscustomobject]@{ ProcessId = $connection[0].OwningProcess; CommandLine = $process.CommandLine }
}

function Wait-Http {
  param(
    [Parameter(Mandatory = $true)][string]$Uri,
    [Parameter(Mandatory = $true)][scriptblock]$Accept,
    [int]$TimeoutSeconds = 30
  )
  $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
  do {
    try {
      $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
      if (& $Accept $response) { return $response }
    } catch {
      $response = $_.Exception.Response
      if ($null -ne $response -and (& $Accept $response)) { return $response }
    }
    Start-Sleep -Milliseconds 500
  } while ([DateTime]::UtcNow -lt $deadline)
  throw "Timed out waiting for $Uri."
}

$targetPath = Get-ResolvedPath $TargetRoot
$git = (Get-Command git.exe -ErrorAction Stop).Source
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$globalRoot = (& $npm "root" "-g" | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Cannot resolve npm global root." }
$sourceCommit = (& $git -C $targetPath rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch "^[0-9a-f]{40}$") { throw "TargetRoot is not a Git checkout with a valid source commit: $targetPath" }
$routerCommand = (Get-Command 9router.cmd -ErrorAction SilentlyContinue).Source
if ([string]::IsNullOrWhiteSpace($routerCommand)) { $routerCommand = Join-Path (Split-Path $globalRoot -Parent) "9router.cmd" }

if ($InstallGlobal) {
  $installer = Join-Path $PSScriptRoot "Install-9RouterGlobal.ps1"
  . $installer
  $installArguments = @("-TargetPath", $targetPath)
  if ($AllowDowngrade) { $installArguments += "-AllowDowngrade" }
  Install-9RouterGlobal @installArguments
}

$routerCommand = (Get-Command 9router.cmd -ErrorAction SilentlyContinue).Source
if ([string]::IsNullOrWhiteSpace($routerCommand)) { $routerCommand = Join-Path (Split-Path $globalRoot -Parent) "9router.cmd" }
if (-not (Test-Path -LiteralPath $routerCommand -PathType Leaf)) { throw "Global 9router command is missing: $routerCommand. Run with -InstallGlobal to repair it." }
$installedPackageRoot = Join-Path $globalRoot "9router"
$installedPackageJson = Join-Path $installedPackageRoot "package.json"
$receiptPath = Join-Path $installedPackageRoot "9router-install.json"
if (-not (Test-Path -LiteralPath $installedPackageJson -PathType Leaf)) { throw "Global 9router package is missing: $installedPackageRoot" }
if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) { throw "Global 9router install receipt is missing: $receiptPath. Run with -InstallGlobal to repair it." }
$installedPackage = Get-Content -Raw -LiteralPath $installedPackageJson | ConvertFrom-Json
try { $receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json } catch { throw "Global 9router install receipt is invalid JSON: $($_.Exception.Message)" }
if ([int]$receipt.schemaVersion -ne 1 -or [string]$receipt.packageVersion -ne [string]$installedPackage.version -or [string]$receipt.sourceCommit -ne $sourceCommit -or [string]$receipt.packageContentDigest -notmatch "^[0-9a-f]{64}$") {
  throw "Refusing to start a stale or invalid 9router install receipt. Run Install-9RouterGlobal.ps1 with -TargetPath $targetPath."
}

$routerOwner = Get-ListeningOwner 20128
if ($null -eq $routerOwner) {
  Start-Process -FilePath $routerCommand -ArgumentList @("--tray", "--skip-update", "-p", "20128", "-H", "127.0.0.1") -WorkingDirectory $targetPath -WindowStyle Hidden | Out-Null
} elseif ($routerOwner.CommandLine -notmatch "9router|server\.js") {
  throw "Port 20128 is already owned by PID $($routerOwner.ProcessId): $($routerOwner.CommandLine)"
}
Wait-Http -Uri "http://127.0.0.1:20128/api/health" -Accept { param($response) $response.StatusCode -eq 200 } | Out-Null

Write-Output "9router is ready at loopback port 20128."
Write-Output "No optional web provider or startup task is managed by this launcher."
