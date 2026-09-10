[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$TargetRoot,
  [switch]$InstallGlobal,
  [switch]$AllowDowngrade,
  [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Install-9RouterGlobal.ps1")

function Invoke-Native {
  param([string]$File, [string[]]$Arguments)
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) { throw "$File failed with exit code $LASTEXITCODE." }
}

function Test-NativeSuccess {
  param([string]$File, [string[]]$Arguments)
  $previous = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $File @Arguments *> $null
    return $LASTEXITCODE -eq 0
  } finally { $ErrorActionPreference = $previous }
}

$targetPath = (Resolve-Path -LiteralPath $TargetRoot).Path
$overlayRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "overlays\9router-security")).Path
$git = (Get-Command git -ErrorAction Stop).Source
$head = (& $git -C $targetPath rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Target is not a Git checkout: $targetPath" }

$records = Get-ChildItem -LiteralPath $overlayRoot -Directory | ForEach-Object {
  $manifestPath = Join-Path $_.FullName "manifest.json"
  if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { return }
  $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
  [pscustomobject]@{ Manifest = $manifest; Patch = Join-Path $_.FullName ([string]$manifest.patch) }
}

$selected = @($records | Where-Object { [string]$_.Manifest.baseCommit -eq $head }) | Select-Object -First 1
$alreadyApplied = $false
if ($null -eq $selected) {
  $applied = @($records | Where-Object {
    Test-NativeSuccess $git @("-C", $targetPath, "apply", "--reverse", "--check", "--", $_.Patch)
  })
  if ($applied.Count -eq 1) {
    $selected = $applied[0]
    $alreadyApplied = $true
  } elseif (@($records).Count -eq 1) {
    $selected = $records[0]
  } else {
    $available = @($records | ForEach-Object { [string]$_.Manifest.baseCommit }) -join ", "
    throw "No 9router security overlay matches HEAD $head or an already-applied overlay. Available bases: $available"
  }
}

$patch = $selected.Patch
if (-not (Test-Path -LiteralPath $patch -PathType Leaf)) { throw "Overlay patch missing: $patch" }

$correlationPath = Join-Path $targetPath "src\sse\utils\requestCorrelation.js"
$redactionPath = Join-Path $targetPath "tests\unit\mitm-logger-redaction.test.js"
if (-not $alreadyApplied -and (Test-Path -LiteralPath $correlationPath) -and (Test-Path -LiteralPath $redactionPath)) {
  $correlation = [IO.File]::ReadAllText($correlationPath)
  $redaction = [IO.File]::ReadAllText($redactionPath)
  if (($correlation -match "serverCorrelationId|serverRequestId") -and $correlation -match "upstreamRequestId|upstream_request_id" -and $redaction -match "redact") {
    if ($InstallGlobal) {
      if ($VerifyOnly) { throw "-InstallGlobal cannot be combined with -VerifyOnly." }
      Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
    }
    Write-Output "9router security fix already present at $head; no overlay changes needed."
    exit 0
  }
}

$appliedNow = $false
if (-not $alreadyApplied) {
  if (Test-NativeSuccess $git @("-C", $targetPath, "apply", "--check", "--", $patch)) {
    if ($VerifyOnly) { throw "Overlay $($selected.Manifest.version) is available but not applied." }
    Invoke-Native $git @("-C", $targetPath, "apply", "--", $patch)
    $appliedNow = $true
  } elseif ($VerifyOnly) {
    if (-not (Test-NativeSuccess $git @("-C", $targetPath, "apply", "--3way", "--check", "--", $patch))) {
      throw "Overlay $($selected.Manifest.version) does not apply cleanly to HEAD $head. Rebase patch before update."
    }
    Write-Output "Verified 9router security overlay can be rebased onto $head."
    exit 0
  } else {
    Invoke-Native $git @("-C", $targetPath, "apply", "--3way", "--", $patch)
    $appliedNow = $true
  }
}

if ($InstallGlobal) {
  if ($VerifyOnly) { throw "-InstallGlobal cannot be combined with -VerifyOnly." }
  Install-9RouterGlobal -TargetPath $targetPath -AllowDowngrade:$AllowDowngrade
}

if ($appliedNow) { Write-Output "Applied 9router security overlay $($selected.Manifest.version) at $head." }
else { Write-Output "9router security overlay $($selected.Manifest.version) already active at $head." }
