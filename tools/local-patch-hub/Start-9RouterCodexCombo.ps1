[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$TargetRoot,
  [switch]$InstallGlobal,
  [switch]$AllowDowngrade,
  [switch]$InstallStartup
)

$ErrorActionPreference = "Stop"

function Get-ResolvedPath {
  param([string]$Path)
  return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
}

function Get-DotEnvValue {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Name
  )
  foreach ($line in Get-Content -LiteralPath $Path) {
    if ($line -match "^\s*" + [regex]::Escape($Name) + "\s*=\s*(.*)\s*$") {
      $value = $matches[1].Trim()
      if ($value.Length -ge 2 -and (($value[0] -eq '"' -and $value[$value.Length - 1] -eq '"') -or ($value[0] -eq "'" -and $value[$value.Length - 1] -eq "'"))) {
        $value = $value.Substring(1, $value.Length - 2)
      }
      return $value
    }
  }
  return $null
}

function Test-ShimApiKey {
  param([Parameter(Mandatory = $true)][string]$ApiKey)
  try {
    $headers = @{ Authorization = "Bearer $ApiKey" }
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:20129/v1/models" -Headers $headers -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
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

function Test-InstalledCgwReceipt {
  param(
    [Parameter(Mandatory = $true)][string]$PackageRoot,
    [Parameter(Mandatory = $true)][string]$PackageVersion
  )
  $receiptPath = Join-Path $PackageRoot "9router-cgw-overlay.json"
  if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) { return $false }
  try {
    $receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
    $targetVersion = [Version]$receipt.targetVersion
    $receiptPackageVersion = [Version]$receipt.packageVersion
    return [int]$receipt.schemaVersion -eq 1 -and
      [string]$receipt.overlayId -eq "9router-cgw-chat-runtime" -and
      -not [string]::IsNullOrWhiteSpace([string]$receipt.overlayVersion) -and
      $targetVersion -eq $receiptPackageVersion -and
      $receiptPackageVersion -eq [Version]$PackageVersion -and
      [string]$receipt.sourceHead -match "^[0-9a-f]{40}$"
  } catch {
    return $false
  }
}

$targetPath = Get-ResolvedPath $TargetRoot
$shimRunPath = Join-Path $targetPath "tools\cgw-codex-shim\run.js"
$envPath = Join-Path $targetPath ".env"
if (-not (Test-Path -LiteralPath $shimRunPath -PathType Leaf)) {
  throw "CGW Chat shim is missing: $shimRunPath"
}
if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
  throw "Missing local runtime environment: $envPath. Copy .env.example, add CGW_SHIM_API_KEY and CGW_SHIM_MODEL_ALIASES_JSON, and keep .env uncommitted."
}

$shimApiKey = Get-DotEnvValue -Path $envPath -Name "CGW_SHIM_API_KEY"
$modelAliases = Get-DotEnvValue -Path $envPath -Name "CGW_SHIM_MODEL_ALIASES_JSON"
if ([string]::IsNullOrWhiteSpace($modelAliases)) { throw "Missing CGW_SHIM_MODEL_ALIASES_JSON in $envPath." }
try {
  $parsedAliases = $modelAliases | ConvertFrom-Json
  foreach ($property in $parsedAliases.PSObject.Properties) {
    if ([string]$property.Value -notmatch "^chatgpt-web/") {
      throw "CGW alias $($property.Name) targets $($property.Value), which would use the native Codex passthrough and may consume Codex quota. Use a chatgpt-web/* target."
    }
  }
} catch {
  throw "Invalid CGW_SHIM_MODEL_ALIASES_JSON in ${envPath}: $($_.Exception.Message)"
}
$cgwBearer = Get-DotEnvValue -Path $envPath -Name "CGW_SHIM_CGW_BEARER"
$cgwBearerFile = Get-DotEnvValue -Path $envPath -Name "CGW_SHIM_CGW_BEARER_FILE"
if ([string]::IsNullOrWhiteSpace($shimApiKey)) {
  throw "Missing CGW_SHIM_API_KEY in $envPath."
}
if ([string]::IsNullOrWhiteSpace($cgwBearer) -and [string]::IsNullOrWhiteSpace($cgwBearerFile)) {
  throw "Missing CGW bearer source in $envPath. Set CGW_SHIM_CGW_BEARER or CGW_SHIM_CGW_BEARER_FILE."
}
if (-not [string]::IsNullOrWhiteSpace($cgwBearerFile)) {
  $resolvedBearerFile = $cgwBearerFile
  if (-not [IO.Path]::IsPathRooted($resolvedBearerFile)) { $resolvedBearerFile = Join-Path $targetPath $resolvedBearerFile }
  if (-not (Test-Path -LiteralPath $resolvedBearerFile -PathType Leaf)) { throw "CGW bearer file is missing: $resolvedBearerFile" }
}

$node = (Get-Command node -ErrorAction Stop).Source
$npm = (Get-Command npm -ErrorAction Stop).Source
$globalRoot = (& $npm "root" "-g" | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Cannot resolve npm global root." }
$routerCommand = (Get-Command 9router.cmd -ErrorAction SilentlyContinue).Source
if ([string]::IsNullOrWhiteSpace($routerCommand)) {
  $routerCommand = Join-Path (Split-Path $globalRoot -Parent) "9router.cmd"
}

if ($InstallGlobal) {
  $targetPackagePath = Join-Path $targetPath "cli\package.json"
  if (-not (Test-Path -LiteralPath $targetPackagePath -PathType Leaf)) {
    throw "TargetRoot is missing cli\package.json: $targetPath"
  }
  $targetPackage = Get-Content -Raw -LiteralPath $targetPackagePath | ConvertFrom-Json
  $applyScript = Join-Path $PSScriptRoot "Apply-9RouterCgwOverlay.ps1"
  $applyArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $applyScript, "-TargetRoot", $targetPath, "-InstallGlobal")
  if ($AllowDowngrade) { $applyArguments += "-AllowDowngrade" }
  & powershell.exe @applyArguments
  if ($LASTEXITCODE -ne 0) { throw "9router installation failed with exit code $LASTEXITCODE." }
}

$routerCommand = (Get-Command 9router.cmd -ErrorAction SilentlyContinue).Source
if ([string]::IsNullOrWhiteSpace($routerCommand)) {
  $routerCommand = Join-Path (Split-Path $globalRoot -Parent) "9router.cmd"
}
if (-not (Test-Path -LiteralPath $routerCommand -PathType Leaf)) {
  throw "Global 9router command is missing: $routerCommand. Run with -InstallGlobal to repair it."
}
$installedPackageRoot = Join-Path $globalRoot "9router"
$installedPackageJson = Join-Path $installedPackageRoot "package.json"
if (-not (Test-Path -LiteralPath $installedPackageJson -PathType Leaf)) {
  throw "Global 9router package is missing: $installedPackageRoot"
}
$installedPackage = Get-Content -Raw -LiteralPath $installedPackageJson | ConvertFrom-Json
if (-not (Test-InstalledCgwReceipt -PackageRoot $installedPackageRoot -PackageVersion ([string]$installedPackage.version))) {
  throw "Refusing to start an unpatched 9router runtime. Apply Apply-9RouterCgwOverlay.ps1 with -InstallGlobal first."
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
  Start-ProcessHidden -FilePath $node -ArgumentList @((Join-Path "tools" "cgw-codex-shim\run.js")) -WorkingDirectory $targetPath
} elseif ($shimOwner.CommandLine -notmatch "cgw-codex-shim[\\/]+run\.js") {
  throw "Port 20129 is already owned by PID $($shimOwner.ProcessId): $($shimOwner.CommandLine)"
} elseif (-not (Test-ShimApiKey -ApiKey $shimApiKey)) {
  throw "Existing CGW shim on port 20129 rejected the target .env key; stop PID $($shimOwner.ProcessId) and rerun."
}
Wait-Http -Uri ("http://127.0.0.1:{0}/v1/models" -f 20129) -Accept { param($response) $response.StatusCode -in @(200, 401) } | Out-Null
if (-not (Test-ShimApiKey -ApiKey $shimApiKey)) {
  throw "CGW shim started on port 20129 but rejected the target .env key."
}

if ($InstallStartup) {
  $startupScript = Join-Path $PSScriptRoot "Install-9RouterCodexComboStartup.ps1"
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $startupScript -TargetRoot $targetPath
  if ($LASTEXITCODE -ne 0) { throw "9router startup registration failed with exit code $LASTEXITCODE." }
}

Write-Output "9router is ready at loopback port 20128."
Write-Output "CGW Chat shim is ready at loopback port 20129."
Write-Output "The shim loads $envPath; credentials and API keys are not printed."
