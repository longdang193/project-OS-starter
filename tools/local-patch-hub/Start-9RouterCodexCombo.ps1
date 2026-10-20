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
  return [pscustomobject]@{
    ProcessId = $connection[0].OwningProcess
    CommandLine = $process.CommandLine
  }
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

function Start-ProcessHidden {
  param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string[]]$ArgumentList,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory
  )
  Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -WindowStyle Hidden | Out-Null
}

$targetPath = Get-ResolvedPath $TargetRoot
$shimRunPath = Join-Path $targetPath "tools\cgw-codex-shim\run.js"
$envPath = Join-Path $targetPath ".env"
if (-not (Test-Path -LiteralPath $shimRunPath -PathType Leaf)) {
  throw "CGW Codex shim is missing: $shimRunPath"
}
if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
  throw "Missing local runtime environment: $envPath. Copy .env.example, add CGW_SHIM_API_KEY and CGW_SHIM_MODEL_ALIASES_JSON, and keep .env uncommitted."
}

$node = (Get-Command node -ErrorAction Stop).Source
$routerCommand = (Get-Command 9router.cmd -ErrorAction SilentlyContinue).Source
if ([string]::IsNullOrWhiteSpace($routerCommand)) {
  $npm = (Get-Command npm -ErrorAction Stop).Source
  $globalRoot = (& $npm "root" "-g" | Out-String).Trim()
  if ($LASTEXITCODE -ne 0) { throw "Cannot resolve npm global root." }
  $routerCommand = Join-Path (Split-Path $globalRoot -Parent) "9router.cmd"
}
if (-not (Test-Path -LiteralPath $routerCommand -PathType Leaf)) {
  throw "Global 9router command is missing: $routerCommand. Run with -InstallGlobal first."
}

if ($InstallGlobal) {
  $applyScript = Join-Path $PSScriptRoot "Apply-9RouterResponsesOverlay.ps1"
  $applyArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $applyScript, "-TargetRoot", $targetPath, "-InstallGlobal")
  if ($AllowDowngrade) { $applyArguments += "-AllowDowngrade" }
  & powershell.exe @applyArguments
  if ($LASTEXITCODE -ne 0) { throw "9router installation failed with exit code $LASTEXITCODE." }
}

$routerOwner = Get-ListeningOwner 20128
if ($null -eq $routerOwner) {
  Start-ProcessHidden -FilePath $routerCommand -ArgumentList @("--tray", "--skip-update", "-p", "20128", "-H", "127.0.0.1") -WorkingDirectory $targetPath
} elseif ($routerOwner.CommandLine -notmatch "9router|server\.js") {
  throw "Port 20128 is already owned by PID $($routerOwner.ProcessId): $($routerOwner.CommandLine)"
}
Wait-Http -Uri ("http://127.0.0.1:{0}/api/health" -f 20128) -Accept { param($response) $response.StatusCode -eq 200 } | Out-Null

$shimOwner = Get-ListeningOwner 20129
if ($null -eq $shimOwner) {
  Start-ProcessHidden -FilePath $node -ArgumentList @("tools\\cgw-codex-shim\\run.js") -WorkingDirectory $targetPath
} elseif ($shimOwner.CommandLine -notmatch "cgw-codex-shim[\\/]run\.js") {
  throw "Port 20129 is already owned by PID $($shimOwner.ProcessId): $($shimOwner.CommandLine)"
}
Wait-Http -Uri ("http://127.0.0.1:{0}/v1/models" -f 20129) -Accept { param($response) $response.StatusCode -in @(200, 401) } | Out-Null

Write-Output "9router is ready at loopback port 20128."
Write-Output "CGW Codex shim is ready at loopback port 20129."
Write-Output "The shim loads $envPath; credentials and API keys are not printed."
